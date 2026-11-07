"""本地模拟物流：不依赖任何外部平台。"""

from __future__ import annotations

import asyncio
import secrets


class LogisticsError(Exception):
    pass


async def create_shipment(order_no: str, *, simulate: str = "SUCCESS") -> str:
    # 模拟一次网络往返
    await asyncio.sleep(0.01)
    if simulate == "FAIL":
        raise LogisticsError("模拟物流接口暂时不可用，可稍后重试")
    return f"SF{order_no[-8:]}{secrets.randbelow(1000000):06d}"
