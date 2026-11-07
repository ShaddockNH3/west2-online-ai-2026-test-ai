"""请求模型的公共基类。extra=forbid 防止客户端塞入 role、totalAmount 这类字段。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

Json = dict[str, Any]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
