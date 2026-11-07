"""限量发售（秒杀）：原子扣减库存 + 异步建单 + 结果查询。

压测关注的链路是：抢购接口快速受理 -> 后台任务建单 -> 用户查到最终结果。
"""

from __future__ import annotations

import hashlib

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import FlashSaleStatus, JobType, ProductStatus
from app.core.errors import ConflictError, NotFoundError, StockError, ValidationError
from app.models import (
    Activity,
    ActivitySku,
    Address,
    FlashSaleRequest,
    Product,
    Sku,
)
from app.schemas import FlashSaleIn
from app.services import activities as activity_service
from app.services import inventory as inventory_service
from app.services import jobs, orders
from app.utils import iso, utcnow, yuan


async def join(
    session: AsyncSession, user_id: int, activity_id: int, data: FlashSaleIn
) -> tuple[FlashSaleRequest, bool]:
    """返回 (抢购申请, 是否新建)。同一 requestId 重试不会重复占库存。"""
    existing = await session.scalar(
        select(FlashSaleRequest).where(
            FlashSaleRequest.user_id == user_id, FlashSaleRequest.request_id == data.requestId
        )
    )
    if existing is not None:
        if existing.activity_id != activity_id or existing.sku_id != data.skuId:
            raise ConflictError("requestId 已用于另一次抢购，请换一个新的标识")
        return existing, False

    activity_row = (
        await session.execute(
            select(Activity, ActivitySku)
            .join(ActivitySku, ActivitySku.activity_id == Activity.id)
            .where(Activity.id == activity_id, ActivitySku.sku_id == data.skuId)
        )
    ).first()
    if activity_row is None:
        # 区分"活动不存在"和"SKU 没参加"，错误信息更准确
        await activity_service.get_activity(session, activity_id)
        raise NotFoundError("该 SKU 未参加此活动")
    activity, activity_sku = activity_row

    now = utcnow()
    if activity.status != "ACTIVE":
        raise ConflictError("活动未开始或已停用")
    if not (activity.starts_at <= now < activity.ends_at):
        raise ConflictError("当前不在活动时间内")
    if activity.type != "FLASH_SALE":
        raise ConflictError("该活动不是限量发售")

    row = (
        await session.execute(
            select(Sku, Product)
            .join(Product, Product.id == Sku.product_id)
            .where(Sku.id == data.skuId)
        )
    ).first()
    if row is None:
        raise NotFoundError("SKU 不存在")
    sku, product = row
    if product.status != ProductStatus.ON_SALE or sku.status != "ON_SALE":
        raise ConflictError("商品或规格已下架")

    address = await session.scalar(
        select(Address).where(Address.id == data.addressId, Address.user_id == user_id)
    )
    if address is None:
        raise NotFoundError("收货地址不存在")

    if activity_sku.per_user_limit is not None:
        bought = await session.scalar(
            select(func.coalesce(func.sum(FlashSaleRequest.quantity), 0)).where(
                FlashSaleRequest.activity_id == activity_id,
                FlashSaleRequest.sku_id == data.skuId,
                FlashSaleRequest.user_id == user_id,
                FlashSaleRequest.status.in_([FlashSaleStatus.QUEUED, FlashSaleStatus.SUCCEEDED]),
            )
        )
        if int(bought or 0) + data.quantity > activity_sku.per_user_limit:
            raise ConflictError(f"每人限购 {activity_sku.per_user_limit} 件")

    # 发售名额是活动级配额，先原子占名额再占库存，任一失败都整体回滚
    quota = await session.execute(
        update(ActivitySku)
        .where(
            ActivitySku.id == activity_sku.id,
            or_(
                ActivitySku.sale_quota.is_(None),
                ActivitySku.sold_count + data.quantity <= ActivitySku.sale_quota,
            ),
        )
        .values(sold_count=ActivitySku.sold_count + data.quantity)
    )
    if quota.rowcount != 1:
        await session.rollback()
        raise ConflictError("该商品已售罄")

    reserved = await inventory_service.reserve(
        session,
        data.skuId,
        data.quantity,
        order_no=None,
        reason=f"限量发售占用（活动 {activity_id}）",
    )
    if not reserved:
        await session.rollback()
        raise StockError("库存不足，抢购失败")

    request = FlashSaleRequest(
        activity_id=activity_id,
        sku_id=data.skuId,
        user_id=user_id,
        request_id=data.requestId,
        quantity=data.quantity,
        address_id=data.addressId,
        unit_price_cents=activity_sku.activity_price_cents,
        activity_name=activity.name,
        status=FlashSaleStatus.QUEUED,
    )
    session.add(request)
    await session.flush()
    await jobs.enqueue(
        session,
        JobType.CREATE_FLASH_ORDER,
        {"requestId": request.id},
        dedupe_key=f"flash:{request.id}",
    )
    await session.commit()
    await session.refresh(request)
    return request, True


async def process(session: AsyncSession, request_pk: int) -> None:
    """后台任务：把已占库存的抢购申请变成订单。"""
    request = await session.get(FlashSaleRequest, request_pk)
    if request is None or request.status != FlashSaleStatus.QUEUED:
        return
    row = (
        await session.execute(
            select(Sku, Product)
            .join(Product, Product.id == Sku.product_id)
            .where(Sku.id == request.sku_id)
        )
    ).first()
    if row is None:
        await mark_failed(session, request_pk, "SKU 已不存在")
        return
    sku, product = row
    address = await session.get(Address, request.address_id)
    if address is None:
        await mark_failed(session, request_pk, "收货地址已不存在")
        return

    line = orders.Line(
        sku_id=sku.id,
        product_id=product.id,
        product_name=product.name,
        specs=dict(sku.specs or {}),
        quantity=request.quantity,
        unit_price=request.unit_price_cents,
        original_price=sku.price_cents,
        activity_name=request.activity_name,
    )
    fingerprint = hashlib.sha256(
        f"flash:{request.activity_id}:{request.sku_id}:{request.quantity}:{request.address_id}".encode()
    ).hexdigest()
    order, _ = await orders.persist_order(
        session,
        user_id=request.user_id,
        lines=[line],
        address=address,
        request_id=request.request_id,
        fingerprint=fingerprint,
        remark="限量发售",
        reserve_stock=False,
        clear_cart=False,
    )
    request.status = FlashSaleStatus.SUCCEEDED
    request.order_no = order.order_no
    request.message = "抢购成功，请在 30 分钟内完成支付"
    await session.commit()


async def mark_failed(session: AsyncSession, request_pk: int, message: str) -> None:
    request = await session.get(FlashSaleRequest, request_pk)
    if request is None or request.status != FlashSaleStatus.QUEUED:
        return
    request.status = FlashSaleStatus.FAILED
    request.message = message[:255]
    await inventory_service.release(
        session,
        request.sku_id,
        request.quantity,
        order_no=None,
        reason="限量发售失败释放库存",
    )
    await session.execute(
        update(ActivitySku)
        .where(ActivitySku.activity_id == request.activity_id, ActivitySku.sku_id == request.sku_id)
        .values(sold_count=ActivitySku.sold_count - request.quantity)
    )
    await session.commit()


async def get_result(session: AsyncSession, user_id: int, request_id: str) -> dict:
    request = await session.scalar(
        select(FlashSaleRequest).where(
            FlashSaleRequest.user_id == user_id, FlashSaleRequest.request_id == request_id
        )
    )
    if request is None:
        raise NotFoundError("抢购记录不存在")
    return public_request(request)


async def list_mine(session: AsyncSession, user_id: int, *, limit: int = 20) -> list[dict]:
    rows = await session.scalars(
        select(FlashSaleRequest)
        .where(FlashSaleRequest.user_id == user_id)
        .order_by(FlashSaleRequest.id.desc())
        .limit(limit)
    )
    return [public_request(row) for row in rows]


def public_request(request: FlashSaleRequest) -> dict:
    return {
        "requestId": request.request_id,
        "activityId": request.activity_id,
        "activityName": request.activity_name,
        "skuId": request.sku_id,
        "quantity": request.quantity,
        "unitPrice": yuan(request.unit_price_cents),
        "status": request.status,
        "orderNo": request.order_no,
        "message": request.message or None,
        "createdAt": iso(request.created_at),
        "updatedAt": iso(request.updated_at),
    }


def require_quantity(quantity: int) -> int:
    if quantity <= 0:
        raise ValidationError("购买数量必须是正整数")
    return quantity
