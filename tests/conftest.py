# kaboom/tests/conftest.py
import pytest
from kaboom.cards import Card, Rank, Suit
from kaboom.players import Player
from kaboom.game import GameState

@pytest.fixture
def simple_game_state():
    return GameState(
        players=[
            Player(
                id=0,
                name="P1",
                hand=[
                    Card(Rank.FIVE, Suit.SPADES),
                    Card(Rank.TEN, Suit.HEARTS),
                    Card(Rank.A, Suit.HEARTS),
                    Card(Rank.A, Suit.DIAMONDS),
                ],
            ),
            Player(
                id=1,
                name="P2",
                hand=[
                    Card(Rank.FIVE, Suit.CLUBS),
                    Card(Rank.K, Suit.DIAMONDS),
                    Card(Rank.SIX, Suit.HEARTS),
                    Card(Rank.THREE, Suit.HEARTS),
                ],
            ),
        ],
        deck=[
            Card(Rank.SEVEN, Suit.CLUBS),
            Card(Rank.FIVE, Suit.HEARTS),  # drawn first
        ],
    )
