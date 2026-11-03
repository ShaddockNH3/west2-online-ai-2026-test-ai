# Foundation 0 - 环境搭建与基础工具

本目录记录 Foundation 0 的四份作业。作业 1 是环境搭建，本身没有代码产物，因此以本文档作为交付记录，其余作业分别放在对应子目录中。

| 作业 | 内容 | 交付物 |
| --- | --- | --- |
| 作业 1 | 环境搭建与基本工具的使用 | 本文档 + [`assignment1-environment/assets/environment.png`](assignment1-environment/assets/environment.png) |
| 作业 2 | Git 基础使用与第一份 Markdown | [`assignment2-markdown/crazy-day.md`](assignment2-markdown/crazy-day.md) |
| 作业 3 | Hello World | [`assignment3-hello-world/hello_world.py`](assignment3-hello-world/hello_world.py) |
| 作业 4 | OI 五题 | [`assignment4-oi/`](assignment4-oi/) |

## 作业 1 - 环境搭建与基本工具的使用

### 机器与系统

- 机型：MacBook（Apple Silicon，arm64）
- 系统：macOS 26.7.1（Build 25G241）
- 终端：iTerm2 + zsh

### Python 环境

按照考核指南的建议，固定使用 Python 3.12.3，并通过 `uv` 管理版本与虚拟环境，避免不同项目的依赖互相污染。

```zsh
# 安装并固定 3.12.3
uv python install 3.12.3

# 在项目目录中创建虚拟环境
uv venv --python 3.12.3

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖（以 requests 为例）
uv pip install requests
```

`uv venv` 创建的环境默认就在项目根目录的 `.venv/` 下，VS Code 打开项目后会在右下角提示选择解释器，选中 `.venv/bin/python` 即可，后续终端、调试、Pylance 都会使用同一个解释器。

选择 `uv` 而不是 `conda` 的原因：

1. 安装依赖时并发下载，比 `pip` 快很多；
2. 不需要 `conda activate` 那套环境变量改写，对 shell 的侵入性小；
3. `uv python install` 可以直接把指定小版本的 Python 装下来，不会动系统自带的 3.9。

### 编辑器

使用基于 VS Code 内核的编辑器（本机为 CodeBuddy CN，插件与配置方式同 VS Code），安装了以下插件：

- Python（自带 Pylance，负责类型检查与补全）
- Black Formatter（保存时自动格式化）
- Ruff（额外的 lint）
- Markdownlint（写 Markdown 时实时提示规范问题）

保存时自动格式化的设置在 `settings.json` 中：

```json
{
  "editor.formatOnSave": true,
  "python.analysis.typeCheckingMode": "basic"
}
```

### 其他工具

- 浏览器：Chrome，开发时主要用它的 DevTools 和扩展生态。
- 截图：macOS 自带 `Command + Shift + 4`，截窗口用 `Command + Shift + 4` 再按空格。
- Git：2.50.1（Apple Git-155），提交身份已在 `git config` 中配置。

### 环境验证

在终端中依次执行以下命令，输出见截图（[environment.png](assignment1-environment/assets/environment.png)）：

```zsh
sw_vers
python3 --version
uv --version
git --version
```

截图对应的原始文本同样保留在 [`assignment1-environment/assets/environment.txt`](assignment1-environment/assets/environment.txt)，方便核对。
