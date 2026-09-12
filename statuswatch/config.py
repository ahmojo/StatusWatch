"""Application configuration loaded from environment variables."""

import os


def load_config() -> dict[str, object]:
    """Return configuration values for a new application instance."""
    return {
        "APP_ENV": os.getenv("APP_ENV", "development"),
        "SECRET_KEY": os.getenv("SECRET_KEY"),
        "SQLALCHEMY_DATABASE_URI": os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://statuswatch@localhost:5432/statuswatch",
        ),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    }
