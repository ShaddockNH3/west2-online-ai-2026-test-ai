"""管理端：订单、库存、履约、后台任务与总览。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.api import presenters
from app.application.services.auth import PrincipalService
from app.application.services.fulfillment import FulfillmentService
from app.application.services.inventory import InventoryService
from app.application.services.jobs import JobService, OverviewService
from app.application.services.orders import OrderService
from app.core.params import pagination, query_int, query_str, read_body, read_body_optional
from app.core.responses import ok, paged
from app.deps import require_admin
from app.schemas import InventoryIn, InventorySetIn, JobRetryIn, ShipIn
from app.worker import WorkerPool


def register(router: Router) -> None:
    # ---------- 订单 ----------

    @router.get("/admin/orders")
    async def admin_list_orders(
        request: Request, orders: OrderService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        page, page_size = pagination(request)
        rows, total = await orders.admin_list(
            page=page,
            page_size=page_size,
            status=query_str(request, "status"),
            keyword=query_str(request, "keyword"),
        )
        items = [presenters.admin_order_row(row, count) for row, count in rows]
        return paged(items, total, page, page_size)

    @router.get("/admin/orders/{order_no}")
    async def admin_get_order(
        request: Request, order_no: str, orders: OrderService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        return ok(presenters.order_detail(await orders.detail(order_no)))

    # ---------- 库存 ----------

    @router.get("/admin/inventory")
    async def list_inventory(
        request: Request, inventory: InventoryService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        page, page_size = pagination(request)
        rows, total = await inventory.list(
            page=page,
            page_size=page_size,
            keyword=query_str(request, "keyword"),
            low_stock=query_int(request, "lowStock", None, minimum=0),
        )
        return paged([presenters.inventory_row(row) for row in rows], total, page, page_size)

    @router.get("/admin/inventory/logs")
    async def list_inventory_logs(
        request: Request, inventory: InventoryService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        page, page_size = pagination(request)
        rows, total = await inventory.logs(
            sku_id=query_int(request, "skuId", None, minimum=1), page=page, page_size=page_size
        )
        return paged([presenters.inventory_log(row) for row in rows], total, page, page_size)

    @router.post("/admin/skus/{sku_id}/inventory")
    async def inbound(
        request: Request, sku_id: int, inventory: InventoryService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        data = await read_body(request, InventoryIn)
        record = await inventory.inbound(sku_id, data.quantity, reason=data.reason)
        return ok(presenters.inventory_record(record))

    @router.put("/admin/skus/{sku_id}/inventory")
    async def set_inventory(
        request: Request, sku_id: int, inventory: InventoryService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        data = await read_body(request, InventorySetIn)
        record = await inventory.adjust_to(sku_id, data.available, reason=data.reason)
        return ok(presenters.inventory_record(record))

    # ---------- 履约 ----------

    @router.get("/admin/fulfillments")
    async def list_fulfillments(
        request: Request, fulfillments: FulfillmentService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        page, page_size = pagination(request)
        rows, total = await fulfillments.admin_list(
            page=page, page_size=page_size, status=query_str(request, "status")
        )
        return paged([presenters.fulfillment(row) for row in rows], total, page, page_size)

    @router.post("/admin/fulfillments/{fulfillment_no}/prepare")
    async def prepare_fulfillment(
        request: Request,
        fulfillment_no: str,
        fulfillments: FulfillmentService,
        principals: PrincipalService,
    ):
        await require_admin(request, principals)
        record = await fulfillments.prepare(fulfillment_no)
        return ok(presenters.fulfillment(record))

    @router.post("/admin/fulfillments/{fulfillment_no}/ship")
    async def ship_fulfillment(
        request: Request,
        fulfillment_no: str,
        fulfillments: FulfillmentService,
        principals: PrincipalService,
    ):
        await require_admin(request, principals)
        # 允许不带请求体，默认按成功发货处理
        data = await read_body_optional(request, ShipIn, ShipIn())
        record = await fulfillments.ship(fulfillment_no, simulate=data.simulate)
        return ok(presenters.fulfillment(record))

    # ---------- 后台任务 ----------

    @router.get("/admin/jobs")
    async def list_jobs(request: Request, jobs: JobService, principals: PrincipalService):
        await require_admin(request, principals)
        page, page_size = pagination(request)
        rows, total = await jobs.list(
            page=page,
            page_size=page_size,
            status=query_str(request, "status"),
            job_type=query_str(request, "type"),
        )
        return paged([presenters.job(row) for row in rows], total, page, page_size)

    @router.post("/admin/jobs/{job_id}/retry")
    async def retry_job(
        request: Request, job_id: int, jobs: JobService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        data = await read_body(request, JobRetryIn)
        job = await jobs.retry(job_id, reset_attempts=data.reset_attempts)
        return ok(presenters.job(job))

    @router.post("/admin/jobs/run-once")
    async def run_jobs(request: Request, pool: WorkerPool, principals: PrincipalService):
        await require_admin(request, principals)
        processed = await pool.run_once(limit=50)
        return ok({"processed": processed})

    # ---------- 总览 ----------

    @router.get("/admin/overview")
    async def overview(request: Request, reports: OverviewService, principals: PrincipalService):
        await require_admin(request, principals)
        return ok(presenters.overview(await reports.summary()))
