"""Health endpoint used by local checks and deployments."""

from flask import Blueprint, jsonify

health_blueprint = Blueprint("health", __name__)


@health_blueprint.get("/health")
def health() -> tuple[object, int]:
    """Report that the Flask process can serve requests."""
    return jsonify(status="ok"), 200
