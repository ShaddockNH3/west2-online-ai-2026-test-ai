"""后台任务用例：查询、重试与统计。worker 的认领与执行在 app/worker.py。"""

from __future__ import annotations

from app.application.ports.uow import UowFactory
from app.application.read_models import Overview
from app.domain.entities import Job


class JobService:
    def __init__(self, uow_factory: UowFactory) -> None:
        self._uow = uow_factory

    async def list(
        self, *, page: int, page_size: int, status: str | None, job_type: str | None
    ) -> tuple[list[Job], int]:
        async with self._uow() as uow:
            return await uow.jobs.list(
                page=page, page_size=page_size, status=status, job_type=job_type
            )

    async def retry(self, job_id: int, *, reset_attempts: bool) -> Job:
        async with self._uow() as uow:
            job = await uow.jobs.retry(job_id, reset_attempts=reset_attempts)
            await uow.commit()
            return job

    async def stats(self) -> dict:
        async with self._uow() as uow:
            counts = await uow.jobs.count_by_status()
        return {
            "pending": counts.get("PENDING", 0),
            "failed": counts.get("FAILED", 0),
            "total": sum(counts.values()),
        }


class OverviewService:
    def __init__(self, uow_factory: UowFactory, inventory: InventoryReader) -> None:
        self._uow = uow_factory
        self._inventory = inventory

    async def summary(self) -> Overview:
        async with self._uow() as uow:
            orders = await uow.orders.count_by_status()
            paid = await uow.orders.paid_amount()
            pending_fulfillments = await uow.fulfillments.count_pending()
            jobs = await uow.jobs.count_by_status()
        low_stock, _ = await self._inventory.list(page=1, page_size=5, low_stock=5)
        return Overview(
            orders_by_status=orders,
            paid_amount_cents=paid,
            pending_fulfillments=pending_fulfillments,
            pending_jobs=jobs.get("PENDING", 0),
            failed_jobs=jobs.get("FAILED", 0),
            low_stock=low_stock,
        )


class InventoryReader:
    """只读库存，供总览复用，避免 OverviewService 依赖整个 InventoryService。"""

    def __init__(self, uow_factory: UowFactory) -> None:
        self._uow = uow_factory

    async def list(self, *, page: int, page_size: int, low_stock: int | None = None):
        async with self._uow() as uow:
            return await uow.inventory.list_rows(
                page=page, page_size=page_size, keyword=None, low_stock=low_stock
            )
