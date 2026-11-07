"""履约与后台任务的 SQLAlchemy 实现。"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Fulfillment, Job
from app.domain.errors import NotFoundError
from app.domain.money import utcnow
from app.infrastructure.persistence.mappers import to_fulfillment, to_job
from app.infrastructure.persistence.models import Fulfillment as FulfillmentRow
from app.infrastructure.persistence.models import Job as JobRow


class SqlFulfillmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: Fulfillment) -> Fulfillment:
        row = FulfillmentRow(
            fulfillment_no=record.fulfillment_no,
            order_id=record.order_id,
            order_no=record.order_no,
            status=record.status,
            receiver=record.receiver,
            phone=record.phone,
            address_detail=record.address_detail,
            items=record.items,
        )
        self._session.add(row)
        await self._session.flush()
        return to_fulfillment(row)

    async def get_by_no(self, fulfillment_no: str) -> Fulfillment | None:
        row = await self._session.scalar(
            select(FulfillmentRow).where(FulfillmentRow.fulfillment_no == fulfillment_no)
        )
        return to_fulfillment(row) if row else None

    async def get_by_order(self, order_id: int) -> Fulfillment | None:
        row = await self._session.scalar(
            select(FulfillmentRow).where(FulfillmentRow.order_id == order_id)
        )
        return to_fulfillment(row) if row else None

    async def list(
        self, *, page: int, page_size: int, status: str | None
    ) -> tuple[list[Fulfillment], int]:
        conditions = []
        if status:
            conditions.append(FulfillmentRow.status == status)
        total = await self._session.scalar(select(func.count(FulfillmentRow.id)).where(*conditions))
        rows = await self._session.scalars(
            select(FulfillmentRow)
            .where(*conditions)
            .order_by(FulfillmentRow.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        return [to_fulfillment(row) for row in rows], int(total or 0)

    async def save(self, record: Fulfillment) -> None:
        row = await self._session.get(FulfillmentRow, record.id)
        if row is None:
            raise NotFoundError("履约单不存在")
        row.status = record.status
        row.tracking_no = record.tracking_no
        row.attempts = record.attempts
        row.last_error = record.last_error
        row.shipped_at = record.shipped_at
        row.completed_at = record.completed_at
        await self._session.flush()

    async def count_pending(self) -> int:
        total = await self._session.scalar(
            select(func.count(FulfillmentRow.id)).where(
                FulfillmentRow.status.in_(["PENDING", "READY_TO_SHIP"])
            )
        )
        return int(total or 0)


class SqlJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def enqueue(
        self,
        job_type: str,
        payload: dict[str, Any],
        *,
        dedupe_key: str | None,
        delay_seconds: float,
        max_attempts: int | None,
    ) -> Job | None:
        if dedupe_key is not None:
            existing = await self._session.scalar(
                select(JobRow.id).where(JobRow.dedupe_key == dedupe_key)
            )
            if existing is not None:
                return None
        row = JobRow(
            job_type=job_type,
            dedupe_key=dedupe_key,
            payload=payload,
            status="PENDING",
            attempts=0,
            max_attempts=max_attempts or 3,
            next_run_at=utcnow() + timedelta(seconds=delay_seconds),
        )
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            return None
        return to_job(row)

    async def claim_one(self) -> Job | None:
        now = utcnow()
        for _ in range(5):
            candidate = await self._session.scalar(
                select(JobRow.id)
                .where(JobRow.status == "PENDING", JobRow.next_run_at <= now)
                .order_by(JobRow.next_run_at.asc(), JobRow.id.asc())
                .limit(1)
            )
            if candidate is None:
                return None
            result = await self._session.execute(
                update(JobRow)
                .where(JobRow.id == candidate, JobRow.status == "PENDING")
                .values(
                    status="RUNNING",
                    attempts=JobRow.attempts + 1,
                    locked_at=now,
                    updated_at=now,
                )
            )
            if result.rowcount == 1:
                row = await self._session.get(JobRow, candidate, populate_existing=True)
                return to_job(row) if row else None
        return None

    async def finish(self, job_id: int, *, error: str = "") -> None:
        row = await self._session.get(JobRow, job_id)
        if row is None:
            return
        row.status = "SUCCEEDED"
        row.last_error = error[:255]
        row.locked_at = None
        row.updated_at = utcnow()
        await self._session.flush()

    async def retry_or_fail(self, job: Job, error: str) -> bool:
        row = await self._session.get(JobRow, job.id)
        if row is None:
            return False
        row.last_error = error[:255]
        row.locked_at = None
        row.updated_at = utcnow()
        if row.attempts >= row.max_attempts:
            row.status = "FAILED"
            await self._session.flush()
            return False
        row.status = "PENDING"
        row.next_run_at = utcnow() + timedelta(seconds=min(2**row.attempts, 30))
        await self._session.flush()
        return True

    async def recover_stale(self, *, stuck_seconds: int) -> int:
        deadline = utcnow() - timedelta(seconds=stuck_seconds)
        result = await self._session.execute(
            update(JobRow)
            .where(JobRow.status == "RUNNING", JobRow.locked_at < deadline)
            .values(status="PENDING", locked_at=None, updated_at=utcnow())
        )
        return int(result.rowcount or 0)

    async def list(
        self, *, page: int, page_size: int, status: str | None, job_type: str | None
    ) -> tuple[list[Job], int]:
        conditions = []
        if status:
            conditions.append(JobRow.status == status)
        if job_type:
            conditions.append(JobRow.job_type == job_type)
        total = await self._session.scalar(select(func.count(JobRow.id)).where(*conditions))
        rows = await self._session.scalars(
            select(JobRow)
            .where(*conditions)
            .order_by(JobRow.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        return [to_job(row) for row in rows], int(total or 0)

    async def get(self, job_id: int) -> Job | None:
        row = await self._session.get(JobRow, job_id)
        return to_job(row) if row else None

    async def retry(self, job_id: int, *, reset_attempts: bool) -> Job:
        row = await self._session.get(JobRow, job_id)
        if row is None:
            raise NotFoundError("任务不存在")
        row.status = "PENDING"
        row.next_run_at = utcnow()
        row.locked_at = None
        row.last_error = ""
        if reset_attempts:
            row.attempts = 0
        elif row.attempts >= row.max_attempts:
            row.max_attempts = row.attempts + 3
        await self._session.flush()
        return to_job(row)

    async def count_by_status(self) -> dict[str, int]:
        rows = await self._session.execute(
            select(JobRow.status, func.count(JobRow.id)).group_by(JobRow.status)
        )
        return {status: int(count) for status, count in rows.all()}
