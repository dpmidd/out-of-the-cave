from __future__ import annotations

from src.models.game_state import GameState


def check_milestones(state: GameState, turn_deaths: int = 0) -> list[str]:
    """Check all unachieved milestones against current state.

    Returns list of milestone IDs that were just achieved.
    """
    newly_achieved = []

    for ms in state.milestones:
        if ms.achieved:
            continue

        # Can only achieve milestones in current or previous tiers
        if ms.tier > state.current_tier + 1:
            continue

        achieved = _check_condition(ms.id, state, turn_deaths)
        if achieved:
            ms.achieved = True
            state.apply_chaos(ms.chaos_reward)
            state.civilization.stability = max(
                0.0, min(1.0, state.civilization.stability + ms.stability_reward)
            )
            newly_achieved.append(ms.id)

    return newly_achieved


def _check_condition(milestone_id: str, state: GameState, turn_deaths: int) -> bool:
    """Evaluate whether a specific milestone's conditions are met."""
    civ = state.civilization
    achieved = state.achieved_milestone_ids

    match milestone_id:
        # --- Tier 1: Survival ---
        case "fire":
            return civ.shelter >= 1

        case "sustenance":
            return civ.food >= 8

        case "first_night":
            return state.turn >= 2 and turn_deaths == 0

        # --- Tier 2: Organization ---
        case "roles_assigned":
            assigned = sum(1 for n in state.npcs if n.alive and n.role is not None)
            return assigned >= 2

        case "first_law":
            return len(civ.laws) >= 1

        case "explored":
            return "explored" in state.event_history

        # --- Tier 3: Society ---
        case "council":
            leadership_roles = {"council_member", "enforcer", "speaker", "guardian"}
            leaders = sum(
                1 for n in state.npcs
                if n.alive and n.role in leadership_roles
            )
            return leaders >= 3

        case "conflict_resolved":
            return "conflict_resolved" in state.event_history

        case "agora":
            return civ.shelter >= 5

        case "education":
            return civ.knowledge >= 3

        case "specialization":
            alive_with_roles = [n for n in state.npcs if n.alive and n.role is not None]
            if len(alive_with_roles) < 5:
                return False
            distinct_roles = {n.role for n in alive_with_roles}
            return len(distinct_roles) >= 3

        # --- Tier 4: The Republic ---
        case "justice":
            justice_keywords = {"dispute resolution", "trial by council", "right of appeal"}
            return bool(justice_keywords & {law.lower() for law in civ.laws})

        case "guardian_class":
            guardian_count = sum(
                1 for n in state.npcs
                if n.alive and n.role in {"enforcer", "guardian"}
            )
            return guardian_count >= 2 and "council" in achieved and len(civ.laws) >= 1

        case "allegory_taught":
            return civ.knowledge >= 6 and "allegory_taught" in state.event_history

        case "three_laws":
            return len(civ.laws) >= 3

        case "philosopher_king":
            required = {"justice", "allegory_taught", "guardian_class"}
            return (
                "philosopher_king" in state.event_history
                and required.issubset(achieved)
                and civ.knowledge >= 8
            )

        # --- Tier 5: Legacy ---
        case "constitution":
            return (
                len(civ.laws) >= 5
                and civ.knowledge >= 10
                and "constitution_written" in state.event_history
            )

        case "succession":
            has_successor = any(
                n for n in state.npcs
                if n.alive and n.loyalty >= 0.8 and n.role in {"council_member", "speaker"}
            )
            return has_successor and "successor_chosen" in state.event_history

        case "the_republic":
            return (
                civ.stability >= 0.8
                and "philosopher_king" in achieved
                and civ.population >= 10
            )

        case _:
            return False
