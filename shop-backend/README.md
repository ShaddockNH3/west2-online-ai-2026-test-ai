# shop-backend

西二在线后端考核第二至第四轮的完整实现：工作室周边商城的用户、商品、购物车、订单、活动、库存、履约与限量发售。

Python 3.12 + BlackSheep 2.6 + SQLAlchemy 2.1。本机用 SQLite 跑通全部功能，
也提供 MySQL 8 的建表脚本与 Docker Compose。

## 目录

- [快速开始](#快速开始)
- [功能范围](#功能范围)
- [接口](#接口)
- [配置](#配置)
- [测试](#测试)
- [Docker 与 MySQL](#docker-与-mysql)
- [压测](#压测)
- [已知问题](#已知问题)

## 快速开始

```zsh
cp .env.example .env
uv sync --extra dev
uv run python -m scripts.init_db        # 建表 + 演示数据
uv run uvicorn app.server:app --port 8000
```

打开 <http://127.0.0.1:8000>（Vue3 + Naive UI 构建产物已放在 `web/dist`，由后端托管）。
接口健康检查：`curl http://127.0.0.1:8000/health`。

演示账号：`demo / demo123456`（普通用户）、`admin / admin123456`（管理员，只能由初始化脚本创建）。

## 功能范围

| 轮次 | 内容 | 状态 |
| --- | --- | --- |
| 第二轮 | 注册登录、双 Token、个人信息、收货地址、商品浏览、购物车 | 已完成 |
| 第三轮 | RBAC、类目/商品/SKU、结算预览、下单（幂等）、订单查询与取消、mock 支付 | 已完成 |
| 第四轮 | 活动选价、库存占用/释放/扣减、履约与模拟发货、持久化后台任务、限量发售专项、压测 | 已完成 |

六个业务域落在同一个服务里：用户、商品、交易、活动、仓储、履约。专项选的是**限量发售（秒杀）**：抢购接口先原子占库存并返回 ticket，建单交给后台任务，另有结果查询接口。

## 接口

完整定义见 [`docs/openapi.json`](docs/openapi.json)，可直接导入 Apifox（OpenAPI/Swagger → 选文件）。
请求体与响应都是 JSON；受保护接口带 `Authorization: Bearer <accessToken>`。

| 模块 | 主要接口 |
| --- | --- |
| 认证 | `POST /auth/register`、`/auth/login`、`/auth/refresh`、`/auth/logout` |
| 用户 | `GET/PATCH /users/me`、`PATCH /users/me/password` |
| 地址 | `GET/POST /addresses`、`PATCH/DELETE /addresses/{id}`、`PUT /addresses/{id}/default` |
| 商品 | `GET /categories`、`GET /products`、`GET /products/{id}` |
| 购物车 | `GET/POST /cart/items`、`PATCH/DELETE /cart/items/{id}` |
| 订单 | `POST /orders/preview`、`POST /orders`、`GET /orders`、`GET /orders/{orderNo}`、`POST /orders/{orderNo}/cancel`、`POST /orders/{orderNo}/confirm` |
| 支付 | `POST /orders/{orderNo}/payments`、`GET /orders/{orderNo}/payments` |
| 秒杀 | `POST /activities/{id}/flash-sale`、`GET /flash-sale/requests/{requestId}` |
| 管理端 | `/admin/categories`、`/admin/products`、`/admin/skus`、`/admin/activities`、`/admin/inventory`、`/admin/orders`、`/admin/fulfillments`、`/admin/jobs`、`/admin/overview` |

错误统一返回 `{"code": "...", "message": "...", "details": ...}`。
状态码区分 400 参数错误、401 未登录或令牌失效、403 权限不足、
404 资源不存在、409 业务冲突（库存不足、重复支付、售罄）。

## 配置

复制 `.env.example` 后按需改：

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `SHOP_DATABASE_URL` | `sqlite+aiosqlite:///./var/shop.db` | 换 MySQL：`mysql+asyncmy://shop:shop_pwd@127.0.0.1:3306/shop?charset=utf8mb4` |
| `SHOP_JWT_SECRET` | 开发用占位值 | 生产必须换成随机 48 位以上 |
| `SHOP_ACCESS_TTL` / `SHOP_REFRESH_TTL` | 1800 / 604800 | Access 30 分钟，Refresh 7 天 |
| `SHOP_ORDER_EXPIRE_MINUTES` | 30 | 待支付订单超时关单时间 |
| `SHOP_WORKER_ENABLED` / `SHOP_WORKER_CONCURRENCY` | true / 2 | 后台任务 worker |
| `SHOP_REDIS_URL` | 空（不启用） | 填 `redis://127.0.0.1:6379/0` 才开启商品目录缓存 |
| `SHOP_CACHE_TTL` | 20 | 目录缓存秒数，写操作会让旧版本立即失效 |

Token 规则：Access 短期有效，Refresh 长期；刷新会轮换 Refresh
（旧值立即失效，重放会作废整个会话）；退出、改密都会让已签发的两种 Token 失效。

## 测试

```zsh
uv run pytest -q            # 103 个用例，约 1 分钟（argon2 校验占大头）
uv run ruff check .
```

覆盖注册登录与刷新、越权访问、订单幂等与事务回滚、
活动选价、库存占用/释放/扣减、并发下单不超卖、支付失败重试、履约发货失败重试、
后台任务重试与重启恢复、秒杀限购与售罄。

## Docker 与 MySQL

```zsh
docker compose up --build                   # app + MySQL 8.4，自动建表并写入演示数据
SHOP_PORT=8080 docker compose up --build    # 8000 被占用时换端口
```

MySQL 建表脚本由模型生成（`uv run python -m scripts.gen_mysql_ddl`
→ `sql/schema.mysql.sql`），避免手写 DDL 与模型漂移。

本机 Docker Desktop + MySQL 8.4 实测通过：建表、登录、下单、支付、履约发货、
确认收货、限量抢购全链路都走了一遍，压测见 `docs/LOADTEST.md`。

## 压测

```zsh
uv run python -m scripts.init_db --reset
uv run python scripts/loadtest.py --users 40 --concurrency 20
```

结果写入 `logs/loadtest-*.json`。本机实测与优化记录见 [`docs/LOADTEST.md`](docs/LOADTEST.md)。

开了 Redis 目录缓存后商品浏览从 213 涨到 271 req/s（P50 64ms → 42ms）。

## 已知问题

- 容器内只起 1 个 uvicorn worker，多进程部署与连接池调优没有做。
- 40 并发抢购时 P95 约 1.27s（SQLite）/ 1.78s（Docker 里的 MySQL），瓶颈是每个请求
  一个多语句事务加一次提交，不是单纯换数据库能解决的。
- 前端是演示用的简易控制台，没做移动端适配与权限细节打磨。
- 优惠只实现「指定 SKU 固定活动价」一种规则，不支持叠加与满减。
- 商品列表缓存 TTL 20 秒，下单不会主动失效，列表里的库存数字最多滞后 20 秒。

## License

MIT
