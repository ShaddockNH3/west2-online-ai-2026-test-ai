"""业务异常。路由里直接 raise，统一由异常处理器转成 JSON。"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, message: str = "请求有误", details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ValidationError(AppError):
    status_code = 400
    code = "INVALID_PARAM"


class AuthError(AppError):
    status_code = 401
    code = "AUTH_REQUIRED"


class TokenExpiredError(AppError):
    status_code = 401
    code = "TOKEN_EXPIRED"


class PermissionDenied(AppError):
    status_code = 403
    code = "FORBIDDEN"


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"


class StockError(ConflictError):
    code = "STOCK_NOT_ENOUGH"


class ExternalServiceError(AppError):
    status_code = 502
    code = "EXTERNAL_SERVICE_ERROR"
