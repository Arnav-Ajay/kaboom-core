import pytest

from kaboom.game.turn import apply_action
from kaboom.game.actions import CallKaboom
from kaboom.exceptions import InvalidActionError


def test_cannot_call_kaboom_in_round_one(simple_game_state):
    with pytest.raises(InvalidActionError):
        apply_action(simple_game_state, CallKaboom(actor_id=0))


def test_call_kaboom_marks_player_inactive(simple_game_state):
    # Advance to round 2
    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))
    apply_action(simple_game_state, Draw(actor_id=1))
    apply_action(simple_game_state, Discard(actor_id=1))

    apply_action(simple_game_state, CallKaboom(actor_id=0))

    player = simple_game_state.players[0]
    assert player.active is False
    assert player.revealed is True
    assert simple_game_state.kaboom_called_by == 0
