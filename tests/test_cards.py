# tests/test_cards.py
from kaboom.cards.card import Card, Rank, Suit

def test_red_king_score_zero():
    card = Card(Rank.K, Suit.HEARTS)
    assert card.score_value == 0

    card = Card(Rank.K, Suit.DIAMONDS)
    assert card.score_value == 0


def test_black_king_score_ten():
    card = Card(Rank.K, Suit.SPADES)
    assert card.score_value == 10

    card = Card(Rank.K, Suit.CLUBS)
    assert card.score_value == 10


def test_face_cards_score_ten():
    assert Card(Rank.J, Suit.CLUBS).score_value == 10
    assert Card(Rank.Q, Suit.CLUBS).score_value == 10
    assert Card(Rank.J, Suit.DIAMONDS).score_value == 10
    assert Card(Rank.Q, Suit.DIAMONDS).score_value == 10
    assert Card(Rank.J, Suit.SPADES).score_value == 10
    assert Card(Rank.Q, Suit.SPADES).score_value == 10
    assert Card(Rank.J, Suit.HEARTS).score_value == 10
    assert Card(Rank.Q, Suit.HEARTS).score_value == 10


def test_number_cards_score_face_value():
    assert Card(Rank.TWO, Suit.SPADES).score_value == 2
    assert Card(Rank.TEN, Suit.HEARTS).score_value == 10


def test_card_string_representation():
    assert str(Card(Rank.A, Suit.CLUBS)) == "A♣"
    assert str(Card(Rank.TWO, Suit.HEARTS)) == "2♥"
    assert str(Card(Rank.THREE, Suit.DIAMONDS)) == "3♦"
    assert str(Card(Rank.FOUR, Suit.SPADES)) == "4♠"
    assert str(Card(Rank.FIVE, Suit.CLUBS)) == "5♣"
    assert str(Card(Rank.SIX, Suit.HEARTS)) == "6♥"
    assert str(Card(Rank.SEVEN, Suit.DIAMONDS)) == "7♦"
    assert str(Card(Rank.EIGHT, Suit.SPADES)) == "8♠"
    assert str(Card(Rank.NINE, Suit.CLUBS)) == "9♣"
    assert str(Card(Rank.TEN, Suit.HEARTS)) == "10♥"
    assert str(Card(Rank.J, Suit.DIAMONDS)) == "J♦"
    assert str(Card(Rank.Q, Suit.SPADES)) == "Q♠"
    assert str(Card(Rank.K, Suit.CLUBS)) == "K♣"
