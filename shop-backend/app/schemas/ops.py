from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from app.schemas.base import StrictModel


class InventoryIn(StrictModel):
    quantity: int = Field(gt=0, le=1_000_000)
    reason: str = Field(default="采购入库", max_length=255)


class InventorySetIn(StrictModel):
    available: int = Field(ge=0, le=1_000_000)
    reason: str = Field(default="盘点调整", max_length=255)


class ShipIn(StrictModel):
    simulate: Literal["SUCCESS", "FAIL"] = "SUCCESS"


class JobRetryIn(StrictModel):
    reset_attempts: bool = False


Json = dict[str, Any]
