"""Tests for persistence, relationships, constraints, and deletion."""

from datetime import UTC, datetime, timedelta

import pytest
from flask import Flask
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from statuswatch.database import db
from statuswatch.models import CheckResult, Monitor


def test_monitor_is_stored_and_can_be_queried(app: Flask) -> None:
    monitor = Monitor(name="Example", url="https://example.com")
    db.session.add(monitor)
    db.session.commit()

    stored = db.session.scalar(
        select(Monitor).where(Monitor.url == "https://example.com")
    )

    assert stored is not None
    assert stored.name == "Example"
    assert stored.is_active is True
    assert stored.interval_seconds == 300
    assert stored.created_at is not None
    assert stored.updated_at is not None


def test_results_belong_to_monitor_and_can_be_ordered(app: Flask) -> None:
    monitor = Monitor(name="Example", url="https://example.com")
    older = CheckResult(
        monitor=monitor,
        checked_at=datetime.now(UTC) - timedelta(minutes=5),
        status_code=503,
        response_time_ms=220,
        success=False,
        error_category="http_status",
    )
    newer = CheckResult(
        monitor=monitor,
        checked_at=datetime.now(UTC),
        status_code=204,
        response_time_ms=95,
        success=True,
    )
    db.session.add_all([older, newer])
    db.session.commit()

    results = db.session.scalars(
        select(CheckResult)
        .where(CheckResult.monitor_id == monitor.id)
        .order_by(CheckResult.checked_at.desc())
    ).all()

    assert results == [newer, older]
    assert newer.monitor is monitor
    assert monitor.check_results == [older, newer]


def test_deleting_monitor_cascades_to_results(app: Flask) -> None:
    monitor = Monitor(name="Example", url="https://example.com")
    monitor.check_results.append(
        CheckResult(
            success=False,
            error_category="timeout",
            response_time_ms=1000,
        )
    )
    db.session.add(monitor)
    db.session.commit()

    db.session.delete(monitor)
    db.session.commit()

    assert db.session.scalar(select(Monitor)) is None
    assert db.session.scalar(select(CheckResult)) is None


@pytest.mark.parametrize(
    "monitor",
    [
        Monitor(name="", url="https://empty-name.example"),
        Monitor(
            name="Too frequent",
            url="https://interval.example",
            interval_seconds=30,
        ),
    ],
)
def test_monitor_constraints_reject_invalid_values(
    app: Flask, monitor: Monitor
) -> None:
    db.session.add(monitor)

    with pytest.raises(IntegrityError):
        db.session.commit()


def test_monitor_url_must_be_unique(app: Flask) -> None:
    db.session.add_all(
        [
            Monitor(name="First", url="https://example.com"),
            Monitor(name="Second", url="https://example.com"),
        ]
    )

    with pytest.raises(IntegrityError):
        db.session.commit()


def test_result_constraint_requires_error_for_failure(app: Flask) -> None:
    monitor = Monitor(name="Example", url="https://example.com")
    monitor.check_results.append(CheckResult(success=False))
    db.session.add(monitor)

    with pytest.raises(IntegrityError):
        db.session.commit()


@pytest.mark.parametrize(
    "result",
    [
        CheckResult(success=True, status_code=700),
        CheckResult(success=True, response_time_ms=-1),
        CheckResult(success=True, error_category="timeout"),
    ],
)
def test_result_constraints_reject_invalid_values(
    app: Flask, result: CheckResult
) -> None:
    monitor = Monitor(name="Example", url="https://example.com")
    monitor.check_results.append(result)
    db.session.add(monitor)

    with pytest.raises(IntegrityError):
        db.session.commit()


def test_init_db_command_is_reproducible(app: Flask) -> None:
    db.drop_all()
    runner = app.test_cli_runner()

    first = runner.invoke(args=["init-db"])
    second = runner.invoke(args=["init-db"])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert first.output == "Database initialized.\n"
    assert second.output == "Database initialized.\n"
