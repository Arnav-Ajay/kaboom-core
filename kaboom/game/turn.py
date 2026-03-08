# kaboom/game/turn.py
from __future__ import annotations

from ..exceptions import InvalidActionError
from .actions import (
    Action,
    Draw,
    Discard,
    Replace,
    UsePower,
    CallKaboom,
    CloseReaction,
    ReactDiscardOwnCard,
    ReactDiscardOwnCards,
    ReactDiscardOtherCard,
    ReactDiscardOtherCards
    )
from .reaction import (
    close_reaction,
    react_discard_own_card,
    react_discard_own_cards,
    react_discard_other_card,
    react_discard_other_cards
    )
from .game_state import GameState
from .validators import validate_turn_owner, validate_index, validate_turn, validate_use_power_payload
from ..powers.registry import POWER_REGISTRY
from .results import ActionResult
from .phases import GamePhase

def _draw(state: GameState, action: Draw) -> None:

    if state.drawn_card is not None:
        raise InvalidActionError("Already holding a drawn card.")

    state.ensure_deck()

    if not state.deck:
        raise InvalidActionError("Deck is empty.")

    state.drawn_card = state.deck.pop()
    state.phase = GamePhase.TURN_RESOLVE

def _replace(state: GameState, action: Replace) -> None:
    if state.drawn_card is None:
        raise InvalidActionError("No drawn card to replace with.")

    player = state.current_player()

    validate_index(len(player.hand), action.target_index, "target_index")

    replaced = player.hand[action.target_index]
    state.discard_pile.append(replaced)

    player.hand[action.target_index] = state.drawn_card
    state.drawn_card = None

    # Open reaction window (phase switches to REACTION)
    state.reaction_rank = replaced.rank.value
    state.reaction_initiator = player.id
    state.reaction_open = True
    state.phase = GamePhase.REACTION

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
    state.phase = GamePhase.REACTION

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
    power.apply(state, action)

    state.discard_pile.append(card)
    state.drawn_card = None
    state.advance_turn()
    # after a power use the turn should reset to DRAW for the next player
    state.phase = GamePhase.TURN_DRAW

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
    if state.phase == GamePhase.GAME_OVER:
        raise InvalidActionError("Game is already over.")
    
    # ------------------------------------------------
    # Reaction resolution path (bypass turn rules)
    # ------------------------------------------------

    if isinstance(action, ReactDiscardOwnCard):
        result = react_discard_own_card(state, action.actor_id, action.card_index)
        return [result]

    elif isinstance(action, ReactDiscardOwnCards):
        result = react_discard_own_cards(state, action.actor_id, action.card_indices)
        return [result]

    elif isinstance(action, ReactDiscardOtherCard):
        result = react_discard_other_card(
            state,
            action.actor_id,
            action.target_player_id,
            action.target_card_index,
            action.give_card_index,
        )
        return [result]

    elif isinstance(action, ReactDiscardOtherCards):
        result = react_discard_other_cards(
            state,
            action.actor_id,
            action.target_player_id,
            action.target_card_indices,
            action.give_card_indices,
        )
        return [result]

    elif isinstance(action, CloseReaction):
        close_reaction(state)
        return [
            ActionResult(
                "close_reaction",
                action.actor_id,
                reaction_closed=True,
                instant_winner=state.instant_winner,
            )
        ]

    # ------------------------------------------------
    # Normal turn validation
    # ------------------------------------------------
    if state.reaction_open and not isinstance(
        action,
        (
            CloseReaction,
            ReactDiscardOwnCard,
            ReactDiscardOwnCards,
            ReactDiscardOtherCard,
            ReactDiscardOtherCards,
        ),
    ):
        raise InvalidActionError("Reaction window open.")

    validate_turn_owner(state, action.actor_id)
    validate_turn(state)
    if isinstance(action, UsePower):
        validate_use_power_payload(action)

    phase = state.phase

    if phase == GamePhase.REACTION and not isinstance(action, CloseReaction):
        raise InvalidActionError("Must resolve reaction first.")

    if phase == GamePhase.TURN_DRAW and not (isinstance(action, Draw) or isinstance(action, CallKaboom)):
        raise InvalidActionError("Must draw first.")

    if phase == GamePhase.TURN_RESOLVE and isinstance(action, Draw):
        raise InvalidActionError("Already drawn this turn.")

    # ------------------------------------------------
    # Turn actions
    # ------------------------------------------------
    
    if isinstance(action, Draw):
        _draw(state, action)
        return [ActionResult("draw", action.actor_id, card=state.drawn_card)]

    elif isinstance(action, Replace):
        _replace(state, action)
        return [ActionResult("replace", action.actor_id, reaction_opened=True)]

    elif isinstance(action, Discard):
        _discard(state, action)
        return [ActionResult("discard", action.actor_id, reaction_opened=True)]

    elif isinstance(action, UsePower):
        _use_power(state, action)
        return [ActionResult("use_power", action.actor_id)]

    elif isinstance(action, CallKaboom):
        _call_kaboom(state, action)
        return [ActionResult("call_kaboom", action.actor_id)]
    
    else:
        raise InvalidActionError(f"Unknown action type: {type(action)}")
