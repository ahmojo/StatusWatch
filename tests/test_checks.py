import http.client
import socket
import ssl
from io import BytesIO
from unittest.mock import Mock

import pytest
from sqlalchemy import select

from statuswatch.checks import check_monitor
from statuswatch.database import db
from statuswatch.models import CheckResult, Monitor


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Unexpected network access")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def network(monkeypatch):
    dns = Mock(return_value=[
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))
    ])
    sock = Mock()
    response = Mock(status=200)
    response.read.side_effect = AssertionError("Response body must not be read")
    connection = Mock()
    connection.getresponse.return_value = response
    connection_factory = Mock(return_value=connection)
    context = Mock()
    context.wrap_socket.return_value = sock
    monkeypatch.setattr(socket, "getaddrinfo", dns)
    monkeypatch.setattr(socket, "socket", Mock(return_value=sock))
    monkeypatch.setattr(http.client, "HTTPConnection", connection_factory)
    monkeypatch.setattr(ssl, "create_default_context", Mock(return_value=context))
    return dns, sock, connection, response, context, connection_factory


def run_check(url="https://example.com/path?key=value"):
    monitor = Monitor(name="Example", url=url)
    db.session.add(monitor)
    db.session.commit()
    return check_monitor(monitor)


@pytest.mark.parametrize("status", [200, 204, 299, 301, 399, 400, 503, 599])
def test_status_and_persistence(app, network, status):
    dns, sock, connection, response, context, factory = network
    response.status = status
    result = run_check()
    db.session.expire_all()
    stored = db.session.scalar(select(CheckResult))

    assert stored.id == result.id
    assert stored.monitor.name == "Example"
    assert stored.checked_at is not None
    assert stored.status_code == status
    assert stored.response_time_ms >= 0
    assert stored.success is (200 <= status <= 399)
    assert stored.error_category == (None if stored.success else "http_status")
    dns.assert_called_once_with("example.com", 443, type=socket.SOCK_STREAM)
    sock.settimeout.assert_called_once_with(5)
    sock.connect.assert_called_once_with(("8.8.8.8", 443))
    context.wrap_socket.assert_called_once_with(sock, server_hostname="example.com")
    factory.assert_called_once_with("example.com", 443, timeout=5)
    connection.request.assert_called_once_with("GET", "/path?key=value")
    connection.getresponse.assert_called_once()
    response.read.assert_not_called()
    response.close.assert_called_once()
    connection.close.assert_called_once()
    assert set(stored.__table__.columns.keys()) == {
        "id", "monitor_id", "checked_at", "status_code", "response_time_ms",
        "success", "error_category", "scheduled_period",
    }


@pytest.mark.parametrize("address", [
    "127.0.0.1", "10.0.0.1", "192.168.1.1", "169.254.169.254",
    "0.0.0.0", "224.0.0.1", "240.0.0.1", "100.64.0.1",
    "::1", "::", "fc00::1", "fec0::1", "fe80::1", "ff02::1", "2001:db8::1",
    "::ffff:127.0.0.1",
])
def test_non_public_address_prevents_http(app, network, address):
    dns, sock, connection, _, _, factory = network
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    dns.return_value.append((family, socket.SOCK_STREAM, 6, "", (address, 443)))
    result = run_check()
    assert result.success is False
    assert result.error_category == "blocked_address"
    assert result.status_code is None
    sock.connect.assert_not_called()
    factory.assert_not_called()
    connection.request.assert_not_called()


@pytest.mark.parametrize("url,address,port", [
    ("http://example.com", "8.8.8.8", 80),
    ("http://example.com:443", "8.8.8.8", 443),
    ("https://example.com:80", "8.8.8.8", 80),
    ("https://[2606:4700:4700::1111]", "2606:4700:4700::1111", 443),
])
def test_allowed_protocols_ports_and_ipv6(app, network, url, address, port):
    dns, sock, connection, _, context, _ = network
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    endpoint = (address, port, 0, 0) if family == socket.AF_INET6 else (address, port)
    dns.return_value = [(family, socket.SOCK_STREAM, 6, "", endpoint)]
    assert run_check(url).success is True
    sock.connect.assert_called_once_with(endpoint)
    connection.request.assert_called_once_with("GET", "/")
    if url.startswith("http:"):
        context.wrap_socket.assert_not_called()


@pytest.mark.parametrize("url", [
    "ftp://example.com", "https://example.com:8080", "http://example.com:22",
    "https://user:secret@example.com", "invalid",
])
def test_invalid_url_is_recorded_without_network(app, network, url):
    dns, _, _, _, _, factory = network
    result = run_check(url)
    assert result.success is False
    assert result.error_category == "invalid_url"
    dns.assert_not_called()
    factory.assert_not_called()


@pytest.mark.parametrize("stage,error,category", [
    ("dns", socket.gaierror("private DNS details"), "dns"),
    ("connect", TimeoutError("secret target"), "timeout"),
    ("headers", TimeoutError("secret headers"), "timeout"),
    ("headers", http.client.BadStatusLine("secret body"), "connection"),
    ("connect", OSError("internal address"), "connection"),
    ("tls", ssl.SSLError("certificate details"), "tls"),
])
def test_technical_error_creates_safe_result(app, network, stage, error, category):
    dns, sock, connection, _, context, _ = network
    operation = {
        "dns": dns, "connect": sock.connect,
        "headers": connection.getresponse, "tls": context.wrap_socket,
    }[stage]
    operation.side_effect = error
    result = run_check()
    db.session.expire_all()
    stored = db.session.get(CheckResult, result.id)
    assert stored.success is False
    assert stored.status_code is None
    assert stored.error_category == category
    assert stored.response_time_ms >= 0
    assert stored.checked_at is not None
    assert operation.call_count == 1
    if stage != "dns":
        connection.close.assert_called_once()


def test_empty_dns_result(app, network):
    network[0].return_value = []
    assert run_check().error_category == "dns"
    network[5].assert_not_called()


def test_real_http_parser_does_not_follow_redirect_or_read_body(app, monkeypatch):
    headers = (
        b"HTTP/1.1 302 Found\r\nLocation: http://127.0.0.1/secret\r\n"
        b"Content-Length: 11\r\n\r\n"
    )
    stream = BytesIO(headers + b"secret body")
    file = Mock(wraps=stream)
    file.close = Mock()
    sock = Mock()
    sock.makefile.return_value = file
    dns = Mock(return_value=[
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 80))
    ])
    monkeypatch.setattr(socket, "getaddrinfo", dns)
    monkeypatch.setattr(socket, "socket", Mock(return_value=sock))

    result = run_check("http://example.com")

    assert result.success is True
    assert result.status_code == 302
    assert stream.tell() == len(headers)
    file.read.assert_not_called()
    dns.assert_called_once()
    sock.connect.assert_called_once_with(("8.8.8.8", 80))
    sock.sendall.assert_called_once()
    assert b"GET / HTTP/1.1\r\n" in sock.sendall.call_args.args[0]
    assert b"Host: example.com\r\n" in sock.sendall.call_args.args[0]
    sock.close.assert_called_once()
