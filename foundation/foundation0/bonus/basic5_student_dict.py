"""Bonus 基础 5：字典存学号-姓名，删除尾号为偶数的元素后输出。"""


def build_students() -> dict[str, str]:
    """造一批示例数据。"""
    return {
        "2026001": "张三",
        "2026002": "李四",
        "2026003": "王五",
        "2026004": "赵六",
        "2026005": "孙七",
    }


def drop_even_tail(students: dict[str, str]) -> dict[str, str]:
    """删除学号尾号为偶数（含 0）的元素，返回新字典。"""
    return {sid: name for sid, name in students.items() if int(sid[-1]) % 2 == 1}


def main() -> None:
    """演示。"""
    students = build_students()
    print("删除前：", students)
    students = drop_even_tail(students)
    print("删除后：", students)


if __name__ == "__main__":
    main()
