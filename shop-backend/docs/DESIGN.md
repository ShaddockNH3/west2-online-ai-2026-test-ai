# 设计说明

## 1. 范围与边界

一个服务承载六个业务域：用户、商品、交易、活动、仓储、履约。不是六个微服务——按业务域分目录、分服务模块，共享一个数据库，这样事务边界清楚，也不用为一家店引入注册中心和网关。

专项选**限量发售（秒杀）**：参加活动的 SKU 有发售数量与单人限购，抢购接口只做「占名额 + 占库存 + 写请求 + 投任务」，建单交给后台；前端轮询结果。

不做：真实支付、退款、多商家、售后、采购调拨盘点、报表平台。

## 2. 代码结构

```text
app/
├── main.py             应用工厂：配置、路由、中间件、生命周期
├── server.py           uvicorn 入口（app = create_app()）
├── api/
│   ├── router.py       汇总注册各域路由
│   └── routes/         各域 HTTP 处理：参数解析、鉴权、拼响应
├── core/               横切关注点
│   ├── config.py       环境变量与路径
│   ├── db.py           引擎、会话、SQLite PRAGMA
│   ├── cache.py        Redis 目录缓存（可选，未配置则直通）
│   ├── security.py     argon2 与双 Token
│   ├── errors.py       业务异常 + 统一异常处理器
│   ├── params.py       请求体/查询参数解析
│   ├── responses.py    统一响应结构
│   └── logging.py      日志配置、请求 ID 中间件
├── models/             按域拆的表定义，base 放 Base 与时间戳 Mixin
├── schemas/            按域拆的请求模型，base 放 StrictModel
├── services/           业务规则、事务边界、状态流转
└── worker.py           任务分发与重试
```

拆分依据来自三处官方文档的共识，不是个人偏好：

- **FastAPI「Bigger Applications」**：按业务功能划分子包，明确反对把所有 model 堆一起、所有路由堆一起；
- **Flask 官方 Blueprints**：应用工厂负责装配，每个功能一个 blueprint，扩展集中初始化；
- **BlackSheep MVC 模板**：`app/` 只放 Web 相关（controllers、static、views），领域模型放平级的 `domain/`，与框架解耦。

社区实践（`fastapi-best-practices`，Netflix Dispatch 风格）更彻底，一个域一个目录，
内含 `router.py` / `schemas.py` / `models.py` / `service.py`。本项目没走到那一步：
`services/` 与 `routes/` 仍按同名域文件一一对应，跨域依赖显式 import，
好处是事务边界一眼能看清，代价是文件多了一层目录跳转。

三个具体取舍：

1. **不用 src layout**。项目是单包、不发布到 PyPI，`app/` 直接作为顶层包更省事；
   要发布时再迁到 `src/shop/`。
2. **models 与 schemas 拆包但保留 `__init__` 重导出**。外部仍然
   `from app.models import Order`，内部文件按域拆开；迁移成本低，也不会让调用方跟着改。
3. **只做一层接口，不加 `/api/v1` 前缀**。考核文档给定的是 `/auth/login`、`/orders`
   这类路径，加版本前缀反而与文档不一致；真要版本化，用 `router.include_router` 挂两次即可。

路由里每个写操作都是 `async with db.session()`，服务层负责 `commit`。异常向上抛，由统一异常处理器转 JSON；
未提交的事务在会话关闭时回滚，所以「库存扣了但订单没建」不会发生。

`require_principal` 每次请求查一次会话 + 用户（一条 join），
既校验 JWT 签名与过期，也校验会话是否被退出/改密撤销。
角色以数据库为准，不信 token 里的 role。

## 3. 数据模型

| 表 | 作用 | 关键约束 |
| --- | --- | --- |
| `users` | 账号与角色 | `username` 唯一，密码只存 argon2 哈希 |
| `auth_sessions` | 一次登录，双 Token 挂在这里 | `refresh_jti` 轮换，`revoked_at` 撤销 |
| `addresses` | 收货地址 | `user_id` 索引；同用户只有一条默认 |
| `categories` / `products` / `skus` | 商品域 | SKU 有独立价格、规格 JSON、上下架 |
| `cart_items` | 购物车 | `(user_id, sku_id)` 唯一，同 SKU 合并 |
| `orders` / `order_items` | 订单与明细 | `(user_id, request_id)` 唯一；明细存快照 |
| `payments` | mock 支付流水 | 一单最多一条 SUCCESS（状态机保证） |
| `activities` / `activity_skus` | 活动与活动价 | 同活动同 SKU 唯一；`sold_count` 原子累加 |
| `inventory` / `inventory_logs` | 库存与流水 | `(warehouse_id, sku_id)` 唯一；流水记关联订单 |
| `fulfillments` | 履约单 | 一个订单一张，`order_id` 唯一 |
| `jobs` | 后台任务 | `dedupe_key` 唯一，防重复投递 |
| `flash_sale_requests` | 抢购申请 | `(user_id, request_id)` 唯一，存成交价快照 |

金额用整数分：`3900` 表示 39.00 元，接口输出十进制字符串。浮点在「2 件 39 元 + 1 件 12 元 = 90 元」这种地方迟早出错。

订单明细存商品名、规格、原价、成交价、活动名，后续改价改名不影响历史订单。收货人、电话、地址同样在订单上另存一份。

## 4. 关键流程

### 下单

```text
校验 requestId 幂等 → 校验地址归属 → 读购物车项
→ 重新查商品状态、活动价、库存 → 逐项 UPDATE 占库存
→ 建订单 + 明细（快照）→ 删购物车项 → 投「超时关单」任务 → commit
```

- 价格、库存、总额只由服务端计算，请求体里带 `totalAmount` 之类的字段会被 `extra=forbid` 直接拒绝。
- 占库存是带条件的原子更新：
  `UPDATE inventory SET available=available-? WHERE available>=?`。
  `rowcount=0` 就抛库存不足，整个事务回滚，购物车项也不会被删。
- `requestId` 相同且内容相同返回原订单（`replayed: true`），内容不同返回 409。唯一索引兜住并发重放。

### 支付

失败：只写一条 FAILED 流水，订单仍待支付。
成功：`UPDATE orders SET status='PAID' WHERE status='PENDING_PAYMENT'` 抢状态，成功后再扣库存、写流水、投履约任务。任何一步失败整体回滚，不会出现「流水成功、订单待支付」。

### 取消与超时

取消同样用带状态条件的 UPDATE 抢，然后逐项释放 `reserved → available`。超时关单走后台任务，逻辑同取消，`cancel_reason=EXPIRED`。两个操作同时发生只有一个能成功。

### 履约

支付成功 → 任务生成履约单（待备货）→ 管理员备货 → 调本地模拟物流发货（会返回运单号，也能模拟失败）→ 用户确认收货，订单和履约单同时完成。

发货失败不改状态，只累加 `attempts` 并记录 `last_error`，管理员可以直接再点一次。

### 秒杀

```text
校验活动时间窗 → 幂等查 requestId → 校验限购（已排队+已成功数量）
→ 原子累加 activity_skus.sold_count 且不超过 sale_quota
→ 原子占库存 → 写 flash_sale_requests(QUEUED) + 投建单任务 → 返回 202
```

- 名额和库存都在数据库里用条件 UPDATE 扣，不靠「先查再写」，并发下不会超卖。
- 后台任务用申请里存的活动价建单，不再重新选价，活动结束后也按抢购时的价格成交。
- 建单连续失败会把申请标成 FAILED，并释放库存、归还名额。

## 5. 后台任务

任务表在数据库里，不是内存队列：应用重启后未完成的任务还在。worker 用「先挑一条、再带状态条件 UPDATE 抢占」的方式领取，多协程不会重复执行。

- 失败退避 `2^attempts` 秒，超过 `max_attempts` 记为 FAILED，管理端可以查原因、重新执行。
- 进程被 kill 时停留在 RUNNING 的任务，启动时按 `locked_at` 超时捞回 PENDING。
- 任务类型：超时关单、生成履约单、订单通知、秒杀建单。

## 6. 活动选价

同一 SKU 可能命中多个进行中的活动，取**当前时间窗内、状态 ACTIVE、价格最低**的那个；
活动价高于原价时按原价卖。商详、购物车、预览、下单都走同一个 `resolve_price`，
不会出现「详情页 34 元、结算 39 元」。

## 7. 取舍

- **SQLite 起步**：本机零依赖，测试跑得快。写操作串行，压测里能直接看到上限
  （见 `LOADTEST.md`）。模型全部方言中立，换 MySQL 只需要改连接串和装 `asyncmy`。
  实测换成 Docker 里的 MySQL 8.4 并没有更快——小事务每次提交落盘的成本比
  WAL + `synchronous=NORMAL` 更高，瓶颈在事务本身而不在数据库品牌。
- **不用 ORM 关系**：全部显式查询，避免异步下的隐式懒加载；代价是查询代码略长。
- **不用 Redis**：没引入缓存和分布式锁，所有一致性靠数据库条件更新与唯一约束。以这个项目的并发量够用。
- **前端只做控制台**：不追求视觉，覆盖完整链路，方便答辩时点着走。

## 7.1 目录缓存

商品列表每次要查商品、类目、SKU、活动价、库存五份数据，是浏览请求的主要成本。
接一个可选的 Redis 读缓存：缓存列表（分页/类目/关键词的组合）与详情，默认 TTL 20 秒。

失效用版本号，不用遍历删 key：`shop:version:catalog` 是个计数器，缓存 key 里带上它的值；
管理员改类目、商品、SKU、活动、库存时 `INCR` 一次，旧版本的 key 不会再被读到，
等 TTL 自然回收。实测改价后详情立刻变，不需要等缓存过期。

不缓存用户数据、订单和库存扣减。下单不主动 `INCR`，所以列表里的库存数字最多滞后
一个 TTL——这是拿一致性换吞吐的明确取舍，写在 README 的已知问题里。

没配 `SHOP_REDIS_URL` 或 Redis 连不上时，缓存层完全直通，功能不受影响；测试也不依赖它。

## 8. 跨数据库兼容

模型和查询都写成方言中立的形式，只在两个地方按方言分支：

| 位置 | SQLite | MySQL |
| --- | --- | --- |
| `PRAGMA journal_mode=WAL` | 建表时执行一次 | 跳过（会直接语法错误） |
| 库存条件更新 | `UPDATE ... RETURNING` 少一次 SELECT | 用 `rowcount` 判断，再按数量推算前后值 |

金额用整数、时间用 `DATETIME`、规格用 JSON 列，两边语义一致。建表既能走
`create_all`，也能用 `sql/schema.mysql.sql`（由模型生成，不会漂移）。

## 9. 测试策略

`pytest` 每个用例一个独立 SQLite 文件，走真实 HTTP 层（BlackSheep TestClient），
只对时间与后台任务做显式驱动（把 `next_run_at` 提前、手动 `run_once`）。

重点覆盖「不应该发生」的情况：越权、重复提交、重复支付、已取消再支付、并发超卖、任务失败后重试、重启后任务还在。
