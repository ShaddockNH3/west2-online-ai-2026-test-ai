"""订单领域规则：状态机、可购买性判断、金额汇总、幂等指纹。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum

from app.domain.constants import OrderStatus, ProductStatus
from app.domain.entities import Order, Sku
from app.domain.errors import ConflictError, StockError, ValidationError
from app.domain.pricing import PriceRule, Quote, quote


class LineIssue(StrEnum):
    NONE = ""
    OFF_SALE = "商品已下架"
    SKU_OFF_SALE = "所选规格已下架"
    OUT_OF_STOCK = "库存不足"


@dataclass(slots=True)
class PricedLine:
    """计价后的一行：商品信息 + 成交价 + 是否可买。"""

    sku_id: int
    product_id: int
    product_name: str
    specs: dict
    quantity: int
    quote: Quote
    issue: LineIssue = LineIssue.NONE
    available: int = 0
    cart_item_id: int | None = None

    @property
    def purchasable(self) -> bool:
        return self.issue is LineIssue.NONE

    @property
    def issue_text(self) -> str:
        if self.issue is LineIssue.OUT_OF_STOCK:
            return f"库存不足，当前仅剩 {self.available} 件"
        return str(self.issue)

    @property
    def subtotal_cents(self) -> int:
        return self.quote.unit_cents * self.quantity


# 允许的状态迁移：目标状态 -> 来源状态集合
TRANSITIONS: dict[str, frozenset[str]] = {
    OrderStatus.PAID: frozenset({OrderStatus.PENDING_PAYMENT}),
    OrderStatus.SHIPPED: frozenset({OrderStatus.PAID}),
    OrderStatus.COMPLETED: frozenset({OrderStatus.SHIPPED}),
    OrderStatus.CANCELLED: frozenset({OrderStatus.PENDING_PAYMENT}),
}


def can_transition(current: str, target: str) -> bool:
    return current in TRANSITIONS.get(target, frozenset())


def ensure_cancellable(order: Order) -> None:
    if not can_transition(order.status, OrderStatus.CANCELLED):
        raise ConflictError("只有待支付订单可以取消")


def ensure_payable(order: Order) -> None:
    if order.status == OrderStatus.CANCELLED:
        raise ConflictError("订单已取消，不能支付")
    if not can_transition(order.status, OrderStatus.PAID):
        raise ConflictError("订单已支付，不能重复支付")


def ensure_confirmable(order: Order) -> None:
    if order.status == OrderStatus.COMPLETED:
        return
    if not can_transition(order.status, OrderStatus.COMPLETED):
        raise ConflictError("订单尚未发货，不能确认收货")


def evaluate_line(
    sku: Sku,
    product_status: str,
    product_name: str,
    product_id: int,
    quantity: int,
    rule: PriceRule | None,
    available: int,
    *,
    strict: bool,
    cart_item_id: int | None = None,
) -> PricedLine:
    """算出成交价，并判断这一行还能不能买。

    strict=True 时立刻抛错（提交订单），strict=False 时只标记（结算预览）。
    """
    if quantity <= 0:
        raise ValidationError("购买数量必须是正整数")

    issue = LineIssue.NONE
    if product_status != ProductStatus.ON_SALE:
        issue = LineIssue.OFF_SALE
    elif sku.status != ProductStatus.ON_SALE:
        issue = LineIssue.SKU_OFF_SALE
    elif available < quantity:
        issue = LineIssue.OUT_OF_STOCK

    if issue is not LineIssue.NONE and strict:
        message = f"「{product_name}」{_issue_text(issue, available)}"
        raise StockError(message) if issue is LineIssue.OUT_OF_STOCK else ConflictError(message)

    return PricedLine(
        sku_id=sku.id,
        product_id=product_id,
        product_name=product_name,
        specs=dict(sku.specs or {}),
        quantity=quantity,
        quote=quote(sku.price_cents, rule),
        issue=issue,
        available=available,
        cart_item_id=cart_item_id,
    )


def _issue_text(issue: LineIssue, available: int) -> str:
    if issue is LineIssue.OUT_OF_STOCK:
        return f"库存不足，当前仅剩 {available} 件"
    return str(issue)


def totals(lines: list[PricedLine], *, only_purchasable: bool = False) -> tuple[int, int, int]:
    """返回 (原价合计, 成交合计, 优惠合计)，单位分。"""
    selected = [line for line in lines if line.purchasable] if only_purchasable else lines
    original = sum(line.quote.original_cents * line.quantity for line in selected)
    total = sum(line.quote.unit_cents * line.quantity for line in selected)
    return original, total, original - total


def fingerprint_of(cart_item_ids: list[int], address_id: int) -> str:
    """同一 requestId 配不同购物车/地址时判为冲突，靠这个指纹比对。"""
    raw = f"{sorted(cart_item_ids)}|{address_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def flash_fingerprint(activity_id: int, sku_id: int, quantity: int, address_id: int) -> str:
    raw = f"flash:{activity_id}:{sku_id}:{quantity}:{address_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
