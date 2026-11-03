"""数据分析作业 3：NumPy 基本使用 + 广播机制。

3.1 数组创建、切片、布尔索引、in-place 运算、argmax 定位
3.2 广播算距离矩阵、axis 聚合、复合条件查询

用法：
    python assignment3_numpy.py
"""

from __future__ import annotations

import time

import numpy as np

np.set_printoptions(precision=2, suppress=True, linewidth=120)


def part_one() -> np.ndarray:
    print("=" * 62)
    print("作业 3.1  numpy 的基本使用")
    print("=" * 62)

    # 1. 创建 0-99 的 (10, 10) 矩阵
    data_matrix = np.arange(100).reshape(10, 10)
    print("\n[1] 原始矩阵（arange + reshape）：")
    print(data_matrix)

    # 2. 中心 4x4 子矩阵：10 行取第 3-6 行，同理取列
    center = data_matrix[3:7, 3:7]
    print("\n[2] 中心 4x4 子矩阵 data_matrix[3:7, 3:7]：")
    print(center)

    # 3. 布尔索引把大于 75 的元素置 0
    mask = data_matrix > 75
    print(f"\n[3] 大于 75 的元素共 {mask.sum()} 个，位置：{np.argwhere(mask).tolist()[:6]} ...")
    data_matrix[mask] = 0

    # 4. in-place 缩放 0.8
    #    关键点：原始数组是 int64，直接 *= 0.8 会抛
    #    UFuncTypeError（不能把 float 结果写回 int 数组），
    #    所以必须先转成浮点。转完再做原地乘。
    print(f"\n[4] 缩放前 dtype = {data_matrix.dtype}")
    data_matrix = data_matrix.astype(np.float64)
    data_matrix *= 0.8
    print(f"    缩放后 dtype = {data_matrix.dtype}，最大值 = {data_matrix.max():.2f}")
    print(data_matrix)

    # 5. 最大值及其行列索引
    max_value = data_matrix.max()
    flat_index = data_matrix.argmax()
    row, col = np.unravel_index(flat_index, data_matrix.shape)
    print(f"\n[5] 最大值 {max_value:.2f}，一维下标 {flat_index}，二维位置 ({row}, {col})")
    return data_matrix


def part_two() -> None:
    print("\n" + "=" * 62)
    print("作业 3.2  广播机制与向量化距离计算")
    print("=" * 62)

    rng = np.random.default_rng(20261103)  # 固定种子，结果可复现
    # 1. 两组随机点，取值 [0, 100)
    points_a = rng.integers(0, 100, size=(5, 2))
    points_b = rng.integers(0, 100, size=(8, 2))
    print(f"\n[1] points_A {points_a.shape}：\n{points_a}")
    print(f"    points_B {points_b.shape}：\n{points_b}")

    # 2. 广播算 (5, 8) 距离矩阵
    #    points_A[:, None, :] -> (5, 1, 2)
    #    points_B[None, :, :] -> (1, 8, 2)
    #    相减自动广播成 (5, 8, 2)，再对最后一维平方和开根
    diff = points_a[:, None, :] - points_b[None, :, :]
    distance_matrix = np.sqrt((diff**2).sum(axis=-1))
    print(f"\n[2] 距离矩阵 shape = {distance_matrix.shape}")
    print(distance_matrix)
    print(f"    校验：手算 A[0] 到 B[0] 的距离 = "
          f"{np.linalg.norm(points_a[0] - points_b[0]):.4f}，矩阵里是 {distance_matrix[0, 0]:.4f}")

    # 3. 每个 A 点到 B 的最近距离
    nearest = distance_matrix.min(axis=1)
    nearest_index = distance_matrix.argmin(axis=1)
    print(f"\n[3] 每个 A 点的最近距离（axis=1 聚合）：{nearest.round(2)}")
    for index, (dist, target) in enumerate(zip(nearest, nearest_index)):
        print(f"    A[{index}] 最近的是 B[{target}]，距离 {dist:.2f}")

    # 4. 与至少一个 A 点距离小于 20 的 B 点索引
    close_mask = (distance_matrix < 20).any(axis=0)
    close_indices = np.where(close_mask)[0]
    print(f"\n[4] 与至少一个 A 点相距 < 20 的 B 点索引：{close_indices.tolist()}")
    print(f"    掩码（按 B 排列）：{close_mask.astype(int)}")

    # 5. 向量化 vs 纯 Python 双层循环（体会「为什么不要写 for」）
    #
    #    注意这里对比的是「纯 Python 循环」，不是「用 for 遍历 numpy 行」。
    #    后者其实也是在 numpy 里做向量运算，未必慢；真正慢的是逐元素取标量。
    #    另外广播会生成 (n, m, 2) 的临时数组，规模很大时内存也吃紧，
    #    工程上还可以用 |a|² + |b|² - 2ab 的代数展开（见 notes.md）。
    size = 300
    small_a = rng.random((size, 2))
    small_b = rng.random((size, 2))

    start = time.perf_counter()
    broadcast = np.sqrt(((small_a[:, None, :] - small_b[None, :, :]) ** 2).sum(axis=-1))
    vector_time = time.perf_counter() - start

    start = time.perf_counter()
    loop_result = np.empty((size, size))
    for i in range(size):
        for j in range(size):
            dx = float(small_a[i, 0]) - float(small_b[j, 0])
            dy = float(small_a[i, 1]) - float(small_b[j, 1])
            loop_result[i, j] = (dx * dx + dy * dy) ** 0.5
    loop_time = time.perf_counter() - start

    print(f"\n[5] {size}x{size} 距离矩阵（同一份数据、同一个公式）：")
    print(f"    广播          {vector_time * 1000:8.1f} ms")
    print(f"    纯 Python 双层 {loop_time * 1000:8.1f} ms")
    print(f"    加速比 {loop_time / vector_time:.0f}x，最大误差 {np.abs(broadcast - loop_result).max():.2e}")


def main() -> None:
    part_one()
    part_two()


if __name__ == "__main__":
    main()
