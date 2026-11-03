"""Bonus 基础 4：删除列表中的字符串元素，整数升序排序后输出。"""


def filter_and_sort(mixed: list) -> list[int]:
    """保留 int（排除布尔值），升序返回。"""
    numbers = [item for item in mixed if isinstance(item, int) and not isinstance(item, bool)]
    return sorted(numbers)


def main() -> None:
    """演示。"""
    mixed = [3, "hello", 1, "world", 2, "42", 5]
    print("原列表：", mixed)
    print("过滤排序后：", filter_and_sort(mixed))


if __name__ == "__main__":
    main()
