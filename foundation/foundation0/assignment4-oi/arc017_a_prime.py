"""AtCoder ARC017 A 素数判定：判断一个正整数是否为素数。

N >= 2 时只需要检查到 sqrt(N) 即可，因为因数总是成对出现。
"""

import sys


def is_prime(number: int) -> bool:
    """判断 number 是否为素数。"""
    if number < 2:
        return False
    divisor = 2
    while divisor * divisor <= number:
        if number % divisor == 0:
            return False
        divisor += 1
    return True


def main() -> None:
    """是素数输出 YES，否则输出 NO。"""
    data = sys.stdin.read().split()
    number = int(data[0])
    print("YES" if is_prime(number) else "NO")


if __name__ == "__main__":
    main()
