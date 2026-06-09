"""
KANISTRA ABYSS - Entities: Player, Enemy, Item
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from data import (
    CLASS_DEFS, ClassDef, ENEMY_DEFS, EnemyDef,
    ITEM_DEFS, ItemDef, SKILL_DEFS, SkillDef,
    STATUS_DEFS, XP_TABLE, MAX_LEVEL,
)


# ─────────────────────────────────────────────
#  Status Effect instance
# ─────────────────────────────────────────────
@dataclass
class StatusEffect:
    key: str
    turns_remaining: int

    @property
    def definition(self):
        return STATUS_DEFS[self.key]

    @property
    def name(self) -> str:
        return STATUS_DEFS[self.key].name

    @property
    def symbol(self) -> str:
        return STATUS_DEFS[self.key].symbol

    @property
    def color_key(self) -> str:
        return STATUS_DEFS[self.key].color_key


# ─────────────────────────────────────────────
#  Item instance
# ─────────────────────────────────────────────
@dataclass
class Item:
    key: str
    identified: bool = True   # scrolls start unidentified in classic RL, but we keep simple

    @property
    def definition(self) -> ItemDef:
        return ITEM_DEFS[self.key]

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    def symbol(self) -> str:
        return self.definition.symbol

    @property
    def color_key(self) -> str:
        return self.definition.color_key

    @property
    def item_type(self) -> str:
        return self.definition.item_type


# ─────────────────────────────────────────────
#  Equipment Slots
# ─────────────────────────────────────────────
@dataclass
class Equipment:
    weapon: Optional[Item] = None
    armor:  Optional[Item] = None
    ring:   Optional[Item] = None

    def attack_bonus(self) -> int:
        total = 0
        for slot in (self.weapon, self.armor, self.ring):
            if slot:
                total += slot.definition.attack_bonus
        return total

    def defense_bonus(self) -> int:
        total = 0
        for slot in (self.weapon, self.armor, self.ring):
            if slot:
                total += slot.definition.defense_bonus
        return total

    def hp_bonus(self) -> int:
        total = 0
        for slot in (self.weapon, self.armor, self.ring):
            if slot:
                total += slot.definition.hp_bonus
        return total

    def mana_bonus(self) -> int:
        total = 0
        for slot in (self.weapon, self.armor, self.ring):
            if slot:
                total += slot.definition.mana_bonus
        return total

    def crit_bonus(self) -> float:
        total = 0.0
        for slot in (self.weapon, self.armor, self.ring):
            if slot:
                total += slot.definition.crit_bonus
        return total

    def dodge_bonus(self) -> float:
        total = 0.0
        for slot in (self.weapon, self.armor, self.ring):
            if slot:
                total += slot.definition.dodge_bonus
        return total


# ─────────────────────────────────────────────
#  Base Entity
# ─────────────────────────────────────────────
class Entity:
    def __init__(self, x: int, y: int, name: str, symbol: str,
                 color_key: str, hp: int, attack: int, defense: int):
        self.x = x
        self.y = y
        self.name = name
        self.symbol = symbol
        self.color_key = color_key
        self.max_hp = hp
        self.hp = hp
        self.base_attack = attack
        self.base_defense = defense
        self.statuses: List[StatusEffect] = []
        self.alive: bool = True

    # ── Status helpers ──────────────────────
    def has_status(self, key: str) -> bool:
        return any(s.key == key for s in self.statuses)

    def apply_status(self, key: str, duration: Optional[int] = None) -> None:
        dur = duration if duration is not None else STATUS_DEFS[key].duration_default
        for s in self.statuses:
            if s.key == key:
                s.turns_remaining = max(s.turns_remaining, dur)
                return
        self.statuses.append(StatusEffect(key=key, turns_remaining=dur))

    def remove_status(self, key: str) -> None:
        self.statuses = [s for s in self.statuses if s.key != key]

    def tick_statuses(self) -> List[str]:
        """Advance all statuses by one turn. Returns list of log messages."""
        messages: List[str] = []
        expired = []
        for s in self.statuses:
            sdef = s.definition
            dmg = sdef.tick_damage
            if dmg > 0:
                self.hp = max(0, self.hp - dmg)
                messages.append(f"{self.name} takes {dmg} {sdef.name} damage!")
                if self.hp <= 0:
                    self.alive = False
                    messages.append(f"{self.name} succumbs to {sdef.name}!")
            elif dmg < 0:
                heal = abs(dmg)
                self.hp = min(self.max_hp, self.hp + heal)
                messages.append(f"{self.name} regenerates {heal} HP.")
            s.turns_remaining -= 1
            if s.turns_remaining <= 0:
                expired.append(s.key)
        for k in expired:
            messages.append(f"{self.name} is no longer {STATUS_DEFS[k].name}.")
            self.remove_status(k)
        return messages

    @property
    def effective_attack(self) -> int:
        base = self.base_attack
        mult = 1.0
        for s in self.statuses:
            mult *= s.definition.stat_modifier.get("attack", 1.0)
        return max(1, int(base * mult))

    @property
    def effective_defense(self) -> int:
        base = self.base_defense
        mult = 1.0
        for s in self.statuses:
            mult *= s.definition.stat_modifier.get("defense", 1.0)
        return max(0, int(base * mult))

    @property
    def is_frozen(self) -> bool:
        return self.has_status("frozen")

    @property
    def is_stunned(self) -> bool:
        return self.has_status("stunned")

    @property
    def hp_pct(self) -> float:
        return self.hp / self.max_hp if self.max_hp > 0 else 0.0


# ─────────────────────────────────────────────
#  Player
# ─────────────────────────────────────────────
class Player(Entity):
    def __init__(self, class_key: str, name: str, x: int = 0, y: int = 0):
        cdef: ClassDef = CLASS_DEFS[class_key]
        super().__init__(
            x=x, y=y,
            name=name,
            symbol=cdef.symbol,
            color_key=cdef.color_key,
            hp=cdef.base_hp,
            attack=cdef.base_attack,
            defense=cdef.base_defense,
        )
        self.class_key   = class_key
        self.class_name  = cdef.name
        self.max_mana    = cdef.base_mana
        self.mana        = cdef.base_mana
        self.base_speed  = cdef.base_speed
        self.level       = 1
        self.xp          = 0
        self.xp_next     = XP_TABLE[1] if len(XP_TABLE) > 1 else 9999
        self.gold        = 0
        self.kills       = 0
        self.turns       = 0
        self.floor       = 1
        self.stat_points = 0
        # inventory
        self.inventory: List[Item] = []
        self.equipment   = Equipment()
        # skills: list of (key, cooldown_remaining)
        self.skill_keys: List[str] = list(cdef.skills)
        self.skill_cooldowns: Dict[str, int] = {k: 0 for k in cdef.skills}
        # dodge chance
        self.base_dodge  = 0.05 if class_key == "rogue" else 0.03
        # crit chance
        self.base_crit   = 0.10 if class_key == "rogue" else 0.05

    # ── Derived stats ────────────────────────
    @property
    def attack(self) -> int:
        return self.base_attack + self.equipment.attack_bonus()

    @property
    def defense(self) -> int:
        return self.base_defense + self.equipment.defense_bonus()

    @property
    def effective_attack(self) -> int:
        base = self.attack
        mult = 1.0
        for s in self.statuses:
            mult *= s.definition.stat_modifier.get("attack", 1.0)
        return max(1, int(base * mult))

    @property
    def effective_defense(self) -> int:
        base = self.defense
        mult = 1.0
        for s in self.statuses:
            mult *= s.definition.stat_modifier.get("defense", 1.0)
        return max(0, int(base * mult))

    @property
    def crit_chance(self) -> float:
        return min(0.80, self.base_crit + self.equipment.crit_bonus())

    @property
    def dodge_chance(self) -> float:
        return min(0.60, self.base_dodge + self.equipment.dodge_bonus())

    @property
    def max_hp_total(self) -> int:
        return self.max_hp + self.equipment.hp_bonus()

    @property
    def max_mana_total(self) -> int:
        return self.max_mana + self.equipment.mana_bonus()

    # ── XP / leveling ───────────────────────
    def gain_xp(self, amount: int) -> List[str]:
        if self.level >= MAX_LEVEL:
            return []
        self.xp += amount
        msgs: List[str] = []
        while self.level < MAX_LEVEL and self.xp >= self.xp_next:
            self.xp -= self.xp_next
            self.level += 1
            self.stat_points += 3
            cdef = CLASS_DEFS[self.class_key]
            self.max_hp    += cdef.hp_per_level
            self.hp         = min(self.hp + cdef.hp_per_level, self.max_hp_total)
            self.max_mana  += cdef.mana_per_level
            self.mana       = min(self.mana + cdef.mana_per_level, self.max_mana_total)
            self.base_attack   = int(self.base_attack + cdef.attack_per_level)
            self.base_defense  = int(self.base_defense + cdef.defense_per_level)
            if self.level < MAX_LEVEL:
                self.xp_next = XP_TABLE[self.level]
            else:
                self.xp_next = 0
            msgs.append(f"*** LEVEL UP! You are now level {self.level}! (+3 stat points)")
        return msgs

    def spend_stat_point(self, stat: str) -> str:
        if self.stat_points <= 0:
            return "No stat points available!"
        self.stat_points -= 1
        if stat == "hp":
            self.max_hp += 10
            self.hp = min(self.hp + 10, self.max_hp_total)
            return "+10 Max HP"
        elif stat == "mana":
            self.max_mana += 10
            self.mana = min(self.mana + 10, self.max_mana_total)
            return "+10 Max Mana"
        elif stat == "attack":
            self.base_attack += 2
            return "+2 Attack"
        elif stat == "defense":
            self.base_defense += 1
            return "+1 Defense"
        return "Unknown stat"

    # ── Inventory ───────────────────────────
    def add_item(self, item: Item) -> bool:
        if len(self.inventory) >= 26:
            return False
        self.inventory.append(item)
        return True

    def remove_item(self, item: Item) -> None:
        if item in self.inventory:
            self.inventory.remove(item)

    def equip_item(self, item: Item) -> Tuple[str, Optional[Item]]:
        """Equip item; returns (message, unequipped_old_item_or_None)."""
        itype = item.item_type
        old: Optional[Item] = None
        if itype == "weapon":
            old = self.equipment.weapon
            self.equipment.weapon = item
        elif itype == "armor":
            old = self.equipment.armor
            self.equipment.armor = item
        elif itype == "ring":
            old = self.equipment.ring
            self.equipment.ring = item
        else:
            return (f"Cannot equip {item.name}.", None)
        self.remove_item(item)
        if old:
            self.add_item(old)
        return (f"Equipped {item.name}.", old)

    def unequip_slot(self, slot: str) -> Tuple[str, Optional[Item]]:
        item: Optional[Item] = getattr(self.equipment, slot, None)
        if item is None:
            return ("Nothing equipped in that slot.", None)
        if len(self.inventory) >= 26:
            return ("Inventory full!", None)
        setattr(self.equipment, slot, None)
        self.add_item(item)
        return (f"Unequipped {item.name}.", item)

    # ── Skill helpers ───────────────────────
    def skill_ready(self, key: str) -> bool:
        return self.skill_cooldowns.get(key, 0) == 0

    def start_skill_cooldown(self, key: str) -> None:
        cd = SKILL_DEFS[key].cooldown
        self.skill_cooldowns[key] = cd

    def tick_cooldowns(self) -> None:
        for k in self.skill_cooldowns:
            if self.skill_cooldowns[k] > 0:
                self.skill_cooldowns[k] -= 1

    def mana_regen(self) -> None:
        """Passive mana regen per turn."""
        regen = 2 if self.class_key == "mage" else 1
        self.mana = min(self.max_mana_total, self.mana + regen)

    # ── Serialization ───────────────────────
    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x, "y": self.y,
            "name": self.name,
            "class_key": self.class_key,
            "hp": self.hp, "max_hp": self.max_hp,
            "mana": self.mana, "max_mana": self.max_mana,
            "base_attack": self.base_attack,
            "base_defense": self.base_defense,
            "level": self.level, "xp": self.xp, "xp_next": self.xp_next,
            "gold": self.gold, "kills": self.kills, "turns": self.turns,
            "floor": self.floor, "stat_points": self.stat_points,
            "inventory": [{"key": i.key, "identified": i.identified}
                          for i in self.inventory],
            "equipment": {
                "weapon": {"key": self.equipment.weapon.key} if self.equipment.weapon else None,
                "armor":  {"key": self.equipment.armor.key}  if self.equipment.armor  else None,
                "ring":   {"key": self.equipment.ring.key}   if self.equipment.ring   else None,
            },
            "skill_cooldowns": self.skill_cooldowns,
            "statuses": [{"key": s.key, "turns_remaining": s.turns_remaining}
                         for s in self.statuses],
            "base_dodge": self.base_dodge,
            "base_crit": self.base_crit,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Player":
        p = cls(class_key=d["class_key"], name=d["name"], x=d["x"], y=d["y"])
        p.hp            = d["hp"]
        p.max_hp        = d["max_hp"]
        p.mana          = d["mana"]
        p.max_mana      = d["max_mana"]
        p.base_attack   = d["base_attack"]
        p.base_defense  = d["base_defense"]
        p.level         = d["level"]
        p.xp            = d["xp"]
        p.xp_next       = d["xp_next"]
        p.gold          = d["gold"]
        p.kills         = d["kills"]
        p.turns         = d["turns"]
        p.floor         = d["floor"]
        p.stat_points   = d.get("stat_points", 0)
        p.base_dodge    = d.get("base_dodge", 0.05)
        p.base_crit     = d.get("base_crit", 0.05)
        p.inventory     = [Item(key=i["key"], identified=i.get("identified", True))
                           for i in d.get("inventory", [])]
        eq = d.get("equipment", {})
        p.equipment.weapon = Item(key=eq["weapon"]["key"]) if eq.get("weapon") else None
        p.equipment.armor  = Item(key=eq["armor"]["key"])  if eq.get("armor")  else None
        p.equipment.ring   = Item(key=eq["ring"]["key"])   if eq.get("ring")   else None
        p.skill_cooldowns  = d.get("skill_cooldowns", {k: 0 for k in p.skill_keys})
        for s in d.get("statuses", []):
            p.statuses.append(StatusEffect(key=s["key"], turns_remaining=s["turns_remaining"]))
        return p


# ─────────────────────────────────────────────
#  Enemy
# ─────────────────────────────────────────────
class Enemy(Entity):
    def __init__(self, key: str, x: int, y: int, floor_num: int = 1):
        edef: EnemyDef = ENEMY_DEFS[key]
        # Scale stats with floor
        scale = 1.0 + (floor_num - edef.min_floor) * 0.08
        scale = max(1.0, scale)
        hp    = int(edef.hp * scale)
        atk   = int(edef.attack * scale)
        dfn   = int(edef.defense * scale)
        xp    = int(edef.xp * scale)
        super().__init__(
            x=x, y=y,
            name=edef.name,
            symbol=edef.symbol,
            color_key=edef.color_key,
            hp=hp, attack=atk, defense=dfn,
        )
        self.key         = key
        self.xp_value    = xp
        self.loot_table  = edef.loot_table
        self.abilities   = list(edef.abilities)
        self.is_boss     = edef.is_boss
        self.aggro_range = edef.aggro_range
        self.alerted     = False
        self.turn_timer  = 0       # for speed > 1
        self.ability_cooldowns: Dict[str, int] = {a: 0 for a in edef.abilities}
        self.rng         = random.Random()

    def choose_ability(self) -> Optional[str]:
        """Pick a ready ability at random."""
        ready = [a for a in self.abilities if self.ability_cooldowns.get(a, 0) == 0]
        if not ready:
            return None
        if self.rng.random() < 0.35:
            return self.rng.choice(ready)
        return None

    def tick_ab_cooldowns(self) -> None:
        for k in self.ability_cooldowns:
            if self.ability_cooldowns[k] > 0:
                self.ability_cooldowns[k] -= 1

    def roll_loot(self, rng: random.Random) -> List[str]:
        """Roll loot table; return list of item keys dropped."""
        drops: List[str] = []
        for entry in self.loot_table:
            parts = entry.split(":")
            item_key = parts[0]
            chance = float(parts[1]) if len(parts) > 1 else 0.5
            if item_key in ITEM_DEFS and rng.random() < chance:
                drops.append(item_key)
        return drops

    def move_towards(self, tx: int, ty: int,
                     walkable_fn) -> Tuple[int, int]:
        """Simple greedy approach toward target."""
        dx = tx - self.x
        dy = ty - self.y
        moves: List[Tuple[int, int]] = []
        if dx != 0:
            moves.append((self.x + (1 if dx > 0 else -1), self.y))
        if dy != 0:
            moves.append((self.x, self.y + (1 if dy > 0 else -1)))
        # shuffle for variety
        self.rng.shuffle(moves)
        for nx, ny in moves:
            if walkable_fn(nx, ny):
                return (nx, ny)
        return (self.x, self.y)


# ─────────────────────────────────────────────
#  Floor Item (item lying on the ground)
# ─────────────────────────────────────────────
@dataclass
class FloorItem:
    x: int
    y: int
    item: Item
