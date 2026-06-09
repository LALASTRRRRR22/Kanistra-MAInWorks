"""
KANISTRA ABYSS - Dungeon Generation
Uses BSP (Binary Space Partitioning) for room placement.
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from data import TILE_CHARS, ENEMY_DEFS, ITEM_DEFS, EnemyDef, ItemDef


# ─────────────────────────────────────────────
#  Tile
# ─────────────────────────────────────────────
@dataclass
class Tile:
    char: str = TILE_CHARS["void"]
    walkable: bool = False
    transparent: bool = False
    explored: bool = False
    visible: bool = False
    blocks_movement: bool = True


# ─────────────────────────────────────────────
#  BSP Node
# ─────────────────────────────────────────────
@dataclass
class BSPNode:
    x: int
    y: int
    w: int
    h: int
    left: Optional["BSPNode"] = None
    right: Optional["BSPNode"] = None
    room: Optional[Tuple[int, int, int, int]] = None   # (x, y, w, h)


# ─────────────────────────────────────────────
#  Dungeon Floor
# ─────────────────────────────────────────────
MAP_WIDTH  = 80
MAP_HEIGHT = 45


class DungeonFloor:
    def __init__(self, floor_num: int, rng: random.Random):
        self.floor_num  = floor_num
        self.rng        = rng
        self.width      = MAP_WIDTH
        self.height     = MAP_HEIGHT
        self.tiles: List[List[Tile]] = []
        self.rooms: List[Tuple[int, int, int, int]] = []    # (x, y, w, h)
        self.corridors: List[List[Tuple[int, int]]] = []
        self.player_start: Tuple[int, int] = (0, 0)
        self.stairs_down: Tuple[int, int]  = (0, 0)
        self.stairs_up: Optional[Tuple[int, int]] = None
        self.enemy_spawns: List[Tuple[int, int, str]] = []  # (x, y, enemy_key)
        self.item_spawns:  List[Tuple[int, int, str]] = []  # (x, y, item_key)
        self.is_shop_floor: bool = floor_num > 0 and floor_num % 5 == 0
        self.shop_pos: Optional[Tuple[int, int]] = None

        self._generate()

    # ── Tile access ─────────────────────────
    def at(self, x: int, y: int) -> Tile:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return Tile()   # out-of-bounds → impassable void

    def set_tile(self, x: int, y: int, char: str,
                 walkable: bool = True, transparent: bool = True) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            t = self.tiles[y][x]
            t.char = char
            t.walkable = walkable
            t.transparent = transparent
            t.blocks_movement = not walkable

    # ── Generation pipeline ──────────────────
    def _generate(self) -> None:
        self._init_tiles()
        root = BSPNode(1, 1, self.width - 2, self.height - 2)
        self._split(root, depth=0, max_depth=5)
        self._collect_rooms(root)
        self._carve_rooms()
        self._connect_tree(root)
        self._place_stairs()
        self._place_entities()
        if self.is_shop_floor:
            self._place_shop()

    def _init_tiles(self) -> None:
        self.tiles = [
            [Tile(char=TILE_CHARS["wall"], walkable=False,
                  transparent=False, blocks_movement=True)
             for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def _split(self, node: BSPNode, depth: int, max_depth: int) -> None:
        if depth >= max_depth:
            return
        min_size = 8
        can_h = node.h >= min_size * 2 + 1
        can_v = node.w >= min_size * 2 + 1
        if not can_h and not can_v:
            return
        # choose split axis
        if can_h and can_v:
            horiz = self.rng.random() < 0.5
        elif can_h:
            horiz = True
        else:
            horiz = False

        if horiz:
            split = self.rng.randint(node.y + min_size, node.y + node.h - min_size)
            node.left  = BSPNode(node.x, node.y, node.w, split - node.y)
            node.right = BSPNode(node.x, split,  node.w, node.y + node.h - split)
        else:
            split = self.rng.randint(node.x + min_size, node.x + node.w - min_size)
            node.left  = BSPNode(node.x, node.y, split - node.x, node.h)
            node.right = BSPNode(split,  node.y, node.x + node.w - split, node.h)

        self._split(node.left,  depth + 1, max_depth)
        self._split(node.right, depth + 1, max_depth)

    def _collect_rooms(self, node: BSPNode) -> None:
        """Assign a room to every leaf node."""
        if node.left is None and node.right is None:
            # leaf – place room inside this partition
            margin = 1
            max_w = min(node.w - margin * 2, 16)
            max_h = min(node.h - margin * 2, 10)
            min_w, min_h = 4, 4
            if max_w < min_w or max_h < min_h:
                return
            rw = self.rng.randint(min_w, max_w)
            rh = self.rng.randint(min_h, max_h)
            rx = self.rng.randint(node.x + margin, node.x + node.w - rw - margin)
            ry = self.rng.randint(node.y + margin, node.y + node.h - rh - margin)
            node.room = (rx, ry, rw, rh)
            self.rooms.append(node.room)
        else:
            if node.left:
                self._collect_rooms(node.left)
            if node.right:
                self._collect_rooms(node.right)

    def _carve_rooms(self) -> None:
        for (rx, ry, rw, rh) in self.rooms:
            for y in range(ry, ry + rh):
                for x in range(rx, rx + rw):
                    self.set_tile(x, y, TILE_CHARS["floor"])

    def _room_center(self, room: Tuple[int, int, int, int]) -> Tuple[int, int]:
        rx, ry, rw, rh = room
        return (rx + rw // 2, ry + rh // 2)

    def _carve_corridor_h(self, x1: int, x2: int, y: int) -> None:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.set_tile(x, y, TILE_CHARS["floor"])

    def _carve_corridor_v(self, y1: int, y2: int, x: int) -> None:
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.set_tile(x, y, TILE_CHARS["floor"])

    def _connect_rooms(self, r1: Tuple[int, int, int, int],
                       r2: Tuple[int, int, int, int]) -> None:
        x1, y1 = self._room_center(r1)
        x2, y2 = self._room_center(r2)
        if self.rng.random() < 0.5:
            self._carve_corridor_h(x1, x2, y1)
            self._carve_corridor_v(y1, y2, x2)
        else:
            self._carve_corridor_v(y1, y2, x1)
            self._carve_corridor_h(x1, x2, y2)

    def _get_room(self, node: BSPNode) -> Optional[Tuple[int, int, int, int]]:
        """Return any room descendent from this node."""
        if node.room is not None:
            return node.room
        r = None
        if node.left:
            r = self._get_room(node.left)
        if r is None and node.right:
            r = self._get_room(node.right)
        return r

    def _connect_tree(self, node: BSPNode) -> None:
        if node.left is None or node.right is None:
            return
        self._connect_tree(node.left)
        self._connect_tree(node.right)
        rl = self._get_room(node.left)
        rr = self._get_room(node.right)
        if rl and rr:
            self._connect_rooms(rl, rr)

    def _random_floor_in_room(self, room: Tuple[int, int, int, int]) -> Tuple[int, int]:
        rx, ry, rw, rh = room
        return (self.rng.randint(rx, rx + rw - 1),
                self.rng.randint(ry, ry + rh - 1))

    def _place_stairs(self) -> None:
        if not self.rooms:
            return
        start_room = self.rooms[0]
        cx, cy = self._room_center(start_room)
        self.player_start = (cx, cy)
        if self.floor_num > 1:
            self.stairs_up = (cx, cy)
            self.set_tile(cx, cy, TILE_CHARS["stairs_up"], True, True)

        end_room = self.rooms[-1]
        ex, ey = self._room_center(end_room)
        self.stairs_down = (ex, ey)
        self.set_tile(ex, ey, TILE_CHARS["stairs_down"], True, True)

    # ── Enemy & item placement ───────────────
    def _enemy_candidates(self) -> List[str]:
        fn = self.floor_num
        candidates = []
        for key, edef in ENEMY_DEFS.items():
            if edef.is_boss:
                if edef.boss_floor == fn:
                    candidates.append(key)
            elif edef.min_floor <= fn <= edef.max_floor:
                candidates.append(key)
        return candidates if candidates else list(ENEMY_DEFS.keys())[:3]

    def _item_candidates(self) -> List[str]:
        fn = self.floor_num
        return [k for k, d in ITEM_DEFS.items()
                if d.min_floor <= fn and d.item_type != "gold"]

    def _occupied(self, x: int, y: int) -> bool:
        sx, sy = self.player_start
        if (x, y) == (sx, sy):
            return True
        dx, dy = self.stairs_down
        if (x, y) == (dx, dy):
            return True
        for (ex, ey, _) in self.enemy_spawns:
            if (x, y) == (ex, ey):
                return True
        for (ix, iy, _) in self.item_spawns:
            if (x, y) == (ix, iy):
                return True
        return False

    def _place_entities(self) -> None:
        fn = self.floor_num
        enemy_keys = self._enemy_candidates()
        item_keys  = self._item_candidates()

        # Bosses: exactly one in boss-floor boss room (last room)
        boss_keys = [k for k in enemy_keys if ENEMY_DEFS[k].is_boss]
        normal_keys = [k for k in enemy_keys if not ENEMY_DEFS[k].is_boss]

        # How many enemies per room (scales with floor)
        enemies_per_room = min(1 + fn // 3, 4)
        # skip first room (player start) and last room if shop
        rooms_to_populate = self.rooms[1:]
        if self.is_shop_floor and len(rooms_to_populate) > 1:
            rooms_to_populate = rooms_to_populate[:-1]

        for room in rooms_to_populate:
            n = self.rng.randint(0, enemies_per_room)
            for _ in range(n):
                if not normal_keys:
                    break
                key = self.rng.choice(normal_keys)
                for _try in range(10):
                    x, y = self._random_floor_in_room(room)
                    if not self._occupied(x, y):
                        self.enemy_spawns.append((x, y, key))
                        break

        # Place boss in a dedicated room (second-to-last to avoid shop/stairs clash)
        if boss_keys:
            bkey = boss_keys[0]
            # Pick the room farthest from player start that isn't the very last (shop) room
            if len(self.rooms) >= 3:
                boss_room_candidates = self.rooms[-(3):] if self.is_shop_floor else self.rooms[-2:]
                # choose the room with center NOT at stairs_down
                broom = None
                for candidate in reversed(boss_room_candidates):
                    cx, cy = self._room_center(candidate)
                    if (cx, cy) != self.stairs_down and (cx, cy) != self.player_start:
                        broom = candidate
                        break
                if broom is None:
                    broom = self.rooms[len(self.rooms) // 2]
            elif len(self.rooms) >= 2:
                broom = self.rooms[-1]
            else:
                broom = self.rooms[0]

            # Try placing boss at center, then random spots
            placed = False
            bx, by = self._room_center(broom)
            if not self._occupied(bx, by):
                self.enemy_spawns.append((bx, by, bkey))
                placed = True
            if not placed:
                for _try in range(20):
                    bx, by = self._random_floor_in_room(broom)
                    if not self._occupied(bx, by):
                        self.enemy_spawns.append((bx, by, bkey))
                        break

        # Items: scattered randomly
        n_items = 3 + fn // 2
        for _ in range(n_items):
            if not item_keys:
                break
            key = self.rng.choice(item_keys)
            room = self.rng.choice(self.rooms)
            for _try in range(10):
                x, y = self._random_floor_in_room(room)
                if not self._occupied(x, y):
                    self.item_spawns.append((x, y, key))
                    break

        # Gold drops
        for _ in range(2 + fn):
            gkey = self.rng.choice(["gold_small", "gold_med",
                                    "gold_large" if fn >= 4 else "gold_med"])
            room = self.rng.choice(self.rooms)
            for _try in range(10):
                x, y = self._random_floor_in_room(room)
                if not self._occupied(x, y):
                    self.item_spawns.append((x, y, gkey))
                    break

    def _place_shop(self) -> None:
        if len(self.rooms) < 2:
            return
        shop_room = self.rooms[-1]
        sx, sy = self._room_center(shop_room)
        self.shop_pos = (sx, sy)
        self.set_tile(sx, sy, TILE_CHARS["shop"], True, True)

    # ── Field-of-view (shadow casting) ───────
    def compute_fov(self, ox: int, oy: int, radius: int) -> None:
        """Recursive shadowcasting FOV."""
        # reset visible
        for row in self.tiles:
            for t in row:
                t.visible = False
        self.tiles[oy][ox].visible = True
        self.tiles[oy][ox].explored = True
        for octant in range(8):
            self._cast_light(ox, oy, radius, 1, 1.0, 0.0, octant)

    _OCTANT_TRANSFORMS = [
        ( 1,  0,  0,  1),
        ( 0,  1,  1,  0),
        ( 0, -1,  1,  0),
        (-1,  0,  0,  1),
        (-1,  0,  0, -1),
        ( 0, -1, -1,  0),
        ( 0,  1, -1,  0),
        ( 1,  0,  0, -1),
    ]

    def _cast_light(self, cx: int, cy: int, radius: int, row: int,
                    start: float, end: float, octant: int) -> None:
        if start < end:
            return
        xx, xy, yx, yy = self._OCTANT_TRANSFORMS[octant]
        radius_sq = radius * radius
        new_start = 0.0
        blocked = False
        for j in range(row, radius + 1):
            if blocked:
                break
            dy = -j
            for i in range(-j, 1):
                dx = i
                # map coords
                mx = cx + dx * xx + dy * xy
                my = cy + dx * yx + dy * yy
                if not (0 <= mx < self.width and 0 <= my < self.height):
                    continue
                l_slope = (dx - 0.5) / (dy + 0.5)
                r_slope = (dx + 0.5) / (dy - 0.5)
                if start < r_slope:
                    continue
                if end > l_slope:
                    break
                if dx * dx + dy * dy <= radius_sq:
                    self.tiles[my][mx].visible = True
                    self.tiles[my][mx].explored = True
                if blocked:
                    if not self.tiles[my][mx].transparent:
                        new_start = r_slope
                    else:
                        blocked = False
                        start = new_start
                else:
                    if not self.tiles[my][mx].transparent and j < radius:
                        blocked = True
                        self._cast_light(cx, cy, radius, j + 1,
                                         start, l_slope, octant)
                        new_start = r_slope
            if blocked:
                break

    def reveal_all(self) -> None:
        """Reveal entire map (scroll of mapping effect)."""
        for row in self.tiles:
            for t in row:
                t.explored = True
