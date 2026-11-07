"""可选的目录缓存。

没配 `SHOP_REDIS_URL` 时完全直通，测试和本机开发都不受缓存影响。
配了 Redis 才启用，用于商品列表/详情的读缓存，靠版本号整体失效。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

PREFIX = "shop:"


class Cache:
    def __init__(self) -> None:
        self._client: Redis | None = None
        self._ttl = 20

    @property
    def enabled(self) -> bool:
        return self._client is not None

    async def connect(self, url: str, ttl: int = 20) -> bool:
        if not url:
            return False
        try:
            client = Redis.from_url(url, decode_responses=True)
            await client.ping()
        except Exception as exc:  # noqa: BLE001 - 缓存不可用不应该挡住启动
            logger.warning("Redis 连接失败，缓存关闭：%s", exc)
            return False
        self._client = client
        self._ttl = ttl
        logger.info("Redis 缓存已启用，TTL %ss", ttl)
        return True

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def ping(self) -> bool:
        """给 /health/ready 用：Redis 不可用时返回 False，但不抛异常。"""
        if self._client is None:
            return False
        try:
            return bool(await self._client.ping())
        except Exception:  # noqa: BLE001
            return False

    async def version(self, namespace: str) -> int:
        if self._client is None:
            return 0
        raw = await self._client.get(f"{PREFIX}version:{namespace}")
        return int(raw or 0)

    async def bump(self, namespace: str) -> None:
        """写操作后调一次，旧版本的缓存 key 自然过期。"""
        if self._client is None:
            return
        try:
            await self._client.incr(f"{PREFIX}version:{namespace}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("缓存版本号自增失败：%s", exc)

    async def get_json(self, key: str) -> Any | None:
        if self._client is None:
            return None
        try:
            raw = await self._client.get(key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("读缓存失败：%s", exc)
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        if self._client is None:
            return
        try:
            await self._client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl or self._ttl)
        except Exception as exc:  # noqa: BLE001
            logger.warning("写缓存失败：%s", exc)


cache = Cache()


def catalog_key(*parts: Any) -> str:
    return PREFIX + ":".join(str(part) for part in ("catalog", *parts))
