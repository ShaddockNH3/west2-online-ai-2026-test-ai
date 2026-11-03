"""Bonus 进阶 5：正则验证密码（6-18 位，仅英文字母和数字）。"""

import re

PASSWORD_PATTERN = re.compile(r"[A-Za-z0-9]{6,18}")


def is_valid_password(password: str) -> bool:
    """fullmatch 保证整串匹配，而不是「包含一段合法子串」。"""
    return PASSWORD_PATTERN.fullmatch(password) is not None


def main() -> None:
    """演示几组样例。"""
    samples = ["abc123", "a" * 5, "b" * 19, "abc 123", "Abc123xyz", "带中文的密码"]
    for sample in samples:
        print(f"{sample!r:20} -> {is_valid_password(sample)}")


if __name__ == "__main__":
    main()
