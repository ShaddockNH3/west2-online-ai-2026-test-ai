"""订单与支付的 SQLAlchemy 实现。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import AdminOrderRow, Order, OrderLine, Payment
from app.domain.errors import DuplicateRequestError, NotFoundError
from app.infrastructure.persistence.mappers import to_order, to_order_line, to_payment
from app.infrastructure.persistence.models import Order as OrderRow
from app.infrastructure.persistence.models import OrderItem as OrderItemRow
from app.infrastructure.persistence.models import Payment as PaymentRow
from app.infrastructure.persistence.models import User as UserRow


class SqlOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, order: Order, lines: list[OrderLine]) -> Order:
        row = OrderRow(
            order_no=order.order_no,
            user_id=order.user_id,
            status=order.status,
            original_amount_cents=order.original_amount_cents,
            discount_amount_cents=order.discount_amount_cents,
            total_amount_cents=order.total_amount_cents,
            receiver=order.receiver,
            phone=order.phone,
            address_detail=order.address_detail,
            request_id=order.request_id,
            request_fingerprint=order.request_fingerprint,
            remark=order.remark,
            expire_at=order.expire_at,
        )
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            # (user_id, request_id) 唯一索引：并发重放同一请求
            raise DuplicateRequestError("同一 requestId 已提交过") from exc

        for line in lines:
            self._session.add(
                OrderItemRow(
                    order_id=row.id,
                    sku_id=line.sku_id,
                    product_id=line.product_id,
                    product_name=line.product_name,
                    specs=line.specs,
                    original_unit_price_cents=line.original_unit_price_cents,
                    unit_price_cents=line.unit_price_cents,
                    quantity=line.quantity,
                    subtotal_cents=line.subtotal_cents,
                    discount_cents=line.discount_cents,
                    activity_name=line.activity_name,
                )
            )
        await self._session.flush()
        return to_order(row)

    async def find_by_request_id(self, user_id: int, request_id: str) -> Order | None:
        row = await self._session.scalar(
            select(OrderRow).where(OrderRow.user_id == user_id, OrderRow.request_id == request_id)
        )
        return to_order(row) if row else None

    async def get_by_no(self, order_no: str) -> Order | None:
        row = await self._session.scalar(select(OrderRow).where(OrderRow.order_no == order_no))
        return to_order(row) if row else None

    async def list_for_user(
        self, user_id: int, *, page: int, page_size: int, status: str | None
    ) -> tuple[list[Order], int]:
        conditions = [OrderRow.user_id == user_id]
        if status:
            conditions.append(OrderRow.status == status)
        total = await self._session.scalar(select(func.count(OrderRow.id)).where(*conditions))
        rows = await self._session.scalars(
            select(OrderRow)
            .where(*conditions)
            .order_by(OrderRow.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        return [to_order(row) for row in rows], int(total or 0)

    async def admin_list(
        self, *, page: int, page_size: int, status: str | None, keyword: str | None
    ) -> tuple[list[AdminOrderRow], int]:
        conditions = []
        if status:
            conditions.append(OrderRow.status == status)
        if keyword:
            conditions.append(OrderRow.order_no.like(f"%{keyword.strip()}%"))
        total = await self._session.scalar(select(func.count(OrderRow.id)).where(*conditions))
        rows = (
            await self._session.execute(
                select(OrderRow, UserRow.username)
                .join(UserRow, UserRow.id == OrderRow.user_id)
                .where(*conditions)
                .order_by(OrderRow.id.desc())
                .limit(page_size)
                .offset((page - 1) * page_size)
            )
        ).all()
        return [AdminOrderRow(order=to_order(order), username=name) for order, name in rows], int(
            total or 0
        )

    async def item_counts(self, order_ids: list[int]) -> dict[int, int]:
        if not order_ids:
            return {}
        rows = await self._session.execute(
            select(OrderItemRow.order_id, func.count(OrderItemRow.id))
            .where(OrderItemRow.order_id.in_(order_ids))
            .group_by(OrderItemRow.order_id)
        )
        return {int(order_id): int(count) for order_id, count in rows.all()}

    async def lines_of(self, order_id: int) -> list[OrderLine]:
        rows = await self._session.scalars(
            select(OrderItemRow).where(OrderItemRow.order_id == order_id).order_by(OrderItemRow.id)
        )
        return [to_order_line(row) for row in rows]

    async def payments_of(self, order_id: int) -> list[Payment]:
        rows = await self._session.scalars(
            select(PaymentRow).where(PaymentRow.order_id == order_id).order_by(PaymentRow.id.desc())
        )
        return [to_payment(row) for row in rows]

    async def add_payment(self, payment: Payment) -> Payment:
        row = PaymentRow(
            payment_no=payment.payment_no,
            order_id=payment.order_id,
            order_no=payment.order_no,
            user_id=payment.user_id,
            amount_cents=payment.amount_cents,
            status=payment.status,
            channel=payment.channel,
            transaction_no=payment.transaction_no,
            failure_reason=payment.failure_reason,
            paid_at=payment.paid_at,
        )
        self._session.add(row)
        await self._session.flush()
        return to_payment(row)

    async def transition(
        self,
        order_id: int,
        *,
        from_status: str,
        to_status: str,
        fields: dict[str, Any],
    ) -> bool:
        result = await self._session.execute(
            update(OrderRow)
            .where(OrderRow.id == order_id, OrderRow.status == from_status)
            .values(status=to_status, **fields)
        )
        return result.rowcount == 1

    async def paid_amount(self) -> int:
        total = await self._session.scalar(
            select(func.coalesce(func.sum(OrderRow.total_amount_cents), 0)).where(
                OrderRow.status.in_(["PAID", "SHIPPED", "COMPLETED"])
            )
        )
        return int(total or 0)

    async def count_by_status(self) -> dict[str, int]:
        rows = await self._session.execute(
            select(OrderRow.status, func.count(OrderRow.id)).group_by(OrderRow.status)
        )
        return {status: int(count) for status, count in rows.all()}

    async def get_row(self, order_id: int) -> Order:
        row = await self._session.get(OrderRow, order_id)
        if row is None:
            raise NotFoundError("订单不存在")
        return to_order(row)
