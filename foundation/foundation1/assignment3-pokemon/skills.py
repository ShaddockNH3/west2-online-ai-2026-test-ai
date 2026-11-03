"""技能：一次攻击 = 属性 + 倍率 + 附加效果。

`Skill.use()` 负责「蓄力 → 造成伤害 → 触发附加效果」这条通用流程，
子类只需要通过 `on_hit()` 挂上自己的效果，不用把伤害计算抄一遍。
"""

from __future__ import annotations

import random
from abc import ABC
from typing import TYPE_CHECKING

import effects
from elements import Element

if TYPE_CHECKING:
    from battle import Battle
    from pokemon import Pokemon


class Skill(ABC):
    """技能基类。"""

    name: str = "技能"
    element: Element = Element.GRASS
    charge_turns: int = 0  # 需要蓄力的回合数
    charge_dodge_bonus: float = 0.0  # 蓄力技能释放时，对方额外的闪避率

    def __init__(self, power: float) -> None:
        self.power = power

    def __str__(self) -> str:
        return self.name

    def use(self, user: Pokemon, target: Pokemon, battle: Battle) -> None:
        """标准技能流程：蓄力判定 → 结算伤害 → 触发附加效果。"""
        if self.charge_turns and not user.is_charging(self.name):
            user.begin_charge(self.name)
            print(f"{user.label} 开始蓄力，{self.name} 将在下一回合释放！")
            return

        dodge_bonus = 0.0
        if self.charge_turns:
            user.end_charge()
            dodge_bonus = self.charge_dodge_bonus
            print(f"{user.label} 释放了蓄力已久的 {self.name}！")

        if battle.deal_damage(user, target, self, dodge_bonus):
            self.on_hit(user, target, battle)

    def on_hit(self, user: Pokemon, target: Pokemon, battle: Battle) -> None:
        """命中之后的附加效果，默认什么也不做。"""
        return None


class Thunderbolt(Skill):
    """十万伏特：1.4 倍电属性伤害，10% 概率麻痹。"""

    name = "十万伏特"
    element = Element.ELECTRIC

    def __init__(self) -> None:
        super().__init__(power=1.4)

    def on_hit(self, user: Pokemon, target: Pokemon, battle: Battle) -> None:
        if random.random() < 0.1:
            target.add_status(effects.ParalysisEffect())
            print(f"{target.label} 被电得麻痹了！")


class QuickAttack(Skill):
    """电光一闪：1.0 倍伤害，10% 概率追加一次攻击。"""

    name = "电光一闪"
    element = Element.ELECTRIC

    def __init__(self) -> None:
        super().__init__(power=1.0)

    def on_hit(self, user: Pokemon, target: Pokemon, battle: Battle) -> None:
        if random.random() < 0.1 and target.alive:
            print(f"{user.label} 抓住空隙，又补了一次攻击！")
            battle.deal_damage(user, target, self)


class SeedBomb(Skill):
    """种子炸弹：草属性伤害，15% 概率使目标中毒。"""

    name = "种子炸弹"
    element = Element.GRASS

    def __init__(self) -> None:
        super().__init__(power=1.0)

    def on_hit(self, user: Pokemon, target: Pokemon, battle: Battle) -> None:
        if random.random() < 0.15:
            target.add_status(effects.PoisonEffect())
            print(f"{target.label} 中毒了！")


class ParasiticSeeds(Skill):
    """寄生种子：不造成伤害，让目标每回合被吸取 HP。"""

    name = "寄生种子"
    element = Element.GRASS

    def __init__(self) -> None:
        super().__init__(power=0.0)

    def use(self, user: Pokemon, target: Pokemon, battle: Battle) -> None:
        if target.has_status(effects.LeechSeedEffect.name):
            print(f"{target.label} 身上已经有寄生种子了。")
            return
        target.add_status(effects.LeechSeedEffect(source=user))
        print(f"{user.label} 在 {target.label} 身上播下了寄生种子！")


class AquaJet(Skill):
    """水枪：1.4 倍水属性伤害，没有附加效果。"""

    name = "水枪"
    element = Element.WATER

    def __init__(self) -> None:
        super().__init__(power=1.4)


class Shield(Skill):
    """护盾：本回合不攻击，下回合受到的伤害减半。"""

    name = "护盾"
    element = Element.WATER

    def __init__(self) -> None:
        super().__init__(power=0.0)

    def use(self, user: Pokemon, target: Pokemon, battle: Battle) -> None:
        user.raise_shield()
        print(f"{user.label} 用水流撑起护盾，下回合受到的伤害减半。")


class Ember(Skill):
    """火花：1.0 倍火属性伤害，10% 概率烧伤。"""

    name = "火花"
    element = Element.FIRE

    def __init__(self) -> None:
        super().__init__(power=1.0)

    def on_hit(self, user: Pokemon, target: Pokemon, battle: Battle) -> None:
        if random.random() < 0.1:
            target.add_status(effects.BurnEffect())
            print(f"{target.label} 被烧伤了！")


class FlameCharge(Skill):
    """蓄能爆炎：3 倍火属性伤害，需要蓄力一回合，80% 概率烧伤。"""

    name = "蓄能爆炎"
    element = Element.FIRE
    charge_turns = 1
    charge_dodge_bonus = 0.2

    def __init__(self) -> None:
        super().__init__(power=3.0)

    def on_hit(self, user: Pokemon, target: Pokemon, battle: Battle) -> None:
        if random.random() < 0.8:
            target.add_status(effects.BurnEffect())
            print(f"{target.label} 被烈焰吞没，陷入烧伤！")


class ShadowBall(Skill):
    """暗影球：1.3 倍幽灵属性伤害，25% 概率让目标麻痹。"""

    name = "暗影球"
    element = Element.GHOST

    def __init__(self) -> None:
        super().__init__(power=1.3)

    def on_hit(self, user: Pokemon, target: Pokemon, battle: Battle) -> None:
        if random.random() < 0.25:
            target.add_status(effects.ParalysisEffect())
            print(f"{target.label} 被暗影缠住，动弹不得！")


class Hypnosis(Skill):
    """催眠术：不造成伤害，让目标睡上两回合。"""

    name = "催眠术"
    element = Element.GHOST

    def __init__(self) -> None:
        super().__init__(power=0.0)

    def use(self, user: Pokemon, target: Pokemon, battle: Battle) -> None:
        if target.has_status(effects.SleepEffect.name):
            print(f"{target.label} 已经睡着了。")
            return
        if random.random() < 0.6:
            target.add_status(effects.SleepEffect())
            print(f"{user.label} 摇晃着手指，{target.label} 睡着了！")
        else:
            print(f"{user.label} 的催眠术没有命中。")
