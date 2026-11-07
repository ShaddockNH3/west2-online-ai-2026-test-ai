"""限量发售规则：时间窗、限购、名额。"""

from __future__ import annotations

from datetime import datetime

from app.domain.constants import ActivityStatus, ActivityType
from app.domain.entities import Activity, ActivitySku
from app.domain.errors import ConflictError


def ensure_running(activity: Activity, now: datetime) -> None:
    if activity.status != ActivityStatus.ACTIVE:
        raise ConflictError("活动未开始或已停用")
    if not (activity.starts_at <= now < activity.ends_at):
        raise ConflictError("当前不在活动时间内")
    if activity.type != ActivityType.FLASH_SALE:
        raise ConflictError("该活动不是限量发售")


def ensure_per_user_limit(activity_sku: ActivitySku, bought: int, quantity: int) -> None:
    limit = activity_sku.per_user_limit
    if limit is not None and bought + quantity > limit:
        raise ConflictError(f"每人限购 {limit} 件")


def ensure_quota(activity_sku: ActivitySku, quantity: int) -> None:
    if activity_sku.sale_quota is not None and activity_sku.sold_count + quantity > (
        activity_sku.sale_quota
    ):
        raise ConflictError("该商品已售罄")
