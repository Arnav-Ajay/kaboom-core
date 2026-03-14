# kaboom/game/validators.py

# Basic validation of a turn-based action.
# This file is deliberately minimal so that callers can use it before performing type-specific checks.
# It is used by :func:`apply_action` but can also be invoked by external code (e.g. AI agents) to verify that their intended move is legal.

# The following conditions are enforced:
# * The game must not already be over.
# * It must be the actor's turn.
# * No reaction window may be open; reactions are handled separately.

from itertools import combinations

from ..exceptions import InvalidActionError
from .game_state import GameState
from .phases import GamePhase
from .actions import (
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
from ..powers.types import PowerType
from ..powers.registry import get_power_for_card

def validate_turn_owner(state: GameState, actor_id: int) -> None:
    current = state.current_player()
    if current.id != actor_id:
        raise InvalidActionError("Not this player's turn.")
    if not current.active:
        raise InvalidActionError("Inactive player cannot act.")
    
def validate_turn(state: GameState):

    if state.phase == GamePhase.GAME_OVER:
        raise InvalidActionError("Game is already over.")

    if state.reaction_open:
        raise InvalidActionError("Cannot take regular action while reaction is open.")

def validate_index(length: int, index: int, name: str):
    if index is None:
        raise InvalidActionError(f"{name} required.")
    if index < 0 or index >= length:
        raise InvalidActionError(f"{name} out of range.")
    
def get_valid_actions(state: GameState):
    """
    Return all valid actions for the current player.

    This exposes the *complete* action space for simulations,
    reinforcement learning, or AI agents.
    """

    if state.phase == GamePhase.GAME_OVER:
        return []

    player = state.current_player()
    actions = []

    if state.phase == GamePhase.OPENING_PEEK:
        peek_count = state.required_opening_peek_count(player.id)
        for combo in combinations(range(len(player.hand)), peek_count):
            actions.append(OpeningPeek(actor_id=player.id, card_indices=combo))
        if not actions and peek_count == 0:
            actions.append(OpeningPeek(actor_id=player.id, card_indices=()))
        return actions

    # ------------------------------------------------
    # REACTION PHASE
    # ------------------------------------------------

    if state.phase == GamePhase.REACTION:
        if state.pending_power_action is not None:
            actions.append(ResolvePendingPower(actor_id=state.pending_power_action.actor_id))

        for reacting_player in state.reactable_players(exclude_initiator=False):
            if not state.can_attempt_reaction(reacting_player.id):
                continue
            for idx in range(len(reacting_player.hand)):
                actions.append(
                    ReactDiscardOwnCard(actor_id=reacting_player.id, card_index=idx)
                )

            for target in state.players:
                if target.id == reacting_player.id:
                    continue
                if not target.active:
                    continue

                for idx in range(len(target.hand)):
                    for give_idx in range(len(reacting_player.hand)):
                        actions.append(
                            ReactDiscardOtherCard(
                                actor_id=reacting_player.id,
                                target_player_id=target.id,
                                target_card_index=idx,
                                give_card_index=give_idx,
                            )
                        )

        if state.pending_power_action is None:
            actions.append(CloseReaction(actor_id=player.id))
        return actions

    # ------------------------------------------------
    # TURN DRAW
    # ------------------------------------------------

    if state.phase == GamePhase.TURN_DRAW:
        actions.append(Draw(actor_id=player.id))

        if state.round_number > 1:
            actions.append(CallKaboom(actor_id=player.id))

        return actions

    # ------------------------------------------------
    # TURN RESOLVE
    # ------------------------------------------------

    if state.phase == GamePhase.TURN_RESOLVE:

        actions.append(Discard(actor_id=player.id))

        for i in range(len(player.hand)):
            actions.append(
                Replace(actor_id=player.id, target_index=i)
            )

        # power actions
        if state.drawn_card:
            power_type = get_power_for_card(state.drawn_card)

            if power_type:
                actions.append(
                    UsePower(
                        actor_id=player.id,
                        power_name=power_type,
                        source_card=state.drawn_card,
                    )
                )

        return actions

    return actions

def validate_use_power_payload(action: UsePower) -> None:
    name = action.power_name

    if name == PowerType.SEE_SELF:
        if action.target_card_index is None:
            raise InvalidActionError("SeeSelfPower requires target_card_index.")
        if action.target_player_id is not None:
            raise InvalidActionError("SeeSelfPower does not use target_player_id.")
        if action.second_target_player_id is not None or action.second_target_card_index is not None:
            raise InvalidActionError("SeeSelfPower does not use second target fields.")

    elif name == PowerType.SEE_OTHER:
        if action.target_player_id is None or action.target_card_index is None:
            raise InvalidActionError("SeeOtherPower requires target_player_id and target_card_index.")
        if action.second_target_player_id is not None or action.second_target_card_index is not None:
            raise InvalidActionError("SeeOtherPower does not use second target fields.")

    elif name in {PowerType.BLIND_SWAP, PowerType.SEE_AND_SWAP}:
        required = (
            action.target_player_id,
            action.target_card_index,
            action.second_target_player_id,
            action.second_target_card_index,
        )
        if any(v is None for v in required):
            raise InvalidActionError(
                f"{name} requires target_player_id, target_card_index, "
                "second_target_player_id, and second_target_card_index."
            )
        if action.target_player_id != action.actor_id:
            raise InvalidActionError(f"{name} must start from the acting player's own card.")
        if action.second_target_player_id == action.actor_id:
            raise InvalidActionError(f"{name} must target another player's card as the second card.")

    else:
        raise InvalidActionError(f"Unknown power: {name}")
