import logging
import os
import signal
import subprocess
from time import time
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


def stop_server(signum, frame):
    raise SystemExit(0)


def main():
    token = os.environ.get("SCHEDULER_TOKEN")
    if not token:
        raise SystemExit("SCHEDULER_TOKEN must be configured")

    web = subprocess.Popen([
        "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "120",
        "statuswatch:create_app()",
    ])
    try:
        signal.signal(signal.SIGTERM, stop_server)
        signal.signal(signal.SIGINT, stop_server)
        while True:
            # Align with UTC five-minute periods instead of adding request duration.
            delay = 300 - time() % 300
            try:
                return web.wait(timeout=delay) or 1
            except subprocess.TimeoutExpired:
                pass

            request = Request(
                "http://127.0.0.1:8000/internal/checks",
                headers={"Authorization": f"Bearer {token}"},
                method="POST",
            )
            try:
                with urlopen(request, timeout=90) as response:
                    response.read()
                logger.info("Automatic monitor checks completed")
            except (URLError, OSError) as error:
                logger.error("Automatic monitor checks failed: %s", type(error).__name__)
    finally:
        web.terminate()
        try:
            web.wait(timeout=10)
        except subprocess.TimeoutExpired:
            web.kill()
            web.wait()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    raise SystemExit(main())
