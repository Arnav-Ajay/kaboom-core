# Kaboom Engine

A deterministic Python engine for the **Kaboom card game**.

The project implements the full game logic including turns, reactions, powers, and endgame rules, designed to be used as a reusable **simulation engine, AI environment, or UI backend**.

---

# Features

* Complete Kaboom game rules
* Deterministic turn engine
* Reaction resolution system
* Card power mechanics
* Kaboom endgame logic
* Deck reshuffle handling
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

Clone the repository:

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
from kaboom import GameState, apply_action
from kaboom.game.actions import Draw, Discard

state = GameState.new_game()

apply_action(state, Draw(actor_id=0))
apply_action(state, Discard(actor_id=0))
```

---

# Running Simulations

The engine supports automated play.

```python
import random
from kaboom import GameState, apply_action
from kaboom.game.turn import get_valid_actions

state = GameState.new_game()

while True:
    actions = get_valid_actions(state)

    if not actions:
        break

    action = random.choice(actions)
    apply_action(state, action)
```

This allows thousands of games to be simulated for testing or AI training.

---

# Architecture

The engine follows a modular architecture:

```
GameState
    |
Action (Draw / Discard / Replace / UsePower / CallKaboom)
    |
apply_action()
    |
ActionResult
```

Key components:

```
kaboom/cards      → card definitions
kaboom/players    → player state
kaboom/powers     → power system
kaboom/game       → turn engine, reactions, validators
```

This separation keeps game logic independent from any UI layer.

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
```

---

# Testing

The engine includes a full pytest test suite.

Run tests:

```bash
pytest
```

Current coverage includes:

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

---