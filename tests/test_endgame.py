# tests/test_endgame.py
import pytest

from kaboom.game.turn import apply_action
from kaboom.game.actions import Draw, Discard, CallKaboom, CloseReaction
from kaboom.game.engine import GameEngine
from kaboom.game.phases import GamePhase
from kaboom.exceptions import InvalidActionError


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
