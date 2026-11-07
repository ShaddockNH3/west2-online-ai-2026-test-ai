"""ORM 行 → 领域实体。只在这一层出现 SQLAlchemy 模型。"""

from __future__ import annotations

from app.domain import entities as e
from app.infrastructure.persistence.models import (
    Activity,
    ActivitySku,
    Address,
    AuthSession,
    CartItem,
    Category,
    FlashSaleRequest,
    Fulfillment,
    Inventory,
    InventoryLog,
    Job,
    Order,
    OrderItem,
    Payment,
    Product,
    Sku,
    User,
)


def to_user(row: User) -> e.User:
    return e.User(
        id=row.id,
        username=row.username,
        password_hash=row.password_hash,
        nickname=row.nickname,
        email=row.email,
        phone=row.phone,
        role=row.role,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_session(row: AuthSession) -> e.AuthSession:
    return e.AuthSession(
        id=row.id,
        user_id=row.user_id,
        refresh_jti=row.refresh_jti,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
        user_agent=row.user_agent,
        last_used_at=row.last_used_at,
        created_at=row.created_at,
    )


def to_address(row: Address) -> e.Address:
    return e.Address(
        id=row.id,
        user_id=row.user_id,
        receiver=row.receiver,
        phone=row.phone,
        detail=row.detail,
        is_default=bool(row.is_default),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_category(row: Category) -> e.Category:
    return e.Category(
        id=row.id,
        name=row.name,
        sort_order=row.sort_order,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_product(row: Product) -> e.Product:
    return e.Product(
        id=row.id,
        category_id=row.category_id,
        name=row.name,
        description=row.description,
        cover_url=row.cover_url,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_sku(row: Sku) -> e.Sku:
    return e.Sku(
        id=row.id,
        product_id=row.product_id,
        sku_code=row.sku_code,
        specs=dict(row.specs or {}),
        price_cents=row.price_cents,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_cart_item(row: CartItem) -> e.CartItem:
    return e.CartItem(
        id=row.id,
        user_id=row.user_id,
        sku_id=row.sku_id,
        quantity=row.quantity,
        created_at=row.created_at,
    )


def to_order(row: Order) -> e.Order:
    return e.Order(
        id=row.id,
        order_no=row.order_no,
        user_id=row.user_id,
        status=row.status,
        original_amount_cents=row.original_amount_cents,
        discount_amount_cents=row.discount_amount_cents,
        total_amount_cents=row.total_amount_cents,
        receiver=row.receiver,
        phone=row.phone,
        address_detail=row.address_detail,
        request_id=row.request_id,
        request_fingerprint=row.request_fingerprint,
        remark=row.remark,
        expire_at=row.expire_at,
        paid_at=row.paid_at,
        shipped_at=row.shipped_at,
        cancelled_at=row.cancelled_at,
        completed_at=row.completed_at,
        cancel_reason=row.cancel_reason,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_order_line(row: OrderItem) -> e.OrderLine:
    return e.OrderLine(
        id=row.id,
        sku_id=row.sku_id,
        product_id=row.product_id,
        product_name=row.product_name,
        specs=dict(row.specs or {}),
        quantity=row.quantity,
        unit_price_cents=row.unit_price_cents,
        original_unit_price_cents=row.original_unit_price_cents,
        activity_name=row.activity_name,
    )


def to_payment(row: Payment) -> e.Payment:
    return e.Payment(
        id=row.id,
        payment_no=row.payment_no,
        order_id=row.order_id,
        order_no=row.order_no,
        user_id=row.user_id,
        amount_cents=row.amount_cents,
        status=row.status,
        channel=row.channel,
        transaction_no=row.transaction_no,
        failure_reason=row.failure_reason,
        created_at=row.created_at,
        paid_at=row.paid_at,
    )


def to_activity(row: Activity) -> e.Activity:
    return e.Activity(
        id=row.id,
        name=row.name,
        type=row.type,
        status=row.status,
        description=row.description,
        starts_at=row.starts_at,
        ends_at=row.ends_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_activity_sku(row: ActivitySku) -> e.ActivitySku:
    return e.ActivitySku(
        id=row.id,
        activity_id=row.activity_id,
        sku_id=row.sku_id,
        activity_price_cents=row.activity_price_cents,
        sale_quota=row.sale_quota,
        sold_count=row.sold_count,
        per_user_limit=row.per_user_limit,
    )


def to_flash_request(row: FlashSaleRequest) -> e.FlashSaleRequest:
    return e.FlashSaleRequest(
        id=row.id,
        activity_id=row.activity_id,
        sku_id=row.sku_id,
        user_id=row.user_id,
        request_id=row.request_id,
        quantity=row.quantity,
        address_id=row.address_id,
        unit_price_cents=row.unit_price_cents,
        activity_name=row.activity_name,
        status=row.status,
        order_no=row.order_no,
        message=row.message,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_inventory(row: Inventory) -> e.InventoryRecord:
    return e.InventoryRecord(
        id=row.id,
        warehouse_id=row.warehouse_id,
        sku_id=row.sku_id,
        available=row.available,
        reserved=row.reserved,
        sold=row.sold,
        updated_at=row.updated_at,
    )


def to_inventory_log(row: InventoryLog) -> e.InventoryLogEntry:
    return e.InventoryLogEntry(
        id=row.id,
        inventory_id=row.inventory_id,
        sku_id=row.sku_id,
        change_type=row.change_type,
        quantity=row.quantity,
        available_before=row.available_before,
        available_after=row.available_after,
        order_no=row.order_no,
        reason=row.reason,
        created_at=row.created_at,
    )


def to_fulfillment(row: Fulfillment) -> e.Fulfillment:
    return e.Fulfillment(
        id=row.id,
        fulfillment_no=row.fulfillment_no,
        order_id=row.order_id,
        order_no=row.order_no,
        status=row.status,
        receiver=row.receiver,
        phone=row.phone,
        address_detail=row.address_detail,
        items=list(row.items or []),
        tracking_no=row.tracking_no,
        attempts=row.attempts,
        last_error=row.last_error,
        shipped_at=row.shipped_at,
        completed_at=row.completed_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_job(row: Job) -> e.Job:
    return e.Job(
        id=row.id,
        job_type=row.job_type,
        payload=dict(row.payload or {}),
        status=row.status,
        attempts=row.attempts,
        max_attempts=row.max_attempts,
        next_run_at=row.next_run_at,
        locked_at=row.locked_at,
        last_error=row.last_error,
        dedupe_key=row.dedupe_key,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
