"""Health endpoint used by local checks and deployments."""

from flask import Blueprint, current_app, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from statuswatch.database import db

health_blueprint = Blueprint("health", __name__)


@health_blueprint.get("/health")
def health() -> tuple[object, int]:
    """Report that the Flask process can serve requests."""
    return jsonify(status="ok"), 200


@health_blueprint.get("/health/live")
def live() -> tuple[object, int]:
    """Report the revision baked into the running container."""
    return jsonify(status="ok", commit=current_app.config["SOURCE_COMMIT"]), 200


@health_blueprint.get("/health/ready")
def ready() -> tuple[object, int]:
    """Check that the process can also query its database."""
    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return jsonify(status="unavailable", database="unavailable"), 503
    return jsonify(status="ok", database="ok"), 200
