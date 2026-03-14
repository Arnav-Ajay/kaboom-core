# kaboom/game/turn.py
from __future__ import annotations

from ..exceptions import InvalidActionError
from .actions import (
    Action,
    OpeningPeek,
    Draw,
    Discard,
    Replace,
    UsePower,
    CallKaboom,
    CloseReaction,
    ResolvePendingPower,
    ReactDiscardOwnCard,
    ReactDiscardOtherCard,
    
    )
from .reaction import (
    close_reaction,
    react_discard_own_card,
    react_discard_other_card,
    
    )
from .game_state import GameState
from .validators import validate_turn_owner, validate_index, validate_turn, validate_use_power_payload
from ..powers.registry import POWER_REGISTRY
from .results import ActionResult, ReactionResult
from .phases import GamePhase


def _current_phase_value(state: GameState) -> str:
    return state.phase.value


def _current_player_id_or_none(state: GameState) -> int | None:
    if state.phase == GamePhase.GAME_OVER:
        return None
    return state.current_player().id


def _finalize_reaction_result(
    result: ReactionResult,
    *,
    phase_before: str,
    state: GameState,
    actor_id: int,
    reaction_type: str,
    target_player_id: int | None = None,
    target_card_index: int | None = None,
) -> ReactionResult:
    result.actor_id = actor_id
    result.reaction_type = reaction_type
    result.target_player_id = target_player_id
    result.target_card_index = target_card_index
    result.discarded_rank = state.reaction_rank or result.discarded_rank
    result.phase_before = phase_before
    result.phase_after = _current_phase_value(state)
    result.next_player_id = _current_player_id_or_none(state)
    return result

def _draw(state: GameState, action: Draw) -> None:

    if state.drawn_card is not None:
        raise InvalidActionError("Already holding a drawn card.")

    state.ensure_deck()

    if not state.deck:
        raise InvalidActionError("Deck is empty.")

    state.drawn_card = state.deck.pop()
    state.phase = GamePhase.TURN_RESOLVE

def _opening_peek(state: GameState, action: OpeningPeek) -> None:
    state.apply_opening_peek(action.actor_id, action.card_indices)
    state.advance_opening_peek()

def _replace(state: GameState, action: Replace) -> None:
    if state.drawn_card is None:
        raise InvalidActionError("No drawn card to replace with.")

    player = state.current_player()

    validate_index(len(player.hand), action.target_index, "target_index")

    replaced = player.hand[action.target_index]
    state.discard_pile.append(replaced)

    player.hand[action.target_index] = state.drawn_card
    state.remember_replaced_card(player.id, player.id, action.target_index, state.drawn_card)
    state.drawn_card = None

    # Open reaction window (phase switches to REACTION)
    state.open_reaction(replaced.rank.value, player.id)

    state.advance_turn()

def _discard(state: GameState, action: Discard) -> None:
    if state.drawn_card is None:
        raise InvalidActionError("No drawn card to discard.")

    discarded = state.drawn_card
    state.discard_pile.append(discarded)
    state.drawn_card = None

    state.open_reaction(discarded.rank.value, action.actor_id)

    state.advance_turn()

def _use_power(state: GameState, action: UsePower) -> None:
    card = action.source_card

    if state.drawn_card is None:
        raise InvalidActionError("No drawn card to use power with.")

    if state.drawn_card != card:
        raise InvalidActionError("Power must use drawn card.")

    power = POWER_REGISTRY[action.power_name]
    if not power.can_apply(state, action.actor_id, card):
        raise InvalidActionError("Power cannot be applied for this card.")

    state.discard_pile.append(card)
    state.pending_power_action = action
    state.drawn_card = None
    state.open_reaction(card.rank.value, action.actor_id)
    state.advance_turn()

def _resolve_pending_power(state: GameState, action: ResolvePendingPower) -> None:
    pending = state.pending_power_action
    if pending is None:
        raise InvalidActionError("No pending power to resolve.")
    if pending.actor_id != action.actor_id:
        raise InvalidActionError("Only the initiating player can resolve pending power.")

    power = POWER_REGISTRY[pending.power_name]
    power.apply(state, pending)
    close_reaction(state)

def _call_kaboom(state: GameState, action: CallKaboom) -> None:
    if state.round_number <= 1:
        raise InvalidActionError("Kaboom cannot be called in round 1.")

    player = state.current_player()

    state.kaboom_called_by = player.id
    player.active = False
    player.revealed = True

def apply_action(state: GameState, action: Action) -> list[ActionResult]:
    """
    Apply a validated action to the game state.
    """
    phase_before = _current_phase_value(state)
    reaction_rank_before = state.reaction_rank
    if state.phase == GamePhase.GAME_OVER:
        raise InvalidActionError("Game is already over.")
    
    # ------------------------------------------------
    # Reaction resolution path (bypass turn rules)
    # ------------------------------------------------

    if isinstance(action, ReactDiscardOwnCard):
        result = react_discard_own_card(state, action.actor_id, action.card_index)
        return [
            _finalize_reaction_result(
                result,
                phase_before=phase_before,
                state=state,
                actor_id=action.actor_id,
                reaction_type="react_discard_own_card",
                target_player_id=action.actor_id,
                target_card_index=action.card_index,
            )
        ]

    elif isinstance(action, ReactDiscardOtherCard):
        result = react_discard_other_card(
            state,
            action.actor_id,
            action.target_player_id,
            action.target_card_index,
            action.give_card_index,
        )
        return [
            _finalize_reaction_result(
                result,
                phase_before=phase_before,
                state=state,
                actor_id=action.actor_id,
                reaction_type="react_discard_other_card",
                target_player_id=action.target_player_id,
                target_card_index=action.target_card_index,
            )
        ]

    elif isinstance(action, CloseReaction):
        pending_power_cancelled = state.pending_power_action is not None
        close_reaction(state)
        return [
            ActionResult(
                "close_reaction",
                action.actor_id,
                discarded_rank=reaction_rank_before,
                phase_before=phase_before,
                phase_after=_current_phase_value(state),
                next_player_id=_current_player_id_or_none(state),
                reaction_closed=True,
                pending_power_cancelled=pending_power_cancelled,
                instant_winner=state.instant_winner,
            )
        ]

    elif isinstance(action, ResolvePendingPower):
        pending = state.pending_power_action
        _resolve_pending_power(state, action)
        return [
            ActionResult(
                "use_power",
                action.actor_id,
                power_name=pending.power_name.value if pending is not None else None,
                target_player_id=pending.target_player_id if pending is not None else None,
                target_card_index=pending.target_card_index if pending is not None else None,
                second_target_player_id=pending.second_target_player_id if pending is not None else None,
                second_target_card_index=pending.second_target_card_index if pending is not None else None,
                discarded_rank=reaction_rank_before,
                phase_before=phase_before,
                phase_after=_current_phase_value(state),
                next_player_id=_current_player_id_or_none(state),
                reaction_closed=True,
                pending_power_resolved=True,
            )
        ]

    # ------------------------------------------------
    # Normal turn validation
    # ------------------------------------------------
    if state.reaction_open and not isinstance(
        action,
        (
            CloseReaction,
            ResolvePendingPower,
            ReactDiscardOwnCard,
            ReactDiscardOtherCard,
        ),
    ):
        raise InvalidActionError("Reaction window open.")

    validate_turn_owner(state, action.actor_id)
    validate_turn(state)
    if isinstance(action, UsePower):
        validate_use_power_payload(action)

    phase = state.phase

    if phase == GamePhase.REACTION and not isinstance(action, CloseReaction):
        if not isinstance(action, ResolvePendingPower):
            raise InvalidActionError("Must resolve reaction first.")

    if phase == GamePhase.OPENING_PEEK and not isinstance(action, OpeningPeek):
        raise InvalidActionError("Must complete the opening peek before play begins.")

    if phase == GamePhase.TURN_DRAW and not (isinstance(action, Draw) or isinstance(action, CallKaboom)):
        raise InvalidActionError("Must draw first.")

    if phase == GamePhase.TURN_RESOLVE and isinstance(action, Draw):
        raise InvalidActionError("Already drawn this turn.")

    # ------------------------------------------------
    # Turn actions
    # ------------------------------------------------
    
    if isinstance(action, OpeningPeek):
        _opening_peek(state, action)
        return [
            ActionResult(
                "opening_peek",
                action.actor_id,
                peeked_indices=action.card_indices,
                phase_before=phase_before,
                phase_after=_current_phase_value(state),
                next_player_id=_current_player_id_or_none(state),
            )
        ]

    elif isinstance(action, Draw):
        _draw(state, action)
        return [
            ActionResult(
                "draw",
                action.actor_id,
                card=state.drawn_card,
                phase_before=phase_before,
                phase_after=_current_phase_value(state),
                next_player_id=_current_player_id_or_none(state),
            )
        ]

    elif isinstance(action, Replace):
        _replace(state, action)
        return [
            ActionResult(
                "replace",
                action.actor_id,
                target_card_index=action.target_index,
                discarded_rank=reaction_rank_before or state.reaction_rank,
                phase_before=phase_before,
                phase_after=_current_phase_value(state),
                next_player_id=_current_player_id_or_none(state),
                reaction_opened=True,
            )
        ]

    elif isinstance(action, Discard):
        _discard(state, action)
        return [
            ActionResult(
                "discard",
                action.actor_id,
                discarded_rank=reaction_rank_before or state.reaction_rank,
                phase_before=phase_before,
                phase_after=_current_phase_value(state),
                next_player_id=_current_player_id_or_none(state),
                reaction_opened=True,
            )
        ]

    elif isinstance(action, UsePower):
        _use_power(state, action)
        return [
            ActionResult(
                "discard_for_power",
                action.actor_id,
                card=action.source_card,
                power_name=action.power_name.value,
                target_player_id=action.target_player_id,
                target_card_index=action.target_card_index,
                second_target_player_id=action.second_target_player_id,
                second_target_card_index=action.second_target_card_index,
                discarded_rank=action.source_card.rank.value,
                phase_before=phase_before,
                phase_after=_current_phase_value(state),
                next_player_id=_current_player_id_or_none(state),
                reaction_opened=True,
                pending_power_created=True,
            )
        ]

    elif isinstance(action, CallKaboom):
        _call_kaboom(state, action)
        return [
            ActionResult(
                "call_kaboom",
                action.actor_id,
                phase_before=phase_before,
                phase_after=_current_phase_value(state),
                next_player_id=_current_player_id_or_none(state),
            )
        ]
    
    else:
        raise InvalidActionError(f"Unknown action type: {type(action)}")
