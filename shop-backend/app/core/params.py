"""请求参数解析。不用框架的隐式绑定，错误信息才可控。"""

from __future__ import annotations

import json

from blacksheep import Request
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.core.errors import ValidationError


def _validate[TModel: BaseModel](model: type[TModel], payload: object) -> TModel:
    if not isinstance(payload, dict):
        raise ValidationError("请求体必须是 JSON 对象")
    try:
        return model.model_validate(payload)
    except PydanticValidationError as exc:
        details = [
            {
                "field": ".".join(str(part) for part in error["loc"]) or "body",
                "message": error["msg"],
            }
            for error in exc.errors()
        ]
        raise ValidationError("参数校验失败", details) from exc


async def read_body[TModel: BaseModel](request: Request, model: type[TModel]) -> TModel:
    try:
        payload = await request.json()
    except Exception as exc:  # noqa: BLE001 - 框架抛的解析异常类型不统一
        raise ValidationError("请求体必须是合法的 JSON") from exc
    return _validate(model, payload)


async def read_body_optional[TModel: BaseModel](
    request: Request, model: type[TModel], default: TModel
) -> TModel:
    """请求体可以完全省略，用于 all-optional 的接口（例如发货）。"""
    raw = await request.text()
    if not raw or not raw.strip():
        return default
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError("请求体必须是合法的 JSON") from exc
    return _validate(model, payload)


def query_str(request: Request, name: str, default: str | None = None) -> str | None:
    values = request.query.get(name)
    if not values:
        return default
    return values[0]


def query_int(
    request: Request,
    name: str,
    default: int | None = None,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int | None:
    raw = query_str(request, name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValidationError(f"{name} 必须是整数") from exc
    if minimum is not None and value < minimum:
        raise ValidationError(f"{name} 不能小于 {minimum}")
    if maximum is not None and value > maximum:
        raise ValidationError(f"{name} 不能大于 {maximum}")
    return value


def pagination(request: Request, *, default_size: int = 20, max_size: int = 100) -> tuple[int, int]:
    page = query_int(request, "page", 1, minimum=1) or 1
    page_size = query_int(request, "pageSize", default_size, minimum=1, maximum=max_size)
    return page, page_size or default_size


def path_int(value: str, field: str = "id") -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} 必须是整数") from exc
    if parsed <= 0:
        raise ValidationError(f"{field} 必须是正整数")
    return parsed
