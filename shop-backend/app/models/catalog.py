from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="ENABLED", nullable=False)


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    cover_url: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="OFF_SALE", nullable=False)

    __table_args__ = (Index("ix_products_status_id", "status", "id"),)


class Sku(TimestampMixin, Base):
    __tablename__ = "skus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    sku_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    specs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="ON_SALE", nullable=False)
