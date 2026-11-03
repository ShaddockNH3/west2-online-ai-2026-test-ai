"""玩家状态：身份、武将、体力、手牌与回合内的临时标记。"""

from __future__ import annotations

import random

from cards import Card, Deck
from generals import General

IDENTITIES: tuple[str, ...] = ("主公", "忠臣", "反贼", "内奸")


class Player:
    """一名在场玩家。"""

    def __init__(self, seat: int, name: str, identity: str, general: General) -> None:
        self.seat = seat
        self.name = name
        self.identity = identity
        self.general = general
        self.max_hp = general.hp
        self.hp = general.hp
        self.hand: list[Card] = []
        self.alive = True
        # 回合内临时状态
        self.wine_used = False       # 本回合是否已喝过酒（下一张杀 +1 伤害）
        self.sha_played = False      # 本回合是否出过杀（咆哮 / 克己要用）
        self.rende_given = 0         # 仁德本阶段已给出的牌数
        self.rende_healed = False    # 仁德是否已经回复过体力
        self.zhiheng_used = False    # 制衡每阶段一次
        self.kunang_used = False     # 苦肉每阶段一次
        self.qingnang_used = False   # 青囊每阶段一次
        self.lijian_used = False     # 离间每阶段一次

    # ---------- 基本信息 ----------

    @property
    def is_human(self) -> bool:
        return self.name == "你"

    def has_skill(self, skill: str) -> bool:
        return skill in self.general.skills

    def __str__(self) -> str:
        status = "存活" if self.alive else "阵亡"
        return (
            f"{self.name}［{self.general}｜身份 {self.identity}｜体力 "
            f"{self.hp}/{self.max_hp}｜手牌 {len(self.hand)}｜{status}］"
        )

    def brief(self, hidden_hand: bool = True) -> str:
        """给旁观者看的一行摘要（AI 的手牌不公开）。"""
        hand = "?" if hidden_hand else " ".join(repr(card) for card in self.hand)
        status = "存活" if self.alive else "阵亡"
        return (
            f"{self.name}（{self.general.name}，{self.identity}）"
            f" 体力 {'□' * self.hp}{'×' * (self.max_hp - self.hp)}"
            f" 手牌 {len(self.hand)}（{hand}） {status}"
        )

    # ---------- 牌 ----------

    def draw(self, deck: Deck, count: int = 1) -> list[Card]:
        drawn = [deck.draw() for _ in range(count)]
        self.hand.extend(drawn)
        return drawn

    def take_random_card(self) -> Card | None:
        """被顺走 / 获得时的随机一张手牌。"""
        if not self.hand:
            return None
        return self.hand.pop(random.randrange(len(self.hand)))

    def take_card(self, card: Card) -> Card:
        """从手牌里移除指定牌（按对象匹配）。"""
        for index, item in enumerate(self.hand):
            if item is card:
                return self.hand.pop(index)
        raise ValueError("指定的牌不在手牌里")

    def discard_random(self, deck: Deck) -> Card | None:
        """刚烈判定成功时弃一张随机手牌。"""
        card = self.take_random_card()
        if card:
            deck.discard(card)
        return card

    def discard_all(self, deck: Deck) -> None:
        """阵亡 / 主公处刑忠臣时弃光手牌。"""
        deck.discard(self.hand)
        self.hand = []

    # ---------- 体力 ----------

    def change_hp(self, amount: int) -> None:
        self.hp = max(0, min(self.max_hp, self.hp + amount))

    def heal(self, amount: int) -> bool:
        """回复体力，已满则返回 False（桃就无法使用）。"""
        if self.hp >= self.max_hp:
            return False
        self.hp = min(self.max_hp, self.hp + amount)
        return True

    # ---------- 回合内状态 ----------

    def reset_turn_state(self) -> None:
        self.wine_used = False
        self.sha_played = False
        self.rende_given = 0
        self.rende_healed = False
        self.zhiheng_used = False
        self.kunang_used = False
        self.qingnang_used = False
        self.lijian_used = False
