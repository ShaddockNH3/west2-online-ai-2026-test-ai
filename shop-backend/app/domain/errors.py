"""领域异常：只表达「出了什么事」，不关心 HTTP 状态码。

映射到状态码是接口层的事，见 `app/api/errors.py`。
"""

from __future__ import annotations

from typing import Any


class DomainError(Exception):
    code = "DOMAIN_ERROR"

    def __init__(self, message: str = "请求有误", details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ValidationError(DomainError):
    code = "INVALID_PARAM"


class AuthError(DomainError):
    code = "AUTH_REQUIRED"


class TokenExpiredError(DomainError):
    code = "TOKEN_EXPIRED"


class PermissionDenied(DomainError):
    code = "FORBIDDEN"


class NotFoundError(DomainError):
    code = "NOT_FOUND"


class ConflictError(DomainError):
    code = "CONFLICT"


class DuplicateRequestError(ConflictError):
    code = "DUPLICATE_REQUEST"


class StockError(ConflictError):
    code = "STOCK_NOT_ENOUGH"


class ExternalServiceError(DomainError):
    code = "EXTERNAL_SERVICE_ERROR"


__all__ = [
    "ConflictError",
    "AuthError",
    "DomainError",
    "DuplicateRequestError",
    "ExternalServiceError",
    "NotFoundError",
    "PermissionDenied",
    "StockError",
    "TokenExpiredError",
    "ValidationError",
]
