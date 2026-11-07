"""异常 → HTTP 的翻译层。

领域层抛的是「库存不足」「找不到订单」，这里决定它对应 409 还是 404。
换协议（gRPC、CLI）只需要换这一层。
"""

from __future__ import annotations

import logging

from blacksheep.exceptions import HTTPException
from blacksheep.server.responses import json

from app.core.logging import request_id_of
from app.domain.errors import (
    AuthError,
    ConflictError,
    DomainError,
    ExternalServiceError,
    NotFoundError,
    PermissionDenied,
    TokenExpiredError,
    ValidationError,
)

# 顺序有讲究：子类要排在父类前面，查表时按 MRO 往上找
STATUS_BY_ERROR: dict[type[Exception], int] = {
    ValidationError: 400,
    AuthError: 401,
    TokenExpiredError: 401,
    PermissionDenied: 403,
    NotFoundError: 404,
    ConflictError: 409,
    ExternalServiceError: 502,
}


def status_for(error: Exception) -> int:
    for klass in type(error).__mro__:
        if klass in STATUS_BY_ERROR:
            return STATUS_BY_ERROR[klass]
    return 500


def register_exception_handlers(app) -> None:  # type: ignore[no-untyped-def]
    @app.exception_handler(DomainError)
    async def handle_domain_error(application, request, exc: DomainError):  # type: ignore[no-untyped-def]
        payload: dict = {"code": exc.code, "message": exc.message}
        if exc.details is not None:
            payload["details"] = exc.details
        return json(payload, status=status_for(exc))

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
