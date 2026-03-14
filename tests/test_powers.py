# tests/test_powers.py
from kaboom.cards.card import Card, Rank, Suit
from kaboom.players.player import Player
from kaboom.game.game_state import GameState
from kaboom.game.actions import  Draw, UsePower, ResolvePendingPower, ReactDiscardOwnCard
from kaboom.game.turn import apply_action
from kaboom.game.validators import get_valid_actions
from kaboom.powers.types import PowerType
import pytest
from kaboom.exceptions import InvalidActionError

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
    apply_action(state, ResolvePendingPower(actor_id=0))

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
    apply_action(state, ResolvePendingPower(actor_id=0))

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
    apply_action(state, ResolvePendingPower(actor_id=0))

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
    apply_action(state, ResolvePendingPower(actor_id=0))

    # Must have seen both
    assert (0, 0) in state.resolve_player(0).memory
    assert (1, 0) in state.resolve_player(0).memory

    # Must have swapped
    assert state.resolve_player(0).hand[0].rank == Rank.K
    assert state.resolve_player(1).hand[0].rank == Rank.A
    # external memory should also have shifted
    assert state.players[1].memory.get((0,0)).rank == Rank.K
    assert state.players[1].memory.get((1,0)).rank == Rank.A

def test_blind_swap_preserves_memory_by_moving_it_to_new_location():
    state = GameState(
        players=[
            Player(
                id=0,
                name="P1",
                hand=[Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.A, Suit.HEARTS)],
            ),
            Player(
                id=1,
                name="P2",
                hand=[Card(Rank.NINE, Suit.CLUBS), Card(Rank.TEN, Suit.SPADES)],
            ),
        ],
        deck=[Card(Rank.J, Suit.CLUBS)],
    )

    # Each player knows one of their own cards before the blind swap.
    state.players[0].remember(0, 1, state.players[0].hand[1])
    state.players[1].remember(1, 1, state.players[1].hand[1])

    apply_action(state, Draw(actor_id=0))
    apply_action(
        state,
        UsePower(
            actor_id=0,
            power_name=PowerType.BLIND_SWAP,
            source_card=state.drawn_card,
            target_player_id=0,
            target_card_index=1,
            second_target_player_id=1,
            second_target_card_index=1,
        ),
    )
    apply_action(state, ResolvePendingPower(actor_id=0))

    # Knowledge should move with the swapped cards, not disappear.
    assert state.players[0].memory.get((1, 1)).rank == Rank.A
    assert (0, 1) not in state.players[0].memory
    assert state.players[1].memory.get((0, 1)).rank == Rank.TEN
    assert (1, 1) not in state.players[1].memory


def test_red_king_does_not_expose_use_power_action():
    state = GameState(
        players=[
            Player(id=0, name="P1", hand=[Card(Rank.A, Suit.HEARTS)]),
            Player(id=1, name="P2", hand=[Card(Rank.FIVE, Suit.CLUBS)]),
        ],
        deck=[Card(Rank.K, Suit.HEARTS)],
    )

    apply_action(state, Draw(actor_id=0))

    actions = get_valid_actions(state)

    assert all(action.__class__.__name__ != "UsePower" for action in actions)


def test_discard_for_power_opens_pending_power_contention():
    state = GameState(
        players=[
            Player(id=0, name="P1", hand=[Card(Rank.A, Suit.HEARTS)]),
            Player(id=1, name="P2", hand=[Card(Rank.FIVE, Suit.CLUBS)]),
        ],
        deck=[Card(Rank.J, Suit.CLUBS)],
    )

    apply_action(state, Draw(actor_id=0))

    results = apply_action(
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

    assert results[0].action == "discard_for_power"
    assert state.pending_power_action is not None
    assert state.discard_pile[-1].rank == Rank.J
    assert state.phase.name == "REACTION"

    reaction_actions = [action for action in get_valid_actions(state) if action.__class__.__name__.startswith("React")]
    assert all(action.__class__.__name__ != "ReactDiscardOwnCards" for action in reaction_actions)
    assert all(action.__class__.__name__ != "ReactDiscardOtherCards" for action in reaction_actions)


def test_reaction_can_cancel_pending_power_priority():
    state = GameState(
        players=[
            Player(id=0, name="P1", hand=[Card(Rank.A, Suit.HEARTS)]),
            Player(id=1, name="P2", hand=[Card(Rank.J, Suit.SPADES), Card(Rank.FIVE, Suit.CLUBS)]),
        ],
        deck=[Card(Rank.J, Suit.CLUBS)],
    )

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

    reaction = next(
        action
        for action in get_valid_actions(state)
        if isinstance(action, ReactDiscardOwnCard) and action.actor_id == 1
    )
    result = apply_action(state, reaction)[0]

    assert result.success is True
    assert result.phase_before == "reaction"
    assert result.phase_after == "turn_draw"
    assert result.cancelled_pending_power is True
    assert state.pending_power_action is None
    assert state.resolve_player(0).hand[0].rank == Rank.A


def test_resolve_pending_power_reports_metadata():
    state = GameState(
        players=[
            Player(id=0, name="P1", hand=[Card(Rank.A, Suit.HEARTS)]),
            Player(id=1, name="P2", hand=[Card(Rank.FIVE, Suit.CLUBS)]),
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

    result = apply_action(state, ResolvePendingPower(actor_id=0))[0]

    assert result.action == "use_power"
    assert result.pending_power_resolved is True
    assert result.phase_before == "reaction"
    assert result.phase_after == "turn_draw"
    assert result.target_player_id == 1
    assert result.target_card_index == 0

def test_blind_swap_requires_actor_card_against_other_player_card():
    state = GameState(
        players=[
            Player(
                id=0,
                name="P1",
                hand=[Card(Rank.A, Suit.HEARTS), Card(Rank.TWO, Suit.CLUBS)],
            ),
            Player(
                id=1,
                name="P2",
                hand=[Card(Rank.K, Suit.SPADES), Card(Rank.THREE, Suit.DIAMONDS)],
            ),
        ],
        deck=[Card(Rank.J, Suit.CLUBS)],
    )

    apply_action(state, Draw(actor_id=0))

    with pytest.raises(InvalidActionError):
        apply_action(
            state,
            UsePower(
                actor_id=0,
                power_name=PowerType.BLIND_SWAP,
                source_card=state.drawn_card,
                target_player_id=1,
                target_card_index=0,
                second_target_player_id=1,
                second_target_card_index=1,
            ),
        )

    with pytest.raises(InvalidActionError):
        apply_action(
            state,
            UsePower(
                actor_id=0,
                power_name=PowerType.BLIND_SWAP,
                source_card=state.drawn_card,
                target_player_id=0,
                target_card_index=0,
                second_target_player_id=0,
                second_target_card_index=1,
            ),
        )
