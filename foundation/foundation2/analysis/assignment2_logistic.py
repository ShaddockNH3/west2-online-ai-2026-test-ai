"""数据分析作业 2：用 matplotlib 画 Logistic 函数。

    f(x) = L / (1 + e^(-k(x - x0)))

三个参数各管一件事：
  * L  —— 曲线的上限（饱和值），只影响高度，不影响形状；
  * k  —— 陡峭程度，k 越大越像阶跃函数，k 越小越平缓；
  * x0 —— 中点位置（f(x0) = L/2），只左右平移。

用法：
    python assignment2_logistic.py
输出：
    report/logistic.png
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


def logistic(x: np.ndarray, L: float = 1.0, k: float = 1.0, x0: float = 0.0) -> np.ndarray:
    """Logistic 函数。整个函数体只有一行，向量化不用写循环。"""
    return L / (1.0 + np.exp(-k * (x - x0)))


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    x = np.linspace(-10, 10, 400)

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle("Logistic 函数：f(x) = L / (1 + e^(-k(x-x0)))", fontsize=15)

    # ---------- 标准曲线 ----------
    ax = axes[0, 0]
    y = logistic(x, L=1, k=1, x0=0)
    ax.plot(x, y, color="#c0392b", linewidth=2.2, label="L=1, k=1, x0=0")
    ax.axhline(1.0, color="#7f8c8d", linestyle="--", linewidth=1, label="上限 L=1")
    ax.axhline(0.5, color="#95a5a6", linestyle=":", linewidth=1)
    ax.axvline(0, color="#95a5a6", linestyle=":", linewidth=1)
    ax.scatter([0], [0.5], color="#2c3e50", zorder=5)
    ax.annotate("中点 (x0, L/2) = (0, 0.5)", xy=(0, 0.5), xytext=(1.2, 0.32),
                arrowprops={"arrowstyle": "->", "color": "#2c3e50"}, fontsize=10)
    ax.set_title("标准 Logistic 曲线")
    ax.set_xlabel("x")
    ax.set_ylabel("f(x)")
    ax.set_ylim(-0.05, 1.15)
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=9)

    # ---------- 改变 L ----------
    ax = axes[0, 1]
    for L, color in zip([0.5, 1.0, 2.0], ["#2980b9", "#c0392b", "#27ae60"]):
        ax.plot(x, logistic(x, L=L), color=color, linewidth=2, label=f"L={L}")
    ax.set_title("改变 L：只拉伸高度，形状不变")
    ax.set_xlabel("x")
    ax.set_ylabel("f(x)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)

    # ---------- 改变 k ----------
    ax = axes[1, 0]
    for k, color in zip([0.3, 1.0, 3.0], ["#2980b9", "#c0392b", "#8e44ad"]):
        ax.plot(x, logistic(x, k=k), color=color, linewidth=2, label=f"k={k}")
    ax.set_title("改变 k：k 越大越陡（过渡带越窄）")
    ax.set_xlabel("x")
    ax.set_ylabel("f(x)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    ax.annotate("k=3 近似阶跃", xy=(0.35, 0.75), xytext=(2.0, 0.62), fontsize=9,
                arrowprops={"arrowstyle": "->", "color": "#8e44ad"})

    # ---------- 改变 x0 ----------
    ax = axes[1, 1]
    for x0, color in zip([-3.0, 0.0, 3.0], ["#2980b9", "#c0392b", "#e67e22"]):
        ax.plot(x, logistic(x, x0=x0), color=color, linewidth=2, label=f"x0={x0}")
        ax.axvline(x0, color=color, linestyle=":", linewidth=1, alpha=0.6)
    ax.set_title("改变 x0：左右平移，中点跟着走")
    ax.set_xlabel("x")
    ax.set_ylabel("f(x)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)

    fig.tight_layout()
    output = REPORT_DIR / "logistic.png"
    fig.savefig(output, dpi=150)
    print(f"图已保存：{output}")

    # 顺手把关键数值打印出来，方便核对
    print("\n标准曲线采样：")
    for value in (-4, -2, -1, 0, 1, 2, 4):
        print(f"  f({value:>2}) = {float(logistic(np.array([value]))[0]):.4f}")
    print(f"\n两条渐近线：x -> -inf 时趋近 0，x -> +inf 时趋近 L")
    print(f"导数在 x0 处最大，最大值 = k*L/4 = {1 * 1 / 4:.3f}")


if __name__ == "__main__":
    main()
