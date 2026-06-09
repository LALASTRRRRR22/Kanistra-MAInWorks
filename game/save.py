"""
KANISTRA ABYSS - Save / Load / High Scores
"""
from __future__ import annotations
import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

SAVE_DIR = os.path.join(os.path.dirname(__file__), "saves")
SAVE_FILE = os.path.join(SAVE_DIR, "savegame.json")
HISCORE_FILE = os.path.join(SAVE_DIR, "hiscores.json")

MAX_SCORES = 10


@dataclass
class HiScoreEntry:
    name: str
    char_class: str
    score: int
    floor_reached: int
    level: int
    kills: int
    gold: int
    timestamp: str


def _ensure_save_dir() -> None:
    os.makedirs(SAVE_DIR, exist_ok=True)


def load_hiscores() -> List[HiScoreEntry]:
    _ensure_save_dir()
    if not os.path.exists(HISCORE_FILE):
        return []
    try:
        with open(HISCORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [HiScoreEntry(**entry) for entry in data]
    except Exception:
        return []


def save_hiscores(scores: List[HiScoreEntry]) -> None:
    _ensure_save_dir()
    try:
        with open(HISCORE_FILE, "w", encoding="utf-8") as f:
            json.dump([asdict(e) for e in scores], f, indent=2)
    except Exception:
        pass


def add_hiscore(name: str, char_class: str, score: int, floor_reached: int,
                level: int, kills: int, gold: int) -> int:
    """Add a new score. Returns the rank (1-based), or 0 if not in top-MAX_SCORES."""
    scores = load_hiscores()
    entry = HiScoreEntry(
        name=name,
        char_class=char_class,
        score=score,
        floor_reached=floor_reached,
        level=level,
        kills=kills,
        gold=gold,
        timestamp=time.strftime("%Y-%m-%d %H:%M"),
    )
    scores.append(entry)
    scores.sort(key=lambda e: e.score, reverse=True)
    scores = scores[:MAX_SCORES]
    save_hiscores(scores)
    try:
        rank = next(i + 1 for i, e in enumerate(scores)
                    if e.timestamp == entry.timestamp and e.name == name)
    except StopIteration:
        rank = 0
    return rank


def compute_score(floor_reached: int, level: int, kills: int, gold: int,
                  turns: int, is_winner: bool) -> int:
    base = floor_reached * 500 + level * 200 + kills * 30 + gold
    if is_winner:
        base = int(base * 2.5)
    # Efficiency bonus: fewer turns = better
    if turns > 0:
        efficiency = max(0, 10000 - turns) // 10
        base += efficiency
    return base


# ─── Simple save game ───────────────────────
def save_game(state: Dict[str, Any]) -> bool:
    _ensure_save_dir()
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        return True
    except Exception:
        return False


def load_game() -> Optional[Dict[str, Any]]:
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def delete_save() -> None:
    try:
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
    except Exception:
        pass


def has_save() -> bool:
    return os.path.exists(SAVE_FILE)
