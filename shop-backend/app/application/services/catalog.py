"""类目、商品、SKU 的用例：管理员维护 + 前台浏览（带可选目录缓存）。"""

from __future__ import annotations

from datetime import datetime

from app.application.cache_keys import (
    CATALOG_NAMESPACE,
    catalog_product_key,
    catalog_products_key,
)
from app.application.ports.services import CachePort, Clock
from app.application.ports.uow import UowFactory
from app.application.read_models import ProductCard, ProductDetail, SkuCard
from app.domain.constants import ProductStatus
from app.domain.entities import Category, Product, Sku
from app.domain.errors import ConflictError, NotFoundError, ValidationError
from app.domain.money import to_cents
from app.domain.pricing import quote


def _price_cents(value: str, field: str = "价格") -> int:
    try:
        cents = to_cents(value, field=field)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if cents <= 0:
        raise ValidationError(f"{field}必须大于 0")
    return cents


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def _card_to_dict(card: ProductCard) -> dict:
    return {
        "id": card.id,
        "name": card.name,
        "cover_url": card.cover_url,
        "category_id": card.category_id,
        "category_name": card.category_name,
        "min_price_cents": card.min_price_cents,
        "max_price_cents": card.max_price_cents,
        "has_activity": card.has_activity,
        "stock_available": card.stock_available,
        "created_at": card.created_at.isoformat() if card.created_at else None,
    }


def _card_from_dict(data: dict) -> ProductCard:
    return ProductCard(
        id=data["id"],
        name=data["name"],
        cover_url=data["cover_url"],
        category_id=data["category_id"],
        category_name=data["category_name"],
        min_price_cents=data["min_price_cents"],
        max_price_cents=data["max_price_cents"],
        has_activity=data["has_activity"],
        stock_available=data["stock_available"],
        created_at=_parse_dt(data.get("created_at")),
    )


def _sku_card_to_dict(card: SkuCard) -> dict:
    return {
        "id": card.id,
        "code": card.code,
        "specs": card.specs,
        "price_cents": card.price_cents,
        "original_cents": card.original_cents,
        "activity_name": card.activity_name,
        "status": card.status,
        "available_stock": card.available_stock,
        "purchasable": card.purchasable,
    }


def _detail_to_dict(detail: ProductDetail) -> dict:
    return {
        "id": detail.id,
        "name": detail.name,
        "description": detail.description,
        "cover_url": detail.cover_url,
        "status": detail.status,
        "category": {
            "id": detail.category.id,
            "name": detail.category.name,
            "sort_order": detail.category.sort_order,
            "status": detail.category.status,
        }
        if detail.category
        else None,
        "skus": [_sku_card_to_dict(sku) for sku in detail.skus],
        "created_at": detail.created_at.isoformat() if detail.created_at else None,
        "updated_at": detail.updated_at.isoformat() if detail.updated_at else None,
    }


def _detail_from_dict(data: dict) -> ProductDetail:
    category = data.get("category")
    return ProductDetail(
        id=data["id"],
        name=data["name"],
        description=data["description"],
        cover_url=data["cover_url"],
        status=data["status"],
        category=Category(
            id=category["id"],
            name=category["name"],
            sort_order=category["sort_order"],
            status=category["status"],
        )
        if category
        else None,
        skus=[SkuCard(**sku) for sku in data["skus"]],
        created_at=_parse_dt(data.get("created_at")),
        updated_at=_parse_dt(data.get("updated_at")),
    )


class CatalogService:
    def __init__(self, uow_factory: UowFactory, clock: Clock, cache: CachePort) -> None:
        self._uow = uow_factory
        self._clock = clock
        self._cache = cache

    async def _bump(self) -> None:
        await self._cache.bump(CATALOG_NAMESPACE)

    # ---------- 类目 ----------

    async def list_categories(self, *, include_disabled: bool = False) -> list[Category]:
        async with self._uow() as uow:
            return await uow.catalog.list_categories(include_disabled=include_disabled)

    async def create_category(self, *, name: str, sort_order: int) -> Category:
        async with self._uow() as uow:
            category = await uow.catalog.create_category(name=name, sort_order=sort_order)
            await uow.commit()
        await self._bump()
        return category

    async def update_category(
        self,
        category_id: int,
        *,
        name: str | None,
        sort_order: int | None,
        status: str | None,
    ) -> Category:
        async with self._uow() as uow:
            category = await uow.catalog.update_category(
                category_id, name=name, sort_order=sort_order, status=status
            )
            await uow.commit()
        await self._bump()
        return category

    # ---------- 商品 ----------

    async def create_product(
        self,
        *,
        category_id: int,
        name: str,
        description: str,
        cover_url: str,
    ) -> Product:
        async with self._uow() as uow:
            if await uow.catalog.get_category(category_id) is None:
                raise NotFoundError("类目不存在")
            product = await uow.catalog.create_product(
                category_id=category_id,
                name=name,
                description=description,
                cover_url=cover_url,
                status=ProductStatus.OFF_SALE,
            )
            await uow.commit()
        await self._bump()
        return product

    async def update_product(
        self,
        product_id: int,
        *,
        category_id: int | None,
        name: str | None,
        description: str | None,
        cover_url: str | None,
    ) -> Product:
        async with self._uow() as uow:
            if category_id is not None and await uow.catalog.get_category(category_id) is None:
                raise NotFoundError("类目不存在")
            product = await uow.catalog.update_product(
                product_id,
                category_id=category_id,
                name=name,
                description=description,
                cover_url=cover_url,
            )
            await uow.commit()
        await self._bump()
        return product

    async def set_product_status(self, product_id: int, status: str) -> Product:
        async with self._uow() as uow:
            if status == ProductStatus.ON_SALE and not await uow.catalog.has_sellable_sku(
                product_id
            ):
                raise ConflictError("商品还没有可售规格，不能上架")
            product = await uow.catalog.set_product_status(product_id, status)
            await uow.commit()
        await self._bump()
        return product

    # ---------- SKU ----------

    async def list_skus(self, product_id: int) -> list[Sku]:
        async with self._uow() as uow:
            if await uow.catalog.get_product(product_id) is None:
                raise NotFoundError("商品不存在")
            return await uow.catalog.get_skus(product_id)

    async def admin_skus(self, product_id: int) -> list[tuple[Sku, object | None]]:
        async with self._uow() as uow:
            if await uow.catalog.get_product(product_id) is None:
                raise NotFoundError("商品不存在")
            skus = await uow.catalog.get_skus(product_id)
            return [(sku, await uow.inventory.get(sku.id)) for sku in skus]

    async def create_sku(
        self,
        product_id: int,
        *,
        sku_code: str | None,
        specs: dict,
        price: str,
        status: str,
        stock: int,
    ) -> Sku:
        price_cents = _price_cents(price)
        async with self._uow() as uow:
            if await uow.catalog.get_product(product_id) is None:
                raise NotFoundError("商品不存在")
            code = sku_code or await self._next_sku_code(uow, product_id)
            sku = await uow.catalog.create_sku(
                product_id=product_id,
                sku_code=code,
                specs=specs,
                price_cents=price_cents,
                status=status,
            )
            await uow.inventory.ensure(sku.id, stock)
            await uow.commit()
        await self._bump()
        return sku

    async def _next_sku_code(self, uow, product_id: int) -> str:
        count = await uow.catalog.count_skus(product_id)
        return f"SKU-{product_id:04d}-{count + 1:02d}"

    async def update_sku(
        self,
        sku_id: int,
        *,
        specs: dict | None,
        price: str | None,
        status: str | None,
    ) -> Sku:
        price_cents = _price_cents(price) if price is not None else None
        async with self._uow() as uow:
            sku = await uow.catalog.update_sku(
                sku_id, specs=specs, price_cents=price_cents, status=status
            )
            await uow.commit()
        await self._bump()
        return sku

    # ---------- 前台浏览 ----------

    async def list_products(
        self,
        *,
        page: int,
        page_size: int,
        category_id: int | None,
        keyword: str | None,
    ) -> tuple[list[ProductCard], int]:
        version = await self._cache.version(CATALOG_NAMESPACE)
        key = catalog_products_key(version, page, page_size, category_id, keyword or "")
        cached = await self._cache.get_json(key)
        if cached is not None:
            return [_card_from_dict(item) for item in cached["items"]], int(cached["total"])

        async with self._uow() as uow:
            rows, total = await uow.catalog.list_public_products(
                page=page, page_size=page_size, category_id=category_id, keyword=keyword
            )
            product_ids = [product.id for product, _ in rows]
            skus = await uow.catalog.list_skus_for_products(product_ids)
            sku_ids = [sku.id for sku in skus]
            rules = await uow.activities.active_rules(sku_ids, now=self._clock.now())
            stock = await uow.inventory.available_map(sku_ids)

        grouped: dict[int, list[Sku]] = {}
        for sku in skus:
            grouped.setdefault(sku.product_id, []).append(sku)

        cards: list[ProductCard] = []
        for product, category in rows:
            product_skus = grouped.get(product.id, [])
            prices = []
            has_activity = False
            for sku in product_skus:
                priced = quote(sku.price_cents, rules.get(sku.id))
                prices.append(priced.unit_cents)
                has_activity = has_activity or bool(priced.activity_name)
            cards.append(
                ProductCard(
                    id=product.id,
                    name=product.name,
                    cover_url=product.cover_url,
                    category_id=category.id,
                    category_name=category.name,
                    min_price_cents=min(prices) if prices else None,
                    max_price_cents=max(prices) if prices else None,
                    has_activity=has_activity,
                    stock_available=sum(stock.get(sku.id, 0) for sku in product_skus),
                    created_at=product.created_at,
                )
            )

        await self._cache.set_json(
            key, {"items": [_card_to_dict(card) for card in cards], "total": total}
        )
        return cards, total

    async def get_product(self, product_id: int) -> ProductDetail:
        version = await self._cache.version(CATALOG_NAMESPACE)
        key = catalog_product_key(version, product_id)
        cached = await self._cache.get_json(key)
        if cached is not None:
            return _detail_from_dict(cached)

        async with self._uow() as uow:
            product = await uow.catalog.get_product(product_id)
            if product is None:
                raise NotFoundError("商品不存在或已下架")
            category = await uow.catalog.get_category(product.category_id)
            if product.status != ProductStatus.ON_SALE or (
                category is not None and category.status != "ENABLED"
            ):
                raise NotFoundError("商品不存在或已下架")
            skus = await uow.catalog.get_skus(product_id)
            detail = await self._build_detail(uow, product, category, skus, include_off_sale=False)

        await self._cache.set_json(key, _detail_to_dict(detail))
        return detail

    async def admin_detail(self, product_id: int) -> ProductDetail:
        async with self._uow() as uow:
            product = await uow.catalog.get_product(product_id)
            if product is None:
                raise NotFoundError("商品不存在")
            category = await uow.catalog.get_category(product.category_id)
            skus = await uow.catalog.get_skus(product_id)
            return await self._build_detail(uow, product, category, skus, include_off_sale=True)

    async def _build_detail(
        self,
        uow,
        product: Product,
        category: Category | None,
        skus: list[Sku],
        *,
        include_off_sale: bool,
    ) -> ProductDetail:
        sku_ids = [sku.id for sku in skus]
        rules = await uow.activities.active_rules(sku_ids, now=self._clock.now())
        stock = await uow.inventory.available_map(sku_ids)

        cards: list[SkuCard] = []
        for sku in skus:
            priced = quote(sku.price_cents, rules.get(sku.id))
            available = stock.get(sku.id, 0)
            cards.append(
                SkuCard(
                    id=sku.id,
                    code=sku.sku_code,
                    specs=dict(sku.specs or {}),
                    price_cents=priced.unit_cents,
                    original_cents=priced.original_cents,
                    activity_name=priced.activity_name,
                    status=sku.status,
                    available_stock=available,
                    purchasable=(
                        sku.status == ProductStatus.ON_SALE
                        and available > 0
                        and product.status == ProductStatus.ON_SALE
                    ),
                )
            )
        if not include_off_sale:
            cards = [card for card in cards if card.status == ProductStatus.ON_SALE]

        return ProductDetail(
            id=product.id,
            name=product.name,
            description=product.description,
            cover_url=product.cover_url,
            status=product.status,
            category=category,
            skus=cards,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    async def admin_list_products(
        self,
        *,
        page: int,
        page_size: int,
        status: str | None,
        category_id: int | None,
    ) -> tuple[list[tuple[Product, Category]], int]:
        async with self._uow() as uow:
            return await uow.catalog.admin_list_products(
                page=page, page_size=page_size, status=status, category_id=category_id
            )
