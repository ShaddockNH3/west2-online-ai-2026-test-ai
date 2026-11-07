"""类目、商品、SKU 的维护与浏览。"""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import cache, catalog_key
from app.constants import CategoryStatus, ProductStatus
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models import Category, Product, Sku
from app.schemas import CategoryIn, CategoryPatch, ProductIn, ProductPatch, SkuIn, SkuPatch
from app.services import inventory as inventory_service
from app.services.pricing import active_rules, resolve_price
from app.utils import iso, to_cents, yuan


def public_category(category: Category) -> dict:
    return {
        "id": category.id,
        "name": category.name,
        "sortOrder": category.sort_order,
        "status": category.status,
        "createdAt": iso(category.created_at),
    }


async def list_categories(
    session: AsyncSession, *, include_disabled: bool = False
) -> list[Category]:
    stmt = select(Category).order_by(Category.sort_order.asc(), Category.id.asc())
    if not include_disabled:
        stmt = stmt.where(Category.status == CategoryStatus.ENABLED)
    return list(await session.scalars(stmt))


async def create_category(session: AsyncSession, data: CategoryIn) -> Category:
    category = Category(name=data.name, sort_order=data.sortOrder)
    session.add(category)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("类目名称已存在") from exc
    await cache.bump("catalog")
    await session.refresh(category)
    return category


async def update_category(session: AsyncSession, category_id: int, data: CategoryPatch) -> Category:
    category = await session.get(Category, category_id)
    if category is None:
        raise NotFoundError("类目不存在")
    if data.name is not None:
        category.name = data.name
    if data.sortOrder is not None:
        category.sort_order = data.sortOrder
    if data.status is not None:
        category.status = data.status
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("类目名称已存在") from exc
    await cache.bump("catalog")
    await session.refresh(category)
    return category


async def _category_or_404(session: AsyncSession, category_id: int) -> Category:
    category = await session.get(Category, category_id)
    if category is None:
        raise NotFoundError("类目不存在")
    return category


async def create_product(session: AsyncSession, data: ProductIn) -> Product:
    await _category_or_404(session, data.categoryId)
    product = Product(
        category_id=data.categoryId,
        name=data.name,
        description=data.description,
        cover_url=data.coverUrl,
        status=ProductStatus.OFF_SALE,
    )
    session.add(product)
    await session.commit()
    await cache.bump("catalog")
    await session.refresh(product)
    return product


async def update_product(session: AsyncSession, product_id: int, data: ProductPatch) -> Product:
    product = await _product_or_404(session, product_id)
    if data.categoryId is not None:
        await _category_or_404(session, data.categoryId)
        product.category_id = data.categoryId
    if data.name is not None:
        product.name = data.name
    if data.description is not None:
        product.description = data.description
    if data.coverUrl is not None:
        product.cover_url = data.coverUrl
    await session.commit()
    await cache.bump("catalog")
    await session.refresh(product)
    return product


async def set_product_status(session: AsyncSession, product_id: int, status: str) -> Product:
    product = await _product_or_404(session, product_id)
    if status == ProductStatus.ON_SALE:
        sellable = await session.scalar(
            select(Sku.id).where(Sku.product_id == product_id, Sku.status == "ON_SALE").limit(1)
        )
        if sellable is None:
            raise ConflictError("商品还没有可售规格，不能上架")
    product.status = status
    await session.commit()
    await cache.bump("catalog")
    await session.refresh(product)
    return product


async def _product_or_404(session: AsyncSession, product_id: int) -> Product:
    product = await session.get(Product, product_id)
    if product is None:
        raise NotFoundError("商品不存在")
    return product


async def create_sku(session: AsyncSession, product_id: int, data: SkuIn) -> Sku:
    await _product_or_404(session, product_id)
    price_cents = _price_or_400(data.price, "价格")
    if price_cents <= 0:
        raise ValidationError("价格必须大于 0")
    sku_code = data.skuCode or await _next_sku_code(session, product_id)
    sku = Sku(
        product_id=product_id,
        sku_code=sku_code,
        specs=data.specs,
        price_cents=price_cents,
        status=data.status,
    )
    session.add(sku)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("SKU 编码已存在") from exc
    await inventory_service.ensure_inventory(session, sku.id, data.stock)
    await session.commit()
    await cache.bump("catalog")
    await session.refresh(sku)
    return sku


async def update_sku(session: AsyncSession, sku_id: int, data: SkuPatch) -> Sku:
    sku = await session.get(Sku, sku_id)
    if sku is None:
        raise NotFoundError("SKU 不存在")
    if data.specs is not None:
        sku.specs = data.specs
    if data.price is not None:
        price_cents = _price_or_400(data.price, "价格")
        if price_cents <= 0:
            raise ValidationError("价格必须大于 0")
        sku.price_cents = price_cents
    if data.status is not None:
        sku.status = data.status
    await session.commit()
    await cache.bump("catalog")
    await session.refresh(sku)
    return sku


async def list_skus(session: AsyncSession, product_id: int) -> list[Sku]:
    return list(
        await session.scalars(select(Sku).where(Sku.product_id == product_id).order_by(Sku.id))
    )


async def _next_sku_code(session: AsyncSession, product_id: int) -> str:
    count = await session.scalar(select(func.count(Sku.id)).where(Sku.product_id == product_id))
    return f"SKU-{product_id:04d}-{(count or 0) + 1:02d}"


def _price_or_400(value: str, field: str) -> int:
    try:
        return to_cents(value, field=field)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


async def list_public_products(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    category_id: int | None = None,
    keyword: str | None = None,
) -> tuple[list[dict], int]:
    version = await cache.version("catalog") if cache.enabled else 0
    cache_key = catalog_key("products", version, page, page_size, category_id, keyword or "")
    if cache.enabled:
        cached = await cache.get_json(cache_key)
        if cached is not None:
            return cached["items"], cached["total"]

    conditions = [
        Product.status == ProductStatus.ON_SALE,
        Category.status == CategoryStatus.ENABLED,
    ]
    if category_id is not None:
        conditions.append(Product.category_id == category_id)
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(or_(Product.name.like(like), Product.description.like(like)))

    total = await session.scalar(
        select(func.count(Product.id))
        .join(Category, Category.id == Product.category_id)
        .where(*conditions)
    )
    rows = await session.execute(
        select(Product, Category)
        .join(Category, Category.id == Product.category_id)
        .where(*conditions)
        .order_by(Product.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    products = rows.all()
    product_ids = [product.id for product, _ in products]
    skus = list(
        await session.scalars(
            select(Sku).where(Sku.product_id.in_(product_ids), Sku.status == "ON_SALE")
            if product_ids
            else select(Sku).where(False)
        )
    )
    sku_ids = [sku.id for sku in skus]
    rules = await active_rules(session, sku_ids)
    stock = await inventory_service.available_map(session, sku_ids)

    grouped: dict[int, list[Sku]] = {}
    for sku in skus:
        grouped.setdefault(sku.product_id, []).append(sku)

    items = []
    for product, category in products:
        product_skus = grouped.get(product.id, [])
        prices = []
        has_activity = False
        for sku in product_skus:
            price, original, activity_name = resolve_price(sku, rules.get(sku.id))
            prices.append(price)
            has_activity = has_activity or bool(activity_name)
        items.append(
            {
                "id": product.id,
                "name": product.name,
                "coverUrl": product.cover_url,
                "categoryId": category.id,
                "categoryName": category.name,
                "minPrice": yuan(min(prices)) if prices else None,
                "maxPrice": yuan(max(prices)) if prices else None,
                "hasActivity": has_activity,
                "stockAvailable": sum(stock.get(sku.id, 0) for sku in product_skus),
                "createdAt": iso(product.created_at),
            }
        )
    if cache.enabled:
        await cache.set_json(cache_key, {"items": items, "total": int(total or 0)})
    return items, int(total or 0)


async def get_public_product(session: AsyncSession, product_id: int) -> dict:
    version = await cache.version("catalog") if cache.enabled else 0
    cache_key = catalog_key("product", version, product_id)
    if cache.enabled:
        cached = await cache.get_json(cache_key)
        if cached is not None:
            return cached

    product = await _product_or_404(session, product_id)
    category = await session.get(Category, product.category_id)
    if (
        product.status != ProductStatus.ON_SALE
        or category is None
        or category.status != CategoryStatus.ENABLED
    ):
        raise NotFoundError("商品不存在或已下架")
    skus = [sku for sku in await list_skus(session, product_id) if sku.status == "ON_SALE"]
    detail = await _product_detail(session, product, category, skus, include_off_sale=False)
    if cache.enabled:
        await cache.set_json(cache_key, detail)
    return detail


async def get_admin_product(session: AsyncSession, product_id: int) -> dict:
    product = await _product_or_404(session, product_id)
    category = await session.get(Category, product.category_id)
    skus = await list_skus(session, product_id)
    return await _product_detail(session, product, category, skus, include_off_sale=True)


async def _product_detail(
    session: AsyncSession,
    product: Product,
    category: Category | None,
    skus: list[Sku],
    *,
    include_off_sale: bool,
) -> dict:
    sku_ids = [sku.id for sku in skus]
    rules = await active_rules(session, sku_ids)
    stock = await inventory_service.available_map(session, sku_ids)
    sku_items = []
    for sku in skus:
        price, original, activity_name = resolve_price(sku, rules.get(sku.id))
        available = stock.get(sku.id, 0)
        sku_items.append(
            {
                "id": sku.id,
                "code": sku.sku_code,
                "specs": sku.specs,
                "price": yuan(price),
                "originalPrice": yuan(original),
                "activityName": activity_name or None,
                "status": sku.status,
                "availableStock": available,
                "purchasable": sku.status == "ON_SALE"
                and available > 0
                and (product.status == ProductStatus.ON_SALE),
            }
        )
    data = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "coverUrl": product.cover_url,
        "status": product.status,
        "category": public_category(category) if category else None,
        "skus": sku_items,
        "createdAt": iso(product.created_at),
        "updatedAt": iso(product.updated_at),
    }
    if not include_off_sale:
        data["skus"] = [item for item in sku_items if item["status"] == "ON_SALE"]
    return data


async def admin_list_products(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    status: str | None = None,
    category_id: int | None = None,
) -> tuple[list[dict], int]:
    conditions = []
    if status:
        conditions.append(Product.status == status)
    if category_id is not None:
        conditions.append(Product.category_id == category_id)
    total = await session.scalar(select(func.count(Product.id)).where(*conditions))
    rows = await session.execute(
        select(Product, Category)
        .join(Category, Category.id == Product.category_id)
        .where(*conditions)
        .order_by(Product.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    items = [
        {
            "id": product.id,
            "name": product.name,
            "status": product.status,
            "categoryId": category.id,
            "categoryName": category.name,
            "createdAt": iso(product.created_at),
        }
        for product, category in rows.all()
    ]
    return items, int(total or 0)
