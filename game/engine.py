"""
KANISTRA ABYSS - Game Engine
Core game loop, state management, input handling.
"""
from __future__ import annotations
import curses
import random
import math
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from data import (
    ENEMY_DEFS, ITEM_DEFS, SKILL_DEFS, STATUS_DEFS,
    SHOP_STOCK, MAX_FLOOR, XP_TABLE, TILE_CHARS,
)
from dungeon import DungeonFloor
from entities import Player, Enemy, Item, FloorItem, Equipment
from combat import CombatEngine, CombatResult
from ui import Renderer
import save as Save


FOV_RADIUS = 8
MAX_LOG = 200


@dataclass
class GameState:
    player:       Player
    floor:        DungeonFloor
    enemies:      List[Enemy]           = field(default_factory=list)
    floor_items:  List[FloorItem]       = field(default_factory=list)
    log:          List[str]             = field(default_factory=list)
    target_enemy: Optional[Enemy]       = None
    rng:          random.Random         = field(default_factory=random.Random)
    turn:         int                   = 0
    game_over:    bool                  = False
    won:          bool                  = False
    floor_cache:  Dict[int, dict]       = field(default_factory=dict)


class GameEngine:
    def __init__(self, stdscr):
        self.stdscr   = stdscr
        self.renderer = Renderer(stdscr)
        self.combat   = CombatEngine()
        self.state: Optional[GameState] = None
        self.rng      = random.Random()

    # ─────────────────────────────────────────
    #  Initialise new game
    # ─────────────────────────────────────────
    def new_game(self, class_key: str, player_name: str) -> None:
        self.rng = random.Random()
        player = Player(class_key=class_key, name=player_name)
        floor  = self._generate_floor(1, self.rng)
        player.x, player.y = floor.player_start
        player.floor = 1

        state = GameState(player=player, floor=floor, rng=self.rng)
        self._spawn_entities(state)
        self.state = state
        self._recompute_fov()
        self.log(f"Welcome to the Kanistra Abyss, {player_name}!")
        self.log("Press '?' for help, 'i' for inventory, '>' to descend stairs.")

    def load_game(self) -> bool:
        data = Save.load_game()
        if not data:
            return False
        try:
            player = Player.from_dict(data["player"])
            self.rng = random.Random(data.get("rng_state", None))
            floor = self._generate_floor(player.floor, self.rng)
            state = GameState(player=player, floor=floor, rng=self.rng)
            self._spawn_entities(state)
            self.state = state
            self._recompute_fov()
            self.log("Game loaded.")
            return True
        except Exception as e:
            return False

    def save_game(self) -> bool:
        if not self.state:
            return False
        data = {
            "player": self.state.player.to_dict(),
        }
        return Save.save_game(data)

    # ─────────────────────────────────────────
    #  Floor management
    # ─────────────────────────────────────────
    def _generate_floor(self, floor_num: int, rng: random.Random) -> DungeonFloor:
        floor_rng = random.Random(rng.randint(0, 2**31))
        return DungeonFloor(floor_num, floor_rng)

    def _spawn_entities(self, state: GameState) -> None:
        """Populate enemies and items from floor spawn lists."""
        state.enemies.clear()
        state.floor_items.clear()

        for (ex, ey, ekey) in state.floor.enemy_spawns:
            if ekey in ENEMY_DEFS:
                enemy = Enemy(ekey, ex, ey, state.floor.floor_num)
                enemy.rng = random.Random(state.rng.randint(0, 2**31))
                state.enemies.append(enemy)

        for (ix, iy, ikey) in state.floor.item_spawns:
            if ikey in ITEM_DEFS:
                fi = FloorItem(x=ix, y=iy, item=Item(key=ikey))
                state.floor_items.append(fi)

    def _descend(self) -> None:
        state = self.state
        p = state.player
        if (p.x, p.y) != state.floor.stairs_down:
            self.log("You must stand on the stairs (>) to descend.")
            return
        if p.floor >= MAX_FLOOR:
            self.log("You have reached the deepest level! (Use '>' to claim final victory)")
            state.won = True
            return

        p.floor += 1
        new_floor = self._generate_floor(p.floor, state.rng)
        p.x, p.y = new_floor.player_start
        state.floor = new_floor
        state.enemies.clear()
        state.floor_items.clear()
        state.target_enemy = None
        self._spawn_entities(state)
        self._recompute_fov()

        # Shop floor?
        if new_floor.is_shop_floor:
            self.log(f"Floor {p.floor}: You hear the tinkle of a merchant's bell...")
        else:
            self.log(f"You descend to floor {p.floor}. The darkness deepens...")

        # Boss warning
        boss_enemies = [e for e in state.enemies if e.is_boss]
        for b in boss_enemies:
            self.log(f"*** {b.name.upper()} lurks on this floor! ***")

    def _ascend(self) -> None:
        state = self.state
        p = state.player
        if state.floor.stairs_up is None or (p.x, p.y) != state.floor.stairs_up:
            self.log("No stairs up here.")
            return
        if p.floor <= 1:
            self.log("You are already on the first floor.")
            return
        p.floor -= 1
        new_floor = self._generate_floor(p.floor, state.rng)
        p.x, p.y = new_floor.stairs_down  # arrive at bottom of upper floor
        state.floor = new_floor
        state.enemies.clear()
        state.floor_items.clear()
        state.target_enemy = None
        self._spawn_entities(state)
        self._recompute_fov()
        self.log(f"You ascend to floor {p.floor}.")

    # ─────────────────────────────────────────
    #  FOV
    # ─────────────────────────────────────────
    def _recompute_fov(self) -> None:
        state = self.state
        state.floor.compute_fov(state.player.x, state.player.y, FOV_RADIUS)
        # Update enemy alert status
        for e in state.enemies:
            if e.alive:
                tile = state.floor.at(e.x, e.y)
                if tile.visible:
                    e.alerted = True
                    if state.target_enemy is None or not state.target_enemy.alive:
                        state.target_enemy = e

    # ─────────────────────────────────────────
    #  Movement & collision
    # ─────────────────────────────────────────
    def _try_move_player(self, dx: int, dy: int) -> bool:
        """Try to move player by (dx, dy). Returns True if turn consumed."""
        state = self.state
        p = state.player
        nx, ny = p.x + dx, p.y + dy

        tile = state.floor.at(nx, ny)
        if not tile.walkable:
            return False

        # Check for enemy at destination → melee attack
        target = next((e for e in state.enemies
                       if e.alive and e.x == nx and e.y == ny), None)
        if target:
            result = self.combat.player_attack(p, target)
            self._apply_result(result)
            return True

        # Move
        p.x, p.y = nx, ny

        # Auto-pick up gold
        gold_items = [fi for fi in state.floor_items
                      if fi.x == nx and fi.y == ny
                      and fi.item.definition.item_type == "gold"]
        for fi in gold_items:
            msgs = self.combat.use_item(p, fi.item)
            for m in msgs:
                self.log(m)
            state.floor_items.remove(fi)

        # Check shop trigger
        if state.floor.shop_pos == (nx, ny):
            self._enter_shop()

        return True

    def _enter_shop(self) -> None:
        state = self.state
        fn = state.player.floor
        if fn <= 5:
            stock_key = "early"
        elif fn <= 10:
            stock_key = "mid"
        else:
            stock_key = "late"
        stock = list(SHOP_STOCK[stock_key])
        self.log("You enter the Kanistra Shop. Browse wares with ↑↓, press B/ENTER to buy.")
        self.renderer.draw_shop(state.player, stock)

    # ─────────────────────────────────────────
    #  Item interaction
    # ─────────────────────────────────────────
    def _pick_up_item(self) -> None:
        state = self.state
        p = state.player
        here = [fi for fi in state.floor_items if fi.x == p.x and fi.y == p.y]
        if not here:
            self.log("Nothing here to pick up.")
            return
        fi = here[0]
        if fi.item.definition.item_type == "gold":
            msgs = self.combat.use_item(p, fi.item)
            for m in msgs:
                self.log(m)
            state.floor_items.remove(fi)
        elif p.add_item(fi.item):
            self.log(f"Picked up {fi.item.name}.")
            state.floor_items.remove(fi)
        else:
            self.log("Inventory is full!")

    def _use_item_at_index(self, idx: int) -> None:
        state = self.state
        p = state.player
        if idx < 0 or idx >= len(p.inventory):
            return
        item = p.inventory[idx]
        idef = item.definition

        if idef.item_type in ("weapon", "armor", "ring"):
            msg, old = p.equip_item(item)
            self.log(msg)
            return

        # consumable
        if idef.effect == "teleport":
            self._teleport_player()
            p.remove_item(item)
            self.log("You teleport to a random location!")
            return

        msgs = self.combat.use_item(p, item,
                                     dungeon=state.floor,
                                     enemies=state.enemies)
        for m in msgs:
            self.log(m)
        if idef.item_type in ("potion", "scroll"):
            p.remove_item(item)

    def _teleport_player(self) -> None:
        state = self.state
        p = state.player
        floor = state.floor
        for _ in range(200):
            room = state.rng.choice(floor.rooms)
            rx, ry, rw, rh = room
            nx = state.rng.randint(rx, rx + rw - 1)
            ny = state.rng.randint(ry, ry + rh - 1)
            if floor.at(nx, ny).walkable:
                p.x, p.y = nx, ny
                break

    # ─────────────────────────────────────────
    #  Skill usage
    # ─────────────────────────────────────────
    def _use_skill(self, skill_idx: int) -> None:
        state = self.state
        p = state.player
        if skill_idx < 0 or skill_idx >= len(p.skill_keys):
            return
        skill_key = p.skill_keys[skill_idx]
        sdef = SKILL_DEFS.get(skill_key)
        if sdef is None:
            return

        nearby = [e for e in state.enemies
                  if e.alive and max(abs(e.x - p.x), abs(e.y - p.y)) <= max(sdef.range_cells, sdef.aoe_radius, 1)]

        target = state.target_enemy if (state.target_enemy and state.target_enemy.alive) else None
        if target and not target.alive:
            # pick new target
            target = next((e for e in nearby if e.alive), None)
            state.target_enemy = target

        result = self.combat.player_use_skill(p, skill_key, target, nearby, state.floor)
        self._apply_result(result)

    # ─────────────────────────────────────────
    #  Apply combat result
    # ─────────────────────────────────────────
    def _apply_result(self, result: CombatResult) -> None:
        state = self.state
        for m in result.messages:
            self.log(m)

        if result.xp_gained > 0:
            lvl_msgs = state.player.gain_xp(result.xp_gained)
            for m in lvl_msgs:
                self.log(m)
            if lvl_msgs:  # level up!
                self.renderer.render(state)
                self.renderer.draw_stat_allocation(state.player)

        # Drop loot
        if result.loot_dropped and result.enemy:
            for ikey in result.loot_dropped:
                ex, ey = result.enemy.x, result.enemy.y
                fi = FloorItem(x=ex, y=ey, item=Item(key=ikey))
                state.floor_items.append(fi)
                self.log(f"{result.enemy.name} drops {ITEM_DEFS[ikey].name}!")

        if result.player_died:
            state.game_over = True

    # ─────────────────────────────────────────
    #  Enemy AI turn
    # ─────────────────────────────────────────
    def _do_enemy_turns(self) -> None:
        state = self.state
        p = state.player
        floor = state.floor

        for e in list(state.enemies):
            if not e.alive:
                continue
            if e.is_frozen or e.is_stunned:
                tick_msgs = e.tick_statuses()
                for m in tick_msgs:
                    self.log(m)
                e.tick_ab_cooldowns()
                continue

            # Check if alerted
            dist = max(abs(e.x - p.x), abs(e.y - p.y))
            tile = floor.at(e.x, e.y)
            if tile.visible or dist <= e.aggro_range:
                e.alerted = True

            if not e.alerted:
                # Wander randomly
                if state.rng.random() < 0.3:
                    dirs = [(0,1),(0,-1),(1,0),(-1,0)]
                    dx, dy = state.rng.choice(dirs)
                    nx, ny = e.x + dx, e.y + dy
                    if floor.at(nx, ny).walkable and not self._enemy_blocked(nx, ny, state):
                        e.x, e.y = nx, ny
            else:
                # Adjacent to player → attack
                if dist <= 1:
                    # Try ability
                    ability = e.choose_ability()
                    if ability:
                        result = self.combat.enemy_use_ability(e, ability, p)
                    else:
                        result = self.combat.enemy_attack(e, p)
                    self._apply_result(result)
                    if state.game_over:
                        break
                else:
                    # Move towards player
                    def can_walk(nx: int, ny: int) -> bool:
                        if not floor.at(nx, ny).walkable:
                            return False
                        return not self._enemy_blocked(nx, ny, state)
                    nx, ny = e.move_towards(p.x, p.y, can_walk)
                    e.x, e.y = nx, ny

            # Tick statuses
            tick_msgs = e.tick_statuses()
            for m in tick_msgs:
                self.log(m)
            if not e.alive:
                xp_msgs = p.gain_xp(e.xp_value)
                for m in xp_msgs:
                    self.log(m)
                if xp_msgs:
                    self.renderer.render(state)
                    self.renderer.draw_stat_allocation(p)
                # drop loot
                for ikey in e.roll_loot(state.rng):
                    fi = FloorItem(x=e.x, y=e.y, item=Item(key=ikey))
                    state.floor_items.append(fi)
                    self.log(f"{e.name} drops {ITEM_DEFS[ikey].name}!")

            e.tick_ab_cooldowns()

    def _enemy_blocked(self, nx: int, ny: int, state: GameState) -> bool:
        if (nx, ny) == (state.player.x, state.player.y):
            return True
        return any(e.alive and e.x == nx and e.y == ny
                   for e in state.enemies)

    # ─────────────────────────────────────────
    #  Player turn end
    # ─────────────────────────────────────────
    def _end_player_turn(self) -> None:
        state = self.state
        p = state.player
        p.turns += 1
        state.turn += 1

        # Tick player statuses
        tick_msgs = p.tick_statuses()
        for m in tick_msgs:
            self.log(m)

        # Mana regen
        p.mana_regen()

        # Tick skill cooldowns
        p.tick_cooldowns()

        # Check player alive
        if not p.alive or p.hp <= 0:
            state.game_over = True
            return

        # Remove dead enemies
        state.enemies = [e for e in state.enemies if e.alive]

        # Update target
        if state.target_enemy and not state.target_enemy.alive:
            alive_visible = [e for e in state.enemies
                             if e.alive and state.floor.at(e.x, e.y).visible]
            state.target_enemy = alive_visible[0] if alive_visible else None

        # Do enemy turns
        self._do_enemy_turns()

        # Re-FOV
        self._recompute_fov()

    # ─────────────────────────────────────────
    #  Inventory screen
    # ─────────────────────────────────────────
    def _show_inventory(self) -> None:
        state = self.state
        p = state.player

        while True:
            self.renderer.draw_inventory(p)
            key = self.stdscr.getch()

            if key == 27:  # ESC
                break

            # Letter a-z → select item
            if ord('a') <= key <= ord('z'):
                idx = key - ord('a')
                if idx < len(p.inventory):
                    item = p.inventory[idx]
                    self._use_item_at_index(idx)
                    self.renderer.draw_inventory(p)
            elif key in (ord('d'), ord('D')):
                self.log("Drop: press a-z to drop item.")
                # simple: next key is drop target
                drop_key = self.stdscr.getch()
                if ord('a') <= drop_key <= ord('z'):
                    idx = drop_key - ord('a')
                    if idx < len(p.inventory):
                        item = p.inventory[idx]
                        # drop at player position
                        fi = FloorItem(x=p.x, y=p.y, item=item)
                        state.floor_items.append(fi)
                        p.inventory.remove(item)
                        self.log(f"Dropped {item.name}.")
            elif key in (ord('q'), ord('Q')):
                break

    # ─────────────────────────────────────────
    #  Tab-cycle target
    # ─────────────────────────────────────────
    def _cycle_target(self) -> None:
        state = self.state
        visible = [e for e in state.enemies
                   if e.alive and state.floor.at(e.x, e.y).visible]
        if not visible:
            state.target_enemy = None
            return
        if state.target_enemy is None or state.target_enemy not in visible:
            state.target_enemy = visible[0]
        else:
            idx = visible.index(state.target_enemy)
            state.target_enemy = visible[(idx + 1) % len(visible)]
        self.log(f"Targeting: {state.target_enemy.name}")

    # ─────────────────────────────────────────
    #  Logging
    # ─────────────────────────────────────────
    def log(self, msg: str) -> None:
        state = self.state
        if state:
            state.log.append(msg)
            if len(state.log) > MAX_LOG:
                state.log = state.log[-MAX_LOG:]

    # ─────────────────────────────────────────
    #  Main game loop
    # ─────────────────────────────────────────
    def game_loop(self) -> None:
        state = self.state
        stdscr = self.stdscr
        stdscr.nodelay(False)
        stdscr.timeout(100)

        while not state.game_over and not state.won:
            self.renderer.render(state)
            self.renderer.draw_controls()

            key = stdscr.getch()
            if key == -1:
                continue

            turn_consumed = False

            # Movement
            if key in (ord('w'), curses.KEY_UP):
                turn_consumed = self._try_move_player(0, -1)
            elif key in (ord('s'), curses.KEY_DOWN):
                turn_consumed = self._try_move_player(0, 1)
            elif key in (ord('a'), curses.KEY_LEFT):
                turn_consumed = self._try_move_player(-1, 0)
            elif key in (ord('d'), curses.KEY_RIGHT):
                turn_consumed = self._try_move_player(1, 0)
            # Diagonal movement
            elif key == curses.KEY_HOME or key == ord('7'):
                turn_consumed = self._try_move_player(-1, -1)
            elif key == curses.KEY_PPAGE or key == ord('9'):
                turn_consumed = self._try_move_player(1, -1)
            elif key == curses.KEY_END or key == ord('1'):
                turn_consumed = self._try_move_player(-1, 1)
            elif key == curses.KEY_NPAGE or key == ord('3'):
                turn_consumed = self._try_move_player(1, 1)
            # Wait
            elif key in (ord('.'), curses.KEY_B2, ord('5')):
                turn_consumed = True
            # Skills 1-4
            elif key == ord('1'):
                self._use_skill(0)
                turn_consumed = True
            elif key == ord('2'):
                self._use_skill(1)
                turn_consumed = True
            elif key == ord('3'):
                self._use_skill(2)
                turn_consumed = True
            elif key == ord('4'):
                self._use_skill(3)
                turn_consumed = True
            # Inventory
            elif key == ord('i'):
                self._show_inventory()
                turn_consumed = False
            # Pick up
            elif key == ord('g'):
                self._pick_up_item()
                turn_consumed = True
            # Descend
            elif key == ord('>'):
                self._descend()
                turn_consumed = True
            # Ascend
            elif key == ord('<'):
                self._ascend()
                turn_consumed = True
            # Target cycle
            elif key == ord('\t'):
                self._cycle_target()
            # Save
            elif key == ord('S'):
                if self.save_game():
                    self.log("Game saved.")
                else:
                    self.log("Save failed!")
            # Help
            elif key == ord('?'):
                self._show_help()
            # Stat allocation
            elif key == ord('L'):
                if state.player.stat_points > 0:
                    self.renderer.draw_stat_allocation(state.player)
            # Quit
            elif key in (ord('q'), ord('Q')):
                if self._confirm_quit():
                    state.game_over = True
                    break

            if turn_consumed and not state.game_over and not state.won:
                self._end_player_turn()

            # Check victory condition
            if not state.game_over and state.won:
                break

        self.renderer.render(state)

    def _confirm_quit(self) -> bool:
        h, w = self.stdscr.getmaxyx()
        msg = "Quit game? [Y/N]"
        self.renderer.safe_addstr_center(h // 2, msg, curses.A_BOLD) if hasattr(
            self.renderer, "safe_addstr_center") else None
        from ui import safe_addstr
        safe_addstr(self.stdscr, h // 2, w // 2 - len(msg) // 2, msg,
                    curses.A_BOLD)
        self.stdscr.refresh()
        key = self.stdscr.getch()
        return key in (ord('y'), ord('Y'))

    def _show_help(self) -> None:
        lines = [
            "WASD / Arrow keys : Move / Attack (bump)",
            "1-4               : Use skills",
            "i                 : Open inventory",
            "g                 : Pick up item",
            ">                 : Descend stairs",
            "<                 : Ascend stairs",
            "TAB               : Cycle targets",
            "L                 : Spend stat points",
            "S                 : Save game",
            ".                 : Wait one turn",
            "q / Q             : Quit",
            "",
            "Bump into enemies to attack them.",
            "Skills use mana (MP). Cooldowns shown in brackets.",
            "Find the Demon Lord on floor 15 to win!",
        ]
        self.renderer.draw_message_box("HELP", lines, "UI")


# ─────────────────────────────────────────────
#  Top-level curses main
# ─────────────────────────────────────────────
def run_game(stdscr) -> None:
    """Entry point called by curses.wrapper."""
    curses.curs_set(0)
    try:
        curses.set_escdelay(25)
    except Exception:
        pass

    engine = GameEngine(stdscr)

    while True:
        has_save = Save.has_save()
        engine.renderer.draw_title_screen(has_save)
        key = stdscr.getch()

        if key in (ord('q'), ord('Q')):
            break

        elif key in (ord('n'), ord('N')):
            # New game
            class_key = engine.renderer.draw_class_select()
            name = engine.renderer.draw_name_input(class_key)
            Save.delete_save()
            engine.new_game(class_key, name)
            engine.game_loop()

            if engine.state:
                _handle_end_game(engine, stdscr)

        elif key in (ord('c'), ord('C')) and has_save:
            if engine.load_game():
                engine.game_loop()
                if engine.state:
                    _handle_end_game(engine, stdscr)
            else:
                from ui import safe_addstr
                h, w = stdscr.getmaxyx()
                safe_addstr(stdscr, h // 2, w // 2 - 10,
                            "Failed to load save!", curses.A_BOLD)
                stdscr.refresh()
                stdscr.getch()

        elif key in (ord('h'), ord('H')):
            scores = Save.load_hiscores()
            engine.renderer.draw_high_scores(scores)


def _handle_end_game(engine: GameEngine, stdscr) -> None:
    state = engine.state
    if not state:
        return
    p = state.player
    score = Save.compute_score(
        floor_reached=p.floor,
        level=p.level,
        kills=p.kills,
        gold=p.gold,
        turns=p.turns,
        is_winner=state.won,
    )
    rank = Save.add_hiscore(
        name=p.name,
        char_class=p.class_name,
        score=score,
        floor_reached=p.floor,
        level=p.level,
        kills=p.kills,
        gold=p.gold,
    )
    Save.delete_save()

    if state.won:
        engine.renderer.draw_victory(p, score)
    else:
        engine.renderer.draw_game_over(p, score, rank)

    stdscr.getch()
