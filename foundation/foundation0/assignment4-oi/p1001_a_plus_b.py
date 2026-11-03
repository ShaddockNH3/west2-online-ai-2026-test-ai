"""洛谷 P1001 A+B Problem：读入两个整数，输出它们的和。"""

import sys


def solve(a: int, b: int) -> int:
    """返回两个整数之和。"""
    return a + b


def main() -> None:
    """从标准输入读取两个整数并输出结果。"""
    data = sys.stdin.read().split()
    a, b = int(data[0]), int(data[1])
    print(solve(a, b))


if __name__ == "__main__":
    main()
