"""Bonus 基础 8：斗地主随机发牌（不分花色、不排序）。

54 张牌发给 3 个玩家，每人 17 张，剩下 3 张作为底牌，
结果分别写入 player1.txt、player2.txt、player3.txt、others.txt。
"""

import random

HAND_SIZE = 17
OUTPUT_FILES = ("player1.txt", "player2.txt", "player3.txt", "others.txt")


def build_deck() -> list[str]:
    """构造 54 张牌。"""
    ranks = [str(point) for point in range(3, 11)] + ["J", "Q", "K", "A", "2"]
    jokers = ["小王", "大王"]
    return ranks * 4 + jokers


def deal() -> tuple[list[str], list[str], list[str], list[str]]:
    """洗牌并分发。"""
    deck = build_deck()
    random.shuffle(deck)
    hands = [deck[i * HAND_SIZE:(i + 1) * HAND_SIZE] for i in range(3)]
    bottom = deck[3 * HAND_SIZE:]
    return hands[0], hands[1], hands[2], bottom


def main() -> None:
    """发牌并写文件。"""
    p1, p2, p3, bottom = deal()
    for filename, cards in zip(OUTPUT_FILES, (p1, p2, p3, bottom)):
        with open(filename, "w", encoding="utf-8") as handle:
            handle.write(" ".join(cards))
        print(f"{filename}: {' '.join(cards)}")


if __name__ == "__main__":
    main()
