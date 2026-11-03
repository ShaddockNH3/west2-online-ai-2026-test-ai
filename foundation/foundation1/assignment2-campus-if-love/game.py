"""游戏流程：三个决定点、角色线主循环、结局。"""

from __future__ import annotations

from character import Character
from story import ENDINGS, GIFTS, NOBODY_CHOSEN, OPENING, SCENES
from ui import ask_choice, show_lines

SCENE_ORDER: tuple[str, ...] = ("学姐", "小白", "姐姐")


class Game:
    """把角色、场景和玩家操作串成一个流程。"""

    def __init__(self) -> None:
        self.characters: dict[str, Character] = {
            "学姐": Character("学姐", "社团里的艺术少女"),
            "小白": Character("小白", "课堂上的元气同学"),
            "姐姐": Character("姐姐", "咖啡店里的研究生"),
        }
        self.target: Character | None = None
        self.aborted = False

    def run(self) -> None:
        """游戏入口：开场 → 三个决定点 → 角色线。"""
        show_lines(OPENING)

        for name in SCENE_ORDER:
            if self._play_scene(name):
                break
            if self.aborted:
                return

        if self.target is None:
            print(f"\n{NOBODY_CHOSEN}")
            return

        self._story_loop()

    # ---------- 决定点 ----------

    def _play_scene(self, name: str) -> bool:
        """播放一个场景，返回是否进入了该角色的线。"""
        scene = SCENES[name]
        print(f"\n【{scene['title']}】")
        show_lines(scene["lines"])

        choice = ask_choice(scene["prompt"], 2)
        if choice is None:
            self.aborted = True
            return False

        if choice == 1:
            show_lines(scene["yes"])
            self.target = self.characters[name]
            print(f"你进入了【{name}线】！")
            return True

        show_lines(scene["no"])
        return False

    # ---------- 角色线 ----------

    def _story_loop(self) -> None:
        target = self.target
        if target is None:
            return

        while True:
            print("\n你要做什么？")
            print("1. 和她聊天")
            print("2. 送她礼物")
            print("3. 查看好感度")
            print("4. 离开（退出游戏）")

            choice = ask_choice("请输入选项：", 4)
            if choice is None or choice == 4:
                print("你选择离开，游戏结束。")
                return

            if choice == 1:
                target.talk()
            elif choice == 2:
                self._gift_menu(target)
            else:
                print(target.status_line())

            if target.check_ending():
                self._show_ending(target)
                return

    def _gift_menu(self, target: Character) -> None:
        print("\n你要送什么？")
        for order, gift in enumerate(GIFTS, start=1):
            print(f"  {order}. {gift}")
        cancel = len(GIFTS) + 1
        print(f"  {cancel}. 算了，什么都不送")

        choice = ask_choice("请输入选项：", cancel)
        if choice is None or choice == cancel:
            return

        target.give_gift(GIFTS[choice - 1])

    def _show_ending(self, target: Character) -> None:
        print(f"\n恭喜！你和 {target.name} 的故事进入了结局线。")
        print(ENDINGS.get(target.name, ""))
