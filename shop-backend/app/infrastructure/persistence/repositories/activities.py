"""活动、活动 SKU 与抢购申请的 SQLAlchemy 实现。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.constants import ActivityStatus, FlashSaleStatus
from app.domain.entities import Activity, ActivitySku, ActivitySkuRow, FlashSaleRequest
from app.domain.errors import NotFoundError
from app.domain.pricing import PriceRule
from app.infrastructure.persistence.mappers import (
    to_activity,
    to_activity_sku,
    to_flash_request,
)
from app.infrastructure.persistence.models import Activity as ActivityRow
from app.infrastructure.persistence.models import ActivitySku as ActivitySkuRowModel
from app.infrastructure.persistence.models import FlashSaleRequest as FlashRequestRow
from app.infrastructure.persistence.models import Sku as SkuRow


class SqlActivityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, activity: Activity, skus: list[ActivitySku]) -> Activity:
        row = ActivityRow(
            name=activity.name,
            type=activity.type,
            status=activity.status,
            description=activity.description,
            starts_at=activity.starts_at,
            ends_at=activity.ends_at,
        )
        self._session.add(row)
        await self._session.flush()
        for item in skus:
            self._session.add(
                ActivitySkuRowModel(
                    activity_id=row.id,
                    sku_id=item.sku_id,
                    activity_price_cents=item.activity_price_cents,
                    sale_quota=item.sale_quota,
                    per_user_limit=item.per_user_limit,
                )
            )
        await self._session.flush()
        return to_activity(row)

    async def update(self, activity_id: int, fields: dict[str, Any]) -> Activity:
        row = await self._session.get(ActivityRow, activity_id)
        if row is None:
            raise NotFoundError("活动不存在")
        for name, value in fields.items():
            setattr(row, name, value)
        await self._session.flush()
        return to_activity(row)

    async def get(self, activity_id: int) -> Activity | None:
        row = await self._session.get(ActivityRow, activity_id)
        return to_activity(row) if row else None

    async def list(self, *, include_disabled: bool, active_only: bool) -> list[Activity]:
        stmt = select(ActivityRow).order_by(ActivityRow.id.desc())
        if active_only:
            from app.domain.money import utcnow

            now = utcnow()
            stmt = stmt.where(
                ActivityRow.status == ActivityStatus.ACTIVE,
                ActivityRow.starts_at <= now,
                ActivityRow.ends_at > now,
            )
        elif not include_disabled:
            stmt = stmt.where(ActivityRow.status != ActivityStatus.DISABLED)
        return [to_activity(row) for row in await self._session.scalars(stmt)]

    async def sku_rows(self, activity_id: int) -> list[ActivitySkuRow]:
        rows = await self._session.execute(
            select(ActivitySkuRowModel, SkuRow)
            .join(SkuRow, SkuRow.id == ActivitySkuRowModel.sku_id)
            .where(ActivitySkuRowModel.activity_id == activity_id)
            .order_by(ActivitySkuRowModel.id)
        )
        return [
            ActivitySkuRow(
                activity_sku=to_activity_sku(activity_sku),
                sku_code=sku.sku_code,
                sku_price_cents=sku.price_cents,
            )
            for activity_sku, sku in rows.all()
        ]

    async def get_activity_sku(
        self, *, activity_id: int, sku_id: int
    ) -> tuple[Activity, ActivitySku] | None:
        row = (
            await self._session.execute(
                select(ActivityRow, ActivitySkuRowModel)
                .join(ActivitySkuRowModel, ActivitySkuRowModel.activity_id == ActivityRow.id)
                .where(ActivityRow.id == activity_id, ActivitySkuRowModel.sku_id == sku_id)
            )
        ).first()
        if row is None:
            return None
        activity, activity_sku = row
        return to_activity(activity), to_activity_sku(activity_sku)

    async def active_rules(self, sku_ids: list[int], *, now: datetime) -> dict[int, PriceRule]:
        if not sku_ids:
            return {}
        rows = await self._session.execute(
            select(ActivitySkuRowModel, ActivityRow)
            .join(ActivityRow, ActivityRow.id == ActivitySkuRowModel.activity_id)
            .where(
                ActivitySkuRowModel.sku_id.in_(sku_ids),
                ActivityRow.status == ActivityStatus.ACTIVE,
                ActivityRow.starts_at <= now,
                ActivityRow.ends_at > now,
            )
            .order_by(ActivitySkuRowModel.activity_price_cents.asc(), ActivitySkuRowModel.id.asc())
        )
        rules: dict[int, PriceRule] = {}
        for activity_sku, activity in rows.all():
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

    async def consume_quota(self, activity_sku_id: int, quantity: int) -> bool:
        result = await self._session.execute(
            update(ActivitySkuRowModel)
            .where(
                ActivitySkuRowModel.id == activity_sku_id,
                or_(
                    ActivitySkuRowModel.sale_quota.is_(None),
                    ActivitySkuRowModel.sold_count + quantity <= ActivitySkuRowModel.sale_quota,
                ),
            )
            .values(sold_count=ActivitySkuRowModel.sold_count + quantity)
        )
        return result.rowcount == 1

    async def release_quota(self, activity_id: int, sku_id: int, quantity: int) -> None:
        await self._session.execute(
            update(ActivitySkuRowModel)
            .where(
                ActivitySkuRowModel.activity_id == activity_id,
                ActivitySkuRowModel.sku_id == sku_id,
            )
            .values(sold_count=ActivitySkuRowModel.sold_count - quantity)
        )

    async def bought_quantity(self, activity_id: int, sku_id: int, user_id: int) -> int:
        total = await self._session.scalar(
            select(func.coalesce(func.sum(FlashRequestRow.quantity), 0)).where(
                FlashRequestRow.activity_id == activity_id,
                FlashRequestRow.sku_id == sku_id,
                FlashRequestRow.user_id == user_id,
                FlashRequestRow.status.in_([FlashSaleStatus.QUEUED, FlashSaleStatus.SUCCEEDED]),
            )
        )
        return int(total or 0)


class SqlFlashSaleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_request(self, user_id: int, request_id: str) -> FlashSaleRequest | None:
        row = await self._session.scalar(
            select(FlashRequestRow).where(
                FlashRequestRow.user_id == user_id,
                FlashRequestRow.request_id == request_id,
            )
        )
        return to_flash_request(row) if row else None

    async def create(self, request: FlashSaleRequest) -> FlashSaleRequest:
        row = FlashRequestRow(
            activity_id=request.activity_id,
            sku_id=request.sku_id,
            user_id=request.user_id,
            request_id=request.request_id,
            quantity=request.quantity,
            address_id=request.address_id,
            unit_price_cents=request.unit_price_cents,
            activity_name=request.activity_name,
            status=request.status,
            order_no=request.order_no,
            message=request.message,
        )
        self._session.add(row)
        await self._session.flush()
        return to_flash_request(row)

    async def get(self, request_id: int) -> FlashSaleRequest | None:
        row = await self._session.get(FlashRequestRow, request_id)
        return to_flash_request(row) if row else None

    async def save(self, request: FlashSaleRequest) -> None:
        row = await self._session.get(FlashRequestRow, request.id)
        if row is None:
            raise NotFoundError("抢购记录不存在")
        row.status = request.status
        row.order_no = request.order_no
        row.message = request.message
        await self._session.flush()

    async def list_for_user(self, user_id: int, *, limit: int) -> list[FlashSaleRequest]:
        rows = await self._session.scalars(
            select(FlashRequestRow)
            .where(FlashRequestRow.user_id == user_id)
            .order_by(FlashRequestRow.id.desc())
            .limit(limit)
        )
        return [to_flash_request(row) for row in rows]
