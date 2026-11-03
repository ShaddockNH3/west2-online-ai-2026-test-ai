"""Bonus 基础 3：判断并替换子串 "ol"，最后倒序输出。"""


def process(text: str) -> str:
    """把所有 "ol" 替换为 "fzu" 后整体倒序。"""
    replaced = text.replace("ol", "fzu")
    return replaced[::-1]


def main() -> None:
    """从标准输入读一行字符串。"""
    text = input("请输入一个字符串：")
    if "ol" in text:
        print("包含 ol，替换后倒序：", process(text))
    else:
        print("不包含 ol，原样倒序：", process(text))


if __name__ == "__main__":
    main()
