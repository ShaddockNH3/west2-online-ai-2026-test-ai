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
│   └── assignment4-oi/              # 作业 4：洛谷与 AtCoder 五题
└── foundation1/                     # 语法基础与简单面向对象
    ├── docs/                        # 文档 1：Python 语法笔记 / 文档 2：终端使用
    ├── assignment1-nabiya/          # 作业 1：娜比娅偷吃事件
    ├── assignment2-campus-if-love/  # 作业 2：校园 if 恋
    └── assignment3-pokemon/         # 作业 3：宝可梦对战
```

## 完成情况

### Foundation 0

| 作业 | 内容 | 状态 |
| --- | --- | --- |
| 作业 1 | 环境搭建与基本工具的使用 | 已完成 |
| 作业 2 | Git 基础使用与第一份 Markdown | 已完成 |
| 作业 3 | Hello World | 已完成 |
| 作业 4 | OI 五题 | 已完成 |
| Bonus | Python 小程序 13 题 | 未做（可选） |

### Foundation 1

| 作业 | 内容 | 状态 |
| --- | --- | --- |
| 文档 1 | Python 语法与编程技巧笔记 | 已完成 |
| 文档 2 | 终端的基本使用 | 已完成 |
| 作业 1 | 娜比娅偷吃事件（必做） | 已完成 |
| 作业 2 | 校园 if 恋 | 已完成 |
| 作业 3 | 宝可梦对战 | 已完成 |
| 作业 4 | 好玩的东西 | 未做（选做，本轮不做） |
| Bonus | CS61A | 未做（可选） |

> Foundation 1 的作业 2 - 4 要求任选两个完成，本仓库选择作业 2 与作业 3。

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
