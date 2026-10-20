import http.client
import socket
import ssl
from datetime import UTC, datetime
from ipaddress import IPv6Address, ip_address
from time import monotonic
from urllib.parse import urlsplit

from statuswatch.database import db
from statuswatch.models import CheckResult, Monitor
from statuswatch.monitors import normalize_url


def check_monitor(monitor: Monitor) -> CheckResult:
    result = CheckResult(
        monitor_id=monitor.id, checked_at=datetime.now(UTC), success=False
    )
    started = monotonic()
    connection = None
    try:
        try:
            parts = urlsplit(normalize_url(monitor.url))
        except ValueError:
            result.error_category = "invalid_url"
        else:
            port = parts.port or (443 if parts.scheme == "https" else 80)
            addresses = socket.getaddrinfo(
                parts.hostname, port, type=socket.SOCK_STREAM
            )
            ips = [ip_address(address[4][0]) for address in addresses]
            if not addresses:
                result.error_category = "dns"
            elif any(
                not ip.is_global or ip.is_multicast or ip.is_reserved
                or (isinstance(ip, IPv6Address) and ip.is_site_local)
                for ip in ips
            ):
                result.error_category = "blocked_address"
            else:
                family, kind, protocol, _, address = addresses[0]
                connection = http.client.HTTPConnection(parts.hostname, port, timeout=5)
                # Connect to the checked address without resolving the host again.
                connection.sock = socket.socket(family, kind, protocol)
                connection.sock.settimeout(5)
                connection.sock.connect(address)
                if parts.scheme == "https":
                    connection.sock = ssl.create_default_context().wrap_socket(
                        connection.sock, server_hostname=parts.hostname
                    )
                target = parts.path or "/"
                if parts.query:
                    target += "?" + parts.query
                connection.request("GET", target)
                response = connection.getresponse()
                try:
                    result.status_code = response.status
                    result.success = 200 <= response.status <= 399
                    if not result.success:
                        result.error_category = "http_status"
                finally:
                    response.close()
    except socket.gaierror:
        result.error_category = "dns"
    except TimeoutError:
        result.error_category = "timeout"
    except ssl.SSLError:
        result.error_category = "tls"
    except (OSError, http.client.HTTPException):
        result.error_category = "connection"
    finally:
        if connection is not None:
            connection.close()
    result.response_time_ms = round((monotonic() - started) * 1000)
    db.session.add(result)
    db.session.commit()
    return result
