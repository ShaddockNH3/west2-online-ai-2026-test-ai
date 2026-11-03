"""Bonus 进阶 1：装饰器输出函数名、开始时间、结束时间与运行时长。"""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any


def timer(func: Callable[..., Any]) -> Callable[..., Any]:
    """开始与结束时各打一行日志，结束时附运行时长。"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        print(f"开始执行 {func.__name__}（{time.strftime('%H:%M:%S')}）")
        try:
            return func(*args, **kwargs)
        finally:
            cost = (time.perf_counter() - start) * 1000
            print(f"结束执行 {func.__name__}（{time.strftime('%H:%M:%S')}），耗时 {cost:.2f} ms")

    return wrapper


@timer
def sum_slow(n: int) -> int:
    """一个用来被计时的慢函数。"""
    total = 0
    for i in range(n):
        total += i
    time.sleep(0.05)
    return total


def main() -> None:
    """演示。"""
    sum_slow(100000)


if __name__ == "__main__":
    main()
