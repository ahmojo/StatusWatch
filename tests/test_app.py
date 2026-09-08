"""Smoke tests for the Flask application."""

from statuswatch import create_app


def test_health_endpoint() -> None:
    app = create_app({"TESTING": True})

    response = app.test_client().get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_configuration_uses_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test-environment")
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    app = create_app({"TESTING": True})

    assert app.config["APP_ENV"] == "test-environment"
    assert app.config["SECRET_KEY"] == "test-secret"
