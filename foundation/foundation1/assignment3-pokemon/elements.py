"""属性与克制关系。

克制表只写「谁克制谁」，被克制的一半由 `multiplier()` 反推，
这样加新属性时只需要维护一张正向表，不用担心两边写反。
"""

from __future__ import annotations

from enum import Enum


class Element(Enum):
    """宝可梦的属性。"""

    GRASS = "草"
    FIRE = "火"
    WATER = "水"
    ELECTRIC = "电"
    GHOST = "幽灵"

    def __str__(self) -> str:
        return self.value


# 正向克制表：key 克制 value 里的每一个属性。
STRONG_AGAINST: dict[Element, frozenset[Element]] = {
    Element.GRASS: frozenset({Element.WATER}),
    Element.FIRE: frozenset({Element.GRASS}),
    Element.WATER: frozenset({Element.FIRE}),
    Element.ELECTRIC: frozenset({Element.WATER}),
    # 幽灵是本作新增的属性，克制电系：原作里没有这条关系，这里是为了让新属性有存在感。
    Element.GHOST: frozenset({Element.ELECTRIC}),
}

SUPER_EFFECTIVE = 2.0
NOT_EFFECTIVE = 0.5
NORMAL = 1.0


def multiplier(attacker: Element, defender: Element) -> float:
    """返回攻击方属性打防守方属性时的伤害倍率。"""
    if defender in STRONG_AGAINST[attacker]:
        return SUPER_EFFECTIVE
    if attacker in STRONG_AGAINST[defender]:
        return NOT_EFFECTIVE
    return NORMAL


def describe(multiplier_value: float) -> str:
    """把倍率翻译成一句提示语，没有效果时就返回空字符串。"""
    if multiplier_value > NORMAL:
        return "效果绝佳！"
    if multiplier_value < NORMAL:
        return "效果不太好……"
    return ""
