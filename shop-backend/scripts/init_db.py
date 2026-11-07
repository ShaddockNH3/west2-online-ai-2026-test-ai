"""初始化数据库与演示数据。

python -m scripts.init_db          # 建表 + 补齐演示数据（幂等）
python -m scripts.init_db --reset  # 删表重建，清空全部数据
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import timedelta

from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import db
from app.core.security import hash_password
from app.domain.constants import (
    DEFAULT_WAREHOUSE_ID,
    ActivityStatus,
    ActivityType,
    InventoryChange,
    Role,
)
from app.infrastructure.persistence.models import (
    Activity,
    ActivitySku,
    Address,
    Category,
    Inventory,
    InventoryLog,
    Product,
    Sku,
    User,
    Warehouse,
)
from app.utils import utcnow


async def ensure_user(session, username: str, password: str, role: str, nickname: str) -> User:
    user = await session.scalar(select(User).where(User.username == username))
    if user is not None:
        return user
    user = User(
        username=username,
        password_hash=hash_password(password),
        nickname=nickname,
        role=role,
    )
    session.add(user)
    await session.flush()
    return user


async def ensure_category(session, name: str, sort_order: int) -> Category:
    category = await session.scalar(select(Category).where(Category.name == name))
    if category is not None:
        return category
    category = Category(name=name, sort_order=sort_order)
    session.add(category)
    await session.flush()
    return category


async def ensure_product(session, category: Category, name: str, description: str) -> Product:
    product = await session.scalar(select(Product).where(Product.name == name))
    if product is not None:
        return product
    product = Product(
        category_id=category.id,
        name=name,
        description=description,
        status="ON_SALE",
    )
    session.add(product)
    await session.flush()
    return product


async def ensure_sku(
    session, product: Product, code: str, specs: dict[str, str], price_cents: int, stock: int
) -> Sku:
    sku = await session.scalar(select(Sku).where(Sku.sku_code == code))
    if sku is not None:
        return sku
    sku = Sku(
        product_id=product.id,
        sku_code=code,
        specs=specs,
        price_cents=price_cents,
        status="ON_SALE",
    )
    session.add(sku)
    await session.flush()
    session.add(Inventory(warehouse_id=DEFAULT_WAREHOUSE_ID, sku_id=sku.id, available=stock))
    await session.flush()
    session.add(
        InventoryLog(
            inventory_id=(
                await session.scalar(select(Inventory.id).where(Inventory.sku_id == sku.id))
            ),
            sku_id=sku.id,
            change_type=InventoryChange.INBOUND,
            quantity=stock,
            available_before=0,
            available_after=stock,
            reason="初始化库存",
        )
    )
    return sku


async def seed(reset: bool = False) -> None:
    settings = get_settings()
    db.configure(settings)
    if reset:
        await db.drop_all()
    await db.create_all()

    async with db.session() as session:
        warehouse = await session.get(Warehouse, DEFAULT_WAREHOUSE_ID)
        if warehouse is None:
            session.add(Warehouse(id=DEFAULT_WAREHOUSE_ID, name="默认仓库", is_default=True))
            await session.flush()

        await ensure_user(
            session, settings.admin_username, settings.admin_password, Role.ADMIN, "店主"
        )
        demo = await ensure_user(
            session, settings.demo_username, settings.demo_password, Role.USER, "同学"
        )

        address = await session.scalar(select(Address).where(Address.user_id == demo.id))
        if address is None:
            session.add(
                Address(
                    user_id=demo.id,
                    receiver="西二同学",
                    phone="13800000000",
                    detail="福建省福州市福州大学 西二在线工作室",
                    is_default=True,
                )
            )

        clothing = await ensure_category(session, "服饰", 1)
        bags = await ensure_category(session, "包袋", 2)
        small = await ensure_category(session, "小物", 3)

        tee = await ensure_product(
            session, clothing, "工作室文化衫", "纯棉短袖，正面印工作室鲸鱼 logo。"
        )
        black_m = await ensure_sku(
            session, tee, "TEE-BLK-M", {"颜色": "黑色", "尺码": "M"}, 3900, 50
        )
        await ensure_sku(session, tee, "TEE-WHT-L", {"颜色": "白色", "尺码": "L"}, 3900, 30)

        bag = await ensure_product(session, bags, "帆布袋", "加厚帆布，装得下 16 寸笔记本。")
        await ensure_sku(session, bag, "BAG-NAT-01", {"颜色": "米白"}, 2900, 20)

        badge = await ensure_product(session, small, "亚克力徽章", "55mm，别在包上刚好。")
        await ensure_sku(session, badge, "BADGE-01", {"规格": "默认"}, 1200, 100)

        existing = await session.scalar(select(Activity).where(Activity.name == "开学季周边特惠"))
        if existing is None:
            now = utcnow()
            activity = Activity(
                name="开学季周边特惠",
                type=ActivityType.FIXED_PRICE,
                status=ActivityStatus.ACTIVE,
                description="文化衫限时 34 元，活动结束恢复原价。",
                starts_at=now - timedelta(days=1),
                ends_at=now + timedelta(days=30),
            )
            session.add(activity)
            await session.flush()
            session.add(
                ActivitySku(
                    activity_id=activity.id,
                    sku_id=black_m.id,
                    activity_price_cents=3400,
                )
            )

        flash_existing = await session.scalar(
            select(Activity).where(Activity.name == "限量徽章 50 枚")
        )
        if flash_existing is None:
            now = utcnow()
            flash = Activity(
                name="限量徽章 50 枚",
                type=ActivityType.FLASH_SALE,
                status=ActivityStatus.ACTIVE,
                description="限量发售，每人限购 2 枚。",
                starts_at=now - timedelta(days=1),
                ends_at=now + timedelta(days=7),
            )
            session.add(flash)
            await session.flush()
            badge_sku = await session.scalar(select(Sku).where(Sku.sku_code == "BADGE-01"))
            if badge_sku is not None:
                session.add(
                    ActivitySku(
                        activity_id=flash.id,
                        sku_id=badge_sku.id,
                        activity_price_cents=900,
                        sale_quota=50,
                        per_user_limit=2,
                    )
                )

        await session.commit()

    print("数据库初始化完成")
    print(f"  管理员：{settings.admin_username} / {settings.admin_password}")
    print(f"  普通用户：{settings.demo_username} / {settings.demo_password}")


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化商城数据库")
    parser.add_argument("--reset", action="store_true", help="删表重建，清空数据")
    args = parser.parse_args()
    asyncio.run(seed(reset=args.reset))


if __name__ == "__main__":
    main()
