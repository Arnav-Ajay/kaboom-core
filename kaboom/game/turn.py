from __future__ import annotations

from kaboom.cards.card import Card
from kaboom.exceptions import InvalidActionError
from kaboom.game.actions import (
    Action,
    Draw,
    Discard,
    Replace,
    UsePower,
    CallKaboom,
)
from kaboom.game.game_state import GameState

def _validate_turn_owner(state: GameState, actor_id: int) -> None:
    current = state.current_player()
    if current.id != actor_id:
        raise InvalidActionError("Not this player's turn.")
    if not current.active:
        raise InvalidActionError("Inactive player cannot act.")


def _draw(state: GameState, action: Draw) -> None:
    if state.drawn_card is not None:
        raise InvalidActionError("Already holding a drawn card.")

    if not state.deck:
        raise InvalidActionError("Deck is empty.")

    state.drawn_card = state.deck.pop()

def _replace(state: GameState, action: Replace) -> None:
    if state.drawn_card is None:
        raise InvalidActionError("No drawn card to replace with.")

    player = state.current_player()

    if action.target_index < 0 or action.target_index >= len(player.hand):
        raise InvalidActionError("Invalid hand index.")

    replaced = player.hand[action.target_index]
    state.discard_pile.append(replaced)

    player.hand[action.target_index] = state.drawn_card
    state.drawn_card = None

    # Open reaction window
    state.reaction_rank = replaced.rank.value
    state.reaction_initiator = player.id
    state.reaction_open = True

    state.advance_turn()

def _discard(state: GameState, action: Discard) -> None:
    if state.drawn_card is None:
        raise InvalidActionError("No drawn card to discard.")

    discarded = state.drawn_card
    state.discard_pile.append(discarded)
    state.drawn_card = None

    state.reaction_rank = discarded.rank.value
    state.reaction_initiator = action.actor_id
    state.reaction_open = True

    state.advance_turn()
def _use_power(state: GameState, action: UsePower) -> None:
    if state.drawn_card != action.source_card:
        raise InvalidActionError("Power card must be the drawn card.")

    # Power resolution will:
    # - consume the card
    # - mutate hands / memory
    # - decide if a swap happens
    # Implemented in kaboom/powers/*
    raise NotImplementedError("Power resolution not wired yet.")

def _call_kaboom(state: GameState, action: CallKaboom) -> None:
    if state.round_number <= 1:
        raise InvalidActionError("Kaboom cannot be called in round 1.")

    player = state.current_player()

    state.kaboom_called_by = player.id
    player.active = False
    player.revealed = True


def apply_action(state: GameState, action: Action) -> None:
    """
    Apply a validated action to the game state.
    """
    _validate_turn_owner(state, action.actor_id)

    if isinstance(action, Draw):
        _draw(state, action)

    elif isinstance(action, Replace):
        _replace(state, action)

    elif isinstance(action, Discard):
        _discard(state, action)

    elif isinstance(action, UsePower):
        _use_power(state, action)

    elif isinstance(action, CallKaboom):
        _call_kaboom(state, action)

    else:
        raise InvalidActionError(f"Unknown action type: {type(action)}")
