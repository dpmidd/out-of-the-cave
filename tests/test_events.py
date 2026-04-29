"""Tests for event system and event selection."""

import pytest

from src.systems.events import select_event, resolve_choice
from src.models.game_state import GameState
from src.models.npc import NPC


class TestEventSelection:
    """Test event selection based on conditions."""

    def test_select_event_returns_dict_or_none(self):
        """select_event should return a dict (event) or None."""
        state = GameState()
        event = select_event(state)

        assert event is None or isinstance(event, dict)

    def test_select_event_respects_history(self):
        """Events in event_history should not be selected twice."""
        state = GameState()

        # Select an event
        event1 = select_event(state)
        if event1:
            event_id = event1["id"]
            state.event_history.append(event_id)

            # Select another
            event2 = select_event(state)
            if event2:
                # Should be different (or None if no more events available)
                assert event2["id"] != event_id or event2 is None

    def test_select_event_respects_tier(self):
        """Events should match current tier or be from lower tiers."""
        state = GameState()
        # Start in tier 1
        assert state.current_tier == 1

        event = select_event(state)
        if event:
            # Event tier should be <= current tier
            assert event.get("conditions", {}).get("tier", 1) <= state.current_tier

    def test_select_event_respects_population_minimum(self):
        """Events with min_population should only trigger with enough NPCs."""
        state = GameState()
        state.civilization.population = 2

        event = select_event(state)
        if event:
            min_pop = event.get("conditions", {}).get("min_population", 0)
            assert state.civilization.population >= min_pop


class TestResolveChoice:
    """Test choice resolution and outcome determination."""

    def test_resolve_choice_returns_text_and_info(self):
        """resolve_choice should return (outcome_text, info_dict)."""
        state = GameState()
        state.npcs = [NPC(name="Alice", alive=True)]

        # Create a mock choice
        choice = {
            "skill_check": "courage",
            "difficulty": 5,
            "outcomes": {
                "success": {
                    "text": "You succeeded.",
                    "effects": {},
                },
                "failure": {
                    "text": "You failed.",
                    "effects": {},
                },
            },
        }

        outcome_text, info = resolve_choice(choice, state)

        assert isinstance(outcome_text, str)
        assert isinstance(info, dict)
        assert outcome_text in ("You succeeded.", "You failed.")

    def test_resolve_choice_returns_success_flag(self):
        """Info dict should indicate success or failure."""
        state = GameState()
        state.npcs = [NPC(name="Alice", alive=True)]

        choice = {
            "skill_check": "courage",
            "difficulty": 5,
            "outcomes": {
                "success": {
                    "text": "Success",
                    "effects": {},
                },
                "failure": {
                    "text": "Failure",
                    "effects": {},
                },
            },
        }

        outcome_text, info = resolve_choice(choice, state)
        assert "success" in info
        assert isinstance(info["success"], bool)

    def test_resolve_choice_applies_effects(self):
        """Choice effects should modify state."""
        state = GameState()
        state.npcs = [NPC(name="Alice", alive=True)]
        initial_food = state.civilization.food

        choice = {
            "skill_check": "wisdom",
            "difficulty": 3,
            "outcomes": {
                "success": {
                    "text": "Success",
                    "effects": {
                        "food": 10,
                    },
                },
                "failure": {
                    "text": "Failure",
                    "effects": {
                        "food": 5,
                    },
                },
            },
        }

        outcome_text, info = resolve_choice(choice, state)

        # Food should have changed
        assert state.civilization.food != initial_food

    def test_resolve_choice_retreat_special(self):
        """'retreat' special choice should return "retreat" text."""
        state = GameState()
        state.npcs = [NPC(name="Alice", alive=True)]

        choice = {
            "skill_check": "pragmatism",
            "difficulty": 1,
            "special": "retreat",
            "outcomes": {
                "success": {"text": "You retreat.", "effects": {}},
                "failure": {"text": "You retreat.", "effects": {}},
            },
        }

        outcome_text, info = resolve_choice(choice, state)
        assert outcome_text == "retreat"

    def test_resolve_choice_records_history_flag(self):
        """History flags should be recorded in event_history."""
        state = GameState()
        state.npcs = [NPC(name="Alice", alive=True)]

        choice = {
            "skill_check": "courage",
            "difficulty": 1,
            "outcomes": {
                "success": {
                    "text": "Success",
                    "effects": {},
                    "history_flag": "test_flag",
                },
                "failure": {
                    "text": "Failure",
                    "effects": {},
                },
            },
        }

        initial_history = len(state.event_history)
        outcome_text, info = resolve_choice(choice, state)

        # If success, history flag should be recorded
        if info["success"]:
            assert "test_flag" in state.event_history

    def test_resolve_choice_applies_chaos_delta(self):
        """Choice chaos_delta should modify state chaos."""
        state = GameState()
        state.npcs = [NPC(name="Alice", alive=True)]
        initial_chaos = state.chaos

        choice = {
            "skill_check": "wisdom",
            "difficulty": 1,
            "chaos_delta": 0.2,
            "outcomes": {
                "success": {
                    "text": "Success",
                    "effects": {},
                },
                "failure": {
                    "text": "Failure",
                    "effects": {},
                },
            },
        }

        outcome_text, info = resolve_choice(choice, state)

        # Chaos should have increased
        assert state.chaos > initial_chaos
