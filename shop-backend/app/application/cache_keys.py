"""缓存 key 的组织方式：版本号 + 参数，写操作只改版本号就整体失效。"""

from __future__ import annotations

from typing import Any

PREFIX = "shop:"
CATALOG_NAMESPACE = "catalog"


def _join(*parts: Any) -> str:
    return PREFIX + ":".join(str(part) for part in parts)


def catalog_products_key(
    version: int, page: int, page_size: int, category_id: int | None, keyword: str
) -> str:
    return _join(CATALOG_NAMESPACE, "products", version, page, page_size, category_id, keyword)


def catalog_product_key(version: int, product_id: int) -> str:
    return _join(CATALOG_NAMESPACE, "product", version, product_id)
