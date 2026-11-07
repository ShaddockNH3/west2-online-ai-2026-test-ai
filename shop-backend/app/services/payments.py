"""mock 支付。金额只从订单读，成功后同一订单不会再有第二笔成功记录。"""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import JobType, OrderStatus, PaymentStatus
from app.core.errors import ConflictError
from app.models import Order, OrderItem, Payment
from app.services import inventory as inventory_service
from app.services import jobs
from app.services.orders import get_order
from app.utils import iso, new_id, utcnow, yuan


async def pay(session: AsyncSession, user_id: int, order_no: str, result: str) -> dict:
    order = await get_order(session, order_no, user_id=user_id)
    if order.status == OrderStatus.CANCELLED:
        raise ConflictError("订单已取消，不能支付")
    if order.status != OrderStatus.PENDING_PAYMENT:
        raise ConflictError("订单已支付，不能重复支付")

    now = utcnow()
    if result == "FAILURE":
        payment = Payment(
            payment_no=new_id("P"),
            order_id=order.id,
            order_no=order.order_no,
            user_id=user_id,
            amount_cents=order.total_amount_cents,
            status=PaymentStatus.FAILED,
            failure_reason="模拟支付失败",
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return public_payment(payment)

    # 成功支付：先抢占订单状态，再扣库存，任何一步失败整体回滚
    changed = await session.execute(
        update(Order)
        .where(Order.id == order.id, Order.status == OrderStatus.PENDING_PAYMENT)
        .values(status=OrderStatus.PAID, paid_at=now)
    )
    if changed.rowcount != 1:
        await session.rollback()
        existing = await _success_payment(session, order.id)
        if existing is not None:
            raise ConflictError("订单已支付，不能重复支付")
        raise ConflictError("订单状态已变化，请刷新后重试")

    items = list(await session.scalars(select(OrderItem).where(OrderItem.order_id == order.id)))
    for item in items:
        ok = await inventory_service.deduct(
            session,
            item.sku_id,
            item.quantity,
            order_no=order.order_no,
            reason="支付成功扣减库存",
        )
        if not ok:
            await session.rollback()
            raise ConflictError("库存占用记录异常，支付已回滚，请联系管理员")

    payment = Payment(
        payment_no=new_id("P"),
        order_id=order.id,
        order_no=order.order_no,
        user_id=user_id,
        amount_cents=order.total_amount_cents,
        status=PaymentStatus.SUCCESS,
        transaction_no=new_id("MOCK"),
        paid_at=now,
    )
    session.add(payment)
    await jobs.enqueue(
        session,
        JobType.BUILD_FULFILLMENT,
        {"orderNo": order.order_no},
        dedupe_key=f"fulfill:{order.order_no}",
    )
    await session.commit()
    await session.refresh(payment)
    return public_payment(payment)


async def list_payments(session: AsyncSession, user_id: int, order_no: str) -> list[dict]:
    order = await get_order(session, order_no, user_id=user_id)
    rows = await session.scalars(
        select(Payment).where(Payment.order_id == order.id).order_by(Payment.id.desc())
    )
    return [public_payment(payment) for payment in rows]


async def _success_payment(session: AsyncSession, order_id: int) -> Payment | None:
    return await session.scalar(
        select(Payment).where(Payment.order_id == order_id, Payment.status == PaymentStatus.SUCCESS)
    )


def public_payment(payment: Payment) -> dict:
    return {
        "paymentNo": payment.payment_no,
        "orderNo": payment.order_no,
        "amount": yuan(payment.amount_cents),
        "status": payment.status,
        "channel": payment.channel,
        "transactionNo": payment.transaction_no or None,
        "failureReason": payment.failure_reason or None,
        "createdAt": iso(payment.created_at),
        "paidAt": iso(payment.paid_at),
    }
