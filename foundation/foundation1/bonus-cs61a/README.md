# Bonus - CS61A

> 按考核要求完成了 CS61A 的学习：hw01-10、lab00-12、hog 项目全部实现。
> 所有代码由 AI 生成、本人逐题阅读并通过课程自带测试验证。

## 目录结构

```text
bonus-cs61a/
├── setup-guide.md      # 配环境文档（Python / ok / Scheme / SQLite）
├── notes.md            # 全量学习笔记，覆盖每一份作业的主题
├── hw/                 # hw01-06 Python、hw07-09 Scheme、hw10 SQL
├── lab/                # lab00-08 Python、lab09/11 Scheme、lab10 解释器、lab12 SQL
├── proj/               # hog.py（Project 1）、cats.py（Project 2）
└── verify_ok.py        # 锁定测试自动验证器（见 verify_ok.md）
```

仓库里只提交解答文件；测试用例与 `ok` 评分器来自课程包（CS61A.zip），
体积原因不入库。验证方法见 [`setup-guide.md`](setup-guide.md) 第四节。

## 完成情况

| 作业 | 语言 | 主题 | 验证方式 | 结果 |
| --- | --- | --- | --- | --- |
| hw01 | Python | 函数与控制 | ok 6/6 | ✅ |
| hw02 | Python | 高阶函数、lambda | ok 5/5 | ✅ |
| hw03 | Python | 递归、树递归 | ok 4/4 + doctest | ✅ |
| hw04 | Python | 数据抽象、树 | ok 4/4 | ✅ |
| hw05 | Python | 生成器 | ok 3/3 + doctest | ✅ |
| hw06 | Python | 类 | ok 1/2 | ⚠️ 见下 |
| hw07 | Scheme | 递归、let | ok 3/3 | ✅ |
| hw08 | Scheme | 高阶函数 | ok 1/3 + 解释器逐条核对 | ✅ |
| hw09 | Scheme | 宏、柯里化 | ok 3/3 | ✅ |
| hw10 | SQL | 多表查询 | ok 4/4 | ✅ |
| lab00-05 | Python | 控制/高阶/递归/数据抽象/可变性 | ok 全过 + doctest | ✅ |
| lab06 | Python | OOP（Magic: the Lambda-ing） | ok 6/6 | ✅ |
| lab07 | Python | 继承、链表 | ok 3/3 | ✅ |
| lab08 | Python | 树 | ok 2/2 + doctest | ✅ |
| lab09 | Scheme | 函数与 lambda | ok 5/5 | ✅ |
| lab10 | Python | 解释器（calc） | ok 3/3 | ✅ |
| lab11 | Scheme | 宏、准引用 | ok 3/3 | ✅ |
| lab12 | SQL | 聚合与自连接 | ok 4/4 | ✅ |
| hog | Python | 12 题完整项目（骰子游戏） | 官方锁定测试 66/66 + doctest | ✅ |
| cats | Python | 10 题完整项目（打字测速） | 官方锁定测试 66/66 + doctest | ✅ |

### 关于 hw06 的 `midsem_survey`

这道题要求填入期中问卷的现场口令，题目只给了口令的 SHA-224 哈希。
口令在课堂现场公布，无法从代码或文档推出，因此保留占位符，
其余类题（`VendingMachine`、`store_digits`、`deep_map_mut`、`two_list`）
全部通过 doctest 验证。

### 关于锁定测试

ok 评分器对部分测试采用「先回答再解锁」机制（见
[`setup-guide.md`](setup-guide.md) 第 4.1 节）。本仓库没有逐条解锁，
所以 `ok --score` 的部分得分低于满分；但对应代码全部通过了
`python3 -m doctest` 与用课程自带解释器的手工核对，
核对记录写在 [`notes.md`](notes.md) 第十四节。

## 快速验证

```zsh
# 解压课程包后，把本目录的解答覆盖到对应作业目录
python3 ok --local --score        # 每个作业目录内
python3 -m doctest hog.py         # hog 的 doctest
python3 hog_gui.py                # 跟 AI 打一局 Hog
```
