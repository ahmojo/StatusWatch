import http.client
import re
import socket
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from statuswatch.checks import check_monitor
from statuswatch.database import db
from statuswatch.models import CheckResult, Monitor

HEADERS = {"Authorization": "Bearer scheduler-secret"}


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Unexpected network access")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def client(app, monkeypatch):
    app.config["SCHEDULER_TOKEN"] = "scheduler-secret"
    clock = Mock()
    clock.now.return_value = datetime(2026, 10, 26, 9, 4, 59, tzinfo=UTC)
    monkeypatch.setattr("statuswatch.scheduler.datetime", clock)
    return app.test_client()


@pytest.fixture
def monitors(app):
    first = Monitor(name="First", url="http://first.example/")
    inactive = Monitor(name="Inactive", url="http://inactive.example/", is_active=False)
    second = Monitor(name="Second", url="http://second.example/")
    db.session.add_all([first, inactive, second])
    db.session.commit()
    return first, inactive, second


@pytest.fixture
def network(monkeypatch):
    events = []

    def resolve(host, port, **kwargs):
        events.append(host)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", port))]

    dns = Mock(side_effect=resolve)
    connection = Mock()
    connection.getresponse.return_value.status = 200
    connection.close.side_effect = lambda: events.append("closed")
    monkeypatch.setattr(socket, "getaddrinfo", dns)
    monkeypatch.setattr(socket, "socket", Mock(return_value=Mock()))
    monkeypatch.setattr(http.client, "HTTPConnection", Mock(return_value=connection))
    return dns, connection, events


@pytest.mark.parametrize("authorization", [None, "", "Bearer wrong", "scheduler-secret"])
def test_invalid_token_starts_no_checks(client, monitors, authorization, monkeypatch):
    checker = Mock(side_effect=AssertionError("Checker must not run"))
    monkeypatch.setattr("statuswatch.scheduler.check_monitor", checker)
    headers = {} if authorization is None else {"Authorization": authorization}
    response = client.post("/internal/checks", headers=headers)
    assert response.status_code == 401
    checker.assert_not_called()
    assert db.session.scalar(select(CheckResult)) is None


@pytest.mark.parametrize("configured", [None, ""])
def test_missing_configuration_starts_no_checks(app, client, monitors, configured):
    app.config["SCHEDULER_TOKEN"] = configured
    assert client.post("/internal/checks", headers=HEADERS).status_code == 503
    assert db.session.scalar(select(CheckResult)) is None


def test_only_active_monitors_are_checked_sequentially(client, monitors, network):
    response = client.post("/internal/checks", headers=HEADERS)
    assert response.status_code == 200
    assert response.get_json() == {"checked": 2, "skipped": 0}
    results = db.session.scalars(select(CheckResult).order_by(CheckResult.id)).all()
    assert [result.monitor_id for result in results] == [monitors[0].id, monitors[2].id]
    assert all(result.success for result in results)
    period = int(datetime(2026, 10, 26, 9, 4, 59, tzinfo=UTC).timestamp()) // 300
    assert [result.scheduled_period for result in results] == [period, period]
    assert network[2] == ["first.example", "closed", "second.example", "closed"]


@pytest.mark.parametrize("failure,category", [
    (socket.gaierror("private details"), "dns"),
    (TimeoutError("private details"), "timeout"),
    (503, "http_status"),
])
def test_target_error_does_not_stop_remaining_monitors(
    client, monitors, network, failure, category
):
    if category == "dns":
        network[0].side_effect = [failure, [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 80))
        ]]
    else:
        first_response = Mock(status=failure) if isinstance(failure, int) else failure
        network[1].getresponse.side_effect = [first_response, Mock(status=200)]
    response = client.post("/internal/checks", headers=HEADERS)
    assert response.status_code == 200
    assert response.get_json() == {"checked": 2, "skipped": 0}
    results = db.session.scalars(select(CheckResult).order_by(CheckResult.id)).all()
    assert results[0].error_category == category
    assert results[1].success is True
    assert results[1].monitor_id == monitors[2].id
    assert "private details" not in response.text


def test_repeat_in_same_period_is_skipped_and_next_period_runs(
    client, monitors, network, monkeypatch
):
    assert client.post("/internal/checks", headers=HEADERS).get_json()["checked"] == 2
    response = client.post("/internal/checks", headers=HEADERS)
    assert response.get_json() == {"checked": 0, "skipped": 2}
    assert network[0].call_count == 2
    clock = Mock()
    clock.now.return_value = datetime(2026, 10, 26, 9, 5, tzinfo=UTC)
    monkeypatch.setattr("statuswatch.scheduler.datetime", clock)
    assert client.post("/internal/checks", headers=HEADERS).get_json()["checked"] == 2
    assert len(db.session.scalars(select(CheckResult)).all()) == 4
    assert network[0].call_count == 4


def test_database_rejects_duplicate_monitor_period(app, monitors):
    first, _, second = monitors
    db.session.add_all([
        CheckResult(monitor_id=first.id, scheduled_period=123, success=True),
        CheckResult(monitor_id=second.id, scheduled_period=123, success=True),
    ])
    db.session.commit()
    db.session.add(CheckResult(monitor_id=first.id, scheduled_period=123, success=True))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
    assert len(db.session.scalars(select(CheckResult)).all()) == 2


def test_duplicate_insert_race_is_skipped_and_remaining_monitor_runs(
    client, monitors, network, monkeypatch
):
    def competing_check(monitor, *, scheduled_period):
        if monitor.id == monitors[0].id:
            db.session.add(CheckResult(
                monitor_id=monitor.id, scheduled_period=scheduled_period, success=True,
            ))
            db.session.commit()
        return check_monitor(monitor, scheduled_period=scheduled_period)

    monkeypatch.setattr("statuswatch.scheduler.check_monitor", competing_check)
    response = client.post("/internal/checks", headers=HEADERS)
    assert response.status_code == 200
    assert response.get_json() == {"checked": 1, "skipped": 1}
    results = db.session.scalars(select(CheckResult).order_by(CheckResult.id)).all()
    assert [result.monitor_id for result in results] == [monitors[0].id, monitors[2].id]


def test_unrelated_database_error_is_not_hidden(client, monitors, monkeypatch):
    def invalid_result(monitor, *, scheduled_period):
        db.session.add(CheckResult(
            monitor_id=monitor.id, scheduled_period=scheduled_period, success=False,
        ))
        db.session.commit()

    monkeypatch.setattr("statuswatch.scheduler.check_monitor", invalid_result)
    with pytest.raises(IntegrityError):
        client.post("/internal/checks", headers=HEADERS)


def test_manual_results_do_not_block_automatic_period(client, monitors, network):
    now = datetime.now(UTC)
    for seconds in (0, 31):
        db.session.add(CheckResult(
            monitor_id=monitors[0].id, checked_at=now - timedelta(seconds=seconds),
            success=True,
        ))
    db.session.commit()
    assert client.post("/internal/checks", headers=HEADERS).get_json()["checked"] == 2
    results = db.session.scalars(select(CheckResult)).all()
    assert len(results) == 4
    assert sum(result.scheduled_period is None for result in results) == 2


def test_empty_monitor_list_and_post_only(client):
    assert client.get("/internal/checks", headers=HEADERS).status_code == 405
    response = client.post("/internal/checks", headers=HEADERS)
    assert response.status_code == 200
    assert response.get_json() == {"checked": 0, "skipped": 0}


def test_browser_session_cannot_replace_scheduler_token(app, client, monitors):
    with client.session_transaction() as session:
        session["logged_in"] = True
    assert client.post("/internal/checks").status_code == 401
    # Other forms still require CSRF protection.
    response = client.post("/", data={"name": "New", "url": "http://new.example/"})
    assert response.status_code == 400


def test_workflow_has_five_minute_schedule_dispatch_and_shared_concurrency():
    path = Path(__file__).parents[1] / ".github/workflows/scheduled-checks.yml"
    workflow = path.read_text()
    assert re.search(
        r'^on:\n  schedule:\n    - cron: "\*/5 \* \* \* \*"\n  workflow_dispatch:',
        workflow, re.M,
    )
    assert (
        "concurrency:\n  group: statuswatch-scheduled-checks\n  cancel-in-progress: false"
        in workflow
    )
    assert "${{ secrets.SCHEDULER_TOKEN }}" in workflow
    assert '--request POST' in workflow and '/internal/checks' in workflow
