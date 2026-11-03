"""学长改名问题：模拟 m 次「移情别恋」，输出 1 号学长最后的名字。

规则：如果 u 喜欢上了 v，u 会立刻把自己的名字改为 "I_love_" + v 当前的名字。
注意读取的是 v「当前」的名字，而不是初始名字，所以必须按输入顺序逐条模拟。
"""

import sys

PREFIX = "I_love_"


def simulate(names: list[str], records: list[tuple[int, int]]) -> list[str]:
    """按顺序执行所有改名记录，返回最终的名字列表（下标 1 起用）。"""
    for u, v in records:
        names[u] = PREFIX + names[v]
    return names


def main() -> None:
    """解析输入并输出 1 号学长的名字。"""
    data = sys.stdin.read().split()
    cursor = 0

    n = int(data[cursor])
    cursor += 1
    names = [""] * (n + 1)
    for index in range(1, n + 1):
        names[index] = data[cursor]
        cursor += 1

    m = int(data[cursor])
    cursor += 1
    records: list[tuple[int, int]] = []
    for _ in range(m):
        u, v = int(data[cursor]), int(data[cursor + 1])
        cursor += 2
        records.append((u, v))

    print(simulate(names, records)[1])


if __name__ == "__main__":
    main()
