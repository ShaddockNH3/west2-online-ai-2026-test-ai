"""后台任务：持久化、失败重试、重启恢复、超时关单。"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select, update

from app.core.db import db
from app.domain.constants import JobStatus
from app.infrastructure.persistence.models import Job, Order
from app.infrastructure.persistence.repositories.fulfillments import SqlJobRepository
from app.utils import utcnow
from tests.helpers import Api, recover_jobs, run_worker


async def test_expired_order_is_closed_and_stock_released(user: Api, admin: Api):
    await user.add_to_cart(3, 1)
    order = await user.checkout("expire-order-01")
    order_no = order["orderNo"]

    async with db.session() as session:
        await session.execute(
            update(Order)
            .where(Order.order_no == order_no)
            .values(expire_at=utcnow() - timedelta(minutes=1))
        )
        await session.execute(
            update(Job)
            .where(Job.dedupe_key == f"close:{order_no}")
            .values(next_run_at=utcnow() - timedelta(seconds=1))
        )
        await session.commit()

    await run_worker(limit=20)
    detail = await user.order_detail(order_no)
    assert detail["status"] == "CANCELLED"
    assert detail["cancelReason"] == "EXPIRED"
    rows = (await admin.get("/admin/inventory?keyword=BAG-NAT"))["items"]
    assert rows[0]["reserved"] == 0


async def test_failed_job_retries_then_marks_failed(admin: Api):
    async with db.session() as session:
        job = await SqlJobRepository(session).enqueue(
            "UNKNOWN_JOB", {"foo": "bar"}, dedupe_key=None, delay_seconds=0, max_attempts=None
        )
        assert job is not None
        await session.commit()
        job_id = job.id

    # 失败后有退避，测试里把下次执行时间提前
    for _ in range(3):
        async with db.session() as session:
            await session.execute(update(Job).values(next_run_at=utcnow() - timedelta(seconds=1)))
            await session.commit()
        await run_worker(limit=5)

    async with db.session() as session:
        stored = await session.get(Job, job_id)
        assert stored is not None
        assert stored.status == JobStatus.FAILED
        assert stored.attempts == 3
        assert "未知任务类型" in stored.last_error

    rows = (await admin.get("/admin/jobs?status=FAILED"))["items"]
    assert any(row["id"] == job_id for row in rows)

    retried = await admin.post(f"/admin/jobs/{job_id}/retry", {"reset_attempts": True})
    assert retried["status"] == "PENDING"
    assert retried["attempts"] == 0


async def test_recover_stale_running_jobs(admin: Api):
    async with db.session() as session:
        job = await SqlJobRepository(session).enqueue(
            "SEND_ORDER_NOTIFICATION",
            {"orderNo": "x"},
            dedupe_key=None,
            delay_seconds=0,
            max_attempts=None,
        )
        await session.commit()
        await session.execute(
            update(Job)
            .where(Job.id == job.id)
            .values(status=JobStatus.RUNNING, locked_at=utcnow() - timedelta(minutes=10))
        )
        await session.commit()
    recovered = await recover_jobs()
    assert recovered == 1
    async with db.session() as session:
        stored = await session.get(Job, job.id)
        assert stored is not None
        assert stored.status == JobStatus.PENDING


async def test_jobs_are_persisted(user: Api):
    await user.add_to_cart(3, 1)
    order = await user.checkout("persist-job-001")
    async with db.session() as session:
        rows = list(
            await session.scalars(select(Job).where(Job.dedupe_key == f"close:{order['orderNo']}"))
        )
    assert len(rows) == 1
    assert rows[0].status == JobStatus.PENDING
    assert rows[0].payload["orderNo"] == order["orderNo"]


async def test_manual_run_once_endpoint(user: Api, admin: Api):
    await user.add_to_cart(1, 1)
    order = await user.checkout("manual-job-001")
    await user.pay(order["orderNo"])
    data = await admin.post("/admin/jobs/run-once")
    assert data["processed"] >= 1
    rows = (await admin.get("/admin/fulfillments"))["items"]
    assert any(row["orderNo"] == order["orderNo"] for row in rows)
