from __future__ import annotations

from pydantic import Field, field_validator

from app.schemas.base import StrictModel

USERNAME_PATTERN = r"^[A-Za-z0-9_]{3,32}$"


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
