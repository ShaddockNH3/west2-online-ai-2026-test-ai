"""订单用例：结算预览、下单（幂等 + 快照 + 事务）、查询与取消。"""

from __future__ import annotations

from datetime import timedelta

from app.application.ports.services import Clock
from app.application.ports.uow import UowFactory
from app.application.read_models import OrderDetail, OrderPreview, PreviewLine
from app.core.config import get_settings
from app.domain.constants import InventoryChange, JobType, OrderStatus
from app.domain.entities import Address, AdminOrderRow, Order, OrderLine
from app.domain.errors import (
    ConflictError,
    DuplicateRequestError,
    NotFoundError,
    StockError,
    ValidationError,
)
from app.domain.ordering import (
    PricedLine,
    ensure_cancellable,
    evaluate_line,
    fingerprint_of,
    totals,
)
from app.utils import order_no as new_order_no

ORDER_STATUSES = {
    OrderStatus.PENDING_PAYMENT,
    OrderStatus.PAID,
    OrderStatus.SHIPPED,
    OrderStatus.COMPLETED,
    OrderStatus.CANCELLED,
}


class OrderService:
    def __init__(self, uow_factory: UowFactory, clock: Clock) -> None:
        self._uow = uow_factory
        self._clock = clock

    # ---------- 计价 ----------

    async def _address(self, uow, user_id: int, address_id: int) -> Address:
        address = await uow.addresses.get_owned(address_id, user_id)
        if address is None:
            raise NotFoundError("收货地址不存在")
        return address

    async def _priced_lines(
        self, uow, inputs: list[tuple[int, int, int | None]], *, strict: bool
    ) -> list[PricedLine]:
        if not inputs:
            raise ValidationError("请选择要结算的商品")
        sku_ids = [sku_id for sku_id, _, _ in inputs]
        pairs = await uow.catalog.get_skus_with_products(sku_ids)
        mapping = {sku.id: (sku, product) for sku, product in pairs}
        rules = await uow.activities.active_rules(sku_ids, now=self._clock.now())
        stock = await uow.inventory.available_map(sku_ids)

        lines: list[PricedLine] = []
        for sku_id, quantity, cart_item_id in inputs:
            sku, product = mapping.get(sku_id, (None, None))
            if sku is None or product is None:
                raise NotFoundError(f"SKU {sku_id} 不存在")
            lines.append(
                evaluate_line(
                    sku=sku,
                    product_status=product.status,
                    product_name=product.name,
                    product_id=product.id,
                    quantity=quantity,
                    rule=rules.get(sku_id),
                    available=stock.get(sku_id, 0),
                    strict=strict,
                    cart_item_id=cart_item_id,
                )
            )
        return lines

    async def _cart_inputs(self, uow, user_id: int, item_ids: list[int]):
        items = await uow.cart.get_by_ids(user_id, item_ids)
        if len(items) != len(set(item_ids)):
            raise ValidationError("购物车项不存在或不属于当前用户")
        order_index = {item_id: index for index, item_id in enumerate(item_ids)}
        items.sort(key=lambda item: order_index.get(item.id, 0))
        return [(item.sku_id, item.quantity, item.id) for item in items]

    # ---------- 预览 ----------

    async def preview(
        self, user_id: int, *, cart_item_ids: list[int], address_id: int
    ) -> OrderPreview:
        async with self._uow() as uow:
            address = await self._address(uow, user_id, address_id)
            inputs = await self._cart_inputs(uow, user_id, cart_item_ids)
            lines = await self._priced_lines(uow, inputs, strict=False)

        original, total, discount = totals(lines, only_purchasable=True)
        return OrderPreview(
            items=[
                PreviewLine(
                    sku_id=line.sku_id,
                    product_id=line.product_id,
                    product_name=line.product_name,
                    specs=line.specs,
                    quantity=line.quantity,
                    unit_price_cents=line.quote.unit_cents,
                    original_unit_price_cents=line.quote.original_cents,
                    activity_name=line.quote.activity_name,
                    purchasable=line.purchasable,
                    issue=line.issue_text if not line.purchasable else "",
                    subtotal_cents=line.subtotal_cents,
                    discount_cents=line.quote.discount_cents * line.quantity,
                )
                for line in lines
            ],
            original_amount_cents=original,
            discount_amount_cents=discount,
            total_amount_cents=total,
            issues=[(line.product_name, line.issue_text) for line in lines if not line.purchasable],
            address=address,
        )

    # ---------- 下单 ----------

    async def create(
        self,
        user_id: int,
        *,
        cart_item_ids: list[int],
        address_id: int,
        request_id: str,
        remark: str = "",
    ) -> tuple[Order, bool]:
        fingerprint = fingerprint_of(cart_item_ids, address_id)
        async with self._uow() as uow:
            existing = await uow.orders.find_by_request_id(user_id, request_id)
            if existing is not None:
                if existing.request_fingerprint != fingerprint:
                    raise ConflictError("requestId 已用于另一次下单，请换一个新的标识")
                return existing, False

            address = await self._address(uow, user_id, address_id)
            inputs = await self._cart_inputs(uow, user_id, cart_item_ids)
            lines = await self._priced_lines(uow, inputs, strict=True)
            try:
                order = await self._persist(
                    uow,
                    user_id=user_id,
                    lines=lines,
                    address=address,
                    request_id=request_id,
                    fingerprint=fingerprint,
                    remark=remark,
                    reserve_stock=True,
                    clear_cart=True,
                )
                await uow.commit()
            except DuplicateRequestError as exc:
                # 并发重放：唯一索引拦下来了，回头再查一次原订单
                await uow.rollback()
                replay = await uow.orders.find_by_request_id(user_id, request_id)
                if replay is not None and replay.request_fingerprint == fingerprint:
                    return replay, False
                raise ConflictError("下单失败，请重试") from exc
            return order, True

    async def create_from_flash_sale(
        self,
        *,
        user_id: int,
        lines: list[PricedLine],
        address: Address,
        request_id: str,
        fingerprint: str,
        remark: str,
    ) -> Order:
        """抢购建单：库存已经在抢购时占用，这里只落订单，不再二次占库存。"""
        async with self._uow() as uow:
            order = await self._persist(
                uow,
                user_id=user_id,
                lines=lines,
                address=address,
                request_id=request_id,
                fingerprint=fingerprint,
                remark=remark,
                reserve_stock=False,
                clear_cart=False,
            )
            await uow.commit()
            return order

    async def _persist(
        self,
        uow,
        *,
        user_id: int,
        lines: list[PricedLine],
        address: Address,
        request_id: str,
        fingerprint: str,
        remark: str,
        reserve_stock: bool,
        clear_cart: bool,
    ) -> Order:
        settings = get_settings()
        now = self._clock.now()
        original, total, discount = totals(lines)
        order = await uow.orders.create(
            Order(
                id=0,
                order_no=new_order_no(),
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
            ),
            [
                OrderLine(
                    sku_id=line.sku_id,
                    product_id=line.product_id,
                    product_name=line.product_name,
                    specs=line.specs,
                    quantity=line.quantity,
                    unit_price_cents=line.quote.unit_cents,
                    original_unit_price_cents=line.quote.original_cents,
                    activity_name=line.quote.activity_name,
                )
                for line in lines
            ],
        )

        if reserve_stock:
            for line in lines:
                ok = await uow.inventory.move(
                    line.sku_id,
                    line.quantity,
                    action=InventoryChange.RESERVE,
                    order_no=order.order_no,
                    reason="下单占用库存",
                )
                if not ok:
                    raise StockError(f"「{line.product_name}」库存不足")

        if clear_cart:
            cart_ids = [line.cart_item_id for line in lines if line.cart_item_id is not None]
            await uow.cart.delete_many(cart_ids)

        await uow.jobs.enqueue(
            JobType.CLOSE_EXPIRED_ORDER,
            {"orderNo": order.order_no},
            dedupe_key=f"close:{order.order_no}",
            delay_seconds=settings.order_expire_minutes * 60,
            max_attempts=settings.job_max_attempts,
        )
        await uow.jobs.enqueue(
            JobType.SEND_ORDER_NOTIFICATION,
            {"orderNo": order.order_no, "userId": user_id},
            dedupe_key=f"notify:{order.order_no}",
            delay_seconds=0,
            max_attempts=settings.job_max_attempts,
        )
        return order

    # ---------- 查询 ----------

    async def list_for_user(
        self, user_id: int, *, page: int, page_size: int, status: str | None
    ) -> tuple[list[tuple[Order, int]], int]:
        self._check_status(status)
        async with self._uow() as uow:
            orders, total = await uow.orders.list_for_user(
                user_id, page=page, page_size=page_size, status=status
            )
            counts = await uow.orders.item_counts([order.id for order in orders])
        return [(order, counts.get(order.id, 0)) for order in orders], total

    async def admin_list(
        self, *, page: int, page_size: int, status: str | None, keyword: str | None
    ) -> tuple[list[tuple[AdminOrderRow, int]], int]:
        self._check_status(status)
        async with self._uow() as uow:
            rows, total = await uow.orders.admin_list(
                page=page, page_size=page_size, status=status, keyword=keyword
            )
            counts = await uow.orders.item_counts([row.order.id for row in rows])
        return [(row, counts.get(row.order.id, 0)) for row in rows], total

    def _check_status(self, status: str | None) -> None:
        if status and status not in ORDER_STATUSES:
            raise ValidationError("订单状态不合法")

    async def detail(self, order_no: str, *, user_id: int | None = None) -> OrderDetail:
        async with self._uow() as uow:
            order = await uow.orders.get_by_no(order_no)
            if order is None or (user_id is not None and order.user_id != user_id):
                raise NotFoundError("订单不存在")
            lines = await uow.orders.lines_of(order.id)
            payments = await uow.orders.payments_of(order.id)
            fulfillment = await uow.fulfillments.get_by_order(order.id)
        return OrderDetail(order=order, lines=lines, payments=payments, fulfillment=fulfillment)

    # ---------- 取消与超时 ----------

    async def cancel(self, user_id: int, order_no: str, *, reason: str = "USER_CANCELLED") -> Order:
        async with self._uow() as uow:
            order = await uow.orders.get_by_no(order_no)
            if order is None or order.user_id != user_id:
                raise NotFoundError("订单不存在")
            ensure_cancellable(order)
            changed = await uow.orders.transition(
                order.id,
                from_status=OrderStatus.PENDING_PAYMENT,
                to_status=OrderStatus.CANCELLED,
                fields={"cancelled_at": self._clock.now(), "cancel_reason": reason},
            )
            if not changed:
                await uow.rollback()
                raise ConflictError("订单状态已变化，请刷新后重试")
            await self._release_lines(uow, order, reason="取消订单释放库存")
            await uow.commit()
            order.status = OrderStatus.CANCELLED
            return order

    async def close_if_expired(self, order_no: str) -> bool:
        async with self._uow() as uow:
            order = await uow.orders.get_by_no(order_no)
            if order is None or order.status != OrderStatus.PENDING_PAYMENT:
                return False
            if order.expire_at is not None and order.expire_at > self._clock.now():
                return False
            changed = await uow.orders.transition(
                order.id,
                from_status=OrderStatus.PENDING_PAYMENT,
                to_status=OrderStatus.CANCELLED,
                fields={"cancelled_at": self._clock.now(), "cancel_reason": "EXPIRED"},
            )
            if not changed:
                await uow.rollback()
                return False
            await self._release_lines(uow, order, reason="超时未支付关闭订单")
            await uow.commit()
            return True

    async def _release_lines(self, uow, order: Order, *, reason: str) -> None:
        lines = await uow.orders.lines_of(order.id)
        for line in lines:
            ok = await uow.inventory.move(
                line.sku_id,
                line.quantity,
                action=InventoryChange.RELEASE,
                order_no=order.order_no,
                reason=reason,
            )
            if not ok:
                raise ConflictError(f"订单 {order.order_no} 的库存释放失败，请检查库存占用记录")
