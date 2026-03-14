# Kaboom Engine

![PyPI](https://img.shields.io/pypi/v/kaboom-engine)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

`kaboom-engine` is the deterministic rules engine for the Kaboom card game.

Current release line: `0.3.0`

It is intended to be reused by:

* CLIs
* simulations and AI agents
* multiplayer servers
* future graphical clients

## What The Engine Owns

The engine is the source of truth for:

* game setup and dealing
* mandatory opening peek setup
* legal action generation
* turn and reaction phase transitions
* card powers
* Kaboom endgame flow
* player memory mutation when cards move

Interfaces should choose and render actions, not reimplement rules.

## What's New In 0.3.0

`0.3.0` is the first fully rule-shaped engine release.

Highlights:

* opening peek is now an explicit setup phase instead of an implicit side effect
* power use is discard-first and shares the same contested discard window as reactions
* pending power resolution is explicit through `ResolvePendingPower`
* reactions are single-card claims, and the initiator may compete for the same discard event
* wrong reaction guesses now reveal information, apply penalty, and keep the window open
* Kaboom final-round discard windows fully resolve before the game ends
* result metadata is richer for CLI, simulation, and future multiplayer/server layers

## Install

```bash
pip install kaboom-engine
```

Local editable install:

```bash
git clone https://github.com/Arnav-Ajay/kaboom-core.git
cd kaboom-core
pip install -e .
```

## Minimal Usage

```python
from kaboom import GameEngine, get_valid_actions, apply_action

engine = GameEngine(game_id=0, num_players=2, hand_size=4)
state = engine.state

while not engine.is_game_over():
    actions = get_valid_actions(state)
    action = actions[0]
    apply_action(state, action)
```

Note:

* a fresh game starts in the opening peek setup phase
* `get_valid_actions(state)` already exposes the required `OpeningPeek` actions before round 1 begins

## Docs

Reference docs live in [`docs/`](./docs):

* [`GAME_RULES.md`](./docs/GAME_RULES.md)
* [`ENGINE_FLOW.md`](./docs/ENGINE_FLOW.md)
* [`GAME_ENGINE_API.md`](./docs/GAME_ENGINE_API.md)

These documents describe:

* state and phase flow
* action dispatch
* memory invariants
* `GameEngine` methods
* parameters and return types
* ownership boundaries between engine and UI

## Examples

Two maintained examples live in [`examples/`](./examples):

* [`game_info_demo.py`](./examples/game_info_demo.py) for inspecting setup, memory, and legal actions
* [`random_policy_simulation.py`](./examples/random_policy_simulation.py) for a simple simulation / AI / RL-style rollout loop

## Architecture

Core modules:

* [`kaboom/game`](./kaboom/game)
* [`kaboom/powers`](./kaboom/powers)
* [`kaboom/players`](./kaboom/players)
* [`kaboom/cards`](./kaboom/cards)

Main entrypoints:

* `GameEngine`
* `GameState`
* `apply_action(state, action)`
* `get_valid_actions(state)`

## Testing

Run the test suite with:

```bash
pytest
```

Important test coverage areas:

* setup and dealing
* powers
* reactions
* turn flow
* Kaboom endgame
* memory updates after card movement

## License

MIT
