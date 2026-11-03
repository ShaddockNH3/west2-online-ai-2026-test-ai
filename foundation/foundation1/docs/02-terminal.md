# 终端的基本使用

> 这篇文档记录两件事：在 Foundation 1 的作业里，我在终端上真正遇到的问题；
> 以及编辑器右上角那个三角形按钮，按下去到底发生了什么。

## 一、终端、Shell 与提示符

打开终端时看到的黑框，准确说是「终端模拟器」，它只负责显示字符、接收键盘输入。
真正解释你敲的命令的是 shell（macOS 默认是 zsh，Linux 上常见 bash）。

提示符里藏着三条信息：

```text
(.venv) shaddocknh3@mac west2-online-ai-2026-test-ai %
```

- `(.venv)`：当前激活的虚拟环境，没有括号说明用的是全局 Python；
- `shaddocknh3@mac`：当前用户和主机名；
- `west2-online-ai-2026-test-ai`：当前工作目录的目录名，不代表路径。

第三点最容易误判。提示符只显示最后一级目录名，两个不同路径下的同名目录看起来一模一样。
所以真正需要确认位置时，我用 `pwd` 而不是看提示符。

## 二、这次作业里真正用到的命令

命令很多，但作业里反复出现的其实就这些：

| 命令 | 作用 | 这次的具体用法 |
| --- | --- | --- |
| `pwd` | 打印当前绝对路径 | 确认自己在仓库根目录还是作业子目录 |
| `cd` | 切换目录 | `cd foundation/foundation1/assignment1-nabiya` |
| `ls -la` | 列目录内容（含隐藏文件） | 确认 `.venv`、`assets` 是否生成 |
| `mkdir -p` | 建目录，已存在不报错 | 建 `assets` 子目录 |
| `cp` / `mv` / `rm` | 复制 / 移动 / 删除 | 复制考核给的框架代码，删掉临时文件 |
| `python xxx.py` | 用当前解释器执行脚本 | 跑 `check_my_code.py`、`start_the_battle.py` |
| `which python` | 查命令来自哪个路径 | 验证虚拟环境是否真的生效 |
| `source .venv/bin/activate` | 激活虚拟环境 | 每次新开终端都要做一次 |
| `git status` / `add` / `commit` / `push` | 版本控制 | 每份作业单独提交 |
| `npx markdownlint-cli2` | 检查 Markdown 规范 | 提交前跑一遍 |
| `basedpyright` | 静态类型检查 | 确认 type hint 能过 Pylance 那一关 |

再补三个「让终端变强」的语法：

```zsh
# 管道：把前一个命令的输出交给后一个
ls foundation/foundation1 | grep assignment

# 重定向：把输出写进文件
python check_my_code.py > result.txt 2>&1

# 顺序执行与条件执行
cd assignment1-nabiya && python check_my_code.py    # 前者成功才执行后者
python check_my_code.py; echo "退出码：$?"          # 无论成败都执行后面
```

`&&` 和 `;` 的区别值得记住：`&&` 是「前一条成功才继续」，`;` 是「不管成败都继续」。
写 `cd 某目录 && python xxx.py` 时，如果目录不存在，后半句会被跳过，反而比 `;` 安全。

## 三、作业里碰到的终端问题

### 3.1 在错误的目录下运行脚本

第一次跑娜比娅作业时，我在仓库根目录敲了：

```text
$ python foundation/foundation1/assignment1-nabiya/check_my_code.py
ModuleNotFoundError: No module named 'longmen_vs_nabiya'
```

原因不是文件缺失，而是**解释器搜索模块的起点**。

`python path/to/script.py` 会把 `path/to/` 加进 `sys.path[0]`，理论上能导入同目录的模块。
但这次报错说明我在跑一个「被复制过的脚本」时路径并不一致。
解决办法很简单：

```zsh
cd foundation/foundation1/assignment1-nabiya
python check_my_code.py
```

顺带记一个相关结论：`python -m package.module` 与 `python module.py` 的 `sys.path` 起点不同。
前者是当前工作目录，后者是脚本所在目录。这也是为什么有些项目里「直接跑」会找不到包，而加 `-m` 就能跑。

### 3.2 交互式程序用管道喂输入，报 EOFError

测「校园 if 恋」时，我不想每次手动敲选项，于是这样跑：

```zsh
printf '1\n1\n2\n3\n4\n' | python main.py
```

如果输入给少了，`input()` 读到空就会抛 `EOFError`。
这不是程序写错了，而是「没有人在键盘前」这一事实被暴露了出来。

处理方式有两种：

1. 把输入给够（管道里多准备几行）；
2. 在代码里捕获 `EOFError`，当作「玩家退出」处理。

我选了第二种，因为玩家按 `Ctrl + D` 时同样会触发它，接住之后能干净地退出，而不是甩一堆红字。

### 3.3 激活虚拟环境这件事只对当前窗口有效

我在一个终端里 `source .venv/bin/activate`，换了窗口再跑，`which python` 又指回系统 Python。
虚拟环境的激活是通过修改当前 shell 的环境变量实现的，**新开的窗口不会继承**。

判断有没有生效，不看提示符，看路径：

```zsh
$ which python
/Users/.../west2-online-ai-2026-test-ai/.venv/bin/python
```

只要路径里带 `.venv` 就对了。这个习惯帮我避免了一次「包装到全局去了」的事故。

### 3.4 通配符被 shell 提前展开

跑 Markdown 检查时，我一开始这样写：

```zsh
# 错误写法：通配符被 shell 自己展开，npx 收到的是一串具体文件名
npx markdownlint-cli2 foundation/**/*.md

# 正确写法：加引号，交给工具自己递归
npx markdownlint-cli2 "foundation/**/*.md"
```

结果 npx 收到的是已经被 zsh 展开的一串具体文件名，`**` 的递归语义没了，只扫到一层。
加上引号交给工具自己展开才对：

```zsh
npx markdownlint-cli2 "foundation/**/*.md" "README.md"
```

结论：**通配符要么自己展开（不加引号），要么完全交给工具（加引号）**，不要各管一半。

### 3.5 中文与宽字符把对齐搞乱

终端里用 `tabulate` 或手写空格拼表格时，中文占两个字符宽度、英文占一个，`len()` 却都算 1。
结果表格在对齐上惨不忍睹。真正要处理时得按「显示宽度」算（例如 `east_asian_width`），
或者干脆用固定格式输出，不依赖对齐。

### 3.6 程序停不下来

- `Ctrl + C`：发 SIGINT，中断当前前台进程。跑 `start_the_battle.py` 时想提前结束就用它。
- `Ctrl + Z`：挂起到后台（不是结束），用 `fg` 回到前台、`jobs` 查看后台任务。
- 卡在 `input()` 里等待输入时，上面两个键都能救你。

我一开始习惯直接关窗口，但那会留下半截没结束的进程，日志也一起没了。

## 四、右上角那个三角形按钮是什么

### 4.1 它做的是一次「组装」

在 VS Code 里点右上角的 ▷，看到的结果是下方弹出一个终端，里面自动出现一行命令并执行。

那一行命令不是凭空来的，它是三样东西拼起来的：

```text
<当前打开的文件的绝对路径>  ← 由「活动编辑器」决定
<选中的 Python 解释器>      ← 由右下角状态栏决定，可以是 .venv 里的
<工作目录>                  ← 默认是工作区根目录
```

等价于手写：

```zsh
cd /Users/.../west2-online-ai-2026-test-ai
/Users/.../west2-online-ai-2026-test-ai/.venv/bin/python foundation/foundation1/assignment2-campus-if-love/main.py
```

所以它省掉的是「切目录 + 敲解释器路径 + 敲文件名」这三步，本质上没有魔法。
PyCharm 的同位置按钮也是同样的道理，只是它默认用「运行配置（Run Configuration）」里的解释器和工作目录。

### 4.2 为什么会出现「点按钮报错，手敲没事」

最常见的三个差异：

1. **工作目录不同。** 按钮用工作区根目录，程序里写 `open("data.txt")` 就会去根目录找；手敲时你在子目录里，反而找得到。可靠写法是用脚本自身位置定位：`Path(__file__).parent / "data.txt"`。
2. **解释器不同。** 状态栏没选 `.venv`，按钮就用全局 Python，于是「明明装了却导入失败」。
3. **当前活动文件不对。** 它运行的是「你最后点开的那个文件」，不是你正在看的那个标签页的邻居。

### 4.3 运行、调试、launch.json

- ▷（或 `Ctrl + F5`）：直接运行，不带断点；
- 虫子图标（或 `F5`）：带调试器运行，能打断点、看变量、单步；
- `.vscode/launch.json`：写死「运行哪个文件、用什么参数、在哪个目录、用什么环境变量」。

一个能让「按钮」和「手敲」行为一致的配置：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: 当前文件",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "cwd": "${fileDirname}",
      "console": "integratedTerminal",
      "justMyCode": true
    }
  ]
}
```

关键在 `"cwd": "${fileDirname}"`：让工作目录跟着脚本走，`open("相对路径")` 的行为就稳定了。

### 4.4 我什么时候不用按钮

- 需要喂标准输入（`printf ... | python main.py`）时，按钮给不了管道；
- 需要批量跑多个脚本、对比输出时，终端里一个 `for` 循环更快；
- 需要确认「换一台机器也能跑」时，我会刻意用终端原样敲一遍，避免依赖编辑器帮我拼好的路径。

结论：按钮是「快速试一下」的入口，终端是「知道自己在干什么」的地方。
真正让我理解程序的，是那条被手敲出来的命令。

## 五、几个保命习惯

1. 不确定在哪 → `pwd`；
2. 不确定用哪个 Python → `which python`；
3. 删除之前 → 先 `ls` 看一眼展开结果，再删；
4. 长命令先 `echo` 一遍，确认变量展开无误再执行；
5. 改代码前 `git status`，出问题才有退路。
