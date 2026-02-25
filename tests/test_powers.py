from kaboom.cards.card import Card, Rank, Suit
from kaboom.players import Player
from kaboom.game import GameState
from kaboom.game.turn import apply_action
from kaboom.game.actions import Draw, UsePower


def test_see_self_power():
    state = GameState(
        players=[
            Player(
                id=0,
                name="P1",
                hand=[
                    Card(Rank.SEVEN, Suit.SPADES),
                    Card(Rank.A, Suit.HEARTS),
                ],
            )
        ],
        deck=[Card(Rank.SEVEN, Suit.CLUBS)],
    )

    apply_action(state, Draw(actor_id=0))

    apply_action(
        state,
        UsePower(
            actor_id=0,
            power_name="see_self",
            source_card=state.drawn_card,
            target_card_index=1,
        ),
    )

    assert (0, 1) in state.players[0].memory

def test_see_other_power():
    state = GameState(
        players=[
            Player(id=0, name="P1", hand=[Card(Rank.A, Suit.HEARTS)]),
            Player(id=1, name="P2", hand=[Card(Rank.K, Suit.SPADES)]),
        ],
        deck=[Card(Rank.NINE, Suit.CLUBS)],
    )

    apply_action(state, Draw(actor_id=0))

    apply_action(
        state,
        UsePower(
            actor_id=0,
            power_name="see_other",
            source_card=state.drawn_card,
            target_player_id=1,
            target_card_index=0,
        ),
    )

    assert (1, 0) in state.players[0].memory

def test_blind_swap_power():
    state = GameState(
        players=[
            Player(id=0, name="P1", hand=[Card(Rank.A, Suit.HEARTS)]),
            Player(id=1, name="P2", hand=[Card(Rank.K, Suit.SPADES)]),
        ],
        deck=[Card(Rank.J, Suit.CLUBS)],
    )

    apply_action(state, Draw(actor_id=0))

    apply_action(
        state,
        UsePower(
            actor_id=0,
            power_name="blind_swap",
            source_card=state.drawn_card,
            target_player_id=1,
            target_card_index=0,
            second_target_card_index=0,
        ),
    )

    assert state.players[0].hand[0].rank == Rank.K
    assert state.players[1].hand[0].rank == Rank.A

def test_see_and_swap_power():
    state = GameState(
        players=[
            Player(id=0, name="P1", hand=[Card(Rank.A, Suit.HEARTS)]),
            Player(id=1, name="P2", hand=[Card(Rank.K, Suit.DIAMONDS)]),
        ],
        deck=[Card(Rank.K, Suit.SPADES)],  # black king
    )

    apply_action(state, Draw(actor_id=0))

    apply_action(
        state,
        UsePower(
            actor_id=0,
            power_name="see_and_swap",
            source_card=state.drawn_card,
            target_player_id=0,
            target_card_index=0,
            second_target_player_id=1,
            second_target_card_index=0,
        ),
    )

    # Must have seen both
    assert (0, 0) in state.players[0].memory
    assert (1, 0) in state.players[0].memory

    # Must have swapped
    assert state.players[0].hand[0].rank == Rank.K
    assert state.players[1].hand[0].rank == Rank.A