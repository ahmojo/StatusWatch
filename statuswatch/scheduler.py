import hmac
from datetime import UTC, datetime

from flask import Blueprint, abort, current_app, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from statuswatch.checks import check_monitor
from statuswatch.database import db
from statuswatch.models import CheckResult, Monitor

scheduler_blueprint = Blueprint("scheduler", __name__)


@scheduler_blueprint.post("/internal/checks")
def check_active_monitors():
    token = current_app.config["SCHEDULER_TOKEN"]
    if not token:
        abort(503)
    expected = f"Bearer {token}".encode("utf-8")
    supplied = request.headers.get("Authorization", "").encode("utf-8")
    if not hmac.compare_digest(supplied, expected):
        abort(401)

    period = int(datetime.now(UTC).timestamp()) // 300
    monitors = db.session.scalars(
        select(Monitor).where(Monitor.is_active.is_(True)).order_by(Monitor.id)
    ).all()
    checked = 0
    skipped = 0
    for monitor in monitors:
        existing_result = select(CheckResult.id).where(
            CheckResult.monitor_id == monitor.id,
            CheckResult.scheduled_period == period,
        )
        if db.session.scalar(existing_result) is not None:
            skipped += 1
            continue
        try:
            check_monitor(monitor, scheduled_period=period)
        except IntegrityError:
            db.session.rollback()
            # A simultaneous request may have stored this period first.
            if db.session.scalar(existing_result) is None:
                raise
            skipped += 1
        else:
            checked += 1
    return {"checked": checked, "skipped": skipped}
