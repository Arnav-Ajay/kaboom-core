# tests/test_players.py
from kaboom.cards.card import Card, Rank, Suit
from kaboom.players.player import Player

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

def _create_players(num_players):
    return [Player(id=i, name=f"P{i+1}") for i in range(num_players)]

def _assign_hands(players, deck, hand_size=4):
    for player in players:
        player.hand = []

    for _ in range(hand_size):
        for player in players:
            player.hand.append(deck.pop())

def test_create_players():
    players = _create_players(2)
    assert len(players) == 2
    assert players[0].id == 0
    assert players[1].id == 1
    assert type(players[0].id) == int
    assert type(players[1].id) == int

    assert players[0].name == 'P1'
    assert players[1].name == 'P2'
    assert type(players[0].name) == str
    assert type(players[1].name) == str

    assert players[0].hand == []
    assert players[1].hand == []
    

    deck = _create_deck()
    assert len(deck) == 52
    
    _assign_hands(players, deck)
    assert len(players[0].hand) == 4
    assert len(players[1].hand) == 4
    assert type(players[0].hand[0]) == Card
    assert type(players[1].hand[0]) == Card
    assert len(deck) == 44