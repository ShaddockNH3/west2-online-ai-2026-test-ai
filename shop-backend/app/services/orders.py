"""订单：结算预览、创建（幂等 + 事务 + 快照）、查询与取消。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import JobType, OrderStatus, ProductStatus
from app.core.config import get_settings
from app.core.errors import ConflictError, NotFoundError, StockError, ValidationError
from app.models import (
    Address,
    CartItem,
    Fulfillment,
    Order,
    OrderItem,
    Payment,
    Product,
    Sku,
    User,
)
from app.services import inventory as inventory_service
from app.services import jobs
from app.services.pricing import active_rules, resolve_price
from app.utils import iso, utcnow, yuan
from app.utils import order_no as new_order_no

ORDER_STATUSES = {
    OrderStatus.PENDING_PAYMENT,
    OrderStatus.PAID,
    OrderStatus.SHIPPED,
    OrderStatus.COMPLETED,
    OrderStatus.CANCELLED,
}


@dataclass(slots=True)
class Line:
    sku_id: int
    product_id: int
    product_name: str
    specs: dict
    quantity: int
    unit_price: int
    original_price: int
    activity_name: str
    cart_item_id: int | None = None
    purchasable: bool = True
    unavailable_reason: str = ""


@dataclass(slots=True)
class LineInput:
    sku_id: int
    quantity: int
    cart_item_id: int | None = None


def fingerprint_of(cart_item_ids: list[int], address_id: int) -> str:
    raw = f"{sorted(cart_item_ids)}|{address_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def _load_cart_inputs(
    session: AsyncSession, user_id: int, cart_item_ids: list[int]
) -> list[LineInput]:
    rows = list(
        await session.scalars(
            select(CartItem).where(CartItem.user_id == user_id, CartItem.id.in_(cart_item_ids))
        )
    )
    if len(rows) != len(set(cart_item_ids)):
        raise ValidationError("购物车项不存在或不属于当前用户")
    order_index = {item_id: index for index, item_id in enumerate(cart_item_ids)}
    rows.sort(key=lambda item: order_index.get(item.id, 0))
    return [
        LineInput(sku_id=item.sku_id, quantity=item.quantity, cart_item_id=item.id) for item in rows
    ]


async def build_lines(
    session: AsyncSession, inputs: list[LineInput], *, strict: bool
) -> list[Line]:
    """按当前商品状态与活动价重新计价，绝不使用客户端传来的价格。"""
    if not inputs:
        raise ValidationError("请选择要结算的商品")
    sku_ids = [item.sku_id for item in inputs]
    rows = await session.execute(
        select(Sku, Product).join(Product, Product.id == Sku.product_id).where(Sku.id.in_(sku_ids))
    )
    mapping = {sku.id: (sku, product) for sku, product in rows.all()}
    rules = await active_rules(session, sku_ids)
    stock = await inventory_service.available_map(session, sku_ids)

    lines: list[Line] = []
    for item in inputs:
        sku, product = mapping.get(item.sku_id, (None, None))
        if sku is None or product is None:
            raise NotFoundError(f"SKU {item.sku_id} 不存在")
        if item.quantity <= 0:
            raise ValidationError("购买数量必须是正整数")
        issue = ""
        if product.status != ProductStatus.ON_SALE:
            issue = "商品已下架"
        elif sku.status != "ON_SALE":
            issue = "所选规格已下架"
        elif stock.get(sku.id, 0) < item.quantity:
            issue = f"库存不足，当前仅剩 {stock.get(sku.id, 0)} 件"
        if issue and strict:
            raise (
                StockError(f"「{product.name}」{issue}")
                if "库存" in issue
                else ConflictError(f"「{product.name}」{issue}")
            )
        unit_price, original_price, activity_name = resolve_price(sku, rules.get(sku.id))
        lines.append(
            Line(
                sku_id=sku.id,
                product_id=product.id,
                product_name=product.name,
                specs=dict(sku.specs or {}),
                quantity=item.quantity,
                unit_price=unit_price,
                original_price=original_price,
                activity_name=activity_name,
                cart_item_id=item.cart_item_id,
                purchasable=not issue,
                unavailable_reason=issue,
            )
        )
    return lines


def totals(lines: list[Line], *, only_purchasable: bool = False) -> tuple[int, int, int]:
    selected = [line for line in lines if line.purchasable] if only_purchasable else lines
    original = sum(line.original_price * line.quantity for line in selected)
    total = sum(line.unit_price * line.quantity for line in selected)
    return original, total, original - total


def _line_view(line: Line) -> dict:
    return {
        "skuId": line.sku_id,
        "productId": line.product_id,
        "productName": line.product_name,
        "specs": line.specs,
        "quantity": line.quantity,
        "unitPrice": yuan(line.unit_price),
        "originalUnitPrice": yuan(line.original_price),
        "subtotal": yuan(line.unit_price * line.quantity),
        "discount": yuan((line.original_price - line.unit_price) * line.quantity),
        "activityName": line.activity_name or None,
        "purchasable": line.purchasable,
        "issue": line.unavailable_reason or None,
    }


async def preview(
    session: AsyncSession, user_id: int, cart_item_ids: list[int], address_id: int
) -> dict:
    address = await _owned_address(session, user_id, address_id)
    inputs = await _load_cart_inputs(session, user_id, cart_item_ids)
    lines = await build_lines(session, inputs, strict=False)
    original, total, discount = totals(lines, only_purchasable=True)
    return {
        "items": [_line_view(line) for line in lines],
        "originalAmount": yuan(original),
        "discountAmount": yuan(discount),
        "totalAmount": yuan(total),
        "issues": [
            {"productName": line.product_name, "reason": line.unavailable_reason}
            for line in lines
            if not line.purchasable
        ],
        "address": {
            "id": address.id,
            "receiver": address.receiver,
            "phone": address.phone,
            "detail": address.detail,
        },
        "priceLocked": False,
        "note": "预览不锁定价格与库存，提交订单时按当时状态重新计算",
    }


async def create_order(
    session: AsyncSession,
    user_id: int,
    cart_item_ids: list[int],
    address_id: int,
    request_id: str,
    remark: str = "",
) -> tuple[Order, bool]:
    """返回 (订单, 是否新建)。同一 requestId 重试返回同一订单。"""
    fingerprint = fingerprint_of(cart_item_ids, address_id)
    existing = await _find_by_request(session, user_id, request_id)
    if existing is not None:
        if existing.request_fingerprint != fingerprint:
            raise ConflictError("requestId 已用于另一次下单，请换一个新的标识")
        return existing, False

    address = await _owned_address(session, user_id, address_id)
    inputs = await _load_cart_inputs(session, user_id, cart_item_ids)
    lines = await build_lines(session, inputs, strict=True)
    return await persist_order(
        session,
        user_id=user_id,
        lines=lines,
        address=address,
        request_id=request_id,
        fingerprint=fingerprint,
        remark=remark,
        reserve_stock=True,
        clear_cart=True,
    )


async def persist_order(
    session: AsyncSession,
    *,
    user_id: int,
    lines: list[Line],
    address: Address,
    request_id: str,
    fingerprint: str,
    remark: str = "",
    reserve_stock: bool,
    clear_cart: bool,
    activity_name: str = "",
) -> tuple[Order, bool]:
    settings = get_settings()
    now = utcnow()
    original, total, discount = totals(lines)
    order = Order(
        order_no=_generate_order_no(),
        user_id=user_id,
        status=OrderStatus.PENDING_PAYMENT,
        original_amount_cents=original,
        discount_amount_cents=discount,
        total_amount_cents=total,
        receiver=address.receiver,
        phone=address.phone,
        address_detail=address.detail,
        request_id=request_id,
        request_fingerprint=fingerprint,
        remark=remark,
        expire_at=now + timedelta(minutes=settings.order_expire_minutes),
    )
    session.add(order)
    await session.flush()

    if reserve_stock:
        for line in lines:
            ok = await inventory_service.reserve(
                session,
                line.sku_id,
                line.quantity,
                order_no=order.order_no,
                reason="下单占用库存",
            )
            if not ok:
                raise StockError(f"「{line.product_name}」库存不足")

    for line in lines:
        session.add(
            OrderItem(
                order_id=order.id,
                sku_id=line.sku_id,
                product_id=line.product_id,
                product_name=line.product_name,
                specs=line.specs,
                original_unit_price_cents=line.original_price,
                unit_price_cents=line.unit_price,
                quantity=line.quantity,
                subtotal_cents=line.unit_price * line.quantity,
                discount_cents=(line.original_price - line.unit_price) * line.quantity,
                activity_name=line.activity_name or activity_name,
            )
        )

    if clear_cart:
        cart_ids = [line.cart_item_id for line in lines if line.cart_item_id is not None]
        if cart_ids:
            await session.execute(delete(CartItem).where(CartItem.id.in_(cart_ids)))

    await jobs.enqueue(
        session,
        JobType.CLOSE_EXPIRED_ORDER,
        {"orderNo": order.order_no},
        dedupe_key=f"close:{order.order_no}",
        delay_seconds=settings.order_expire_minutes * 60,
    )
    await jobs.enqueue(
        session,
        JobType.SEND_ORDER_NOTIFICATION,
        {"orderNo": order.order_no, "userId": user_id},
        dedupe_key=f"notify:{order.order_no}",
    )

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        replay = await _find_by_request(session, user_id, request_id)
        if replay is not None and replay.request_fingerprint == fingerprint:
            return replay, False
        raise ConflictError("下单失败，请重试") from exc
    await session.refresh(order)
    return order, True


async def list_orders(
    session: AsyncSession,
    user_id: int,
    *,
    page: int,
    page_size: int,
    status: str | None = None,
) -> tuple[list[dict], int]:
    conditions = [Order.user_id == user_id]
    if status:
        if status not in ORDER_STATUSES:
            raise ValidationError("订单状态不合法")
        conditions.append(Order.status == status)
    total = await session.scalar(select(func.count(Order.id)).where(*conditions)) or 0
    rows = list(
        await session.scalars(
            select(Order)
            .where(*conditions)
            .order_by(Order.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
    )
    counts = await _item_counts(session, [order.id for order in rows])
    return [summary(order, counts.get(order.id, 0)) for order in rows], int(total)


async def admin_list_orders(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    status: str | None = None,
    keyword: str | None = None,
) -> tuple[list[dict], int]:
    conditions = []
    if status:
        if status not in ORDER_STATUSES:
            raise ValidationError("订单状态不合法")
        conditions.append(Order.status == status)
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(Order.order_no.like(like))
    total = await session.scalar(select(func.count(Order.id)).where(*conditions)) or 0
    rows = (
        await session.execute(
            select(Order, User.username)
            .join(User, User.id == Order.user_id)
            .where(*conditions)
            .order_by(Order.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
    ).all()
    counts = await _item_counts(session, [order.id for order, _ in rows])
    items = [
        {**summary(order, counts.get(order.id, 0)), "username": username}
        for order, username in rows
    ]
    return items, int(total)


async def _item_counts(session: AsyncSession, order_ids: list[int]) -> dict[int, int]:
    if not order_ids:
        return {}
    rows = await session.execute(
        select(OrderItem.order_id, func.count(OrderItem.id))
        .where(OrderItem.order_id.in_(order_ids))
        .group_by(OrderItem.order_id)
    )
    return {int(order_id): int(count) for order_id, count in rows.all()}


def summary(order: Order, item_count: int = 0) -> dict:
    return {
        "orderNo": order.order_no,
        "status": order.status,
        "totalAmount": yuan(order.total_amount_cents),
        "originalAmount": yuan(order.original_amount_cents),
        "discountAmount": yuan(order.discount_amount_cents),
        "itemCount": item_count,
        "createdAt": iso(order.created_at),
        "paidAt": iso(order.paid_at),
        "expireAt": iso(order.expire_at),
        "receiver": order.receiver,
    }


async def get_order(session: AsyncSession, order_no: str, *, user_id: int | None = None) -> Order:
    order = await session.scalar(select(Order).where(Order.order_no == order_no))
    if order is None:
        raise NotFoundError("订单不存在")
    if user_id is not None and order.user_id != user_id:
        raise NotFoundError("订单不存在")
    return order


async def detail(session: AsyncSession, order: Order) -> dict:
    items = list(
        await session.scalars(
            select(OrderItem).where(OrderItem.order_id == order.id).order_by(OrderItem.id)
        )
    )
    payments = list(
        await session.scalars(
            select(Payment).where(Payment.order_id == order.id).order_by(Payment.id.desc())
        )
    )
    fulfillment = await session.scalar(select(Fulfillment).where(Fulfillment.order_id == order.id))
    return {
        "orderNo": order.order_no,
        "status": order.status,
        "originalAmount": yuan(order.original_amount_cents),
        "discountAmount": yuan(order.discount_amount_cents),
        "totalAmount": yuan(order.total_amount_cents),
        "receiver": order.receiver,
        "phone": order.phone,
        "addressDetail": order.address_detail,
        "remark": order.remark,
        "createdAt": iso(order.created_at),
        "paidAt": iso(order.paid_at),
        "shippedAt": iso(order.shipped_at),
        "completedAt": iso(order.completed_at),
        "cancelledAt": iso(order.cancelled_at),
        "cancelReason": order.cancel_reason or None,
        "expireAt": iso(order.expire_at),
        "items": [
            {
                "productName": item.product_name,
                "skuId": item.sku_id,
                "specs": item.specs,
                "quantity": item.quantity,
                "unitPrice": yuan(item.unit_price_cents),
                "originalUnitPrice": yuan(item.original_unit_price_cents),
                "subtotal": yuan(item.subtotal_cents),
                "discount": yuan(item.discount_cents),
                "activityName": item.activity_name or None,
            }
            for item in items
        ],
        "payments": [
            {
                "paymentNo": payment.payment_no,
                "amount": yuan(payment.amount_cents),
                "status": payment.status,
                "channel": payment.channel,
                "transactionNo": payment.transaction_no or None,
                "failureReason": payment.failure_reason or None,
                "createdAt": iso(payment.created_at),
                "paidAt": iso(payment.paid_at),
            }
            for payment in payments
        ],
        "fulfillment": _fulfillment_view(fulfillment) if fulfillment else None,
    }


def _fulfillment_view(fulfillment: Fulfillment) -> dict:
    return {
        "fulfillmentNo": fulfillment.fulfillment_no,
        "status": fulfillment.status,
        "trackingNo": fulfillment.tracking_no or None,
        "attempts": fulfillment.attempts,
        "lastError": fulfillment.last_error or None,
        "shippedAt": iso(fulfillment.shipped_at),
        "completedAt": iso(fulfillment.completed_at),
    }


async def cancel_order(
    session: AsyncSession, user_id: int, order_no: str, *, reason: str = "USER_CANCELLED"
) -> Order:
    order = await get_order(session, order_no, user_id=user_id)
    if order.status != OrderStatus.PENDING_PAYMENT:
        raise ConflictError("只有待支付订单可以取消")
    result = await session.execute(
        update(Order)
        .where(Order.id == order.id, Order.status == OrderStatus.PENDING_PAYMENT)
        .values(status=OrderStatus.CANCELLED, cancelled_at=utcnow(), cancel_reason=reason)
    )
    if result.rowcount != 1:
        await session.rollback()
        raise ConflictError("订单状态已变化，请刷新后重试")
    await _release_items(session, order, reason="取消订单释放库存")
    await session.commit()
    await session.refresh(order)
    return order


async def close_if_expired(session: AsyncSession, order_no: str) -> bool:
    order = await session.scalar(select(Order).where(Order.order_no == order_no))
    if order is None or order.status != OrderStatus.PENDING_PAYMENT:
        return False
    if order.expire_at > utcnow():
        return False
    result = await session.execute(
        update(Order)
        .where(Order.id == order.id, Order.status == OrderStatus.PENDING_PAYMENT)
        .values(status=OrderStatus.CANCELLED, cancelled_at=utcnow(), cancel_reason="EXPIRED")
    )
    if result.rowcount != 1:
        await session.rollback()
        return False
    await _release_items(session, order, reason="超时未支付关闭订单")
    await session.commit()
    return True


async def _release_items(session: AsyncSession, order: Order, *, reason: str) -> None:
    items = list(await session.scalars(select(OrderItem).where(OrderItem.order_id == order.id)))
    for item in items:
        ok = await inventory_service.release(
            session, item.sku_id, item.quantity, order_no=order.order_no, reason=reason
        )
        if not ok:
            raise ConflictError(f"订单 {order.order_no} 的库存释放失败，请检查库存占用记录")


async def _owned_address(session: AsyncSession, user_id: int, address_id: int) -> Address:
    address = await session.scalar(
        select(Address).where(Address.id == address_id, Address.user_id == user_id)
    )
    if address is None:
        raise NotFoundError("收货地址不存在")
    return address


async def _find_by_request(session: AsyncSession, user_id: int, request_id: str) -> Order | None:
    return await session.scalar(
        select(Order).where(Order.user_id == user_id, Order.request_id == request_id)
    )


def _generate_order_no() -> str:
    """时间戳 + 随机后缀；真正的唯一性由 orders.order_no 唯一索引保证。"""
    return new_order_no()
