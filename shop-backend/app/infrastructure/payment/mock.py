"""mock 支付网关：本地模拟，成功/失败由调用方指定。"""

from __future__ import annotations

import asyncio
import secrets

from app.application.ports.services import ChargeResult


class MockPaymentGateway:
    """换成真渠道时，实现同样的 `charge` 即可，应用层不用改。"""

    async def charge(
        self, *, order_no: str, amount_cents: int, simulate: str = "SUCCESS"
    ) -> ChargeResult:
        await asyncio.sleep(0)  # 占位：真实网关这里是一次网络往返
        if amount_cents <= 0:
            return ChargeResult(ok=False, failure_reason="支付金额必须大于 0")
        if simulate == "FAILURE":
            return ChargeResult(ok=False, failure_reason="模拟支付失败")
        return ChargeResult(
            ok=True,
            transaction_no=f"MOCK{secrets.token_hex(8)}",
        )
