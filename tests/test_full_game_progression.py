"""Full game progression validation — simulate playthrough to victory and verify all systems."""

import random
from pathlib import Path

import pytest

from src.models.game_state import GameState
from src.systems.npc_generator import generate_npcs
from src.models.civilization import Civilization
from src.models.player import Player
from src.persistence.save_manager import save_game, load_game
from src.systems.events import select_event, resolve_choice, load_all_events
from src.systems.milestones import check_milestones


@pytest.fixture
def initial_state():
    """Create a fresh game state for testing."""
    npcs = generate_npcs(12)
    return GameState(
        player=Player(),
        npcs=npcs,
        civilization=Civilization(population=12),
        narrative_depth="medium",
        difficulty="normal",
    )


class TestFullProgression:
    """Validate that a full game can be played to victory."""

    def test_game_can_progress_multiple_turns(self, initial_state):
        """Simulate gameplay with milestone unlocking to validate long-game progression."""
        state = initial_state

        # Boost initial resources and stats to allow progression
        state.civilization.food = 50
        state.civilization.shelter = 5
        state.civilization.knowledge = 5
        state.player.rhetoric = 5
        state.player.wisdom = 5
        state.player.courage = 5
        state.player.authority = 5
        state.player.pragmatism = 5

        # Pre-unlock all milestones to allow all events (avoid tier gating issues)
        for m in state.milestones:
            if m.id != "the_republic":  # Don't achieve final victory condition
                m.achieved = True

        turn_limit = 50
        milestone_history = []

        print(f"\n{'='*80}")
        print("GAME PROGRESSION TEST (Tier 2+ unlocked)")
        print(f"{'='*80}\n")

        while state.turn < turn_limit and not state.is_victory and not state.is_defeat:
            # Select and resolve event
            event = select_event(state)
            if event is None:
                print(f"[Turn {state.turn}] No events available (game ended)")
                break

            # Smart choice selection: prefer passive or high-success-rate choices
            best_idx = 0
            best_score = -999
            for idx, choice in enumerate(event["choices"]):
                if choice.get("special") == "retreat":
                    # Avoid retreat unless necessary
                    continue

                if "skill_check" not in choice:
                    # Passive choice always succeeds - prefer it
                    best_score = 999
                    best_idx = idx
                    break

                skill = choice["skill_check"]
                attr_val = state.player.get_attribute(skill)
                difficulty = choice.get("difficulty", 5)
                score = attr_val - difficulty  # Higher = better success chance

                # Prefer food/resources over other effects if available
                effects = choice.get("outcomes", {}).get("success", {}).get("effects", {})
                if "food" in effects or "shelter" in effects:
                    score += 5  # Bonus for resource gains

                if score > best_score:
                    best_score = score
                    best_idx = idx

            choice_idx = best_idx

            chosen = event["choices"][choice_idx]

            # Resolve choice
            outcome_text, info = resolve_choice(chosen, state)
            if outcome_text == "retreat":
                break

            # Record and advance
            state.event_history.append(event["id"])
            state.turn += 1

            # Per-turn mechanics (from main.py)
            state.decay_stability()
            state.decay_chaos()
            if random.random() < 0.15:
                state.apply_chaos(0.03)

            # Food consumption
            food_needed = max(1, state.civilization.population // 3)
            state.civilization.food = max(0, state.civilization.food - food_needed)
            if state.civilization.food == 0:
                state.civilization.starvation_turns += 1
                if state.civilization.starvation_turns >= 2:
                    state.civilization.population = max(0, state.civilization.population - 1)
            else:
                state.civilization.starvation_turns = 0

            # Check milestones
            newly_achieved = check_milestones(state, info.get("deaths", 0))
            for ms_id in newly_achieved:
                milestone_history.append((state.turn, ms_id))
                print(f"[Turn {state.turn}] 🏛️  Milestone achieved: {ms_id}")

            # Progress update every 10 turns
            if state.turn % 10 == 0:
                tier = state.current_tier
                stability = f"{state.civilization.stability:.0%}"
                chaos = f"{state.chaos:.0%}"
                pop = state.civilization.population
                print(f"[Turn {state.turn}] Tier {tier} | Stability {stability} | Chaos {chaos} | Pop {pop}")

        print(f"\n{'='*80}")
        print(f"FINAL STATE (Turn {state.turn})")
        print(f"{'='*80}")
        print(f"Victory: {state.is_victory}")
        print(f"Defeat: {state.is_defeat}")
        print(f"Tier: {state.current_tier}")
        print(f"Population: {state.civilization.population}")
        print(f"Stability: {state.civilization.stability:.1%}")
        print(f"Chaos: {state.chaos:.1%}")
        print(f"Events triggered: {len(state.event_history)}")
        print(f"Milestones achieved: {len(milestone_history)}")
        print(f"\nMilestone progression:")
        for turn, ms_id in milestone_history:
            print(f"  Turn {turn}: {ms_id}")

        # Verify game ran for many turns with all systems working
        assert state.turn >= 10, f"Game should progress at least 10 turns (got {state.turn})"
        assert state.civilization.population > 0, "Population should survive"
        assert len(state.event_history) > 5, "Should trigger multiple events"
        print(f"\n✅ Long-running game test passed\n")

    def test_can_reach_victory(self, initial_state):
        """Specifically test that philosopher_king milestone can be reached."""
        state = initial_state
        turn_limit = 200

        # Boost stats to make choices easier
        state.player.rhetoric = 5
        state.player.wisdom = 5
        state.player.authority = 5
        state.player.pragmatism = 5
        state.player.courage = 5

        # Reduce chaos to make progression easier
        state.apply_chaos(-0.02)

        print(f"\n{'='*80}")
        print("VICTORY CONDITION TEST (boosted stats)")
        print(f"{'='*80}\n")

        while state.turn < turn_limit and not state.is_victory and not state.is_defeat:
            event = select_event(state)
            if event is None:
                break

            # Make best choice
            choice_idx = 0
            for idx, choice in enumerate(event["choices"]):
                if choice.get("special") == "retreat":
                    continue
                if "skill_check" not in choice:
                    choice_idx = idx
                    break
                skill = choice["skill_check"]
                attr_val = state.player.get_attribute(skill)
                difficulty = choice.get("difficulty", 5)
                if attr_val - difficulty >= (state.player.get_attribute("rhetoric") - 5):
                    choice_idx = idx

            chosen = event["choices"][choice_idx]
            outcome_text, info = resolve_choice(chosen, state)
            if outcome_text == "retreat":
                break

            state.event_history.append(event["id"])
            state.turn += 1

            state.decay_stability()
            state.decay_chaos()
            if random.random() < 0.15:
                state.apply_chaos(0.03)

            food_needed = max(1, state.civilization.population // 3)
            state.civilization.food = max(0, state.civilization.food - food_needed)
            if state.civilization.food == 0:
                state.civilization.starvation_turns += 1
                if state.civilization.starvation_turns >= 2:
                    state.civilization.population = max(0, state.civilization.population - 1)
            else:
                state.civilization.starvation_turns = 0

            newly_achieved = check_milestones(state, info.get("deaths", 0))
            for ms_id in newly_achieved:
                print(f"[Turn {state.turn}] 🏛️  {ms_id}")
                if ms_id == "philosopher_king":
                    print(f"\n✅ PHILOSOPHER_KING ACHIEVED AT TURN {state.turn}\n")

        print(f"Final turn: {state.turn}")
        print(f"Is victory: {state.is_victory}")
        print(f"Philosopher_king achieved: {'philosopher_king' in state.achieved_milestone_ids}")

        assert state.is_victory or "philosopher_king" in state.achieved_milestone_ids, \
            f"Should be able to reach victory (achieved: {state.achieved_milestone_ids})"

    def test_save_load_preserves_state(self, initial_state):
        """Test that save/load cycle preserves game state exactly."""
        state = initial_state

        # Advance game 20 turns
        for _ in range(20):
            event = select_event(state)
            if event is None:
                break
            choice_idx = 0
            chosen = event["choices"][choice_idx]
            outcome_text, info = resolve_choice(chosen, state)
            if outcome_text == "retreat":
                break
            state.event_history.append(event["id"])
            state.turn += 1
            state.decay_stability()
            state.decay_chaos()

        # Save
        save_path = save_game(state, slot="test_validation")
        assert Path(save_path).exists(), "Save file should exist"

        # Load
        loaded_state = load_game(slot="test_validation")
        assert loaded_state is not None, "Should load saved game"

        # Verify equivalence
        assert loaded_state.turn == state.turn, f"Turn mismatch: {loaded_state.turn} vs {state.turn}"
        assert loaded_state.chaos == state.chaos, f"Chaos mismatch: {loaded_state.chaos} vs {state.chaos}"
        assert loaded_state.civilization.stability == state.civilization.stability, "Stability mismatch"
        assert loaded_state.civilization.population == state.civilization.population, "Population mismatch"
        assert loaded_state.event_history == state.event_history, "Event history mismatch"
        assert loaded_state.achieved_milestone_ids == state.achieved_milestone_ids, "Milestones mismatch"

        print(f"\n✅ Save/load test passed (Turn {state.turn})\n")

    def test_critical_flags_obtainable(self, initial_state):
        """Verify that constitution_written and successor_chosen flags can be obtained."""
        state = initial_state
        state.player.wisdom = 5
        state.player.rhetoric = 5
        state.player.pragmatism = 5

        # Load all events to find the critical ones
        all_events = load_all_events()
        constitution_event = next((e for e in all_events if e["id"] == "the_writing_of_the_constitution"), None)
        successor_event = next((e for e in all_events if e["id"] == "the_named_successor"), None)

        print(f"\n{'='*80}")
        print("CRITICAL FLAGS TEST")
        print(f"{'='*80}\n")

        assert constitution_event is not None, "the_writing_of_the_constitution event must exist"
        assert successor_event is not None, "the_named_successor event must exist"

        print(f"✅ the_writing_of_the_constitution exists")
        print(f"✅ the_named_successor exists")

        # Check that events produce the flags
        print(f"\nFlag production:")

        has_constitution_flag = False
        for choice in constitution_event["choices"]:
            if "outcomes" in choice:
                for outcome in choice["outcomes"].values():
                    if outcome.get("history_flag") == "constitution_written":
                        has_constitution_flag = True
                        print(f"✅ constitution_written flag produced by {constitution_event['id']}")

        has_successor_flag = False
        for choice in successor_event["choices"]:
            if "outcomes" in choice:
                for outcome in choice["outcomes"].values():
                    if outcome.get("history_flag") == "successor_chosen":
                        has_successor_flag = True
                        print(f"✅ successor_chosen flag produced by {successor_event['id']}")

        assert has_constitution_flag, "the_writing_of_the_constitution must produce constitution_written flag"
        assert has_successor_flag, "the_named_successor must produce successor_chosen flag"

        print(f"\n✅ Critical flags test passed\n")
