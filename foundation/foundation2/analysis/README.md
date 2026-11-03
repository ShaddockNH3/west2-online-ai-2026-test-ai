# Foundation 2 · 数据分析

三个作业 + 一个图像 Bonus。数据来自 `../crawler/` 的产出。

```text
analysis/
├── assignment1_jwch_analysis.ipynb   # 作业 1：教务处通知分析（Pandas + Matplotlib）
├── assignment2_logistic.py           # 作业 2：Logistic 函数绘图
├── assignment3_numpy.py              # 作业 3：NumPy 基本使用 + 广播
├── bonus_image.py                    # Bonus：图像数组操作
└── report/                            # 全部图表
```

## 运行

```zsh
# 作业 1 需要先有爬虫产出
cd ../crawler && python assignment1_jwch.py

# 执行 notebook 并保留输出
cd ../analysis
jupyter nbconvert --to notebook --execute --inplace assignment1_jwch_analysis.ipynb

# 其余三个直接跑
python assignment2_logistic.py
python assignment3_numpy.py
python bonus_image.py
```

## 作业 1 · 教务处通知分析（Pandas）

`assignment1_jwch_analysis.ipynb`，按题目 7 个问题组织：

| 题目 | notebook 小节 | 做法 |
| --- | --- | --- |
| 通知人都有谁、占比 | §2 | `value_counts` + 横向条形图 |
| 课程调整类通知 | §3 | 标题关键词筛选，单独导出 CSV |
| 附件下载次数与通知人的关系 | §4 | 附件明细表 → `groupby` 聚合 → 条形图 + 箱线图 |
| 发布高峰期 | §5 | 按月份 / 星期聚合 |
| 自由探索 | §6 | 标题长度 vs 下载量（相关系数）、主题关键词 vs 下载量 |
| 可视化 | §3 / §4 / §5 / §6 | 共 6 张图，全部存 `report/` |

用到的 Pandas 功能：`read_csv` / `to_csv`、`to_datetime` 与 `.dt` 访问器、
`str.contains`、`map`、`groupby().agg()`、`value_counts`、布尔索引、`corr`。

产出图表：

| 文件 | 内容 |
| --- | --- |
| `report/01_notifier_top10.png` | 通知人 Top 10 |
| `report/02_course_adjust_by_month.png` | 课程调整类通知的月度分布 |
| `report/03_attachment_downloads.png` | 附件下载量：均值对比 + 分布 |
| `report/04_publish_time.png` | 月度 / 星期分布 |
| `report/05_title_length_vs_download.png` | 标题长度与下载量散点 |
| `report/06_topic_vs_download.png` | 主题关键词与平均下载量 |

## 作业 2 · Logistic 函数（Matplotlib）

`report/logistic.png` 是 2×2 子图：

* 标准曲线（L=1, k=1, x0=0），标出中点、上限、渐近线；
* 改变 L：曲线高度变了，形状不变；
* 改变 k：k 越大越像阶跃函数；
* 改变 x0：整体左右平移。

导数在 `x0` 处取最大值 `kL/4`，这一点在控制台也打印出来了——
它就是深度学习里 sigmoid 饱和导致梯度消失的根源。

## 作业 3 · 矩阵操作

`assignment3_numpy.py`，两个小题都在里面，跑一遍看输出即可。

**3.1**：`arange(100).reshape(10,10)` → 中心 4×4（`[3:7, 3:7]`）
→ 布尔索引把 `>75` 置 0 → `astype(float)` 后原地 `*= 0.8`
→ `argmax` + `unravel_index` 定位最大值。

「缩放前应该做什么」的答案就是那次 `astype`：整数数组存不下 0.8 的结果，
numpy 会直接抛 `UFuncTypeError`（见 `../notes.md` 2.1）。

**3.2**：`(5,2)` 与 `(8,2)` 通过 `[:, None, :]` / `[None, :, :]` 广播成 `(5,8,2)`，
平方和开根得到 `(5,8)` 距离矩阵；`min(axis=1)` 取最近距离；
`(distance_matrix < 20).any(axis=0)` + `np.where` 找复合条件下的索引。

最后附了一个「广播 vs 纯 Python 双层循环」的基准（300×300 下约 14 倍加速），
用来说明为什么不该写 for——注意对比对象是纯 Python 循环，不是 numpy 逐行运算。

## Bonus · 图像数组操作

`bonus_image.py` → `report/image_effects.png`，2 行 4 列：

* 第一行是题目要求的随机噪声图（原始 / 复古 / 过饱和 / 渐变边框）；
* 第二行是额外造的彩色测试图（同样四种处理），因为噪声图三通道相同，
  过饱和公式在它上面是恒等变换，看不出效果。

关键实现：

```python
# 复古色：一次矩阵乘法代替逐像素循环
sepia = np.clip(color.astype(float) @ SEPIA_MATRIX.T, 0, 255).astype(np.uint8)

# 过饱和：亮度 L 扩一维后与三通道广播
luminance = (0.299 * p[..., 0] + 0.587 * p[..., 1] + 0.114 * p[..., 2])[..., None]
enhanced = luminance + alpha * (p - luminance)

# 渐变边框：权重 (1, width, 1) 与左右边缘列 (h, 1, 3) 广播
weights = np.linspace(0, 1, width)[None, :, None]
left = pixels[:, :1, :] * weights
right = pixels[:, -1:, :] + (255.0 - pixels[:, -1:, :]) * weights
```

全程没有一处 `for` 遍历像素。
