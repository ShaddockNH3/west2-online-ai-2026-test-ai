"""洛谷 P1046 陶陶摘苹果：统计陶陶能够到的苹果数量。

陶陶把手伸直的最大高度是「身高 + 30 厘米的板凳高度」，
高度不超过这个值的苹果都能摘到。
"""

import sys

BENCH_HEIGHT = 30


def count_reachable(apples: list[int], hand_height: int) -> int:
    """返回高度不超过 hand_height 的苹果个数。"""
    return sum(1 for apple in apples if apple <= hand_height)


def main() -> None:
    """读取 10 个苹果高度、陶陶的身高，输出能摘到的苹果数。"""
    data = sys.stdin.read().split()
    apples = [int(value) for value in data[:10]]
    height = int(data[10])
    print(count_reachable(apples, height + BENCH_HEIGHT))


if __name__ == "__main__":
    main()
