"""
KANISTRA ABYSS - UI Rendering (curses-based)
Split screen: dungeon map (left) + stats panel (right).
"""
from __future__ import annotations
import curses
import math
from typing import List, Optional, Tuple, TYPE_CHECKING

from data import (
    CP, TILE_CHARS, CLASS_DEFS, SKILL_DEFS,
    STATUS_DEFS, ITEM_DEFS, ENEMY_DEFS,
)
from entities import Player, Enemy, FloorItem

if TYPE_CHECKING:
    from dungeon import DungeonFloor
    from engine import GameState


# Panel dimensions (will be set by engine on init)
MAP_PANEL_W = 60
MAP_PANEL_H = 45
SIDE_PANEL_W = 24
LOG_PANEL_H = 10

TOTAL_W = MAP_PANEL_W + SIDE_PANEL_W
TOTAL_H = MAP_PANEL_H + LOG_PANEL_H


def init_colors() -> None:
    """Initialise curses colour pairs."""
    curses.start_color()
    curses.use_default_colors()

    def c(r: int, g: int, b: int) -> int:
        # curses uses 0-1000 range
        return (r * 1000 // 255, g * 1000 // 255, b * 1000 // 255)

    pairs = {
        CP["WALL"]:        (curses.COLOR_WHITE,   curses.COLOR_BLACK),
        CP["FLOOR"]:       (curses.COLOR_WHITE,   curses.COLOR_BLACK),
        CP["PLAYER"]:      (curses.COLOR_CYAN,    curses.COLOR_BLACK),
        CP["ENEMY"]:       (curses.COLOR_RED,     curses.COLOR_BLACK),
        CP["ITEM"]:        (curses.COLOR_YELLOW,  curses.COLOR_BLACK),
        CP["UI"]:          (curses.COLOR_WHITE,   curses.COLOR_BLACK),
        CP["HP_HIGH"]:     (curses.COLOR_GREEN,   curses.COLOR_BLACK),
        CP["HP_MED"]:      (curses.COLOR_YELLOW,  curses.COLOR_BLACK),
        CP["HP_LOW"]:      (curses.COLOR_RED,     curses.COLOR_BLACK),
        CP["MANA"]:        (curses.COLOR_BLUE,    curses.COLOR_BLACK),
        CP["STAIRS"]:      (curses.COLOR_CYAN,    curses.COLOR_BLACK),
        CP["EXPLORED"]:    (curses.COLOR_BLACK,   curses.COLOR_BLACK),
        CP["STATUS_BAD"]:  (curses.COLOR_RED,     curses.COLOR_BLACK),
        CP["STATUS_GOOD"]: (curses.COLOR_GREEN,   curses.COLOR_BLACK),
        CP["CRIT"]:        (curses.COLOR_MAGENTA, curses.COLOR_BLACK),
        CP["BOSS"]:        (curses.COLOR_MAGENTA, curses.COLOR_BLACK),
        CP["GOLD"]:        (curses.COLOR_YELLOW,  curses.COLOR_BLACK),
        CP["TITLE"]:       (curses.COLOR_CYAN,    curses.COLOR_BLACK),
        CP["SHOP"]:        (curses.COLOR_YELLOW,  curses.COLOR_BLACK),
        CP["LOG_OLD"]:     (curses.COLOR_WHITE,   curses.COLOR_BLACK),
    }
    for pair_id, (fg, bg) in pairs.items():
        try:
            curses.init_pair(pair_id, fg, bg)
        except Exception:
            pass


def color(key: str) -> int:
    pair_id = CP.get(key, CP["UI"])
    return curses.color_pair(pair_id)


def safe_addstr(win, y: int, x: int, text: str, attr: int = 0) -> None:
    """curses addstr that silently ignores out-of-bounds / resize errors."""
    try:
        h, w = win.getmaxyx()
        if y < 0 or y >= h or x < 0:
            return
        # clip text to available width
        avail = w - x
        if avail <= 0:
            return
        text = text[:avail]
        win.addstr(y, x, text, attr)
    except curses.error:
        pass


def draw_box(win, y: int, x: int, h: int, w: int, attr: int = 0,
             title: str = "") -> None:
    """Draw a box with optional title."""
    try:
        # top
        safe_addstr(win, y, x, "╔" + "═" * (w - 2) + "╗", attr)
        # sides
        for i in range(1, h - 1):
            safe_addstr(win, y + i, x, "║", attr)
            safe_addstr(win, y + i, x + w - 1, "║", attr)
        # bottom
        safe_addstr(win, y + h - 1, x, "╚" + "═" * (w - 2) + "╝", attr)
        if title:
            t = f" {title} "
            safe_addstr(win, y, x + (w - len(t)) // 2, t,
                        attr | curses.A_BOLD)
    except Exception:
        pass


def bar(current: int, maximum: int, width: int, fill_char: str = "█",
        empty_char: str = "░") -> str:
    if maximum <= 0:
        return empty_char * width
    filled = max(0, min(width, int(current / maximum * width)))
    return fill_char * filled + empty_char * (width - filled)


# ─────────────────────────────────────────────
#  Main renderer
# ─────────────────────────────────────────────
class Renderer:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        init_colors()
        curses.curs_set(0)

        # Calculate panel sizes dynamically
        self.side_w = min(SIDE_PANEL_W, max(20, self.width - MAP_PANEL_W))
        self.map_w  = self.width - self.side_w
        self.log_h  = min(LOG_PANEL_H, max(5, self.height - MAP_PANEL_H))
        self.map_h  = self.height - self.log_h

        # Camera / viewport
        self.cam_x = 0
        self.cam_y = 0

    def update_size(self) -> None:
        self.height, self.width = self.stdscr.getmaxyx()
        self.side_w = min(SIDE_PANEL_W, max(20, self.width - MAP_PANEL_W))
        self.map_w  = self.width - self.side_w
        self.log_h  = min(LOG_PANEL_H, max(5, self.height - MAP_PANEL_H))
        self.map_h  = self.height - self.log_h

    def center_camera(self, px: int, py: int, floor_w: int, floor_h: int) -> None:
        self.cam_x = max(0, min(px - self.map_w // 2, floor_w - self.map_w))
        self.cam_y = max(0, min(py - self.map_h // 2, floor_h - self.map_h))

    # ── Dungeon map ──────────────────────────
    def draw_map(self, floor: "DungeonFloor", player: Player,
                 enemies: List[Enemy], items: List[FloorItem]) -> None:
        stdscr = self.stdscr
        mw = self.map_w
        mh = self.map_h
        cx, cy = self.cam_x, self.cam_y

        # Build entity position maps
        enemy_map  = {(e.x, e.y): e for e in enemies if e.alive}
        item_map: dict = {}
        for fi in items:
            if (fi.x, fi.y) not in item_map:
                item_map[(fi.x, fi.y)] = fi

        for screen_y in range(mh):
            map_y = screen_y + cy
            if map_y < 0 or map_y >= floor.height:
                continue
            for screen_x in range(mw):
                map_x = screen_x + cx
                if map_x < 0 or map_x >= floor.width:
                    continue
                tile = floor.tiles[map_y][map_x]
                if not tile.explored:
                    safe_addstr(stdscr, screen_y, screen_x, " ")
                    continue

                pos = (map_x, map_y)
                ch = tile.char
                attr = 0

                if not tile.visible:
                    # explored but not visible → dim
                    attr = color("EXPLORED") | curses.A_DIM
                    # Draw explored walls/floor in dim
                    if tile.char == TILE_CHARS["wall"]:
                        ch = "#"
                        attr = color("EXPLORED") | curses.A_DIM
                    else:
                        ch = "·"
                else:
                    # Determine what to draw
                    if pos == (player.x, player.y):
                        ch = player.symbol
                        attr = color("PLAYER") | curses.A_BOLD
                    elif pos in enemy_map:
                        e = enemy_map[pos]
                        ch = e.symbol
                        attr = color(e.color_key) | curses.A_BOLD
                        if e.is_boss:
                            attr = color("BOSS") | curses.A_BOLD | curses.A_BLINK
                    elif pos in item_map:
                        fi = item_map[pos]
                        ch = fi.item.symbol
                        attr = color(fi.item.color_key) | curses.A_BOLD
                    elif tile.char == TILE_CHARS["wall"]:
                        ch = "#"
                        attr = color("WALL")
                    elif tile.char == TILE_CHARS["stairs_down"]:
                        ch = ">"
                        attr = color("STAIRS") | curses.A_BOLD
                    elif tile.char == TILE_CHARS["stairs_up"]:
                        ch = "<"
                        attr = color("STAIRS") | curses.A_BOLD
                    elif tile.char == TILE_CHARS["shop"]:
                        ch = "$"
                        attr = color("SHOP") | curses.A_BOLD
                    else:
                        ch = "."
                        attr = color("FLOOR") | curses.A_DIM

                safe_addstr(stdscr, screen_y, screen_x, ch, attr)

    # ── Side panel ───────────────────────────
    def draw_side_panel(self, player: Player,
                         floor_num: int,
                         enemy_target: Optional[Enemy] = None) -> None:
        stdscr = self.stdscr
        sx = self.map_w
        sw = self.side_w

        def sp(y: int, x: int, text: str, attr: int = 0) -> None:
            safe_addstr(stdscr, y, sx + x, text, attr)

        # Border
        for y in range(self.height):
            safe_addstr(stdscr, y, sx, "│", color("UI"))

        row = 0
        # Title
        title = "KANISTRA ABYSS"
        sp(row, (sw - len(title)) // 2, title,
           color("TITLE") | curses.A_BOLD)
        row += 1
        sp(row, 0, "═" * (sw - 1), color("UI"))
        row += 1

        # Character info
        sp(row, 1, f"{player.name[:14]}", color("PLAYER") | curses.A_BOLD)
        row += 1
        sp(row, 1, f"{player.class_name} Lv.{player.level}", color("UI") | curses.A_BOLD)
        row += 1
        sp(row, 1, f"Floor: {floor_num}", color("STAIRS"))
        row += 1
        sp(row, 0, "─" * (sw - 1), color("UI") | curses.A_DIM)
        row += 1

        # HP bar
        bar_w = sw - 6
        hp_bar = bar(player.hp, player.max_hp_total, bar_w)
        hp_pct = player.hp / player.max_hp_total if player.max_hp_total > 0 else 0
        hp_col = "HP_HIGH" if hp_pct > 0.5 else ("HP_MED" if hp_pct > 0.25 else "HP_LOW")
        sp(row, 1, f"HP ", color("UI"))
        sp(row, 4, hp_bar, color(hp_col) | curses.A_BOLD)
        row += 1
        sp(row, 1, f"   {player.hp:>4}/{player.max_hp_total:<4}", color(hp_col))
        row += 1

        # Mana bar
        if player.max_mana_total > 0:
            mp_bar = bar(player.mana, player.max_mana_total, bar_w)
            sp(row, 1, f"MP ", color("UI"))
            sp(row, 4, mp_bar, color("MANA") | curses.A_BOLD)
            row += 1
            sp(row, 1, f"   {player.mana:>4}/{player.max_mana_total:<4}", color("MANA"))
            row += 1

        # XP bar
        if player.level < 20 and player.xp_next > 0:
            xp_bar = bar(player.xp, player.xp_next, bar_w, "▓", "░")
            sp(row, 1, f"XP ", color("UI"))
            sp(row, 4, xp_bar, color("GOLD"))
            row += 1
            sp(row, 1, f"   {player.xp:>4}/{player.xp_next:<4}", color("GOLD") | curses.A_DIM)
            row += 1
        else:
            sp(row, 1, "MAX LEVEL!", color("GOLD") | curses.A_BOLD)
            row += 1

        sp(row, 0, "─" * (sw - 1), color("UI") | curses.A_DIM)
        row += 1

        # Stats
        sp(row, 1, f"ATK:{player.effective_attack:<4} DEF:{player.effective_defense:<3}",
           color("UI"))
        row += 1
        sp(row, 1, f"CRIT:{player.crit_chance*100:.0f}%  DODGE:{player.dodge_chance*100:.0f}%",
           color("UI") | curses.A_DIM)
        row += 1
        sp(row, 1, f"Gold: {player.gold}", color("GOLD") | curses.A_BOLD)
        row += 1
        if player.stat_points > 0:
            sp(row, 1, f"STAT PTS: {player.stat_points}",
               color("CRIT") | curses.A_BOLD | curses.A_BLINK)
            row += 1

        sp(row, 0, "─" * (sw - 1), color("UI") | curses.A_DIM)
        row += 1

        # Equipment
        sp(row, 1, "EQUIPMENT", color("UI") | curses.A_BOLD | curses.A_UNDERLINE)
        row += 1
        weap_name = player.equipment.weapon.name[:sw-5] if player.equipment.weapon else "---"
        arm_name  = player.equipment.armor.name[:sw-5]  if player.equipment.armor  else "---"
        ring_name = player.equipment.ring.name[:sw-5]   if player.equipment.ring   else "---"
        sp(row, 1, f"⚔ {weap_name}", color("ITEM"))
        row += 1
        sp(row, 1, f"🛡 {arm_name}", color("ITEM"))
        row += 1
        sp(row, 1, f"○ {ring_name}", color("GOLD"))
        row += 1

        sp(row, 0, "─" * (sw - 1), color("UI") | curses.A_DIM)
        row += 1

        # Skills
        sp(row, 1, "SKILLS", color("UI") | curses.A_BOLD | curses.A_UNDERLINE)
        row += 1
        for i, sk_key in enumerate(player.skill_keys):
            if row >= self.map_h - 1:
                break
            sdef = SKILL_DEFS.get(sk_key)
            if not sdef:
                continue
            cd = player.skill_cooldowns.get(sk_key, 0)
            ready = cd == 0
            cost = sdef.mana_cost
            can_use = player.mana >= cost and ready
            col = "HP_HIGH" if can_use else ("HP_MED" if ready else "EXPLORED")
            cd_str = f"[{cd}]" if cd > 0 else "   "
            sp(row, 1, f"{i+1} {sdef.name[:12]:<12}{cd_str}",
               color(col) | (curses.A_BOLD if can_use else 0))
            row += 1

        # Status effects
        if player.statuses and row < self.map_h - 2:
            sp(row, 0, "─" * (sw - 1), color("UI") | curses.A_DIM)
            row += 1
            sp(row, 1, "STATUS:", color("UI") | curses.A_BOLD)
            row += 1
            status_str = " ".join(s.symbol for s in player.statuses[:6])
            sp(row, 1, status_str[:sw-2], color("STATUS_BAD") | curses.A_BOLD)
            row += 1
            # Names
            for s in player.statuses[:4]:
                if row >= self.map_h - 1:
                    break
                col = s.color_key
                sp(row, 1, f"{s.name[:10]} ({s.turns_remaining}t)",
                   color(col))
                row += 1

        # Target info
        if enemy_target and enemy_target.alive and row < self.map_h - 4:
            sp(row, 0, "─" * (sw - 1), color("UI") | curses.A_DIM)
            row += 1
            sp(row, 1, "TARGET:", color("ENEMY") | curses.A_BOLD)
            row += 1
            tname = enemy_target.name[:sw-3]
            sp(row, 1, tname, color(enemy_target.color_key) | curses.A_BOLD)
            row += 1
            bar_w = sw - 6
            thp_bar = bar(enemy_target.hp, enemy_target.max_hp, bar_w, "█", "░")
            hp_pct  = enemy_target.hp / enemy_target.max_hp if enemy_target.max_hp > 0 else 0
            thp_col = "HP_HIGH" if hp_pct > 0.5 else ("HP_MED" if hp_pct > 0.25 else "HP_LOW")
            sp(row, 1, f"HP {thp_bar}", color(thp_col))
            row += 1
            sp(row, 1, f"   {enemy_target.hp}/{enemy_target.max_hp}", color(thp_col))
            row += 1
            if enemy_target.statuses:
                st_str = " ".join(s.symbol for s in enemy_target.statuses[:4])
                sp(row, 1, st_str[:sw-2], color("STATUS_BAD"))
                row += 1

    # ── Combat log ───────────────────────────
    def draw_log(self, messages: List[str]) -> None:
        stdscr = self.stdscr
        log_y = self.map_h
        log_h = self.log_h
        log_w = self.width

        # Border
        safe_addstr(stdscr, log_y, 0, "─" * log_w, color("UI"))
        safe_addstr(stdscr, log_y, 1, " COMBAT LOG ", color("UI") | curses.A_BOLD)

        display = messages[-(log_h - 1):]  # last N messages
        for i, msg in enumerate(display):
            row = log_y + 1 + i
            if row >= self.height:
                break
            # Colour coding
            if "CRITICAL" in msg or "***" in msg:
                attr = color("CRIT") | curses.A_BOLD
            elif "slain" in msg or "dies" in msg or "SLAIN" in msg:
                attr = color("HP_LOW") | curses.A_BOLD
            elif "LEVEL UP" in msg:
                attr = color("GOLD") | curses.A_BOLD
            elif "heals" in msg or "restores" in msg or "regenerates" in msg:
                attr = color("HP_HIGH")
            elif "Burning" in msg or "Frozen" in msg or "Poisoned" in msg or "Stunned" in msg:
                attr = color("STATUS_BAD")
            elif "Blessed" in msg or "Shielded" in msg or "Invisible" in msg:
                attr = color("STATUS_GOOD")
            elif i < len(display) - 3:
                attr = color("LOG_OLD") | curses.A_DIM
            else:
                attr = color("UI")
            safe_addstr(stdscr, row, 1, msg[:log_w - 2], attr)

    # ── Controls hint ────────────────────────
    def draw_controls(self) -> None:
        hints = "WASD/←↑↓→:Move  1-4:Skills  i:Inv  g:Pickup  e:Interact  >/<:Stairs  TAB:Target  ?:Help  q:Quit"
        safe_addstr(self.stdscr, self.height - 1, 0,
                    hints[:self.width - 1], color("UI") | curses.A_DIM)

    # ── Full render ──────────────────────────
    def render(self, state: "GameState") -> None:
        self.stdscr.erase()
        self.update_size()
        self.center_camera(state.player.x, state.player.y,
                           state.floor.width, state.floor.height)
        self.draw_map(state.floor, state.player, state.enemies, state.floor_items)
        self.draw_side_panel(state.player, state.player.floor, state.target_enemy)
        self.draw_log(state.log)
        self.stdscr.refresh()

    # ─────────────────────────────────────────
    #  Overlay screens
    # ─────────────────────────────────────────
    def draw_title_screen(self, has_save: bool = False) -> None:
        stdscr = self.stdscr
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        cx = w // 2

        logo = [
            r"  _  __   _   _  _ ___ ___  _____ ___   _   ",
            r" | |/ /  /_\ | \| |_ _/ __|_   _| _ \ /_\  ",
            r" | ' <  / _ \| .` || |\__ \ | | |   // _ \ ",
            r" |_|\_\/_/ \_\_|\_|___|___/ |_| |_|_/_/ \_|",
            r"            A  B  Y  S  S                    ",
        ]

        start_y = max(2, h // 2 - 10)
        for i, line in enumerate(logo):
            x = max(0, cx - len(line) // 2)
            safe_addstr(stdscr, start_y + i, x, line,
                        color("TITLE") | curses.A_BOLD)

        tagline = "Descend into the eternal darkness..."
        safe_addstr(stdscr, start_y + 7, cx - len(tagline) // 2, tagline,
                    color("EXPLORED") | curses.A_ITALIC)

        options = [
            ("N", "New Game"),
            ("C", "Continue" if has_save else None),
            ("H", "High Scores"),
            ("Q", "Quit"),
        ]
        oy = start_y + 10
        for key, label in options:
            if label is None:
                continue
            line = f"  [{key}]  {label}"
            attr = color("GOLD") | curses.A_BOLD
            safe_addstr(stdscr, oy, cx - 8, line, attr)
            oy += 2

        stdscr.refresh()

    def draw_game_over(self, player: Player, score: int, rank: int) -> None:
        stdscr = self.stdscr
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        cx = w // 2

        lines = [
            ("GAME OVER", color("HP_LOW") | curses.A_BOLD),
            ("", 0),
            (f"{player.name} the {player.class_name}", color("PLAYER") | curses.A_BOLD),
            (f"Reached floor {player.floor}", color("STAIRS")),
            (f"Level {player.level}  |  {player.kills} kills  |  {player.gold} gold",
             color("UI")),
            ("", 0),
            (f"SCORE: {score}", color("GOLD") | curses.A_BOLD),
        ]
        if rank > 0:
            lines.append((f"Rank #{rank} on the leaderboard!", color("GOLD") | curses.A_BLINK))

        lines += [
            ("", 0),
            ("[ENTER] Return to menu", color("UI")),
        ]

        sy = max(2, h // 2 - len(lines) // 2)
        for i, (text, attr) in enumerate(lines):
            if text:
                safe_addstr(stdscr, sy + i, cx - len(text) // 2, text, attr)
        stdscr.refresh()

    def draw_victory(self, player: Player, score: int) -> None:
        stdscr = self.stdscr
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        cx = w // 2

        lines = [
            ("*** VICTORY! ***", color("GOLD") | curses.A_BOLD | curses.A_BLINK),
            ("", 0),
            ("The Demon Lord has fallen!", color("CRIT") | curses.A_BOLD),
            ("You have conquered the Kanistra Abyss!", color("TITLE")),
            ("", 0),
            (f"{player.name} the {player.class_name}", color("PLAYER") | curses.A_BOLD),
            (f"Level {player.level}  |  {player.kills} kills  |  {player.gold} gold",
             color("UI")),
            ("", 0),
            (f"FINAL SCORE: {score}", color("GOLD") | curses.A_BOLD),
            ("", 0),
            ("[ENTER] Return to menu", color("UI")),
        ]
        sy = max(2, h // 2 - len(lines) // 2)
        for i, (text, attr) in enumerate(lines):
            if text:
                safe_addstr(stdscr, sy + i, cx - len(text) // 2, text, attr)
        stdscr.refresh()

    def draw_high_scores(self, scores) -> None:
        stdscr = self.stdscr
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        cx = w // 2

        title = "─── HIGH SCORES ───"
        safe_addstr(stdscr, 2, cx - len(title) // 2, title,
                    color("GOLD") | curses.A_BOLD)

        header = f"{'Rank':<5} {'Name':<14} {'Class':<10} {'Score':>8} {'Floor':>6} {'Level':>6}"
        safe_addstr(stdscr, 4, cx - len(header) // 2, header, color("UI") | curses.A_UNDERLINE)

        for i, entry in enumerate(scores[:10]):
            row = 5 + i
            line = (f"#{i+1:<4} {entry.name:<14} {entry.char_class:<10} "
                    f"{entry.score:>8} {entry.floor_reached:>6} {entry.level:>6}")
            attr = color("GOLD") if i == 0 else color("UI")
            safe_addstr(stdscr, row, cx - len(header) // 2, line, attr)

        safe_addstr(stdscr, 17, cx - 10, "[ANY KEY] Return", color("UI"))
        stdscr.refresh()

    def draw_inventory(self, player: Player) -> Optional[str]:
        """Draw inventory screen. Returns selected item key or None."""
        stdscr = self.stdscr
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        draw_box(stdscr, 0, 0, h - 1, w - 1, color("UI"), "INVENTORY")

        # Equipment summary
        safe_addstr(stdscr, 2, 2, "EQUIPPED:", color("UI") | curses.A_BOLD)
        weap_str = f"Weapon: {player.equipment.weapon.name}" if player.equipment.weapon else "Weapon: ---"
        arm_str  = f"Armor:  {player.equipment.armor.name}"  if player.equipment.armor  else "Armor:  ---"
        ring_str = f"Ring:   {player.equipment.ring.name}"   if player.equipment.ring   else "Ring:   ---"
        safe_addstr(stdscr, 3, 2, weap_str[:w-4], color("ITEM"))
        safe_addstr(stdscr, 4, 2, arm_str[:w-4],  color("ITEM"))
        safe_addstr(stdscr, 5, 2, ring_str[:w-4], color("GOLD"))
        safe_addstr(stdscr, 6, 2, "─" * (w - 4), color("UI") | curses.A_DIM)

        safe_addstr(stdscr, 7, 2, f"ITEMS ({len(player.inventory)}/26)  Gold: {player.gold}",
                    color("UI") | curses.A_BOLD)

        for i, item in enumerate(player.inventory):
            row = 8 + i
            if row >= h - 4:
                break
            idef = item.definition
            slot_info = ""
            if item == player.equipment.weapon:
                slot_info = "[W]"
            elif item == player.equipment.armor:
                slot_info = "[A]"
            elif item == player.equipment.ring:
                slot_info = "[R]"

            stats = ""
            if idef.attack_bonus:  stats += f"+{idef.attack_bonus}atk "
            if idef.defense_bonus: stats += f"+{idef.defense_bonus}def "
            if idef.hp_bonus:      stats += f"+{idef.hp_bonus}hp "
            if idef.effect_value:  stats += f"+{idef.effect_value}"

            line = f"  {chr(ord('a') + i)}) {item.symbol} {item.name:<20} {stats:<15} {slot_info}"
            safe_addstr(stdscr, row, 2, line[:w-4], color(item.color_key))

        cmds = "[a-z] Use/Equip  [e] Equip  [u] Unequip  [d] Drop  [ESC] Close"
        safe_addstr(stdscr, h - 3, 2, cmds[:w-4], color("UI") | curses.A_DIM)
        stdscr.refresh()
        return None

    def draw_class_select(self) -> str:
        """Class selection screen. Returns chosen class key."""
        stdscr = self.stdscr
        classes = ["warrior", "mage", "rogue", "paladin"]
        selected = 0

        while True:
            stdscr.erase()
            h, w = stdscr.getmaxyx()
            cx = w // 2

            title = "CHOOSE YOUR CLASS"
            safe_addstr(stdscr, 2, cx - len(title) // 2, title,
                        color("TITLE") | curses.A_BOLD)

            for i, ck in enumerate(classes):
                cdef = CLASS_DEFS[ck]
                y = 5 + i * 7
                is_sel = (i == selected)
                box_attr = color("GOLD") if is_sel else color("UI")
                draw_box(stdscr, y, cx - 28, 6, 56, box_attr)
                attr = color("PLAYER") | curses.A_BOLD if is_sel else color("UI")
                safe_addstr(stdscr, y + 1, cx - 26,
                             f"[{i+1}] {cdef.name.upper()}", attr | curses.A_BOLD)
                safe_addstr(stdscr, y + 2, cx - 26,
                             cdef.description[:50], color("UI") | curses.A_DIM)
                safe_addstr(stdscr, y + 3, cx - 26,
                             f"HP:{cdef.base_hp}  MP:{cdef.base_mana}  "
                             f"ATK:{cdef.base_attack}  DEF:{cdef.base_defense}",
                             color("UI"))
                safe_addstr(stdscr, y + 4, cx - 26,
                             f'Skills: {", ".join(SKILL_DEFS[sk].name for sk in cdef.skills[:4])}',
                             color("ITEM") | curses.A_DIM)

            safe_addstr(stdscr, h - 3, cx - 20,
                        "↑↓/1-4: Select   ENTER: Confirm",
                        color("UI") | curses.A_DIM)
            stdscr.refresh()

            key = stdscr.getch()
            if key in (ord('1'), ord('2'), ord('3'), ord('4')):
                selected = key - ord('1')
            elif key in (curses.KEY_UP, ord('k')) and selected > 0:
                selected -= 1
            elif key in (curses.KEY_DOWN, ord('j')) and selected < len(classes) - 1:
                selected += 1
            elif key in (curses.KEY_ENTER, ord('\n'), ord('\r'), ord(' ')):
                return classes[selected]

    def draw_name_input(self, class_key: str) -> str:
        """Name input screen. Returns entered name."""
        stdscr = self.stdscr
        cdef = CLASS_DEFS[class_key]
        name = ""
        curses.curs_set(1)

        while True:
            stdscr.erase()
            h, w = stdscr.getmaxyx()
            cx = w // 2

            safe_addstr(stdscr, h // 2 - 3, cx - 15,
                        f"Enter name for your {cdef.name}:",
                        color("TITLE") | curses.A_BOLD)
            draw_box(stdscr, h // 2 - 1, cx - 12, 3, 24, color("UI"))
            safe_addstr(stdscr, h // 2, cx - 10, f"{name}_"[:20],
                        color("PLAYER") | curses.A_BOLD)
            safe_addstr(stdscr, h // 2 + 3, cx - 15,
                        "ENTER to confirm (min 1 char)", color("UI") | curses.A_DIM)
            stdscr.refresh()

            key = stdscr.getch()
            if key in (curses.KEY_ENTER, ord('\n'), ord('\r')) and len(name) >= 1:
                break
            elif key in (curses.KEY_BACKSPACE, 127, 8) and name:
                name = name[:-1]
            elif 32 <= key <= 126 and len(name) < 16:
                name += chr(key)

        curses.curs_set(0)
        return name.strip() or "Adventurer"

    def draw_shop(self, player: Player, stock: List[str]) -> None:
        """Shop screen. Returns when player exits."""
        stdscr = self.stdscr
        selected = 0

        while True:
            stdscr.erase()
            h, w = stdscr.getmaxyx()

            draw_box(stdscr, 0, 0, h - 1, w - 1, color("SHOP"), "KANISTRA SHOP")
            safe_addstr(stdscr, 2, 2, f"Gold: {player.gold}", color("GOLD") | curses.A_BOLD)
            safe_addstr(stdscr, 3, 2, "─" * (w - 4), color("UI") | curses.A_DIM)
            safe_addstr(stdscr, 4, 2, f"{'Item':<22} {'Cost':>6}  {'Description':<30}",
                        color("UI") | curses.A_UNDERLINE)

            for i, key in enumerate(stock):
                if key not in ITEM_DEFS:
                    continue
                idef = ITEM_DEFS[key]
                row = 5 + i
                if row >= h - 5:
                    break
                is_sel = (i == selected)
                attr = color("GOLD") | curses.A_BOLD if is_sel else color(idef.color_key)
                prefix = ">" if is_sel else " "
                line = f"{prefix} {idef.name:<22} {idef.value:>5}g  {idef.description[:28]}"
                safe_addstr(stdscr, row, 2, line[:w-4], attr)

            safe_addstr(stdscr, h - 4, 2,
                        "↑↓: Navigate  ENTER/B: Buy  ESC/Q: Leave",
                        color("UI") | curses.A_DIM)
            stdscr.refresh()

            key_ch = stdscr.getch()
            if key_ch in (curses.KEY_UP, ord('w')) and selected > 0:
                selected -= 1
            elif key_ch in (curses.KEY_DOWN, ord('s')) and selected < len(stock) - 1:
                selected += 1
            elif key_ch in (curses.KEY_ENTER, ord('\n'), ord('\r'), ord('b'), ord('B')):
                if 0 <= selected < len(stock):
                    item_key = stock[selected]
                    if item_key in ITEM_DEFS:
                        idef = ITEM_DEFS[item_key]
                        if player.gold >= idef.value:
                            if len(player.inventory) < 26:
                                player.gold -= idef.value
                                from entities import Item as ItemCls
                                player.add_item(ItemCls(key=item_key))
                                # brief confirmation
                                safe_addstr(stdscr, h - 3, 2,
                                            f"Purchased {idef.name}!",
                                            color("HP_HIGH") | curses.A_BOLD)
                                stdscr.refresh()
                                curses.napms(600)
                            else:
                                safe_addstr(stdscr, h - 3, 2, "Inventory full!",
                                            color("HP_LOW"))
                                stdscr.refresh()
                                curses.napms(600)
                        else:
                            safe_addstr(stdscr, h - 3, 2, "Not enough gold!",
                                        color("HP_LOW"))
                            stdscr.refresh()
                            curses.napms(600)
            elif key_ch in (27, ord('q'), ord('Q')):
                break

    def draw_stat_allocation(self, player: Player) -> None:
        """Stat point allocation screen."""
        stdscr = self.stdscr

        while player.stat_points > 0:
            stdscr.erase()
            h, w = stdscr.getmaxyx()
            cx = w // 2

            draw_box(stdscr, h // 2 - 7, cx - 20, 14, 40,
                     color("GOLD"), "LEVEL UP!")
            y = h // 2 - 5
            safe_addstr(stdscr, y, cx - 18,
                        f"Level {player.level}!  Points remaining: {player.stat_points}",
                        color("GOLD") | curses.A_BOLD)
            y += 2
            opts = [
                ("H", "hp",      f"+10 Max HP    (now {player.max_hp})"),
                ("M", "mana",    f"+10 Max Mana  (now {player.max_mana})"),
                ("A", "attack",  f"+2 Attack     (now {player.base_attack})"),
                ("D", "defense", f"+1 Defense    (now {player.base_defense})"),
            ]
            for key_c, stat, desc in opts:
                safe_addstr(stdscr, y, cx - 16,
                             f"[{key_c}] {desc}", color("UI"))
                y += 1
            y += 1
            safe_addstr(stdscr, y, cx - 16, "[ESC] Close", color("UI") | curses.A_DIM)
            stdscr.refresh()

            key_ch = stdscr.getch()
            if key_ch in (ord('h'), ord('H')):
                player.spend_stat_point("hp")
            elif key_ch in (ord('m'), ord('M')):
                player.spend_stat_point("mana")
            elif key_ch in (ord('a'), ord('A')):
                player.spend_stat_point("attack")
            elif key_ch in (ord('d'), ord('D')):
                player.spend_stat_point("defense")
            elif key_ch == 27:
                break

    def draw_message_box(self, title: str, lines: List[str],
                          color_key: str = "UI") -> None:
        stdscr = self.stdscr
        h, w = stdscr.getmaxyx()
        cx = w // 2
        box_h = len(lines) + 4
        box_w = max(len(title) + 4, max((len(l) for l in lines), default=20) + 4, 30)
        by = h // 2 - box_h // 2
        bx = cx - box_w // 2

        draw_box(stdscr, by, bx, box_h, box_w, color(color_key), title)
        for i, line in enumerate(lines):
            safe_addstr(stdscr, by + 2 + i, bx + 2, line[:box_w - 4], color(color_key))
        stdscr.refresh()
        stdscr.getch()
