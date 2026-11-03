"""角色类：好感度、对话与送礼。"""

from __future__ import annotations

from story import DIALOGUES, GIFT_REPLIES, GIFT_TABLE
from ui import ask_choice

ENDING_THRESHOLD = 100


class Character:
    """一位可攻略角色。

    角色只负责「自己的状态」：好感度、聊过几次、收过什么礼物。
    至于什么时候该聊天、什么时候该换场景，那是 `game.Game` 的事。
    """

    def __init__(self, name: str, role: str, affinity: int = 0) -> None:
        self.name = name
        self.role = role
        self.affinity = affinity
        self.talk_count = 0
        self.gift_count = 0

    # ---------- 对外接口 ----------

    def talk(self) -> None:
        """进行一轮对话：出题、二选一、结算好感度。"""
        dialogues = DIALOGUES[self.name]
        # 聊完最后一轮之后重复最后一轮，避免越界。
        index = min(self.talk_count, len(dialogues) - 1)
        dialogue = dialogues[index]

        print(f"\n{self.name}：{dialogue['text']}")
        options = dialogue["options"]
        for order, option in enumerate(options, start=1):
            print(f"  {order}. {option['text']}")

        choice = ask_choice("请选择：", len(options))
        if choice is None:
            return

        chosen = options[choice - 1]
        print(f"你：{chosen['text']}")
        print(chosen["reply"])

        self.talk_count += 1
        self.change_affinity(chosen["delta"])

    def give_gift(self, gift: str) -> None:
        """送出一份礼物，按礼物表结算好感度。"""
        delta = self._gift_delta(gift)
        print(f"\n你送给 {self.name} 一份「{gift}」。")
        print(self._gift_reply(delta))

        self.gift_count += 1
        self.change_affinity(delta)

    def change_affinity(self, value: int) -> None:
        """修改好感度，并保证不会掉到 0 以下。"""
        self.affinity = max(0, self.affinity + value)
        sign = "+" if value >= 0 else ""
        print(f"{self.name} 的好感度 {sign}{value} → 当前好感度：{self.affinity}")

    def check_ending(self) -> bool:
        """好感度达到阈值就进入结局线。"""
        return self.affinity >= ENDING_THRESHOLD

    def status_line(self) -> str:
        """一行状态描述，供「查看好感度」使用。"""
        rest = max(0, ENDING_THRESHOLD - self.affinity)
        return (
            f"{self.name}（{self.role}）好感度 {self.affinity} / {ENDING_THRESHOLD}，"
            f"距离结局还差 {rest}；已聊天 {self.talk_count} 次，收礼 {self.gift_count} 次。"
        )

    # ---------- 内部实现 ----------

    def _gift_delta(self, gift: str) -> int:
        table = GIFT_TABLE.get(gift, {})
        if self.name in table:
            return table[self.name]
        return table.get("*", 0)

    def _gift_reply(self, delta: int) -> str:
        replies = GIFT_REPLIES.get(self.name, {})
        if delta > 0:
            return replies.get("like", f"{self.name}：谢谢你。")
        if delta < 0:
            return replies.get("dislike", f"{self.name}：……")
        return replies.get("neutral", f"{self.name}：嗯，谢谢。")
