"""编号工具与兼容再导出。

时间、金额的实现在 `app.domain.money`，这里转出一份，
免得调用方为了一个 iso() 到处改 import。
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from app.domain.money import (  # noqa: F401 - 兼容再导出
    MAX_AMOUNT_CENTS,
    iso,
    to_cents,
    utcnow,
    yuan,
)


def new_id(prefix: str, length: int = 10) -> str:
    return f"{prefix}{secrets.token_hex(length // 2)}"


def order_no() -> str:
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S") + f"{secrets.randbelow(10000):04d}"
