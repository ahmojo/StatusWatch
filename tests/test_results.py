import http.client
import re
import socket
from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
from sqlalchemy import func, select

from statuswatch.database import db
from statuswatch.models import CheckResult, Monitor
from statuswatch.monitors import utc_time


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Unexpected network access")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def token(client, path="/login"):
    with client.application.app_context():
        page = client.get(path)
    return re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)


@pytest.fixture
def client(app):
    client = app.test_client()
    client.post(
        "/login", data={"password": "test-password", "csrf_token": token(client)}
    )
    return client


@pytest.fixture
def monitor(app):
    monitor = Monitor(name="Example", url="http://example.com/")
    db.session.add(monitor)
    db.session.commit()
    return monitor


@pytest.fixture
def target(monkeypatch):
    dns = Mock(return_value=[
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 80))
    ])
    connection = Mock()
    connection.getresponse.return_value.status = 200
    monkeypatch.setattr(socket, "getaddrinfo", dns)
    monkeypatch.setattr(socket, "socket", Mock(return_value=Mock()))
    monkeypatch.setattr(http.client, "HTTPConnection", Mock(return_value=connection))
    return dns, connection


def add_result(monitor, checked_at, success=True, response_time_ms=42):
    result = CheckResult(
        monitor=monitor, checked_at=checked_at, success=success,
        status_code=200 if success else 503,
        error_category=None if success else "http_status",
        response_time_ms=response_time_ms,
    )
    db.session.add(result)
    db.session.commit()
    return result


def test_overview_shows_latest_result_for_each_monitor(client, monitor):
    add_result(monitor, datetime(2026, 1, 1, tzinfo=UTC))
    add_result(monitor, datetime(2026, 1, 2, tzinfo=UTC), False, 123)
    other = Monitor(name="Other", url="https://other.example/")
    add_result(other, datetime(2026, 1, 3, tzinfo=UTC), True, 0)
    page = client.get("/")
    assert page.status_code == 200
    first, second = page.text.split("Other", 1)
    assert "Example" in first and "http://example.com/" in first
    assert "Nicht erreichbar" in first
    assert "2026-01-02 00:00:00 UTC" in first
    assert "123 ms" in first and "503" in first
    assert "2026-01-01" not in first and "42 ms" not in first
    assert "Erreichbar" in second and "0 ms" in second


def test_unchecked_monitor_is_neutral(client, monitor):
    for path in ("/", f"/monitors/{monitor.id}"):
        page = client.get(path)
        assert page.status_code == 200
        assert "Noch nicht geprüft" in page.text
        assert "Nicht erreichbar" not in page.text


def test_detail_shows_only_ten_latest_results_in_order(client, monitor):
    # Insert out of chronological order, including a timestamp tie.
    for day in (5, 1, 12, 3, 8, 2, 11, 4, 10, 6, 9, 7, 12):
        add_result(monitor, datetime(2026, 1, day, tzinfo=UTC),
                   response_time_ms=day)
    db.session.scalar(select(CheckResult).order_by(CheckResult.id.desc())).response_time_ms = 99
    other = Monitor(name="Other", url="https://other.example/")
    add_result(other, datetime(2026, 2, 1, tzinfo=UTC), response_time_ms=999)
    page = client.get(f"/monitors/{monitor.id}")
    assert page.status_code == 200
    assert page.text.count("<dt>Prüfzeit</dt>") == 10
    dates = re.findall(r"2026-01-\d{2} 00:00:00 UTC", page.text)
    assert dates == [f"2026-01-{day:02} 00:00:00 UTC"
                     for day in (12, 12, 11, 10, 9, 8, 7, 6, 5, 4)]
    assert page.text.index("99 ms") < page.text.index("12 ms")
    assert "999 ms" not in page.text


def test_manual_check_uses_checker_and_displays_one_saved_result(client, monitor, target):
    before = datetime.now(UTC)
    response = client.post(
        f"/monitors/{monitor.id}/check", data={"csrf_token": token(client)},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Erreichbar" in response.text and "200" in response.text
    assert db.session.scalar(select(func.count()).select_from(CheckResult)) == 1
    result = db.session.scalar(select(CheckResult))
    assert result.monitor_id == monitor.id
    assert before <= result.checked_at.replace(tzinfo=UTC) <= datetime.now(UTC)
    assert utc_time(result.checked_at) in response.text
    assert f"{result.response_time_ms} ms" in response.text
    target[0].assert_called_once()
    target[1].request.assert_called_once_with("GET", "/")


def test_second_manual_check_is_blocked_without_calling_checker(client, monitor, target):
    csrf = token(client)
    path = f"/monitors/{monitor.id}/check"
    assert client.post(path, data={"csrf_token": csrf}).status_code == 302
    response = client.post(path, data={"csrf_token": csrf}, follow_redirects=True)
    assert "Bitte zwischen zwei Prüfungen 30 Sekunden warten." in response.text
    assert db.session.scalar(select(func.count()).select_from(CheckResult)) == 1
    target[0].assert_called_once()


@pytest.mark.parametrize("seconds,allowed", [(29, False), (30, True)])
def test_cooldown_boundary(client, monitor, target, monkeypatch, seconds, allowed):
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    add_result(monitor, now - timedelta(seconds=seconds), success=False)
    clock = Mock()
    clock.now.return_value = now
    monkeypatch.setattr("statuswatch.monitors.datetime", clock)
    response = client.post(
        f"/monitors/{monitor.id}/check", data={"csrf_token": token(client)},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert target[0].call_count == int(allowed)
    assert db.session.scalar(select(func.count()).select_from(CheckResult)) == 1 + allowed


def test_cooldown_is_per_monitor(client, monitor, target):
    add_result(monitor, datetime.now(UTC))
    other = Monitor(name="Other", url="http://other.example/")
    db.session.add(other)
    db.session.commit()
    response = client.post(
        f"/monitors/{other.id}/check", data={"csrf_token": token(client)}
    )
    assert response.status_code == 302
    assert db.session.scalar(select(func.count()).select_from(CheckResult)) == 2
    target[0].assert_called_once()


@pytest.mark.parametrize("method,path", [
    ("get", "/monitors/1"), ("post", "/monitors/1/check"),
])
def test_results_require_login(app, monitor, method, path):
    client = app.test_client()
    csrf = token(client)
    response = getattr(client, method)(path, data={"csrf_token": csrf})
    assert response.status_code == 302
    assert response.location == "/login"
    assert db.session.scalar(select(CheckResult)) is None


@pytest.mark.parametrize("csrf", [None, "invalid"])
def test_manual_check_requires_csrf(client, monitor, csrf):
    response = client.post(f"/monitors/{monitor.id}/check", data={"csrf_token": csrf})
    assert response.status_code == 400
    assert db.session.scalar(select(CheckResult)) is None


def test_check_is_post_only_and_unknown_monitor_is_404(client):
    assert client.get("/monitors/999/check").status_code == 405
    assert client.get("/monitors/999").status_code == 404
    assert client.post("/monitors/999/check", data={"csrf_token": token(client)}).status_code == 404


@pytest.mark.parametrize("failure,message", [
    ("dns", "Der Hostname konnte nicht aufgelöst werden."),
    ("timeout", "Das Ziel hat nicht rechtzeitig geantwortet."),
    ("http_status", "Das Ziel hat einen HTTP-Fehler gemeldet."),
])
def test_target_errors_are_saved_and_displayed(client, monitor, target, failure, message):
    if failure == "dns":
        target[0].side_effect = socket.gaierror("private details")
    elif failure == "timeout":
        target[1].getresponse.side_effect = TimeoutError("private details")
    else:
        target[1].getresponse.return_value.status = 503
    response = client.post(
        f"/monitors/{monitor.id}/check", data={"csrf_token": token(client)},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Nicht erreichbar" in response.text
    assert message in response.text and "private details" not in response.text
    assert message in client.get("/").text
    assert db.session.scalar(select(func.count()).select_from(CheckResult)) == 1
    assert db.session.scalar(select(CheckResult)).error_category == failure


def test_utc_format_accepts_naive_and_offset_times():
    assert utc_time(datetime(2026, 1, 1, 12)) == "2026-01-01 12:00:00 UTC"
    assert utc_time(datetime(2026, 1, 1, 14, tzinfo=timezone(timedelta(hours=2)))) == (
        "2026-01-01 12:00:00 UTC"
    )
