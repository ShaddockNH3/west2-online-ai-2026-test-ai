"""时间、金额与编号工具。"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

MAX_AMOUNT_CENTS = 100_000_000  # 一百万元，防止误填


def utcnow() -> datetime:
    """统一使用 naive UTC，避免 SQLite 读回来丢时区后再比较出错。"""
    return datetime.now(UTC).replace(tzinfo=None)


def iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.replace(microsecond=0).isoformat() + "Z"


def yuan(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"


def to_cents(value: str | int | Decimal, *, field: str = "金额") -> int:
    """把用户填的金额（元）转成整数分，拒绝超过两位小数和负值。"""
    if isinstance(value, bool):
        raise ValueError(f"{field}格式不正确")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field}格式不正确") from exc
    if amount < 0:
        raise ValueError(f"{field}不能为负数")
    if amount.as_tuple().exponent < -2:
        raise ValueError(f"{field}最多两位小数")
    cents = int(amount * 100)
    if cents > MAX_AMOUNT_CENTS:
        raise ValueError(f"{field}超出上限")
    return cents


def new_id(prefix: str, length: int = 10) -> str:
    return f"{prefix}{secrets.token_hex(length // 2)}"


def order_no() -> str:
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S") + f"{secrets.randbelow(10000):04d}"


def parse_bool(value: str | None, *, field: str = "参数") -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise ValueError(f"{field}必须是布尔值")
