"""支付用例：调用网关、落支付记录、扣减库存、触发履约。

金额只从订单读，客户端传什么都不作数。
"""

from __future__ import annotations

from app.application.ports.services import Clock, PaymentGateway
from app.application.ports.uow import UowFactory
from app.domain.constants import InventoryChange, JobType, OrderStatus, PaymentStatus
from app.domain.entities import Payment
from app.domain.errors import ConflictError, NotFoundError
from app.domain.ordering import ensure_payable
from app.utils import new_id


class PaymentService:
    def __init__(self, uow_factory: UowFactory, clock: Clock, gateway: PaymentGateway) -> None:
        self._uow = uow_factory
        self._clock = clock
        self._gateway = gateway

    async def pay(self, user_id: int, order_no: str, *, result: str) -> Payment:
        async with self._uow() as uow:
            order = await uow.orders.get_by_no(order_no)
            if order is None or order.user_id != user_id:
                raise NotFoundError("订单不存在")
            ensure_payable(order)

            charge = await self._gateway.charge(
                order_no=order.order_no,
                amount_cents=order.total_amount_cents,
                simulate=result,
            )
            now = self._clock.now()

            if not charge.ok:
                payment = await uow.orders.add_payment(
                    Payment(
                        id=0,
                        payment_no=new_id("P"),
                        order_id=order.id,
                        order_no=order.order_no,
                        user_id=user_id,
                        amount_cents=order.total_amount_cents,
                        status=PaymentStatus.FAILED,
                        failure_reason=charge.failure_reason or "支付失败",
                    )
                )
                await uow.commit()
                return payment

            # 先抢订单状态，再扣库存；任何一步失败整体回滚
            changed = await uow.orders.transition(
                order.id,
                from_status=OrderStatus.PENDING_PAYMENT,
                to_status=OrderStatus.PAID,
                fields={"paid_at": now},
            )
            if not changed:
                await uow.rollback()
                raise ConflictError("订单已支付，不能重复支付")

            lines = await uow.orders.lines_of(order.id)
            for line in lines:
                ok = await uow.inventory.move(
                    line.sku_id,
                    line.quantity,
                    action=InventoryChange.DEDUCT,
                    order_no=order.order_no,
                    reason="支付成功扣减库存",
                )
                if not ok:
                    await uow.rollback()
                    raise ConflictError("库存占用记录异常，支付已回滚，请联系管理员")

            payment = await uow.orders.add_payment(
                Payment(
                    id=0,
                    payment_no=new_id("P"),
                    order_id=order.id,
                    order_no=order.order_no,
                    user_id=user_id,
                    amount_cents=order.total_amount_cents,
                    status=PaymentStatus.SUCCESS,
                    transaction_no=charge.transaction_no,
                    paid_at=now,
                )
            )
            await uow.jobs.enqueue(
                JobType.BUILD_FULFILLMENT,
                {"orderNo": order.order_no},
                dedupe_key=f"fulfill:{order.order_no}",
                delay_seconds=0,
                max_attempts=None,
            )
            await uow.commit()
            return payment

    async def list_for_order(self, user_id: int, order_no: str) -> list[Payment]:
        async with self._uow() as uow:
            order = await uow.orders.get_by_no(order_no)
            if order is None or order.user_id != user_id:
                raise NotFoundError("订单不存在")
            return await uow.orders.payments_of(order.id)
