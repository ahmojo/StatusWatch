"""Persistence models for monitored targets and their check results."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from statuswatch.database import db


class Monitor(db.Model):
    """A public HTTP or HTTPS target monitored by StatusWatch."""

    __tablename__ = "monitors"
    __table_args__ = (
        CheckConstraint("length(name) BETWEEN 1 AND 80", name="name_length"),
        CheckConstraint("interval_seconds >= 60", name="minimum_interval"),
        UniqueConstraint("url"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    interval_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=300
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    check_results: Mapped[list[CheckResult]] = relationship(
        back_populates="monitor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CheckResult(db.Model):
    """One recorded availability check for a monitor."""

    __tablename__ = "check_results"
    __table_args__ = (
        CheckConstraint(
            "status_code IS NULL OR status_code BETWEEN 100 AND 599",
            name="valid_status_code",
        ),
        CheckConstraint(
            "response_time_ms IS NULL OR response_time_ms >= 0",
            name="non_negative_response_time",
        ),
        CheckConstraint(
            "(success AND error_category IS NULL) OR "
            "(NOT success AND error_category IS NOT NULL)",
            name="error_matches_success",
        ),
        Index("ix_check_results_monitor_checked", "monitor_id", "checked_at"),
        UniqueConstraint(
            "monitor_id", "scheduled_period", name="uq_check_results_monitor_period"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    monitor_id: Mapped[int] = mapped_column(
        ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    status_code: Mapped[int | None] = mapped_column(Integer)
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_category: Mapped[str | None] = mapped_column(String(50))
    scheduled_period: Mapped[int | None] = mapped_column(Integer)
    monitor: Mapped[Monitor] = relationship(back_populates="check_results")
