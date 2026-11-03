"""宝可梦：基类 + 五个属性族 + 五只具体宝可梦。

设计思路是三层：

1. `Pokemon` 负责所有宝可梦共有的东西（血量、状态、蓄力、护盾）；
2. `GrassPokemon` / `FirePokemon` 这层只实现各自的属性被动；
3. `Bulbasaur` 这层只填数值和技能表。

这样一来，「加一只宝可梦」只需要写几行数值，「改一种属性被动」只影响同属性的所有宝可梦。
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING

import effects
import skills
from elements import Element

if TYPE_CHECKING:
    from battle import Battle
    from effects import StatusEffect
    from skills import Skill


class Pokemon(ABC):
    """所有宝可梦的共同父类。"""

    element: Element

    def __init__(
        self,
        name: str,
        hp: int,
        attack: int,
        defense: int,
        dodge: float,
    ) -> None:
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.base_attack = attack
        self.defense = defense
        self.dodge = dodge
        self.statuses: list[StatusEffect] = []
        self.skill_list: list[Skill] = self.create_skills()
        self.charging_skill: str | None = None
        self.shield = False
        # 由 Battle 设置成「我方」或「对手」，让战斗日志能区分同名宝可梦。
        self.owner = ""

    # ---------- 由子类实现 ----------

    @abstractmethod
    def create_skills(self) -> list[Skill]:
        """返回这只宝可梦的技能表。"""

    # ---------- 基本信息 ----------

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def label(self) -> str:
        """带阵营前缀的名字。双方可能派出同一只宝可梦，日志里必须能分清是谁。"""
        return f"{self.owner}{self.name}" if self.owner else self.name

    @property
    def attack(self) -> int:
        """实际攻击力，默认等于基础攻击力，火焰属性会覆盖它。"""
        return self.base_attack

    def __str__(self) -> str:
        return f"{self.name}（{self.element}属性）"

    # ---------- 血量与状态 ----------

    def heal(self, amount: int, message: str | None = None) -> None:
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        gained = self.hp - before
        if gained <= 0:
            return
        if message:
            print(f"{message}（当前 HP：{self.hp}/{self.max_hp}）")
        else:
            print(f"{self.label} 回复了 {gained} 点 HP")

    def lose_hp(self, amount: int, message: str | None = None) -> None:
        self.hp = max(0, self.hp - amount)
        detail = message if message else f"{self.label} 损失了 {amount} 点 HP"
        print(f"{detail}（剩余 HP：{self.hp}）")
        if not self.alive:
            print(f"{self.label} 昏厥了！")

    def add_status(self, effect: StatusEffect) -> None:
        """同类状态只保留一个，重复附着时刷新持续时间。"""
        for existing in self.statuses:
            if existing.name == effect.name:
                existing.refresh(effect.duration)
                return
        self.statuses.append(effect)

    def has_status(self, name: str) -> bool:
        return any(status.name == name for status in self.statuses)

    def blocks_action(self) -> bool:
        return any(status.blocks_action() for status in self.statuses)

    def tick_statuses(self) -> None:
        """回合结束时结算所有状态，过期的移除。"""
        for status in list(self.statuses):
            status.on_turn_end(self)
            if status.tick():
                self.statuses.remove(status)
                print(f"{self.label} 的「{status.name}」状态解除了。")

    # ---------- 蓄力与护盾 ----------

    def is_charging(self, skill_name: str) -> bool:
        return self.charging_skill == skill_name

    def begin_charge(self, skill_name: str) -> None:
        self.charging_skill = skill_name

    def end_charge(self) -> None:
        self.charging_skill = None

    def raise_shield(self) -> None:
        self.shield = True

    # ---------- 被动钩子 ----------

    def on_turn_start(self) -> None:
        """回合开始时的被动，默认什么也不做。"""
        return None

    def on_dealt_damage(self) -> None:
        """成功造成伤害后的被动，默认什么也不做。"""
        return None

    def modify_incoming_damage(self, damage: int, attacker: Pokemon) -> int:
        """受到伤害前的被动，返回修正后的伤害。"""
        return damage

    def on_take_damage(self, damage: int, attacker: Pokemon) -> None:
        """受到伤害后的被动，默认什么也不做。"""
        return None

    def on_dodge(self, opponent: Pokemon, battle: Battle, allow_counter: bool) -> None:
        """成功闪避后的被动，默认什么也不做。"""
        return None


# ==================== 属性族 ====================


class GrassPokemon(Pokemon):
    """草属性：每回合回复 10% 最大 HP。"""

    element = Element.GRASS

    def on_turn_start(self) -> None:
        heal = max(1, int(self.max_hp * 0.1))
        if self.hp < self.max_hp:
            self.heal(heal, f"{self.label} 借着草属性回复了 {heal} 点 HP")


class FirePokemon(Pokemon):
    """火属性：每次造成伤害叠加 10% 攻击力，最多 4 层。"""

    element = Element.FIRE

    def __init__(self, name: str, hp: int, attack: int, defense: int, dodge: float) -> None:
        super().__init__(name, hp, attack, defense, dodge)
        self.flame_stacks = 0

    @property
    def attack(self) -> int:
        return int(self.base_attack * (1 + 0.1 * self.flame_stacks))

    def on_dealt_damage(self) -> None:
        if self.flame_stacks < 4:
            self.flame_stacks += 1
            print(
                f"{self.label} 的火焰更旺了，攻击力提升到 {self.attack}"
                f"（{self.flame_stacks}/4 层）"
            )


class WaterPokemon(Pokemon):
    """水属性：受到伤害时有 50% 概率减免 30%。"""

    element = Element.WATER

    def modify_incoming_damage(self, damage: int, attacker: Pokemon) -> int:
        if self.shield:
            self.shield = False
            print(f"{self.label} 的护盾抵消了一半伤害！")
            return int(damage * 0.5)
        if random.random() < 0.5:
            print(f"{self.label} 借水流卸掉了一部分力道！")
            return int(damage * 0.7)
        return damage


class ElectricPokemon(Pokemon):
    """电属性：成功闪避后立刻还击一次技能。"""

    element = Element.ELECTRIC

    def on_dodge(self, opponent: Pokemon, battle: Battle, allow_counter: bool) -> None:
        if not allow_counter:
            return
        skill = random.choice(self.skill_list)
        print(f"{self.label} 趁着闪避的空档，立刻回敬 {skill.name}！")
        battle.resolve_skill(self, opponent, skill, allow_counter=False)


class GhostPokemon(Pokemon):
    """幽灵属性：受到伤害时，25% 概率把 30% 的伤害反弹回去。"""

    element = Element.GHOST

    def on_take_damage(self, damage: int, attacker: Pokemon) -> None:
        if random.random() < 0.25 and attacker.alive:
            reflected = max(1, int(damage * 0.3))
            print(f"{self.label} 的怨念反噬了 {attacker.label}！")
            attacker.lose_hp(reflected, f"{attacker.label} 受到 {reflected} 点反噬伤害")


# ==================== 具体宝可梦 ====================


class PikaChu(ElectricPokemon):
    """皮卡丘：高闪避的电系。"""

    def __init__(self) -> None:
        super().__init__("皮卡丘", hp=80, attack=35, defense=5, dodge=0.30)

    def create_skills(self) -> list[Skill]:
        return [skills.Thunderbolt(), skills.QuickAttack()]


class Bulbasaur(GrassPokemon):
    """妙蛙种子：耐久型草系。"""

    def __init__(self) -> None:
        super().__init__("妙蛙种子", hp=100, attack=35, defense=10, dodge=0.10)

    def create_skills(self) -> list[Skill]:
        return [skills.SeedBomb(), skills.ParasiticSeeds()]


class Squirtle(WaterPokemon):
    """杰尼龟：防御最高的水系。"""

    def __init__(self) -> None:
        super().__init__("杰尼龟", hp=80, attack=25, defense=20, dodge=0.20)

    def create_skills(self) -> list[Skill]:
        return [skills.AquaJet(), skills.Shield()]


class Charmander(FirePokemon):
    """小火龙：越打越强的火系。"""

    def __init__(self) -> None:
        super().__init__("小火龙", hp=80, attack=35, defense=15, dodge=0.10)

    def create_skills(self) -> list[Skill]:
        return [skills.Ember(), skills.FlameCharge()]


class Gengar(GhostPokemon):
    """耿鬼：自设计的幽灵属性宝可梦，靠催眠和反伤打乱节奏。"""

    def __init__(self) -> None:
        super().__init__("耿鬼", hp=90, attack=32, defense=8, dodge=0.15)

    def create_skills(self) -> list[Skill]:
        return [skills.ShadowBall(), skills.Hypnosis()]


# 这里存的是「能无参构造出一个 Pokemon 的工厂」，正好就是这些子类本身。
ALL_POKEMON: list[Callable[[], Pokemon]] = [
    PikaChu,
    Bulbasaur,
    Squirtle,
    Charmander,
    Gengar,
]


def create_roster() -> dict[str, Pokemon]:
    """每次开局都新建一批实例，避免上一局的血量带到下一局。"""
    roster: dict[str, Pokemon] = {}
    for pokemon_type in ALL_POKEMON:
        instance = pokemon_type()
        roster[instance.name] = instance
    return roster
