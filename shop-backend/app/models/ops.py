from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.utils import utcnow


class Job(Base):
    """持久化后台任务：应用重启后仍能捞回未完成的工作。"""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    dedupe_key: Mapped[str | None] = mapped_column(String(96), unique=True, default=None)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_run_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    last_error: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (Index("ix_jobs_status_next", "status", "next_run_at"),)
