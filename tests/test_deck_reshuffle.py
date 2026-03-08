import pytest
from kaboom.cards.card import Card, Rank, Suit
from kaboom.exceptions import InvalidActionError


def test_deck_reshuffles_when_empty(simple_game_state):

    state = simple_game_state

    # empty the deck
    state.deck = []

    # put cards in discard
    state.discard_pile = state.players[0].hand[:]

    state.ensure_deck()

    assert len(state.deck) > 0
    assert len(state.discard_pile) == 1


def test_ensure_deck_raises_when_no_cards_to_shuffle(simple_game_state):
    state = simple_game_state
    state.deck = []
    # discard pile has only one card, so there is nothing to reshuffle
    state.discard_pile = [Card(Rank.TEN, Suit.CLUBS)]
    with pytest.raises(InvalidActionError):
        state.ensure_deck()
