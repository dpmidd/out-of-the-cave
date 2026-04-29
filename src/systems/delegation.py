"""Delegation system — entrust NPCs with ongoing tasks for passive per-turn output."""

from __future__ import annotations

import random
from dataclasses import dataclass

from src.models.game_state import GameState
from src.models.npc import NPC


# Tasks NPCs can be delegated to
TASKS = {
    "foraging": {
        "label": "Foraging",
        "description": "Gather food from the surrounding land",
        "skill": "scouting",
        "output": "food",
        "base_yield": 2,
    },
    "building": {
        "label": "Building",
        "description": "Construct and maintain shelters",
        "skill": "labor",
        "output": "shelter",
        "base_yield": 1,
    },
    "peacekeeping": {
        "label": "Peacekeeping",
        "description": "Patrol the settlement and resolve disputes",
        "skill": "combat",
        "output": "chaos_reduction",
        "base_yield": 0.04,
    },
    "teaching": {
        "label": "Teaching",
        "description": "Share knowledge and train others",
        "skill": "wisdom",
        "output": "knowledge",
        "base_yield": 1,
    },
}


def get_max_delegation_slots(state: GameState) -> int:
    """How many NPCs can be delegated, based on tier progression."""
    tier = state.current_tier
    if tier >= 5:
        return 8
    elif tier >= 4:
        return 6
    elif tier >= 3:
        return 4
    elif tier >= 2:
        return 2
    else:
        return 0


def get_delegated_npcs(state: GameState) -> list[NPC]:
    """Get all NPCs currently assigned to delegation tasks."""
    return [n for n in state.npcs if n.alive and n.role in TASKS]


def get_available_for_delegation(state: GameState) -> list[NPC]:
    """Get NPCs that can be assigned to a delegation task."""
    # NPCs with no role or with a non-delegation role (like council_member) can't be reassigned
    # Only unassigned NPCs or those in delegation roles can be moved
    delegation_roles = set(TASKS.keys())
    return [
        n for n in state.npcs
        if n.alive and (n.role is None or n.role in delegation_roles)
    ]


def assign_delegation(state: GameState, npc_idx: int, task: str) -> None:
    """Assign an NPC to a delegation task. Replace any previous assignment."""
    if npc_idx < 0 or npc_idx >= len(state.npcs):
        return

    npc = state.npcs[npc_idx]
    if not npc.alive:
        return

    if task not in TASKS:
        return

    state.delegations[npc_idx] = task


def get_npc_task_impression(npc: NPC, task_id: str) -> str:
    """Describe how well-suited an NPC seems for a task (without revealing exact stats)."""
    task = TASKS[task_id]
    skill_val = npc.skills.get(task["skill"], 0)

    if skill_val >= 7:
        fit = "seems born for this work"
    elif skill_val >= 5:
        fit = "could handle this reasonably well"
    elif skill_val >= 3:
        fit = "might manage, with effort"
    else:
        fit = "would struggle with this"

    if npc.loyalty >= 0.7:
        trust = "and you trust them"
    elif npc.loyalty >= 0.4:
        trust = "though their commitment is uncertain"
    else:
        trust = "but their loyalty is questionable"

    return f"{npc.name} {fit}, {trust}."


@dataclass
class DelegationResult:
    npc_name: str
    task_label: str
    success: bool
    description: str
    effects: dict


def process_delegations(state: GameState) -> list[DelegationResult]:
    """Process all delegation tasks for this turn. Returns results."""
    results = []

    for npc_idx, task_id in state.delegations.items():
        if npc_idx < 0 or npc_idx >= len(state.npcs):
            continue

        npc = state.npcs[npc_idx]
        if not npc.alive or task_id not in TASKS:
            continue

        task = TASKS[task_id]
        result = _resolve_delegation(npc, task, state.chaos)
        results.append(result)

        # Apply effects
        civ = state.civilization
        if result.success:
            match task["output"]:
                case "food":
                    civ.food += result.effects.get("food", 0)
                case "shelter":
                    civ.shelter += result.effects.get("shelter", 0)
                case "knowledge":
                    civ.knowledge += result.effects.get("knowledge", 0)
                case "chaos_reduction":
                    state.apply_chaos(result.effects.get("chaos", 0))
        else:
            # Failed delegation can cause chaos
            if "chaos" in result.effects:
                state.apply_chaos(result.effects["chaos"])
            if "loyalty" in result.effects:
                npc.loyalty = max(0.0, min(1.0, npc.loyalty + result.effects["loyalty"]))

    state.delegations.clear()
    return results


def _resolve_delegation(npc: NPC, task: dict, chaos: float) -> DelegationResult:
    """Resolve a single NPC's delegation task."""
    skill_val = npc.skills.get(task["skill"], 0)
    base_yield = task["base_yield"]

    # Success chance: skill provides base, loyalty scales it, chaos undermines it
    # skill 1-9 maps to 0.2-0.9 base chance
    skill_chance = 0.1 + skill_val * 0.08
    loyalty_mult = 0.5 + npc.loyalty * 0.5  # loyalty 0 = 50% effectiveness, loyalty 1 = 100%
    chaos_penalty = chaos * 0.3  # high chaos reduces effectiveness

    success_chance = min(0.95, max(0.1, skill_chance * loyalty_mult - chaos_penalty))
    success = random.random() < success_chance

    if success:
        # Yield scales with skill
        yield_mult = 0.5 + skill_val * 0.1  # skill 5 = 1.0x, skill 9 = 1.4x
        actual_yield = base_yield * yield_mult

        if isinstance(base_yield, float):
            # Chaos reduction
            effects = {"chaos": -round(actual_yield, 3)}
            desc = f"{npc.name} keeps the peace. Tensions ease."
        elif task["output"] == "knowledge":
            effects = {"knowledge": max(1, int(actual_yield))}
            desc = f"{npc.name} teaches well. Understanding grows."
        elif task["output"] == "food":
            effects = {"food": max(1, int(actual_yield))}
            desc = f"{npc.name} returns with provisions."
        else:  # shelter
            # Shelter gains are slow — only sometimes yield
            if random.random() < 0.4 + skill_val * 0.05:
                effects = {"shelter": 1}
                desc = f"{npc.name} makes progress on the structures."
            else:
                effects = {}
                desc = f"{npc.name} works steadily. The shelters hold."

        # Successful delegation slowly builds loyalty
        npc.loyalty = min(1.0, npc.loyalty + 0.02)

        return DelegationResult(
            npc_name=npc.name,
            task_label=task["label"],
            success=True,
            description=desc,
            effects=effects,
        )
    else:
        # Failure — what goes wrong depends on loyalty
        if npc.loyalty < 0.3:
            # Low loyalty: sabotage or abandonment
            desc = f"{npc.name} neglects their duties. Trust erodes."
            effects = {"chaos": 0.03, "loyalty": -0.05}
        else:
            # Honest failure
            desc = f"{npc.name} tries but comes up short."
            effects = {"chaos": 0.01}

        return DelegationResult(
            npc_name=npc.name,
            task_label=task["label"],
            success=False,
            description=desc,
            effects=effects,
        )
