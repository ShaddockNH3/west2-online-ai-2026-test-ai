"""履约：支付成功后生成履约单，备货、模拟发货、确认收货。"""

from __future__ import annotations

import secrets

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import FulfillmentStatus, OrderStatus
from app.core.errors import ConflictError, ExternalServiceError, NotFoundError
from app.mock_logistics import LogisticsError, create_shipment
from app.models import Fulfillment, Order, OrderItem
from app.utils import iso, utcnow


async def create_for_order(session: AsyncSession, order_no: str) -> Fulfillment | None:
    order = await session.scalar(select(Order).where(Order.order_no == order_no))
    if order is None or order.status not in (
        OrderStatus.PAID,
        OrderStatus.SHIPPED,
        OrderStatus.COMPLETED,
    ):
        return None
    existing = await session.scalar(select(Fulfillment).where(Fulfillment.order_id == order.id))
    if existing is not None:
        return existing
    items = list(await session.scalars(select(OrderItem).where(OrderItem.order_id == order.id)))
    fulfillment = Fulfillment(
        fulfillment_no=f"F{order.order_no[-10:]}{secrets.randbelow(100):02d}",
        order_id=order.id,
        order_no=order.order_no,
        status=FulfillmentStatus.PENDING,
        receiver=order.receiver,
        phone=order.phone,
        address_detail=order.address_detail,
        items=[
            {
                "productName": item.product_name,
                "specs": item.specs,
                "quantity": item.quantity,
            }
            for item in items
        ],
    )
    session.add(fulfillment)
    await session.commit()
    await session.refresh(fulfillment)
    return fulfillment


async def prepare(session: AsyncSession, fulfillment_no: str) -> Fulfillment:
    fulfillment = await _get_by_no(session, fulfillment_no)
    if fulfillment.status == FulfillmentStatus.READY_TO_SHIP:
        return fulfillment
    if fulfillment.status != FulfillmentStatus.PENDING:
        raise ConflictError("当前履约状态不能备货")
    fulfillment.status = FulfillmentStatus.READY_TO_SHIP
    fulfillment.updated_at = utcnow()
    await session.commit()
    await session.refresh(fulfillment)
    return fulfillment


async def ship(
    session: AsyncSession, fulfillment_no: str, *, simulate: str = "SUCCESS"
) -> Fulfillment:
    fulfillment = await _get_by_no(session, fulfillment_no)
    if fulfillment.status == FulfillmentStatus.SHIPPED:
        raise ConflictError("该履约单已发货")
    if fulfillment.status != FulfillmentStatus.READY_TO_SHIP:
        raise ConflictError("请先完成备货再发货")
    fulfillment.attempts += 1
    try:
        tracking_no = await create_shipment(fulfillment.order_no, simulate=simulate)
    except LogisticsError as exc:
        fulfillment.last_error = str(exc)[:255]
        fulfillment.updated_at = utcnow()
        await session.commit()
        raise ExternalServiceError(
            f"发货失败：{exc}（已记录第 {fulfillment.attempts} 次尝试，可重试）"
        ) from exc

    now = utcnow()
    fulfillment.status = FulfillmentStatus.SHIPPED
    fulfillment.tracking_no = tracking_no
    fulfillment.last_error = ""
    fulfillment.shipped_at = now
    fulfillment.updated_at = now
    result = await session.execute(
        update(Order)
        .where(Order.id == fulfillment.order_id, Order.status == OrderStatus.PAID)
        .values(status=OrderStatus.SHIPPED, shipped_at=now)
    )
    if result.rowcount != 1:
        await session.rollback()
        raise ConflictError("订单状态已变化，发货失败")
    await session.commit()
    await session.refresh(fulfillment)
    return fulfillment


async def confirm_receipt(session: AsyncSession, user_id: int, order_no: str) -> Order:
    order = await session.scalar(
        select(Order).where(Order.order_no == order_no, Order.user_id == user_id)
    )
    if order is None:
        raise NotFoundError("订单不存在")
    if order.status == OrderStatus.COMPLETED:
        return order
    if order.status != OrderStatus.SHIPPED:
        raise ConflictError("订单尚未发货，不能确认收货")
    now = utcnow()
    result = await session.execute(
        update(Order)
        .where(Order.id == order.id, Order.status == OrderStatus.SHIPPED)
        .values(status=OrderStatus.COMPLETED, completed_at=now)
    )
    if result.rowcount != 1:
        await session.rollback()
        raise ConflictError("订单状态已变化，请刷新后重试")
    fulfillment = await session.scalar(select(Fulfillment).where(Fulfillment.order_id == order.id))
    if fulfillment is not None and fulfillment.status == FulfillmentStatus.SHIPPED:
        fulfillment.status = FulfillmentStatus.COMPLETED
        fulfillment.completed_at = now
        fulfillment.updated_at = now
    await session.commit()
    await session.refresh(order)
    return order


async def get_for_user(session: AsyncSession, user_id: int, order_no: str) -> Fulfillment:
    order = await session.scalar(
        select(Order).where(Order.order_no == order_no, Order.user_id == user_id)
    )
    if order is None:
        raise NotFoundError("订单不存在")
    fulfillment = await session.scalar(select(Fulfillment).where(Fulfillment.order_id == order.id))
    if fulfillment is None:
        raise NotFoundError("该订单还没有履约记录")
    return fulfillment


async def list_admin(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    status: str | None = None,
) -> tuple[list[dict], int]:
    conditions = []
    if status:
        conditions.append(Fulfillment.status == status)
    total = await session.scalar(select(func.count(Fulfillment.id)).where(*conditions)) or 0
    rows = await session.scalars(
        select(Fulfillment)
        .where(*conditions)
        .order_by(Fulfillment.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return [public_fulfillment(row) for row in rows], int(total)


async def _get_by_no(session: AsyncSession, fulfillment_no: str) -> Fulfillment:
    fulfillment = await session.scalar(
        select(Fulfillment).where(Fulfillment.fulfillment_no == fulfillment_no)
    )
    if fulfillment is None:
        raise NotFoundError("履约单不存在")
    return fulfillment


def public_fulfillment(fulfillment: Fulfillment) -> dict:
    return {
        "fulfillmentNo": fulfillment.fulfillment_no,
        "orderNo": fulfillment.order_no,
        "status": fulfillment.status,
        "receiver": fulfillment.receiver,
        "phone": fulfillment.phone,
        "addressDetail": fulfillment.address_detail,
        "items": fulfillment.items,
        "trackingNo": fulfillment.tracking_no or None,
        "attempts": fulfillment.attempts,
        "lastError": fulfillment.last_error or None,
        "shippedAt": iso(fulfillment.shipped_at),
        "completedAt": iso(fulfillment.completed_at),
        "createdAt": iso(fulfillment.created_at),
        "updatedAt": iso(fulfillment.updated_at),
    }
