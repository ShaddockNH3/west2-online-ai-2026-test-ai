"""Bonus 基础 7：商品类，含私有属性与 display / income / setdata。"""


class Product:
    """商品：序号、名称、单价、总数量、剩余数量全部私有。"""

    def __init__(self, pid: str, name: str, price: float, total: int, left: int) -> None:
        self.__pid = pid
        self.__name = name
        self.__price = price
        self.__total = total
        self.__left = left

    def display(self) -> None:
        """显示商品信息。"""
        print(
            f"商品 {self.__pid}：{self.__name}，单价 {self.__price} 元，"
            f"总数量 {self.__total}，剩余 {self.__left}"
        )

    def income(self) -> float:
        """计算已售出商品的价值。"""
        return (self.__total - self.__left) * self.__price

    def setdata(self, name: str | None = None, price: float | None = None) -> None:
        """修改商品信息，传 None 表示不改。"""
        if name is not None:
            self.__name = name
        if price is not None:
            self.__price = price


def main() -> None:
    """演示。"""
    apple = Product("P001", "红富士苹果", 5.5, 100, 40)
    apple.display()
    print(f"已售出价值：{apple.income()} 元")

    apple.setdata(name="阿克苏苹果", price=6.0)
    apple.display()
    print(f"调价后已售出价值：{apple.income()} 元")

    # 私有属性无法直接访问：下面这行会报 AttributeError
    # print(apple.__price)


if __name__ == "__main__":
    main()
