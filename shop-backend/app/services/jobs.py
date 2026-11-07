"""持久化任务队列。表在库里，应用重启后未完成的任务还在。"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import JobStatus
from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.models import Job
from app.utils import iso, utcnow


async def enqueue(
    session: AsyncSession,
    job_type: str,
    payload: dict[str, Any],
    *,
    dedupe_key: str | None = None,
    delay_seconds: float = 0,
    max_attempts: int | None = None,
) -> Job | None:
    """dedupe_key 命中已有任务时直接跳过，保证重复提交不会做两遍。"""
    if dedupe_key is not None:
        existing = await session.scalar(select(Job.id).where(Job.dedupe_key == dedupe_key))
        if existing is not None:
            return None
    settings = get_settings()
    job = Job(
        job_type=job_type,
        dedupe_key=dedupe_key,
        payload=payload,
        status=JobStatus.PENDING,
        attempts=0,
        max_attempts=max_attempts or settings.job_max_attempts,
        next_run_at=utcnow() + timedelta(seconds=delay_seconds),
    )
    session.add(job)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        return None
    return job


async def claim_one(session: AsyncSession) -> Job | None:
    """先挑一条待执行任务，再用带状态条件的 UPDATE 抢占。并发下只会有一个 worker 拿到。"""
    now = utcnow()
    for _ in range(5):
        candidate = await session.scalar(
            select(Job.id)
            .where(Job.status == JobStatus.PENDING, Job.next_run_at <= now)
            .order_by(Job.next_run_at.asc(), Job.id.asc())
            .limit(1)
        )
        if candidate is None:
            return None
        result = await session.execute(
            update(Job)
            .where(Job.id == candidate, Job.status == JobStatus.PENDING)
            .values(
                status=JobStatus.RUNNING,
                attempts=Job.attempts + 1,
                locked_at=now,
                updated_at=now,
            )
        )
        await session.commit()
        if result.rowcount == 1:
            return await session.get(Job, candidate, populate_existing=True)
    return None


async def finish(session: AsyncSession, job: Job, *, error: str = "") -> None:
    job.status = JobStatus.SUCCEEDED
    job.last_error = error[:255]
    job.locked_at = None
    job.updated_at = utcnow()
    await session.commit()


async def retry_or_fail(session: AsyncSession, job: Job, error: str) -> bool:
    """返回 True 表示还会重试，False 表示已判定失败。"""
    job.last_error = error[:255]
    job.locked_at = None
    job.updated_at = utcnow()
    if job.attempts >= job.max_attempts:
        job.status = JobStatus.FAILED
        await session.commit()
        return False
    job.status = JobStatus.PENDING
    job.next_run_at = utcnow() + timedelta(seconds=min(2**job.attempts, 30))
    await session.commit()
    return True


async def recover_stale(session: AsyncSession, *, stuck_seconds: int = 300) -> int:
    """进程被 kill 时留在 RUNNING 的任务，启动时捞回来。"""
    deadline = utcnow() - timedelta(seconds=stuck_seconds)
    result = await session.execute(
        update(Job)
        .where(Job.status == JobStatus.RUNNING, Job.locked_at < deadline)
        .values(status=JobStatus.PENDING, locked_at=None, updated_at=utcnow())
    )
    await session.commit()
    return int(result.rowcount or 0)


async def list_jobs(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    status: str | None = None,
    job_type: str | None = None,
) -> tuple[list[dict], int]:
    conditions = []
    if status:
        conditions.append(Job.status == status)
    if job_type:
        conditions.append(Job.job_type == job_type)
    total = await session.scalar(select(func.count(Job.id)).where(*conditions)) or 0
    rows = await session.scalars(
        select(Job)
        .where(*conditions)
        .order_by(Job.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return [public_job(job) for job in rows], int(total)


async def retry_job(session: AsyncSession, job_id: int, *, reset_attempts: bool = False) -> Job:
    job = await session.get(Job, job_id)
    if job is None:
        raise NotFoundError("任务不存在")
    job.status = JobStatus.PENDING
    job.next_run_at = utcnow()
    job.locked_at = None
    job.last_error = ""
    if reset_attempts:
        job.attempts = 0
    elif job.attempts >= job.max_attempts:
        job.max_attempts = job.attempts + 3
    await session.commit()
    await session.refresh(job)
    return job


def public_job(job: Job) -> dict:
    return {
        "id": job.id,
        "type": job.job_type,
        "status": job.status,
        "attempts": job.attempts,
        "maxAttempts": job.max_attempts,
        "nextRunAt": iso(job.next_run_at),
        "lastError": job.last_error or None,
        "payload": job.payload,
        "createdAt": iso(job.created_at),
        "updatedAt": iso(job.updated_at),
    }
