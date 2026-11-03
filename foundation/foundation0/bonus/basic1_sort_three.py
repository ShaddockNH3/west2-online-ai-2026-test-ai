"""Bonus 基础 1：用多种方式把三个整数由大到小输出。"""

import sys


def sort_by_list(x: int, y: int, z: int) -> list[int]:
    """方式一：列表排序。"""
    return sorted([x, y, z], reverse=True)


def sort_by_branch(x: int, y: int, z: int) -> tuple[int, int, int]:
    """方式二：纯 if/else 比较，不借助任何容器。"""
    if x < y:
        x, y = y, x
    if x < z:
        x, z = z, x
    if y < z:
        y, z = z, y
    return x, y, z


def sort_by_removal(x: int, y: int, z: int) -> list[int]:
    """方式三：反复取最大值并从候选里移除。"""
    rest = [x, y, z]
    result = []
    while rest:
        result.append(max(rest))
        rest.remove(max(rest))
    return result


def main() -> None:
    """从命令行参数或标准输入读三个整数并输出。"""
    if len(sys.argv) == 4:
        x, y, z = (int(value) for value in sys.argv[1:])
    else:
        x, y, z = (int(value) for value in input("请输入三个整数（空格分隔）：").split())

    print("列表排序：", sort_by_list(x, y, z))
    print("条件判断：", sort_by_branch(x, y, z))
    print("逐个取最大：", sort_by_removal(x, y, z))


if __name__ == "__main__":
    main()
