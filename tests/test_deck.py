# tests/test_deck.py
from kaboom.cards.card import Card, Rank, Suit

def _shuffle_deck(deck):
    import random
    random.shuffle(deck)
    return deck

def _create_deck():
    deck = []
    for suit in Suit:
        for rank in Rank:
            deck.append(Card(rank, suit))
    return _shuffle_deck(deck)

def test_create_deck():
    deck = _create_deck()
    assert len(deck) == 52
    assert len([c for c in deck if c.suit == '♠']) == 13
    assert len([c for c in deck if c.suit == '♥']) == 13
    assert len([c for c in deck if c.suit == '♦']) == 13
    assert len([c for c in deck if c.suit == '♣']) == 13
    assert len([c for c in deck if c.rank == 'A']) == 4
    assert len([c for c in deck if c.rank == '2']) == 4
    assert len([c for c in deck if c.rank == '3']) == 4
    assert len([c for c in deck if c.rank == '4']) == 4
    assert len([c for c in deck if c.rank == '5']) == 4
    assert len([c for c in deck if c.rank == '6']) == 4
    assert len([c for c in deck if c.rank == '7']) == 4
    assert len([c for c in deck if c.rank == '8']) == 4
    assert len([c for c in deck if c.rank == '9']) == 4
    assert len([c for c in deck if c.rank == '10']) == 4
    assert len([c for c in deck if c.rank == 'J']) == 4
    assert len([c for c in deck if c.rank == 'Q']) == 4
    assert len([c for c in deck if c.rank == 'K']) == 4