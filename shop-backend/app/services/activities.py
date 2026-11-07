"""活动配置与查询。基础规则只有一种：指定 SKU 的固定活动价。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import cache
from app.constants import ActivityStatus, ActivityType
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models import Activity, ActivitySku, Sku
from app.schemas import ActivityIn, ActivityPatch
from app.utils import iso, to_cents, utcnow, yuan


def parse_time(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{field} 需为 ISO 8601 时间，例如 2026-11-08T00:00:00Z") from exc
    if parsed.tzinfo is not None:
        from datetime import UTC

        parsed = parsed.astimezone(UTC).replace(tzinfo=None)
    return parsed.replace(microsecond=0)


def _price(value: str, field: str) -> int:
    try:
        cents = to_cents(value, field=field)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if cents <= 0:
        raise ValidationError(f"{field} 必须大于 0")
    return cents


async def create_activity(session: AsyncSession, data: ActivityIn) -> Activity:
    starts_at = parse_time(data.startsAt, "开始时间")
    ends_at = parse_time(data.endsAt, "结束时间")
    if ends_at <= starts_at:
        raise ValidationError("结束时间必须晚于开始时间")
    if data.type == ActivityType.FLASH_SALE and not data.skus:
        raise ValidationError("限量发售活动必须指定参加活动的 SKU")
    activity = Activity(
        name=data.name,
        type=data.type,
        status=data.status,
        description=data.description,
        starts_at=starts_at,
        ends_at=ends_at,
    )
    session.add(activity)
    await session.flush()
    for item in data.skus:
        sku = await session.get(Sku, item.skuId)
        if sku is None:
            raise NotFoundError(f"SKU {item.skuId} 不存在")
        price = _price(item.activityPrice, f"SKU {item.skuId} 的活动价")
        if price > sku.price_cents:
            raise ValidationError("活动价高于原价没有意义")
        if item.perUserLimit is not None and item.saleQuota is not None:
            if item.perUserLimit > item.saleQuota:
                raise ValidationError("单人限购不能大于发售数量")
        session.add(
            ActivitySku(
                activity_id=activity.id,
                sku_id=item.skuId,
                activity_price_cents=price,
                sale_quota=item.saleQuota,
                per_user_limit=item.perUserLimit,
            )
        )
    await session.commit()
    await cache.bump("catalog")
    await session.refresh(activity)
    return activity


async def update_activity(session: AsyncSession, activity_id: int, data: ActivityPatch) -> Activity:
    activity = await session.get(Activity, activity_id)
    if activity is None:
        raise NotFoundError("活动不存在")
    if data.name is not None:
        activity.name = data.name
    if data.description is not None:
        activity.description = data.description
    if data.startsAt is not None:
        activity.starts_at = parse_time(data.startsAt, "开始时间")
    if data.endsAt is not None:
        activity.ends_at = parse_time(data.endsAt, "结束时间")
    if activity.ends_at <= activity.starts_at:
        raise ValidationError("结束时间必须晚于开始时间")
    if data.status is not None:
        activity.status = data.status
    await session.commit()
    await cache.bump("catalog")
    await session.refresh(activity)
    return activity


async def list_activities(
    session: AsyncSession, *, include_disabled: bool = False, active_only: bool = False
) -> list[Activity]:
    stmt = select(Activity).order_by(Activity.id.desc())
    if active_only:
        now = utcnow()
        stmt = stmt.where(
            Activity.status == ActivityStatus.ACTIVE,
            Activity.starts_at <= now,
            Activity.ends_at > now,
        )
    elif not include_disabled:
        stmt = stmt.where(Activity.status != ActivityStatus.DISABLED)
    return list(await session.scalars(stmt))


async def detail(session: AsyncSession, activity: Activity) -> dict:
    rows = await session.execute(
        select(ActivitySku, Sku)
        .join(Sku, Sku.id == ActivitySku.sku_id)
        .where(ActivitySku.activity_id == activity.id)
        .order_by(ActivitySku.id)
    )
    now = utcnow()
    return {
        "id": activity.id,
        "name": activity.name,
        "type": activity.type,
        "status": activity.status,
        "description": activity.description,
        "startsAt": iso(activity.starts_at),
        "endsAt": iso(activity.ends_at),
        "running": activity.status == ActivityStatus.ACTIVE
        and activity.starts_at <= now < activity.ends_at,
        "skus": [
            {
                "skuId": sku.id,
                "skuCode": sku.sku_code,
                "originalPrice": yuan(sku.price_cents),
                "activityPrice": yuan(activity_sku.activity_price_cents),
                "saleQuota": activity_sku.sale_quota,
                "soldCount": activity_sku.sold_count,
                "perUserLimit": activity_sku.per_user_limit,
            }
            for activity_sku, sku in rows.all()
        ],
    }


async def get_activity(session: AsyncSession, activity_id: int) -> Activity:
    activity = await session.get(Activity, activity_id)
    if activity is None:
        raise NotFoundError("活动不存在")
    return activity


async def get_active_activity_sku(
    session: AsyncSession, activity_id: int, sku_id: int
) -> ActivitySku:
    activity = await get_activity(session, activity_id)
    now = utcnow()
    if activity.status != ActivityStatus.ACTIVE:
        raise ConflictError("活动未开始或已停用")
    if not (activity.starts_at <= now < activity.ends_at):
        raise ConflictError("当前不在活动时间内")
    if activity.type != ActivityType.FLASH_SALE:
        raise ConflictError("该活动不是限量发售")
    activity_sku = await session.scalar(
        select(ActivitySku).where(
            ActivitySku.activity_id == activity_id, ActivitySku.sku_id == sku_id
        )
    )
    if activity_sku is None:
        raise NotFoundError("该 SKU 未参加此活动")
    return activity_sku
