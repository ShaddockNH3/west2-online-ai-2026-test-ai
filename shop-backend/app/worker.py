"""后台任务执行器：轮询 jobs 表，异步处理订单关单、履约生成、秒杀建单。"""

from __future__ import annotations

import asyncio
import logging

from app.constants import JobStatus, JobType
from app.core.db import db
from app.models import Job
from app.services import flashsale, fulfillment, jobs
from app.services import orders as order_service

logger = logging.getLogger(__name__)


async def dispatch(session, job: Job) -> None:
    payload = job.payload or {}
    if job.job_type == JobType.CLOSE_EXPIRED_ORDER:
        closed = await order_service.close_if_expired(session, str(payload.get("orderNo", "")))
        logger.info("close expired order %s -> %s", payload.get("orderNo"), closed)
    elif job.job_type == JobType.BUILD_FULFILLMENT:
        record = await fulfillment.create_for_order(session, str(payload.get("orderNo", "")))
        logger.info(
            "build fulfillment for %s -> %s",
            payload.get("orderNo"),
            record and record.fulfillment_no,
        )
    elif job.job_type == JobType.SEND_ORDER_NOTIFICATION:
        # 本地模拟通知渠道，不接真实短信/邮件
        logger.info("notify user %s about order %s", payload.get("userId"), payload.get("orderNo"))
    elif job.job_type == JobType.CREATE_FLASH_ORDER:
        await flashsale.process(session, int(payload.get("requestId", 0)))
    else:
        raise ValueError(f"未知任务类型：{job.job_type}")


async def execute(job_id: int) -> bool:
    """执行一条已认领的任务。任何异常都会写回 last_error 并决定是否重试。"""
    async with db.session() as session:
        job = await session.get(Job, job_id)
        if job is None:
            return False
        job_type = job.job_type
        payload = dict(job.payload or {})
        try:
            await dispatch(session, job)
            await jobs.finish(session, job)
            return True
        except Exception as exc:  # noqa: BLE001 - 任务失败必须落库，不能吞掉
            logger.exception("job %s (%s) failed", job.id, job_type)
            await session.rollback()
            fresh = await session.get(Job, job_id, populate_existing=True)
            if fresh is None:
                return False
            retrying = await jobs.retry_or_fail(session, fresh, f"{type(exc).__name__}: {exc}")
            if not retrying and job_type == JobType.CREATE_FLASH_ORDER:
                await flashsale.mark_failed(
                    session, int(payload.get("requestId", 0)), f"建单失败：{exc}"
                )
            return False


class WorkerPool:
    """协程池。数据库是唯一状态源，所以重启不会丢任务。"""

    def __init__(self, concurrency: int = 2, poll_interval: float = 0.5) -> None:
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
            async with db.session() as session:
                job = await jobs.claim_one(session)
            if job is None:
                break
            await execute(job.id)
            processed += 1
            self.processed += 1
        return processed


async def recover() -> int:
    async with db.session() as session:
        return await jobs.recover_stale(session)


async def run_until_idle(max_rounds: int = 50) -> int:
    """测试与本地手动排查用：把当前待执行任务跑完。"""
    total = 0
    for _ in range(max_rounds):
        worked = await WorkerPool(concurrency=1).run_once()
        if not worked:
            break
        total += 1
    return total


async def stats() -> dict:
    async with db.session() as session:
        rows = await jobs.list_jobs(session, page=1, page_size=1)
        pending = await jobs.list_jobs(session, page=1, page_size=1, status=JobStatus.PENDING)
        failed = await jobs.list_jobs(session, page=1, page_size=1, status=JobStatus.FAILED)
    return {"pending": pending[1], "failed": failed[1], "total": rows[1]}
