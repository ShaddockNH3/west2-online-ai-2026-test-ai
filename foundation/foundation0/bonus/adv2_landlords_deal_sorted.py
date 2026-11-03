"""Bonus 进阶 2：斗地主发牌，结果按点数从大到小排序后写文件。"""

import random

HAND_SIZE = 17
OUTPUT_FILES = ("player1.txt", "player2.txt", "player3.txt", "others.txt")

# 点数从大到小的顺序：大王 > 小王 > 2 > A > K > ... > 3
RANK_ORDER = ["大王", "小王", "2", "A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3"]


def build_deck() -> list[str]:
    """构造 54 张牌（花色不影响排序，只发一份每张牌）。"""
    ranks = [str(point) for point in range(3, 11)] + ["J", "Q", "K", "A", "2"]
    return ranks * 4 + ["小王", "大王"]


def deal() -> tuple[list[str], list[str], list[str], list[str]]:
    """洗牌、分发并排序。"""
    deck = build_deck()
    random.shuffle(deck)
    hands = [sorted(deck[i * HAND_SIZE:(i + 1) * HAND_SIZE], key=RANK_ORDER.index)
             for i in range(3)]
    bottom = sorted(deck[3 * HAND_SIZE:], key=RANK_ORDER.index)
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
