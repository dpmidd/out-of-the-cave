"""Tests for dice roll and skill check system."""

import pytest

from src.systems.dice import roll
from src.models.game_state import GameState


class TestRollMechanics:
    """Test d10 + attribute + chaos against target difficulty."""

    def test_roll_succeeds_with_high_attribute(self):
        """High attribute should frequently exceed target."""
        attribute = 8  # Very high
        difficulty = 5
        chaos = 0.0

        successes = sum(
            1 for _ in range(100)
            if roll(attribute, difficulty, chaos)
        )
        # Should succeed most of the time
        assert successes > 70

    def test_roll_fails_with_low_attribute(self):
        """Low attribute should frequently fail to meet target."""
        attribute = 1  # Very low
        difficulty = 8
        chaos = 0.0

        successes = sum(
            1 for _ in range(100)
            if roll(attribute, difficulty, chaos)
        )
        # Should fail most of the time
        assert successes < 30

    def test_roll_with_positive_chaos_helps(self):
        """Positive chaos (luck) should increase success rate."""
        attribute = 5
        difficulty = 6
        chaos_neutral = 0.0
        chaos_lucky = 0.5

        successes_neutral = sum(
            1 for _ in range(100)
            if roll(attribute, difficulty, chaos_neutral)
        )
        successes_lucky = sum(
            1 for _ in range(100)
            if roll(attribute, difficulty, chaos_lucky)
        )

        # Lucky chaos should help
        assert successes_lucky > successes_neutral

    def test_roll_with_negative_chaos_hurts(self):
        """Negative chaos (bad luck) should decrease success rate."""
        attribute = 5
        difficulty = 6
        chaos_neutral = 0.0
        chaos_unlucky = -0.5

        successes_neutral = sum(
            1 for _ in range(100)
            if roll(attribute, difficulty, chaos_neutral)
        )
        successes_unlucky = sum(
            1 for _ in range(100)
            if roll(attribute, difficulty, chaos_unlucky)
        )

        # Unlucky chaos should hurt
        assert successes_unlucky < successes_neutral

    def test_roll_returns_boolean(self):
        """Roll should return True (success) or False (failure)."""
        result = roll(attribute=5, difficulty=5, chaos=0.0)
        assert isinstance(result, bool)

    def test_roll_extreme_values(self):
        """Test edge cases."""
        # Max attribute vs low difficulty should always succeed
        for _ in range(10):
            assert roll(attribute=10, difficulty=2, chaos=0.0) is True

        # Low attribute vs high difficulty should always fail
        for _ in range(10):
            assert roll(attribute=1, difficulty=10, chaos=0.0) is False
