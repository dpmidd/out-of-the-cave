"""Save/load system — persist GameState as JSON files in the saves/ directory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.models.game_state import GameState


SAVES_DIR = Path(__file__).resolve().parent.parent.parent / "saves"


def _ensure_saves_dir() -> None:
    SAVES_DIR.mkdir(parents=True, exist_ok=True)


def _slot_path(slot: str) -> Path:
    return SAVES_DIR / f"{slot}.json"


def save_game(state: GameState, slot: str = "manual") -> Path:
    """Save the current game state to a named slot. Returns the file path."""
    _ensure_saves_dir()
    path = _slot_path(slot)

    payload = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "turn": state.turn,
        "population": state.civilization.population,
        "difficulty": state.difficulty,
        "state": json.loads(state.model_dump_json()),
    }

    path.write_text(json.dumps(payload, indent=2))
    return path


def load_game(slot: str = "manual") -> GameState | None:
    """Load a game state from a named slot. Returns None if not found."""
    path = _slot_path(slot)
    if not path.exists():
        return None

    payload = json.loads(path.read_text())
    return GameState.model_validate(payload["state"])


def list_saves() -> list[dict]:
    """List all save files with metadata. Returns list of dicts sorted by recency."""
    _ensure_saves_dir()
    saves = []

    for path in SAVES_DIR.glob("*.json"):
        try:
            payload = json.loads(path.read_text())
            saves.append({
                "slot": path.stem,
                "saved_at": payload.get("saved_at", "unknown"),
                "turn": payload.get("turn", "?"),
                "population": payload.get("population", "?"),
                "difficulty": payload.get("difficulty", "?"),
            })
        except (json.JSONDecodeError, KeyError):
            continue

    saves.sort(key=lambda s: s["saved_at"], reverse=True)
    return saves


def delete_save(slot: str) -> bool:
    """Delete a save file. Returns True if deleted."""
    path = _slot_path(slot)
    if path.exists():
        path.unlink()
        return True
    return False


def save_checkpoint(state: GameState) -> Path:
    """Save an auto-checkpoint (easy mode milestone saves)."""
    return save_game(state, slot="checkpoint")


def load_checkpoint() -> GameState | None:
    """Load the last auto-checkpoint."""
    return load_game(slot="checkpoint")
