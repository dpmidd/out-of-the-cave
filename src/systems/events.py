from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import yaml

from src.models.game_state import GameState
from src.systems.dice import roll


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

_event_cache: dict[str, list[dict]] = {}


def load_all_events() -> list[dict]:
    """Load all event YAML files from the events directory."""
    if _event_cache:
        return [e for events in _event_cache.values() for e in events]

    events_dir = DATA_DIR / "events"
    all_events = []
    for path in sorted(events_dir.glob("*.yaml")):
        with open(path) as f:
            data = yaml.safe_load(f) or []
            _event_cache[path.stem] = data
            all_events.extend(data)
    return all_events


def get_available_events(events: list[dict], state: GameState) -> list[dict]:
    """Filter events to those whose conditions are met and haven't been seen."""
    achieved = state.achieved_milestone_ids
    available = []

    for event in events:
        if event["id"] in state.event_history:
            continue

        conditions = event.get("conditions", {})

        # Milestone gating: event requires certain milestones to be achieved
        required = set(conditions.get("required_milestones", []))
        if required and not required.issubset(achieved):
            continue

        # Milestone blocking: event only appears if milestone NOT yet achieved
        blocked_by = set(conditions.get("blocked_by_milestones", []))
        if blocked_by and blocked_by.intersection(achieved):
            continue

        # Tier gating: event only available in current or earlier tiers
        event_tier = conditions.get("tier", 1)
        if event_tier > state.current_tier:
            continue

        # Numeric conditions
        if conditions.get("turn_min", 0) > state.turn:
            continue
        if conditions.get("turn_max", 999) < state.turn:
            continue
        if conditions.get("chaos_min", 0.0) > state.chaos:
            continue
        if conditions.get("chaos_max", 1.0) < state.chaos:
            continue
        if conditions.get("min_population", 0) > state.civilization.population:
            continue

        available.append(event)

    return available


def select_event(state: GameState) -> dict | None:
    """Pick the next event for the current game state."""
    all_events = load_all_events()
    available = get_available_events(all_events, state)
    if not available:
        return None

    # Prefer events from the current tier, but allow earlier-tier stragglers
    current_tier_events = [
        e for e in available
        if e.get("conditions", {}).get("tier", 1) == state.current_tier
    ]

    pool = current_tier_events if current_tier_events else available
    return random.choice(pool)


def resolve_choice(choice: dict, state: GameState) -> tuple[str, dict[str, Any]]:
    """Resolve a player's choice. Returns (outcome_text, effects dict)."""
    if choice.get("special") == "retreat":
        return "retreat", {}

    skill_name = choice.get("skill_check")
    difficulty = choice.get("difficulty", 5)

    if skill_name:
        attribute_value = state.player.get_attribute(skill_name)
        success = roll(attribute_value, difficulty, state.chaos)
        roll_val = attribute_value + difficulty + 5  # approximate value for display
        target = difficulty + 5
    else:
        success = True
        roll_val, target = 0, 0

    outcome_key = "success" if success else "failure"
    outcome = choice["outcomes"][outcome_key]

    # Apply chaos delta from the choice itself (extreme actions)
    if "chaos_delta" in choice:
        state.apply_chaos(choice["chaos_delta"])

    effects = outcome.get("effects", {})

    # Apply effects to game state
    if "chaos" in effects:
        state.apply_chaos(effects.pop("chaos"))
    if "loyalty_all" in effects:
        state.apply_loyalty_all(effects.pop("loyalty_all"))

    # Track special flags in event history (for milestone triggers)
    if "history_flag" in outcome:
        state.event_history.append(outcome["history_flag"])

    # Assign NPC roles if specified
    if "assign_role" in outcome:
        _assign_random_role(state, outcome["assign_role"])

    civ_log = state.civilization.apply_effects(effects)

    return outcome["text"], {
        "success": success,
        "roll": roll_val,
        "target": target,
        "civ_changes": civ_log,
        "deaths": abs(effects.get("population", 0)) if effects.get("population", 0) < 0 else 0,
    }


def _assign_random_role(state: GameState, role: str) -> None:
    """Assign a role to a random unassigned, alive NPC."""
    candidates = [n for n in state.npcs if n.alive and n.role is None]
    if candidates:
        # Prefer higher-loyalty NPCs
        candidates.sort(key=lambda n: n.loyalty, reverse=True)
        candidates[0].role = role
