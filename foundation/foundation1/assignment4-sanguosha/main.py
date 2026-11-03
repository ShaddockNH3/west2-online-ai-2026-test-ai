"""三国杀 demo：命令行入口。

运行方式：

    python main.py            # 玩家随机武将
    python main.py --seed 7   # 固定随机种子，方便复现
"""

from __future__ import annotations

import argparse
import random

from cards import Deck
from game import Game, PlayerQuit
from generals import GENERALS, General
from player import Player


def assign_identities(rng: random.Random) -> list[str]:
    """5 人标准局：主公、忠臣、内奸各一名，反贼两名。"""
    identities = ["主公", "忠臣", "反贼", "反贼", "内奸"]
    rng.shuffle(identities)
    return identities


def pick_generals(rng: random.Random, count: int = 5) -> list[General]:
    """随机抽 count 名武将，保证四个阵营各出一人。"""
    by_kingdom: dict[str, list[General]] = {}
    for general in GENERALS.values():
        by_kingdom.setdefault(general.kingdom, []).append(general)
    chosen: list[General] = []
    for kingdom in sorted(by_kingdom):
        chosen.append(rng.choice(by_kingdom[kingdom]))
    remaining = [g for g in GENERALS.values() if g not in chosen]
    rng.shuffle(remaining)
    return chosen + remaining[: count - len(chosen)]


def show_generals(generals: list[General]) -> None:
    """把本局的武将展示给玩家。"""
    from generals import SKILL_HELP  # 局部导入避免循环依赖观感

    print("\n本局武将：")
    for general in generals:
        skills = "、".join(f"{skill}（{SKILL_HELP[skill]}）" for skill in general.skills)
        print(f"  {general}  技能：{skills}")


def main() -> None:
    """建局、发身份、开打。"""
    parser = argparse.ArgumentParser(description="三国杀 demo")
    parser.add_argument("--seed", type=int, default=None, help="固定随机种子")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    identities = assign_identities(rng)
    generals = pick_generals(rng)

    # 主公固定坐 1 号位（也是玩家习惯的视角起点），把主公身份分给人类玩家
    identities[identities.index("主公")] = identities[0]
    identities[0] = "主公"

    show_generals(generals)
    print("\n你的身份：主公！其余玩家的身份暂时保密（AI 直接知晓彼此身份，属简化）。")
    print("场上配置：主公（你）、忠臣、内奸各一名，反贼两名。\n")

    players = [
        Player(seat=index, name="你" if index == 0 else f"AI {index}",
               identity=identities[index], general=generals[index])
        for index in range(len(identities))
    ]

    game = Game(players, Deck(seed=args.seed))
    try:
        winner = game.run()
        print(f"\n===== 游戏结束，【{winner}】获胜 =====")
        for player in players:
            print(player)
    except PlayerQuit:
        print("\n你退出了游戏。")


if __name__ == "__main__":
    main()
