"""履约用例：支付成功后生成履约单，备货、模拟发货、确认收货。"""

from __future__ import annotations

import secrets

from app.application.ports.services import Clock, LogisticsPort, ShipmentError
from app.application.ports.uow import UowFactory
from app.domain.constants import FulfillmentStatus, OrderStatus
from app.domain.entities import Fulfillment, Order
from app.domain.errors import ConflictError, ExternalServiceError, NotFoundError
from app.domain.inventory import ensure_preparable, ensure_shippable
from app.domain.ordering import ensure_confirmable


class FulfillmentService:
    def __init__(self, uow_factory: UowFactory, clock: Clock, logistics: LogisticsPort) -> None:
        self._uow = uow_factory
        self._clock = clock
        self._logistics = logistics

    async def create_for_order(self, order_no: str) -> Fulfillment | None:
        async with self._uow() as uow:
            order = await uow.orders.get_by_no(order_no)
            if order is None or order.status not in (
                OrderStatus.PAID,
                OrderStatus.SHIPPED,
                OrderStatus.COMPLETED,
            ):
                return None
            existing = await uow.fulfillments.get_by_order(order.id)
            if existing is not None:
                return existing

            lines = await uow.orders.lines_of(order.id)
            record = await uow.fulfillments.create(
                Fulfillment(
                    id=0,
                    fulfillment_no=f"F{order.order_no[-10:]}{secrets.randbelow(100):02d}",
                    order_id=order.id,
                    order_no=order.order_no,
                    status=FulfillmentStatus.PENDING,
                    receiver=order.receiver,
                    phone=order.phone,
                    address_detail=order.address_detail,
                    items=[
                        {
                            "productName": line.product_name,
                            "specs": line.specs,
                            "quantity": line.quantity,
                        }
                        for line in lines
                    ],
                )
            )
            await uow.commit()
            return record

    async def prepare(self, fulfillment_no: str) -> Fulfillment:
        async with self._uow() as uow:
            record = await uow.fulfillments.get_by_no(fulfillment_no)
            if record is None:
                raise NotFoundError("履约单不存在")
            if record.status == FulfillmentStatus.READY_TO_SHIP:
                return record
            ensure_preparable(record.status)
            record.status = FulfillmentStatus.READY_TO_SHIP
            await uow.fulfillments.save(record)
            await uow.commit()
            return record

    async def ship(self, fulfillment_no: str, *, simulate: str = "SUCCESS") -> Fulfillment:
        async with self._uow() as uow:
            record = await uow.fulfillments.get_by_no(fulfillment_no)
            if record is None:
                raise NotFoundError("履约单不存在")
            ensure_shippable(record.status)

            record.attempts += 1
            try:
                tracking_no = await self._logistics.create_shipment(
                    record.order_no, simulate=simulate
                )
            except ShipmentError as exc:
                record.last_error = str(exc)[:255]
                await uow.fulfillments.save(record)
                await uow.commit()
                raise ExternalServiceError(
                    f"发货失败：{exc}（已记录第 {record.attempts} 次尝试，可重试）"
                ) from exc

            now = self._clock.now()
            changed = await uow.orders.transition(
                record.order_id,
                from_status=OrderStatus.PAID,
                to_status=OrderStatus.SHIPPED,
                fields={"shipped_at": now},
            )
            if not changed:
                await uow.rollback()
                raise ConflictError("订单状态已变化，发货失败")

            record.status = FulfillmentStatus.SHIPPED
            record.tracking_no = tracking_no
            record.last_error = ""
            record.shipped_at = now
            await uow.fulfillments.save(record)
            await uow.commit()
            return record

    async def confirm_receipt(self, user_id: int, order_no: str) -> Order:
        async with self._uow() as uow:
            order = await uow.orders.get_by_no(order_no)
            if order is None or order.user_id != user_id:
                raise NotFoundError("订单不存在")
            ensure_confirmable(order)
            if order.status == OrderStatus.COMPLETED:
                return order

            now = self._clock.now()
            changed = await uow.orders.transition(
                order.id,
                from_status=OrderStatus.SHIPPED,
                to_status=OrderStatus.COMPLETED,
                fields={"completed_at": now},
            )
            if not changed:
                await uow.rollback()
                raise ConflictError("订单状态已变化，请刷新后重试")

            record = await uow.fulfillments.get_by_order(order.id)
            if record is not None and record.status == FulfillmentStatus.SHIPPED:
                record.status = FulfillmentStatus.COMPLETED
                record.completed_at = now
                await uow.fulfillments.save(record)

            await uow.commit()
            order.status = OrderStatus.COMPLETED
            order.completed_at = now
            return order

    async def get_for_user(self, user_id: int, order_no: str) -> Fulfillment:
        async with self._uow() as uow:
            order = await uow.orders.get_by_no(order_no)
            if order is None or order.user_id != user_id:
                raise NotFoundError("订单不存在")
            record = await uow.fulfillments.get_by_order(order.id)
            if record is None:
                raise NotFoundError("该订单还没有履约记录")
            return record

    async def admin_list(
        self, *, page: int, page_size: int, status: str | None
    ) -> tuple[list[Fulfillment], int]:
        async with self._uow() as uow:
            return await uow.fulfillments.list(page=page, page_size=page_size, status=status)
