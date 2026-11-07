from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.base import StrictModel


class ActivitySkuIn(StrictModel):
    skuId: int = Field(gt=0)
    activityPrice: str = Field(min_length=1, max_length=16)
    saleQuota: int | None = Field(default=None, ge=1, le=1_000_000)
    perUserLimit: int | None = Field(default=None, ge=1, le=100)


class ActivityIn(StrictModel):
    name: str = Field(min_length=1, max_length=64)
    type: Literal["FIXED_PRICE", "FLASH_SALE"] = "FIXED_PRICE"
    startsAt: str = Field(min_length=10, max_length=40)
    endsAt: str = Field(min_length=10, max_length=40)
    description: str = Field(default="", max_length=255)
    status: Literal["DRAFT", "ACTIVE", "DISABLED"] = "DRAFT"
    skus: list[ActivitySkuIn] = Field(default_factory=list, max_length=50)


class ActivityPatch(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    startsAt: str | None = Field(default=None, min_length=10, max_length=40)
    endsAt: str | None = Field(default=None, min_length=10, max_length=40)
    description: str | None = Field(default=None, max_length=255)
    status: Literal["DRAFT", "ACTIVE", "DISABLED"] | None = None


class FlashSaleIn(StrictModel):
    skuId: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)
    addressId: int = Field(gt=0)
    requestId: str = Field(min_length=8, max_length=64)
