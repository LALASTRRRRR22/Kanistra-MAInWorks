"""
KANISTRA ABYSS - Combat System
Turn-based combat with skills, crits, status effects.
"""
from __future__ import annotations
import random
import math
from typing import List, Optional, Tuple, TYPE_CHECKING

from data import SKILL_DEFS, SkillDef, STATUS_DEFS, ITEM_DEFS
from entities import Entity, Player, Enemy, Item, FloorItem

if TYPE_CHECKING:
    from dungeon import DungeonFloor


class CombatResult:
    def __init__(self):
        self.messages:     List[str]          = []
        self.player_died:  bool               = False
        self.enemy_died:   bool               = False
        self.enemy:        Optional[Enemy]    = None
        self.xp_gained:    int                = 0
        self.loot_dropped: List[str]          = []
        self.is_crit:      bool               = False
        self.damage_dealt: int                = 0
        self.damage_taken: int                = 0


class CombatEngine:
    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()

    # ─────────────────────────────────────────
    #  Core damage formula
    # ─────────────────────────────────────────
    def _calc_damage(self, attacker_atk: int, defender_def: int,
                     mult: float = 1.0, variance: float = 0.15) -> int:
        base = max(1, attacker_atk - defender_def // 2)
        spread = self.rng.uniform(1.0 - variance, 1.0 + variance)
        return max(1, int(base * mult * spread))

    def _is_crit(self, crit_chance: float) -> bool:
        return self.rng.random() < crit_chance

    def _is_dodge(self, dodge_chance: float) -> bool:
        return self.rng.random() < dodge_chance

    # ─────────────────────────────────────────
    #  Player attacks enemy (basic)
    # ─────────────────────────────────────────
    def player_attack(self, player: Player, enemy: Enemy) -> CombatResult:
        result = CombatResult()
        result.enemy = enemy

        # invisible player = surprise attack (bonus damage)
        invisible_bonus = 1.5 if player.has_status("invisible") else 1.0
        if player.has_status("invisible"):
            player.remove_status("invisible")

        crit = self._is_crit(player.crit_chance)
        crit_mult = 2.0 if crit else 1.0
        dmg = self._calc_damage(player.effective_attack, enemy.effective_defense,
                                 mult=crit_mult * invisible_bonus)

        # apply weapon status on hit
        weap = player.equipment.weapon
        if weap and weap.definition.apply_status:
            status_key = weap.definition.apply_status
            if status_key and self.rng.random() < 0.4:
                enemy.apply_status(status_key)
                result.messages.append(f"Enemy is {STATUS_DEFS[status_key].name}!")

        enemy.hp -= dmg
        result.damage_dealt = dmg
        result.is_crit = crit

        if crit:
            result.messages.append(f"*** CRITICAL HIT! {player.name} slashes {enemy.name} for {dmg}!")
        else:
            result.messages.append(f"{player.name} attacks {enemy.name} for {dmg} damage.")

        if enemy.hp <= 0:
            enemy.alive = False
            result.enemy_died = True
            result.xp_gained = enemy.xp_value
            player.kills += 1
            result.messages.append(f"{enemy.name} is slain! (+{enemy.xp_value} XP)")
            result.loot_dropped = enemy.roll_loot(self.rng)

        return result

    # ─────────────────────────────────────────
    #  Enemy attacks player
    # ─────────────────────────────────────────
    def enemy_attack(self, enemy: Enemy, player: Player) -> CombatResult:
        result = CombatResult()
        result.enemy = enemy

        # Check player invisibility
        if player.has_status("invisible"):
            result.messages.append(f"{enemy.name} swings at empty air!")
            return result

        # Dodge
        if self._is_dodge(player.dodge_chance):
            result.messages.append(f"{player.name} dodges {enemy.name}'s attack!")
            return result

        crit = self._is_crit(0.08)
        crit_mult = 1.8 if crit else 1.0
        dmg = self._calc_damage(enemy.effective_attack, player.effective_defense,
                                 mult=crit_mult)

        player.hp -= dmg
        result.damage_taken = dmg

        if crit:
            result.messages.append(f"*** {enemy.name} critically hits {player.name} for {dmg}!")
        else:
            result.messages.append(f"{enemy.name} attacks {player.name} for {dmg} damage.")

        if player.hp <= 0:
            player.alive = False
            result.player_died = True
            result.messages.append(f"{player.name} has been slain by {enemy.name}!")

        return result

    # ─────────────────────────────────────────
    #  Player uses skill
    # ─────────────────────────────────────────
    def player_use_skill(self, player: Player, skill_key: str,
                          enemy: Optional[Enemy],
                          nearby_enemies: List[Enemy],
                          dungeon: Optional["DungeonFloor"] = None) -> CombatResult:
        result = CombatResult()
        if skill_key not in SKILL_DEFS:
            result.messages.append("Unknown skill!")
            return result

        sdef: SkillDef = SKILL_DEFS[skill_key]

        # Mana check
        if player.mana < sdef.mana_cost:
            result.messages.append(f"Not enough mana! Need {sdef.mana_cost} MP.")
            return result

        # Cooldown check
        if not player.skill_ready(skill_key):
            cd = player.skill_cooldowns[skill_key]
            result.messages.append(f"{sdef.name} is on cooldown ({cd} turns).")
            return result

        player.mana -= sdef.mana_cost
        player.start_skill_cooldown(skill_key)
        result.messages.append(f"{player.name} uses {sdef.name}!")

        # Self-target skills
        if sdef.target == "self":
            if sdef.heal_amount > 0:
                heal = sdef.heal_amount
                player.hp = min(player.max_hp_total, player.hp + heal)
                result.messages.append(f"{player.name} heals for {heal} HP.")
            if sdef.status_apply and self.rng.random() < sdef.status_chance:
                player.apply_status(sdef.status_apply)
                result.messages.append(f"{player.name} gains {STATUS_DEFS[sdef.status_apply].name}!")
            return result

        # AOE skills (hit all nearby enemies)
        if sdef.target == "all_enemies":
            targets = [e for e in nearby_enemies
                       if e.alive and self._in_range(player, e, max(sdef.range_cells, sdef.aoe_radius))]
            if not targets:
                result.messages.append("No enemies in range!")
                player.mana += sdef.mana_cost  # refund
                player.skill_cooldowns[skill_key] = 0
                return result
            for t in targets:
                if sdef.damage_mult > 0:
                    dmg = self._calc_damage(player.effective_attack, t.effective_defense,
                                            mult=sdef.damage_mult)
                    t.hp -= dmg
                    result.damage_dealt += dmg
                    result.messages.append(f"{t.name} takes {dmg} damage from {sdef.name}!")
                if sdef.status_apply and self.rng.random() < sdef.status_chance:
                    t.apply_status(sdef.status_apply)
                    result.messages.append(f"{t.name} is {STATUS_DEFS[sdef.status_apply].name}!")
                if t.hp <= 0:
                    t.alive = False
                    result.xp_gained += t.xp_value
                    player.kills += 1
                    result.messages.append(f"{t.name} is slain! (+{t.xp_value} XP)")
                    result.loot_dropped.extend(t.roll_loot(self.rng))
            return result

        # Single-target enemy skills
        if enemy is None:
            result.messages.append("No target selected!")
            player.mana += sdef.mana_cost  # refund
            player.skill_cooldowns[skill_key] = 0
            return result

        if not self._in_range(player, enemy, sdef.range_cells if sdef.range_cells > 0 else 1):
            result.messages.append(f"{enemy.name} is out of range!")
            player.mana += sdef.mana_cost
            player.skill_cooldowns[skill_key] = 0
            return result

        crit = self._is_crit(player.crit_chance)
        crit_mult = 2.0 if crit else 1.0
        dmg = 0
        if sdef.damage_mult > 0:
            dmg = self._calc_damage(player.effective_attack, enemy.effective_defense,
                                    mult=sdef.damage_mult * crit_mult)
            enemy.hp -= dmg
            result.damage_dealt = dmg
            result.is_crit = crit
            if crit:
                result.messages.append(f"*** CRITICAL! {sdef.name} hits {enemy.name} for {dmg}!")
            else:
                result.messages.append(f"{sdef.name} hits {enemy.name} for {dmg} damage!")

        if sdef.status_apply and self.rng.random() < sdef.status_chance:
            enemy.apply_status(sdef.status_apply)
            result.messages.append(f"{enemy.name} is {STATUS_DEFS[sdef.status_apply].name}!")

        if enemy.hp <= 0 and not result.enemy_died:
            enemy.alive = False
            result.enemy_died = True
            result.xp_gained = enemy.xp_value
            player.kills += 1
            result.messages.append(f"{enemy.name} is slain! (+{enemy.xp_value} XP)")
            result.loot_dropped = enemy.roll_loot(self.rng)

        result.enemy = enemy
        return result

    # ─────────────────────────────────────────
    #  Enemy uses ability
    # ─────────────────────────────────────────
    def enemy_use_ability(self, enemy: Enemy, ability_key: str,
                           player: Player) -> CombatResult:
        result = CombatResult()
        if ability_key not in SKILL_DEFS:
            return self.enemy_attack(enemy, player)

        sdef = SKILL_DEFS[ability_key]
        result.messages.append(f"{enemy.name} uses {sdef.name}!")
        enemy.ability_cooldowns[ability_key] = sdef.cooldown

        if sdef.target == "self":
            if sdef.heal_amount > 0:
                enemy.hp = min(enemy.max_hp, enemy.hp + sdef.heal_amount)
                result.messages.append(f"{enemy.name} heals for {sdef.heal_amount} HP!")
            if sdef.status_apply:
                enemy.apply_status(sdef.status_apply)
            return result

        # Attack player
        if _is_dodge_check := self._is_dodge(player.dodge_chance):
            result.messages.append(f"{player.name} dodges {sdef.name}!")
            return result

        dmg = 0
        if sdef.damage_mult > 0:
            dmg = self._calc_damage(enemy.effective_attack, player.effective_defense,
                                    mult=sdef.damage_mult)
            player.hp -= dmg
            result.damage_taken = dmg
            result.messages.append(f"{sdef.name} hits {player.name} for {dmg} damage!")

        if sdef.status_apply and self.rng.random() < sdef.status_chance:
            player.apply_status(sdef.status_apply)
            result.messages.append(f"{player.name} is {STATUS_DEFS[sdef.status_apply].name}!")

        if player.hp <= 0:
            player.alive = False
            result.player_died = True
            result.messages.append(f"{player.name} has been slain by {enemy.name}'s {sdef.name}!")

        return result

    # ─────────────────────────────────────────
    #  Use item (potion / scroll)
    # ─────────────────────────────────────────
    def use_item(self, player: Player, item: Item,
                 dungeon: Optional["DungeonFloor"] = None,
                 enemies: Optional[List[Enemy]] = None) -> List[str]:
        idef = item.definition
        msgs: List[str] = []

        if idef.effect == "heal":
            heal = idef.effect_value
            player.hp = min(player.max_hp_total, player.hp + heal)
            msgs.append(f"You drink {idef.name} and restore {heal} HP.")

        elif idef.effect == "mana":
            restore = idef.effect_value
            player.mana = min(player.max_mana_total, player.mana + restore)
            msgs.append(f"You drink {idef.name} and restore {restore} MP.")

        elif idef.effect == "status":
            if idef.apply_status:
                player.apply_status(idef.apply_status)
                msgs.append(f"You use {idef.name}. {STATUS_DEFS[idef.apply_status].name} applied!")

        elif idef.effect == "identify":
            msgs.append("All items identified!")
            for inv_item in player.inventory:
                inv_item.identified = True

        elif idef.effect == "teleport":
            # Handled in engine (need floor access)
            msgs.append("Reality warps around you...")

        elif idef.effect == "map":
            if dungeon:
                dungeon.reveal_all()
            msgs.append("The dungeon layout reveals itself to you!")

        elif idef.effect == "fire_wall":
            if enemies:
                count = 0
                for e in enemies:
                    if e.alive and abs(e.x - player.x) <= 3 and abs(e.y - player.y) <= 3:
                        e.apply_status("burning")
                        dmg = self.rng.randint(15, 25)
                        e.hp -= dmg
                        count += 1
                        if e.hp <= 0:
                            e.alive = False
                msgs.append(f"Fire erupts! {count} enemies engulfed in flames!")
            else:
                msgs.append("Flames erupt around you!")

        elif idef.effect == "gold":
            amount = idef.effect_value
            player.gold += amount
            msgs.append(f"You pick up {amount} gold.")

        return msgs

    # ─────────────────────────────────────────
    #  Helpers
    # ─────────────────────────────────────────
    @staticmethod
    def _in_range(attacker: Entity, target: Entity, max_range: int) -> bool:
        if max_range <= 0:
            max_range = 1
        dist = max(abs(attacker.x - target.x), abs(attacker.y - target.y))  # Chebyshev
        return dist <= max_range

    @staticmethod
    def chebyshev_dist(ax: int, ay: int, bx: int, by: int) -> int:
        return max(abs(ax - bx), abs(ay - by))
