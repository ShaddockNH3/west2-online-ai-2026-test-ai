"""战斗流程：回合推进、伤害结算、换人与胜负判定。

伤害公式（固定在这里，技能和宝可梦都不重复实现）：

    伤害 = 攻击力 × 技能倍率 × 属性倍率 − 防御力

得到的结果再交给防守方的被动做修正（水系减伤、护盾、反伤）。
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from elements import describe, multiplier
from pokemon import Pokemon

if TYPE_CHECKING:
    from skills import Skill


class PlayerQuit(Exception):
    """玩家在战斗中选择了退出（或者输入流结束）。"""


def ask(prompt: str, count: int) -> int:
    """读取 1 到 count 的选择，读不到就当作退出。"""
    while True:
        try:
            raw = input(prompt).strip()
        except EOFError as error:
            raise PlayerQuit from error
        if raw.isdigit() and 1 <= int(raw) <= count:
            return int(raw)
        print(f"请输入 1 到 {count} 之间的数字。")


class Battle:
    """一场 3v3 的对战。"""

    def __init__(self, player_team: list[Pokemon], computer_team: list[Pokemon]) -> None:
        self.player_team = player_team
        self.computer_team = computer_team
        for mon in player_team:
            mon.owner = "我方"
        for mon in computer_team:
            mon.owner = "对手"
        self.player = player_team[0]
        self.computer = computer_team[0]
        self.round = 1
        # 当前这次技能是否允许触发「闪避反击」，反击技能执行期间会被置为 False。
        self.allow_counter = True

    # ---------- 伤害结算 ----------

    def deal_damage(
        self,
        attacker: Pokemon,
        defender: Pokemon,
        skill: Skill,
        dodge_bonus: float = 0.0,
    ) -> bool:
        """结算一次技能伤害，返回是否命中。"""
        if random.random() < defender.dodge + dodge_bonus:
            print(f"{defender.label} 闪开了 {skill.name}！")
            defender.on_dodge(attacker, self, allow_counter=self.allow_counter)
            return False

        rate = multiplier(skill.element, defender.element)
        raw = attacker.attack * skill.power * rate
        damage = max(1, int(raw - defender.defense))
        damage = defender.modify_incoming_damage(damage, attacker)
        if damage <= 0:
            print(f"{defender.label} 硬抗了下来，没有受到伤害。")
            return True

        defender.hp = max(0, defender.hp - damage)
        print(f"{defender.label} 受到了 {damage} 点伤害！剩余 HP：{defender.hp}")
        tip = describe(rate)
        if tip:
            print(f"  {tip}")

        attacker.on_dealt_damage()
        defender.on_take_damage(damage, attacker)
        if not defender.alive:
            print(f"{defender.label} 昏厥了！")
        return True

    def resolve_skill(
        self,
        user: Pokemon,
        target: Pokemon,
        skill: Skill,
        allow_counter: bool = True,
    ) -> None:
        """执行一次技能。

        `allow_counter=False` 用于「闪避反击」触发的技能，避免双方来回反击无限递归。
        """
        if not user.alive or not target.alive:
            return

        print(f"{user.label} 使用了 {skill.name}！")
        previous = self.allow_counter
        self.allow_counter = allow_counter
        try:
            skill.use(user, target, self)
        finally:
            self.allow_counter = previous

    # ---------- 玩家与电脑的回合 ----------

    def player_action(self) -> None:
        skills = self.player.skill_list
        print(f"\n{self.player.label} 的技能：")
        for order, skill in enumerate(skills, start=1):
            charge = "（需蓄力）" if skill.charge_turns else ""
            print(f"  {order}. {skill.name}{charge}")
        switch_index = len(skills) + 1
        print(f"  {switch_index}. 换人")

        choice = ask("选择一个行动：", switch_index)
        if choice == switch_index:
            self.switch_player()
            return

        self.resolve_skill(self.player, self.computer, skills[choice - 1])

    def computer_action(self) -> None:
        skills = self.computer.skill_list
        super_effective = [
            skill for skill in skills if multiplier(skill.element, self.player.element) > 1
        ]
        if super_effective and random.random() < 0.6:
            skill = random.choice(super_effective)
        else:
            skill = random.choice(skills)
        self.resolve_skill(self.computer, self.player, skill)

    def switch_player(self, forced: bool = False) -> None:
        """换人。`forced=True` 表示当前宝可梦已经昏厥，必须换，不能取消。"""
        candidates = [mon for mon in self.player_team if mon.alive and mon is not self.player]
        if not candidates:
            print("没有可以换上场的宝可梦了。")
            return

        print("\n可以换上场的宝可梦：")
        for order, mon in enumerate(candidates, start=1):
            print(f"  {order}. {mon}  HP：{mon.hp}/{mon.max_hp}")
        if not forced:
            print(f"  {len(candidates) + 1}. 算了，不换")

        limit = len(candidates) if forced else len(candidates) + 1
        choice = ask("请选择：", limit)
        if not forced and choice == limit:
            return

        self.player = candidates[choice - 1]
        print(f"你换上了 {self.player}！")

    def switch_computer(self) -> None:
        candidates = [mon for mon in self.computer_team if mon.alive]
        if not candidates:
            return
        self.computer = random.choice(candidates)
        print(f"对手换上了 {self.computer}！")

    # ---------- 胜负 ----------

    def check_finished(self) -> str | None:
        if all(not mon.alive for mon in self.computer_team):
            return "win"
        if all(not mon.alive for mon in self.player_team):
            return "lose"
        return None

    # ---------- 主循环 ----------

    def run(self) -> str:
        """跑完整场战斗，返回 win 或 lose。"""
        print("\n===== 对战开始 =====")
        print(f"你的首发：{self.player}  HP：{self.player.hp}/{self.player.max_hp}")
        print(f"对手首发：{self.computer}  HP：{self.computer.hp}/{self.computer.max_hp}")

        while True:
            print(f"\n---------- 第 {self.round} 回合 ----------")

            # 回合开始的被动：草属性回血
            self.player.on_turn_start()
            self.computer.on_turn_start()

            # 玩家行动
            if self.player.blocks_action():
                print(f"{self.player.label} 动弹不得，无法行动！")
            else:
                self.player_action()

            # 对手被打倒：先判定胜负，再决定要不要换人
            computer_can_act = True
            if not self.computer.alive:
                if self.check_finished() == "win":
                    print("\n对手的宝可梦全部昏厥，你赢了！")
                    return "win"
                self.switch_computer()
                computer_can_act = False  # 刚上场的宝可梦这一回合不能动

            # 电脑行动
            if computer_can_act:
                if self.computer.blocks_action():
                    print(f"{self.computer.label} 动弹不得，无法行动！")
                else:
                    self.computer_action()

            if not self.player.alive:
                if self.check_finished() == "lose":
                    print("\n你的宝可梦全部昏厥，你输了。")
                    return "lose"
                self.switch_player(forced=True)

            # 回合结束：结算异常状态
            for mon in (self.player, self.computer):
                if mon.alive:
                    mon.tick_statuses()

            finished = self.check_finished()
            if finished == "win":
                print("\n对手的宝可梦全部昏厥，你赢了！")
                return "win"
            if finished == "lose":
                print("\n你的宝可梦全部昏厥，你输了。")
                return "lose"

            # 被状态伤害打倒的话，这里补一次换人
            if not self.player.alive:
                self.switch_player(forced=True)
            if not self.computer.alive:
                self.switch_computer()

            self.round += 1
