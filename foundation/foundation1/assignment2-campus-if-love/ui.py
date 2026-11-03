"""终端交互的小工具：把「读一个合法选项」这件事收在一处。"""

from __future__ import annotations


def ask_choice(prompt: str, count: int) -> int | None:
    """读取 1 到 count 之间的选择。

    - 输入非法时重新提问，不打断游戏；
    - 读到 EOF（玩家按 Ctrl + D，或用管道喂完了输入）时返回 None，
      让上层把它当作「退出游戏」，而不是抛一堆红字。
    """
    while True:
        try:
            raw = input(prompt).strip()
        except EOFError:
            print("\n（输入结束，游戏退出。）")
            return None

        if raw.isdigit() and 1 <= int(raw) <= count:
            return int(raw)

        print(f"请输入 1 到 {count} 之间的数字。")


def show_lines(lines: list[str]) -> None:
    """按顺序打印一段旁白。"""
    for line in lines:
        print(line)
