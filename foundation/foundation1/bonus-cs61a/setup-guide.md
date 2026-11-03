# CS61A 配环境指南

> 这份文档专门记录把 CS61A 的作业环境在本机跑起来的完整过程，
> 包括 Python、ok 自动评分器、Scheme 解释器、SQLite shell 四块，
> 以及每一步会撞到的坑。

## 一、需要的工具

| 工具 | 用途 | 本机版本 |
| --- | --- | --- |
| Python 3.9+ | 跑作业与 ok 评分器 | 3.12.3（uv 管理） |
| 终端 | 所有命令都在这里敲 | zsh |
| VS Code | 编辑代码，装 Python 插件 | 基于 VS Code 内核 |
| 课程包 | 包含 hw/lab/proj 的 zip 与测试 | CS61A.zip（sp24 版） |

不需要单独安装 Scheme 或 SQLite：课程包里自带了用 Python 写的
Scheme 解释器和 SQLite shell，直接用 `python3` 跑即可。

## 二、Python 与虚拟环境

CS61A 是纯标准库项目，依赖极少，但仍然建议放进虚拟环境，
避免以后装 AI 框架时把全局 Python 搅乱：

```zsh
uv venv --python 3.12.3
source .venv/bin/activate
```

验证：

```zsh
python --version
# Python 3.12.3
```

> 坑：不要用 Python 2 时代的 `python` 命令；macOS 自带的
> `/usr/bin/python3` 版本较旧，建议统一用 uv 装的 3.12。

## 三、解压课程包

课程包内是多层 zip：外层 zip 里每个作业又是一个 zip。

```zsh
unzip CS61A.zip -d cs61a
cd cs61a
for z in hw/*.zip lab/*.zip proj/hog.zip; do
    unzip -qo "$z" -d work/
done
```

`-o` 是覆盖已有文件，重复解压不会卡在交互询问上。
解压完 `work/` 下应该有 `hw01` 到 `hw10`、`lab00` 到 `lab12`、`hog`。

## 四、ok 自动评分器

每个作业目录里都带一个 `ok` 可执行脚本和 `tests/` 目录。常用命令：

```zsh
# 跑当前作业的全部测试并显示得分
python3 ok --local --score

# 只跑某一题
python3 ok -q 01 --local

# 跑某个测试但带着失败栈启动交互解释器，方便调试
python3 ok -q 01 --local -i

# 解锁测试（需要回答题目，答对才解锁，见下文）
python3 ok -q 02 -u
```

`--local` 很重要：不加它会尝试把成绩备份到 Berkeley 的服务器，
本地跑不通网络时会报 `Cannot backup when running ok with --local`。

### 4.1 关于「锁定测试」

CS61A 的一部分测试是**锁定的**（`tests/*.py` 里 `'locked': True`）。
`ok --score` 时锁定测试直接记 0 分，需要先用 `ok -u` 回答问题解锁。

解锁是交互式的：它会展示一段代码，让你**预测输出**，答案哈希比对通过才算解锁。
这是课程设计的一部分，目的在于逼你先理解题意再写代码。

实操上有两点：

1. 答错会重问，`Ctrl + C` 可以跳过当前题目；
2. 如果只是想验证自己写对没有，先把 doctest 全过一遍，
   再回来逐题解锁，命中率会高很多。

本仓库的代码用 `python3 -m doctest` 全量验证过；
锁定测试未逐条解锁，得分表见 `README.md` 的说明。

### 4.2 常见报错

| 报错 | 原因 | 处理 |
| --- | --- | --- |
| `SyntaxError: invalid syntax` | 文件里还有 `_____` 占位符没替换 | 搜 `____` 和 `YOUR CODE HERE` |
| `AttributeError: 'function' object has no attribute ...` | 忘了 `return`，函数返回了 `None` | 检查每个分支都有返回值 |
| `Cannot backup when running ok with --local` | 正常现象，本地模式不备份 | 忽略 |
| `There are still locked tests!` | 有锁定测试没解锁 | `ok -u` 或先看 doctest |
| `TimeoutException` | 测试里有无限循环 | 检查递归终止条件 |

## 五、Scheme 作业（hw07-09、lab09、lab11）

Scheme 作业的交付物是 `.scm` 文件，测试靠包内自带的解释器跑：

```zsh
cd hw07
python3 ok --local --score          # 走 ok，会调用内置解释器

# 想手动玩一玩 REPL：
python3 scheme                      # 进入交互环境
```

在 REPL 里加载自己的文件调试：

```scheme
scm> (load "hw07.scm")
scm> (pow 2 10)
1024
```

也可以用管道喂一批表达式，适合批量验证：

```zsh
printf '(load "hw07.scm")\n(pow 2 10)\n' | python3 scheme
```

几个容易踩的点：

1. **`zero?` 和 `even?` 是内置的**，不要自己再定义一遍；
2. **`define` 里嵌套函数时**，缩进不重要，括号配对才重要，编辑器装个 rainbow括号插件会舒服很多；
3. **宏题（lab11 的 `define-macro`）**生成的表达式是「代码即数据」，
   调试时直接把它打印出来看展开结果，比在脑子里模拟靠谱得多。

## 六、SQL 作业（hw10、lab12）

SQL 作业用包内的 `sqlite_shell.py` 跑：

```zsh
cd hw10
python3 ok --local --score

# 手动交互：
python3 sqlite_shell.py
sqlite> .read hw10.sql
sqlite> SELECT * FROM size_of_dogs;
```

注意事项：

1. `.read` 前面的点号不能少，这是 sqlite 的元命令，不是 SQL；
2. 字符串拼接用 `||`，数字参与拼接时套一层括号：`'一共 ' || (1 + 2) || ' 个'`；
3. hw10 的 `low_variance` 需要 `GROUP BY` + `HAVING`，
   写错聚合范围时不会报错，只会输出空表，要对着期望输出逐行核对。

## 七、Hog 项目

Hog 是第一个大项目，测试最多，建议流程：

```zsh
cd hog
python3 ok -q 01 --local        # 逐题推进
python3 hog_gui.py              # 全写完后可以跟 AI 打一局
python3 ok --local --score      # 汇总
```

调试技巧：

1. `make_test_dice(4, 2, 5, 1)` 会按顺序循环出点数，用来构造确定性测试；
2. 策略函数在 `play` 里每回合只允许调用一次，
   如果你在策略里 print，会发现它被调用的次数和回合数一致；
3. `run_experiments()`（`python3 hog.py -r`）会模拟大量对局统计胜率，
   跑一次要几分钟，调参时可以先把 `samples_count` 调小。

## 八、VS Code 侧的配置

1. Python 插件选中 `.venv` 解释器；
2. 装 Markdownlint 插件，写笔记时实时提示规范问题；
3. Scheme 没有官方插件，装一个带括号高亮的主题即可，
   再配合 `python3 scheme` 的 REPL，基本够用；
4. SQL 文件可以关联到 SQLite 插件获得关键字高亮。

## 九、总结

整套 CS61A 环境的依赖其实只有「Python 本体 + 课程包」，
真正的门槛在三个地方：

1. 记得加 `--local`，别让 ok 去连服务器；
2. 理解锁定测试的机制，别把 0 分当成代码写错了；
3. Scheme 与 SQL 都是用 Python 实现的解释器跑的，报错信息是 Python 的 traceback，
   看到报错先看最内层那行，再回到 `.scm` / `.sql` 里找对应表达式。
