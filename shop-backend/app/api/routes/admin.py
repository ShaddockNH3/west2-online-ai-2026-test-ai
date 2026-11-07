"""管理端：订单、库存、履约、后台任务与总览。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router
from sqlalchemy import func, select

from app.constants import FulfillmentStatus, JobStatus, OrderStatus
from app.core.db import db
from app.core.params import pagination, query_int, query_str, read_body, read_body_optional
from app.core.responses import ok, paged
from app.deps import require_admin
from app.models import Fulfillment, Job, Order
from app.schemas import InventoryIn, InventorySetIn, JobRetryIn, ShipIn
from app.services import fulfillment as fulfillment_service
from app.services import inventory as inventory_service
from app.services import jobs as jobs_service
from app.services import orders as order_service
from app.utils import yuan
from app.worker import WorkerPool


def register(router: Router) -> None:
    # ---------- 订单 ----------

    @router.get("/admin/orders")
    async def admin_list_orders(request: Request):
        await require_admin(request)
        page, page_size = pagination(request)
        status = query_str(request, "status")
        keyword = query_str(request, "keyword")
        async with db.session() as session:
            items, total = await order_service.admin_list_orders(
                session, page=page, page_size=page_size, status=status, keyword=keyword
            )
            return paged(items, total, page, page_size)

    @router.get("/admin/orders/{order_no}")
    async def admin_get_order(request: Request, order_no: str):
        await require_admin(request)
        async with db.session() as session:
            order = await order_service.get_order(session, order_no)
            return ok(await order_service.detail(session, order))

    # ---------- 库存 ----------

    @router.get("/admin/inventory")
    async def list_inventory(request: Request):
        await require_admin(request)
        page, page_size = pagination(request)
        keyword = query_str(request, "keyword")
        low_stock = query_int(request, "lowStock", None, minimum=0)
        async with db.session() as session:
            items, total = await inventory_service.list_inventory(
                session,
                page=page,
                page_size=page_size,
                keyword=keyword,
                low_stock=low_stock,
            )
            return paged(items, total, page, page_size)

    @router.get("/admin/inventory/logs")
    async def list_inventory_logs(request: Request):
        await require_admin(request)
        page, page_size = pagination(request)
        sku_id = query_int(request, "skuId", None, minimum=1)
        async with db.session() as session:
            rows, total = await inventory_service.logs(
                session, sku_id=sku_id, page=page, page_size=page_size
            )
            return paged(
                [inventory_service.public_log(row) for row in rows], total, page, page_size
            )

    @router.post("/admin/skus/{sku_id}/inventory")
    async def inbound(request: Request, sku_id: int):
        await require_admin(request)
        data = await read_body(request, InventoryIn)
        async with db.session() as session:
            inventory = await inventory_service.inbound(
                session, sku_id, data.quantity, reason=data.reason
            )
            return ok(inventory_service.public_inventory(inventory))

    @router.put("/admin/skus/{sku_id}/inventory")
    async def set_inventory(request: Request, sku_id: int):
        await require_admin(request)
        data = await read_body(request, InventorySetIn)
        async with db.session() as session:
            inventory = await inventory_service.adjust_to(
                session, sku_id, data.available, reason=data.reason
            )
            return ok(inventory_service.public_inventory(inventory))

    # ---------- 履约 ----------

    @router.get("/admin/fulfillments")
    async def list_fulfillments(request: Request):
        await require_admin(request)
        page, page_size = pagination(request)
        status = query_str(request, "status")
        async with db.session() as session:
            items, total = await fulfillment_service.list_admin(
                session, page=page, page_size=page_size, status=status
            )
            return paged(items, total, page, page_size)

    @router.post("/admin/fulfillments/{fulfillment_no}/prepare")
    async def prepare_fulfillment(request: Request, fulfillment_no: str):
        await require_admin(request)
        async with db.session() as session:
            record = await fulfillment_service.prepare(session, fulfillment_no)
            return ok(fulfillment_service.public_fulfillment(record))

    @router.post("/admin/fulfillments/{fulfillment_no}/ship")
    async def ship_fulfillment(request: Request, fulfillment_no: str):
        await require_admin(request)
        # 允许不带请求体，默认按成功发货处理
        data = await read_body_optional(request, ShipIn, ShipIn())
        async with db.session() as session:
            record = await fulfillment_service.ship(session, fulfillment_no, simulate=data.simulate)
            return ok(fulfillment_service.public_fulfillment(record))

    # ---------- 后台任务 ----------

    @router.get("/admin/jobs")
    async def list_jobs(request: Request):
        await require_admin(request)
        page, page_size = pagination(request)
        status = query_str(request, "status")
        job_type = query_str(request, "type")
        async with db.session() as session:
            items, total = await jobs_service.list_jobs(
                session, page=page, page_size=page_size, status=status, job_type=job_type
            )
            return paged(items, total, page, page_size)

    @router.post("/admin/jobs/{job_id}/retry")
    async def retry_job(request: Request, job_id: int):
        await require_admin(request)
        data = await read_body(request, JobRetryIn)
        async with db.session() as session:
            job = await jobs_service.retry_job(session, job_id, reset_attempts=data.reset_attempts)
            return ok(jobs_service.public_job(job))

    @router.post("/admin/jobs/run-once")
    async def run_jobs(request: Request):
        await require_admin(request)
        processed = await WorkerPool(concurrency=1).run_once(limit=50)
        return ok({"processed": processed})

    # ---------- 总览 ----------

    @router.get("/admin/overview")
    async def overview(request: Request):
        await require_admin(request)
        async with db.session() as session:
            order_rows = await session.execute(
                select(Order.status, func.count(Order.id)).group_by(Order.status)
            )
            order_counts = {status: int(count) for status, count in order_rows.all()}
            paid_amount = await session.scalar(
                select(func.coalesce(func.sum(Order.total_amount_cents), 0)).where(
                    Order.status.in_([OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.COMPLETED])
                )
            )
            pending_fulfillments = await session.scalar(
                select(func.count(Fulfillment.id)).where(
                    Fulfillment.status.in_(
                        [FulfillmentStatus.PENDING, FulfillmentStatus.READY_TO_SHIP]
                    )
                )
            )
            pending_jobs = await session.scalar(
                select(func.count(Job.id)).where(Job.status == JobStatus.PENDING)
            )
            failed_jobs = await session.scalar(
                select(func.count(Job.id)).where(Job.status == JobStatus.FAILED)
            )
            low_stock_items, _ = await inventory_service.list_inventory(
                session, page=1, page_size=5, low_stock=5
            )
            return ok(
                {
                    "ordersByStatus": order_counts,
                    "paidAmount": yuan(int(paid_amount or 0)),
                    "pendingFulfillments": int(pending_fulfillments or 0),
                    "pendingJobs": int(pending_jobs or 0),
                    "failedJobs": int(failed_jobs or 0),
                    "lowStockSkus": low_stock_items,
                }
            )
