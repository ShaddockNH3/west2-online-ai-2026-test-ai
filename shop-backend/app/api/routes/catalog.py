"""商品域接口：公开浏览 + 管理员维护。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.api import presenters
from app.application.services.auth import PrincipalService
from app.application.services.catalog import CatalogService
from app.core.params import pagination, query_int, query_str, read_body
from app.core.responses import ok, paged
from app.deps import require_admin
from app.schemas import (
    CategoryIn,
    CategoryPatch,
    ProductIn,
    ProductPatch,
    ProductStatusIn,
    SkuIn,
    SkuPatch,
)


def register(router: Router) -> None:
    @router.get("/categories")
    async def list_categories(catalog: CatalogService):
        rows = await catalog.list_categories()
        return ok({"items": [presenters.category(row) for row in rows]})

    @router.get("/products")
    async def list_products(request: Request, catalog: CatalogService):
        page, page_size = pagination(request)
        category_id = query_int(request, "categoryId", None, minimum=1)
        keyword = query_str(request, "keyword")
        items, total = await catalog.list_products(
            page=page,
            page_size=page_size,
            category_id=category_id,
            keyword=keyword,
        )
        return paged([presenters.product_card(item) for item in items], total, page, page_size)

    @router.get("/products/{product_id}")
    async def get_product(product_id: int, catalog: CatalogService):
        return ok(presenters.product_detail(await catalog.get_product(product_id)))

    # ---------- 管理员：类目 ----------

    @router.post("/admin/categories")
    async def create_category(
        request: Request, catalog: CatalogService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        data = await read_body(request, CategoryIn)
        category = await catalog.create_category(name=data.name, sort_order=data.sortOrder)
        return ok(presenters.category(category), status=201)

    @router.patch("/admin/categories/{category_id}")
    async def update_category(
        request: Request, category_id: int, catalog: CatalogService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        data = await read_body(request, CategoryPatch)
        category = await catalog.update_category(
            category_id, name=data.name, sort_order=data.sortOrder, status=data.status
        )
        return ok(presenters.category(category))

    @router.get("/admin/categories")
    async def admin_list_categories(
        request: Request, catalog: CatalogService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        rows = await catalog.list_categories(include_disabled=True)
        return ok({"items": [presenters.category(row) for row in rows]})

    # ---------- 管理员：商品 ----------

    @router.get("/admin/products")
    async def admin_list_products(
        request: Request, catalog: CatalogService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        page, page_size = pagination(request)
        status = query_str(request, "status")
        category_id = query_int(request, "categoryId", None, minimum=1)
        rows, total = await catalog.admin_list_products(
            page=page, page_size=page_size, status=status, category_id=category_id
        )
        items = [
            {
                "id": product.id,
                "name": product.name,
                "status": product.status,
                "categoryId": category.id,
                "categoryName": category.name,
                "createdAt": presenters.iso(product.created_at),
            }
            for product, category in rows
        ]
        return paged(items, total, page, page_size)

    @router.get("/admin/products/{product_id}")
    async def admin_get_product(
        request: Request, product_id: int, catalog: CatalogService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        return ok(presenters.product_detail(await catalog.admin_detail(product_id)))

    @router.post("/admin/products")
    async def create_product(
        request: Request, catalog: CatalogService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        data = await read_body(request, ProductIn)
        product = await catalog.create_product(
            category_id=data.categoryId,
            name=data.name,
            description=data.description,
            cover_url=data.coverUrl,
        )
        return ok(presenters.product_brief(product), status=201)

    @router.patch("/admin/products/{product_id}")
    async def update_product(
        request: Request, product_id: int, catalog: CatalogService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        data = await read_body(request, ProductPatch)
        product = await catalog.update_product(
            product_id,
            category_id=data.categoryId,
            name=data.name,
            description=data.description,
            cover_url=data.coverUrl,
        )
        return ok(presenters.product_brief(product))

    @router.patch("/admin/products/{product_id}/status")
    async def set_product_status(
        request: Request, product_id: int, catalog: CatalogService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        data = await read_body(request, ProductStatusIn)
        product = await catalog.set_product_status(product_id, data.status)
        return ok(presenters.product_brief(product))

    # ---------- 管理员：SKU ----------

    @router.get("/admin/products/{product_id}/skus")
    async def list_skus(
        request: Request, product_id: int, catalog: CatalogService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        rows = await catalog.admin_skus(product_id)
        items = [
            {
                **presenters.sku_brief(sku),
                "available": inventory.available if inventory else 0,
                "reserved": inventory.reserved if inventory else 0,
                "sold": inventory.sold if inventory else 0,
            }
            for sku, inventory in rows
        ]
        return ok({"items": items})

    @router.post("/admin/products/{product_id}/skus")
    async def create_sku(
        request: Request, product_id: int, catalog: CatalogService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        data = await read_body(request, SkuIn)
        sku = await catalog.create_sku(
            product_id,
            sku_code=data.skuCode,
            specs=data.specs,
            price=data.price,
            status=data.status,
            stock=data.stock,
        )
        return ok(presenters.sku_brief(sku, stock=data.stock), status=201)

    @router.patch("/admin/skus/{sku_id}")
    async def update_sku(
        request: Request, sku_id: int, catalog: CatalogService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        data = await read_body(request, SkuPatch)
        sku = await catalog.update_sku(
            sku_id, specs=data.specs, price=data.price, status=data.status
        )
        return ok(presenters.sku_brief(sku))
