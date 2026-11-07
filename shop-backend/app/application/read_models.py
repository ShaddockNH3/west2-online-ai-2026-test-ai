"""应用层读模型：服务返回这些对象，接口层负责翻译成 JSON。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.entities import (
    Activity,
    Address,
    Category,
    Fulfillment,
    InventoryRow,
    Order,
    OrderLine,
    Payment,
)


@dataclass(slots=True)
class SkuCard:
    id: int
    code: str
    specs: dict[str, Any]
    price_cents: int
    original_cents: int
    activity_name: str
    status: str
    available_stock: int
    purchasable: bool


@dataclass(slots=True)
class ProductCard:
    id: int
    name: str
    cover_url: str
    category_id: int
    category_name: str
    min_price_cents: int | None
    max_price_cents: int | None
    has_activity: bool
    stock_available: int
    created_at: datetime | None


@dataclass(slots=True)
class ProductDetail:
    id: int
    name: str
    description: str
    cover_url: str
    status: str
    category: Category | None
    skus: list[SkuCard]
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(slots=True)
class CartLine:
    id: int
    sku_id: int
    product_id: int
    product_name: str
    specs: dict[str, Any]
    price_cents: int
    original_cents: int
    activity_name: str
    quantity: int
    subtotal_cents: int
    available_stock: int
    purchasable: bool
    reason: str


@dataclass(slots=True)
class CartView:
    items: list[CartLine] = field(default_factory=list)
    total_quantity: int = 0
    total_amount_cents: int = 0


@dataclass(slots=True)
class PreviewLine:
    sku_id: int
    product_id: int
    product_name: str
    specs: dict[str, Any]
    quantity: int
    unit_price_cents: int
    original_unit_price_cents: int
    activity_name: str
    purchasable: bool
    issue: str
    subtotal_cents: int
    discount_cents: int


@dataclass(slots=True)
class OrderPreview:
    items: list[PreviewLine]
    original_amount_cents: int
    discount_amount_cents: int
    total_amount_cents: int
    issues: list[tuple[str, str]]
    address: Address
    note: str = "预览不锁定价格与库存，提交订单时按当时状态重新计算"


@dataclass(slots=True)
class OrderDetail:
    order: Order
    lines: list[OrderLine]
    payments: list[Payment]
    fulfillment: Fulfillment | None


@dataclass(slots=True)
class ActivitySkuView:
    sku_id: int
    sku_code: str
    original_cents: int
    activity_cents: int
    sale_quota: int | None
    sold_count: int
    per_user_limit: int | None


@dataclass(slots=True)
class ActivityDetail:
    activity: Activity
    running: bool
    skus: list[ActivitySkuView]


@dataclass(slots=True)
class Overview:
    orders_by_status: dict[str, int]
    paid_amount_cents: int
    pending_fulfillments: int
    pending_jobs: int
    failed_jobs: int
    low_stock: list[InventoryRow]
