"""
KANISTRA ABYSS - Game Data
All static game data: enemies, items, spells, character classes.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────
#  Colour / tile constants (used by rendering)
# ─────────────────────────────────────────────
COLORS = {
    "black":   (0, 0, 0),
    "white":   (255, 255, 255),
    "red":     (220, 50, 50),
    "green":   (50, 200, 50),
    "blue":    (50, 100, 220),
    "yellow":  (220, 220, 50),
    "cyan":    (50, 220, 220),
    "magenta": (180, 50, 180),
    "orange":  (220, 140, 50),
    "gray":    (140, 140, 140),
    "dark":    (60, 60, 60),
    "brown":   (140, 80, 40),
    "purple":  (120, 50, 180),
    "gold":    (255, 215, 0),
    "silver":  (192, 192, 192),
}

# Curses colour pair indices
CP = {
    "WALL":       1,
    "FLOOR":      2,
    "PLAYER":     3,
    "ENEMY":      4,
    "ITEM":       5,
    "UI":         6,
    "HP_HIGH":    7,
    "HP_MED":     8,
    "HP_LOW":     9,
    "MANA":       10,
    "STAIRS":     11,
    "EXPLORED":   12,
    "STATUS_BAD": 13,
    "STATUS_GOOD":14,
    "CRIT":       15,
    "BOSS":       16,
    "GOLD":       17,
    "TITLE":      18,
    "SHOP":       19,
    "LOG_OLD":    20,
}


# ─────────────────────────────────────────────
#  Status Effects
# ─────────────────────────────────────────────
@dataclass
class StatusDef:
    name: str
    symbol: str
    color_key: str
    duration_default: int
    tick_damage: int = 0          # damage per turn
    stat_modifier: Dict[str, float] = field(default_factory=dict)
    description: str = ""


STATUS_DEFS: Dict[str, StatusDef] = {
    "burning": StatusDef(
        name="Burning", symbol="🔥", color_key="STATUS_BAD",
        duration_default=4, tick_damage=3,
        stat_modifier={},
        description="Taking fire damage each turn"
    ),
    "frozen": StatusDef(
        name="Frozen", symbol="❄", color_key="STATUS_BAD",
        duration_default=3, tick_damage=0,
        stat_modifier={"speed": 0.0},
        description="Cannot move for duration"
    ),
    "poisoned": StatusDef(
        name="Poisoned", symbol="☠", color_key="STATUS_BAD",
        duration_default=6, tick_damage=2,
        stat_modifier={},
        description="Taking poison damage each turn"
    ),
    "stunned": StatusDef(
        name="Stunned", symbol="★", color_key="STATUS_BAD",
        duration_default=2, tick_damage=0,
        stat_modifier={"speed": 0.0},
        description="Skips turn"
    ),
    "blessed": StatusDef(
        name="Blessed", symbol="✦", color_key="STATUS_GOOD",
        duration_default=8, tick_damage=0,
        stat_modifier={"defense": 1.3, "attack": 1.2},
        description="+20% attack, +30% defense"
    ),
    "shielded": StatusDef(
        name="Shielded", symbol="🛡", color_key="STATUS_GOOD",
        duration_default=3, tick_damage=0,
        stat_modifier={"defense": 2.0},
        description="Defense doubled"
    ),
    "invisible": StatusDef(
        name="Invisible", symbol="👻", color_key="STATUS_GOOD",
        duration_default=5, tick_damage=0,
        stat_modifier={},
        description="Enemies cannot detect you"
    ),
    "regenerating": StatusDef(
        name="Regenerating", symbol="♥", color_key="STATUS_GOOD",
        duration_default=5, tick_damage=-3,   # negative = heal
        stat_modifier={},
        description="Recovering HP each turn"
    ),
    "weakened": StatusDef(
        name="Weakened", symbol="↓", color_key="STATUS_BAD",
        duration_default=4, tick_damage=0,
        stat_modifier={"attack": 0.6},
        description="-40% attack"
    ),
    "slowed": StatusDef(
        name="Slowed", symbol="≈", color_key="STATUS_BAD",
        duration_default=3, tick_damage=0,
        stat_modifier={"speed": 0.5},
        description="Movement slowed"
    ),
}


# ─────────────────────────────────────────────
#  Character Classes
# ─────────────────────────────────────────────
@dataclass
class ClassDef:
    name: str
    symbol: str
    color_key: str
    description: str
    base_hp: int
    base_mana: int
    base_attack: int
    base_defense: int
    base_speed: int
    hp_per_level: int
    mana_per_level: int
    attack_per_level: float
    defense_per_level: float
    skills: List[str]
    flavor: str


CLASS_DEFS: Dict[str, ClassDef] = {
    "warrior": ClassDef(
        name="Warrior", symbol="@", color_key="PLAYER",
        description="Stalwart fighter with unbreakable will",
        base_hp=120, base_mana=30,
        base_attack=14, base_defense=8,
        base_speed=1,
        hp_per_level=12, mana_per_level=3,
        attack_per_level=2.0, defense_per_level=1.5,
        skills=["shield_bash", "berserker_rage", "war_cry", "execute"],
        flavor="Steel and fury — the Warrior breaks all who stand before."
    ),
    "mage": ClassDef(
        name="Mage", symbol="@", color_key="PLAYER",
        description="Master of arcane destruction",
        base_hp=60, base_mana=120,
        base_attack=8, base_defense=3,
        base_speed=1,
        hp_per_level=5, mana_per_level=15,
        attack_per_level=1.0, defense_per_level=0.5,
        skills=["fireball", "ice_bolt", "lightning", "arcane_shield"],
        flavor="Whispers of power — the Mage reshapes reality itself."
    ),
    "rogue": ClassDef(
        name="Rogue", symbol="@", color_key="PLAYER",
        description="Silent predator of the dark",
        base_hp=80, base_mana=50,
        base_attack=12, base_defense=5,
        base_speed=1,
        hp_per_level=7, mana_per_level=5,
        attack_per_level=1.8, defense_per_level=0.8,
        skills=["backstab", "stealth", "smoke_bomb", "shadow_strike"],
        flavor="Silence is a weapon — the Rogue strikes unseen."
    ),
    "paladin": ClassDef(
        name="Paladin", symbol="@", color_key="PLAYER",
        description="Holy warrior of divine purpose",
        base_hp=100, base_mana=80,
        base_attack=11, base_defense=7,
        base_speed=1,
        hp_per_level=9, mana_per_level=8,
        attack_per_level=1.5, defense_per_level=1.2,
        skills=["holy_strike", "lay_on_hands", "divine_shield", "holy_aura"],
        flavor="Light eternal — the Paladin stands between darkness and life."
    ),
}


# ─────────────────────────────────────────────
#  Skills / Spells
# ─────────────────────────────────────────────
@dataclass
class SkillDef:
    name: str
    key: str
    mana_cost: int
    cooldown: int           # in turns
    damage_mult: float      # multiplier of base attack
    heal_amount: int        # flat heal
    range_cells: int        # 0 = adjacent melee, 1+ = ranged
    aoe_radius: int         # 0 = single target
    status_apply: str       # status effect key to apply (or "")
    status_chance: float    # 0.0 – 1.0
    description: str
    color_key: str = "UI"
    target: str = "enemy"   # "enemy", "self", "all_enemies"


SKILL_DEFS: Dict[str, SkillDef] = {
    # ── Warrior ──────────────────────────────
    "shield_bash": SkillDef(
        name="Shield Bash", key="shield_bash",
        mana_cost=15, cooldown=3,
        damage_mult=1.2, heal_amount=0, range_cells=1,
        aoe_radius=0, status_apply="stunned", status_chance=0.6,
        description="Bash with shield. Chance to stun.",
        color_key="UI", target="enemy"
    ),
    "berserker_rage": SkillDef(
        name="Berserker Rage", key="berserker_rage",
        mana_cost=20, cooldown=5,
        damage_mult=2.5, heal_amount=0, range_cells=1,
        aoe_radius=0, status_apply="weakened", status_chance=0.4,
        description="Unleash furious strikes. High damage.",
        color_key="CRIT", target="enemy"
    ),
    "war_cry": SkillDef(
        name="War Cry", key="war_cry",
        mana_cost=10, cooldown=6,
        damage_mult=0.0, heal_amount=0, range_cells=0,
        aoe_radius=3, status_apply="stunned", status_chance=0.5,
        description="Terrifying shout. Stuns nearby enemies.",
        color_key="UI", target="all_enemies"
    ),
    "execute": SkillDef(
        name="Execute", key="execute",
        mana_cost=25, cooldown=4,
        damage_mult=3.0, heal_amount=0, range_cells=1,
        aoe_radius=0, status_apply="", status_chance=0.0,
        description="Devastating blow. Triple damage.",
        color_key="CRIT", target="enemy"
    ),
    # ── Mage ────────────────────────────────
    "fireball": SkillDef(
        name="Fireball", key="fireball",
        mana_cost=25, cooldown=2,
        damage_mult=2.8, heal_amount=0, range_cells=8,
        aoe_radius=2, status_apply="burning", status_chance=0.7,
        description="Explosive fire. AoE + burn chance.",
        color_key="STATUS_BAD", target="enemy"
    ),
    "ice_bolt": SkillDef(
        name="Ice Bolt", key="ice_bolt",
        mana_cost=18, cooldown=2,
        damage_mult=1.8, heal_amount=0, range_cells=10,
        aoe_radius=0, status_apply="frozen", status_chance=0.5,
        description="Piercing cold. Chance to freeze.",
        color_key="UI", target="enemy"
    ),
    "lightning": SkillDef(
        name="Lightning", key="lightning",
        mana_cost=30, cooldown=3,
        damage_mult=3.2, heal_amount=0, range_cells=12,
        aoe_radius=0, status_apply="stunned", status_chance=0.4,
        description="Bolt of lightning. High damage + stun.",
        color_key="GOLD", target="enemy"
    ),
    "arcane_shield": SkillDef(
        name="Arcane Shield", key="arcane_shield",
        mana_cost=35, cooldown=8,
        damage_mult=0.0, heal_amount=0, range_cells=0,
        aoe_radius=0, status_apply="shielded", status_chance=1.0,
        description="Magical barrier. Doubles defense temporarily.",
        color_key="STATUS_GOOD", target="self"
    ),
    # ── Rogue ───────────────────────────────
    "backstab": SkillDef(
        name="Backstab", key="backstab",
        mana_cost=15, cooldown=3,
        damage_mult=3.5, heal_amount=0, range_cells=1,
        aoe_radius=0, status_apply="poisoned", status_chance=0.4,
        description="Deadly stab. 3.5x damage + poison.",
        color_key="STATUS_BAD", target="enemy"
    ),
    "stealth": SkillDef(
        name="Stealth", key="stealth",
        mana_cost=20, cooldown=7,
        damage_mult=0.0, heal_amount=0, range_cells=0,
        aoe_radius=0, status_apply="invisible", status_chance=1.0,
        description="Become invisible for 5 turns.",
        color_key="STATUS_GOOD", target="self"
    ),
    "smoke_bomb": SkillDef(
        name="Smoke Bomb", key="smoke_bomb",
        mana_cost=12, cooldown=4,
        damage_mult=0.0, heal_amount=0, range_cells=5,
        aoe_radius=3, status_apply="stunned", status_chance=0.6,
        description="Blind and stun area of enemies.",
        color_key="UI", target="all_enemies"
    ),
    "shadow_strike": SkillDef(
        name="Shadow Strike", key="shadow_strike",
        mana_cost=22, cooldown=3,
        damage_mult=2.2, heal_amount=0, range_cells=1,
        aoe_radius=0, status_apply="weakened", status_chance=0.5,
        description="Shadows empower your strike. Weaken enemy.",
        color_key="UI", target="enemy"
    ),
    # ── Paladin ─────────────────────────────
    "holy_strike": SkillDef(
        name="Holy Strike", key="holy_strike",
        mana_cost=18, cooldown=2,
        damage_mult=2.0, heal_amount=0, range_cells=1,
        aoe_radius=0, status_apply="stunned", status_chance=0.3,
        description="Sacred blow deals holy damage.",
        color_key="STATUS_GOOD", target="enemy"
    ),
    "lay_on_hands": SkillDef(
        name="Lay on Hands", key="lay_on_hands",
        mana_cost=30, cooldown=5,
        damage_mult=0.0, heal_amount=50, range_cells=0,
        aoe_radius=0, status_apply="regenerating", status_chance=1.0,
        description="Divine healing + regeneration.",
        color_key="HP_HIGH", target="self"
    ),
    "divine_shield": SkillDef(
        name="Divine Shield", key="divine_shield",
        mana_cost=25, cooldown=8,
        damage_mult=0.0, heal_amount=0, range_cells=0,
        aoe_radius=0, status_apply="blessed", status_chance=1.0,
        description="Holy blessing. +20% atk, +30% def.",
        color_key="STATUS_GOOD", target="self"
    ),
    "holy_aura": SkillDef(
        name="Holy Aura", key="holy_aura",
        mana_cost=40, cooldown=10,
        damage_mult=1.5, heal_amount=15, range_cells=3,
        aoe_radius=3, status_apply="weakened", status_chance=0.6,
        description="Sacred pulse. Damages + weakens all nearby.",
        color_key="GOLD", target="all_enemies"
    ),
}


# ─────────────────────────────────────────────
#  Enemy Definitions
# ─────────────────────────────────────────────
@dataclass
class EnemyDef:
    key: str
    name: str
    symbol: str
    color_key: str
    hp: int
    attack: int
    defense: int
    speed: int          # 1 = normal, 2 = fast (acts every other player turn gets an extra act)
    xp: int
    min_floor: int
    max_floor: int
    abilities: List[str]   # list of skill keys (enemies can use some skills)
    loot_table: List[str]  # item keys with drop probability embedded
    is_boss: bool = False
    boss_floor: int = 0
    description: str = ""
    aggro_range: int = 6


ENEMY_DEFS: Dict[str, EnemyDef] = {
    "rat": EnemyDef(
        key="rat", name="Giant Rat", symbol="r", color_key="ENEMY",
        hp=12, attack=4, defense=1, speed=1, xp=5,
        min_floor=1, max_floor=3,
        abilities=[], loot_table=["health_potion_small:0.15"],
        description="Vermin from the depths.", aggro_range=5
    ),
    "goblin": EnemyDef(
        key="goblin", name="Goblin", symbol="g", color_key="ENEMY",
        hp=20, attack=6, defense=2, speed=1, xp=10,
        min_floor=1, max_floor=5,
        abilities=[], loot_table=["health_potion_small:0.2", "gold_small:0.4"],
        description="Cunning and vicious.", aggro_range=6
    ),
    "skeleton": EnemyDef(
        key="skeleton", name="Skeleton", symbol="s", color_key="ENEMY",
        hp=25, attack=8, defense=3, speed=1, xp=15,
        min_floor=2, max_floor=6,
        abilities=[], loot_table=["gold_small:0.3", "scroll_identify:0.1"],
        description="Undead warrior, rattling bones.", aggro_range=6
    ),
    "orc": EnemyDef(
        key="orc", name="Orc Warrior", symbol="o", color_key="ENEMY",
        hp=40, attack=12, defense=5, speed=1, xp=25,
        min_floor=3, max_floor=8,
        abilities=["berserker_rage"], loot_table=["health_potion_med:0.25", "gold_med:0.3", "sword_iron:0.05"],
        description="Brutal soldier of the deep.", aggro_range=6
    ),
    "troll": EnemyDef(
        key="troll", name="Cave Troll", symbol="T", color_key="BOSS",
        hp=70, attack=16, defense=8, speed=1, xp=45,
        min_floor=4, max_floor=9,
        abilities=[], loot_table=["health_potion_med:0.4", "gold_med:0.5", "armor_leather:0.08"],
        description="Thick-skulled regenerating beast.", aggro_range=7
    ),
    "dark_elf": EnemyDef(
        key="dark_elf", name="Dark Elf", symbol="e", color_key="ENEMY",
        hp=35, attack=14, defense=6, speed=1, xp=35,
        min_floor=5, max_floor=12,
        abilities=["ice_bolt"], loot_table=["mana_potion:0.3", "gold_med:0.35", "ring_of_speed:0.03"],
        description="Elven exile, master of frost.", aggro_range=8
    ),
    "demon": EnemyDef(
        key="demon", name="Demon Spawn", symbol="d", color_key="STATUS_BAD",
        hp=55, attack=18, defense=7, speed=1, xp=55,
        min_floor=7, max_floor=14,
        abilities=["fireball"], loot_table=["health_potion_large:0.2", "gold_large:0.4", "sword_fire:0.04"],
        description="Born of hellfire and malice.", aggro_range=7
    ),
    "dragon_whelp": EnemyDef(
        key="dragon_whelp", name="Dragon Whelp", symbol="D", color_key="CRIT",
        hp=65, attack=20, defense=10, speed=1, xp=70,
        min_floor=9, max_floor=16,
        abilities=["fireball"], loot_table=["gold_large:0.6", "armor_dragon:0.05", "health_potion_large:0.3"],
        description="Young dragon, still deadly.", aggro_range=8
    ),
    "necromancer": EnemyDef(
        key="necromancer", name="Necromancer", symbol="N", color_key="ENEMY",
        hp=50, attack=15, defense=5, speed=1, xp=80,
        min_floor=10, max_floor=18,
        abilities=["lightning"], loot_table=["scroll_summon:0.3", "mana_potion:0.4", "staff_bone:0.06"],
        description="Weaves death into terrible power.", aggro_range=9
    ),
    "shadow": EnemyDef(
        key="shadow", name="Shadow", symbol="S", color_key="EXPLORED",
        hp=45, attack=22, defense=4, speed=1, xp=90,
        min_floor=12, max_floor=20,
        abilities=["stealth", "backstab"], loot_table=["gold_large:0.5", "cloak_shadow:0.05"],
        description="Darkness given form and hunger.", aggro_range=10
    ),
    # ── Bosses ──────────────────────────────
    "giant_troll": EnemyDef(
        key="giant_troll", name="GIANT TROLL", symbol="B", color_key="BOSS",
        hp=200, attack=22, defense=12, speed=1, xp=300,
        min_floor=5, max_floor=5,
        abilities=["war_cry", "berserker_rage"],
        loot_table=["health_potion_large:1.0", "gold_large:1.0", "sword_iron:1.0"],
        is_boss=True, boss_floor=5,
        description="Mountain of muscle and malice.", aggro_range=99
    ),
    "lich_king": EnemyDef(
        key="lich_king", name="LICH KING", symbol="L", color_key="BOSS",
        hp=350, attack=30, defense=18, speed=1, xp=600,
        min_floor=10, max_floor=10,
        abilities=["lightning", "ice_bolt", "fireball"],
        loot_table=["health_potion_large:1.0", "gold_large:1.0", "staff_bone:1.0", "ring_of_power:1.0"],
        is_boss=True, boss_floor=10,
        description="Death incarnate, ruler of the undead abyss.", aggro_range=99
    ),
    "demon_lord": EnemyDef(
        key="demon_lord", name="DEMON LORD", symbol="X", color_key="BOSS",
        hp=600, attack=42, defense=25, speed=1, xp=1200,
        min_floor=15, max_floor=15,
        abilities=["fireball", "berserker_rage", "war_cry"],
        loot_table=["health_potion_large:1.0", "gold_large:1.0", "sword_fire:1.0", "armor_dragon:1.0"],
        is_boss=True, boss_floor=15,
        description="Supreme commander of the infernal legions.", aggro_range=99
    ),
}


# ─────────────────────────────────────────────
#  Item Definitions
# ─────────────────────────────────────────────
@dataclass
class ItemDef:
    key: str
    name: str
    symbol: str
    color_key: str
    item_type: str          # "weapon", "armor", "potion", "scroll", "ring", "gold"
    value: int              # gold value
    weight: float
    # stat bonuses (for equipment)
    attack_bonus: int = 0
    defense_bonus: int = 0
    hp_bonus: int = 0
    mana_bonus: int = 0
    speed_bonus: int = 0
    crit_bonus: float = 0.0
    dodge_bonus: float = 0.0
    # effect (for consumables)
    effect: str = ""        # "heal", "mana", "identify", "teleport", "summon"
    effect_value: int = 0
    apply_status: str = ""
    description: str = ""
    min_floor: int = 1
    rarity: str = "common"  # common, uncommon, rare, epic, legendary


ITEM_DEFS: Dict[str, ItemDef] = {
    # ── Weapons ─────────────────────────────
    "sword_iron": ItemDef(
        key="sword_iron", name="Iron Sword", symbol="/", color_key="ITEM",
        item_type="weapon", value=50, weight=3.0,
        attack_bonus=5, crit_bonus=0.05,
        description="Reliable iron blade.", min_floor=1, rarity="common"
    ),
    "sword_fire": ItemDef(
        key="sword_fire", name="Flame Sword", symbol="/", color_key="STATUS_BAD",
        item_type="weapon", value=200, weight=3.0,
        attack_bonus=12, crit_bonus=0.10,
        apply_status="burning",
        description="Blade wreathed in eternal flame.", min_floor=7, rarity="rare"
    ),
    "dagger_shadow": ItemDef(
        key="dagger_shadow", name="Shadow Dagger", symbol="†", color_key="EXPLORED",
        item_type="weapon", value=120, weight=1.5,
        attack_bonus=8, crit_bonus=0.20, dodge_bonus=0.05,
        description="Forged in absolute darkness.", min_floor=5, rarity="uncommon"
    ),
    "staff_bone": ItemDef(
        key="staff_bone", name="Bone Staff", symbol="|", color_key="ENEMY",
        item_type="weapon", value=150, weight=2.0,
        attack_bonus=6, mana_bonus=30,
        description="Focus for dark magic.", min_floor=6, rarity="uncommon"
    ),
    "axe_war": ItemDef(
        key="axe_war", name="War Axe", symbol="¥", color_key="ITEM",
        item_type="weapon", value=80, weight=5.0,
        attack_bonus=9, crit_bonus=0.08,
        description="Heavy cleaving axe.", min_floor=3, rarity="common"
    ),
    "bow_elven": ItemDef(
        key="bow_elven", name="Elven Bow", symbol="}",  color_key="STATUS_GOOD",
        item_type="weapon", value=180, weight=2.0,
        attack_bonus=10, crit_bonus=0.15, speed_bonus=0,
        description="Elegant ranged weapon.", min_floor=5, rarity="uncommon"
    ),
    # ── Armor ───────────────────────────────
    "armor_leather": ItemDef(
        key="armor_leather", name="Leather Armor", symbol="[", color_key="ITEM",
        item_type="armor", value=40, weight=4.0,
        defense_bonus=3, dodge_bonus=0.05,
        description="Light, flexible protection.", min_floor=1, rarity="common"
    ),
    "armor_chain": ItemDef(
        key="armor_chain", name="Chain Mail", symbol="[", color_key="ITEM",
        item_type="armor", value=100, weight=8.0,
        defense_bonus=7,
        description="Interlocked rings of steel.", min_floor=3, rarity="common"
    ),
    "armor_plate": ItemDef(
        key="armor_plate", name="Plate Armor", symbol="[", color_key="SILVER",
        item_type="armor", value=250, weight=15.0,
        defense_bonus=14, hp_bonus=20,
        description="Full steel plate. Heavy but effective.", min_floor=6, rarity="uncommon"
    ),
    "armor_dragon": ItemDef(
        key="armor_dragon", name="Dragon Scale Armor", symbol="[", color_key="CRIT",
        item_type="armor", value=500, weight=10.0,
        defense_bonus=20, hp_bonus=30, crit_bonus=0.05,
        description="Scales from a fallen dragon.", min_floor=12, rarity="epic"
    ),
    "cloak_shadow": ItemDef(
        key="cloak_shadow", name="Shadow Cloak", symbol="(", color_key="EXPLORED",
        item_type="armor", value=300, weight=1.0,
        defense_bonus=4, dodge_bonus=0.20,
        description="Woven from solidified darkness.", min_floor=10, rarity="rare"
    ),
    # ── Rings ───────────────────────────────
    "ring_of_speed": ItemDef(
        key="ring_of_speed", name="Ring of Speed", symbol="°", color_key="GOLD",
        item_type="ring", value=150, weight=0.1,
        speed_bonus=1, dodge_bonus=0.10,
        description="Quickens your step.", min_floor=4, rarity="uncommon"
    ),
    "ring_of_power": ItemDef(
        key="ring_of_power", name="Ring of Power", symbol="°", color_key="CRIT",
        item_type="ring", value=400, weight=0.1,
        attack_bonus=8, mana_bonus=20, crit_bonus=0.10,
        description="Amplifies all destructive force.", min_floor=9, rarity="rare"
    ),
    "ring_of_life": ItemDef(
        key="ring_of_life", name="Ring of Life", symbol="°", color_key="HP_HIGH",
        item_type="ring", value=200, weight=0.1,
        hp_bonus=30, defense_bonus=2,
        description="Strengthens the life force.", min_floor=5, rarity="uncommon"
    ),
    # ── Potions ─────────────────────────────
    "health_potion_small": ItemDef(
        key="health_potion_small", name="Small Health Potion", symbol="!", color_key="HP_HIGH",
        item_type="potion", value=15, weight=0.5,
        effect="heal", effect_value=25,
        description="Restores 25 HP.", min_floor=1, rarity="common"
    ),
    "health_potion_med": ItemDef(
        key="health_potion_med", name="Health Potion", symbol="!", color_key="HP_HIGH",
        item_type="potion", value=35, weight=0.5,
        effect="heal", effect_value=60,
        description="Restores 60 HP.", min_floor=3, rarity="common"
    ),
    "health_potion_large": ItemDef(
        key="health_potion_large", name="Large Health Potion", symbol="!", color_key="HP_HIGH",
        item_type="potion", value=80, weight=0.5,
        effect="heal", effect_value=120,
        description="Restores 120 HP.", min_floor=5, rarity="uncommon"
    ),
    "mana_potion": ItemDef(
        key="mana_potion", name="Mana Potion", symbol="!", color_key="MANA",
        item_type="potion", value=30, weight=0.5,
        effect="mana", effect_value=50,
        description="Restores 50 MP.", min_floor=2, rarity="common"
    ),
    "elixir_power": ItemDef(
        key="elixir_power", name="Elixir of Power", symbol="!", color_key="CRIT",
        item_type="potion", value=120, weight=0.5,
        effect="status", apply_status="blessed", effect_value=0,
        description="Grants blessed status for 8 turns.", min_floor=6, rarity="uncommon"
    ),
    # ── Scrolls ─────────────────────────────
    "scroll_identify": ItemDef(
        key="scroll_identify", name="Scroll of Identify", symbol="~", color_key="ITEM",
        item_type="scroll", value=20, weight=0.1,
        effect="identify",
        description="Reveals properties of an item.", min_floor=1, rarity="common"
    ),
    "scroll_teleport": ItemDef(
        key="scroll_teleport", name="Scroll of Teleport", symbol="~", color_key="MANA",
        item_type="scroll", value=50, weight=0.1,
        effect="teleport",
        description="Randomly transports you.", min_floor=3, rarity="uncommon"
    ),
    "scroll_summon": ItemDef(
        key="scroll_summon", name="Scroll of Fire Wall", symbol="~", color_key="STATUS_BAD",
        item_type="scroll", value=80, weight=0.1,
        effect="fire_wall",
        description="Creates a barrier of fire.", min_floor=6, rarity="uncommon"
    ),
    "scroll_mapping": ItemDef(
        key="scroll_mapping", name="Scroll of Mapping", symbol="~", color_key="UI",
        item_type="scroll", value=40, weight=0.1,
        effect="map",
        description="Reveals the entire floor.", min_floor=2, rarity="common"
    ),
    # ── Gold ────────────────────────────────
    "gold_small": ItemDef(
        key="gold_small", name="Gold Coins", symbol="$", color_key="GOLD",
        item_type="gold", value=10, weight=0.1,
        effect="gold", effect_value=10,
        description="A handful of gold.", min_floor=1, rarity="common"
    ),
    "gold_med": ItemDef(
        key="gold_med", name="Gold Pouch", symbol="$", color_key="GOLD",
        item_type="gold", value=30, weight=0.3,
        effect="gold", effect_value=30,
        description="A decent sum of gold.", min_floor=2, rarity="common"
    ),
    "gold_large": ItemDef(
        key="gold_large", name="Gold Chest", symbol="$", color_key="GOLD",
        item_type="gold", value=100, weight=1.0,
        effect="gold", effect_value=100,
        description="A substantial treasure.", min_floor=4, rarity="uncommon"
    ),
}

# Shop stock tables per floor range
SHOP_STOCK: Dict[str, List[str]] = {
    "early": ["health_potion_small", "health_potion_med", "mana_potion", "scroll_identify",
              "sword_iron", "armor_leather", "scroll_mapping"],
    "mid":   ["health_potion_med", "health_potion_large", "mana_potion", "elixir_power",
              "scroll_teleport", "axe_war", "armor_chain", "ring_of_life", "dagger_shadow"],
    "late":  ["health_potion_large", "elixir_power", "mana_potion", "scroll_summon",
              "sword_fire", "armor_plate", "ring_of_power", "cloak_shadow", "bow_elven"],
}

# XP required per level (index = level-1, so index 0 = XP to reach level 2)
XP_TABLE: List[int] = [
    0,      # level 1 → no XP needed (starting level)
    50,     # level 2
    130,    # level 3
    250,    # level 4
    420,    # level 5
    650,    # level 6
    950,    # level 7
    1320,   # level 8
    1780,   # level 9
    2350,   # level 10
    3050,   # level 11
    3900,   # level 12
    4900,   # level 13
    6100,   # level 14
    7500,   # level 15
    9200,   # level 16
    11200,  # level 17
    13600,  # level 18
    16400,  # level 19
    19600,  # level 20 (max)
]

MAX_LEVEL = 20
MAX_FLOOR = 20

# Tile characters
TILE_CHARS = {
    "wall":       "#",
    "floor":      ".",
    "stairs_down":">",
    "stairs_up":  "<",
    "door_closed":"D",
    "door_open":  "d",
    "water":      "~",
    "void":       " ",
    "shop":       "£",
}
