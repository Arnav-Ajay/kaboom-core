# tests/test_reaction_engine.py
from kaboom.cards.card import Card, Rank, Suit
from kaboom.game.game_state import GameState
from kaboom.game.reaction import (
    react_discard_own_card,
    react_discard_other_card,
)
from kaboom.game.turn import apply_action
from kaboom.game.actions import Draw, Discard
from kaboom.game.validators import get_valid_actions
from kaboom.players.player import Player
import pytest
from kaboom.exceptions import InvalidActionError

def test_react_discard_own_card_success(simple_game_state):
    # P1 discards 5 → reaction opens
    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    result = react_discard_own_card(
        state=simple_game_state,
        actor_id=1,
        card_index=0,
    )


    assert result.success is True
    assert len(simple_game_state.resolve_player(1).hand) == 3
    assert simple_game_state.reaction_open is False


def test_react_discard_own_card_shifts_memory_indices(simple_game_state):
    player = simple_game_state.resolve_player(1)
    player.remember(1, 0, player.hand[0])
    player.remember(1, 1, player.hand[1])
    player.remember(1, 2, player.hand[2])

    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    react_discard_own_card(
        state=simple_game_state,
        actor_id=1,
        card_index=0,
    )

    assert (1, 0) in player.memory
    assert player.memory[(1, 0)].rank == Rank.K
    assert (1, 1) in player.memory
    assert player.memory[(1, 1)].rank == Rank.SIX
    assert (1, 2) not in player.memory

def test_react_wrong_match_penalty(simple_game_state):
    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    # P2 attempts wrong match
    result = react_discard_own_card(
        state=simple_game_state,
        actor_id=1,
        card_index=1,
    )


    assert result.success is False
    assert result.penalty_applied is True
    assert result.revealed_card.rank == Rank.K
    assert result.penalty_card is not None
    assert result.reaction_continues is True
    assert result.wrong_guess_count == 1
    assert result.wrong_guess_limit_reached is True
    assert result.target_player_id == 1
    assert result.target_card_index == 1
    assert len(simple_game_state.resolve_player(1).hand) == 5
    assert simple_game_state.resolve_player(0).memory[(1, 1)].rank == Rank.K
    assert simple_game_state.resolve_player(1).memory[(1, 1)].rank == Rank.K
    assert simple_game_state.reaction_open is True

def test_wrong_guess_limit_blocks_repeat_attempt_in_same_window(simple_game_state):
    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    react_discard_own_card(
        state=simple_game_state,
        actor_id=1,
        card_index=1,
    )

    actions = get_valid_actions(simple_game_state)
    assert all(
        not (action.__class__.__name__ == "ReactDiscardOwnCard" and action.actor_id == 1)
        for action in actions
    )

    with pytest.raises(InvalidActionError):
        react_discard_own_card(
            state=simple_game_state,
            actor_id=1,
            card_index=0,
        )

def test_reaction_actions_allow_wrong_guesses():
    p1 = Player(
        id=0,
        name="P1",
        hand=[Card(Rank.FIVE, Suit.SPADES), Card(Rank.NINE, Suit.HEARTS)],
    )
    p2 = Player(
        id=1,
        name="P2",
        hand=[Card(Rank.K, Suit.CLUBS), Card(Rank.SIX, Suit.DIAMONDS)],
    )
    state = GameState(
        players=[p1, p2],
        deck=[Card(Rank.TWO, Suit.CLUBS)],
    )

    apply_action(state, Draw(actor_id=0))
    apply_action(state, Discard(actor_id=0))

    actions = get_valid_actions(state)

    assert any(
        action.actor_id == 1 and action.card_index == 0
        for action in actions
        if action.__class__.__name__ == "ReactDiscardOwnCard"
    )
    assert any(
        action.actor_id == 1 and action.card_index == 1
        for action in actions
        if action.__class__.__name__ == "ReactDiscardOwnCard"
    )


def test_react_discard_other_card(simple_game_state):
    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    # P2 steals P1's 5♠
    result = react_discard_other_card(
        state=simple_game_state,
        actor_id=1,
        target_player_id=0,
        target_card_index=0,
        give_card_index=0,
    )

    assert result.success is True
    assert len(simple_game_state.resolve_player(0).hand) == 4
    assert len(simple_game_state.resolve_player(1).hand) == 3


def test_instant_win_on_zero_cards(simple_game_state):
    # Give P2 only one matching card
    simple_game_state.resolve_player(1).hand = [
        Card(Rank.FIVE, Suit.CLUBS)
    ]

    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    result = react_discard_own_card(
        state=simple_game_state,
        actor_id=1,
        card_index=0,
    )

    assert result.instant_win_player == 1
    assert simple_game_state.instant_winner == 1


def test_initiator_can_react_to_own_discard(simple_game_state):
    apply_action(simple_game_state, Draw(actor_id=0))
    apply_action(simple_game_state, Discard(actor_id=0))

    result = react_discard_own_card(
        state=simple_game_state,
        actor_id=0,
        card_index=0,
    )

    assert result.success is True
    assert len(simple_game_state.resolve_player(0).hand) == 3
