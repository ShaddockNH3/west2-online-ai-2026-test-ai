"""外部依赖端口：缓存、支付网关、物流、时钟。

应用层只依赖这些 Protocol；换成真支付、真快递只需要换适配器。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CachePort(Protocol):
    @property
    def enabled(self) -> bool: ...

    async def get_json(self, key: str) -> Any | None: ...

    async def set_json(self, key: str, value: Any) -> None: ...

    async def version(self, namespace: str) -> int: ...

    async def bump(self, namespace: str) -> None: ...

    async def ping(self) -> bool: ...


@dataclass(frozen=True, slots=True)
class ChargeResult:
    """支付网关的返回。失败也带上原因，便于写进支付记录。"""

    ok: bool
    transaction_no: str = ""
    failure_reason: str = ""


class PaymentGatewayError(Exception):
    pass


@runtime_checkable
class PaymentGateway(Protocol):
    async def charge(
        self, *, order_no: str, amount_cents: int, simulate: str = "SUCCESS"
    ) -> ChargeResult: ...


class ShipmentError(Exception):
    pass


@runtime_checkable
class LogisticsPort(Protocol):
    async def create_shipment(self, order_no: str, *, simulate: str = "SUCCESS") -> str: ...


@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime: ...
