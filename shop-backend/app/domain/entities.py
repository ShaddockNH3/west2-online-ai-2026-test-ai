"""领域实体：与存储无关的数据结构。

仓储负责把数据库行映射成这些对象，应用层只认它们。
约定：金额用整数分，时间用 naive UTC，布尔字段不用 0/1。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class User:
    id: int
    username: str
    password_hash: str
    nickname: str = ""
    email: str | None = None
    phone: str | None = None
    role: str = "USER"
    status: str = "ACTIVE"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class AuthSession:
    id: str
    user_id: int
    refresh_jti: str
    expires_at: datetime
    revoked_at: datetime | None = None
    user_agent: str = ""
    last_used_at: datetime | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class Address:
    id: int
    user_id: int
    receiver: str
    phone: str
    detail: str
    is_default: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class Category:
    id: int
    name: str
    sort_order: int = 0
    status: str = "ENABLED"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class Product:
    id: int
    category_id: int
    name: str
    description: str = ""
    cover_url: str = ""
    status: str = "OFF_SALE"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class Sku:
    id: int
    product_id: int
    sku_code: str
    specs: dict[str, Any] = field(default_factory=dict)
    price_cents: int = 0
    status: str = "ON_SALE"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class CartItem:
    id: int
    user_id: int
    sku_id: int
    quantity: int
    created_at: datetime | None = None


@dataclass(slots=True)
class OrderLine:
    """订单明细快照。下单时的价格、名称、规格都固化在这里。"""

    sku_id: int
    product_id: int
    product_name: str
    specs: dict[str, Any]
    quantity: int
    unit_price_cents: int
    original_unit_price_cents: int
    activity_name: str = ""
    id: int = 0

    @property
    def subtotal_cents(self) -> int:
        return self.unit_price_cents * self.quantity

    @property
    def discount_cents(self) -> int:
        return (self.original_unit_price_cents - self.unit_price_cents) * self.quantity


@dataclass(slots=True)
class Order:
    id: int
    order_no: str
    user_id: int
    status: str
    original_amount_cents: int
    total_amount_cents: int
    receiver: str
    phone: str
    address_detail: str
    discount_amount_cents: int = 0
    request_id: str | None = None
    request_fingerprint: str = ""
    remark: str = ""
    expire_at: datetime | None = None
    paid_at: datetime | None = None
    shipped_at: datetime | None = None
    cancelled_at: datetime | None = None
    completed_at: datetime | None = None
    cancel_reason: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class Payment:
    id: int
    payment_no: str
    order_id: int
    order_no: str
    user_id: int
    amount_cents: int
    status: str
    channel: str = "MOCK"
    transaction_no: str = ""
    failure_reason: str = ""
    created_at: datetime | None = None
    paid_at: datetime | None = None


@dataclass(slots=True)
class Activity:
    id: int
    name: str
    type: str
    status: str
    starts_at: datetime
    ends_at: datetime
    description: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class ActivitySku:
    id: int
    activity_id: int
    sku_id: int
    activity_price_cents: int
    sale_quota: int | None = None
    sold_count: int = 0
    per_user_limit: int | None = None


@dataclass(slots=True)
class FlashSaleRequest:
    id: int
    activity_id: int
    sku_id: int
    user_id: int
    request_id: str
    quantity: int
    address_id: int
    unit_price_cents: int = 0
    activity_name: str = ""
    status: str = "QUEUED"
    order_no: str | None = None
    message: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class InventoryRecord:
    id: int
    warehouse_id: int
    sku_id: int
    available: int = 0
    reserved: int = 0
    sold: int = 0
    updated_at: datetime | None = None


@dataclass(slots=True)
class InventoryLogEntry:
    id: int
    inventory_id: int
    sku_id: int
    change_type: str
    quantity: int
    available_before: int
    available_after: int
    order_no: str | None = None
    reason: str = ""
    created_at: datetime | None = None


@dataclass(slots=True)
class Fulfillment:
    id: int
    fulfillment_no: str
    order_id: int
    order_no: str
    status: str
    receiver: str
    phone: str
    address_detail: str
    items: list[dict[str, Any]] = field(default_factory=list)
    tracking_no: str = ""
    attempts: int = 0
    last_error: str = ""
    shipped_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class Job:
    id: int
    job_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "PENDING"
    attempts: int = 0
    max_attempts: int = 3
    next_run_at: datetime | None = None
    locked_at: datetime | None = None
    last_error: str = ""
    dedupe_key: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class AdminOrderRow:
    """管理端订单列表的读模型：订单 + 下单人用户名。"""

    order: Order
    username: str


@dataclass(slots=True)
class InventoryRow:
    """库存列表的读模型：库存 + SKU + 商品。"""

    inventory: InventoryRecord
    sku_code: str
    sku_specs: dict[str, Any]
    sku_status: str
    product_id: int
    product_name: str
    product_status: str


@dataclass(slots=True)
class ActivitySkuRow:
    """活动详情读模型：活动 SKU + 商品 SKU 的价格快照。"""

    activity_sku: ActivitySku
    sku_code: str
    sku_price_cents: int
