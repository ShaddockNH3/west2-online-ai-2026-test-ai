# Foundation 2 踩坑记录

按题目顺序记下真正卡住过的地方。有些是环境问题，有些是自己写错，都留着。

## 一、爬虫

### 1.1 教务处的页码是倒着编的

第 1 页是 `/jxtz.htm`，第 2 页却是 `/jxtz/215.htm`，最后一页是 `/jxtz/1.htm`。
规律是「第 n 页 = `217 - n`」，一共 216 页、每页 20 条。

一开始按「`jxtz/{n}.htm` 从 1 开始爬」写，结果从最老的通知开始爬，
而列表页还有个 `尾页 -> jxtz/1.htm` 的链接，两下一对照才发现页码是反的。

### 1.2 忘了 `page += 1`，爬虫原地打转

改完页码映射之后跑批量，日志刷了满屏同一个「第 1 页 20 条」，进度条却一动不动——
`while` 循环里所有条目都 `continue`（因为已经在 jsonl 里），而循环变量没自增。

这个 bug 很隐蔽：**断点续爬恰好把它掩盖了**。第一次跑（有新条目）看起来正常，
第二次跑才暴露成死循环。修法是把 `page += 1` 放到 `for` 循环外面，
并且加一条防御：如果这一页所有条目都命中 `done`，说明翻页逻辑有问题，直接抛错而不是继续转。

### 1.3 附件下载次数是 JS 渲染的

详情页里长这样：

<!-- autocorrect-disable -->

```html
附件【<a href="...wbfileid=18563163">附件1：拍照地点示意图.pdf</a>】已下载
<span id="nattach18563163"><script>getClickTimes(18563163,1744984858,"wbnewsfile","attach")</script></span>次
```

<!-- autocorrect-enable -->

`requests` 拿到的 HTML 里只有这段 `<script>`，没有数字。按题目提示不能上 Selenium，
于是顺着 `getClickTimes` 找到 `/system/resource/js/ajax.js`，里面写死了接口：

```js
var url = '/system/resource/code/news/click/clicktimes.jsp';
url += "?wbnewsid="+newsid+"&owner="+owner+"&type="+type+"&randomid="+randomid;
```

返回 `{"wbshowtimes": 86, ...}`，`wbshowtimes` 就是下载次数。

**教训**：JS 渲染的数据不一定非要浏览器。先看页面里的 `<script>` 调了什么函数、
函数定义在哪个 js 文件里，八成能找到它请求的接口。

### 1.4 附件那段 HTML 在正文容器外面

`div.v_news_content` 只包正文，附件列表在它之后的另一个 `<ul>` 里。
所以不能「取正文容器再在里面找附件」，得对整页 HTML 做正则。
正则是：

```python
r'附件【\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>\s*】.*?id="nattach(\d+)"'
```

`.*?` 用非贪婪，否则多个附件之间的内容会被吞掉。

### 1.5 逐条落盘要 `fsync`，不是 `flush`

`flush()` 只是把 Python 缓冲推给操作系统，进程被 `kill -9` 或断电时，
数据可能还在内核缓冲里没落盘。真正「写一条算一条」需要 `os.fsync(fd)`。
代价是每条都要等磁盘，速度会慢一点点——在几百条的量级完全可接受。

### 1.6 知乎：没登录就是没登录

Playwright 打开话题页，`requests` 时代的 403 确实没了，但会弹出登录框，
`.ContentItem` 一个都取不到。这里没有「绕过」的余地，脚本直接抛错并提示：

```text
被登录墙拦住了，先用 --login 登录并把 cookie 保存下来。
```

`--login` 会打开有头浏览器让人扫码，检测到 `z_c0` 这个 cookie 就把
`storage_state` 存下来。仓库里不包含这个文件，`.gitignore` 里也排除了。

### 1.7 开源之夏：参数名试错

`getProList` 的 `pageNum/pageSize` 一次就试对了，`getProDetail` 却一直返回
`410 项目不存在`。把常见字段名全试了一遍：

| 参数 | 结果 |
| --- | --- |
| `proId` / `projectId` / `id` / `code` / `programCode` / `projectCode` | 410 |
| `programId` | 200 |

而列表里那个字段叫 `proId`，值是 `30`。所以是「字段名 A，传参叫 B」，纯靠试。
如果能直接看前端 bundle 里调用处的代码会更快，但 minify 之后变量名被压成 `Bne(`，
调用点不好定位，试参反而是最短路径。

### 1.8 MediaWiki 的 `maxlag` 不是装饰

B-Wiki 的 API 支持 `maxlag=5`：服务器副本延迟超过 5 秒时，请求会被拒绝并返回
`{"error": {"code": "maxlag"}}`，同时可能带 `Retry-After`。
按文档应该等一下再试，而不是狂刷。实测 48 个页面里没触发过一次，
但代码里还是实现了重试（最多 3 次，每次等 5 秒或 `Retry-After`）。

另外题目特意说了不能并发。这看起来慢，其实是对的：48 页 × 1 秒 ≈ 1 分钟，
并发省下的那 50 秒不值得换来一个被封的 IP。

## 二、数据分析

### 2.1 `int64` 数组不能原地乘 0.8

```python
data_matrix = np.arange(100).reshape(10, 10)
data_matrix *= 0.8   # UFuncTypeError: Cannot cast ufunc 'multiply' output
                     # from dtype('float64') to dtype('int64')
```

题目问「进行这一步之前应该对矩阵做什么操作」，答案就是这个：
**先转成浮点**（`astype(np.float64)`）。整数数组没有地方存 0.8 这种结果，
numpy 宁可直接报错也不做静默截断（老版本会截断，更坑）。

### 2.2 广播不一定比 `for` 快——要和「纯 Python 循环」比

第一版基准测试写的是「广播 vs 逐行 `numpy` 运算」：

```text
广播      31.5 ms
for 循环  24.1 ms     # 每一行还是在 numpy 里做向量运算
```

广播反而更慢，因为 `(n, 1, 2) - (1, m, 2)` 会生成一个 `(n, m, 2)` 的临时数组，
内存带宽全花在这上面；而逐行写法每次只处理 `(m, 2)`。

**所以对比对象要选对**：向量化的价值是相对「纯 Python 逐元素循环」而言的。
换成 300×300 的双层 `for` 之后：

```text
广播            1.9 ms
纯 Python 双层  26.3 ms
加速比 14x，最大误差 2.22e-16
```

工程上还有一招：把 `|a-b|²` 展开成 `|a|² + |b|² - 2ab`，用一次矩阵乘法代替广播，
就不需要 `(n, m, 2)` 的临时数组了（大矩阵时能省一大截内存）。

### 2.3 随机噪声图看不出饱和度变化

题目要求用 `np.random.randint(0, 256, size=(200, 300))` 造灰度图，再 stack 成三通道。
这种图 R=G=B，而饱和度公式是 `C_new = L + α(C - L)`，其中
`L = 0.299R + 0.587G + 0.114B = R`（因为三通道相同），于是 `C - L = 0`，
**结果恒等于原图**。公式没错，是输入退化。

为了能看出滤镜效果，额外用纯数组运算造了一张「天空 + 太阳 + 草地」的彩色图，
两张图都跑一遍：噪声图用来对数值，彩色图用来看效果。

### 2.4 中文字体和负号

matplotlib 默认字体没有中文，标题会变成方块，负号会变成方框。
两行配置解决：

```python
plt.rcParams["font.sans-serif"] = ["PingFang SC", "Songti SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
```

macOS 上 `PingFang SC` 一定有；留几个 fallback 是为了在 Linux/Windows 上也能跑。

### 2.5 灰度图 `imshow` 要指定 `vmin/vmax`

`imshow(gray, cmap="gray")` 默认会按数据的最小/最大值拉伸对比度。
我们的灰度是 0–255，最好显式写 `vmin=0, vmax=255`，
否则跟别的图并排时会显得「更亮」或「更暗」，误以为处理过。

### 2.6 Notebook 里找不到 CSV

notebook 的工作目录取决于从哪里启动（Jupyter、nbconvert、IDE 都不一样）。
所以路径不能写死成 `../crawler/data/...`，而是从 `Path.cwd()` 往上逐级找：

```python
for base in [cwd, *cwd.parents]:
    for name in ["crawler/data/jwch_notices.csv", "foundation2/crawler/data/jwch_notices.csv", ...]:
        if (base / name).exists():
            return base / name
```

### 2.7 数据还没爬完就跑分析

中途用 8 条样本试跑 notebook，`课程调整` 一条都没命中，
`course_df.groupby("月份").size().plot(kind="bar")` 在**空 Series** 上直接
`IndexError: index 0 is out of bounds for axis 0 with size 0`。

pandas 的 `plot` 对空数据不会给友好提示。修法是作图前判空，
空的时候打印一句「样本不足，跳过作图」，而不是让整个 notebook 中断。
这也提醒一件事：**分析脚本要对「没数据」有防御**，因为数据是外部依赖。
