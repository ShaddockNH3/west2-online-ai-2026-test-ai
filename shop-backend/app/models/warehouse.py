from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.utils import utcnow


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    sku_id: Mapped[int] = mapped_column(ForeignKey("skus.id"), index=True, nullable=False)
    available: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (UniqueConstraint("warehouse_id", "sku_id", name="uq_inventory_sku"),)


class InventoryLog(Base):
    __tablename__ = "inventory_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventory.id"), nullable=False)
    sku_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    order_no: Mapped[str | None] = mapped_column(String(32), default=None)
    change_type: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    available_before: Mapped[int] = mapped_column(Integer, nullable=False)
    available_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
