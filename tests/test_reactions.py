from kaboom.cards.card import Card, Rank, Suit
import pytest
from kaboom.players.player import Player
from kaboom.game.game_state import GameState
from kaboom.game.actions import Draw, Discard, Replace, CloseReaction
from kaboom.game.turn import apply_action
from kaboom.game.reaction import (
    react_discard_own_card,
    react_discard_other_card,
    react_discard_own_cards,
    react_discard_other_cards,
    ReactionResult,
)
from kaboom.game.phases import GamePhase
from kaboom.exceptions import InvalidActionError


def test_reaction_phase_transitions(simple_game_state):
    state = simple_game_state

    # start at draw phase
    assert state.phase == GamePhase.TURN_DRAW

    apply_action(state, Draw(actor_id=0))
    assert state.phase == GamePhase.TURN_RESOLVE

    # a discard should open a reaction window and flip the phase
    apply_action(state, Discard(actor_id=0))
    assert state.phase == GamePhase.REACTION
    assert state.reaction_open is True

    # closing the window resets to TURN_DRAW even if the closer isn't the
    # initiator (the validation allows any actor to close)
    apply_action(state, CloseReaction(actor_id=1))
    assert state.phase == GamePhase.TURN_DRAW
    assert not state.reaction_open


def test_reaction_penalty_and_instant_win():
    # create a minimal two-player state where player1 has one card matching the
    # next reaction rank and player2 has a nonmatching card to incur a penalty.
    p1 = Player(id=0, name="P1", hand=[Card(Rank.FOUR, Suit.SPADES)])
    p2 = Player(id=1, name="P2", hand=[Card(Rank.THREE, Suit.CLUBS)])
    # we need at least one card remaining in the deck for the penalty draw
    state = GameState(players=[p1, p2], deck=[Card(Rank.A, Suit.HEARTS), Card(Rank.TWO, Suit.CLUBS)])

    # player1 draws and discards the four, reaction rank becomes '4'
    apply_action(state, Draw(actor_id=0))
    apply_action(state, Discard(actor_id=0))

    # player2 attempts wrong reaction -> penalty
    res: ReactionResult = react_discard_own_card(state, actor_id=1, card_index=0)
    assert not res.success and res.penalty_applied
    assert len(state.resolve_player(1).hand) == 2

    # set up scenario for instant win: arrange for the drawn card to match the
    # lone card held by player2 so that a successful reaction empties their hand.
    p1.hand[:] = [Card(Rank.FIVE, Suit.DIAMONDS)]
    p2.hand[:] = [Card(Rank.FIVE, Suit.HEARTS)]
    state = GameState(players=[p1, p2], deck=[Card(Rank.FIVE, Suit.CLUBS)])
    apply_action(state, Draw(actor_id=0))
    apply_action(state, Discard(actor_id=0))

    res = react_discard_own_card(state, actor_id=1, card_index=0)
    assert res.success and res.instant_win_player == 1
    assert state.phase == GamePhase.GAME_OVER


def test_reactable_order(simple_game_state):
    state = simple_game_state
    # set an initiator manually and ensure ordering works
    state.reaction_initiator = 0
    order = [p.id for p in state.reaction_order()]
    # since players list is [0,1], order should start after 0 -> [1,0]
    assert order == [1, 0]

    # if initiator not in active players or None, order should match raw list
    state.reaction_initiator = None
    assert [p.id for p in state.reaction_order()] == [0, 1]


def test_validate_turn_restrictions(simple_game_state):
    state = simple_game_state
    # wrong actor
    with pytest.raises(InvalidActionError):
        apply_action(state, Draw(actor_id=1))

    # open a reaction and ensure normal actions are blocked
    apply_action(state, Draw(actor_id=0))
    apply_action(state, Discard(actor_id=0))
    with pytest.raises(InvalidActionError):
        apply_action(state, Draw(actor_id=0))
    # closing still works
    apply_action(state, CloseReaction(actor_id=0))

