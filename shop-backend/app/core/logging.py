"""日志与请求上下文。

访问日志交给 uvicorn，这里只负责应用日志的格式与请求 ID，方便把一次请求的
多条日志串起来。ID 从 `X-Request-Id` 头沿用，没有就生成一个。
"""

from __future__ import annotations

import logging
import time
import uuid

from blacksheep import Request, Response

from app.core.config import Settings

REQUEST_ID_HEADER = b"x-request-id"


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("blacksheep").setLevel(logging.WARNING)


def request_id_of(request: Request) -> str:
    return str(request.scope.get("request_id", "-"))


async def request_context_middleware(request: Request, handler) -> Response:  # type: ignore[no-untyped-def]
    raw = request.get_first_header(REQUEST_ID_HEADER)
    request_id = raw.decode("latin1") if raw else uuid.uuid4().hex[:12]
    request.scope["request_id"] = request_id
    started = time.perf_counter()
    try:
        response = await handler(request)
    finally:
        elapsed = (time.perf_counter() - started) * 1000
        if elapsed >= 500:
            # 只记慢请求，正常的访问日志 uvicorn 已经打过了
            logging.getLogger("app.access").warning(
                "slow %s %s %.0fms request_id=%s",
                request.method,
                request.path,
                elapsed,
                request_id,
            )
    response.add_header(REQUEST_ID_HEADER, request_id.encode())
    return response
