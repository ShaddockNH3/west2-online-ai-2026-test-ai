"""应用工厂：装配配置、依赖、路由、中间件与生命周期。

业务在 `app/application`，持久化与外部系统在 `app/infrastructure`，
这一层只做「把谁传给谁」。
"""

from __future__ import annotations

from blacksheep import Application, Request
from blacksheep.server.responses import json
from blacksheep.server.routing import Router
from sqlalchemy import text

from app.api.errors import register_exception_handlers
from app.api.router import register_routes
from app.application.services.activities import ActivityService
from app.application.services.addresses import AddressService
from app.application.services.auth import AuthService, PrincipalService
from app.application.services.cart import CartService
from app.application.services.catalog import CatalogService
from app.application.services.flashsale import FlashSaleService
from app.application.services.fulfillment import FulfillmentService
from app.application.services.inventory import InventoryService
from app.application.services.jobs import JobService, OverviewService
from app.application.services.orders import OrderService
from app.application.services.payments import PaymentService
from app.container import Container, build_container
from app.core.config import Settings, get_settings
from app.core.db import db
from app.core.logging import configure_logging, request_context_middleware
from app.worker import WorkerPool


def create_app(settings: Settings | None = None, *, start_worker: bool = True) -> Application:
    settings = settings or get_settings()
    configure_logging(settings)
    db.configure(settings)
    container = build_container(settings)

    router = Router()
    app = Application(router=router, show_error_details=False)
    app.middlewares.append(request_context_middleware)
    register_routes(router)
    register_exception_handlers(app)

    pool = WorkerPool(
        container,
        concurrency=settings.worker_concurrency,
        poll_interval=settings.worker_poll_interval,
    )
    _register_services(app, container, pool)

    @app.lifespan
    async def lifespan(application: Application):  # type: ignore[no-untyped-def]
        if settings.redis_url:
            await container.cache.connect(settings.redis_url, settings.cache_ttl)
        if settings.env != "prod":
            await db.create_all()
        if start_worker and settings.worker_enabled:
            await pool.recover()
            await pool.start()
        yield
        if start_worker and settings.worker_enabled:
            await pool.stop()
        await container.cache.close()

    @router.get("/health")
    async def health():
        """存活探针：进程起来了就返回 200，不碰数据库。"""
        return json({"status": "ok", "app": settings.app_name, "env": settings.env})

    @router.get("/health/ready")
    async def ready():
        """就绪探针：数据库不通或 Redis 挂了返回 503，方便编排系统摘流量。"""
        database_ok = True
        try:
            async with db.session() as session:
                await session.execute(text("SELECT 1"))
        except Exception:  # noqa: BLE001 - 探针不能抛异常
            database_ok = False

        redis_state = "disabled"
        if container.cache.enabled:
            redis_state = "ok" if await container.cache.ping() else "down"

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

    return app


def _register_services(app: Application, container: Container, pool: WorkerPool) -> None:
    """把具体实现登记到容器里；路由按类型声明依赖，框架负责注入。"""
    app.services.add_instance(container, Container)
    app.services.add_instance(container.auth, AuthService)
    app.services.add_instance(container.principal, PrincipalService)
    app.services.add_instance(container.addresses, AddressService)
    app.services.add_instance(container.catalog, CatalogService)
    app.services.add_instance(container.cart, CartService)
    app.services.add_instance(container.orders, OrderService)
    app.services.add_instance(container.payments, PaymentService)
    app.services.add_instance(container.inventory, InventoryService)
    app.services.add_instance(container.activities, ActivityService)
    app.services.add_instance(container.flash_sales, FlashSaleService)
    app.services.add_instance(container.fulfillments, FulfillmentService)
    app.services.add_instance(container.jobs, JobService)
    app.services.add_instance(container.overview, OverviewService)
    app.services.add_instance(pool, WorkerPool)
