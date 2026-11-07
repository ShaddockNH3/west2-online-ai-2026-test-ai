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


def register_exception_handlers(app) -> None:  # type: ignore[no-untyped-def]
    """把业务异常、框架异常和兜底异常统一成 `{code, message, details}`。"""
    import logging

    from blacksheep.exceptions import HTTPException
    from blacksheep.server.responses import json

    from app.core.logging import request_id_of

    @app.exception_handler(AppError)
    async def handle_app_error(application, request, exc: AppError):  # type: ignore[no-untyped-def]
        payload = {"code": exc.code, "message": exc.message}
        if exc.details is not None:
            payload["details"] = exc.details
        return json(payload, status=exc.status_code)

    @app.exception_handler(HTTPException)
    async def handle_http_error(application, request, exc: HTTPException):  # type: ignore[no-untyped-def]
        return json(
            {"code": "HTTP_ERROR", "message": str(exc.message or "请求失败")},
            status=exc.status,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(application, request, exc: Exception):  # type: ignore[no-untyped-def]
        logging.getLogger("app").exception(
            "unhandled error on %s %s request_id=%s",
            request.method,
            request.path,
            request_id_of(request),
        )
        # 对外只给通用描述，堆栈留在日志里
        return json({"code": "INTERNAL_ERROR", "message": "服务器内部错误，请稍后重试"}, status=500)
