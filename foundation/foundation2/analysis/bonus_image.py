"""Bonus：把图像当成数组来操作。

五个步骤都是「纯数组运算」，没有一处 for 循环遍历像素：
  1. 200x300 灰度图 -> stack 成 (200, 300, 3) 的 RGB；
  2. 复古色滤镜：每个像素的 RGB 向量左乘一个 3x3 矩阵（矩阵乘法一次算完整张图）；
  3. 过饱和：按亮度公式做元素级运算；
  4. 左右各加 20px 渐变边框（linspace 生成权重，切片拼起来）；
  5. matplotlib 拼图对比。

用法：
    python bonus_image.py
输出：
    report/image_effects.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPORT_DIR = Path(__file__).resolve().parent / "report"

plt.rcParams["font.sans-serif"] = ["PingFang SC", "Songti SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

SEPIA_MATRIX = np.array(
    [
        [0.393, 0.769, 0.189],
        [0.349, 0.686, 0.168],
        [0.272, 0.534, 0.131],
    ]
)

SATURATION_ALPHA = 1.5
BORDER_WIDTH = 20


def make_images(rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """1. 随机灰度图，再堆成三通道 RGB（三通道数值相同，所以看起来还是灰的）。"""
    grayscale = rng.integers(0, 256, size=(200, 300), dtype=np.uint8)
    color = np.stack([grayscale, grayscale, grayscale], axis=-1)
    return grayscale, color


def make_demo_image() -> np.ndarray:
    """一张「有意义」的彩色测试图，用来展示滤镜的视觉效果。

    题目要求的随机噪声图是三通道相同的灰度，过饱和公式
    C_new = L + alpha*(C-L) 在那种图上恒等（C 就等于 L），改了也看不出来。
    所以额外用纯数组运算造一张有天空、太阳、地面的图，
    顺便也算把「向量化构图」练了一遍。
    """
    height, width = 200, 300
    # x 是 (1, width)，y 是 (height, 1)，两者运算自动广播成 (height, width)
    y = np.linspace(0.0, 1.0, height)[:, None]
    x = np.linspace(0.0, 1.0, width)[None, :]

    # 天空：从左到右变亮的蓝，越靠上越深
    red = 60 + 150 * x - 40 * (1 - y)
    green = 120 + 90 * x - 30 * (1 - y)
    blue = 235 - 90 * y + 0 * x  # 加 0*x 把形状撑开成 (height, width)
    image = np.stack([red, green, blue], axis=-1)

    # 太阳：以 (0.22, 0.28) 为圆心，半径 0.10，边缘用距离做一点柔化
    dist = np.sqrt((x - 0.22) ** 2 + (y - 0.28) ** 2)
    sun_mask = np.clip((0.10 - dist) / 0.02, 0.0, 1.0)[..., None]
    sun_color = np.array([255.0, 214.0, 120.0])
    image = image * (1 - sun_mask) + sun_color * sun_mask

    # 地面：y > 0.72 的部分换成草绿，带一点横向条纹
    ground_mask = (y > 0.72).astype(np.float64)[..., None]  # (h, 1, 1)
    stripes = 0.75 + 0.25 * np.sin(30 * x)  # (1, width)，广播即可
    grass = np.stack([stripes * 60, stripes * 110, stripes * 50], axis=-1)
    image = image * (1 - ground_mask) + grass * ground_mask

    return np.clip(image, 0, 255).astype(np.uint8)


def sepia(color: np.ndarray) -> np.ndarray:
    """2. 复古色：整张图做一次矩阵乘法。

    (200, 300, 3) @ (3, 3) —— 最后两维参与矩阵乘法，
    广播之后等价于对每个像素的 [R, G, B] 各做一次线性变换。
    uint8 不能直接参与浮点乘法，所以先转 float。
    """
    pixels = color.astype(np.float64)
    transformed = pixels @ SEPIA_MATRIX.T  # 每行是一个像素，所以乘矩阵转置
    return np.clip(transformed, 0, 255).astype(np.uint8)


def over_saturate(color: np.ndarray, alpha: float = SATURATION_ALPHA) -> np.ndarray:
    """3. 过饱和：先算亮度 L，再对每个通道做 L + alpha * (C - L)。"""
    pixels = color.astype(np.float64)
    # L 的形状是 (200, 300)，用 [..., None] 扩成 (200, 300, 1) 才能和三通道广播
    luminance = (
        0.299 * pixels[..., 0] + 0.587 * pixels[..., 1] + 0.114 * pixels[..., 2]
    )[..., None]
    enhanced = luminance + alpha * (pixels - luminance)
    return np.clip(enhanced, 0, 255).astype(np.uint8)


def add_gradient_border(color: np.ndarray, width: int = BORDER_WIDTH) -> np.ndarray:
    """4. 左右各加一条渐变边框。

    左边：纯黑 -> 原图像素，权重从 0 线性到 1；
    右边：原图像素 -> 纯白，等价于 原图 + (255 - 原图) * 权重。
    权重形状 (1, width, 1)，正好和 (高度, width, 3) 的切片广播。
    """
    pixels = color.astype(np.float64)
    weights = np.linspace(0.0, 1.0, width)[None, :, None]

    left_edge = pixels[:, :1, :]          # 最左一列 -> (200, 1, 3)
    right_edge = pixels[:, -1:, :]        # 最右一列 -> (200, 1, 3)

    left = left_edge * weights                                  # 黑 -> 左边缘色
    right = right_edge + (255.0 - right_edge) * weights          # 右边缘色 -> 白

    framed = np.concatenate([left, pixels, right], axis=1)
    return np.clip(framed, 0, 255).astype(np.uint8)


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261103)

    grayscale, color = make_images(rng)
    print(f"灰度图 {grayscale.shape} dtype={grayscale.dtype}")
    print(f"RGB 图  {color.shape} dtype={color.dtype}")
    print(f"三通道是否完全一致：{np.array_equal(color[..., 0], color[..., 1]) and np.array_equal(color[..., 1], color[..., 2])}")

    sepia_image = sepia(color)
    print(f"\n复古色：dtype={sepia_image.dtype}，范围 [{sepia_image.min()}, {sepia_image.max()}]")

    saturated = over_saturate(color)
    print(f"过饱和 alpha={SATURATION_ALPHA}：范围 [{saturated.min()}, {saturated.max()}]")

    framed = add_gradient_border(sepia_image)
    print(f"加边框：{color.shape} -> {framed.shape}（左右各 {BORDER_WIDTH}px）")

    # 验证边框确实是从黑渐变到图像、再从图像渐变到白
    left_first_col = framed[:, 0, :].mean()
    left_last_col = framed[:, BORDER_WIDTH - 1, :].mean()
    right_last_col = framed[:, -1, :].mean()
    print(f"边框校验：最左列均值 {left_first_col:.1f}（应接近 0），"
          f"左边框内沿 {left_last_col:.1f}，最右列均值 {right_last_col:.1f}（应接近 255）")

    fig, axes = plt.subplots(2, 4, figsize=(12, 5.6))
    fig.suptitle("NumPy 图像操作：矩阵乘法、元素级运算、切片拼接", fontsize=15)

    # 第一行：题目要求的随机噪声图
    axes[0, 0].imshow(grayscale, cmap="gray", vmin=0, vmax=255)
    axes[0, 0].set_title("必做 · 原始灰度图")
    axes[0, 1].imshow(sepia_image)
    axes[0, 1].set_title("必做 · 复古色")
    axes[0, 2].imshow(saturated)
    axes[0, 2].set_title("必做 · 过饱和（三通道本就相同）")
    axes[0, 3].imshow(framed)
    axes[0, 3].set_title("必做 · 渐变边框")

    # 第二行：彩色测试图，看得出滤镜的实际效果
    demo = make_demo_image()
    axes[1, 0].imshow(demo)
    axes[1, 0].set_title("测试图 · 原始")
    axes[1, 1].imshow(sepia(demo))
    axes[1, 1].set_title("测试图 · 复古色")
    axes[1, 2].imshow(over_saturate(demo))
    axes[1, 2].set_title("测试图 · 过饱和 alpha=1.5")
    axes[1, 3].imshow(add_gradient_border(demo))
    axes[1, 3].set_title("测试图 · 渐变边框")

    for ax in axes.ravel():
        ax.axis("off")

    fig.tight_layout()
    output = REPORT_DIR / "image_effects.png"
    fig.savefig(output, dpi=100)
    print(f"\n图已保存：{output}")


if __name__ == "__main__":
    main()
