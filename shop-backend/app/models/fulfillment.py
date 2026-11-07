from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.utils import utcnow


class Fulfillment(Base):
    __tablename__ = "fulfillments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fulfillment_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True, nullable=False)
    order_no: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    receiver: Mapped[str] = mapped_column(String(64), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    address_detail: Mapped[str] = mapped_column(String(255), nullable=False)
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    tracking_no: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )
