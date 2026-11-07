"""应用配置。全部通过环境变量（前缀 SHOP_）或 .env 覆盖。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SHOP_",
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "西二周边小店"
    env: str = "dev"
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'var' / 'shop.db'}"

    jwt_secret: str = "dev-only-change-me-please-use-a-random-secret-0123456789"
    access_ttl: int = 1800
    refresh_ttl: int = 604800

    order_expire_minutes: int = 30

    # 留空表示不用缓存；填 redis://127.0.0.1:6379/0 才启用商品目录缓存
    redis_url: str = ""
    cache_ttl: int = 20

    worker_enabled: bool = True
    worker_concurrency: int = 2
    worker_poll_interval: float = 0.5
    job_max_attempts: int = 3

    admin_username: str = "admin"
    admin_password: str = "admin123456"
    demo_username: str = "demo"
    demo_password: str = "demo123456"

    log_level: str = "INFO"
    # 静态页面目录（Vue 构建产物）；不存在时只提供 API
    web_dir: Path = BASE_DIR / "web" / "dist"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def is_mysql(self) -> bool:
        return self.database_url.startswith("mysql")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """测试里切换数据库时需要丢弃缓存。"""
    get_settings.cache_clear()
