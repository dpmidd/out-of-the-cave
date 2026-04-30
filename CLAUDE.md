# CLAUDE.md — Out of the Cave Development Guide

## Project Overview

**Out of the Cave** is a philosophical text adventure game inspired by Plato's allegory. Players guide a civilization from darkness through emergence, building society through narrative choices that affect game state.

- **Genre:** Text adventure / philosophical simulation
- **Scope:** Single-player, turn-based, narrative-driven
- **Tech Stack:** Python 3.12, Pydantic, YAML, Pytest
- **Solo Dev:** Learning project, emphasis on clean architecture and testability

## Architecture at a Glance

### Core Systems

| System | Files | Purpose |
|--------|-------|---------|
| **Game State** | `src/models/game_state.py` | Central state object (Pydantic BaseModel), 100% serializable |
| **Events** | `src/systems/events.py` | YAML-driven event system, auto-loads from `data/events/`, filters by conditions |
| **Milestones** | `src/systems/milestones.py` | 18 achievement-based milestones across 5 tiers, unlock progression |
| **Dice/Rolls** | `src/systems/dice.py` | d10 + attribute vs difficulty, chaos-influenced |
| **Narrator** | `src/ai/narrator.py` | Optional Ollama LLM integration for prose enhancement (high/very_high narrative_depth) |
| **NPCs** | `src/models/npc.py` | Alive/dead, roles, loyalty, names from `data/npcs.yaml` |
| **Player** | `src/models/player.py` | 5 attributes (rhetoric, wisdom, courage, authority, pragmatism) |
| **Civilization** | `src/models/civilization.py` | Population, stability, food, shelter, knowledge, laws, starvation |

### Data-Driven Design

- **Events:** `data/events/tier_X_*.yaml` (51 events across 5 tiers)
- **Milestones:** Hard-coded in `src/systems/milestones.py` (18 total)
- **NPCs:** `data/npcs.yaml` (names used for {npc} substitution)
- **Saves:** User-created, GameState serialized as JSON

## File Structure

```
workspace/game/
├── src/
│   ├── models/
│   │   ├── game_state.py       # Central state (Pydantic)
│   │   ├── civilization.py     # Population, stability, resources
│   │   ├── milestone.py        # Milestone definitions and check logic
│   │   ├── npc.py             # NPC definition (name, alive, role, loyalty)
│   │   └── player.py          # Player attributes (rhetoric, etc.)
│   ├── systems/
│   │   ├── events.py          # Event loading, filtering, resolution
│   │   ├── dice.py            # d10 roll system
│   │   └── milestones.py      # Milestone triggering
│   ├── ai/
│   │   └── narrator.py        # Ollama LLM integration (optional)
│   └── main.py                # Entry point (WIP)
├── data/
│   ├── events/
│   │   ├── tier_1_emergence.yaml
│   │   ├── tier_2_organization.yaml (10 events)
│   │   ├── tier_3_society.yaml     (14 events)
│   │   ├── tier_4_republic.yaml    (13 events)
│   │   └── tier_5_legacy.yaml      (9 events)
│   └── npcs.yaml              # NPC names for {npc} substitution
├── tests/
│   ├── test_game_state.py     # State mutations, chaos, stability decay
│   ├── test_milestones.py     # Milestone triggering logic
│   ├── test_narrator.py       # LLM fallback behavior
│   └── conftest.py
└── pytest.ini
```

## YAML Event Schema (Quick Reference)

Every event must follow this structure:

```yaml
- id: unique_event_id
  conditions:
    tier: 1-5                              # Required
    turn_min: <int>                        # Always set; prevents early fire
    turn_max: <int>                        # Optional, default 999
    required_milestones: [id1, id2, ...]   # Optional; event gated behind milestones
    blocked_by_milestones: [id1, ...]      # Optional; one-shot (can't re-trigger if these achieved)
    chaos_min: <float>                     # Optional; chaos-triggered events
    chaos_max: <float>                     # Optional
    min_population: <int>                  # Optional
  text: > Prose, 100-200 words, second-person, {npc} placeholder
  choices:
    - text: "Choice label (skill difficulty X)"
      skill_check: rhetoric|wisdom|courage|authority|pragmatism
      difficulty: 3-8
      chaos_delta: <float>                 # Optional, fires before roll
      outcomes:
        success:
          text: > Outcome prose, 30-60 words
          effects:
            chaos: <float>                 # Optional
            loyalty_all: <float>           # Optional
            food|shelter|knowledge|population|stability: <int/float>
            law: "Law text"                # Optional; appends to civ.laws
          history_flag: <string>           # Optional; appended to event_history
          assign_role: council_member|scout|enforcer|builder|healer|guardian
        failure:
          text: > Outcome prose
          effects: {...}
    - text: "Retreat — do nothing"
      special: retreat                     # Required as last choice in every event
```

**Key Rules:**
- Every event **must** have a retreat choice as the last option
- Choices without `skill_check` always succeed (passive options)
- `assign_role` assigns to highest-loyalty unassigned alive NPC
- `history_flag` gates future events — keep names descriptive
- `law` adds a string to `civilization.laws` (used for milestone checks)
- `chaos_delta` applies before the roll, shifts odds
- Tone: grim, sparse, philosophical. No sentimentality.

## Critical Game Mechanics

### State Flow

1. Event is selected via `events.select_event(state)` (filters by conditions, prefers current tier)
2. Player chooses an option
3. `events.resolve_choice(choice, state)` processes skill check, effects, flags
4. Effects applied to `state.civilization` and `state`
5. Milestones checked via `milestones.check_milestones(state)`
6. Turn increments, chaos/stability decay

### Skill Checks

```python
def roll(attribute: int, difficulty: int, chaos: float) -> bool:
    base_roll = random.randint(1, 10)
    chaos_swing = chaos * random.uniform(0, 3)
    final = base_roll + attribute + chaos_swing
    target = difficulty + 5
    return final >= target
```

- Chaos > 0 increases success chance (luck)
- Chaos < 0 decreases it (bad luck)
- Chaos oscillates ±0.05 per turn

### Milestone Triggering

Milestones are checked each turn in `milestones.py`. Examples:
- `fire` → `state.civilization.shelter >= 1`
- `council` → `len([n for n in state.npcs if n.role]) >= 3`
- `three_laws` → `len(state.civilization.laws) >= 3`
- `constitution_written` → `"constitution_written" in state.event_history` (flag-based)
- Tier gating: Tier N milestones only unlock when Tier N-1 all achieved

### Victory/Defeat

- **Victory:** `state.is_victory` = `"philosopher_king" in achieved_milestone_ids`
- **Defeat:** `state.is_defeat` = `population <= 0` OR `chaos >= 1.0`

## Token Optimization for Future Work

### What to Read First (Per Task Type)

**Adding/modifying events:**
- Read only the specific event file(s) you're editing
- Skip reading `src/systems/events.py` unless you're changing filtering logic
- Reference the YAML schema above (don't read the full event loader)

**Bug fixes in game logic:**
- Read `src/systems/milestones.py` for milestone bugs
- Read `src/systems/dice.py` for roll mechanics
- Read `src/systems/events.py` for event resolution
- Skip model files unless the bug touches BaseModel validation

**UI/frontend work:**
- Read `src/main.py` (currently minimal; WIP for CLI)
- Skip data files and systems unless integrating with them

**Testing additions:**
- Read `tests/conftest.py` for fixtures
- Read relevant test file to understand existing pattern
- Skip reading implementation; trust the code

### What to Skip

- ❌ Don't read all 51 events when adding a single event — just read the YAML schema and one example
- ❌ Don't read `src/models/` unless modifying model structure
- ❌ Don't read full `src/systems/events.py` when adding events — use the schema in this file
- ❌ Don't read all milestones when checking a single one — grep for `def check_` and read that function
- ❌ Don't read tests unless you're modifying tests or debugging test failures

### Caching and Reuse

- Events are cached in `_event_cache` after first load — safe to call `load_all_events()` freely
- GameState is fully Pydantic-serializable — model_dump_json() and model_validate_json() work
- Milestones are static (hard-coded), not data-driven — changes require code edits

## Common Tasks

### Add a New Event

1. Read the YAML schema above
2. Pick an unused `id`, matching tier and theme
3. Write event in appropriate `data/events/tier_X_*.yaml`
4. Ensure `turn_min` is set and conditions are correct
5. Run: `python -c "from src.systems.events import load_all_events; load_all_events()"`
6. Test with: `pytest tests/test_*.py -v`

### Add a New Milestone

1. Read `src/systems/milestones.py`, find `MILESTONES` list
2. Add milestone definition (id, tier, condition function, rewards)
3. If flag-based, ensure the event producing the flag exists
4. Run tests: all 79 tests should pass

### Modify Game State

1. Read `src/models/game_state.py` 
2. Pydantic fields use Field() for defaults and constraints
3. Properties return computed values (current_tier, is_victory, etc.)
4. Changes to fields may require test updates
5. Always run `pytest -v` after changes

### Test a Feature

```bash
source venv/bin/activate
pytest tests/ -v                    # Run all tests
pytest tests/test_events.py -v      # Run specific suite
pytest tests/ -k milestone -v       # Run by pattern
```

All 79 tests should pass. No external services required (Ollama integration gracefully fails).

## Important Constraints

- **Pydantic models:** Use Field() for validation. All game state must be serializable.
- **YAML must be clean:** Test loads with `load_all_events()` before committing
- **No breaking changes to event conditions:** Events reference milestones by ID — renaming breaks saves
- **Tone consistency:** All prose should match existing events (grim, philosophical, second-person)
- **No sentimentality:** Avoid melodrama; earned emotion only
- **Tests are non-negotiable:** New features need tests; all existing tests must pass

## Development Workflow

1. **Read this file** to understand context
2. **Make local changes** (events, models, systems)
3. **Run tests:** `pytest tests/ -v` (should be fast, <1s)
4. **Commit:** Include what changed and why (not how)
5. **Push:** Creates PR automatically
6. **Verify:** All 79 tests pass in CI

## Quick Debugging

| Issue | Solution |
|-------|----------|
| Event won't load | Check YAML syntax; run `python -c "from src.systems.events import load_all_events; print(load_all_events())"` |
| Milestone not triggering | Check condition function and tier gating in `milestones.py` |
| Tests fail | Run full suite: `pytest -v`. Check conftest.py for fixtures. |
| NPC name not substituting | Check {npc} placeholder in event text and `data/npcs.yaml` has names |
| Chaos/stability wrong | Check decay logic in `game_state.py` (decay_chaos, decay_stability) |

## Future Work Notes

- **UI:** `src/main.py` is WIP. CLI will likely use `src/systems/events.py` and loop on `state.turn`
- **Saving:** GameState is serializable; save/load should be straightforward JSON
- **AI Narrator:** Optional enhancement at high/very_high narrative_depth. Fallback to original text if Ollama unavailable
- **Balancing:** Chaos/stability decay, event reward tuning — data-driven via effects dicts

---

**Last Updated:** 2026-04-29  
**Total Events:** 51 (Tiers 1-5)  
**Total Milestones:** 18  
**Test Coverage:** 79 tests, all passing
