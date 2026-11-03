"""校园 if 恋：程序入口。

运行方式：

    python main.py
"""

from __future__ import annotations

from game import Game


def main() -> None:
    """创建一局游戏并开始。"""
    Game().run()


if __name__ == "__main__":
    main()
