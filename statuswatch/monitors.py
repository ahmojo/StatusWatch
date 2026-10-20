import re
from datetime import UTC, datetime
from ipaddress import IPv6Address
from urllib.parse import urlsplit, urlunsplit

from flask import Blueprint, redirect, render_template, request, url_for
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from statuswatch.auth import login_required
from statuswatch.database import db
from statuswatch.models import CheckResult, Monitor

monitors_blueprint = Blueprint("monitors", __name__)


@monitors_blueprint.app_template_filter("utc_time")
def utc_time(value: datetime) -> str:
    # SQLite returns naive timestamps; stored check times are UTC.
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


def normalize_url(value: str) -> str:
    value = value.strip()
    if any(character.isspace() or ord(character) < 32 for character in value):
        raise ValueError("Die URL darf keine Leer- oder Steuerzeichen enthalten.")
    parts = urlsplit(value)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError("Eine vollständige HTTP- oder HTTPS-URL ist erforderlich.")
    if parts.username is not None or parts.password is not None:
        raise ValueError("Die URL darf keine Zugangsdaten enthalten.")
    if "\\" in value or parts.netloc.endswith(":"):
        raise ValueError("Die URL ist ungültig.")
    port = parts.port
    if port is not None and port not in (80, 443):
        raise ValueError("Nur die Ports 80 und 443 sind erlaubt.")

    host = parts.hostname.rstrip(".").encode("idna").decode("ascii").lower()
    if ":" in host:
        host = f"[{IPv6Address(host)}]"
    elif len(host) > 253 or not all(
        re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
        for label in host.split(".")
    ):
        raise ValueError("Der Hostname ist ungültig.")

    default_port = 80 if parts.scheme == "http" else 443
    if port is not None and port != default_port:
        host = f"{host}:{port}"
    normalized = urlunsplit((parts.scheme, host, parts.path or "/", parts.query, ""))
    if len(normalized) > 2048:
        raise ValueError("Die URL darf höchstens 2048 Zeichen enthalten.")
    return normalized


@monitors_blueprint.route("/", methods=["GET", "POST"])
@login_required
def index():
    error = None
    name = ""
    url = ""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        url = request.form.get("url", "")
        if not 1 <= len(name) <= 80:
            error = "Der Name muss zwischen 1 und 80 Zeichen enthalten."
        else:
            try:
                normalized = normalize_url(url)
            except ValueError:
                error = (
                    "Die URL ist ungültig. Erlaubt sind HTTP/HTTPS und Ports 80/443."
                )
            else:
                if db.session.scalar(select(func.count()).select_from(Monitor)) >= 10:
                    error = "Es sind höchstens zehn Monitore erlaubt."
                elif db.session.scalar(
                    select(Monitor).where(Monitor.url == normalized)
                ):
                    error = "Diese URL ist bereits vorhanden."
                else:
                    db.session.add(Monitor(name=name, url=normalized))
                    try:
                        db.session.commit()
                    except IntegrityError:
                        db.session.rollback()
                        error = "Diese URL ist bereits vorhanden."
                    else:
                        return redirect(url_for("monitors.index"))

    monitors = db.session.scalars(select(Monitor).order_by(Monitor.id)).all()
    latest_results = {
        monitor.id: db.session.scalar(
            select(CheckResult)
            .where(CheckResult.monitor_id == monitor.id)
            .order_by(CheckResult.checked_at.desc(), CheckResult.id.desc())
            .limit(1)
        )
        for monitor in monitors
    }
    return render_template(
        "monitors.html", monitors=monitors, latest_results=latest_results,
        error=error, name=name, url=url
    ), 400 if error else 200


@monitors_blueprint.get("/monitors/<int:monitor_id>")
@login_required
def detail(monitor_id: int):
    monitor = db.get_or_404(Monitor, monitor_id)
    results = db.session.scalars(
        select(CheckResult)
        .where(CheckResult.monitor_id == monitor.id)
        .order_by(CheckResult.checked_at.desc(), CheckResult.id.desc())
        .limit(10)
    ).all()
    return render_template("monitor_detail.html", monitor=monitor, results=results)


@monitors_blueprint.post("/monitors/<int:monitor_id>/delete")
@login_required
def delete(monitor_id: int):
    monitor = db.get_or_404(Monitor, monitor_id)
    db.session.delete(monitor)
    db.session.commit()
    return redirect(url_for("monitors.index"))
