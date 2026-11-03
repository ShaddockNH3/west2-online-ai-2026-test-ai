# Foundation 2 · 网络爬虫与数据分析

四个爬虫作业 + 一个爬虫 Bonus（B-Wiki）+ 三个数据分析作业 + 一个分析 Bonus（图像）。

```text
foundation2/
├── crawler/                    # 爬虫
│   ├── common.py               # Session 重试 / 限速 / JSONL 断点续爬 / 文本清洗
│   ├── assignment1_jwch.py     # 作业 1：福大教务通知（700 条，含附件下载量）
│   ├── assignment2_zhihu.py    # 作业 2：知乎话题（Playwright）
│   ├── assignment3_ospp.py     # 作业 3：开源之夏项目列表（接口）
│   ├── assignment4_openmeteo.py# 作业 4：Open-Meteo 天气（单次请求）
│   ├── bonus_bwiki.py          # Bonus：B-Wiki 方案舰娘（MediaWiki API）
│   └── data/                   # 产出：CSV / JSON / 原始 wikitext
├── analysis/                   # 数据分析
│   ├── assignment1_jwch_analysis.ipynb  # Pandas 分析（已执行，含图表与结论）
│   ├── assignment2_logistic.py          # Matplotlib 画 Logistic
│   ├── assignment3_numpy.py             # NumPy 基本使用 + 广播
│   ├── bonus_image.py                   # 图像数组操作
│   └── report/                          # 9 张图
├── notes.md                    # 踩坑记录（14 条）
└── README.md
```

## 完成情况

| 作业 | 内容 | 状态 | 产出 |
| --- | --- | --- | --- |
| 爬虫 1 | 福大教务通知 500+ 条 | 已完成 | 700 条通知 / 585 个附件 |
| 爬虫 2 | 知乎话题（浏览器操控） | 脚本完成，需扫码登录 | 不提交登录态 |
| 爬虫 3 | 开源之夏项目列表（接口） | 已完成 | 102 个项目 |
| 爬虫 4 | Open-Meteo 单次请求 | 已完成 | 8784 小时 + 366 天 |
| Bonus | B-Wiki 方案舰娘 | 已完成 | 48 页原始 wikitext |
| Bonus | 历年培养方案 | 未做 | — |
| 分析 1 | 教务处通知分析（Pandas） | 已完成 | notebook + 6 张图 |
| 分析 2 | Logistic 函数（Matplotlib） | 已完成 | 1 张 2×2 图 |
| 分析 3 | 矩阵与广播（NumPy） | 已完成 | 控制台输出 |
| Bonus | 图像数组操作 | 已完成 | 1 张 2×4 图 |

两个 Bonus 里，**B-Wiki 做了，「历年培养方案」跳过**——后者不难在代码，
难在要先摸清「从高招页面拿历年专业代号」这条链路，属于需要单独一轮的探索题。

## 环境

```zsh
uv pip install requests beautifulsoup4 lxml numpy pandas matplotlib jupyterlab playwright
```

作业 2 用的是**本机已安装的 Chrome**（`channel="chrome"`），不需要 `playwright install`。

## 快速运行

```zsh
cd crawler

python assignment1_jwch.py            # 约 8 分钟，700 条
python assignment1_jwch.py --download # 顺便把附件下下来（Bonus）
python assignment3_ospp.py            # 约 40 秒，102 个项目
python assignment4_openmeteo.py       # 单次请求，秒级
python bonus_bwiki.py                 # 48 页 × 1.1 秒 ≈ 1 分钟

python assignment2_zhihu.py --login   # 先扫码
python assignment2_zhihu.py           # 再抓取

cd ../analysis
jupyter nbconvert --to notebook --execute --inplace assignment1_jwch_analysis.ipynb
python assignment2_logistic.py
python assignment3_numpy.py
python bonus_image.py
```

## 爬虫

| 站点 | 方式 | 关键点 |
| --- | --- | --- |
| 福大教务处 | requests + bs4 | 页码倒序（第 n 页 = `217-n`）；附件下载次数走 `clicktimes.jsp` 这个 Ajax 接口 |
| 知乎 | Playwright 驱动本机 Chrome | 必须扫码登录，`storage_state` 复用登录态 |
| 开源之夏 | POST 接口 | 详情接口参数是 `programId`（值取 `proId`） |
| Open-Meteo | 单次 GET | hourly + daily 合并到一个请求；`cloud_cover` 才是总云量 |
| B-Wiki | MediaWiki Action API | `maxlag=5` + 1 秒间隔 + 串行，不并发 |

细节（页面结构、接口参数、翻页规则、礼貌策略）见 [`crawler/README.md`](crawler/README.md)。

### 数据规模

| 数据集 | 规模 | 文件 |
| --- | --- | --- |
| 教务通知 | 700 条，2023-06 → 2026-11，345 条带附件（共 585 个） | `jwch_notices.csv` |
| 开源之夏 | 102 个项目，全部拿到简述与产出要求 | `ospp_projects.csv` |
| 天气 | 8784 条小时数据 + 366 条日数据 | `openmeteo_2024_*.csv` |
| B-Wiki | 48 个页面的原始 wikitext | `bwiki_raw/` |

## 数据分析

`assignment1_jwch_analysis.ipynb` 是对 700 条通知的完整分析，7 个小节对应题目 7 个问题，
执行后的输出（表格 + 图 + 结论）都在 notebook 里。主要结论：

* **发布主体高度集中**：教学运行 32.7%、实践科 21.3%、质量办 12.1%，前三合计 66.1%；
* **「课程调整」18 条（2.6%）**，全是节假日放假调课、全由教学运行发布，一年 6 次、提前 1–2 周；
* **附件下载量真正的解释变量是「附件要不要动手填」**：计划科 2460、教研教改 2159、
  实践科 2111 明显高于教材建设 746、综合科 650；
  控制住「累计时间」这个混淆因素（下载次数是累计值，2023 年平均 2505、2026 年 759）后排序基本不变；
* **发布节奏跟校历走**：9 月 112 条为绝对高峰，4–6 月与 12 月次之，寒暑假断崖；
  周末仍占 11.7%；
* **标题长度与下载量弱负相关（-0.24），正文长度弱正相关（0.16）**，
  方向相反说明篇幅不是好指标，主题（学籍 4919、竞赛 2560）信号更强。

`assignment3_numpy.py` 除了完成 3.1 / 3.2，还附了一个「广播 vs 纯 Python 双层循环」的基准
（300×300 下 1.9ms vs 26.3ms，约 14 倍）。这里刻意不用「广播 vs 逐行 numpy 运算」，
因为后者反而更慢——原因写在 [`notes.md`](notes.md) 2.2。

`bonus_image.py` 用 `@` 矩阵乘法、元素级运算和切片拼接完成 sepia / 过饱和 / 渐变边框，
全程没有一处遍历像素的 `for`。因为题目指定的随机噪声图三通道相同、过饱和公式在它上面恒等，
额外造了一张「天空 + 太阳 + 草地」的彩色图来展示效果。

## 关于说明真实性

* 爬虫数据是**真实抓取**的，不是造的；`data/*.jsonl` 保留了逐条原始记录（未入库，`.gitignore` 排除）。
* 知乎作业没有产出 CSV：它需要人工扫码登录，cookie 不能提交，也不该由 AI 代劳。
* 开源之夏的申请书 PDF（bonus）需要登录态，未登录会被 401 拦下，脚本会跳过并说明，不伪造。
* 未做的「历年培养方案」在 `crawler/README.md` 末尾写了原因。
