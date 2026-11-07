# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY sql ./sql
COPY web/dist ./web/dist

ENV SHOP_ENV=prod \
    SHOP_DATABASE_URL=sqlite+aiosqlite:////app/var/shop.db \
    SHOP_WORKER_ENABLED=true

RUN mkdir -p /app/var /app/logs

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

# 启动时补齐表结构与演示数据，重复执行是安全的
CMD ["sh", "-c", "python -m scripts.init_db && uvicorn app.server:app --host 0.0.0.0 --port 8000 --workers 1"]
