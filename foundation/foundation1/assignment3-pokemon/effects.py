"""异常状态：中毒、烧伤、麻痹、睡眠、寄生种子。

每个状态自己决定三件事：每回合结束扣多少血、是否会让宝可梦无法行动、持续几回合。
战斗流程只需要在合适的时候调用 `on_turn_end()` 和 `blocks_action()`。
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pokemon import Pokemon


class StatusEffect(ABC):
    """异常状态的基类。"""

    name: str = "状态"

    def __init__(self, duration: int) -> None:
        self.duration = duration

    def blocks_action(self) -> bool:
        """子类覆盖：返回 True 表示这一回合动不了。"""
        return False

    @abstractmethod
    def on_turn_end(self, owner: Pokemon) -> None:
        """每回合结束时结算一次。"""

    def tick(self) -> bool:
        """持续时间减一，返回是否已经结束。"""
        self.duration -= 1
        return self.duration <= 0

    def refresh(self, duration: int) -> None:
        """重复附着同一个状态时，取更长的持续时间。"""
        self.duration = max(self.duration, duration)


class PoisonEffect(StatusEffect):
    """中毒：每回合损失最大 HP 的 10%。"""

    name = "中毒"

    def __init__(self, ratio: float = 0.1, duration: int = 3) -> None:
        super().__init__(duration)
        self.ratio = ratio

    def on_turn_end(self, owner: Pokemon) -> None:
        damage = max(1, int(owner.max_hp * self.ratio))
        owner.lose_hp(damage, f"{owner.label} 因中毒损失 {damage} 点 HP")


class BurnEffect(StatusEffect):
    """烧伤：每回合固定损失 10 点 HP。"""

    name = "烧伤"

    def __init__(self, damage: int = 10, duration: int = 2) -> None:
        super().__init__(duration)
        self.damage = damage

    def on_turn_end(self, owner: Pokemon) -> None:
        owner.lose_hp(self.damage, f"{owner.label} 因烧伤损失 {self.damage} 点 HP")


class ParalysisEffect(StatusEffect):
    """麻痹：每次行动有 25% 的概率动不了。"""

    name = "麻痹"

    def __init__(self, chance: float = 0.25, duration: int = 3) -> None:
        super().__init__(duration)
        self.chance = chance

    def blocks_action(self) -> bool:
        return random.random() < self.chance

    def on_turn_end(self, owner: Pokemon) -> None:
        # 麻痹本身不扣血，这里只需要占位。
        return None


class SleepEffect(StatusEffect):
    """睡眠：持续期间完全无法行动。"""

    name = "睡眠"

    def __init__(self, duration: int = 2) -> None:
        super().__init__(duration)

    def blocks_action(self) -> bool:
        return True

    def on_turn_end(self, owner: Pokemon) -> None:
        return None


class LeechSeedEffect(StatusEffect):
    """寄生种子：每回合吸取目标 10% 最大 HP，转给施加者。"""

    name = "寄生种子"

    def __init__(self, source: Pokemon, ratio: float = 0.1, duration: int = 3) -> None:
        super().__init__(duration)
        self.source = source
        self.ratio = ratio

    def on_turn_end(self, owner: Pokemon) -> None:
        drain = max(1, int(owner.max_hp * self.ratio))
        owner.lose_hp(drain, f"寄生种子从 {owner.label} 身上吸取了 {drain} 点 HP")
        if self.source.alive:
            self.source.heal(drain, f"{self.source.label} 回复了 {drain} 点 HP")
