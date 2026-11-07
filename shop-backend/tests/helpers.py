"""测试辅助：把 HTTP 调用和断言包一层，测试代码只关心业务。"""

from __future__ import annotations

from typing import Any

from blacksheep import JSONContent
from blacksheep.testing import TestClient


class Api:
    def __init__(self, client: TestClient, token: str | None = None) -> None:
        self.client = client
        self.token = token

    def with_token(self, token: str) -> Api:
        return Api(self.client, token)

    def _headers(self, token: str | None = None) -> dict[str, str]:
        bearer = token if token is not None else self.token
        headers = {"Content-Type": "application/json"}
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        return headers

    async def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        token: str | None = None,
        expected: int | tuple[int, ...] = 200,
    ) -> Any:
        headers = self._headers(token)
        kwargs: dict[str, Any] = {"headers": headers}
        if body is not None:
            kwargs["content"] = JSONContent(body)
        response = await getattr(self.client, method)(path, **kwargs)
        data = await response.json()
        allowed = (expected,) if isinstance(expected, int) else expected
        assert response.status in allowed, f"{method.upper()} {path} -> {response.status}: {data}"
        return data

    async def error(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        token: str | None = None,
        status: int = 400,
    ) -> dict[str, Any]:
        data = await self.request(method, path, body, token=token, expected=status)
        assert "code" in data and "message" in data
        return data

    async def get(self, path: str, *, token: str | None = None, expected: Any = 200) -> Any:
        return await self.request("get", path, token=token, expected=expected)

    async def post(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        token: str | None = None,
        expected: Any = 200,
    ) -> Any:
        return await self.request("post", path, body, token=token, expected=expected)

    async def patch(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        token: str | None = None,
        expected: Any = 200,
    ) -> Any:
        return await self.request("patch", path, body, token=token, expected=expected)

    async def put(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        token: str | None = None,
        expected: Any = 200,
    ) -> Any:
        return await self.request("put", path, body, token=token, expected=expected)

    async def delete(self, path: str, *, token: str | None = None, expected: Any = 200) -> Any:
        return await self.request("delete", path, token=token, expected=expected)

    # ---------- 常用业务动作 ----------

    async def login(self, username: str = "demo", password: str = "demo123456") -> Api:
        data = await self.post(
            "/auth/login", {"username": username, "password": password}, expected=200
        )
        return Api(self.client, data["accessToken"])

    async def me(self) -> dict[str, Any]:
        return await self.get("/users/me")

    async def add_to_cart(self, sku_id: int, quantity: int = 1) -> dict[str, Any]:
        return await self.post("/cart/items", {"skuId": sku_id, "quantity": quantity}, expected=201)

    async def cart(self) -> dict[str, Any]:
        return await self.get("/cart/items")

    async def first_address(self) -> dict[str, Any]:
        data = await self.get("/addresses")
        assert data["items"], "演示账号需要一条默认地址"
        return data["items"][0]

    async def checkout(
        self,
        request_id: str,
        *,
        address_id: int | None = None,
        cart_item_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        address = address_id or (await self.first_address())["id"]
        if cart_item_ids is None:
            cart = await self.cart()
            cart_item_ids = [item["id"] for item in cart["items"]]
        return await self.post(
            "/orders",
            {"cartItemIds": cart_item_ids, "addressId": address, "requestId": request_id},
            expected=(200, 201),
        )

    async def order_detail(self, order_no: str) -> dict[str, Any]:
        return await self.get(f"/orders/{order_no}")

    async def pay(self, order_no: str, result: str = "SUCCESS") -> dict[str, Any]:
        return await self.post(f"/orders/{order_no}/payments", {"result": result}, expected=201)


def worker(concurrency: int = 1):
    """按当前配置建一个 WorkerPool，供测试手动驱动后台任务。"""
    from app.container import build_container
    from app.core.config import get_settings
    from app.worker import WorkerPool

    return WorkerPool(build_container(get_settings()), concurrency=concurrency)


async def run_worker(limit: int = 20, concurrency: int = 1) -> int:
    return await worker(concurrency).run_once(limit=limit)


async def recover_jobs() -> int:
    return await worker().recover()
