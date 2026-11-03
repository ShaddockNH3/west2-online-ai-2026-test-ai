"""Bonus 基础 2：九九乘法表。"""


def print_table() -> None:
    """打印九九乘法表。"""
    for i in range(1, 10):
        for j in range(1, i + 1):
            print(f"{j}x{i}={i * j}", end="\t")
        print()


def main() -> None:
    """入口。"""
    print_table()


if __name__ == "__main__":
    main()
