from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from app.schemas.base import StrictModel


class CategoryIn(StrictModel):
    name: str = Field(min_length=1, max_length=64)
    sortOrder: int = Field(default=0, ge=0, le=9999)


class CategoryPatch(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    sortOrder: int | None = Field(default=None, ge=0, le=9999)
    status: Literal["ENABLED", "DISABLED"] | None = None


class ProductIn(StrictModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=2000)
    categoryId: int = Field(gt=0)
    coverUrl: str = Field(default="", max_length=255)


class ProductPatch(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=2000)
    categoryId: int | None = Field(default=None, gt=0)
    coverUrl: str | None = Field(default=None, max_length=255)


class ProductStatusIn(StrictModel):
    status: Literal["ON_SALE", "OFF_SALE"]


class SkuIn(StrictModel):
    specs: dict[str, str] = Field(default_factory=dict)
    price: str = Field(min_length=1, max_length=16)
    skuCode: str | None = Field(default=None, min_length=1, max_length=64)
    stock: int = Field(default=0, ge=0, le=1_000_000)
    status: Literal["ON_SALE", "OFF_SALE"] = "ON_SALE"

    @field_validator("specs")
    @classmethod
    def check_specs(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 8:
            raise ValueError("规格项不能超过 8 个")
        for key, item in value.items():
            if not key.strip() or len(key) > 32 or len(item) > 64:
                raise ValueError("规格名与规格值长度不合法")
        return value


class SkuPatch(StrictModel):
    specs: dict[str, str] | None = None
    price: str | None = Field(default=None, min_length=1, max_length=16)
    status: Literal["ON_SALE", "OFF_SALE"] | None = None
