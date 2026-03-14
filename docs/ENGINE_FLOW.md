# Engine Flow

## Purpose

This document describes the runtime flow of `kaboom-engine`, the ownership of each subsystem, and the state transitions that a client, simulator, or debugging CLI should expect.

The engine is the source of truth for:

* dealing and initial setup
* mandatory opening peek setup
* legal action generation
* turn and phase transitions
* power execution
* reaction resolution
* Kaboom endgame handling
* player memory mutation when cards move

Clients should render state and choose actions. They should not reimplement rules.

## High-Level Model

The engine operates on a mutable [`GameState`](../kaboom/game/game_state.py).

Normal integration loop:

1. Create `GameEngine(...)`.
2. Read `engine.state`.
3. Ask `get_valid_actions(state)` for legal moves.
4. Select one action.
5. Call `apply_action(state, action)` or a `GameEngine` wrapper.
6. Render the updated state and repeat.

## Setup Flow

Game creation is handled by `GameState.new_game(...)`, called from `GameEngine.__post_init__`.

Setup sequence:

1. Build a full 52-card deck.
2. Shuffle deck.
3. Create players `P1..Pn`.
4. Deal `hand_size` cards to each player.
5. Enter `GamePhase.OPENING_PEEK`.
6. Each player chooses exactly two of their own hand positions once.
7. After the last opening peek, start round 1 in `GamePhase.TURN_DRAW`.

Implementation points:

* [`GameEngine.__post_init__`](../kaboom/game/engine.py)
* [`GameState.new_game`](../kaboom/game/game_state.py)
* [`GameState.apply_opening_peek`](../kaboom/game/game_state.py)
* [`GameState.advance_opening_peek`](../kaboom/game/game_state.py)

## Phase Model

The engine has five phases defined in [`GamePhase`](../kaboom/game/phases.py):

* `OPENING_PEEK`
* `TURN_DRAW`
* `TURN_RESOLVE`
* `REACTION`
* `GAME_OVER`

Expected flow:

1. `OPENING_PEEK`
2. `TURN_DRAW`
3. `TURN_RESOLVE`
4. `REACTION` if discard/replace opened one
5. back to `TURN_DRAW` for the next player

Power use is a two-step exception:

1. `UsePower` discards the drawn power card and opens a contested discard event.
2. `ResolvePendingPower` resolves the stored power if no reaction consumed that event first.

## Action Flow

All state mutations go through action objects from [`actions.py`](../kaboom/game/actions.py).

Normal turn actions:

* `OpeningPeek`
* `Draw`
* `Discard`
* `Replace`
* `UsePower`
* `ResolvePendingPower`
* `CallKaboom`
* `CloseReaction`

Reaction actions:

* `ReactDiscardOwnCard`
* `ReactDiscardOtherCard`

Dispatch entrypoint:

* [`apply_action`](../kaboom/game/turn.py)

Validation entrypoints:

* [`validate_turn_owner`](../kaboom/game/validators.py)
* [`validate_turn`](../kaboom/game/validators.py)
* [`validate_use_power_payload`](../kaboom/game/validators.py)
* [`get_valid_actions`](../kaboom/game/validators.py)

## Legal Action Generation

`get_valid_actions(state)` is the authoritative legal action space for the current state.

Rules:

* In `OPENING_PEEK`, legal actions are `OpeningPeek` combinations for the current player's own hand.
* In `TURN_DRAW`, legal actions are `Draw` and optionally `CallKaboom`.
* In `TURN_RESOLVE`, legal actions are `Discard`, one `Replace` per hand index, and possibly `UsePower`.
* In `REACTION`, legal actions are reaction attempts, possibly `ResolvePendingPower`, and sometimes `CloseReaction`.
* In `GAME_OVER`, no actions are legal.

Important constraint:

* `UsePower` is only exposed for cards that are truly eligible. In particular, `see_and_swap` is available only for black kings, not all kings.

## Memory Model

Player memory lives on [`Player.memory`](../kaboom/players/player.py) and maps `(player_id, card_index)` to a remembered `Card`.

The engine updates memory in three classes of situations:

1. Observation
* opening peek on two chosen self-card positions
* `SeeSelfPower`
* `SeeOtherPower`
* `SeeAndSwapPower`

2. Positional movement
* `BlindSwapPower`
* `SeeAndSwapPower`

3. Hand mutation
* `Replace`
* reaction discards from own hand
* reaction steals/discards from another hand

Shared state helpers now live in [`GameState`](../kaboom/game/game_state.py):

* `apply_opening_peek(...)`
* `forget_position_everywhere(...)`
* `shift_memories_after_removal(...)`
* `shift_memories_after_swap(...)`
* `remember_replaced_card(...)`

Design rule:

* if a card changes owner or index, memory updates belong in core, not the UI

## Power Flow

Power types are defined in [`PowerType`](../kaboom/powers/types.py) and mapped in [`registry.py`](../kaboom/powers/registry.py).

Execution sequence for `UsePower`:

1. Validate payload shape in `validate_use_power_payload`.
2. Resolve the power implementation from `POWER_REGISTRY`.
3. Verify the power can apply to the concrete drawn card.
4. Discard the source card immediately.
5. Store the action in `state.pending_power_action`.
6. Open the reaction window for that discarded rank.
7. Advance turn into the contested discard window.

If the acting player wins priority, `ResolvePendingPower` then:

1. loads `state.pending_power_action`
2. applies the stored power
3. closes the reaction window
4. clears `pending_power_action`
5. returns to `TURN_DRAW`

## Reaction Flow

Discarding, replacing, or discarding for power opens a reaction window:

* `state.reaction_rank` is set to the discarded/replaced card rank
* `state.reaction_initiator` records the initiating player
* `state.reaction_open = True`
* phase becomes `REACTION`
* turn advances to the next player for reaction handling

If the discard came from `UsePower`, the state also stores:

* `state.pending_power_action`

Resolution options:

* resolve the pending power before any reaction wins priority
* discard one matching own card
* discard one matching other-player card and give one replacement card
* close reaction with no claim
* wrong guesses reveal the attempted card to all players, add one penalty card, and keep the window open

Reaction implementation:

* [`reaction.py`](../kaboom/game/reaction.py)
* [`turn.py`](../kaboom/game/turn.py)

## Kaboom Flow

Kaboom behavior:

1. A player may call Kaboom only after round 1.
2. The caller becomes inactive and revealed.
3. Other active players get one final turn each.
4. If the last final-round action opens a discard window, that window resolves first.
5. When the turn would return to the caller and no reaction window remains, the game ends.

Implementation points:

* [`_call_kaboom`](../kaboom/game/turn.py)
* [`GameState.advance_turn`](../kaboom/game/game_state.py)

## Return Types

Turn actions return `list[ActionResult]`.

Reaction actions return `ReactionResult`, wrapped as a single-item list by `apply_action(...)`.

Type definitions:

* [`ActionResult`](../kaboom/game/results.py)
* [`ReactionResult`](../kaboom/game/results.py)
* [`GameResult`](../kaboom/game/results.py)

Practical note:

* low-level callers using `apply_action(...)` should treat the result as `list[GameResult]`
* `GameEngine` convenience methods expose more specific return types per method

## Ownership Boundaries

Belongs in core:

* legality
* phase transitions
* memory invariants
* card movement semantics
* scoring and winner logic

Belongs in interfaces:

* how hidden information is rendered
* when to show derived score information to a human
* prompt/command structure
* logging/replay formatting
