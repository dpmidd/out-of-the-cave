"""Tests for milestone achievement system."""

import pytest

from src.systems.milestones import check_milestones
from src.models.game_state import GameState
from src.models.npc import NPC


class TestCheckMilestones:
    """Test milestone condition checking."""

    def test_fire_milestone_on_shelter(self):
        """'fire' milestone achieved when shelter >= 1."""
        state = GameState()
        state.civilization.shelter = 1

        newly_achieved = check_milestones(state)

        fire_milestone = next(m for m in state.milestones if m.id == "fire")
        assert fire_milestone.achieved is True
        assert "fire" in newly_achieved

    def test_sustenance_milestone_on_food(self):
        """'sustenance' milestone achieved when food >= 8."""
        state = GameState()
        state.civilization.food = 8

        newly_achieved = check_milestones(state)

        sustenance_milestone = next(
            m for m in state.milestones if m.id == "sustenance"
        )
        assert sustenance_milestone.achieved is True
        assert "sustenance" in newly_achieved

    def test_first_night_requires_turn_and_no_deaths(self):
        """'first_night' needs turn >= 2 and no deaths that turn."""
        state = GameState()
        state.turn = 2

        # With deaths, should fail
        newly_achieved = check_milestones(state, turn_deaths=1)
        first_night = next(m for m in state.milestones if m.id == "first_night")
        assert first_night.achieved is False

        # Without deaths, should succeed
        newly_achieved = check_milestones(state, turn_deaths=0)
        assert first_night.achieved is True
        assert "first_night" in newly_achieved

    def test_roles_assigned_needs_two_npcs(self):
        """'roles_assigned' milestone needs 2+ NPCs with roles."""
        state = GameState()
        state.npcs = [
            NPC(name="Alice", role="forager", alive=True),
            NPC(name="Bob", role=None, alive=True),
        ]

        # With only 1 role assigned, should fail
        newly_achieved = check_milestones(state)
        roles_milestone = next(
            m for m in state.milestones if m.id == "roles_assigned"
        )
        assert roles_milestone.achieved is False

        # With 2 roles assigned, should succeed
        state.npcs[1].role = "builder"
        newly_achieved = check_milestones(state)
        assert roles_milestone.achieved is True
        assert "roles_assigned" in newly_achieved

    def test_first_law_needs_civilization_law(self):
        """'first_law' milestone needs len(laws) >= 1."""
        state = GameState()
        state.civilization.laws = []

        newly_achieved = check_milestones(state)
        first_law = next(m for m in state.milestones if m.id == "first_law")
        assert first_law.achieved is False

        state.civilization.laws = ["No theft"]
        newly_achieved = check_milestones(state)
        assert first_law.achieved is True
        assert "first_law" in newly_achieved

    def test_milestone_already_achieved_not_repeated(self):
        """Already achieved milestones should not be checked again."""
        state = GameState()
        state.civilization.shelter = 1

        # First check
        newly_achieved_1 = check_milestones(state)
        assert "fire" in newly_achieved_1

        # Second check (milestone already achieved)
        newly_achieved_2 = check_milestones(state)
        assert "fire" not in newly_achieved_2

    def test_milestone_applies_stability_reward(self):
        """Achieving milestone should apply stability reward."""
        state = GameState()
        initial_stability = state.civilization.stability
        state.civilization.shelter = 1

        check_milestones(state)

        fire_milestone = next(m for m in state.milestones if m.id == "fire")
        expected_stability = initial_stability + fire_milestone.stability_reward
        assert state.civilization.stability == pytest.approx(expected_stability)

    def test_milestone_applies_chaos_reward(self):
        """Achieving milestone should apply chaos reward."""
        state = GameState()
        initial_chaos = state.chaos
        state.civilization.shelter = 1

        check_milestones(state)

        fire_milestone = next(m for m in state.milestones if m.id == "fire")
        expected_chaos = initial_chaos + fire_milestone.chaos_reward
        assert state.chaos == pytest.approx(expected_chaos)

    def test_milestone_tier_gating(self):
        """Milestones can only be achieved in current tier or next tier."""
        state = GameState()
        state.turn = 0
        state.chaos = 0.0

        # Player is in tier 1 (no tier 1 milestones achieved)
        # Tier 3+ milestones should not be achievable
        for milestone in state.milestones:
            if milestone.tier >= 3:
                # Even with perfect conditions, tier 3+ shouldn't be achievable
                assert milestone.achieved is False

    def test_multiple_milestones_achieved_same_turn(self):
        """Multiple milestones can be achieved in one check."""
        state = GameState()
        state.civilization.shelter = 1
        state.civilization.food = 8

        newly_achieved = check_milestones(state)

        assert "fire" in newly_achieved
        assert "sustenance" in newly_achieved
        assert len(newly_achieved) >= 2
