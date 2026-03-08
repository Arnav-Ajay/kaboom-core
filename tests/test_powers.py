# tests/test_powers.py
from kaboom.cards.card import Card, Rank, Suit
from kaboom.players.player import Player
from kaboom.game.game_state import GameState
from kaboom.game.actions import  Draw, UsePower
from kaboom.game.turn import apply_action
from kaboom.powers.types import PowerType

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
            power_name=PowerType.SEE_SELF,
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
            power_name=PowerType.SEE_OTHER,
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

    # give everybody some memory about these positions
    state.players[0].remember(0, 0, state.players[0].hand[0])
    state.players[0].remember(1, 0, state.players[1].hand[0])
    state.players[1].remember(0, 0, state.players[0].hand[0])

    apply_action(state, Draw(actor_id=0))

    apply_action(
        state,
        UsePower(
            actor_id=0,
            power_name=PowerType.BLIND_SWAP,
            source_card=state.drawn_card,
            target_player_id=0,
            target_card_index=0,
            second_target_player_id=1,
            second_target_card_index=0,
        ),
    )

    assert state.players[0].hand[0].rank == Rank.K
    assert state.players[1].hand[0].rank == Rank.A
    # memories should have moved
    assert state.players[0].memory.get((0,0)).rank == Rank.K
    assert state.players[0].memory.get((1,0)).rank == Rank.A
    # the card P1 remembered originally (A at 0,0) has now moved to (1,0)
    assert state.players[1].memory.get((1,0)).rank == Rank.A
    # and there should no longer be an entry for (0,0)
    assert (0,0) not in state.players[1].memory

def test_see_and_swap_power():
    state = GameState(
        players=[
            Player(id=0, name="P1", hand=[Card(Rank.A, Suit.HEARTS)]),
            Player(id=1, name="P2", hand=[Card(Rank.K, Suit.DIAMONDS)]),
        ],
        deck=[Card(Rank.K, Suit.SPADES)],  # black king
    )

    # prepopulate other players' memory about those positions
    state.players[1].remember(0, 0, state.players[0].hand[0])
    state.players[1].remember(1, 0, state.players[1].hand[0])

    apply_action(state, Draw(actor_id=0))

    apply_action(
        state,
        UsePower(
            actor_id=0,
            power_name=PowerType.SEE_AND_SWAP,
            source_card=state.drawn_card,
            target_player_id=0,
            target_card_index=0,
            second_target_player_id=1,
            second_target_card_index=0,
        ),
    )

    # Must have seen both
    assert (0, 0) in state.resolve_player(0).memory
    assert (1, 0) in state.resolve_player(0).memory

    # Must have swapped
    assert state.resolve_player(0).hand[0].rank == Rank.K
    assert state.resolve_player(1).hand[0].rank == Rank.A
    # external memory should also have shifted
    assert state.players[1].memory.get((0,0)).rank == Rank.K
    assert state.players[1].memory.get((1,0)).rank == Rank.A