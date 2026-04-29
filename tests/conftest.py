"""Pytest configuration and fixtures."""

import pytest

from src.models.game_state import GameState
from src.models.npc import NPC
from src.models.player import Player


@pytest.fixture
def empty_state():
    """Fresh GameState with no NPCs."""
    return GameState()


@pytest.fixture
def state_with_npcs():
    """GameState with 5 NPCs."""
    state = GameState()
    state.npcs = [
        NPC(name="Alice", loyalty=0.8, alive=True),
        NPC(name="Bob", loyalty=0.5, alive=True),
        NPC(name="Carol", loyalty=0.3, alive=True),
        NPC(name="Dave", loyalty=0.9, alive=True),
        NPC(name="Eve", loyalty=0.4, alive=True),
    ]
    return state


@pytest.fixture
def player_high_courage():
    """Player with high courage attribute."""
    p = Player()
    p.courage = 9
    return p


@pytest.fixture
def player_low_wisdom():
    """Player with low wisdom attribute."""
    p = Player()
    p.wisdom = 1
    return p
