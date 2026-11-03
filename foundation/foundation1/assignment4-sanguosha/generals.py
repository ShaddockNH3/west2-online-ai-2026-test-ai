"""十六名武将：四大阵营各四名。

标准包里群雄只有华佗、吕布、貂蝉三人，第四位补了风包的张角，
（雷击做了大幅简化），README 里有说明。

每个武将的技能以名字列表描述，具体逻辑在 `game.py` 里按名字分发。
"""

from __future__ import annotations

from dataclasses import dataclass

WEI = "魏"
SHU = "蜀"
WU = "吴"
QUN = "群"

KINGDOMS: tuple[str, ...] = (WEI, SHU, WU, QUN)


@dataclass(frozen=True)
class General:
    """一名武将：阵营、体力上限、性别、技能列表。"""

    name: str
    kingdom: str
    hp: int
    male: bool
    skills: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.name}（{self.kingdom}，{self.hp} 体力）"


GENERALS: dict[str, General] = {
    general.name: general
    for general in (
        # ---------- 魏 ----------
        General("曹操", WEI, 4, True, ("奸雄",)),
        General("司马懿", WEI, 3, True, ("反馈",)),
        General("夏侯惇", WEI, 4, True, ("刚烈",)),
        General("张辽", WEI, 3, True, ("突袭",)),
        # ---------- 蜀 ----------
        General("刘备", SHU, 4, True, ("仁德",)),
        General("关羽", SHU, 4, True, ("武圣",)),
        General("张飞", SHU, 4, True, ("咆哮",)),
        General("赵云", SHU, 4, True, ("龙胆",)),
        # ---------- 吴 ----------
        General("孙权", WU, 4, True, ("制衡",)),
        General("甘宁", WU, 4, True, ("奇袭",)),
        General("吕蒙", WU, 4, True, ("克己",)),
        General("黄盖", WU, 4, True, ("苦肉",)),
        # ---------- 群 ----------
        General("华佗", QUN, 3, True, ("急救", "青囊")),
        General("吕布", QUN, 5, True, ("无双",)),
        General("貂蝉", QUN, 3, False, ("离间", "闭月")),
        General("张角", QUN, 3, True, ("雷击",)),
    )
}

# 技能说明（用于人类玩家的技能菜单与 README）。
SKILL_HELP: dict[str, str] = {
    "奸雄": "受到伤害后，可以获得造成伤害的牌",
    "反馈": "受到伤害后，获得伤害来源的一张随机手牌",
    "刚烈": "受到伤害后，50% 概率令来源弃一张手牌或失去 1 点体力",
    "突袭": "摸牌阶段可以改为获得至多两名其他角色的各一张随机手牌",
    "仁德": "出牌阶段可以把任意张手牌交给其他角色，累计给出两张以上回复 1 点体力",
    "武圣": "红色手牌可以当杀使用或打出",
    "咆哮": "出牌阶段使用杀没有次数限制",
    "龙胆": "杀可以当闪、闪可以当杀",
    "制衡": "出牌阶段可以弃置任意张手牌，然后摸等量的牌（每阶段一次）",
    "奇袭": "黑色手牌可以当过河拆桥使用",
    "克己": "若本回合未使用过杀，跳过弃牌阶段",
    "苦肉": "出牌阶段可以失去 1 点体力，然后摸两张牌",
    "急救": "你的红色手牌可以当桃使用",
    "青囊": "出牌阶段弃一张手牌，令一名角色回复 1 点体力（每阶段一次）",
    "无双": "你使用杀时目标需要两张闪，你决斗的对手需要两张杀",
    "离间": "出牌阶段弃一张牌，令两名男性角色决斗（每阶段一次）",
    "闭月": "结束阶段摸一张牌",
    "雷击": "你打出闪抵挡杀时，50% 概率对杀的使用者造成 1 点雷电伤害（简化版）",
}
