"""Bonus 进阶 3：列表推导式生成 5x10 的全 1 矩阵并转置。"""


def make_matrix() -> list[list[int]]:
    """5 行 10 列，值全为 1。"""
    return [[1 for _ in range(10)] for _ in range(5)]


def transpose(matrix: list[list[int]]) -> list[list[int]]:
    """用列表推导式转置。"""
    return [[row[col] for row in matrix] for col in range(len(matrix[0]))]


def main() -> None:
    """演示。"""
    matrix = make_matrix()
    print("原矩阵 5x10：")
    for row in matrix:
        print(row)

    transposed = transpose(matrix)
    print("转置后 10x5：")
    for row in transposed:
        print(row)


if __name__ == "__main__":
    main()
