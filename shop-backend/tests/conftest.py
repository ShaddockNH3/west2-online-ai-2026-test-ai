"""pytest 夹具：每个测试一个独立 SQLite 文件，互不干扰。"""

from __future__ import annotations

import pytest
from blacksheep.testing import TestClient

from app.config import reset_settings_cache
from app.db import db


@pytest.fixture
async def app(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOP_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/test.db")
    monkeypatch.setenv("SHOP_WORKER_ENABLED", "false")
    monkeypatch.setenv("SHOP_JWT_SECRET", "test-secret-only-0123456789abcdef0123456789")
    reset_settings_cache()
    await db.dispose()

    from app.main import create_app

    application = create_app(start_worker=False)
    await application.start()
    await db.drop_all()
    await db.create_all()
    yield application
    await application.stop()
    await db.dispose()
    reset_settings_cache()


@pytest.fixture
async def client(app) -> TestClient:
    return TestClient(app)


@pytest.fixture
async def shop(app):
    from scripts.init_db import seed
    from tests.helpers import Api

    await seed()
    return Api(TestClient(app))


@pytest.fixture
async def user(shop):
    return await shop.login()


@pytest.fixture
async def admin(shop):
    return await shop.login("admin", "admin123456")
