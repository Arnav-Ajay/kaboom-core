# kaboom/game/reaction.py
from __future__ import annotations
from ..exceptions import InvalidActionError
from .game_state import GameState
from .phases import GamePhase
from .results import ReactionResult

def close_reaction(state: GameState) -> None:
    if not state.reaction_open:
        raise InvalidActionError("No reaction to close")
    
    state.clear_pending_power()
    state.reaction_open = False
    state.reaction_rank = None
    state.reaction_initiator = None
    state.reaction_wrong_guess_counts = {}
    if state.pending_game_over_after_reaction:
        state.pending_game_over_after_reaction = False
        state.phase = GamePhase.GAME_OVER
    else:
        state.phase = GamePhase.TURN_DRAW

def _apply_penalty(
    state: GameState,
    actor_id: int,
    revealed_player_id: int,
    revealed_card_index: int,
    revealed_card,
) -> ReactionResult:
    if not state.deck:
        raise InvalidActionError("Deck empty during penalty.")

    state.remember_position_everywhere(
        revealed_player_id,
        revealed_card_index,
        revealed_card,
    )

    penalty_card = state.deck.pop()
    state.resolve_player(actor_id).hand.append(penalty_card)
    wrong_guess_count = state.record_wrong_reaction_attempt(actor_id)
    return ReactionResult(
        success=False,
        revealed_card=revealed_card,
        penalty_card=penalty_card,
        wrong_guess_count=wrong_guess_count,
        wrong_guess_limit_reached=not state.can_attempt_reaction(actor_id),
        reaction_continues=True,
        target_player_id=revealed_player_id,
        target_card_index=revealed_card_index,
        penalty_applied=True,
    )

def _check_instant_win(state: GameState, actor_id: int) -> ReactionResult:
    if not state.resolve_player(actor_id).hand:
        state.instant_winner = actor_id
        state.phase = GamePhase.GAME_OVER
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
    if not player.active:
        raise InvalidActionError("Inactive player cannot react.")
    if not state.can_attempt_reaction(actor_id):
        raise InvalidActionError("Reaction attempt limit reached for this discard event.")

    if card_index < 0 or card_index >= len(player.hand):
        raise InvalidActionError("Invalid card index.")

    card = player.hand[card_index]

    if card.rank.value != state.reaction_rank:
        return _apply_penalty(state, actor_id, actor_id, card_index, card)

    # Valid match
    discarded = player.hand.pop(card_index)
    state.discard_pile.append(discarded)
    state.shift_memories_after_removal(actor_id, card_index)

    cancelled_pending_power = state.pending_power_action is not None
    close_reaction(state)
    result = _check_instant_win(state, actor_id)
    result.cancelled_pending_power = cancelled_pending_power
    return result

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
    if not actor.active:
        raise InvalidActionError("Inactive player cannot react.")
    if not target.active:
        raise InvalidActionError("Cannot target an inactive player's locked cards.")
    if not state.can_attempt_reaction(actor_id):
        raise InvalidActionError("Reaction attempt limit reached for this discard event.")

    if not actor.hand:
        raise InvalidActionError("Actor must have a card to give.")
    if target_card_index < 0 or target_card_index >= len(target.hand):
        raise InvalidActionError("Invalid target card index.")
    if give_card_index < 0 or give_card_index >= len(actor.hand):
        raise InvalidActionError("Invalid give card index.")

    target_card = target.hand[target_card_index]

    if target_card.rank.value != state.reaction_rank:
        return _apply_penalty(
            state,
            actor_id,
            target_player_id,
            target_card_index,
            target_card,
        )

    # Discard target's card
    discarded = target.hand.pop(target_card_index)
    state.discard_pile.append(discarded)
    state.shift_memories_after_removal(target_player_id, target_card_index)

    # Give actor's card (hidden)
    given = actor.hand.pop(give_card_index)
    state.shift_memories_after_removal(actor_id, give_card_index)
    target.hand.append(given)
    actor.remember(target_player_id, len(target.hand) - 1, given)

    cancelled_pending_power = state.pending_power_action is not None
    close_reaction(state)
    return ReactionResult(success=True, cancelled_pending_power=cancelled_pending_power)
