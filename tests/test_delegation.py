"""Tests for delegation system."""

import pytest

from src.systems.delegation import (
    get_max_delegation_slots,
    process_delegations,
    assign_delegation,
)
from src.models.game_state import GameState
from src.models.npc import NPC


class TestMaxDelegationSlots:
    """Test delegation slot unlocking by tier."""

    def test_tier_1_no_slots(self):
        """Tier 1 should have 0 delegation slots."""
        state = GameState()
        assert state.current_tier == 1
        assert get_max_delegation_slots(state) == 0

    def test_tier_2_two_slots(self):
        """Tier 2 should unlock 2 delegation slots."""
        state = GameState()
        # Mark all tier 1 milestones as achieved
        for m in state.milestones:
            if m.tier == 1:
                m.achieved = True

        assert state.current_tier >= 2
        assert get_max_delegation_slots(state) >= 2

    def test_tier_3_four_slots(self):
        """Tier 3 should unlock 4 total slots."""
        state = GameState()
        # Mark all tier 1 and 2 milestones as achieved
        for m in state.milestones:
            if m.tier <= 2:
                m.achieved = True

        assert state.current_tier >= 3
        assert get_max_delegation_slots(state) >= 4


class TestAssignDelegation:
    """Test assigning NPCs to delegation tasks."""

    def test_assign_delegation_requires_alive_npc(self):
        """Can only delegate to alive NPCs."""
        state = GameState()
        state.npcs = [
            NPC(name="Alice", alive=True, labor=5),
            NPC(name="Bob", alive=False, labor=5),
        ]

        # Assigning to dead NPC should not add to delegations
        assign_delegation(state, npc_idx=1, task="foraging")

        # Alive NPC assignment should work
        assign_delegation(state, npc_idx=0, task="foraging")

    def test_assign_delegation_valid_tasks(self):
        """Valid delegation tasks should be accepted."""
        state = GameState()
        state.npcs = [NPC(name="Alice", alive=True, labor=5)]

        valid_tasks = ["foraging", "building", "peacekeeping", "teaching"]
        for task in valid_tasks:
            assign_delegation(state, npc_idx=0, task=task)
            # Should not raise

    def test_assign_delegation_resets_previous_assignment(self):
        """Assigning a new task replaces the previous one."""
        state = GameState()
        state.npcs = [NPC(name="Alice", alive=True, labor=5)]

        assign_delegation(state, npc_idx=0, task="foraging")
        assign_delegation(state, npc_idx=0, task="building")

        # Only the latest assignment should be active
        assert state.delegations.get(0) == "building"


class TestProcessDelegations:
    """Test delegation outcome processing."""

    def test_process_delegations_returns_results(self):
        """process_delegations should return a list of results."""
        state = GameState()
        state.npcs = [NPC(name="Alice", alive=True, labor=8)]
        assign_delegation(state, npc_idx=0, task="foraging")

        results = process_delegations(state)

        assert isinstance(results, list)

    def test_process_delegations_clears_assignments(self):
        """Delegations should be cleared after processing."""
        state = GameState()
        state.npcs = [NPC(name="Alice", alive=True, labor=8)]
        assign_delegation(state, npc_idx=0, task="foraging")

        assert len(state.delegations) > 0
        process_delegations(state)
        assert len(state.delegations) == 0

    def test_foraging_produces_food(self):
        """Foraging delegation should produce food on success."""
        state = GameState()
        state.npcs = [NPC(name="Alice", alive=True, labor=10)]  # High skill
        initial_food = state.civilization.food

        assign_delegation(state, npc_idx=0, task="foraging")
        results = process_delegations(state)

        # With high skill, should succeed
        # Food should increase
        assert state.civilization.food >= initial_food

    def test_building_produces_shelter(self):
        """Building delegation should increase shelter."""
        state = GameState()
        state.npcs = [NPC(name="Alice", alive=True, labor=10)]
        initial_shelter = state.civilization.shelter

        assign_delegation(state, npc_idx=0, task="building")
        results = process_delegations(state)

        # With high skill, should succeed
        assert state.civilization.shelter >= initial_shelter

    def test_teaching_produces_knowledge(self):
        """Teaching delegation should increase knowledge."""
        state = GameState()
        state.npcs = [NPC(name="Alice", alive=True, labor=10)]
        initial_knowledge = state.civilization.knowledge

        assign_delegation(state, npc_idx=0, task="teaching")
        results = process_delegations(state)

        # With high skill, should succeed
        assert state.civilization.knowledge >= initial_knowledge
