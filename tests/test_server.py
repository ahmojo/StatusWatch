import signal
import socket
import subprocess
from unittest.mock import Mock, call
from urllib.error import URLError

import pytest

from statuswatch import server


@pytest.fixture
def runtime(monkeypatch):
    monkeypatch.setenv("SCHEDULER_TOKEN", "scheduler-test-token")
    web = Mock()
    monkeypatch.setattr(server.subprocess, "Popen", Mock(return_value=web))
    monkeypatch.setattr(server.signal, "signal", Mock())
    monkeypatch.setattr(server, "time", Mock(side_effect=[299, 302, 601]))
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    http = Mock(return_value=response)
    monkeypatch.setattr(server, "urlopen", http)

    def forbidden(*args, **kwargs):
        pytest.fail("Unexpected network access")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    return web, http


def test_checks_follow_five_minute_boundaries_without_request_drift(runtime):
    web, http = runtime
    web.wait.side_effect = [
        subprocess.TimeoutExpired("gunicorn", 1),
        subprocess.TimeoutExpired("gunicorn", 298),
        7, None,
    ]
    assert server.main() == 7
    assert web.wait.call_args_list == [
        call(timeout=1), call(timeout=298), call(timeout=299), call(timeout=10),
    ]
    assert http.call_count == 2
    for invocation in http.call_args_list:
        request = invocation.args[0]
        assert request.full_url == "http://127.0.0.1:8000/internal/checks"
        assert request.get_method() == "POST"
        assert request.get_header("Authorization") == "Bearer scheduler-test-token"
        assert invocation.kwargs == {"timeout": 90}
    assert server.subprocess.Popen.call_args.args[0].count("gunicorn") == 1
    command = server.subprocess.Popen.call_args.args[0]
    assert command[command.index("--workers") + 1] == "1"
    web.terminate.assert_called_once()


@pytest.mark.parametrize("error", [URLError("test-token-private"), TimeoutError()])
def test_failed_request_waits_until_next_period(runtime, caplog, error):
    web, http = runtime
    web.wait.side_effect = [
        subprocess.TimeoutExpired("gunicorn", 1),
        subprocess.TimeoutExpired("gunicorn", 298),
        1, None,
    ]
    http.side_effect = [error, http.return_value]
    assert server.main() == 1
    assert http.call_count == 2
    assert "Automatic monitor checks failed" in caplog.text
    assert "test-token-private" not in caplog.text


def test_web_process_exit_stops_scheduler(runtime):
    web, http = runtime
    web.wait.return_value = 0
    assert server.main() == 1
    http.assert_not_called()


def test_shutdown_terminates_web_process_and_kills_if_it_does_not_stop(runtime):
    web, http = runtime
    web.wait.side_effect = [SystemExit(0), subprocess.TimeoutExpired("gunicorn", 10), None]
    with pytest.raises(SystemExit):
        server.main()
    web.terminate.assert_called_once()
    web.kill.assert_called_once()
    http.assert_not_called()
    assert server.signal.signal.call_args_list == [
        call(signal.SIGTERM, server.stop_server), call(signal.SIGINT, server.stop_server),
    ]


def test_missing_token_starts_no_process(runtime, monkeypatch):
    monkeypatch.delenv("SCHEDULER_TOKEN")
    with pytest.raises(SystemExit, match="SCHEDULER_TOKEN must be configured"):
        server.main()
    server.subprocess.Popen.assert_not_called()


def test_signal_requests_shutdown():
    with pytest.raises(SystemExit) as stopped:
        server.stop_server(signal.SIGTERM, None)
    assert stopped.value.code == 0
