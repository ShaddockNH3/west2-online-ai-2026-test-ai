"""Bonus 基础 6：统计列表中各数字出现的次数，以字典返回。"""


def count_numbers(numbers: list[int]) -> dict[int, int]:
    """统计每个数字出现的次数。"""
    counts: dict[int, int] = {}
    for number in numbers:
        counts[number] = counts.get(number, 0) + 1
    return counts


def main() -> None:
    """演示。"""
    data = [1, 2, 2, 3, 3, 3, 4, 4, 4, 4]
    print("列表：", data)
    print("统计：", count_numbers(data))


if __name__ == "__main__":
    main()
