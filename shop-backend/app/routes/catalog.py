"""商品域接口：公开浏览 + 管理员维护。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.db import db
from app.deps import require_admin
from app.params import pagination, query_int, query_str, read_body
from app.responses import ok, paged
from app.schemas import (
    CategoryIn,
    CategoryPatch,
    ProductIn,
    ProductPatch,
    ProductStatusIn,
    SkuIn,
    SkuPatch,
)
from app.services import catalog as catalog_service
from app.services import inventory as inventory_service


def _product_brief(product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "coverUrl": product.cover_url,
        "status": product.status,
        "categoryId": product.category_id,
    }


def register(router: Router) -> None:
    @router.get("/categories")
    async def list_categories(request: Request):
        async with db.session() as session:
            rows = await catalog_service.list_categories(session)
            return ok({"items": [catalog_service.public_category(row) for row in rows]})

    @router.get("/products")
    async def list_products(request: Request):
        page, page_size = pagination(request)
        category_id = query_int(request, "categoryId", None, minimum=1)
        keyword = query_str(request, "keyword")
        async with db.session() as session:
            items, total = await catalog_service.list_public_products(
                session,
                page=page,
                page_size=page_size,
                category_id=category_id,
                keyword=keyword,
            )
            return paged(items, total, page, page_size)

    @router.get("/products/{product_id}")
    async def get_product(request: Request, product_id: int):
        async with db.session() as session:
            return ok(await catalog_service.get_public_product(session, product_id))

    # ---------- 管理员：类目 ----------

    @router.post("/admin/categories")
    async def create_category(request: Request):
        await require_admin(request)
        data = await read_body(request, CategoryIn)
        async with db.session() as session:
            category = await catalog_service.create_category(session, data)
            return ok(catalog_service.public_category(category), status=201)

    @router.patch("/admin/categories/{category_id}")
    async def update_category(request: Request, category_id: int):
        await require_admin(request)
        data = await read_body(request, CategoryPatch)
        async with db.session() as session:
            category = await catalog_service.update_category(session, category_id, data)
            return ok(catalog_service.public_category(category))

    @router.get("/admin/categories")
    async def admin_list_categories(request: Request):
        await require_admin(request)
        async with db.session() as session:
            rows = await catalog_service.list_categories(session, include_disabled=True)
            return ok({"items": [catalog_service.public_category(row) for row in rows]})

    # ---------- 管理员：商品 ----------

    @router.get("/admin/products")
    async def admin_list_products(request: Request):
        await require_admin(request)
        page, page_size = pagination(request)
        status = query_str(request, "status")
        category_id = query_int(request, "categoryId", None, minimum=1)
        async with db.session() as session:
            items, total = await catalog_service.admin_list_products(
                session,
                page=page,
                page_size=page_size,
                status=status,
                category_id=category_id,
            )
            return paged(items, total, page, page_size)

    @router.get("/admin/products/{product_id}")
    async def admin_get_product(request: Request, product_id: int):
        await require_admin(request)
        async with db.session() as session:
            return ok(await catalog_service.get_admin_product(session, product_id))

    @router.post("/admin/products")
    async def create_product(request: Request):
        await require_admin(request)
        data = await read_body(request, ProductIn)
        async with db.session() as session:
            product = await catalog_service.create_product(session, data)
            return ok(_product_brief(product), status=201)

    @router.patch("/admin/products/{product_id}")
    async def update_product(request: Request, product_id: int):
        await require_admin(request)
        data = await read_body(request, ProductPatch)
        async with db.session() as session:
            product = await catalog_service.update_product(session, product_id, data)
            return ok(_product_brief(product))

    @router.patch("/admin/products/{product_id}/status")
    async def set_product_status(request: Request, product_id: int):
        await require_admin(request)
        data = await read_body(request, ProductStatusIn)
        async with db.session() as session:
            product = await catalog_service.set_product_status(session, product_id, data.status)
            return ok(_product_brief(product))

    # ---------- 管理员：SKU ----------

    @router.get("/admin/products/{product_id}/skus")
    async def list_skus(request: Request, product_id: int):
        await require_admin(request)
        async with db.session() as session:
            skus = await catalog_service.list_skus(session, product_id)
            items = []
            for sku in skus:
                inventory = await inventory_service.get_inventory(session, sku.id)
                items.append(
                    {
                        "id": sku.id,
                        "code": sku.sku_code,
                        "specs": sku.specs,
                        "price": f"{sku.price_cents // 100}.{sku.price_cents % 100:02d}",
                        "status": sku.status,
                        "available": inventory.available if inventory else 0,
                        "reserved": inventory.reserved if inventory else 0,
                        "sold": inventory.sold if inventory else 0,
                    }
                )
            return ok({"items": items})

    @router.post("/admin/products/{product_id}/skus")
    async def create_sku(request: Request, product_id: int):
        await require_admin(request)
        data = await read_body(request, SkuIn)
        async with db.session() as session:
            sku = await catalog_service.create_sku(session, product_id, data)
            return ok(
                {
                    "id": sku.id,
                    "code": sku.sku_code,
                    "specs": sku.specs,
                    "price": f"{sku.price_cents // 100}.{sku.price_cents % 100:02d}",
                    "status": sku.status,
                    "stock": data.stock,
                },
                status=201,
            )

    @router.patch("/admin/skus/{sku_id}")
    async def update_sku(request: Request, sku_id: int):
        await require_admin(request)
        data = await read_body(request, SkuPatch)
        async with db.session() as session:
            sku = await catalog_service.update_sku(session, sku_id, data)
            return ok(
                {
                    "id": sku.id,
                    "code": sku.sku_code,
                    "specs": sku.specs,
                    "price": f"{sku.price_cents // 100}.{sku.price_cents % 100:02d}",
                    "status": sku.status,
                }
            )
