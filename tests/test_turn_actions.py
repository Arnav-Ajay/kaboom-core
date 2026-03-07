# tests/test_turn_actions.py
import pytest

from kaboom.game.turn import apply_action
from kaboom.game.actions import Draw, Discard, Replace, CallKaboom, CloseReaction
from kaboom.exceptions import InvalidActionError

def test_draw_adds_drawn_card(simple_game_state):
    apply_action(simple_game_state, Draw(actor_id=0))
    assert simple_game_state.drawn_card is not None
    assert len(simple_game_state.deck) == 1

def test_cannot_draw_twice(simple_game_state):
    apply_action(simple_game_state, Draw(actor_id=0))
    with pytest.raises(InvalidActionError):
        apply_action(simple_game_state, Draw(actor_id=0))

def test_discard_without_draw_fails(simple_game_state):
    with pytest.raises(InvalidActionError):
        apply_action(simple_game_state, Discard(actor_id=0))

def test_discard_advances_turn(simple_game_state):
    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    assert simple_game_state.current_player_index == 1
    assert simple_game_state.drawn_card is None
    assert simple_game_state.reaction_open is True


def test_replace_discards_old_card(simple_game_state):
    p1 = simple_game_state.resolve_player(0)
    old_card = p1.hand[0]

    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Replace(actor_id=0, target_index=0))

    assert old_card in simple_game_state.discard_pile
    assert len(p1.hand) == 4
    assert simple_game_state.drawn_card is None
    assert simple_game_state.reaction_open is True


def test_replace_invalid_index_fails(simple_game_state):
    apply_action(simple_game_state, Draw(actor_id=0))
    with pytest.raises(InvalidActionError):
        apply_action(simple_game_state, Replace(actor_id=0, target_index=99))


def test_player_cannot_act_out_of_turn(simple_game_state):
    with pytest.raises(InvalidActionError):
        apply_action(simple_game_state, Draw(actor_id=1))


def test_round_increments_after_full_cycle(simple_game_state):
    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))
    apply_action(simple_game_state, CloseReaction(actor_id=0))

    apply_action(simple_game_state, Draw(actor_id=1))
    apply_action(simple_game_state, Discard(actor_id=1))
    apply_action(simple_game_state, CloseReaction(actor_id=1))

    assert simple_game_state.round_number == 2
