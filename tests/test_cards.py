# kaboom/tests/test_cards.py
from kaboom.cards import Card, Rank, Suit

def test_red_king_score_zero():
    card = Card(Rank.K, Suit.HEARTS)
    assert card.score_value == 0


def test_black_king_score_ten():
    card = Card(Rank.K, Suit.SPADES)
    assert card.score_value == 10


def test_face_cards_score_ten():
    assert Card(Rank.J, Suit.CLUBS).score_value == 10
    assert Card(Rank.Q, Suit.DIAMONDS).score_value == 10


def test_number_cards_score_face_value():
    assert Card(Rank.TWO, Suit.SPADES).score_value == 2
    assert Card(Rank.TEN, Suit.HEARTS).score_value == 10


def test_card_string_representation():
    card = Card(Rank.A, Suit.CLUBS)
    assert str(card) == "A♣"
