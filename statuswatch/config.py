"""Application configuration loaded from environment variables."""

import os


def load_config() -> dict[str, object]:
    """Return configuration values for a new application instance."""
    return {
        "APP_ENV": os.getenv("APP_ENV", "development"),
        "SECRET_KEY": os.getenv("SECRET_KEY"),
    }
