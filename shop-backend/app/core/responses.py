"""统一响应结构。成功直接返回资源，失败统一 code/message/details。"""

from __future__ import annotations

from typing import Any

from blacksheep import Response
from blacksheep.server.responses import json

from app.utils import iso, yuan


def ok(data: Any = None, status: int = 200) -> Response:
    return json(data if data is not None else {"ok": True}, status=status)


def paged(items: list[Any], total: int, page: int, page_size: int) -> Response:
    return json(
        {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": (total + page_size - 1) // page_size,
        }
    )


def money(cents: int) -> str:
    return yuan(cents)


def ts(value: Any) -> str | None:
    return iso(value)
