from kaboom.game.game_state import GameState
from kaboom.game.engine import GameEngine


def test_state_new_game_constructor():
    state = GameState.new_game(3, 2)
    assert len(state.players) == 3
    for p in state.players:
        assert len(p.hand) == 2
    assert len(state.deck) == 52 - (3 * 2)


def test_engine_initialization_defaults():
    engine = GameEngine(game_id=1)
    assert engine.num_players == 4
    assert engine.hand_size == 4
    assert engine.state.current_player_index == 0
    assert len(engine.state.players) == 4

def test_engine_reaction_helpers(simple_game_state):
    engine = GameEngine(game_id=42)
    # override the state for determinism
    engine.state = simple_game_state

    # simulate a player drawing and discarding to open a reaction window
    engine.draw_card(0)
    engine.discard_card(0)
    assert engine.state.reaction_open

    # have the other player react using the wrapper
    res = engine.react_discard_own_card(actor_id=1, card_index=0)
    assert isinstance(res.success, bool)
    # after reacting window should be closed
    assert not engine.state.reaction_open

    # verify helper passthroughs
    assert engine.reactable_players() == engine.state.reactable_players()
    # reaction_order should rotate starting after initiator (0) -> next player is 1
    engine.state.reaction_initiator = 0
    ids = [p.id for p in engine.reaction_order()]
    assert ids[0] == 1
