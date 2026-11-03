"""宝可梦对战：命令行入口。

运行方式：

    python main.py
"""

from __future__ import annotations

import random

from battle import Battle, PlayerQuit, ask
from pokemon import Pokemon, create_roster

TEAM_SIZE = 3


def show_team(team: list[Pokemon], title: str) -> None:
    print(title)
    for order, mon in enumerate(team, start=1):
        print(f"  {order}. {mon}")


def choose_team(roster: dict[str, Pokemon]) -> list[Pokemon]:
    """让玩家挑选三只不重复的宝可梦。"""
    names = list(roster)
    print(f"请选择 {TEAM_SIZE} 个宝可梦用于组成你的队伍：")
    for order, name in enumerate(names, start=1):
        mon = roster[name]
        print(
            f"  {order}. {mon}  HP {mon.max_hp} 攻击 {mon.base_attack} "
            f"防御 {mon.defense} 闪避 {int(mon.dodge * 100)}%"
        )

    team: list[Pokemon] = []
    while len(team) < TEAM_SIZE:
        choice = ask(f"输入数字选择第 {len(team) + 1} 只宝可梦：", len(names))
        mon = roster[names[choice - 1]]
        if mon in team:
            print(f"{mon.name} 已经在队伍里了，换一只吧。")
            continue
        team.append(mon)

    show_team(team, "\n你的队伍：")
    return team


def choose_lead(team: list[Pokemon]) -> Pokemon:
    """从队伍里选首发。"""
    print("\n请选择你的首发宝可梦：")
    for order, mon in enumerate(team, start=1):
        print(f"  {order}. {mon}")
    choice = ask("输入数字选择：", len(team))
    chosen = team[choice - 1]
    print(f"你选择了 {chosen}！")
    return chosen


def main() -> None:
    """组队 → 选首发 → 开打。"""
    print("========== 宝可梦对战 ==========")
    player_team = choose_team(create_roster())

    # 电脑用另一批实例，避免和玩家共用同一只宝可梦。
    computer_roster = create_roster()
    computer_team = random.sample(list(computer_roster.values()), TEAM_SIZE)
    show_team(computer_team, "\n对手的队伍：")
    print(f"对手派出了 {computer_team[0]}！")

    lead = choose_lead(player_team)
    player_team.remove(lead)
    player_team.insert(0, lead)

    battle = Battle(player_team, computer_team)
    try:
        battle.run()
    except PlayerQuit:
        print("\n你退出了对战。")
    except KeyboardInterrupt:
        print("\n对战被中断。")


if __name__ == "__main__":
    main()
