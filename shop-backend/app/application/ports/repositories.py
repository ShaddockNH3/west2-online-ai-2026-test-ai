"""仓储端口：应用层依赖这些 Protocol，基础设施层给出 SQLAlchemy 实现。

约定
- 只返回领域实体或读模型，不暴露 ORM 对象与会话。
- 写操作要么成功返回，要么抛领域异常；事务提交由 UnitOfWork 负责。
- 需要并发安全的操作（占库存、抢名额、改订单状态）用带条件的原子写，
  返回 bool 表示是否抢到，调用方据此决定回滚还是继续。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from app.domain.entities import (
    Activity,
    ActivitySku,
    ActivitySkuRow,
    Address,
    AdminOrderRow,
    AuthSession,
    CartItem,
    Category,
    FlashSaleRequest,
    Fulfillment,
    InventoryLogEntry,
    InventoryRecord,
    InventoryRow,
    Job,
    Order,
    OrderLine,
    Payment,
    Product,
    Sku,
    User,
)
from app.domain.pricing import PriceRule


@runtime_checkable
class UserRepository(Protocol):
    async def get(self, user_id: int) -> User | None: ...

    async def get_by_username(self, username: str) -> User | None: ...

    async def username_exists(self, username: str) -> bool: ...

    async def create(
        self, *, username: str, password_hash: str, nickname: str, role: str
    ) -> User: ...

    async def update_profile(
        self, user_id: int, *, nickname: str | None, email: str | None, phone: str | None
    ) -> User: ...

    async def update_password(self, user_id: int, password_hash: str) -> None: ...

    async def revoke_sessions(self, user_id: int, *, now: datetime) -> None: ...


@runtime_checkable
class SessionRepository(Protocol):
    async def create(
        self,
        *,
        session_id: str,
        user_id: int,
        refresh_jti: str,
        expires_at: datetime,
        user_agent: str,
    ) -> None: ...

    async def get(self, session_id: str) -> AuthSession | None: ...

    async def get_with_user(self, session_id: str) -> tuple[AuthSession, User] | None: ...

    async def rotate(
        self,
        session_id: str,
        *,
        refresh_jti: str,
        expires_at: datetime,
        last_used_at: datetime,
        user_agent: str,
    ) -> None: ...

    async def revoke(self, session_id: str, *, now: datetime) -> None: ...


@runtime_checkable
class AddressRepository(Protocol):
    async def list_for_user(self, user_id: int) -> list[Address]: ...

    async def get_owned(self, address_id: int, user_id: int) -> Address | None: ...

    async def has_any(self, user_id: int) -> bool: ...

    async def create(
        self, *, user_id: int, receiver: str, phone: str, detail: str, is_default: bool
    ) -> Address: ...

    async def update(
        self,
        address_id: int,
        *,
        receiver: str | None,
        phone: str | None,
        detail: str | None,
        is_default: bool | None,
    ) -> Address: ...

    async def delete(self, address_id: int) -> None: ...

    async def clear_other_defaults(self, user_id: int, keep_id: int) -> None: ...

    async def latest_for_user(self, user_id: int) -> Address | None: ...


@runtime_checkable
class CatalogRepository(Protocol):
    async def list_categories(self, *, include_disabled: bool) -> list[Category]: ...

    async def get_category(self, category_id: int) -> Category | None: ...

    async def create_category(self, *, name: str, sort_order: int) -> Category: ...

    async def update_category(
        self, category_id: int, *, name: str | None, sort_order: int | None, status: str | None
    ) -> Category: ...

    async def get_product(self, product_id: int) -> Product | None: ...

    async def get_skus(self, product_id: int) -> list[Sku]: ...

    async def get_sku(self, sku_id: int) -> Sku | None: ...

    async def get_skus_with_products(self, sku_ids: list[int]) -> list[tuple[Sku, Product]]: ...

    async def count_skus(self, product_id: int) -> int: ...

    async def create_product(
        self, *, category_id: int, name: str, description: str, cover_url: str, status: str
    ) -> Product: ...

    async def update_product(
        self,
        product_id: int,
        *,
        category_id: int | None,
        name: str | None,
        description: str | None,
        cover_url: str | None,
    ) -> Product: ...

    async def set_product_status(self, product_id: int, status: str) -> Product: ...

    async def has_sellable_sku(self, product_id: int) -> bool: ...

    async def create_sku(
        self,
        *,
        product_id: int,
        sku_code: str,
        specs: dict[str, Any],
        price_cents: int,
        status: str,
    ) -> Sku: ...

    async def update_sku(
        self,
        sku_id: int,
        *,
        specs: dict[str, Any] | None,
        price_cents: int | None,
        status: str | None,
    ) -> Sku: ...

    async def list_public_products(
        self,
        *,
        page: int,
        page_size: int,
        category_id: int | None,
        keyword: str | None,
    ) -> tuple[list[tuple[Product, Category]], int]: ...

    async def list_skus_for_products(self, product_ids: list[int]) -> list[Sku]: ...

    async def admin_list_products(
        self,
        *,
        page: int,
        page_size: int,
        status: str | None,
        category_id: int | None,
    ) -> tuple[list[tuple[Product, Category]], int]: ...


@runtime_checkable
class CartRepository(Protocol):
    async def list_for_user(self, user_id: int) -> list[CartItem]: ...

    async def get_by_ids(self, user_id: int, item_ids: list[int]) -> list[CartItem]: ...

    async def get_owned(self, item_id: int, user_id: int) -> CartItem | None: ...

    async def find_by_sku(self, user_id: int, sku_id: int) -> CartItem | None: ...

    async def add(self, *, user_id: int, sku_id: int, quantity: int) -> CartItem: ...

    async def update_quantity(self, item_id: int, quantity: int) -> CartItem: ...

    async def delete(self, item_id: int) -> None: ...

    async def delete_many(self, item_ids: list[int]) -> None: ...


@runtime_checkable
class OrderRepository(Protocol):
    async def create(self, order: Order, lines: list[OrderLine]) -> Order: ...

    async def find_by_request_id(self, user_id: int, request_id: str) -> Order | None: ...

    async def get_by_no(self, order_no: str) -> Order | None: ...

    async def list_for_user(
        self, user_id: int, *, page: int, page_size: int, status: str | None
    ) -> tuple[list[Order], int]: ...

    async def admin_list(
        self, *, page: int, page_size: int, status: str | None, keyword: str | None
    ) -> tuple[list[AdminOrderRow], int]: ...

    async def item_counts(self, order_ids: list[int]) -> dict[int, int]: ...

    async def lines_of(self, order_id: int) -> list[OrderLine]: ...

    async def payments_of(self, order_id: int) -> list[Payment]: ...

    async def add_payment(self, payment: Payment) -> Payment: ...

    async def transition(
        self,
        order_id: int,
        *,
        from_status: str,
        to_status: str,
        fields: dict[str, Any],
    ) -> bool: ...

    async def paid_amount(self) -> int: ...

    async def count_by_status(self) -> dict[str, int]: ...


@runtime_checkable
class InventoryRepository(Protocol):
    async def get(self, sku_id: int) -> InventoryRecord | None: ...

    async def ensure(self, sku_id: int, initial: int = 0) -> InventoryRecord: ...

    async def available_map(self, sku_ids: list[int]) -> dict[int, int]: ...

    async def available_of(self, sku_id: int) -> int: ...

    async def move(
        self,
        sku_id: int,
        quantity: int,
        *,
        action: str,
        order_no: str | None,
        reason: str,
    ) -> bool: ...

    async def inbound(self, sku_id: int, quantity: int, *, reason: str) -> InventoryRecord: ...

    async def adjust_to(self, sku_id: int, target: int, *, reason: str) -> InventoryRecord: ...

    async def list_rows(
        self,
        *,
        page: int,
        page_size: int,
        keyword: str | None,
        low_stock: int | None,
    ) -> tuple[list[InventoryRow], int]: ...

    async def logs(
        self, *, sku_id: int | None, page: int, page_size: int
    ) -> tuple[list[InventoryLogEntry], int]: ...


@runtime_checkable
class ActivityRepository(Protocol):
    async def create(self, activity: Activity, skus: list[ActivitySku]) -> Activity: ...

    async def update(self, activity_id: int, fields: dict[str, Any]) -> Activity: ...

    async def get(self, activity_id: int) -> Activity | None: ...

    async def list(self, *, include_disabled: bool, active_only: bool) -> list[Activity]: ...

    async def sku_rows(self, activity_id: int) -> list[ActivitySkuRow]: ...

    async def get_activity_sku(
        self, *, activity_id: int, sku_id: int
    ) -> tuple[Activity, ActivitySku] | None: ...

    async def active_rules(self, sku_ids: list[int], *, now: datetime) -> dict[int, PriceRule]: ...

    async def consume_quota(self, activity_sku_id: int, quantity: int) -> bool: ...

    async def release_quota(self, activity_id: int, sku_id: int, quantity: int) -> None: ...

    async def bought_quantity(self, activity_id: int, sku_id: int, user_id: int) -> int: ...


@runtime_checkable
class FlashSaleRepository(Protocol):
    async def find_by_request(self, user_id: int, request_id: str) -> FlashSaleRequest | None: ...

    async def create(self, request: FlashSaleRequest) -> FlashSaleRequest: ...

    async def get(self, request_id: int) -> FlashSaleRequest | None: ...

    async def save(self, request: FlashSaleRequest) -> None: ...

    async def list_for_user(self, user_id: int, *, limit: int) -> list[FlashSaleRequest]: ...


@runtime_checkable
class FulfillmentRepository(Protocol):
    async def create(self, record: Fulfillment) -> Fulfillment: ...

    async def get_by_no(self, fulfillment_no: str) -> Fulfillment | None: ...

    async def get_by_order(self, order_id: int) -> Fulfillment | None: ...

    async def list(
        self, *, page: int, page_size: int, status: str | None
    ) -> tuple[list[Fulfillment], int]: ...

    async def save(self, record: Fulfillment) -> None: ...

    async def count_pending(self) -> int: ...


@runtime_checkable
class JobRepository(Protocol):
    async def enqueue(
        self,
        job_type: str,
        payload: dict[str, Any],
        *,
        dedupe_key: str | None,
        delay_seconds: float,
        max_attempts: int | None,
    ) -> Job | None: ...

    async def claim_one(self) -> Job | None: ...

    async def finish(self, job_id: int, *, error: str = "") -> None: ...

    async def retry_or_fail(self, job: Job, error: str) -> bool: ...

    async def recover_stale(self, *, stuck_seconds: int) -> int: ...

    async def list(
        self, *, page: int, page_size: int, status: str | None, job_type: str | None
    ) -> tuple[list[Job], int]: ...

    async def get(self, job_id: int) -> Job | None: ...

    async def retry(self, job_id: int, *, reset_attempts: bool) -> Job: ...

    async def count_by_status(self) -> dict[str, int]: ...
