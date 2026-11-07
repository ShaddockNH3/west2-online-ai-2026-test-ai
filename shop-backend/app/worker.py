"""后台任务执行器：轮询 jobs 表，把任务分派给应用服务。

数据库是唯一状态源，所以进程重启不会丢任务；认领靠带条件的原子更新，
多个 worker 同时跑也只有一个能拿到同一条。
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from app.domain.constants import JobType
from app.domain.entities import Job

if TYPE_CHECKING:
    from app.container import Container

logger = logging.getLogger(__name__)


class JobDispatcher:
    """任务类型 → 应用服务方法。新增任务类型只改这里。"""

    def __init__(self, container: Container) -> None:
        self._c = container

    async def dispatch(self, job: Job) -> None:
        payload = dict(job.payload or {})
        if job.job_type == JobType.CLOSE_EXPIRED_ORDER:
            closed = await self._c.orders.close_if_expired(str(payload.get("orderNo", "")))
            logger.info("close expired order %s -> %s", payload.get("orderNo"), closed)
        elif job.job_type == JobType.BUILD_FULFILLMENT:
            record = await self._c.fulfillments.create_for_order(str(payload.get("orderNo", "")))
            logger.info(
                "build fulfillment for %s -> %s",
                payload.get("orderNo"),
                record and record.fulfillment_no,
            )
        elif job.job_type == JobType.SEND_ORDER_NOTIFICATION:
            # 本地模拟通知渠道，不接真实短信/邮件
            logger.info(
                "notify user %s about order %s", payload.get("userId"), payload.get("orderNo")
            )
        elif job.job_type == JobType.CREATE_FLASH_ORDER:
            await self._c.flash_sales.process(int(payload.get("requestId", 0)))
        else:
            raise ValueError(f"未知任务类型：{job.job_type}")


class WorkerPool:
    def __init__(self, container: Container, concurrency: int = 2, poll_interval: float = 0.5):
        self._container = container
        self._uow = container.uow_factory
        self._dispatcher = JobDispatcher(container)
        self.concurrency = max(1, concurrency)
        self.poll_interval = poll_interval
        self._tasks: list[asyncio.Task] = []
        self._stopping = asyncio.Event()
        self.processed = 0

    async def start(self) -> None:
        if self._tasks:
            return
        self._stopping.clear()
        self._tasks = [
            asyncio.create_task(self._loop(index), name=f"job-worker-{index}")
            for index in range(self.concurrency)
        ]
        logger.info("worker pool started with %s workers", self.concurrency)

    async def stop(self) -> None:
        self._stopping.set()
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []

    async def _loop(self, index: int) -> None:
        while not self._stopping.is_set():
            try:
                worked = await self.run_once()
                if not worked:
                    await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 - 单个任务出错不能拖垮 worker
                logger.exception("worker %s loop error", index)
                await asyncio.sleep(self.poll_interval)

    async def run_once(self, limit: int = 1) -> int:
        processed = 0
        for _ in range(limit):
            async with self._uow() as uow:
                job = await uow.jobs.claim_one()
                if job is None:
                    break
                await uow.commit()
            await self._execute(job)
            processed += 1
            self.processed += 1
        return processed

    async def _execute(self, job: Job) -> bool:
        try:
            await self._dispatcher.dispatch(job)
        except Exception as exc:  # noqa: BLE001 - 任务失败必须落库，不能吞掉
            logger.exception("job %s (%s) failed", job.id, job.job_type)
            async with self._uow() as uow:
                retrying = await uow.jobs.retry_or_fail(job, f"{type(exc).__name__}: {exc}")
                await uow.commit()
            if not retrying and job.job_type == JobType.CREATE_FLASH_ORDER:
                await self._container.flash_sales.mark_failed(
                    int(job.payload.get("requestId", 0)), f"建单失败：{exc}"
                )
            return False

        async with self._uow() as uow:
            await uow.jobs.finish(job.id)
            await uow.commit()
        return True

    async def recover(self) -> int:
        async with self._uow() as uow:
            recovered = await uow.jobs.recover_stale(stuck_seconds=300)
            await uow.commit()
            return recovered
