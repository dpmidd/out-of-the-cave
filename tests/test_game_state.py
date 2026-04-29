"""Tests for GameState and core game mechanics."""

import pytest

from src.models.game_state import GameState
from src.models.npc import NPC
from src.models.civilization import Civilization


class TestGameStateCreation:
    """Test GameState initialization and defaults."""

    def test_default_state_creation(self):
        state = GameState()
        assert state.turn == 0
        assert state.chaos == 0.05
        assert state.narrative_depth == "medium"
        assert state.difficulty == "normal"

    def test_state_with_custom_values(self):
        state = GameState(turn=10, narrative_depth="high", difficulty="hard")
        assert state.turn == 10
        assert state.narrative_depth == "high"
        assert state.difficulty == "hard"

    def test_state_serializes_to_dict(self):
        """GameState (Pydantic) must serialize for save/load."""
        state = GameState(turn=5)
        data = state.model_dump()
        assert data["turn"] == 5
        assert "chaos" in data
        assert "npcs" in data


class TestChaosLabel:
    """Test chaos level labeling."""

    def test_chaos_label_calm(self):
        state = GameState()
        state.chaos = 0.05
        assert state.chaos_label == "Calm"

    def test_chaos_label_uneasy(self):
        state = GameState()
        state.chaos = 0.15
        assert state.chaos_label == "Uneasy"

    def test_chaos_label_simmering(self):
        state = GameState()
        state.chaos = 0.5
        assert state.chaos_label == "Simmering"

    def test_chaos_label_volatile(self):
        state = GameState()
        state.chaos = 0.7
        assert state.chaos_label == "Volatile"

    def test_chaos_label_anarchy(self):
        state = GameState()
        state.chaos = 0.95
        assert state.chaos_label == "Anarchy"


class TestApplyChaos:
    """Test chaos application with clamping."""

    def test_apply_chaos_increases_value(self):
        state = GameState()
        state.chaos = 0.2
        state.apply_chaos(0.1)
        assert state.chaos == 0.3

    def test_apply_chaos_negative_decreases_value(self):
        state = GameState()
        state.chaos = 0.5
        state.apply_chaos(-0.2)
        assert state.chaos == 0.3

    def test_apply_chaos_clamps_at_zero(self):
        state = GameState()
        state.chaos = 0.05
        state.apply_chaos(-0.1)
        assert state.chaos == 0.0

    def test_apply_chaos_clamps_at_one(self):
        state = GameState()
        state.chaos = 0.95
        state.apply_chaos(0.1)
        assert state.chaos == 1.0


class TestDecayChaos:
    """Test per-turn chaos decay."""

    def test_decay_chaos_normal_mode(self):
        state = GameState(difficulty="normal")
        state.chaos = 0.5
        state.decay_chaos()
        # Normal: 0.01 decay per turn
        assert state.chaos == pytest.approx(0.49)

    def test_decay_chaos_hard_mode_slower(self):
        state = GameState(difficulty="hard")
        state.chaos = 0.5
        state.decay_chaos()
        # Hard: 0.005 decay per turn (slower)
        assert state.chaos == pytest.approx(0.495)

    def test_decay_chaos_respects_tier_floor(self):
        """Chaos cannot decay below tier-based floor."""
        state = GameState(difficulty="normal")
        # Tier 2: floor = 0.02 * 2 = 0.04
        state.chaos = 0.03
        state.decay_chaos()
        # Should clamp to floor, not go negative
        assert state.chaos == pytest.approx(0.04)


class TestDecayStability:
    """Test per-turn stability erosion."""

    def test_decay_stability_applies_base_erosion(self):
        state = GameState()
        state.civilization.stability = 1.0
        state.decay_stability()
        # Base erosion is 0.02, so stability should drop
        assert state.civilization.stability < 1.0

    def test_decay_stability_harder_with_population(self):
        state = GameState()
        state.civilization.stability = 1.0
        state.civilization.population = 20
        state.decay_stability()
        initial = 1.0

        state2 = GameState()
        state2.civilization.stability = 1.0
        state2.civilization.population = 5
        state2.decay_stability()

        # Higher population should erode more
        assert state.civilization.stability < state2.civilization.stability

    def test_decay_stability_chaotic_reduces_faster(self):
        state = GameState()
        state.chaos = 0.8
        state.civilization.stability = 1.0
        state.decay_stability()

        state2 = GameState()
        state2.chaos = 0.1
        state2.civilization.stability = 1.0
        state2.decay_stability()

        # High chaos should erode more
        assert state.civilization.stability < state2.civilization.stability


class TestVictoryDefeat:
    """Test victory and defeat conditions."""

    def test_victory_on_philosopher_king_milestone(self):
        state = GameState()
        # Mark philosopher_king as achieved
        for milestone in state.milestones:
            if milestone.id == "philosopher_king":
                milestone.achieved = True

        assert state.is_victory is True

    def test_defeat_on_zero_population(self):
        state = GameState()
        state.civilization.population = 0
        assert state.is_defeat is True

    def test_defeat_on_max_chaos(self):
        state = GameState()
        state.chaos = 1.0
        assert state.is_defeat is True

    def test_not_defeat_with_positive_pop_and_low_chaos(self):
        state = GameState()
        state.civilization.population = 5
        state.chaos = 0.5
        assert state.is_defeat is False


class TestAchievedMilestones:
    """Test milestone tracking."""

    def test_achieved_milestone_ids_property(self):
        state = GameState()
        # Mark some milestones as achieved
        achieved_count = 0
        for milestone in state.milestones[:3]:
            milestone.achieved = True
            achieved_count += 1

        achieved_ids = state.achieved_milestone_ids
        assert len(achieved_ids) == achieved_count

    def test_achieved_milestone_ids_updates_dynamically(self):
        state = GameState()
        initial_count = len(state.achieved_milestone_ids)

        state.milestones[0].achieved = True
        assert len(state.achieved_milestone_ids) == initial_count + 1


class TestApplyLoyaltyAll:
    """Test loyalty changes across all NPCs."""

    def test_apply_loyalty_all_increases(self):
        state = GameState()
        # Create some NPCs
        state.npcs = [
            NPC(name="Alice", loyalty=0.5),
            NPC(name="Bob", loyalty=0.3),
        ]
        state.apply_loyalty_all(0.1)

        assert state.npcs[0].loyalty == 0.6
        assert state.npcs[1].loyalty == 0.4

    def test_apply_loyalty_all_clamps_at_one(self):
        state = GameState()
        state.npcs = [NPC(name="Alice", loyalty=0.95)]
        state.apply_loyalty_all(0.2)
        assert state.npcs[0].loyalty == 1.0

    def test_apply_loyalty_all_clamps_at_zero(self):
        state = GameState()
        state.npcs = [NPC(name="Alice", loyalty=0.05)]
        state.apply_loyalty_all(-0.1)
        assert state.npcs[0].loyalty == 0.0

    def test_apply_loyalty_all_only_affects_alive_npcs(self):
        state = GameState()
        state.npcs = [
            NPC(name="Alice", loyalty=0.5, alive=True),
            NPC(name="Bob", loyalty=0.5, alive=False),
        ]
        state.apply_loyalty_all(0.1)

        assert state.npcs[0].loyalty == 0.6
        assert state.npcs[1].loyalty == 0.5  # Unchanged (dead)
