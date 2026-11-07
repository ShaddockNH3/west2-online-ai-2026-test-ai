from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Activity(TimestampMixin, Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[str] = mapped_column(String(16), default="FIXED_PRICE", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ActivitySku(Base):
    __tablename__ = "activity_skus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id"), index=True, nullable=False
    )
    sku_id: Mapped[int] = mapped_column(ForeignKey("skus.id"), index=True, nullable=False)
    activity_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    sale_quota: Mapped[int | None] = mapped_column(Integer, default=None)
    sold_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    per_user_limit: Mapped[int | None] = mapped_column(Integer, default=None)

    __table_args__ = (UniqueConstraint("activity_id", "sku_id", name="uq_activity_sku"),)


class FlashSaleRequest(TimestampMixin, Base):
    __tablename__ = "flash_sale_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), nullable=False)
    sku_id: Mapped[int] = mapped_column(ForeignKey("skus.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    address_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # 抢购时的成交价与活动名快照，避免活动结束后改价
    unit_price_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    activity_name: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="QUEUED", nullable=False)
    order_no: Mapped[str | None] = mapped_column(String(32), default=None)
    message: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "request_id", name="uq_flash_user_request"),
        Index("ix_flash_activity_sku_user", "activity_id", "sku_id", "user_id"),
    )
