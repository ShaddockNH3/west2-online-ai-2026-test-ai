"""爬虫的公共工具：会话、限速、断点续爬、文本清洗。

几个作业都会用到，抽出来避免每个脚本重复写一遍。
"""

from __future__ import annotations

import json
import random
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# 中英文括号、书名号、方头括号等等，题目要求「去除回车、括号等无用符号」。
_NOISE_CHARS = "（）()【】[]〔〕{}「」『』《》<>\"'\u3000\u00a0　"
_WHITESPACE = " \t\r\n\v\f\u200b\ufeff"


def build_session(
    headers: dict[str, str] | None = None,
    total_retries: int = 4,
    backoff: float = 1.5,
) -> requests.Session:
    """带重试的 Session。

    重试只针对「连接失败 / 5xx / 429」，4xx 直接抛出来——
    404 重试再多次也还是 404，早点暴露问题更好。
    """
    session = requests.Session()
    session.headers.update({"User-Agent": DEFAULT_UA})
    if headers:
        session.headers.update(headers)

    retry = Retry(
        total=total_retries,
        connect=total_retries,
        read=total_retries,
        status=total_retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST", "HEAD"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=8, pool_maxsize=8)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class RateLimiter:
    """最小间隔限速器（带一点随机抖动，避免请求间隔完全等距）。

    Wiki 那类站点明确要求「每次访问间隔 1 秒以上」，这类礼貌由调用方自觉遵守，
    所以这里不设最大值也不做并发——爬虫就该老老实实排队。
    """

    def __init__(self, interval: float, jitter: float = 0.3) -> None:
        self.interval = interval
        self.jitter = jitter
        self._last = 0.0

    def wait(self) -> None:
        if self.interval <= 0:
            return
        elapsed = time.monotonic() - self._last
        delay = self.interval - elapsed
        if delay > 0:
            time.sleep(delay + random.uniform(0, self.jitter))
        self._last = time.monotonic()


class JsonlStore:
    """一行一条 JSON 的增量存储，天然支持断点续爬。

    每写一条就 flush + fsync，进程被 Ctrl-C 或者断网打断时，
    已经落盘的记录不会丢；下次启动时把已有的 id 读出来跳过即可。
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def existing_ids(self, key: str = "url") -> set[str]:
        """读出已经爬过的条目 id，用于跳过。"""
        ids: set[str] = set()
        if not self.path.exists():
            return ids
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    # 上次被打断时可能留下半行，忽略就好
                    continue
                value = record.get(key)
                if isinstance(value, str):
                    ids.add(value)
        return ids

    def append(self, record: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
            import os

            os.fsync(handle.fileno())

    def read_all(self) -> Iterator[dict[str, Any]]:
        if not self.path.exists():
            return
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue

    def count(self) -> int:
        return sum(1 for _ in self.read_all())


def clean_text(text: str, drop_brackets: bool = True) -> str:
    """把正文/标题收拾干净：去回车换行、去括号、压缩连续空白。

    `drop_brackets` 只删括号这层「符号」，括号里的字保留——
    比如「关于《XX办法》（试行）的通知」会变成「关于XX办法试行的通知」。
    """
    if not text:
        return ""
    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    if drop_brackets:
        for char in _NOISE_CHARS:
            text = text.replace(char, "")
    # 全角空格、零宽字符之类统一成普通空格，再压缩
    for char in _WHITESPACE:
        text = text.replace(char, " ")
    return " ".join(text.split())


def safe_filename(name: str, max_length: int = 120) -> str:
    """把标题变成安全的文件名。"""
    cleaned = clean_text(name, drop_brackets=True)
    for bad in '/\\:*?"<>|':
        cleaned = cleaned.replace(bad, "_")
    cleaned = cleaned.strip(". ")
    if not cleaned:
        cleaned = "untitled"
    return cleaned[:max_length]


def human_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}GB"
