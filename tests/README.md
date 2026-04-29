# Out of the Cave — Test Suite

Comprehensive test coverage for core game systems and the new Ollama narrator integration.

## Test Organization

- **test_narrator.py** — Ollama narrative enhancement module (depth gating, fallback behavior)
- **test_game_state.py** — GameState mechanics (chaos, stability decay, victory/defeat conditions)
- **test_dice.py** — Roll system and skill checks
- **test_milestones.py** — Milestone achievement and conditions
- **test_events.py** — Event selection and choice resolution
- **test_delegation.py** — NPC delegation tasks and outcomes
- **conftest.py** — Pytest fixtures (state, NPCs, player attributes)

## Running Tests

### Install dependencies
```bash
pip install pytest pytest-cov
```

### Run all tests
```bash
pytest tests/
```

### Run with verbose output
```bash
pytest tests/ -v
```

### Run with coverage report
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

This shows which lines are not covered by tests.

### Run specific test file
```bash
pytest tests/test_narrator.py -v
```

### Run specific test class
```bash
pytest tests/test_game_state.py::TestChaosLabel -v
```

### Run specific test
```bash
pytest tests/test_narrator.py::TestShouldUseAI::test_ai_enabled_at_high_depth -v
```

## Test Coverage Goals

- **Narrator (100%)**: All code paths including Ollama integration and fallback
- **Game State (95%)**: Chaos/stability mechanics, victory/defeat, milestone tracking
- **Dice System (100%)**: Roll logic with attribute and chaos influence
- **Milestones (90%)**: Condition checking, tier gating, rewards
- **Events (85%)**: Selection, choice resolution, effect application
- **Delegation (80%)**: Task assignment, outcome processing

## Continuous Integration

To add pre-commit hook:
```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
pytest tests/ -q
if [ $? -ne 0 ]; then
  echo "Tests failed. Commit aborted."
  exit 1
fi
EOF
chmod +x .git/hooks/pre-commit
```

## Integration Testing with Ollama

To test narrator with a live Ollama instance:

```bash
# Terminal 1: Start Ollama
ollama run llama3.2

# Terminal 2: Run integration tests
OLLAMA_TEST=1 pytest tests/test_narrator.py -v
```

(Requires OLLAMA_TEST env var implementation in conftest.py)

## Known Limitations

- Event selection tests don't validate all tier/condition combinations (event YAML is dynamic)
- Delegation tests assume outcomes are deterministic (actual rolls are stochastic)
- No tests for UI rendering (renderer.py is display-only)
- No tests for save/load serialization (would require file I/O)
