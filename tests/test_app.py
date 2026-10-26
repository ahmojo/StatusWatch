"""Smoke tests for the Flask application."""

from sqlalchemy.exc import OperationalError

from statuswatch import create_app
from statuswatch.database import db


def test_health_endpoint() -> None:
    app = create_app({"TESTING": True})

    response = app.test_client().get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_configuration_uses_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test-environment")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("OPERATOR_PASSWORD", "test-password")
    monkeypatch.setenv("SCHEDULER_TOKEN", "test-scheduler-token")
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+psycopg://statuswatch@database/statuswatch"
    )

    app = create_app({"TESTING": True})

    assert app.config["APP_ENV"] == "test-environment"
    assert app.config["SECRET_KEY"] == "test-secret"
    assert app.config["OPERATOR_PASSWORD"] == "test-password"
    assert app.config["SCHEDULER_TOKEN"] == "test-scheduler-token"
    assert (
        app.config["SQLALCHEMY_DATABASE_URI"]
        == "postgresql+psycopg://statuswatch@database/statuswatch"
    )


def test_live_reports_container_revision_without_querying_database(app, monkeypatch):
    def unavailable():
        raise OperationalError("SELECT 1", {}, Exception("private database details"))

    monkeypatch.setattr(db.engine, "connect", unavailable)
    app.config["SOURCE_COMMIT"] = "a" * 40
    response = app.test_client().get("/health/live")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "commit": "a" * 40}


def test_ready_checks_database(app):
    response = app.test_client().get("/health/ready")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "database": "ok"}


def test_ready_returns_503_without_database_details(app, monkeypatch):
    def unavailable():
        raise OperationalError("SELECT 1", {}, Exception("private database details"))

    monkeypatch.setattr(db.engine, "connect", unavailable)
    response = app.test_client().get("/health/ready")
    assert response.status_code == 503
    assert response.get_json() == {"status": "unavailable", "database": "unavailable"}


def test_container_revision_comes_from_environment(monkeypatch):
    monkeypatch.setenv("SOURCE_COMMIT", "b" * 40)
    app = create_app({"TESTING": True})
    assert app.test_client().get("/health/live").get_json()["commit"] == "b" * 40
