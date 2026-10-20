import re
import socket
from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy import select

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


def test_utc_format_accepts_naive_and_offset_times():
    assert utc_time(datetime(2026, 1, 1, 12)) == "2026-01-01 12:00:00 UTC"
    assert utc_time(datetime(2026, 1, 1, 14, tzinfo=timezone(timedelta(hours=2)))) == (
        "2026-01-01 12:00:00 UTC"
    )
