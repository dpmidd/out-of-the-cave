"""Tests for the Ollama-backed narrative enhancement module."""

import pytest

from src.ai import narrator
from src.models.game_state import GameState


class TestShouldUseAI:
    """Test narrative_depth gating logic."""

    def test_ai_disabled_at_low_depth(self):
        state = GameState(narrative_depth="low")
        assert narrator.should_use_ai(state) is False

    def test_ai_disabled_at_medium_depth(self):
        state = GameState(narrative_depth="medium")
        assert narrator.should_use_ai(state) is False

    def test_ai_enabled_at_high_depth(self):
        state = GameState(narrative_depth="high")
        assert narrator.should_use_ai(state) is True

    def test_ai_enabled_at_very_high_depth(self):
        state = GameState(narrative_depth="very_high")
        assert narrator.should_use_ai(state) is True


class TestBuildContext:
    """Test game state context string generation."""

    def test_context_includes_turn_and_tier(self):
        state = GameState(turn=5)
        context = narrator._build_context(state)
        assert "Turn 5" in context
        assert "Tier" in context

    def test_context_includes_stability_and_chaos(self):
        state = GameState()
        state.civilization.stability = 0.75
        state.chaos = 0.05
        context = narrator._build_context(state)
        assert "Stability: 75%" in context
        assert "Calm" in context  # chaos_label at 0.05

    def test_context_includes_population(self):
        state = GameState()
        state.civilization.population = 12
        context = narrator._build_context(state)
        assert "Population: 12" in context

    def test_context_includes_recent_laws(self):
        state = GameState()
        state.civilization.laws = ["Law 1", "Law 2", "Law 3"]
        context = narrator._build_context(state)
        assert "Law 1" in context or "Law 3" in context


class TestEnhanceEventFallback:
    """Test event enhancement fallback when Ollama unavailable."""

    def test_enhance_event_returns_original_when_ollama_down(self):
        """With Ollama unavailable, return original text unchanged."""
        state = GameState(narrative_depth="high")
        original = "The cave grows cold. Shadows deepen."
        result = narrator.enhance_event(original, state, "Marcus")
        assert result == original

    def test_enhance_event_respects_depth_gate(self):
        """At low depth, return original without calling LLM."""
        state = GameState(narrative_depth="low")
        original = "A test event."
        result = narrator.enhance_event(original, state, "Alice")
        # Must return original (no AI call)
        assert result == original


class TestEnhanceOutcomeFallback:
    """Test outcome enhancement fallback."""

    def test_enhance_outcome_returns_original_when_ollama_down(self):
        """With Ollama unavailable, return original text unchanged."""
        state = GameState(narrative_depth="high")
        original = "The plan succeeds."
        result = narrator.enhance_outcome(original, success=True, state=state)
        assert result == original

    def test_enhance_outcome_respects_depth_gate(self):
        """At low depth, return original."""
        state = GameState(narrative_depth="low")
        original = "A test outcome."
        result = narrator.enhance_outcome(original, success=True, state=state)
        assert result == original


class TestEnhanceMilestoneFallback:
    """Test milestone enhancement fallback."""

    def test_enhance_milestone_returns_original_when_ollama_down(self):
        """With Ollama unavailable, return original text unchanged."""
        state = GameState(narrative_depth="high")
        original = "Fire was mastered."
        result = narrator.enhance_milestone("fire", original, tier=1, state=state)
        assert result == original

    def test_enhance_milestone_respects_depth_gate(self):
        """At low depth, return original."""
        state = GameState(narrative_depth="low")
        original = "A milestone description."
        result = narrator.enhance_milestone("test", original, tier=1, state=state)
        assert result == original
