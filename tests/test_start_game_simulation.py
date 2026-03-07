# tests/test_start_game_simulation.py
from kaboom.cards.card import Card, Rank, Suit
from kaboom.players.player import Player
from kaboom.game.game_state import GameState

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

def _see_cards_at_start(state: GameState):
    # each player can see 2 of their own cards
    for player in state.players:
        player.remember(player.id, 0, player.hand[0])
        player.remember(player.id, 1, player.hand[1])

def test_game_start():

    players = _create_players(2)
    deck = _create_deck()
    _assign_hands(players, deck)
    
    state = GameState(
        players=players,
        deck=deck,
        discard_pile=[],
        current_player_index=0,
        round_number=1,
        drawn_card = None,
        reaction_rank = None,
        reaction_initiator = None,
        reaction_open = False,

        kaboom_called_by = None,
        instant_winner = None
    )
    _see_cards_at_start(state)

    assert state.round_number == 1
    assert len(state.players) == 2
    assert len(state.deck) == 44
    assert len(state.discard_pile) == 0
    assert len(state.players[0].memory) == 2
    assert len(state.players[1].memory) == 2