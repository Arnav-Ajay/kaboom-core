# GameEngine API

## Scope

This document covers the public convenience surface exposed by [`GameEngine`](../kaboom/game/engine.py), plus the lower-level functions most clients will use directly.

`GameEngine` is a thin wrapper over `GameState` and `apply_action(...)`. It exists to make common operations convenient without hiding the underlying state machine.

## Core Objects

### `GameEngine`

Location:

* [`kaboom/game/engine.py`](../kaboom/game/engine.py)

Constructor:

```python
GameEngine(
    game_id: int,
    num_players: int = 4,
    hand_size: int = 4,
)
```

Behavior:

* validates player and hand limits
* creates a fresh `GameState` in `OPENING_PEEK`
* does not auto-fill opening memory

Primary attribute:

* `state: GameState`

### `GameState`

Location:

* [`kaboom/game/game_state.py`](../kaboom/game/game_state.py)

Important fields:

* `players`
* `deck`
* `discard_pile`
* `phase`
* `current_player_index`
* `round_number`
* `opening_peek_complete`
* `opening_peek_pending_player_ids`
* `drawn_card`
* `pending_power_action`
* `reaction_rank`
* `reaction_initiator`
* `reaction_open`
* `reaction_wrong_guess_counts`
* `kaboom_called_by`
* `instant_winner`
* `pending_game_over_after_reaction`

## GameEngine Methods

### `perform_opening_peek(player_id, card_indices) -> list[ActionResult]`

Calls:

* `apply_action(state, OpeningPeek(...))`

Requirements:

* phase must be `OPENING_PEEK`
* it must be the listed player's setup turn
* `card_indices` must contain exactly two distinct valid hand indices, or all available indices if the hand has fewer than two cards

Effects:

* records those chosen cards in the player's own memory
* advances setup to the next player's opening peek
* after the last player, starts round 1 in `TURN_DRAW`

### `draw_card(player_id) -> list[ActionResult]`

Calls:

* `apply_action(state, Draw(...))`

Requirements:

* it must be the player's turn
* phase must be `TURN_DRAW`

Effects:

* removes one card from the deck
* stores it in `state.drawn_card`
* changes phase to `TURN_RESOLVE`

### `replace_card(player_id, card_idx) -> list[ActionResult]`

Calls:

* `apply_action(state, Replace(...))`

Requirements:

* it must be the player's turn
* phase must be `TURN_RESOLVE`
* `card_idx` must be a valid hand index

Effects:

* swaps the drawn card into hand
* discards the replaced card
* updates memory so the actor knows the new card at that position
* clears stale knowledge of that position for other players
* opens a reaction window
* advances turn to the next player for reaction handling

### `discard_card(player_id) -> list[ActionResult]`

Calls:

* `apply_action(state, Discard(...))`

Requirements:

* it must be the player's turn
* phase must be `TURN_RESOLVE`

Effects:

* discards the drawn card
* opens a reaction window
* advances turn to the next player for reaction handling

### `call_kaboom(player_id) -> list[ActionResult]`

Calls:

* `apply_action(state, CallKaboom(...))`

Requirements:

* it must be the player's turn
* phase must be `TURN_DRAW`
* round number must be greater than 1

Effects:

* marks the caller as inactive and revealed
* records `kaboom_called_by`
* game ends once turn rotation returns to the caller and any final discard window has fully resolved

### `use_power(...) -> list[ActionResult]`

Signature:

```python
use_power(
    power_name: PowerType,
    player: Player | int,
    target_player_id: int | None,
    target_card_index: int | None,
    second_target_player_id: int | None = None,
    second_target_card_index: int | None = None,
)
```

Requirements:

* it must be the player's turn
* phase must be `TURN_RESOLVE`
* `state.drawn_card` must match the power being used
* payload must match the selected `PowerType`

Power payload rules:

* `SEE_SELF`: `target_card_index`
* `SEE_OTHER`: `target_player_id`, `target_card_index`
* `BLIND_SWAP`: all four target fields; first card must be the actor's own card and second card must belong to another player
* `SEE_AND_SWAP`: all four target fields; first card must be the actor's own card and second card must belong to another player

Notes:

* `player` may be passed as a `Player` instance or a raw player id
* only concrete legal power cards are exposed by `get_valid_actions`

Effects:

* discards the source card first
* stores the chosen power as `state.pending_power_action`
* opens a contested discard reaction window for that rank
* advances into `REACTION`

Important:

* `use_power(...)` no longer means "power already resolved"
* it means "the player claimed the power side of this discard event"

### `resolve_pending_power(actor_id) -> list[ActionResult]`

Calls:

* `apply_action(state, ResolvePendingPower(...))`

Requirements:

* a pending power must exist
* `actor_id` must match the player who discarded for power

Effects:

* applies the stored power
* closes the associated reaction window
* clears `pending_power_action`
* leaves the game at the next player's `TURN_DRAW`, or `GAME_OVER` if this was the deferred final Kaboom discard window

### `close_reaction() -> list[ActionResult]`

Calls:

* `apply_action(state, CloseReaction(...))`

Requirements:

* reaction window must be open

Effects:

* clears reaction metadata
* returns phase to `TURN_DRAW`, or `GAME_OVER` if this was the deferred final Kaboom discard window

### `react_discard_own_card(actor_id, card_index) -> ReactionResult`

Effects:

* if correct: discards that card and closes reaction
* if wrong: reveals the attempted card to all players, leaves it in place, adds one facedown penalty card to the actor's hand, and keeps the reaction window open
* each player may make only one wrong reaction attempt per discard window
* if actor goes to zero cards: instant win

### `react_discard_other_card(actor_id, target_player_id, target_card_index, give_card_index) -> ReactionResult`

Effects:

* if correct: discards target card, gives one actor card to target, closes reaction
* if wrong: reveals the attempted card to all players, leaves it in place, adds one facedown penalty card to the actor's hand, and keeps the reaction window open
* each player may make only one wrong reaction attempt per discard window

### `reactable_players(exclude_initiator=False) -> list[Player]`

Returns the currently eligible reacting players.

### `reaction_order() -> list[Player]`

Returns reaction processing order, rotated from just after the initiator.

### `is_game_over() -> bool`

Returns whether the state phase is `GAME_OVER`.

### `get_scores() -> dict[int, int]`

Returns current total score for every player id.

### `get_winner() -> int | list[int] | None`

Behavior:

* `None` if the game is not over
* one player id for a unique winner
* list of player ids on tie
* instant winner id when a player empties their hand during reaction

### `see_cards_at_start(peek_map) -> list[ActionResult]`

Convenience helper for simulations that applies the one-time opening peek across all players.

Requirements:

* `peek_map` must provide explicit chosen indices for each player
* the helper may only be used before opening peek is complete

### `save_to_memory(player, player_id, card_idx, card) -> None`

Manual helper for AI or simulation code to record knowledge.

This is not a game-rule action. It is a utility for external reasoning systems.

## Lower-Level API

### `apply_action(state, action) -> list[GameResult]`

Location:

* [`kaboom/game/turn.py`](../kaboom/game/turn.py)

Use this when you want full control over action objects and do not need the wrapper methods.

### `get_valid_actions(state) -> list[Action]`

Location:

* [`kaboom/game/validators.py`](../kaboom/game/validators.py)

This is the authoritative legal action generator for:

* simulations
* CLI move menus
* bots
* RL environments

## Action Definitions

Location:

* [`kaboom/game/actions.py`](../kaboom/game/actions.py)

Important action payloads:

* `Replace(target_index=...)`
* `UsePower(...)`
* `ResolvePendingPower(actor_id=...)`
* `ReactDiscardOwnCard(card_index=...)`
* `ReactDiscardOtherCard(target_player_id=..., target_card_index=..., give_card_index=...)`

## Result Definitions

Location:

* [`kaboom/game/results.py`](../kaboom/game/results.py)

### `ActionResult`

Fields:

* `action`
* `actor_id`
* `card`
* `peeked_indices`
* `power_name`
* `target_player_id`
* `target_card_index`
* `second_target_player_id`
* `second_target_card_index`
* `discarded_rank`
* `phase_before`
* `phase_after`
* `next_player_id`
* `reaction_opened`
* `reaction_closed`
* `pending_power_created`
* `pending_power_resolved`
* `pending_power_cancelled`
* `instant_winner`

### `ReactionResult`

Fields:

* `success`
* `actor_id`
* `reaction_type`
* `revealed_card`
* `penalty_card`
* `wrong_guess_count`
* `wrong_guess_limit_reached`
* `reaction_continues`
* `target_player_id`
* `target_card_index`
* `discarded_rank`
* `phase_before`
* `phase_after`
* `next_player_id`
* `penalty_applied`
* `instant_win_player`
* `cancelled_pending_power`

## Top-Level Exports

Top-level package exports are defined in [`kaboom/__init__.py`](../kaboom/__init__.py).

Notable exports include:

* `GameEngine`
* `GameState`
* `GamePhase`
* `apply_action`
* `get_valid_actions`
* all normal action dataclasses
* all reaction action dataclasses
* `ActionResult`
* `ReactionResult`
* `PowerType`

## Recommended Usage Patterns

For a manual client:

1. Use `GameEngine`.
2. Render `engine.state`.
3. Use `get_valid_actions(state)` to populate the menu.
4. Convert user input into one selected legal action.
5. Call `apply_action(...)`.

For a simulator or RL environment:

1. Use `GameEngine` or `GameState` directly.
2. Treat `get_valid_actions(state)` as the legal action space.
3. Avoid reimplementing rule checks externally.
