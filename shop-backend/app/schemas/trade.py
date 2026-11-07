from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from app.schemas.base import StrictModel


class CartAddIn(StrictModel):
    skuId: int = Field(gt=0)
    quantity: int = Field(gt=0, le=999)


class CartPatch(StrictModel):
    quantity: int = Field(gt=0, le=999)


class CartItemIdsIn(StrictModel):
    cartItemIds: list[int] = Field(min_length=1, max_length=50)
    addressId: int = Field(gt=0)


class CreateOrderIn(CartItemIdsIn):
    requestId: str = Field(min_length=8, max_length=64)
    remark: str = Field(default="", max_length=255)

    @field_validator("cartItemIds")
    @classmethod
    def check_ids(cls, value: list[int]) -> list[int]:
        if any(item <= 0 for item in value):
            raise ValueError("cartItemIds 必须是正整数")
        return list(dict.fromkeys(value))


class PaymentIn(StrictModel):
    result: Literal["SUCCESS", "FAILURE"]
