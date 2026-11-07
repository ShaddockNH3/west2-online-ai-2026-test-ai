"""活动选价：同一 SKU 命中多个活动时，取当前生效的最低价。"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import ActivityStatus
from app.models import Activity, ActivitySku, Sku
from app.utils import utcnow


@dataclass(frozen=True, slots=True)
class PriceRule:
    activity_id: int
    activity_name: str
    activity_type: str
    price_cents: int
    per_user_limit: int | None
    sale_quota: int | None
    sold_count: int
    activity_sku_id: int


async def active_rules(session: AsyncSession, sku_ids: list[int]) -> dict[int, PriceRule]:
    """返回 sku_id -> 当前最优活动价。活动仅取 ACTIVE 且处于时间窗内的。"""
    if not sku_ids:
        return {}
    now = utcnow()
    rows = await session.execute(
        select(ActivitySku, Activity)
        .join(Activity, Activity.id == ActivitySku.activity_id)
        .where(
            ActivitySku.sku_id.in_(sku_ids),
            Activity.status == ActivityStatus.ACTIVE,
            Activity.starts_at <= now,
            Activity.ends_at > now,
        )
        .order_by(ActivitySku.activity_price_cents.asc(), ActivitySku.id.asc())
    )
    rules: dict[int, PriceRule] = {}
    for activity_sku, activity in rows:
        if activity_sku.sku_id in rules:
            continue
        rules[activity_sku.sku_id] = PriceRule(
            activity_id=activity.id,
            activity_name=activity.name,
            activity_type=activity.type,
            price_cents=activity_sku.activity_price_cents,
            per_user_limit=activity_sku.per_user_limit,
            sale_quota=activity_sku.sale_quota,
            sold_count=activity_sku.sold_count,
            activity_sku_id=activity_sku.id,
        )
    return rules


def resolve_price(sku: Sku, rule: PriceRule | None) -> tuple[int, int, str]:
    """返回 (成交单价, 原价, 活动名)。活动价高于原价时按原价卖，不让用户吃亏。"""
    original = sku.price_cents
    if rule is not None and rule.price_cents < original:
        return rule.price_cents, original, rule.activity_name
    return original, original, ""
