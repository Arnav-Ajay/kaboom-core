# kaboom/game/reaction.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from kaboom.exceptions import InvalidActionError
from kaboom.game.game_state import GameState

@dataclass(slots=True)
class ReactionResult:
    success: bool
    penalty_applied: bool = False
    instant_win_player: Optional[int] = None

def _close_reaction(state: GameState) -> None:
    state.reaction_open = False
    state.reaction_rank = None
    state.reaction_initiator = None

def _apply_penalty(state: GameState, actor_id: int) -> ReactionResult:
    if not state.deck:
        raise InvalidActionError("Deck empty during penalty.")

    penalty_card = state.deck.pop()
    state.resolve_player(actor_id).hand.append(penalty_card)

    _close_reaction(state)
    return ReactionResult(success=False, penalty_applied=True)

def _check_instant_win(state: GameState, actor_id: int) -> ReactionResult:
    if not state.resolve_player(actor_id).hand:
        state.instant_winner = actor_id
        return ReactionResult(success=True, instant_win_player=actor_id)

    return ReactionResult(success=True)

def react_discard_own_card(
    state: GameState,
    actor_id: int,
    card_index: int,
) -> ReactionResult:
    if not state.reaction_open:
        raise InvalidActionError("No active reaction window.")

    player = state.resolve_player(actor_id)

    if card_index < 0 or card_index >= len(player.hand):
        raise InvalidActionError("Invalid card index.")

    card = player.hand[card_index]

    if card.rank.value != state.reaction_rank:
        return _apply_penalty(state, actor_id)

    # Valid match
    discarded = player.hand.pop(card_index)
    state.discard_pile.append(discarded)

    _close_reaction(state)
    return _check_instant_win(state, actor_id)

def react_discard_other_card(
    state: GameState,
    actor_id: int,
    target_player_id: int,
    target_card_index: int,
    give_card_index: int,
) -> ReactionResult:
    if not state.reaction_open:
        raise InvalidActionError("No active reaction window.")

    actor = state.resolve_player(actor_id)
    target = state.resolve_player(target_player_id)

    if not actor.hand:
        raise InvalidActionError("Actor must have a card to give.")

    target_card = target.hand[target_card_index]

    if target_card.rank.value != state.reaction_rank:
        return _apply_penalty(state, actor_id)

    # Discard target's card
    discarded = target.hand.pop(target_card_index)
    state.discard_pile.append(discarded)

    # Give actor's card (hidden)
    given = actor.hand.pop(give_card_index)
    target.hand.append(given)

    _close_reaction(state)
    return ReactionResult(success=True)

def react_discard_own_cards(
    state: GameState,
    actor_id: int,
    card_indices: List[int],
) -> ReactionResult:
    if not state.reaction_open:
        raise InvalidActionError("No active reaction window.")

    if not card_indices:
        raise InvalidActionError("Must discard at least one card.")

    player = state.resolve_player(actor_id)

    # Validate indices
    if any(i < 0 or i >= len(player.hand) for i in card_indices):
        raise InvalidActionError("Invalid card index.")

    # Validate all ranks BEFORE mutating
    for i in card_indices:
        if player.hand[i].rank.value != state.reaction_rank:
            return _apply_penalty(state, actor_id)

    # Discard highest indices first (stable pop)
    for i in sorted(card_indices, reverse=True):
        discarded = player.hand.pop(i)
        state.discard_pile.append(discarded)

    _close_reaction(state)
    return _check_instant_win(state, actor_id)

def react_discard_other_cards(
    state: GameState,
    actor_id: int,
    target_player_id: int,
    target_card_indices: List[int],
    give_card_indices: List[int],
) -> ReactionResult:
    if not state.reaction_open:
        raise InvalidActionError("No active reaction window.")

    if len(target_card_indices) != len(give_card_indices):
        raise InvalidActionError("Must give one card per stolen card.")

    actor = state.resolve_player(actor_id)
    target = state.resolve_player(target_player_id)

    if len(actor.hand) < len(give_card_indices):
        raise InvalidActionError("Not enough cards to give.")

    # Validate ranks first
    for i in target_card_indices:
        if target.hand[i].rank.value != state.reaction_rank:
            return _apply_penalty(state, actor_id)

    # Discard stolen cards
    for i in sorted(target_card_indices, reverse=True):
        discarded = target.hand.pop(i)
        state.discard_pile.append(discarded)

    # Give cards (hidden)
    for i in sorted(give_card_indices, reverse=True):
        given = actor.hand.pop(i)
        target.hand.append(given)

    _close_reaction(state)
    return ReactionResult(success=True)