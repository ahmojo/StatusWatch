"""Application configuration loaded from environment variables."""

import os


def load_config() -> dict[str, object]:
    """Return configuration values for a new application instance."""
    return {
        "APP_ENV": os.getenv("APP_ENV", "development"),
        "SOURCE_COMMIT": os.getenv("SOURCE_COMMIT", "unknown"),
        "SECRET_KEY": os.getenv("SECRET_KEY"),
        "OPERATOR_PASSWORD": os.getenv("OPERATOR_PASSWORD"),
        "SCHEDULER_TOKEN": os.getenv("SCHEDULER_TOKEN"),
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SQLALCHEMY_DATABASE_URI": os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://statuswatch@localhost:5432/statuswatch",
        ),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    }
