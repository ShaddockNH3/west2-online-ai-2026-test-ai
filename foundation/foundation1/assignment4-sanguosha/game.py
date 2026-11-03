"""游戏引擎：回合流程、牌的结算、技能分发、AI 与胜负判定。

简化的规则（README 里有完整说明）：

- 4 人身份局：主公、忠臣、反贼、内奸各一名，AI 知晓彼此身份；
- 没有装备牌与延时锦囊，判定相关的技能（鬼才、鬼道）随之省略；
- 攻击范围固定为 1（相邻即为目标），主公不再额外 +1 距离；
- 手牌上限 = 当前体力值。
"""

from __future__ import annotations

import random

from cards import ALL_CARD_NAMES, Card, Deck, is_red
from generals import SKILL_HELP, General
from player import IDENTITIES, Player


class PlayerQuit(Exception):
    """人类玩家在输入环节退出。"""


def ask(prompt: str, count: int) -> int:
    """读取 1 到 count 的编号，输入流结束视为退出。"""
    while True:
        try:
            raw = input(prompt).strip()
        except EOFError as error:
            raise PlayerQuit from error
        if raw.isdigit() and 1 <= int(raw) <= count:
            return int(raw)
        print(f"请输入 1 到 {count} 之间的数字。")


def ask_or_cancel(prompt: str, count: int) -> int:
    """同 ask，但接受 0 表示取消。"""
    while True:
        try:
            raw = input(prompt).strip()
        except EOFError as error:
            raise PlayerQuit from error
        if raw == "0":
            return 0
        if raw.isdigit() and 1 <= int(raw) <= count:
            return int(raw)
        print(f"请输入 0（取消）到 {count} 之间的数字。")


class Game:
    """一局三国杀。"""

    def __init__(self, players: list[Player], deck: Deck) -> None:
        self.players = players
        self.deck = deck
        self.round = 0

    # ============ 基础查询 ============

    def alive(self) -> list[Player]:
        return [player for player in self.players if player.alive]

    def distance(self, source: Player, target: Player) -> int:
        """按座位顺/逆时针数存活玩家的最小间隔。"""
        alive = self.alive()
        size = len(alive)
        start = alive.index(source)
        end = alive.index(target)
        return min((end - start) % size, (start - end) % size)

    def in_sha_range(self, source: Player, target: Player) -> bool:
        return source.alive and target.alive and self.distance(source, target) <= 1

    def same_team(self, a: Player, b: Player) -> bool:
        team_a = {"主公", "忠臣"} if a.identity in ("主公", "忠臣") else {a.identity}
        team_b = {"主公", "忠臣"} if b.identity in ("主公", "忠臣") else {b.identity}
        return bool(team_a & team_b)

    def display_table(self) -> None:
        print(f"\n---------- 第 {self.round} 轮 ----------")
        for player in self.players:
            if player.is_human:
                hand = " ".join(repr(card) for card in player.hand)
                print(f"{player.brief(hidden_hand=False)}  手牌：{hand}")
            else:
                print(player.brief())

    # ============ 主循环 ============

    def run(self) -> str:
        """跑完整局，返回获胜阵营。"""
        print("\n===== 游戏开始 =====")
        for player in self.players:
            player.draw(self.deck, 4)
        lord = next(player for player in self.players if player.identity == "主公")
        lord.draw(self.deck, 1)
        self.display_table()

        while True:
            for player in [p for p in self.players if p.alive]:
                self.play_turn(player)
                winner = self.check_winner()
                if winner:
                    return winner

    def play_turn(self, player: Player) -> None:
        """完整回合：摸牌 → 出牌 → 弃牌 → 结束。"""
        self.round += 1
        print(f"\n>>> 轮到 {player.name}（{player.general.name}，{player.identity}）行动")
        player.reset_turn_state()

        self.draw_phase(player)
        self.play_phase(player)

        if not player.alive:
            return
        self.discard_phase(player)
        self.end_phase(player)
        self.display_table()

    # ============ 摸牌阶段 ============

    def draw_phase(self, player: Player) -> None:
        print(f"{player.name} 摸牌阶段。")
        if player.has_skill("突袭"):
            others = [p for p in self.alive() if p is not player]
            if others and self._confirm_skill(player, "突袭", "改为夺取其他角色的手牌"):
                stolen = 0
                for target in others:
                    if stolen >= 2:
                        break
                    card = target.take_random_card()
                    if card:
                        player.hand.append(card)
                        print(f"  突袭：获得 {target.name} 的 {card}")
                        stolen += 1
                return
        player.draw(self.deck, 2)

    # ============ 出牌阶段 ============

    def play_phase(self, player: Player) -> None:
        print(f"{player.name} 出牌阶段。")
        if player.is_human:
            self._human_play_phase(player)
        else:
            self._ai_play_phase(player)

    def _human_play_phase(self, player: Player) -> None:
        """人类玩家的出牌循环。"""
        while True:
            if not player.alive:
                return
            print()
            for index, card in enumerate(player.hand, start=1):
                print(f"  [{index}] {card}")
            print("  [s] 发动技能  [e] 结束出牌阶段")
            try:
                raw = input("请选择（编号 / s / e）：").strip()
            except EOFError as error:
                raise PlayerQuit from error

            if raw == "e":
                return
            if raw == "s":
                self._human_skill_menu(player)
                continue
            if raw.isdigit() and 1 <= int(raw) <= len(player.hand):
                card = player.hand[int(raw) - 1]
                self._human_play_card(player, card)
            else:
                print("无效输入。")

    def _human_play_card(self, player: Player, card: Card) -> None:
        name = card.name
        if name == "闪":
            print("闪只能在你成为杀的目标时打出。")
            return
        if name == "桃":
            if player.heal(1):
                self.deck.discard(player.take_card(card))
                print(f"{player.name} 使用桃，回复 1 点体力（{player.hp}/{player.max_hp}）")
            else:
                print("体力已满，不能使用桃。")
            return
        if name == "酒":
            if player.wine_used:
                print("本回合已经喝过酒了。")
                return
            player.wine_used = True
            self.deck.discard(player.take_card(card))
            print(f"{player.name} 喝下酒，下一张杀伤害 +1。")
            return

        if name == "杀":
            if player.sha_played and not player.has_skill("咆哮"):
                print("本回合已经出过杀了。")
                return
            target = self._choose_enemy(player, "选择杀的目标", check_range=True)
            if target is None:
                return
            self.deck.discard(player.take_card(card))
            damage = 1 + (1 if player.wine_used else 0)
            player.wine_used = False
            player.sha_played = True
            self.resolve_sha(player, target, damage, spent_card=card)
            return

        if name in ("万箭齐发", "桃园结义", "南蛮入侵"):
            self.deck.discard(player.take_card(card))
            self.resolve_trick(player, card, None)
            return

        target = self._choose_enemy(player, f"选择{name}的目标", check_range=name == "顺手牵羊")
        if target is None:
            return
        self.deck.discard(player.take_card(card))
        self.resolve_trick(player, card, target)

    def _choose_enemy(
        self, player: Player, prompt: str, check_range: bool = False
    ) -> Player | None:
        """让人类玩家选一个目标（可以是任何存活角色，敌我由玩家自己判断）。"""
        others = [p for p in self.alive() if p is not player]
        if check_range:
            others = [p for p in others if self.in_sha_range(player, p)]
        if not others:
            print("没有合法目标。")
            return None
        for index, candidate in enumerate(others, start=1):
            mark = "" if self.in_sha_range(player, candidate) else "（超出攻击范围）"
            print(f"  [{index}] {candidate.name}（{candidate.general.name}，体力 {candidate.hp}）{mark}")
        choice = ask_or_cancel(f"{prompt}（编号，0 取消）：", len(others))
        if choice == 0:
            return None
        return others[choice - 1]

    # ---- 人类玩家的技能菜单 ----

    def _human_skill_menu(self, player: Player) -> None:
        options: list[tuple[str, tuple[Player, ...]]] = []
        if player.has_skill("制衡") and not player.zhiheng_used and player.hand:
            options.append(("制衡", ()))
        if player.has_skill("苦肉") and not player.kunang_used:
            options.append(("苦肉", ()))
        if player.has_skill("青囊") and not player.qingnang_used and player.hand:
            options.append(("青囊", ()))
        if player.has_skill("离间") and not player.lijian_used and player.hand:
            males = [p for p in self.alive() if p.general.male]
            if len(males) >= 2:
                options.append(("离间", tuple(males)))
        if player.has_skill("仁德") and player.hand:
            others = [p for p in self.alive() if p is not player]
            options.append(("仁德", tuple(others)))
        if player.has_skill("武圣") and any(card.red for card in player.hand):
            options.append(("武圣", ()))
        if player.has_skill("奇袭") and any(not card.red for card in player.hand):
            options.append(("奇袭", ()))

        if not options:
            print("当前没有可发动的技能。")
            return

        print("可发动的技能：")
        for index, (skill, _) in enumerate(options, start=1):
            print(f"  [{index}] {skill}：{SKILL_HELP[skill]}")
        choice = ask("发动哪个技能（编号，0 取消）：", len(options))
        if choice == 0:
            return

        skill, targets = options[choice - 1]
        if skill == "制衡":
            self._skill_zhiheng(player)
        elif skill == "苦肉":
            self._skill_kunang(player)
        elif skill == "青囊":
            self._skill_qingnang(player)
        elif skill == "离间":
            print("离间需要两名男性角色：")
            first = targets[ask("选择第一名（编号）：", len(targets)) - 1]
            second = targets[ask("选择第二名（编号）：", len(targets)) - 1]
            self._skill_lijian(player, first, second)
        elif skill == "仁德":
            self._skill_rende(player)
        elif skill == "武圣":
            self._skill_wusheng(player)
        elif skill == "奇袭":
            self._skill_qixi(player)

    def _skill_zhiheng(self, player: Player) -> None:
        print("选择要弃置的手牌（逗号分隔编号，0 取消）：")
        for index, card in enumerate(player.hand, start=1):
            print(f"  [{index}] {card}")
        try:
            raw = input("编号：").strip()
        except EOFError as error:
            raise PlayerQuit from error
        if raw == "0":
            return
        indices = sorted({int(part) for part in raw.split(",") if part.strip().isdigit()}, reverse=True)
        picked = [player.hand[i - 1] for i in indices if 1 <= i <= len(player.hand)]
        if not picked:
            print("没有选中任何牌。")
            return
        for card in picked:
            self.deck.discard(player.take_card(card))
        player.draw(self.deck, len(picked))
        player.zhiheng_used = True
        print(f"制衡：弃掉 {len(picked)} 张，摸回 {len(picked)} 张。")

    def _skill_kunang(self, player: Player) -> None:
        player.kunang_used = True
        print("苦肉：失去 1 点体力，摸两张牌。")
        self.lose_hp(player, 1, None)
        if player.alive:
            player.draw(self.deck, 2)

    def _skill_qingnang(self, player: Player) -> None:
        card = self._pick_hand(player, "弃一张手牌作为药引")
        if card is None:
            return
        target = self._choose_target(player, "选择回复体力的角色")
        if target is None:
            return
        self.deck.discard(player.take_card(card))
        player.qingnang_used = True
        if target.heal(1):
            print(f"青囊：{target.name} 回复 1 点体力（{target.hp}/{target.max_hp}）")
        else:
            print(f"青囊：{target.name} 体力已满，药引浪费了。")

    def _skill_lijian(self, player: Player, first: Player, second: Player) -> None:
        card = self._pick_hand(player, "弃一张牌发动离间")
        if card is None:
            return
        player.lijian_used = True
        self.deck.discard(player.take_card(card))
        print(f"离间：{player.name} 令 {first.name} 与 {second.name} 决斗！")
        self.resolve_duel(player, first, second)

    def _skill_rende(self, player: Player) -> None:
        others = [p for p in self.alive() if p is not player]
        while player.hand:
            print("仁德：选择要送出的牌（逗号分隔编号，0 结束）：")
            for index, card in enumerate(player.hand, start=1):
                print(f"  [{index}] {card}")
            try:
                raw = input("编号：").strip()
            except EOFError as error:
                raise PlayerQuit from error
            if raw == "0":
                break
            indices = [int(part) for part in raw.split(",") if part.strip().isdigit()]
            picked = [player.hand[i - 1] for i in indices if 1 <= i <= len(player.hand)]
            if not picked:
                break
            print("送给谁？")
            for index, candidate in enumerate(others, start=1):
                print(f"  [{index}] {candidate.name}")
            receiver = others[ask("编号：", len(others)) - 1]
            for card in picked:
                player.take_card(card)
                receiver.hand.append(card)
                player.rende_given += 1
            print(f"仁德：把 {len(picked)} 张牌交给了 {receiver.name}。")
            if player.rende_given >= 2 and not player.rende_healed and player.heal(1):
                player.rende_healed = True
                print(f"仁德：累计给出两张以上，{player.name} 回复 1 点体力。")

    def _skill_wusheng(self, player: Player) -> None:
        """武圣：红色手牌当杀使用。"""
        reds = [card for card in player.hand if card.red]
        for index, card in enumerate(reds, start=1):
            print(f"  [{index}] {card}")
        choice = ask_or_cancel("选择当作杀的牌（编号，0 取消）：", len(reds))
        if choice == 0:
            return
        card = reds[choice - 1]
        target = self._choose_enemy(player, "选择杀的目标", check_range=True)
        if target is None:
            return
        self.deck.discard(player.take_card(card))
        damage = 1 + (1 if player.wine_used else 0)
        player.wine_used = False
        player.sha_played = True
        print(f"武圣：{player.name} 将 {card} 当杀对 {target.name} 使用。")
        self.resolve_sha(player, target, damage, spent_card=card)

    def _skill_qixi(self, player: Player) -> None:
        """奇袭：黑色手牌当过河拆桥使用。"""
        blacks = [card for card in player.hand if not card.red]
        for index, card in enumerate(blacks, start=1):
            print(f"  [{index}] {card}")
        choice = ask_or_cancel("选择当作过河拆桥的牌（编号，0 取消）：", len(blacks))
        if choice == 0:
            return
        card = blacks[choice - 1]
        candidates = [p for p in self.alive() if p is not player and p.hand]
        if not candidates:
            print("没有有手牌的目标。")
            return
        for index, candidate in enumerate(candidates, start=1):
            print(f"  [{index}] {candidate.name}（手牌 {len(candidate.hand)}）")
        picked = ask_or_cancel("选择目标（编号，0 取消）：", len(candidates))
        if picked == 0:
            return
        self.deck.discard(player.take_card(card))
        print(f"奇袭：{player.name} 将 {card} 当过河拆桥使用。")
        self.resolve_trick(player, Card("过河拆桥", card.suit), candidates[picked - 1])

    # ---- 通用的小交互 ----

    def _pick_hand(self, player: Player, prompt: str) -> Card | None:
        if not player.hand:
            print(f"{player.name} 没有手牌。")
            return None
        for index, card in enumerate(player.hand, start=1):
            print(f"  [{index}] {card}")
        choice = ask(f"{prompt}（编号，0 取消）：", len(player.hand))
        if choice == 0:
            return None
        return player.hand[choice - 1]

    def _choose_target(self, player: Player, prompt: str) -> Player | None:
        candidates = [p for p in self.alive()]
        for index, candidate in enumerate(candidates, start=1):
            print(f"  [{index}] {candidate.name}（体力 {candidate.hp}/{candidate.max_hp}）")
        choice = ask(f"{prompt}（编号，0 取消）：", len(candidates))
        if choice == 0:
            return None
        return candidates[choice - 1]

    def _confirm_skill(self, player: Player, skill: str, desc: str) -> bool:
        if player.is_human:
            answer = input(
                f"是否发动【{skill}】（{desc}）？（y/n）："
            ).strip().lower()
            return answer in ("y", "yes", "是")
        return True  # AI 默认发动主动收益技能

    # ============ AI 出牌 ============

    def _ai_enemies(self, player: Player) -> list[Player]:
        """AI 视角下的敌人（简化：AI 直接知道身份）。"""
        enemies = [p for p in self.alive() if p is not player and not self.same_team(player, p)]
        if player.identity == "内奸":
            # 内奸优先打反贼和忠臣，最后再收主公
            enemies.sort(key=lambda p: 0 if p.identity != "主公" else 1)
        return enemies

    def _ai_weakest(self, candidates: list[Player]) -> Player | None:
        return min(candidates, key=lambda p: (p.hp, -len(p.hand)), default=None)

    def _ai_play_phase(self, player: Player) -> None:
        for _ in range(12):  # 防御性上限，避免 AI 死循环
            action_taken = False
            action_taken |= self._ai_act(player)
            if not action_taken or not player.alive:
                break

    def _ai_act(self, player: Player) -> bool:
        """执行一个 AI 动作，返回是否真的执行了。"""
        enemies = self._ai_enemies(player)
        friends = [p for p in self.alive() if p is not player and self.same_team(player, p)]

        # 1. 自己濒死边缘先吃桃
        if player.hp == 1:
            peach = self._find_card(player, "桃")
            if peach and player.heal(1):
                self.deck.discard(player.take_card(peach))
                print(f"{player.name} 使用桃回复体力（{player.hp}/{player.max_hp}）")
                return True

        # 2. 濒死队友的桃在求桃阶段处理，这里优先救残血队友
        if player.has_skill("青囊") and not player.qingnang_used and player.hand:
            wounded = [p for p in friends if p.hp < p.max_hp]
            target = self._ai_weakest(wounded)
            if target and player.hp >= 2:
                self.deck.discard(player.take_card(player.hand[0]))
                player.qingnang_used = True
                if target.heal(1):
                    print(f"青囊：{player.name} 弃一张牌，令 {target.name} 回复 1 点体力")
                    return True

        # 3. 无中生有
        card = self._find_card(player, "无中生有")
        if card:
            self.deck.discard(player.take_card(card))
            print(f"{player.name} 使用无中生有，摸两张牌。")
            player.draw(self.deck, 2)
            return True

        # 4. 桃园结义（己方缺血比敌方多时才用）
        card = self._find_card(player, "桃园结义")
        if card:
            friend_missing = sum(p.max_hp - p.hp for p in friends + [player])
            enemy_missing = sum(p.max_hp - p.hp for p in enemies)
            if friend_missing > enemy_missing:
                self.deck.discard(player.take_card(card))
                self.resolve_trick(player, card, None)
                return True

        # 5. 杀
        card = self._find_card(player, "杀")
        if card and (not player.sha_played or player.has_skill("咆哮")):
            in_range = [p for p in enemies if self.in_sha_range(player, p)]
            target = self._ai_weakest(in_range)
            if target:
                self.deck.discard(player.take_card(card))
                damage = 1 + (1 if player.wine_used else 0)
                player.wine_used = False
                player.sha_played = True
                print(f"{player.name} 对 {target.name} 使用杀。")
                self.resolve_sha(player, target, damage, spent_card=card)
                return True

        # 6. 决斗
        card = self._find_card(player, "决斗")
        if card and enemies:
            target = self._ai_weakest(enemies)
            if target:
                self.deck.discard(player.take_card(card))
                self.resolve_trick(player, card, target)
                return True

        # 7. 顺手牵羊 / 过河拆桥
        for name in ("顺手牵羊", "过河拆桥"):
            card = self._find_card(player, name)
            if card and enemies:
                candidates = [p for p in enemies if p.hand]
                if name == "顺手牵羊":
                    candidates = [p for p in candidates if self.in_sha_range(player, p)]
                target = max(candidates, key=lambda p: len(p.hand), default=None)
                if target:
                    self.deck.discard(player.take_card(card))
                    self.resolve_trick(player, card, target)
                    return True

        # 8. AOE
        card = self._find_card(player, "南蛮入侵") or self._find_card(player, "万箭齐发")
        if card and len(enemies) > len(friends):
            self.deck.discard(player.take_card(card))
            self.resolve_trick(player, card, None)
            return True

        # 9. 酒 + 杀的连招（下一轮再杀）
        card = self._find_card(player, "酒")
        if card and not player.wine_used and any(
            self._find_card(player, "杀") for _ in [0]
        ):
            self.deck.discard(player.take_card(card))
            player.wine_used = True
            print(f"{player.name} 喝下酒。")
            return True

        # 10. 制衡：手里全是没用的牌时换掉
        if player.has_skill("制衡") and not player.zhiheng_used and player.hand:
            useless = [c for c in player.hand if c.name == "闪"]
            if len(useless) >= 2 and not self._find_card(player, "杀"):
                for card in useless:
                    self.deck.discard(player.take_card(card))
                player.draw(self.deck, len(useless))
                player.zhiheng_used = True
                print(f"{player.name} 制衡换掉 {len(useless)} 张闪。")
                return True

        # 11. 苦肉：血量健康且手里没牌时搏一波
        if player.has_skill("苦肉") and not player.kunang_used and not player.hand and player.hp >= 3:
            player.kunang_used = True
            print("苦肉：失去 1 点体力，摸两张牌。")
            self.lose_hp(player, 1, None)
            if player.alive:
                player.draw(self.deck, 2)
            return True

        return False

    def _find_card(self, player: Player, name: str) -> Card | None:
        for card in player.hand:
            if card.name == name:
                return card
        return None

    # ============ 弃牌与结束阶段 ============

    def discard_phase(self, player: Player) -> None:
        limit = player.hp
        if player.has_skill("克己") and not player.sha_played:
            if len(player.hand) > limit:
                print(f"克己：{player.name} 本回合没出杀，跳过弃牌阶段。")
            return
        excess = len(player.hand) - limit
        if excess <= 0:
            return
        if player.is_human:
            print(f"手牌超出上限 {excess} 张，请选择要弃置的牌：")
            for _ in range(excess):
                card = self._pick_hand(player, f"弃牌（还需弃 {excess} 张）")
                if card is None:
                    card = player.hand[0]
                self.deck.discard(player.take_card(card))
                print(f"  弃置 {card}")
        else:
            for _ in range(excess):
                card = player.take_random_card()
                if card:
                    self.deck.discard(card)
            print(f"{player.name} 弃置 {excess} 张手牌。")

    def end_phase(self, player: Player) -> None:
        if player.has_skill("闭月"):
            player.draw(self.deck, 1)
            print(f"闭月：{player.name} 摸一张牌。")

    # ============ 牌的结算 ============

    def resolve_sha(
        self, source: Player, target: Player, damage: int, spent_card: Card | None
    ) -> None:
        """杀的结算：目标出闪（龙胆可用杀代替），否则受伤。"""
        needed = 2 if source.has_skill("无双") else 1
        dodged = self._ask_dodge(target, needed, source)
        if dodged:
            if target.has_skill("雷击") and random.random() < 0.5 and source.alive:
                print(f"雷击：{target.name} 的闪引落天雷，{source.name} 受到 1 点雷电伤害！")
                self.damage(target, source, 1, None)
            return
        self.damage(source, target, damage, spent_card)

    def _ask_dodge(self, target: Player, needed: int, source: Player) -> bool:
        """让 target 打出 needed 张闪（龙胆可用杀代替）。"""
        for _ in range(needed):
            card = self._find_response(target, "闪", "杀")
            if card is None:
                return False
            self.deck.discard(target.take_card(card))
            print(f"{target.name} 打出 {card} 闪避。")
        return True

    def _find_response(self, player: Player, *names: str) -> Card | None:
        """寻找可打出的响应牌，龙胆 / 武圣在此生效。"""
        for card in player.hand:
            if card.name in names:
                return card
        # 龙胆：杀当闪、闪当杀
        if player.has_skill("龙胆") and set(names) == {"闪"}:
            kill = self._find_card(player, "杀")
            if kill:
                print(f"{player.name} 发动龙胆，将杀当闪使用。")
                return kill
        # 武圣：红色手牌当杀
        if player.has_skill("武圣") and "杀" in names:
            for card in player.hand:
                if card.red:
                    print(f"{player.name} 发动武圣，将红色牌 {card} 当杀使用。")
                    return card
        return None

    def resolve_trick(self, source: Player, card: Card, target: Player | None) -> None:
        """锦囊的结算入口。"""
        name = card.name
        print(f"{source.name} 使用【{name}】。")

        if name == "无懈可击":
            return  # 无懈只能作为响应打出

        # 询问无懈可击
        if self._ask_wuxie(source, target, name):
            print(f"【{name}】被无懈可击抵消。")
            return

        if name == "无中生有":
            source.draw(self.deck, 2)
        elif name == "过河拆桥":
            if target and target.hand:
                discarded = target.discard_random(self.deck) if not target.is_human else None
                if target.is_human:
                    print("你要弃置哪张牌？")
                    for index, item in enumerate(target.hand, start=1):
                        print(f"  [{index}] {item}")
                    picked = ask("编号：", len(target.hand))
                    discarded = target.take_card(target.hand[picked - 1])
                    self.deck.discard(discarded)
                print(f"过河拆桥：{target.name} 弃置了一张牌。")
            elif target:
                print(f"{target.name} 没有手牌，过河拆桥落空。")
        elif name == "顺手牵羊":
            if target and target.hand:
                card_taken = target.take_random_card()
                if card_taken:
                    source.hand.append(card_taken)
                    print(f"顺手牵羊：{source.name} 获得 {target.name} 的 {card_taken}。")
            elif target:
                print(f"{target.name} 没有手牌，顺手牵羊落空。")
        elif name == "决斗":
            if target:
                self.resolve_duel(source, source, target)
        elif name in ("南蛮入侵", "万箭齐发"):
            response = "杀" if name == "南蛮入侵" else "闪"
            for other in [p for p in self.alive() if p is not source]:
                response_card = self._find_response(other, response)
                if response_card:
                    self.deck.discard(other.take_card(response_card))
                    print(f"{other.name} 打出 {response_card} 应对。")
                else:
                    print(f"{other.name} 无法应对，受到 1 点伤害。")
                    self.damage(source, other, 1, card)
        elif name == "桃园结义":
            for other in self.alive():
                if other.heal(1):
                    print(f"桃园结义：{other.name} 回复 1 点体力（{other.hp}/{other.max_hp}）")

    def resolve_duel(self, source: Player, duelist: Player, opponent: Player) -> None:
        """决斗：双方轮流打出杀，先不出的一方受 1 点伤害。

        无双（吕布是决斗发起者时）：对手需要两张杀。
        """
        needed = 2 if duelist.has_skill("无双") and duelist is not opponent else 1
        attacker, defender = duelist, opponent
        while True:
            count = needed if attacker is duelist else 1
            played = 0
            for _ in range(count):
                card = self._find_response(defender, "杀")
                if card is None:
                    break
                self.deck.discard(defender.take_card(card))
                print(f"{defender.name} 打出 {card}。")
                played += 1
            if played < count:
                self.damage(attacker, defender, 1, None)
                return
            attacker, defender = defender, attacker

    def _ask_wuxie(self, source: Player, target: Player | None, trick: str) -> bool:
        """询问其他玩家是否用无懈可击抵消，可嵌套反制一次。"""
        cancelled = False
        depth = 0
        while depth < 3:
            responder: Player | None = None
            for other in [p for p in self.alive() if p is not source or cancelled]:
                card = self._find_card(other, "无懈可击")
                if card is None:
                    continue
                if other.is_human:
                    answer = input(
                        f"要对 {source.name} 的【{trick}】使用无懈可击吗？（y/n）："
                    ).strip().lower()
                    if answer not in ("y", "yes", "是"):
                        continue
                elif not self._ai_wants_wuxie(other, target, cancelled):
                    continue
                responder = other
                self.deck.discard(other.take_card(card))
                print(f"{other.name} 打出无懈可击！")
                break
            if responder is None:
                break
            cancelled = not cancelled
            depth += 1
            source = responder
        return cancelled

    def _ai_wants_wuxie(self, player: Player, target: Player | None, cancelling: bool) -> bool:
        """AI 只救自己人和自己。"""
        if target is None:
            return False
        if cancelling:
            return not self.same_team(player, target)
        return self.same_team(player, target)

    # ============ 伤害、濒死与死亡 ============

    def lose_hp(self, player: Player, amount: int, source: Player | None) -> None:
        """不通过伤害的体力流失（苦肉等），同样可能进入濒死。"""
        player.change_hp(-amount)
        print(f"{player.name} 失去 {amount} 点体力（{player.hp}/{player.max_hp}）")
        if player.hp <= 0:
            self.dying(player)

    def damage(self, source: Player | None, target: Player, amount: int, card: Card | None) -> None:
        """造成伤害，并处理受到伤害后的技能。"""
        if source is not None:
            self._last_damager = source
        target.change_hp(-amount)
        verb = f"{source.name} 对 {target.name}" if source else f"{target.name}"
        print(f"{verb} 造成 {amount} 点伤害（体力 {target.hp}/{target.max_hp}）")
        if target.hp <= 0:
            self.dying(target)
        if not target.alive or source is None:
            return

        # 受到伤害后的技能
        if target.has_skill("奸雄") and card is not None:
            if self._confirm_skill(target, "奸雄", f"获得造成伤害的 {card}"):
                target.hand.append(card)
                print(f"奸雄：{target.name} 获得了 {card}。")
                self._remove_from_discard(card)
        if target.has_skill("反馈") and source.hand:
            stolen = source.take_random_card()
            if stolen:
                target.hand.append(stolen)
                print(f"反馈：{target.name} 获得了 {source.name} 的 {stolen}。")
        if target.has_skill("刚烈") and random.random() < 0.5:
            print(f"刚烈：{target.name} 发动刚烈！")
            if source.hand:
                discarded = source.discard_random(self.deck)
                print(f"  {source.name} 弃置了 {discarded}。")
            else:
                self.lose_hp(source, 1, None)

    def _remove_from_discard(self, card: Card) -> None:
        """奸雄拿走的牌还在弃牌堆里，要把它拿回来。"""
        for index, item in enumerate(self.deck._discard):  # noqa: SLF001
            if item is card:
                self.deck._discard.pop(index)  # noqa: SLF001
                return

    def dying(self, player: Player) -> None:
        """濒死：从自己开始按座位顺序询问所有玩家是否出桃。"""
        while player.hp <= 0 and player.alive:
            saved = False
            order = self.alive()
            start = order.index(player) if player in order else 0
            for helper in order[start:] + order[:start]:
                peach = self._find_peach(helper)
                if peach is None:
                    continue
                if helper.is_human:
                    answer = input(
                        f"要对 {player.name} 使用 {peach} 吗？（y/n）："
                    ).strip().lower()
                    if answer not in ("y", "yes", "是"):
                        continue
                elif not (helper is player or self.same_team(helper, player)):
                    continue
                self.deck.discard(helper.take_card(peach))
                player.heal(1)
                print(f"{helper.name} 对 {player.name} 使用桃（体力 {player.hp}/{player.max_hp}）")
                saved = True
                break
            if not saved:
                self.death(player)
                return

    def _find_peach(self, player: Player) -> Card | None:
        """找一张可当桃的牌：桃本身，或华佗的红色手牌（急救）。"""
        peach = self._find_card(player, "桃")
        if peach:
            return peach
        if player.has_skill("急救"):
            for card in player.hand:
                if is_red(card.suit):
                    print(f"{player.name} 发动急救，将 {card} 当桃使用。")
                    return card
        return None

    def death(self, player: Player) -> None:
        """死亡结算：身份揭晓、弃牌、奖惩。"""
        player.alive = False
        player.discard_all(self.deck)
        print(f"\n*** {player.name}（{player.general.name}）阵亡，身份是【{player.identity}】***")
        if player.identity == "反贼":
            killer = self._last_damager
            if killer and killer.alive:
                killer.draw(self.deck, 3)
                print(f"击杀反贼的 {killer.name} 摸三张牌。")

    _last_damager: Player | None = None

    # ============ 胜负 ============

    def check_winner(self) -> str | None:
        alive = self.alive()
        lord = next((p for p in self.players if p.identity == "主公"), None)
        if lord is not None and not lord.alive:
            if len(alive) == 1 and alive[0].identity == "内奸":
                return "内奸"
            return "反贼"
        if all(p.identity != "反贼" for p in alive) and all(
            p.identity != "内奸" for p in alive
        ):
            return "主公与忠臣"
        return None
