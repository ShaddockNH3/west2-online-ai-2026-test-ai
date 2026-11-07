"""库存与履约状态流转规则。

库存的核心不变量：available / reserved / sold 三个数只在占用、释放、扣减、
入库四个动作里变，每次变化都要留一条流水。原子更新在仓储实现里，这里只管判断。
"""

from __future__ import annotations

from app.domain.constants import FulfillmentStatus
from app.domain.errors import ConflictError

# 目标状态 -> 允许的来源状态
FULFILLMENT_TRANSITIONS: dict[str, frozenset[str]] = {
    FulfillmentStatus.READY_TO_SHIP: frozenset({FulfillmentStatus.PENDING}),
    FulfillmentStatus.SHIPPED: frozenset({FulfillmentStatus.READY_TO_SHIP}),
    FulfillmentStatus.COMPLETED: frozenset({FulfillmentStatus.SHIPPED}),
}


def can_move_to(current: str, target: str) -> bool:
    return current in FULFILLMENT_TRANSITIONS.get(target, frozenset())


def ensure_preparable(status: str) -> None:
    if not can_move_to(status, FulfillmentStatus.READY_TO_SHIP):
        raise ConflictError("当前履约状态不能备货")


def ensure_shippable(status: str) -> None:
    if status == FulfillmentStatus.SHIPPED:
        raise ConflictError("该履约单已发货")
    if not can_move_to(status, FulfillmentStatus.SHIPPED):
        raise ConflictError("请先完成备货再发货")
