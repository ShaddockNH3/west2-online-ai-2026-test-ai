"""类目、商品、SKU 的 SQLAlchemy 实现。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Category, Product, Sku
from app.domain.errors import ConflictError, NotFoundError
from app.infrastructure.persistence.mappers import to_category, to_product, to_sku
from app.infrastructure.persistence.models import Category as CategoryRow
from app.infrastructure.persistence.models import Product as ProductRow
from app.infrastructure.persistence.models import Sku as SkuRow


class SqlCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---------- 类目 ----------

    async def list_categories(self, *, include_disabled: bool) -> list[Category]:
        stmt = select(CategoryRow).order_by(CategoryRow.sort_order.asc(), CategoryRow.id.asc())
        if not include_disabled:
            stmt = stmt.where(CategoryRow.status == "ENABLED")
        return [to_category(row) for row in await self._session.scalars(stmt)]

    async def get_category(self, category_id: int) -> Category | None:
        row = await self._session.get(CategoryRow, category_id)
        return to_category(row) if row else None

    async def create_category(self, *, name: str, sort_order: int) -> Category:
        row = CategoryRow(name=name, sort_order=sort_order)
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ConflictError("类目名称已存在") from exc
        return to_category(row)

    async def update_category(
        self, category_id: int, *, name: str | None, sort_order: int | None, status: str | None
    ) -> Category:
        row = await self._session.get(CategoryRow, category_id)
        if row is None:
            raise NotFoundError("类目不存在")
        if name is not None:
            row.name = name
        if sort_order is not None:
            row.sort_order = sort_order
        if status is not None:
            row.status = status
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ConflictError("类目名称已存在") from exc
        return to_category(row)

    # ---------- 商品 ----------

    async def get_product(self, product_id: int) -> Product | None:
        row = await self._session.get(ProductRow, product_id)
        return to_product(row) if row else None

    async def create_product(
        self, *, category_id: int, name: str, description: str, cover_url: str, status: str
    ) -> Product:
        row = ProductRow(
            category_id=category_id, name=name, description=description, cover_url=cover_url
        )
        row.status = status
        self._session.add(row)
        await self._session.flush()
        return to_product(row)

    async def update_product(
        self,
        product_id: int,
        *,
        category_id: int | None,
        name: str | None,
        description: str | None,
        cover_url: str | None,
    ) -> Product:
        row = await self._session.get(ProductRow, product_id)
        if row is None:
            raise NotFoundError("商品不存在")
        if category_id is not None:
            row.category_id = category_id
        if name is not None:
            row.name = name
        if description is not None:
            row.description = description
        if cover_url is not None:
            row.cover_url = cover_url
        await self._session.flush()
        return to_product(row)

    async def set_product_status(self, product_id: int, status: str) -> Product:
        row = await self._session.get(ProductRow, product_id)
        if row is None:
            raise NotFoundError("商品不存在")
        row.status = status
        await self._session.flush()
        return to_product(row)

    async def has_sellable_sku(self, product_id: int) -> bool:
        found = await self._session.scalar(
            select(SkuRow.id)
            .where(SkuRow.product_id == product_id, SkuRow.status == "ON_SALE")
            .limit(1)
        )
        return found is not None

    # ---------- SKU ----------

    async def get_sku(self, sku_id: int) -> Sku | None:
        row = await self._session.get(SkuRow, sku_id)
        return to_sku(row) if row else None

    async def get_skus(self, product_id: int) -> list[Sku]:
        rows = await self._session.scalars(
            select(SkuRow).where(SkuRow.product_id == product_id).order_by(SkuRow.id)
        )
        return [to_sku(row) for row in rows]

    async def get_skus_with_products(self, sku_ids: list[int]) -> list[tuple[Sku, Product]]:
        if not sku_ids:
            return []
        rows = await self._session.execute(
            select(SkuRow, ProductRow)
            .join(ProductRow, ProductRow.id == SkuRow.product_id)
            .where(SkuRow.id.in_(sku_ids))
        )
        return [(to_sku(sku), to_product(product)) for sku, product in rows.all()]

    async def list_skus_for_products(self, product_ids: list[int]) -> list[Sku]:
        if not product_ids:
            return []
        rows = await self._session.scalars(
            select(SkuRow).where(SkuRow.product_id.in_(product_ids), SkuRow.status == "ON_SALE")
        )
        return [to_sku(row) for row in rows]

    async def count_skus(self, product_id: int) -> int:
        count = await self._session.scalar(
            select(func.count(SkuRow.id)).where(SkuRow.product_id == product_id)
        )
        return int(count or 0)

    async def create_sku(
        self,
        *,
        product_id: int,
        sku_code: str,
        specs: dict[str, Any],
        price_cents: int,
        status: str,
    ) -> Sku:
        row = SkuRow(
            product_id=product_id,
            sku_code=sku_code,
            specs=specs,
            price_cents=price_cents,
            status=status,
        )
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ConflictError("SKU 编码已存在") from exc
        return to_sku(row)

    async def update_sku(
        self,
        sku_id: int,
        *,
        specs: dict[str, Any] | None,
        price_cents: int | None,
        status: str | None,
    ) -> Sku:
        row = await self._session.get(SkuRow, sku_id)
        if row is None:
            raise NotFoundError("SKU 不存在")
        if specs is not None:
            row.specs = specs
        if price_cents is not None:
            row.price_cents = price_cents
        if status is not None:
            row.status = status
        await self._session.flush()
        return to_sku(row)

    # ---------- 列表 ----------

    async def list_public_products(
        self,
        *,
        page: int,
        page_size: int,
        category_id: int | None,
        keyword: str | None,
    ) -> tuple[list[tuple[Product, Category]], int]:
        conditions = [
            ProductRow.status == "ON_SALE",
            CategoryRow.status == "ENABLED",
        ]
        if category_id is not None:
            conditions.append(ProductRow.category_id == category_id)
        if keyword:
            like = f"%{keyword.strip()}%"
            conditions.append(or_(ProductRow.name.like(like), ProductRow.description.like(like)))

        total = await self._session.scalar(
            select(func.count(ProductRow.id))
            .join(CategoryRow, CategoryRow.id == ProductRow.category_id)
            .where(*conditions)
        )
        rows = await self._session.execute(
            select(ProductRow, CategoryRow)
            .join(CategoryRow, CategoryRow.id == ProductRow.category_id)
            .where(*conditions)
            .order_by(ProductRow.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        return [(to_product(p), to_category(c)) for p, c in rows.all()], int(total or 0)

    async def admin_list_products(
        self,
        *,
        page: int,
        page_size: int,
        status: str | None,
        category_id: int | None,
    ) -> tuple[list[tuple[Product, Category]], int]:
        conditions = []
        if status:
            conditions.append(ProductRow.status == status)
        if category_id is not None:
            conditions.append(ProductRow.category_id == category_id)

        total = await self._session.scalar(select(func.count(ProductRow.id)).where(*conditions))
        rows = await self._session.execute(
            select(ProductRow, CategoryRow)
            .join(CategoryRow, CategoryRow.id == ProductRow.category_id)
            .where(*conditions)
            .order_by(ProductRow.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        return [(to_product(p), to_category(c)) for p, c in rows.all()], int(total or 0)
