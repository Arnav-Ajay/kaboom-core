# Kaboom Engine
![PyPI](https://img.shields.io/pypi/v/kaboom-engine) 
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

The project implements the full game logic including turns, reactions, powers, and endgame rules, designed to be used as a reusable **simulation engine, AI environment, or UI backend**.

---

# Features

* Complete Kaboom game rules
* Deterministic turn engine
* Reaction resolution system
* Card power mechanics
* Kaboom endgame logic
* Deck reshuffle handling
* Fully enumerated action space
* Action-based engine architecture
* Event-based results
* Fully tested core logic

The engine is designed so it can be used for:

* CLI or graphical game clients
* AI agents
* game simulations
* multiplayer servers
* reinforcement learning environments

---

# Installation

```bash
pip install kaboom-engine
````

OR clone the repository:

```bash
git clone https://github.com/Arnav-Ajay/kaboom-core.git
cd kaboom-core
```

Install locally:

```bash
pip install -e .
```

---

# Basic Usage

```python
from kaboom.game.engine import GameEngine

engine = GameEngine(game_id=0, num_players=4, hand_size=4)
state = engine.state

players = state.players
current_player = state.current_player()

# draw a card
engine.draw_card(current_player.id)

# discard
engine.discard_card(current_player.id)
```

---

# Running Simulations

The engine exposes the **complete legal action space** of the current game state.

```python
import random

from kaboom.game.engine import GameEngine
from kaboom.game.turn import apply_action
from kaboom.game.validators import get_valid_actions

engine = GameEngine(game_id=0, num_players=2, hand_size=4)
state = engine.state

while state.phase != GamePhase.GAME_OVER:

    player = state.current_player()

    # skip inactive players (kaboom caller)
    if not player.active:
        state.advance_turn()
        continue

    actions = get_valid_actions(state)

    if not actions:
        break

    action = random.choice(actions)

    apply_action(state, action)
    
```

---

# Architecture

The engine follows a modular architecture based on **action execution**.

```
GameState
    |
Action
    | (Draw / Discard / Replace / UsePower / CallKaboom / Reaction Actions)
    |
apply_action()
    |
ActionResult
```

---

# Action System

All player interactions are represented as **Action objects**.

Core actions include:

```
Draw
Discard
Replace
UsePower
CallKaboom
CloseReaction
ReactDiscardOwnCard
ReactDiscardOwnCards
ReactDiscardOtherCard
ReactDiscardOtherCards
```

The function:

```
get_valid_actions(state)
```

returns the full list of legal actions for the current state.

---

# Project Structure

```
kaboom/
    cards/
    players/
    powers/
    game/
        actions.py
        game_state.py
        phases.py
        reaction.py
        results.py
        turn.py
        validators.py

tests/
examples/
```

Key modules:

```
kaboom/cards      → card definitions
kaboom/players    → player state and memory
kaboom/powers     → card power implementations
kaboom/game       → engine logic, actions, validation
```

---

# Testing

The engine includes a full pytest test suite.

Run tests:

```bash
pytest
```

Coverage includes:

* card scoring
* deck creation
* player management
* power mechanics
* turn actions
* reaction logic
* Kaboom endgame rules
* full game initialization

---

# Future Improvements

Planned enhancements:

* CLI interface
* graphical UI
* AI player agents
* multiplayer networking
* replay and event logging
* Gym-compatible environment for reinforcement learning

---

# License

This project is licensed under the MIT License.

---

# Author

[Arnav Ajay](https://github.com/Arnav-Ajay)