"""Bonus 进阶 4：MyZoo，练习魔法方法。"""


class MyZoo:
    """动物园：动物名称为 key、数量为 value。

    - 实例化时打印 "My Zoo!"
    - 相等比较只看动物种类，不看数量
    - len() 返回动物总数
    """

    def __init__(self, animals: dict[str, int] | None = None) -> None:
        print("My Zoo!")
        self.animals = dict(animals) if animals else {}

    def __repr__(self) -> str:
        items = ", ".join(f"{name}x{count}" for name, count in self.animals.items())
        return f"MyZoo({items})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MyZoo):
            return NotImplemented
        return set(self.animals) == set(other.animals)

    def __len__(self) -> int:
        return sum(self.animals.values())


def main() -> None:
    """按题目示例演示。"""
    myzoooo1 = MyZoo({"pig": 1})
    myzoooo2 = MyZoo({"pig": 5})
    print(myzoooo1 == myzoooo2)
    print(len(MyZoo({"pig": 5, "dog": 6})))


if __name__ == "__main__":
    main()
