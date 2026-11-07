"""应用工厂：路由、异常处理、生命周期与静态页面。"""

from __future__ import annotations

import logging

from blacksheep import Application, Request
from blacksheep.exceptions import HTTPException
from blacksheep.server.responses import json
from blacksheep.server.routing import Router

from app.cache import cache
from app.config import Settings, get_settings
from app.db import db
from app.errors import AppError
from app.routes import (
    activities,
    addresses,
    admin,
    auth,
    cart,
    catalog,
    flashsale,
    orders,
    users,
)
from app.worker import WorkerPool, recover


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    # 框架访问日志里不带请求体，避免密码等敏感信息落盘
    logging.getLogger("blacksheep").setLevel(logging.WARNING)


def register_routes(router: Router) -> None:
    auth.register(router)
    users.register(router)
    addresses.register(router)
    catalog.register(router)
    cart.register(router)
    orders.register(router)
    activities.register(router)
    flashsale.register(router)
    admin.register(router)


def register_exception_handlers(app: Application) -> None:
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
        logging.getLogger("app").exception("unhandled error on %s %s", request.method, request.path)
        # 对外只给通用描述，堆栈留在日志里
        return json({"code": "INTERNAL_ERROR", "message": "服务器内部错误，请稍后重试"}, status=500)


def create_app(settings: Settings | None = None, *, start_worker: bool = True) -> Application:
    settings = settings or get_settings()
    configure_logging(settings)
    db.configure(settings)

    router = Router()
    app = Application(router=router, show_error_details=False)
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

    @app.router.get("/health")
    async def health(request: Request):
        return json({"status": "ok", "app": settings.app_name, "env": settings.env})

    if settings.web_dir.exists() and (settings.web_dir / "index.html").exists():
        app.serve_files(
            settings.web_dir, discovery=False, cache_time=0, index_document="index.html"
        )
    else:

        @app.router.get("/")
        async def index(request: Request):
            return json(
                {
                    "app": settings.app_name,
                    "message": "前端页面尚未构建，直接访问 /health 或使用接口文档调试",
                }
            )

    app.services.add_instance(WorkerPool, pool)
    return app
