"""限量发售（秒杀）用例：原子占名额与库存 → 异步建单 → 结果查询。"""

from __future__ import annotations

from app.application.ports.services import Clock
from app.application.ports.uow import UowFactory
from app.application.services.orders import OrderService
from app.domain.constants import (
    FlashSaleStatus,
    InventoryChange,
    JobType,
    ProductStatus,
)
from app.domain.entities import Address, FlashSaleRequest
from app.domain.errors import ConflictError, NotFoundError, StockError, ValidationError
from app.domain.flashsale import ensure_per_user_limit, ensure_quota, ensure_running
from app.domain.ordering import PricedLine, flash_fingerprint
from app.domain.pricing import Quote


class FlashSaleService:
    def __init__(self, uow_factory: UowFactory, clock: Clock, orders: OrderService) -> None:
        self._uow = uow_factory
        self._clock = clock
        self._orders = orders

    async def join(
        self,
        user_id: int,
        activity_id: int,
        *,
        sku_id: int,
        quantity: int,
        address_id: int,
        request_id: str,
    ) -> tuple[FlashSaleRequest, bool]:
        if quantity <= 0:
            raise ValidationError("购买数量必须是正整数")

        async with self._uow() as uow:
            existing = await uow.flash_sales.find_by_request(user_id, request_id)
            if existing is not None:
                if existing.activity_id != activity_id or existing.sku_id != sku_id:
                    raise ConflictError("requestId 已用于另一次抢购，请换一个新的标识")
                return existing, False

            pair = await uow.activities.get_activity_sku(activity_id=activity_id, sku_id=sku_id)
            if pair is None:
                # 区分「活动不存在」和「SKU 没参加」，报错信息才有用
                if await uow.activities.get(activity_id) is None:
                    raise NotFoundError("活动不存在")
                raise NotFoundError("该 SKU 未参加此活动")
            activity, activity_sku = pair
            ensure_running(activity, self._clock.now())

            sku = await uow.catalog.get_sku(sku_id)
            pairs = await uow.catalog.get_skus_with_products([sku_id])
            if sku is None or not pairs:
                raise NotFoundError("SKU 不存在")
            product = pairs[0][1]
            if product.status != ProductStatus.ON_SALE or sku.status != ProductStatus.ON_SALE:
                raise ConflictError("商品或规格已下架")

            address: Address | None = await uow.addresses.get_owned(address_id, user_id)
            if address is None:
                raise NotFoundError("收货地址不存在")

            bought = await uow.activities.bought_quantity(activity_id, sku_id, user_id)
            ensure_per_user_limit(activity_sku, bought, quantity)
            ensure_quota(activity_sku, quantity)

            # 名额先原子占，再占库存；任一失败整体回滚
            if not await uow.activities.consume_quota(activity_sku.id, quantity):
                await uow.rollback()
                raise ConflictError("该商品已售罄")

            reserved = await uow.inventory.move(
                sku_id,
                quantity,
                action=InventoryChange.RESERVE,
                order_no=None,
                reason=f"限量发售占用（活动 {activity_id}）",
            )
            if not reserved:
                await uow.rollback()
                raise StockError("库存不足，抢购失败")

            request = await uow.flash_sales.create(
                FlashSaleRequest(
                    id=0,
                    activity_id=activity_id,
                    sku_id=sku_id,
                    user_id=user_id,
                    request_id=request_id,
                    quantity=quantity,
                    address_id=address_id,
                    unit_price_cents=activity_sku.activity_price_cents,
                    activity_name=activity.name,
                    status=FlashSaleStatus.QUEUED,
                )
            )
            await uow.jobs.enqueue(
                JobType.CREATE_FLASH_ORDER,
                {"requestId": request.id},
                dedupe_key=f"flash:{request.id}",
                delay_seconds=0,
                max_attempts=None,
            )
            await uow.commit()
            return request, True

    async def process(self, request_pk: int) -> None:
        """后台任务：把已占库存的抢购申请变成订单。"""
        async with self._uow() as uow:
            request = await uow.flash_sales.get(request_pk)
            if request is None or request.status != FlashSaleStatus.QUEUED:
                return
            pairs = await uow.catalog.get_skus_with_products([request.sku_id])
            if not pairs:
                await self._fail(uow, request, "SKU 已不存在")
                return
            sku, product = pairs[0]
            address = await uow.addresses.get_owned(request.address_id, request.user_id)
            if address is None:
                await self._fail(uow, request, "收货地址已不存在")
                return

            line = PricedLine(
                sku_id=sku.id,
                product_id=product.id,
                product_name=product.name,
                specs=dict(sku.specs or {}),
                quantity=request.quantity,
                quote=Quote(
                    unit_cents=request.unit_price_cents,
                    original_cents=sku.price_cents,
                    activity_name=request.activity_name,
                ),
            )
            fingerprint = flash_fingerprint(
                request.activity_id, request.sku_id, request.quantity, request.address_id
            )

        order = await self._orders.create_from_flash_sale(
            user_id=request.user_id,
            lines=[line],
            address=address,
            request_id=request.request_id,
            fingerprint=fingerprint,
            remark="限量发售",
        )

        async with self._uow() as uow:
            fresh = await uow.flash_sales.get(request_pk)
            if fresh is None:
                return
            fresh.status = FlashSaleStatus.SUCCEEDED
            fresh.order_no = order.order_no
            fresh.message = "抢购成功，请在 30 分钟内完成支付"
            await uow.flash_sales.save(fresh)
            await uow.commit()

    async def _fail(self, uow, request: FlashSaleRequest, message: str) -> None:
        request.status = FlashSaleStatus.FAILED
        request.message = message[:255]
        await uow.flash_sales.save(request)
        await uow.inventory.move(
            request.sku_id,
            request.quantity,
            action=InventoryChange.RELEASE,
            order_no=None,
            reason="限量发售失败释放库存",
        )
        await uow.activities.release_quota(request.activity_id, request.sku_id, request.quantity)
        await uow.commit()

    async def mark_failed(self, request_pk: int, message: str) -> None:
        async with self._uow() as uow:
            request = await uow.flash_sales.get(request_pk)
            if request is None or request.status != FlashSaleStatus.QUEUED:
                return
            await self._fail(uow, request, message)

    async def result(self, user_id: int, request_id: str) -> FlashSaleRequest:
        async with self._uow() as uow:
            request = await uow.flash_sales.find_by_request(user_id, request_id)
            if request is None:
                raise NotFoundError("抢购记录不存在")
            return request

    async def list_mine(self, user_id: int, *, limit: int = 20) -> list[FlashSaleRequest]:
        async with self._uow() as uow:
            return await uow.flash_sales.list_for_user(user_id, limit=limit)
