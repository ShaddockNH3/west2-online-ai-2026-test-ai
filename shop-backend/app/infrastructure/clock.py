"""系统时钟：唯一允许直接用 now() 的地方，方便测试替换。"""

from __future__ import annotations

from datetime import datetime

from app.domain.money import utcnow


class SystemClock:
    def now(self) -> datetime:
        return utcnow()
