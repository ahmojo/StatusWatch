"""Shared fixtures for database tests."""

from collections.abc import Generator

import pytest
from flask import Flask
from sqlalchemy import event

from statuswatch import create_app
from statuswatch.database import db


@pytest.fixture
def app() -> Generator[Flask]:
    """Provide a fresh in-memory SQLite database for each test."""
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with application.app_context():
        event.listen(
            db.engine,
            "connect",
            lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"),
        )
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()
