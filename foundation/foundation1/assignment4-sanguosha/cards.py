"""牌堆与牌。

本 demo 不实现装备牌与延时锦囊（乐不思蜀、闪电等），
牌只有两类：基础牌（杀、闪、桃、酒）与锦囊牌。

每张牌带花色，因为关羽（武圣）、甘宁（奇袭）、华佗（急救）
的技能都依赖牌的颜色：红桃/方块是红色，黑桃/梅花是黑色。
"""

from __future__ import annotations

import random
from dataclasses import dataclass

BASIC_CARDS: tuple[str, ...] = ("杀", "闪", "桃", "酒")
TRICK_CARDS: tuple[str, ...] = (
    "无中生有",
    "过河拆桥",
    "顺手牵羊",
    "决斗",
    "南蛮入侵",
    "万箭齐发",
    "桃园结义",
    "无懈可击",
)
ALL_CARD_NAMES: tuple[str, ...] = BASIC_CARDS + TRICK_CARDS

RED_SUITS: tuple[str, ...] = ("红桃", "方块")
BLACK_SUITS: tuple[str, ...] = ("黑桃", "梅花")


def is_red(suit: str) -> bool:
    """红色牌：红桃、方块。"""
    return suit in RED_SUITS


@dataclass
class Card:
    """一张牌：名字 + 花色。"""

    name: str
    suit: str

    @property
    def red(self) -> bool:
        return is_red(self.suit)

    def __repr__(self) -> str:
        return f"{self.suit}{self.name}"


# 牌堆构成（张数参考标准包的大致比例，非精确复刻）。
DECK_RECIPE: list[tuple[str, int, tuple[str, ...]]] = [
    ("杀", 24, ("黑桃", "梅花", "红桃", "方块")),
    ("闪", 16, ("红桃", "方块")),
    ("桃", 8, ("红桃",)),
    ("酒", 4, ("黑桃", "方块")),
    ("无中生有", 4, ("红桃", "方块")),
    ("过河拆桥", 6, ("黑桃", "梅花", "红桃")),
    ("顺手牵羊", 5, ("黑桃", "梅花", "方块")),
    ("决斗", 4, ("黑桃", "梅花", "红桃")),
    ("南蛮入侵", 3, ("黑桃", "梅花")),
    ("万箭齐发", 1, ("红桃",)),
    ("桃园结义", 1, ("红桃",)),
    ("无懈可击", 4, ("黑桃", "梅花", "红桃", "方块")),
]


class Deck:
    """牌堆：摸完就把弃牌堆洗回去。"""

    def __init__(self, seed: int | None = None) -> None:
        self._random = random.Random(seed)
        self._pile: list[Card] = self._build()
        self._random.shuffle(self._pile)
        self._discard: list[Card] = []

    def _build(self) -> list[Card]:
        cards: list[Card] = []
        for name, count, suits in DECK_RECIPE:
            for index in range(count):
                cards.append(Card(name, suits[index % len(suits)]))
        return cards

    def draw(self) -> Card:
        """摸一张牌，牌堆见底时洗回弃牌堆。"""
        if not self._pile:
            self._pile = self._discard
            self._discard = []
            self._random.shuffle(self._pile)
            if not self._pile:
                raise RuntimeError("牌堆与弃牌堆都空了")
        return self._pile.pop()

    def discard(self, cards: list[Card] | Card) -> None:
        """把牌放进弃牌堆。"""
        if isinstance(cards, Card):
            self._discard.append(cards)
        else:
            self._discard.extend(cards)
