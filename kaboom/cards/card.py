# kaboom/cards/card.py
from enum import Enum
from dataclasses import dataclass


class Suit(str, Enum):
    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"


class Rank(str, Enum):
    A = "A"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    J = "J"
    Q = "Q"
    K = "K"


@dataclass(frozen=True, slots=True)
class Card:
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank.value}{self.suit.value}"
    
    @property
    def score_value(self) -> int:
        if self.rank == Rank.K and self.suit in {Suit.HEARTS, Suit.DIAMONDS}:
            return 0
        if self.rank == Rank.A:
            return 1
        if self.rank in {Rank.J, Rank.Q, Rank.K}:
            return 10
        return int(self.rank.value)
