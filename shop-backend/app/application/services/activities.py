"""活动用例：配置与查询。基础规则只有一种——指定 SKU 的固定活动价。"""

from __future__ import annotations

from datetime import UTC, datetime

from app.application.cache_keys import CATALOG_NAMESPACE
from app.application.ports.services import CachePort, Clock
from app.application.ports.uow import UowFactory
from app.application.read_models import ActivityDetail, ActivitySkuView
from app.domain.constants import ActivityStatus, ActivityType
from app.domain.entities import Activity, ActivitySku
from app.domain.errors import NotFoundError, ValidationError
from app.domain.money import to_cents


def parse_time(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{field} 需为 ISO 8601 时间，例如 2026-11-08T00:00:00Z") from exc
    if parsed.tzinfo is not None:
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


class ActivityService:
    def __init__(self, uow_factory: UowFactory, clock: Clock, cache: CachePort) -> None:
        self._uow = uow_factory
        self._clock = clock
        self._cache = cache

    async def create(
        self,
        *,
        name: str,
        type: str,
        status: str,
        description: str,
        starts_at: str,
        ends_at: str,
        skus: list[dict],
    ) -> Activity:
        start = parse_time(starts_at, "开始时间")
        end = parse_time(ends_at, "结束时间")
        if end <= start:
            raise ValidationError("结束时间必须晚于开始时间")
        if type == ActivityType.FLASH_SALE and not skus:
            raise ValidationError("限量发售活动必须指定参加活动的 SKU")

        async with self._uow() as uow:
            prepared: list[ActivitySku] = []
            for item in skus:
                sku = await uow.catalog.get_sku(item["skuId"])
                if sku is None:
                    raise NotFoundError(f"SKU {item['skuId']} 不存在")
                price = _price(item["activityPrice"], f"SKU {item['skuId']} 的活动价")
                if price > sku.price_cents:
                    raise ValidationError("活动价高于原价没有意义")
                limit = item.get("perUserLimit")
                quota = item.get("saleQuota")
                if limit is not None and quota is not None and limit > quota:
                    raise ValidationError("单人限购不能大于发售数量")
                prepared.append(
                    ActivitySku(
                        id=0,
                        activity_id=0,
                        sku_id=item["skuId"],
                        activity_price_cents=price,
                        sale_quota=quota,
                        per_user_limit=limit,
                    )
                )

            activity = await uow.activities.create(
                Activity(
                    id=0,
                    name=name,
                    type=type,
                    status=status,
                    description=description,
                    starts_at=start,
                    ends_at=end,
                ),
                prepared,
            )
            await uow.commit()
        await self._cache.bump(CATALOG_NAMESPACE)
        return activity

    async def update(
        self,
        activity_id: int,
        *,
        name: str | None,
        description: str | None,
        starts_at: str | None,
        ends_at: str | None,
        status: str | None,
    ) -> Activity:
        fields: dict = {}
        if name is not None:
            fields["name"] = name
        if description is not None:
            fields["description"] = description
        if starts_at is not None:
            fields["starts_at"] = parse_time(starts_at, "开始时间")
        if ends_at is not None:
            fields["ends_at"] = parse_time(ends_at, "结束时间")
        if status is not None:
            fields["status"] = status

        async with self._uow() as uow:
            current = await uow.activities.get(activity_id)
            if current is None:
                raise NotFoundError("活动不存在")
            start = fields.get("starts_at", current.starts_at)
            end = fields.get("ends_at", current.ends_at)
            if end <= start:
                raise ValidationError("结束时间必须晚于开始时间")
            activity = await uow.activities.update(activity_id, fields)
            await uow.commit()
        await self._cache.bump(CATALOG_NAMESPACE)
        return activity

    async def list(
        self, *, include_disabled: bool = False, active_only: bool = False
    ) -> list[Activity]:
        async with self._uow() as uow:
            return await uow.activities.list(
                include_disabled=include_disabled, active_only=active_only
            )

    async def get(self, activity_id: int) -> Activity:
        async with self._uow() as uow:
            activity = await uow.activities.get(activity_id)
            if activity is None:
                raise NotFoundError("活动不存在")
            return activity

    async def detail(self, activity: Activity) -> ActivityDetail:
        async with self._uow() as uow:
            rows = await uow.activities.sku_rows(activity.id)
        now = self._clock.now()
        return ActivityDetail(
            activity=activity,
            running=activity.status == ActivityStatus.ACTIVE
            and activity.starts_at <= now < activity.ends_at,
            skus=[
                ActivitySkuView(
                    sku_id=row.activity_sku.sku_id,
                    sku_code=row.sku_code,
                    original_cents=row.sku_price_cents,
                    activity_cents=row.activity_sku.activity_price_cents,
                    sale_quota=row.activity_sku.sale_quota,
                    sold_count=row.activity_sku.sold_count,
                    per_user_limit=row.activity_sku.per_user_limit,
                )
                for row in rows
            ],
        )

    async def detail_of(self, activity_id: int) -> ActivityDetail:
        return await self.detail(await self.get(activity_id))
