# Foundation 2 · 爬虫

四个作业 + 一个 Bonus（B-Wiki）。全部脚本共用 `common.py` 里的会话、限速、断点续爬与文本清洗。

```text
crawler/
├── common.py                  # Session 重试、限速器、JSONL 增量存储、文本清洗
├── assignment1_jwch.py        # 作业 1：福大教务通知（含附件下载量、附件下载 Bonus）
├── assignment2_zhihu.py       # 作业 2：知乎话题（Playwright 操控浏览器）
├── assignment3_ospp.py        # 作业 3：开源之夏项目列表（接口）
├── assignment4_openmeteo.py   # 作业 4：Open-Meteo 天气数据（单次请求）
├── bonus_bwiki.py             # Bonus：B-Wiki 方案舰娘（MediaWiki API）
└── data/                      # 全部产出
```

## 环境

```zsh
uv pip install requests beautifulsoup4 lxml playwright
# 作业 2 用本机已装的 Chrome，不必 playwright install chromium
```

---

## 作业 1 · 福大教务通知

```zsh
python assignment1_jwch.py                # 默认爬 600 条
python assignment1_jwch.py --target 700   # 想多爬点
python assignment1_jwch.py --download     # Bonus：附件也下下来
python assignment1_jwch.py --export-only  # 只把 jsonl 重新导成 CSV
```

### 页面结构（2026-11 实测）

| 位置 | 结构 | 说明 |
| --- | --- | --- |
| 列表页 | `ul.list-gl > li` | 第 1 页是 `jxtz.htm`，第 n 页是 `jxtz/{217-n}.htm`（**页码倒着编**，最后一页是 `jxtz/1.htm`，共 216 页） |
| 列表项 | `span.doclist_time` + `【通知人】` + `a[title]` | 通知人藏在列表项文本的 `【】` 里 |
| 详情页 | `div.v_news_content` | 正文；发布时间用正则从页面文本里抠 `发布时间：YYYY-MM-DD` |
| 附件 | `附件【<a href="...wbfileid=18563163">名.pdf</a>】已下载<span id="nattach18563163">` | 下载次数是 JS 渲染的 |

### 附件下载次数（题目要求用 Ajax，不许用 Selenium）

页面里那个 `<span>` 的实际内容是：

```html
<script>getClickTimes(18563163, 1744984858, "wbnewsfile", "attach")</script>
```

`getClickTimes` 定义在 `/system/resource/js/ajax.js`，落到这个接口：

```text
GET https://jwch.fzu.edu.cn/system/resource/code/news/click/clicktimes.jsp
    ?wbnewsid=18563163&owner=1744984858&type=wbnewsfile&randomid=nattach
→ {"wbshowtimes": 86, "randomid": "nattach", "wbnewsid": 18563163}
```

`wbshowtimes` 就是下载次数。`owner` 从附件链接的 `?owner=` 参数里取。

### 产出

| 文件 | 内容 |
| --- | --- |
| `data/jwch_notices.jsonl` | 一行一条原始记录，**断点续爬靠它** |
| `data/jwch_notices.csv` | 汇总表：通知人 / 标题 / 发布时间 / 详情链接 / 正文 / 附件名 / 附件下载次数 / 附件链接 / 附件数量 / 正文长度 |
| `data/attachments/<通知 id>/` | `--download` 时的附件文件 |

一条记录长这样：

<!-- autocorrect-disable -->

```json
{
  "id": "14874",
  "publish_date": "2026-11-02",
  "notifier": "教学运行",
  "title": "关于做好2027届预计毕业生电子注册图像采集工作的通知",
  "url": "https://jwch.fzu.edu.cn/info/1036/14874.htm",
  "body": "各学院： 根据《高等教育学历证书电子注册图像采集规范及信息标准》…",
  "attachments": [
    {"name": "附件1：拍照地点示意图.pdf", "download_url": "…", "file_id": "18563163", "download_count": 86}
  ]
}
```

<!-- autocorrect-enable -->

### 题目里那个「思考」

> 爬下来一个数据就存进文件中和爬完之后再批量存入文件中有什么差别？如果程序进行到一半网络中断应该怎么办？

**差别**：

* 批量的写法是「全部爬完 → `json.dump` 一次」。中途断网 / Ctrl-C / 断电，**内存里的一切全丢**，
  下次只能从头再来；而且数据量大时内存吃紧，最后那一次写入还可能因为磁盘满而整体失败。
* 逐条写入的写法是「爬到一条 → 追加一行 → flush + fsync」。中断时最多丢当前这一条，
  下次启动读一遍已有的 id，跳过就能接着爬。日志式追加还有个好处：坏了一行不影响其他行。

**所以这个爬虫的写法是**：

1. 每爬完一条，立刻 `store.append(record)`，内部 `flush()` + `os.fsync()`（真的落到磁盘，不是停在缓冲区）；
2. 启动时 `existing_ids()` 把 `id` 读出来，遇到就 `continue`；
3. `KeyboardInterrupt` 被捕获，`finally` 里照样导出 CSV。

实测：爬到第 300 多条时 `pkill` 掉进程，重新运行直接从第 301 条继续，日志第一行就是
`检测到已有 341 条记录，将从断点继续。`

### 反爬与礼貌

* 教务处没有反爬（题目也说了，校园网随便爬），但脚本仍然保持 0.2s 的最小间隔、串行请求；
* `build_session()` 只对连接错误 / 5xx / 429 重试，404 之类直接跳过并打日志；
* 单条通知失败不会污染整批——附件下载失败只打一行提示。

---

## 作业 2 · 知乎话题（浏览器操控）

```zsh
python assignment2_zhihu.py --login     # 弹出有头 Chrome，扫码登录后自动存 cookie
python assignment2_zhihu.py             # 复用登录态，爬 20 个问题 × 10 条回答
```

**这一步必须人工扫码**，所以仓库里没有 `zhihu_topic_answers.csv`——
cookie 等同于账号密码，既不能提交，也不该由 AI 代劳登录。

做法要点：

* 用 Playwright 驱动**本机 Chrome**（`channel="chrome"`），不用额外下载 chromium；
* `add_init_script` 抹掉 `navigator.webdriver`，降低被判定为自动化的概率；
* 登录态用 Playwright 的 `storage_state`（含 cookies + localStorage）存成 json，
  放在 `data/` 且被 `.gitignore` 排除；
* 抓取时先滚到底触发懒加载，再点掉「阅读全文」，最后按 `.RichText` 取纯文本；
* 每个问题之间随机停 1.5–3 秒，避免触发风控。

cookie 泄露的后果：别人拿到 `z_c0` 就等于登录了你的账号，能改资料、发内容、看私信。
所以这类文件只放本地，绝不进 git（题目里那篇「学生误泄 API 密钥」是同一个道理）。

---

## 作业 3 · 开源之夏项目列表（接口）

```zsh
python assignment3_ospp.py
```

页面是前后端分离的，HTML 里没有数据。抓包（或在前端 bundle 里搜 `/api/`）能得到：

```text
POST /api/getProList   {"pageNum": 1, "pageSize": 50}
     → {"total": 102, "rows": [{programCode, proId, programName, difficulty, techTag, ...}]}

POST /api/getProDetail {"programId": 30}        # 值为列表里的 proId
     → {programDesc, outputRequirement, techRequirement, programmingLanguageTag, ...}
```

坑：详情接口的参数名是 **`programId`**，不是 `proId`、不是 `programCode`。
`proId` / `programId` / `id` / `code` / `programCode` 都试了一遍，只有 `programId` 返回 200，
其余都是 `410 {"err_code":4108,"message":"项目不存在"}`。

产出 `data/ospp_projects.csv`：项目编号 / 项目名 / 所属组织 / 项目难度 / 技术领域 /
编程语言 / 项目简述 / 产出要求 / 技术要求 / 奖金 / 详情链接。

实测 102 个项目全部拿到简述；难度分布是「进阶 89、基础 11、挑战 2」。

**Bonus（下载申请书 PDF）**：`/api/downloadApplication` 需要登录态，未登录返回 401。
脚本支持 `--cookie-file` 传浏览器导出的 cookie，但没有凭证时不会伪造，直接跳过并说明。

---

## 作业 4 · Open-Meteo（只发一次请求）

```zsh
python assignment4_openmeteo.py
```

把 hourly 和 daily 变量塞进**同一个** `/v1/archive` 请求：

```text
GET https://archive-api.open-meteo.com/v1/archive
    ?latitude=26.05942&longitude=119.198
    &start_date=2024-01-01&end_date=2024-12-31
    &hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,
            weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,
            shortwave_radiation_instant,is_day
    &daily=temperature_2m_mean,temperature_2m_max,temperature_2m_min,
           precipitation_sum,sunshine_duration
    &timezone=Asia/Shanghai
```

产出：

| 文件 | 行数 | 说明 |
| --- | --- | --- |
| `data/openmeteo_2024_hourly.csv` | 8784 | 2024 是闰年，366×24 |
| `data/openmeteo_2024_daily.csv` | 366 | 每日 5 个变量 |
| `data/openmeteo_2024_raw.json` | — | 原始响应，便于复核 |

两个小发现：

1. 题目写的 `cloud_cover_total` 在 archive API 里不存在（会 400），实际字段是 `cloud_cover`；
2. 返回的经纬度是 `26.045692, 119.24508` —— 接口会把坐标吸附到最近的网格点，
   海拔 3m。原始请求坐标仍按题目给的旗山校区值。

CSV 里额外加了一列 `weather_desc`（WMO 天气代码的中文名），纯本地映射，不额外发请求。

---

## Bonus · B-Wiki 方案舰娘

```zsh
python bonus_bwiki.py
```

用 MediaWiki Action API，不解析 HTML：

```text
GET https://wiki.biligame.com/blhx/api.php
    ?action=query&list=categorymembers&cmtitle=Category:方案舰娘
    &cmlimit=500&format=json&formatversion=2&maxlag=5
→ 48 个页面

GET …?action=parse&page=埃吉尔&prop=wikitext&format=json&formatversion=2&maxlag=5
→ 原始 wikitext
```

礼貌三件套都实现了：

* 每次请求间隔 ≥ 1 秒（`RateLimiter(1.1)`），**全程串行**，不并发；
* 带 `maxlag=5`，服务器回 `maxlag` 错误时按 `Retry-After`（没有就等 5 秒）重试，3 次不成就跳过；
* User-Agent 写了联系邮箱。

产出 `data/bwiki_raw/PR_<舰名>.txt`（48 个原始 wikitext 文件）与 `data/bwiki_pages.csv` 索引。
题目说不用洗数据，所以文件就是原始 `{{舰娘图鉴 |…}}` 模板文本。

---

## 关于「Bonus · 历年培养方案」

这次没做。它不是技术难，是**思路题**：提示里说了「从各学院官网爬走不通，要先拿到历年专业代号」，
而专业代号要从福大高考高招的历史页面里翻，本质上是一次需要人工摸清站点结构的探索，
代码量反而不是重点。留到单独一轮做，避免这轮作业里塞一个半成品。
