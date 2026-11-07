"""选价规则：同一 SKU 命中多个活动时取最低价，活动价高于原价时按原价卖。

纯函数，没有数据库、没有框架。数据由调用方（仓储）提供。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PriceRule:
    """一条生效中的活动价。"""

    activity_id: int
    activity_name: str
    activity_type: str
    price_cents: int
    per_user_limit: int | None = None
    sale_quota: int | None = None
    sold_count: int = 0
    activity_sku_id: int = 0


@dataclass(frozen=True, slots=True)
class Quote:
    """计价结果。unit 是成交价，original 是划线价。"""

    unit_cents: int
    original_cents: int
    activity_name: str = ""

    @property
    def discount_cents(self) -> int:
        return self.original_cents - self.unit_cents

    @property
    def has_discount(self) -> bool:
        return self.unit_cents < self.original_cents


def quote(original_cents: int, rule: PriceRule | None) -> Quote:
    if rule is not None and rule.price_cents < original_cents:
        return Quote(rule.price_cents, original_cents, rule.activity_name)
    return Quote(original_cents, original_cents, "")
