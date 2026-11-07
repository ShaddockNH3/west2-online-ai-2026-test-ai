"""请求体模型。extra=forbid 是关键：注册时传 role 会被直接拒绝，不能自我提权。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

USERNAME_PATTERN = r"^[A-Za-z0-9_]{3,32}$"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RegisterIn(StrictModel):
    username: str = Field(pattern=USERNAME_PATTERN)
    password: str = Field(min_length=8, max_length=64)
    nickname: str | None = Field(default=None, max_length=32)


class LoginIn(StrictModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=64)


class RefreshIn(StrictModel):
    refreshToken: str = Field(min_length=10)


class UpdateMeIn(StrictModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=32)
    email: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=32)

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return value
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("邮箱格式不正确")
        return value


class ChangePasswordIn(StrictModel):
    oldPassword: str = Field(min_length=1, max_length=64)
    newPassword: str = Field(min_length=8, max_length=64)


class AddressIn(StrictModel):
    receiver: str = Field(min_length=1, max_length=64)
    phone: str = Field(min_length=5, max_length=32)
    detail: str = Field(min_length=5, max_length=255)
    isDefault: bool = False

    @field_validator("phone")
    @classmethod
    def check_phone(cls, value: str) -> str:
        cleaned = value.replace(" ", "").replace("-", "")
        if not cleaned.isdigit() or not 5 <= len(cleaned) <= 20:
            raise ValueError("联系电话格式不正确")
        return value


class AddressPatch(StrictModel):
    receiver: str | None = Field(default=None, min_length=1, max_length=64)
    phone: str | None = Field(default=None, min_length=5, max_length=32)
    detail: str | None = Field(default=None, min_length=5, max_length=255)
    isDefault: bool | None = None


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


class InventoryIn(StrictModel):
    quantity: int = Field(gt=0, le=1_000_000)
    reason: str = Field(default="采购入库", max_length=255)


class InventorySetIn(StrictModel):
    available: int = Field(ge=0, le=1_000_000)
    reason: str = Field(default="盘点调整", max_length=255)


class ShipIn(StrictModel):
    simulate: Literal["SUCCESS", "FAIL"] = "SUCCESS"


class FlashSaleIn(StrictModel):
    skuId: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)
    addressId: int = Field(gt=0)
    requestId: str = Field(min_length=8, max_length=64)


class JobRetryIn(StrictModel):
    reset_attempts: bool = False


Json = dict[str, Any]
