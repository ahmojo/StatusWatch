"""StatusWatch application factory."""

from flask import Flask

from statuswatch.config import load_config
from statuswatch.health import health_blueprint


def create_app(test_config: dict[str, object] | None = None) -> Flask:
    """Create and configure a StatusWatch application instance."""
    app = Flask(__name__)
    app.config.from_mapping(load_config())

    if test_config is not None:
        app.config.update(test_config)

    app.register_blueprint(health_blueprint)
    return app
