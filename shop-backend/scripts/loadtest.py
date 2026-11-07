"""限量发售链路的压测脚本（纯 HTTP，不碰数据库）。

    python scripts/loadtest.py --users 40 --browse-seconds 8

跑之前建议先重置数据：

    SHOP_WORKER_ENABLED=false python -m scripts.init_db --reset

脚本做两段：
1. 日常浏览：并发请求商品列表，统计吞吐与延迟；
2. 集中抢购：所有用户同时抢同一 SKU，分别记录「受理响应」和「最终建单结果」。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Samples:
    latencies: list[float] = field(default_factory=list)
    statuses: dict[int, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    started_at: float = 0.0
    finished_at: float = 0.0

    def add(self, elapsed: float, status: int | None, error: str = "") -> None:
        self.latencies.append(elapsed)
        if status is not None:
            self.statuses[status] = self.statuses.get(status, 0) + 1
        if error:
            self.errors.append(error)

    def summary(self) -> dict[str, Any]:
        total = len(self.latencies)
        wall = max(self.finished_at - self.started_at, 1e-9)
        ordered = sorted(self.latencies)

        def percentile(p: float) -> float:
            if not ordered:
                return 0.0
            index = min(len(ordered) - 1, int(round((len(ordered) - 1) * p)))
            return round(ordered[index] * 1000, 2)

        return {
            "requests": total,
            "durationSeconds": round(wall, 2),
            "throughput": round(total / wall, 2),
            "avgMs": round(statistics.fmean(ordered) * 1000, 2) if ordered else 0,
            "p50Ms": percentile(0.5),
            "p95Ms": percentile(0.95),
            "p99Ms": percentile(0.99),
            "maxMs": round(max(ordered) * 1000, 2) if ordered else 0,
            "statuses": {str(key): value for key, value in sorted(self.statuses.items())},
            "technicalErrors": len(self.errors),
            "sampleErrors": self.errors[:5],
        }


class Api:
    def __init__(self, client: httpx.AsyncClient, token: str | None = None) -> None:
        self.client = client
        self.token = token

    def headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def call(self, method: str, path: str, body: Any = None) -> tuple[int, Any]:
        response = await self.client.request(method, path, headers=self.headers(), json=body)
        try:
            data = response.json()
        except ValueError:
            data = None
        return response.status_code, data


async def timed(samples: Samples, coro) -> tuple[int | None, Any]:
    started = time.perf_counter()
    try:
        status, data = await coro
        samples.add(time.perf_counter() - started, status)
        return status, data
    except Exception as exc:  # noqa: BLE001 - 压测要统计所有失败
        samples.add(time.perf_counter() - started, None, f"{type(exc).__name__}: {exc}")
        return None, None


async def prepare_users(client: httpx.AsyncClient, count: int, prefix: str) -> list[Api]:
    api = Api(client)
    users: list[Api] = []
    for index in range(count):
        username = f"{prefix}{index:03d}"
        await api.call("POST", "/auth/register", {"username": username, "password": "loadtest123"})
        status, data = await api.call(
            "POST", "/auth/login", {"username": username, "password": "loadtest123"}
        )
        if status != 200 or not data:
            continue
        user = Api(client, data["accessToken"])
        await user.call(
            "POST",
            "/addresses",
            {
                "receiver": f"压测{index}",
                "phone": "13900000000",
                "detail": f"压测地址 {index} 号",
                "isDefault": True,
            },
        )
        users.append(user)
    return users


async def browse_test(client: httpx.AsyncClient, concurrency: int, seconds: int) -> dict:
    samples = Samples()
    samples.started_at = time.perf_counter()
    deadline = samples.started_at + seconds

    async def worker() -> None:
        while time.perf_counter() < deadline:
            await timed(samples, Api(client).call("GET", "/products?page=1&pageSize=12"))

    await asyncio.gather(*(worker() for _ in range(concurrency)))
    samples.finished_at = time.perf_counter()
    return samples.summary()


async def flash_sale_test(
    client: httpx.AsyncClient,
    users: list[Api],
    activity_id: int,
    sku_id: int,
    admin: Api,
) -> dict:
    samples = Samples()
    addresses: dict[int, int] = {}
    for index, user in enumerate(users):
        _, data = await user.call("GET", "/addresses")
        if data and data.get("items"):
            addresses[index] = data["items"][0]["id"]

    # 每轮用独立的 requestId，统计时只认这一批，避免把历史抢购记录算进来
    batch = int(time.time())
    request_ids = [f"load-{batch}-{index:04d}" for index in range(len(users))]

    async def grab(index: int) -> None:
        user = users[index]
        body = {
            "skuId": sku_id,
            "quantity": 1,
            "addressId": addresses.get(index, 0),
            "requestId": request_ids[index],
        }
        await timed(samples, user.call("POST", f"/activities/{activity_id}/flash-sale", body))

    samples.started_at = time.perf_counter()
    await asyncio.gather(*(grab(index) for index in range(len(users))))
    samples.finished_at = time.perf_counter()

    accepted = samples.statuses.get(202, 0) + samples.statuses.get(200, 0)
    rejected = samples.statuses.get(409, 0)

    # 等后台任务把受理的请求建成订单
    final: dict[str, int] = {}
    for _ in range(30):
        await asyncio.sleep(1)
        success = queued = 0
        for user in users:
            _, data = await user.call("GET", "/flash-sale/requests")
            for item in (data or {}).get("items", []):
                if item["requestId"] not in request_ids:
                    continue
                if item["status"] == "SUCCEEDED":
                    success += 1
                elif item["status"] == "QUEUED":
                    queued += 1
        final = {"succeeded": success, "queued": queued}
        if queued == 0:
            break

    _, inventory = await admin.call("GET", "/admin/inventory?keyword=")
    sku_row = next(
        (row for row in (inventory or {}).get("items", []) if row["skuId"] == sku_id), None
    )
    _, orders = await admin.call("GET", "/admin/orders?status=PENDING_PAYMENT&pageSize=100")

    return {
        "accepted": accepted,
        "rejected": rejected,
        "final": final,
        "pendingOrders": (orders or {}).get("total"),
        "inventory": sku_row,
        "samples": samples.summary(),
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="商城压测")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--users", type=int, default=40)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--browse-seconds", type=int, default=8)
    parser.add_argument("--activity-id", type=int, default=0)
    parser.add_argument("--sku-id", type=int, default=0)
    parser.add_argument("--user-prefix", default="load")
    parser.add_argument("--skip-browse", action="store_true")
    parser.add_argument("--browse-only", action="store_true", help="只压商品浏览，用于对比缓存效果")
    args = parser.parse_args()

    timeout = httpx.Timeout(15.0, connect=10.0)
    limits = httpx.Limits(max_connections=args.concurrency * 2, max_keepalive_connections=64)
    async with httpx.AsyncClient(base_url=args.base_url, timeout=timeout, limits=limits) as client:
        admin_api = Api(client)
        status, login = await admin_api.call(
            "POST", "/auth/login", {"username": "admin", "password": "admin123456"}
        )
        if status != 200:
            raise SystemExit("管理员登录失败，先运行 scripts/init_db.py")
        admin = Api(client, login["accessToken"])

        print(f"准备 {args.users} 个压测用户…", flush=True)
        start = time.perf_counter()
        users = await prepare_users(client, args.users, args.user_prefix)
        print(f"用户就绪 {len(users)} 个，用时 {time.perf_counter() - start:.1f}s", flush=True)

        activity_id = args.activity_id
        sku_id = args.sku_id
        if not activity_id:
            _, data = await Api(client).call("GET", "/activities")
            flash = next(
                (item for item in (data or {}).get("items", []) if item["type"] == "FLASH_SALE"),
                None,
            )
            if flash is None:
                raise SystemExit("没有进行中的限量活动，先运行 init_db --reset")
            activity_id = flash["id"]
            sku_id = flash["skus"][0]["skuId"]

        report: dict[str, Any] = {
            "startedAt": datetime.now(UTC).isoformat(),
            "environment": {
                "python": "3.12.3",
                "framework": "BlackSheep 2.6.4 + uvicorn",
                "database": "SQLite (WAL)",
                "users": len(users),
                "concurrency": args.concurrency,
            },
            "activityId": activity_id,
            "skuId": sku_id,
        }

        if not args.skip_browse:
            print("① 商品浏览压测…", flush=True)
            report["browse"] = await browse_test(client, args.concurrency, args.browse_seconds)
            print(json.dumps(report["browse"], ensure_ascii=False, indent=2), flush=True)

        if args.browse_only:
            output = ROOT / "logs" / f"browse-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            if not output.parent.exists():
                output.parent.mkdir(parents=True)
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"结果已写入 {output}")
            return

        print("② 集中抢购压测…", flush=True)
        report["flashSale"] = await flash_sale_test(client, users, activity_id, sku_id, admin)
        print(json.dumps(report["flashSale"], ensure_ascii=False, indent=2), flush=True)

        output = ROOT / "logs" / f"loadtest-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        if not output.parent.exists():
            output.parent.mkdir(parents=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"结果已写入 {output}")


if __name__ == "__main__":
    asyncio.run(main())
