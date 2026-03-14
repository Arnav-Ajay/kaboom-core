from kaboom.game.engine import GameEngine
from kaboom.cards.card import Card, Rank, Suit
from kaboom.exceptions import InvalidActionError
from kaboom.game.phases import GamePhase
from kaboom.game.actions import Draw, Discard
from kaboom.game.turn import apply_action
from kaboom.powers.types import PowerType
import pytest

def test_start_game():
    engine = GameEngine(game_id=0, num_players=2, hand_size=4)

    state = engine.state
    player = engine.state.current_player()

    assert player.id == state.current_player_index
    assert state.round_number == 1
    assert len(state.players) == 2
    assert len(state.deck) == 44
    assert len(state.discard_pile) == 0
    assert state.phase == GamePhase.OPENING_PEEK
    assert len(state.players[0].memory) == 0
    assert len(state.players[1].memory) == 0

def test_initial_view_cards():
    engine = GameEngine(game_id=0, num_players=2, hand_size=4)

    engine.perform_opening_peek(0, (1, 3))
    engine.perform_opening_peek(1, (0, 2))

    assert len(engine.state.players[0].memory) == 2
    assert len(engine.state.players[1].memory) == 2
    assert engine.state.phase == GamePhase.TURN_DRAW

def test_opening_peek_is_once_only_and_player_chosen():
    engine = GameEngine(game_id=0, num_players=2, hand_size=4)

    first = engine.perform_opening_peek(0, (1, 3))[0]
    second = engine.perform_opening_peek(1, (0, 2))[0]

    assert first.action == "opening_peek"
    assert first.peeked_indices == (1, 3)
    assert first.phase_before == GamePhase.OPENING_PEEK.value
    assert first.phase_after == GamePhase.OPENING_PEEK.value
    assert second.phase_after == GamePhase.TURN_DRAW.value
    assert set(engine.state.players[0].memory.keys()) == {(0, 1), (0, 3)}
    assert set(engine.state.players[1].memory.keys()) == {(1, 0), (1, 2)}
    with pytest.raises(InvalidActionError):
        engine.perform_opening_peek(0, (0, 2))

def test_game_actions():
    engine = GameEngine(game_id=0, num_players=2, hand_size=4)
    engine.perform_opening_peek(0, (0, 1))
    engine.perform_opening_peek(1, (0, 1))
    state = engine.state
    c_player = state.current_player()
    assert c_player.id == state.current_player_index

    result = engine.draw_card(engine.state.current_player_index)
    assert c_player.id == state.current_player_index
    assert isinstance(result[0].card, Card)
    
    assert len(engine.state.deck) == 43 
    assert engine.state.drawn_card is not None 
    assert len(engine.state.discard_pile) == 0

    engine.replace_card(engine.state.current_player_index, 2)
    player = engine.state.resolve_player(c_player.id)
    assert len(engine.state.deck) == 43
    assert len(player.hand) == 4
    assert engine.state.drawn_card is None 
    assert len(engine.state.discard_pile) == 1
    assert (player.id, 2) in player.memory


def test_power_use_turn_transition():
    # Using a power now discards the card first, opens contention, and only
    # resolves when the pending power is explicitly claimed.
    engine = GameEngine(game_id=0, num_players=2, hand_size=4)
    state = engine.state
    engine.perform_opening_peek(0, (0, 1))
    engine.perform_opening_peek(1, (0, 1))
    power_card = Card(rank=Rank('7'), suit=Suit.HEARTS)
    state.drawn_card = power_card
    state.phase = GamePhase.TURN_RESOLVE
    current_index = state.current_player_index

    results = engine.use_power(PowerType.SEE_SELF, state.current_player(), None, 0)
    assert results[0].action == "discard_for_power"
    assert state.pending_power_action is not None
    assert state.phase == GamePhase.REACTION
    assert state.current_player_index == (current_index + 1) % 2
    assert state.drawn_card is None

    results = engine.resolve_pending_power(actor_id=0)
    assert results[0].action == "use_power"
    assert state.phase == GamePhase.TURN_DRAW
    assert state.pending_power_action is None


def test_close_reaction_wrapper_returns_action_result():
    engine = GameEngine(game_id=0, num_players=2, hand_size=2)
    state = engine.state
    engine.perform_opening_peek(0, (0, 1))
    engine.perform_opening_peek(1, (0, 1))

    apply_action(state, Draw(actor_id=0))
    apply_action(state, Discard(actor_id=0))

    results = engine.close_reaction()

    assert len(results) == 1
    assert results[0].action == "close_reaction"
    assert results[0].phase_before == GamePhase.REACTION.value
    assert results[0].phase_after == GamePhase.TURN_DRAW.value
    assert state.phase == GamePhase.TURN_DRAW
