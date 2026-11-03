"""洛谷 P5737 闰年展示：输出区间 [x, y] 内的所有闰年。"""

import sys


def is_leap_year(year: int) -> bool:
    """判断是否为闰年：能被 4 整除且不能被 100 整除，或者能被 400 整除。"""
    return year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)


def collect_leap_years(start: int, end: int) -> list[int]:
    """返回闭区间 [start, end] 内的全部闰年。"""
    return [year for year in range(start, end + 1) if is_leap_year(year)]


def main() -> None:
    """第一行输出闰年个数，第二行按顺序输出这些年份。"""
    data = sys.stdin.read().split()
    start, end = int(data[0]), int(data[1])
    years = collect_leap_years(start, end)
    print(len(years))
    print(" ".join(str(year) for year in years))


if __name__ == "__main__":
    main()
