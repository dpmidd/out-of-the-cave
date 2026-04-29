"""Local LLM narrative enhancement via Ollama."""

import json
import os
import urllib.error
import urllib.request
from typing import Optional

from src.models.game_state import GameState


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = os.getenv("CAVE_AI_MODEL", "llama3.2")
DEFAULT_TIMEOUT = 8

SYSTEM_PROMPT = (
    "You are narrating a philosophical survival game about cave-dwellers building civilization. "
    "Tone: grim, earned, sparse. Do not add new plot. Do not explain. "
    "Output only the rewritten text, no preamble."
)


def should_use_ai(state: GameState) -> bool:
    """Check if AI enhancement should be used based on narrative_depth setting."""
    return state.narrative_depth in ("high", "very_high")


def _build_context(state: GameState) -> str:
    """Build compact game state context for LLM prompts."""
    laws_str = ", ".join(state.civilization.laws[-3:]) if state.civilization.laws else "none yet"
    chaos_label = state.chaos_label
    stability_pct = int(state.civilization.stability * 100)
    alive_count = sum(1 for n in state.npcs if n.alive)

    return (
        f"Turn {state.turn}, Tier {state.current_tier}. "
        f"Stability: {stability_pct}%, Chaos: {chaos_label}. "
        f"Population: {state.civilization.population}, Leaders: {alive_count}. "
        f"Recent laws: {laws_str}."
    )


def _call_ollama(prompt: str, model: str = DEFAULT_MODEL, timeout: int = DEFAULT_TIMEOUT) -> Optional[str]:
    """Call Ollama API and return generated text, or None on any failure."""
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.7,
        }

        request = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("response", "").strip()
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError, OSError):
        return None


def enhance_event(event_text: str, state: GameState, npc_name: str) -> str:
    """Enhance event narrative with LLM, or return original on failure."""
    if not should_use_ai(state):
        return event_text

    context = _build_context(state)
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Game context: {context}\n\n"
        f"Original event text:\n{event_text}\n\n"
        f"Rewrite this in 2–3 vivid sentences. Reference {npc_name} if possible. "
        f"Keep the same tone and meaning. Output only the rewritten text."
    )

    result = _call_ollama(prompt)
    return result if result else event_text


def enhance_outcome(outcome_text: str, success: bool, state: GameState) -> str:
    """Enhance outcome narrative with LLM, or return original on failure."""
    if not should_use_ai(state):
        return outcome_text

    context = _build_context(state)
    outcome_frame = "SUCCESS" if success else "FAILURE"
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Game context: {context}\n\n"
        f"This is a {outcome_frame}. Original outcome text:\n{outcome_text}\n\n"
        f"Rewrite this in 2 sentences, reflecting the {outcome_frame.lower()}. "
        f"Keep the same meaning. Output only the rewritten text."
    )

    result = _call_ollama(prompt)
    return result if result else outcome_text


def enhance_milestone(name: str, description: str, tier: int, state: GameState) -> str:
    """Enhance milestone achieved moment with LLM, or return original on failure."""
    if not should_use_ai(state):
        return description

    context = _build_context(state)
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Game context: {context}\n\n"
        f"Milestone achieved: {name}\nOriginal description: {description}\n\n"
        f"Write one dramatic sentence marking this achievement in Tier {tier}. "
        f"Output only the sentence, no preamble."
    )

    result = _call_ollama(prompt)
    return result if result else description
