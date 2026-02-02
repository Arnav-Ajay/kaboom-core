# kaboom/tests/test_reaction_engine.py
from kaboom.cards import Card, Rank, Suit
from kaboom.game import (
    react_discard_own_cards,
    react_discard_other_cards,
)
from kaboom.game import apply_action
from kaboom.game import Draw, Discard

def test_react_discard_own_card_success(simple_game_state):
    # P1 discards 5 → reaction opens
    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    result = react_discard_own_cards(
        state=simple_game_state,
        actor_id=1,
        card_indices=[0],
    )


    assert result.success is True
    assert len(simple_game_state.players[1].hand) == 3
    assert simple_game_state.reaction_open is False

def test_react_wrong_match_penalty(simple_game_state):
    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    # P2 attempts wrong match
    result = react_discard_own_cards(
        state=simple_game_state,
        actor_id=1,
        card_indices=[1],
    )


    assert result.success is False
    assert result.penalty_applied is True
    assert len(simple_game_state.players[1].hand) == 5


def test_react_discard_other_card(simple_game_state):
    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    # P2 steals P1's 5♠
    result = react_discard_other_cards(
        state=simple_game_state,
        actor_id=1,
        target_player_id=0,
        target_card_indices=[0],
        give_card_indices=[0],
    )

    assert result.success is True
    assert len(simple_game_state.players[0].hand) == 4
    assert len(simple_game_state.players[1].hand) == 3


def test_instant_win_on_zero_cards(simple_game_state):
    # Give P2 only one matching card
    simple_game_state.players[1].hand = [
        Card(Rank.FIVE, Suit.CLUBS)
    ]

    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    result = react_discard_own_cards(
        state=simple_game_state,
        actor_id=1,
        card_indices=[0],
    )


    assert result.instant_win_player == 1
    assert simple_game_state.instant_winner == 1

def test_multi_card_self_match(simple_game_state):
    # Give P2 two matching cards
    simple_game_state.players[1].hand = [
        Card(Rank.FIVE, Suit.CLUBS),
        Card(Rank.FIVE, Suit.HEARTS),
        Card(Rank.K, Suit.DIAMONDS),
    ]

    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    result = react_discard_own_cards(
        state=simple_game_state,
        actor_id=1,
        card_indices=[0, 1],
    )

    assert result.success is True
    assert len(simple_game_state.players[1].hand) == 1
    assert simple_game_state.reaction_open is False

def test_multi_card_partial_mismatch_penalty(simple_game_state):
    simple_game_state.players[1].hand = [
        Card(Rank.FIVE, Suit.CLUBS),
        Card(Rank.SEVEN, Suit.HEARTS),
    ]

    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    result = react_discard_own_cards(
        state=simple_game_state,
        actor_id=1,
        card_indices=[0, 1],
    )

    assert result.success is False
    assert result.penalty_applied is True
    assert len(simple_game_state.players[1].hand) == 3

def test_multi_card_steal(simple_game_state):
    # P1 has two matching cards
    simple_game_state.players[0].hand = [
        Card(Rank.FIVE, Suit.SPADES),
        Card(Rank.FIVE, Suit.DIAMONDS),
    ]

    # P2 has two cards to give
    simple_game_state.players[1].hand = [
        Card(Rank.A, Suit.CLUBS),
        Card(Rank.K, Suit.HEARTS),
    ]

    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    result = react_discard_other_cards(
        state=simple_game_state,
        actor_id=1,
        target_player_id=0,
        target_card_indices=[0, 1],
        give_card_indices=[0, 1],
    )

    assert result.success is True
    assert len(simple_game_state.players[0].hand) == 2
    assert len(simple_game_state.players[1].hand) == 0

def test_multi_card_instant_win(simple_game_state):
    simple_game_state.players[1].hand = [
        Card(Rank.FIVE, Suit.CLUBS),
        Card(Rank.FIVE, Suit.HEARTS),
    ]

    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    result = react_discard_own_cards(
        state=simple_game_state,
        actor_id=1,
        card_indices=[0, 1],
    )

    assert result.instant_win_player == 1
    assert simple_game_state.instant_winner == 1
