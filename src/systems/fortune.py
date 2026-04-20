"""Miracles and curses — random events that fire after player choices."""

from __future__ import annotations

import random

from src.models.game_state import GameState


MIRACLE_CHANCE = {"easy": 0.12, "normal": 0.08, "hard": 0.05}
CURSE_CHANCE = {"easy": 0.05, "normal": 0.08, "hard": 0.15}

MIRACLES = [
    {
        "name": "Bountiful Harvest",
        "text": "Wild fruit trees are discovered nearby. The land provides.",
        "effects": {"food": 5},
    },
    {
        "name": "Travelers Arrive",
        "text": "A small family appears from the east, seeking a home. They ask to join.",
        "effects": {"population": 2},
    },
    {
        "name": "Gift from Neighbors",
        "text": "Supplies appear at the edge of camp overnight — blankets, rope, tools. Someone out there is watching, and they are kind.",
        "effects": {"shelter": 2},
    },
    {
        "name": "Inspired Leader",
        "text": "One of your people has a breakthrough — a new way to organize, to build, to inspire. Loyalty surges.",
        "effects": {"loyalty_boost": 0.3},
    },
    {
        "name": "Calm Weather",
        "text": "A week of perfect weather. Warm days, cool nights. Tensions ease without effort.",
        "effects": {"chaos": -0.08},
    },
    {
        "name": "Discovery",
        "text": "A curious child finds cave paintings on a nearby cliff — images of stars, seasons, planting. Ancient knowledge, freely given.",
        "effects": {"knowledge": 1},
    },
]

CURSES = [
    {
        "name": "Plague",
        "text": "A fever sweeps through camp. It strikes fast and without mercy.",
        "effects": {"population": -2, "chaos": 0.08},
    },
    {
        "name": "Famine",
        "text": "Insects devour the food stores overnight. By morning, nothing remains.",
        "effects": {"food_zero": True},
    },
    {
        "name": "Civil Unrest",
        "text": "A shouting match at the fire pit escalates into a brawl. Factions form. Trust fractures.",
        "effects": {"chaos": 0.12, "loyalty_all": -0.1},
    },
    {
        "name": "Storm",
        "text": "A violent storm tears through camp. Shelters collapse. Supplies scatter.",
        "effects": {"shelter": -2},
    },
    {
        "name": "Betrayal",
        "text": "One of your trusted people is caught hoarding supplies. The betrayal cuts deeper than any wound.",
        "effects": {"loyalty_betray": True},
    },
    {
        "name": "Fire",
        "text": "An unattended cookfire spreads. By the time it's controlled, food stores and a shelter are ash.",
        "effects": {"food": -3, "shelter": -1},
    },
]


def roll_fortune(state: GameState) -> tuple[str, str, str] | None:
    """Roll for a random miracle or curse.

    Returns (type, name, text) or None if nothing happens.
    Effects are applied directly to the state.
    """
    miracle_chance = MIRACLE_CHANCE.get(state.difficulty, 0.08)
    curse_chance = CURSE_CHANCE.get(state.difficulty, 0.08)

    roll = random.random()

    if roll < miracle_chance:
        miracle = random.choice(MIRACLES)
        _apply_fortune_effects(state, miracle["effects"])
        return ("miracle", miracle["name"], miracle["text"])

    if roll < miracle_chance + curse_chance:
        curse = random.choice(CURSES)
        _apply_fortune_effects(state, curse["effects"])
        return ("curse", curse["name"], curse["text"])

    return None


def _apply_fortune_effects(state: GameState, effects: dict) -> None:
    """Apply fortune effects to the game state."""
    civ = state.civilization

    if "food" in effects:
        civ.food = max(0, civ.food + effects["food"])
    if "food_zero" in effects:
        civ.food = 0
    if "population" in effects:
        civ.population = max(0, civ.population + effects["population"])
    if "shelter" in effects:
        civ.shelter = max(0, civ.shelter + effects["shelter"])
    if "chaos" in effects:
        state.apply_chaos(effects["chaos"])
    if "knowledge" in effects:
        civ.knowledge = max(0, civ.knowledge + effects["knowledge"])
    if "loyalty_all" in effects:
        state.apply_loyalty_all(effects["loyalty_all"])
    if "loyalty_boost" in effects:
        # Boost a random NPC's loyalty
        alive = [n for n in state.npcs if n.alive]
        if alive:
            npc = random.choice(alive)
            npc.loyalty = min(1.0, npc.loyalty + effects["loyalty_boost"])
    if "loyalty_betray" in effects:
        # Drop a random NPC's loyalty to near zero
        alive = [n for n in state.npcs if n.alive and n.loyalty > 0.3]
        if alive:
            npc = random.choice(alive)
            npc.loyalty = 0.1
