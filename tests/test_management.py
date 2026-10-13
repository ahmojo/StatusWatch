import re
import socket

import pytest
from sqlalchemy import func, select

from statuswatch.database import db
from statuswatch.models import CheckResult, Monitor


def csrf_token(client, path="/"):
    with client.application.app_context():
        response = client.get(path)
    match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
    assert match is not None
    return match.group(1)


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Die Monitorverwaltung darf keinen Netzwerkzugriff auslösen.")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_in_client(client):
    token = csrf_token(client, "/login")
    response = client.post(
        "/login", data={"password": "test-password", "csrf_token": token}
    )
    assert response.status_code == 302
    assert response.location == "/"
    return client


def test_login_accepts_configured_password(logged_in_client):
    assert logged_in_client.get("/").status_code == 200
    with logged_in_client.session_transaction() as session:
        assert session["logged_in"] is True
        assert "test-password" not in str(dict(session))


@pytest.mark.parametrize("password", ["wrong-password", "", "falsch-ä"])
def test_login_rejects_wrong_password(client, password):
    token = csrf_token(client, "/login")
    response = client.post("/login", data={"password": password, "csrf_token": token})
    assert response.status_code == 401
    assert "Das Passwort ist falsch." in response.text
    assert client.get("/").location == "/login"
    with client.session_transaction() as session:
        assert not session.get("logged_in")


@pytest.mark.parametrize("setting", ["OPERATOR_PASSWORD", "SECRET_KEY"])
def test_login_is_unavailable_without_configuration(app, client, setting):
    app.config[setting] = None
    assert client.get("/login").status_code == 503
    assert client.get("/").location == "/login"


def test_logout_ends_session(logged_in_client):
    token = csrf_token(logged_in_client)
    response = logged_in_client.post("/logout", data={"csrf_token": token})
    assert response.status_code == 302
    assert response.location == "/login"
    with logged_in_client.session_transaction() as session:
        assert not session
    assert logged_in_client.get("/").location == "/login"
    assert (
        logged_in_client.post(
            "/",
            data={"name": "Example", "url": "https://example.com", "csrf_token": token},
        ).status_code
        == 400
    )


@pytest.mark.parametrize("path", ["/", "/monitors/1/delete", "/logout"])
def test_actions_require_login(client, path):
    monitor = Monitor(name="Keep", url="https://keep.example/")
    db.session.add(monitor)
    db.session.commit()
    token = csrf_token(client, "/login")
    response = client.post(
        path,
        data={"name": "New", "url": "https://new.example", "csrf_token": token},
    )
    assert response.status_code == 302
    assert response.location == "/login"
    assert db.session.scalar(select(func.count()).select_from(Monitor)) == 1
    assert db.session.scalar(select(Monitor)).name == "Keep"


@pytest.mark.parametrize("path", ["/login", "/", "/monitors/1/delete", "/logout"])
@pytest.mark.parametrize("token", [None, "invalid-token"])
def test_csrf_rejects_missing_or_invalid_token(logged_in_client, path, token):
    monitor = Monitor(name="Keep", url="https://keep.example/")
    db.session.add(monitor)
    db.session.commit()
    data = {"password": "test-password", "name": "New", "url": "https://new.example"}
    if token is not None:
        data["csrf_token"] = token
    response = logged_in_client.post(path, data=data)
    assert response.status_code == 400
    assert db.session.scalar(select(func.count()).select_from(Monitor)) == 1
    with logged_in_client.session_transaction() as session:
        assert session["logged_in"] is True


def test_csrf_token_from_another_session_is_rejected(app, client):
    token = csrf_token(app.test_client(), "/login")
    client.get("/login")
    response = client.post(
        "/login", data={"password": "test-password", "csrf_token": token}
    )
    assert response.status_code == 400
    assert client.get("/").location == "/login"


@pytest.mark.parametrize("name", ["X", "X" * 80])
def test_create_and_list_monitor(logged_in_client, name):
    token = csrf_token(logged_in_client)
    response = logged_in_client.post(
        "/",
        data={
            "name": name,
            "url": "HTTPS://Example.COM:443#section",
            "csrf_token": token,
        },
    )
    assert response.status_code == 302
    monitor = db.session.scalar(select(Monitor))
    assert monitor.name == name
    assert monitor.url == "https://example.com/"
    assert monitor.interval_seconds == 300
    page = logged_in_client.get("/")
    assert name in page.text
    assert "https://example.com/" in page.text


@pytest.mark.parametrize(
    ("url", "normalized"),
    [
        ("http://example.com:80", "http://example.com/"),
        ("http://example.com:443/path?x=1", "http://example.com:443/path?x=1"),
        ("https://example.com:80", "https://example.com:80/"),
        ("https://[2606:4700:4700::1111]:443", "https://[2606:4700:4700::1111]/"),
    ],
)
def test_allowed_urls_are_normalized(logged_in_client, url, normalized):
    token = csrf_token(logged_in_client)
    response = logged_in_client.post(
        "/", data={"name": "Example", "url": url, "csrf_token": token}
    )
    assert response.status_code == 302
    assert db.session.scalar(select(Monitor)).url == normalized


@pytest.mark.parametrize(
    ("name", "url"),
    [
        ("", "https://example.com"),
        ("   ", "https://example.com"),
        ("X" * 81, "https://example.com"),
        ("Example", "ftp://example.com"),
        ("Example", "example.com"),
        ("Example", "https://"),
        ("Example", "https://example.com:8080"),
        ("Example", "https://example.com:invalid"),
        ("Example", "https://example.com:"),
        ("Example", "https://[invalid"),
        ("Example", "https://user:password@example.com"),
        ("Example", "https://exa\nmple.com"),
        ("Example", "https://example.com/has space"),
        ("Example", "https://example.com\\other"),
        ("Example", "https://-invalid.example"),
        ("Example", "https://example.com/" + "x" * 2048),
    ],
)
def test_invalid_input_is_rejected_without_network(logged_in_client, name, url):
    token = csrf_token(logged_in_client)
    response = logged_in_client.post(
        "/", data={"name": name, "url": url, "csrf_token": token}
    )
    assert response.status_code == 400
    assert 'role="alert"' in response.text
    assert db.session.scalar(select(func.count()).select_from(Monitor)) == 0


def test_normalized_duplicate_is_rejected(logged_in_client):
    token = csrf_token(logged_in_client)
    for url, expected in [
        ("https://example.com/", 302),
        ("HTTPS://EXAMPLE.COM:443#fragment", 400),
    ]:
        response = logged_in_client.post(
            "/", data={"name": "Example", "url": url, "csrf_token": token}
        )
        assert response.status_code == expected
    assert "Diese URL ist bereits vorhanden." in response.text
    assert db.session.scalar(select(func.count()).select_from(Monitor)) == 1


def test_ten_monitor_limit_and_creation_after_deletion(logged_in_client):
    token = csrf_token(logged_in_client)
    for index in range(11):
        response = logged_in_client.post(
            "/",
            data={
                "name": f"Monitor {index}",
                "url": f"https://example{index}.com",
                "csrf_token": token,
            },
        )
        assert response.status_code == (302 if index < 10 else 400)
    assert "höchstens zehn Monitore" in response.text
    assert db.session.scalar(select(func.count()).select_from(Monitor)) == 10
    monitor = db.session.scalar(select(Monitor))
    assert (
        logged_in_client.post(
            f"/monitors/{monitor.id}/delete", data={"csrf_token": token}
        ).status_code
        == 302
    )
    assert (
        logged_in_client.post(
            "/",
            data={
                "name": "Replacement",
                "url": "https://replacement.com",
                "csrf_token": token,
            },
        ).status_code
        == 302
    )
    assert db.session.scalar(select(func.count()).select_from(Monitor)) == 10


def test_delete_monitor_removes_its_results(logged_in_client):
    monitor = Monitor(name="Delete", url="https://delete.example/")
    db.session.add(CheckResult(monitor=monitor, success=True, status_code=200))
    db.session.add(Monitor(name="Keep", url="https://keep.example/"))
    db.session.commit()
    token = csrf_token(logged_in_client)
    response = logged_in_client.post(
        f"/monitors/{monitor.id}/delete", data={"csrf_token": token}
    )
    assert response.status_code == 302
    assert db.session.scalar(select(CheckResult)) is None
    assert db.session.scalar(select(Monitor)).name == "Keep"


def test_delete_unknown_monitor_returns_404(logged_in_client):
    token = csrf_token(logged_in_client)
    assert (
        logged_in_client.post(
            "/monitors/999/delete", data={"csrf_token": token}
        ).status_code
        == 404
    )


@pytest.mark.parametrize("path", ["/logout", "/monitors/1/delete"])
def test_get_cannot_logout_or_delete(logged_in_client, path):
    assert logged_in_client.get(path).status_code == 405
    assert logged_in_client.get("/").status_code == 200


def test_monitor_name_is_escaped(logged_in_client):
    token = csrf_token(logged_in_client)
    logged_in_client.post(
        "/",
        data={
            "name": "<script>alert(1)</script>",
            "url": "https://example.com",
            "csrf_token": token,
        },
    )
    page = logged_in_client.get("/")
    assert "<script>" not in page.text
    assert "&lt;script&gt;" in page.text
