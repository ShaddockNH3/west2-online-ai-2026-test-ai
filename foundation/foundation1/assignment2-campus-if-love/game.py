"""游戏流程：三个决定点、角色线主循环、结局，以及存档 / 读档 / 即时存档。

存档设计（对应 Bonus 要求的三种存档）：

- **存档**：写入 ``saves/save.json``，由玩家在菜单里手动触发；
- **读档**：从 ``saves/save.json`` 恢复全部状态；
- **即时存档**：写入 ``saves/autosave.json``，每次操作（聊天、送礼、换场景）
  之后自动写入，专门辟出一个存储空间，永远保存「最近一次操作后」的状态。
"""

from __future__ import annotations

import json
from pathlib import Path

from character import Character
from story import ENDINGS, GIFTS, NOBODY_CHOSEN, OPENING, SCENES
from ui import ask_choice, ask_yes_no, show_lines

SCENE_ORDER: tuple[str, ...] = ("学姐", "小白", "姐姐")

SAVE_DIR = Path(__file__).resolve().parent / "saves"
MANUAL_SAVE = SAVE_DIR / "save.json"
AUTOSAVE = SAVE_DIR / "autosave.json"


class Game:
    """把角色、场景和玩家操作串成一个流程，并负责存档。"""

    def __init__(self) -> None:
        self.characters: dict[str, Character] = {
            "学姐": Character("学姐", "社团里的艺术少女"),
            "小白": Character("小白", "课堂上的元气同学"),
            "姐姐": Character("姐姐", "咖啡店里的研究生"),
        }
        self.target: Character | None = None
        self.aborted = False
        # stage: opening 还在选场景；story 已进入角色线；ended 已触发结局
        self.stage = "opening"
        self.scene_index = 0

    # ---------- 存档 ----------

    def snapshot(self) -> dict[str, object]:
        """把当前状态拍成一份可序列化的快照。"""
        target = self.target
        return {
            "stage": self.stage,
            "scene_index": self.scene_index,
            "target": target.name if target else None,
            "affinity": target.affinity if target else 0,
            "talk_count": target.talk_count if target else 0,
            "gift_count": target.gift_count if target else 0,
        }

    def restore(self, data: dict[str, object]) -> None:
        """用快照覆盖当前状态。"""
        self.stage = str(data["stage"])
        self.scene_index = int(data["scene_index"])  # type: ignore[arg-type]
        name = data["target"]
        if name:
            self.target = self.characters[str(name)]
            self.target.affinity = int(data["affinity"])  # type: ignore[arg-type]
            self.target.talk_count = int(data["talk_count"])  # type: ignore[arg-type]
            self.target.gift_count = int(data["gift_count"])  # type: ignore[arg-type]
        else:
            self.target = None

    def save_to(self, path: Path) -> None:
        """把快照写入指定文件。"""
        if not SAVE_DIR.exists():
            SAVE_DIR.mkdir()
        path.write_text(
            json.dumps(self.snapshot(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"（已写入 {path.name}）")

    def load_from(self, path: Path) -> bool:
        """从指定文件读档，文件不存在时返回 False。"""
        if not path.exists():
            print("没有找到存档文件。")
            return False
        try:
            self.restore(json.loads(path.read_text(encoding="utf-8")))
        except (KeyError, ValueError, json.JSONDecodeError) as error:
            print(f"存档文件损坏，无法读取：{error}")
            return False
        print(f"已读取 {path.name}。")
        return True

    def autosave(self) -> None:
        """即时存档：每次操作后自动调用。"""
        self.save_to(AUTOSAVE)

    # ---------- 主流程 ----------

    def run(self) -> None:
        """游戏入口：开场 → 读档询问 → 三个决定点 → 角色线。"""
        show_lines(OPENING)

        if AUTOSAVE.exists() and ask_yes_no("检测到即时存档，要继续上次的进度吗？"):
            self.load_from(AUTOSAVE)

        # 已经选定角色（无论是本局刚选的还是读档恢复的）直接进角色线
        if self.target is not None:
            self._story_loop()
            return

        for index, name in enumerate(SCENE_ORDER):
            if index < self.scene_index:
                continue
            if self._play_scene(index, name):
                break
            if self.aborted:
                return

        if self.target is None:
            print(f"\n{NOBODY_CHOSEN}")
            return

        self._story_loop()

    # ---------- 决定点 ----------

    def _play_scene(self, index: int, name: str) -> bool:
        """播放一个场景，返回是否进入了该角色的线。"""
        scene = SCENES[name]
        print(f"\n【{scene['title']}】")
        show_lines(scene["lines"])

        choice = ask_choice(scene["prompt"], 2)
        if choice is None:
            self.aborted = True
            return False

        self.scene_index = index + 1
        if choice == 1:
            show_lines(scene["yes"])
            self.target = self.characters[name]
            self.stage = "story"
            print(f"你进入了【{name}线】！")
            self.autosave()
            return True

        show_lines(scene["no"])
        self.autosave()
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
            print("4. 存档")
            print("5. 读档")
            print("6. 离开（退出游戏）")

            choice = ask_choice("请输入选项：", 6)
            if choice is None or choice == 6:
                print("你选择离开，游戏结束。")
                self.autosave()
                return

            if choice == 1:
                target.talk()
            elif choice == 2:
                self._gift_menu(target)
            elif choice == 3:
                print(target.status_line())
            elif choice == 4:
                self.save_to(MANUAL_SAVE)
                continue
            else:
                if self.load_from(MANUAL_SAVE):
                    target = self.target
                    if target is None:
                        return
                    print(target.status_line())
                continue

            # 即时存档：任何一次聊天 / 送礼 / 查看之后都自动落盘
            self.autosave()

            if target.check_ending():
                self._show_ending(target)
                self.stage = "ended"
                self.autosave()
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
