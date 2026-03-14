# tests/test_endgame.py
import pytest

from kaboom.cards.card import Card, Rank, Suit
from kaboom.game.turn import apply_action
from kaboom.game.actions import Draw, Discard, CallKaboom, CloseReaction, UsePower, ResolvePendingPower
from kaboom.game.engine import GameEngine
from kaboom.game.phases import GamePhase
from kaboom.exceptions import InvalidActionError
from kaboom.game.validators import get_valid_actions
from kaboom.powers.types import PowerType


def test_cannot_call_kaboom_in_round_one(simple_game_state):
    with pytest.raises(InvalidActionError):
        apply_action(simple_game_state, CallKaboom(actor_id=0))


def test_call_kaboom_marks_player_inactive(simple_game_state):
    # Advance to round 2
    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))
    apply_action(simple_game_state, CloseReaction(actor_id=0))
    apply_action(simple_game_state, Draw(actor_id=1))
    apply_action(simple_game_state, Discard(actor_id=1))
    apply_action(simple_game_state, CloseReaction(actor_id=1))

    apply_action(simple_game_state, CallKaboom(actor_id=0))

    player = simple_game_state.resolve_player(0)
    assert player.active is False
    assert player.revealed is True
    assert simple_game_state.kaboom_called_by == 0


def test_engine_is_game_over_reflects_phase():
    engine = GameEngine(game_id=0, num_players=2, hand_size=4)
    assert engine.is_game_over() is False

    engine.state.phase = GamePhase.GAME_OVER
    assert engine.is_game_over() is True


def test_engine_get_winner_prefers_instant_winner():
    engine = GameEngine(game_id=0, num_players=2, hand_size=4)
    engine.state.phase = GamePhase.GAME_OVER
    engine.state.instant_winner = 1

    assert engine.get_winner() == 1


def test_kaboom_final_discard_still_allows_reaction_before_game_over(simple_game_state):
    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))
    apply_action(simple_game_state, CloseReaction(actor_id=0))
    apply_action(simple_game_state, Draw(actor_id=1))
    apply_action(simple_game_state, Discard(actor_id=1))
    apply_action(simple_game_state, CloseReaction(actor_id=1))

    apply_action(simple_game_state, CallKaboom(actor_id=0))
    simple_game_state.advance_turn()

    apply_action(simple_game_state, Draw(actor_id=1))
    result = apply_action(simple_game_state, Discard(actor_id=1))[0]

    assert result.action == "discard"
    assert result.phase_after == GamePhase.REACTION.value
    assert simple_game_state.phase == GamePhase.REACTION
    assert simple_game_state.pending_game_over_after_reaction is True
    assert get_valid_actions(simple_game_state)

    close_result = apply_action(simple_game_state, CloseReaction(actor_id=1))[0]
    assert close_result.phase_after == GamePhase.GAME_OVER.value
    assert simple_game_state.phase == GamePhase.GAME_OVER


def test_kaboom_final_power_window_still_allows_reaction_or_resolution_before_game_over(simple_game_state):
    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))
    apply_action(simple_game_state, CloseReaction(actor_id=0))
    apply_action(simple_game_state, Draw(actor_id=1))
    apply_action(simple_game_state, Discard(actor_id=1))
    apply_action(simple_game_state, CloseReaction(actor_id=1))

    apply_action(simple_game_state, CallKaboom(actor_id=0))
    simple_game_state.advance_turn()

    simple_game_state.phase = GamePhase.TURN_RESOLVE
    simple_game_state.drawn_card = Card(Rank.SEVEN, Suit.HEARTS)

    result = apply_action(
        simple_game_state,
        UsePower(
            actor_id=1,
            power_name=PowerType.SEE_SELF,
            source_card=simple_game_state.drawn_card,
            target_card_index=0,
        ),
    )[0]

    assert result.action == "discard_for_power"
    assert result.phase_after == GamePhase.REACTION.value
    assert simple_game_state.phase == GamePhase.REACTION
    assert simple_game_state.pending_game_over_after_reaction is True
    assert any(
        isinstance(action, ResolvePendingPower)
        for action in get_valid_actions(simple_game_state)
    )

    resolve_result = apply_action(simple_game_state, ResolvePendingPower(actor_id=1))[0]
    assert resolve_result.phase_after == GamePhase.GAME_OVER.value
    assert simple_game_state.phase == GamePhase.GAME_OVER


def test_reaction_action_space_excludes_inactive_kaboom_player_cards(simple_game_state):
    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))
    apply_action(simple_game_state, CloseReaction(actor_id=0))
    apply_action(simple_game_state, Draw(actor_id=1))
    apply_action(simple_game_state, Discard(actor_id=1))
    apply_action(simple_game_state, CloseReaction(actor_id=1))

    apply_action(simple_game_state, CallKaboom(actor_id=0))
    simple_game_state.advance_turn()
    apply_action(simple_game_state, Draw(actor_id=1))
    apply_action(simple_game_state, Discard(actor_id=1))

    actions = get_valid_actions(simple_game_state)
    assert all(
        getattr(action, "target_player_id", None) != 0
        for action in actions
    )
