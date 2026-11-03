# west2-online-ai-2026-test-ai

如你所见，这是一个尝试全作业都通过 AI 完成的仓库。

## 说明

仓库里的内容由 AI 生成，本人逐行阅读、运行并验证过，每一份代码都能在本机跑通，
关键的取舍与踩坑记录写在各作业的 `README.md` 或笔记里。

考核原文见 [learn-AI](https://github.com/west2-online/learn-AI) 的 `docs/work-2026`。

## 目录

```text
foundation/
├── foundation0/                     # 环境搭建 / Git 与 Markdown / Hello World / OI
│   ├── assignment2-markdown/        # 作业 2：crazy-day.md 与 Git 操作截图
│   ├── assignment3-hello-world/     # 作业 3：Hello World
│   ├── assignment4-oi/              # 作业 4：洛谷与 AtCoder 五题
│   └── bonus/                       # Bonus：13 个 Python 小程序
├── foundation1/                     # 语法基础与简单面向对象
│   ├── docs/                        # 文档 1：Python 语法笔记 / 文档 2：终端使用
│   ├── assignment1-nabiya/          # 作业 1：娜比娅偷吃事件
│   ├── assignment2-campus-if-love/  # 作业 2：校园 if 恋（含存读档 Bonus）
│   ├── assignment3-pokemon/         # 作业 3：宝可梦对战
│   ├── assignment4-sanguosha/       # 作业 4：三国杀 demo
│   └── bonus-cs61a/                 # Bonus：CS61A 全部 hw/lab/hog + 笔记 + 配环境文档
└── foundation2/                     # 网络爬虫与数据分析
    ├── crawler/                     # 4 个爬虫作业 + B-Wiki Bonus
    ├── analysis/                    # Pandas / Matplotlib / NumPy 作业 + 图像 Bonus
    └── notes.md                     # 14 条踩坑记录
```

## 完成情况

### Foundation 0

| 作业 | 内容 | 状态 |
| --- | --- | --- |
| 作业 1 | 环境搭建与基本工具的使用 | 已完成 |
| 作业 2 | Git 基础使用与第一份 Markdown | 已完成 |
| 作业 3 | Hello World | 已完成 |
| 作业 4 | OI 五题 | 已完成 |
| Bonus | Python 小程序 13 题 | 已完成 |

### Foundation 1

| 作业 | 内容 | 状态 |
| --- | --- | --- |
| 文档 1 | Python 语法与编程技巧笔记 | 已完成 |
| 文档 2 | 终端的基本使用 | 已完成 |
| 作业 1 | 娜比娅偷吃事件（必做） | 已完成 |
| 作业 2 | 校园 if 恋（含存读档 Bonus） | 已完成 |
| 作业 3 | 宝可梦对战 | 已完成 |
| 作业 4 | 三国杀 demo（16 武将） | 已完成 |
| Bonus | CS61A（hw01-10 / lab00-12 / hog） | 已完成 |

> Foundation 1 的作业 2 - 4 要求任选两个完成，本仓库三个都做了。

### Foundation 2

| 作业 | 内容 | 状态 |
| --- | --- | --- |
| 爬虫 1 | 福大教务通知 500+ 条 | 已完成（700 条，含附件下载量） |
| 爬虫 2 | 知乎话题（浏览器操控） | 脚本完成，需扫码登录 |
| 爬虫 3 | 开源之夏项目列表（接口） | 已完成（102 个项目） |
| 爬虫 4 | Open-Meteo 单次请求 | 已完成（8784 + 366 行） |
| 数据分析 1 | 教务处通知分析（Pandas） | 已完成（notebook + 6 图） |
| 数据分析 2 | Logistic 函数（Matplotlib） | 已完成 |
| 数据分析 3 | 矩阵与广播（NumPy） | 已完成 |
| 爬虫 Bonus | B-Wiki 方案舰娘 | 已完成（48 页） |
| 分析 Bonus | 图像数组操作 | 已完成 |
| 爬虫 Bonus | 历年培养方案 | 未做 |

> Foundation 2 的爬虫 Bonus 有两个，本轮做了 B-Wiki，「历年培养方案」留待单独一轮。

## 快速运行

```zsh
# 环境
uv venv --python 3.12.3 && source .venv/bin/activate

# Foundation 0
python foundation/foundation0/assignment3-hello-world/hello_world.py
python foundation/foundation0/assignment4-oi/p1001_a_plus_b.py

# Foundation 1
cd foundation/foundation1/assignment1-nabiya && python check_my_code.py
cd foundation/foundation1/assignment2-campus-if-love && python main.py
cd foundation/foundation1/assignment3-pokemon && python main.py

# Foundation 2
cd foundation/foundation2/crawler
python assignment1_jwch.py        # 教务通知（约 8 分钟）
python assignment3_ospp.py        # 开源之夏
python assignment4_openmeteo.py   # 天气
python bonus_bwiki.py             # B-Wiki
cd ../analysis
python assignment2_logistic.py && python assignment3_numpy.py && python bonus_image.py
```

静态检查：

```zsh
basedpyright                                    # 类型检查，等价于 Pylance
npx markdownlint-cli2 "**/*.md"                 # Markdown 规范
npx autocorrect-node --lint "**/*.md"           # 中英文空格（苹果规范）
```

## 运行环境

- macOS 26.7.1（Apple Silicon）
- Python 3.12.3（`uv` 管理）
- 代码统一带 type hint，通过 Pylance 的 basic 类型检查
- Markdown 通过 markdownlint 检查，并按苹果文档规范排版
