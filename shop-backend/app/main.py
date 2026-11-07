"""应用工厂：只负责把配置、路由、中间件和生命周期拼起来。

业务逻辑在 services，HTTP 处理在 api/routes，横切关注点在 core。
"""

from __future__ import annotations

from blacksheep import Application, Request
from blacksheep.server.responses import json
from blacksheep.server.routing import Router
from sqlalchemy import text

from app.api.router import register_routes
from app.core.cache import cache
from app.core.config import Settings, get_settings
from app.core.db import db
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, request_context_middleware
from app.worker import WorkerPool, recover


def create_app(settings: Settings | None = None, *, start_worker: bool = True) -> Application:
    settings = settings or get_settings()
    configure_logging(settings)
    db.configure(settings)

    router = Router()
    app = Application(router=router, show_error_details=False)
    app.middlewares.append(request_context_middleware)
    register_routes(router)
    register_exception_handlers(app)

    pool = WorkerPool(
        concurrency=settings.worker_concurrency,
        poll_interval=settings.worker_poll_interval,
    )

    @app.lifespan
    async def lifespan(application: Application):  # type: ignore[no-untyped-def]
        if settings.redis_url:
            await cache.connect(settings.redis_url, settings.cache_ttl)
        if settings.env != "prod":
            await db.create_all()
        if start_worker and settings.worker_enabled:
            await recover()
            await pool.start()
        yield
        if start_worker and settings.worker_enabled:
            await pool.stop()
        await cache.close()

    @router.get("/health")
    async def health(request: Request):
        """存活探针：进程起来了就返回 200，不碰数据库。"""
        return json({"status": "ok", "app": settings.app_name, "env": settings.env})

    @router.get("/health/ready")
    async def ready(request: Request):
        """就绪探针：数据库不通或 Redis 挂了返回 503，方便编排系统摘流量。"""
        database_ok = True
        try:
            async with db.session() as session:
                await session.execute(text("SELECT 1"))
        except Exception:  # noqa: BLE001 - 探针不能抛异常
            database_ok = False

        redis_state = "disabled"
        if cache.enabled:
            redis_state = "ok" if await cache.ping() else "down"

        healthy = database_ok and redis_state != "down"
        return json(
            {
                "status": "ok" if healthy else "degraded",
                "database": "ok" if database_ok else "down",
                "redis": redis_state,
            },
            status=200 if healthy else 503,
        )

    if settings.web_dir.exists() and (settings.web_dir / "index.html").exists():
        app.serve_files(
            settings.web_dir, discovery=False, cache_time=0, index_document="index.html"
        )
    else:

        @router.get("/")
        async def index(request: Request):
            return json(
                {
                    "app": settings.app_name,
                    "message": "前端页面尚未构建，直接访问 /health 或使用接口文档调试",
                }
            )

    app.services.add_instance(WorkerPool, pool)
    return app
