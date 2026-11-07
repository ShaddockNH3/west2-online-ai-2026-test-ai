"""从 SQLAlchemy 模型生成 MySQL 建表脚本，避免手写 DDL 与模型漂移。

python -m scripts.gen_mysql_ddl
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.infrastructure.persistence.models import Base

OUTPUT = Path(__file__).resolve().parent.parent / "sql" / "schema.mysql.sql"

HEADER = """-- 由 python -m scripts.gen_mysql_ddl 生成，请勿手改。
-- 适用于 MySQL 8.0+，字符集 utf8mb4。

CREATE DATABASE IF NOT EXISTS shop
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;
USE shop;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
"""

FOOTER = """
SET FOREIGN_KEY_CHECKS = 1;

-- 默认仓库与默认门店数据由 scripts/init_db.py 写入。
"""


def main() -> None:
    dialect = mysql.dialect()
    chunks = [HEADER]
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=dialect)).strip()
        ddl = ddl.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1)
        chunks.append(ddl + ";\n")
        for index in table.indexes:
            chunks.append(str(CreateIndex(index).compile(dialect=dialect)).strip() + ";\n")
        chunks.append("\n")
    chunks.append(FOOTER)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("".join(chunks), encoding="utf-8")
    print(f"写入 {OUTPUT}（{len(Base.metadata.sorted_tables)} 张表）")


if __name__ == "__main__":
    main()
