from kaboom.game.engine import GameEngine
from kaboom.cards.card import Card
from kaboom.game.phases import GamePhase

def test_start_game():
    engine = GameEngine(game_id=0, num_players=2, hand_size=4)

    state = engine.state
    player = engine.state.current_player()

    assert player.id == state.current_player_index
    assert state.round_number == 1
    assert len(state.players) == 2
    assert len(state.deck) == 44
    assert len(state.discard_pile) == 0
    assert len(state.players[0].memory) == 0
    assert len(state.players[1].memory) == 0

def test_initial_view_cards():
    engine = GameEngine(game_id=0, num_players=2, hand_size=4)
    players = engine.state.players

    for p in players:
        for i, c in enumerate(p.hand[:2]):
            p.remember(p.id, i, c)

    assert len(engine.state.players[0].memory) == 2
    assert len(engine.state.players[1].memory) == 2

def test_game_actions():
    engine = GameEngine(game_id=0, num_players=2, hand_size=4)
    state = engine.state
    players = engine.state.players
    c_player = state.current_player()
    assert c_player.id == state.current_player_index

    result = engine.draw_card(engine.state.current_player_index)
    assert c_player.id == state.current_player_index
    assert type((result[0].card)) == Card

    print(result[0].card)
    
    assert len(engine.state.deck) == 43 
    assert engine.state.drawn_card is not None 
    assert len(engine.state.discard_pile) == 0

    engine.replace_card(engine.state.current_player_index, 2)
    player = engine.state.current_player()
    player.remember(player.id, 2, result[0].card)
    print(player.memory)
    assert len(engine.state.deck) == 43
    assert len(player.hand) == 4
    assert engine.state.drawn_card is None 
    assert len(engine.state.discard_pile) == 1
    # assert len(engine.state.players[0].memory) == 1


def test_power_use_turn_transition():
    # Ensure using a power advances turn and resets phase to TURN_DRAW
    engine = GameEngine(game_id=0, num_players=2, hand_size=4)
    state = engine.state
    # draw a power card by forcing state
    # we create a dummy power card (7 of hearts) and set as drawn
    from kaboom.cards.card import Card, Rank, Suit
    power_card = Card(rank=Rank('7'), suit=Suit.HEARTS)
    state.drawn_card = power_card
    state.phase = GamePhase.TURN_RESOLVE
    current_index = state.current_player_index

    # use see_self power on own card index 0
    # see_self does not require a target player id, pass None
    engine.use_power('see_self', state.current_player(), None, 0)
    # after action, turn should advance to next player (index 1)
    assert state.current_player_index == (current_index + 1) % 2
    assert state.phase == GamePhase.TURN_DRAW
    assert state.drawn_card is None

    # def call_kaboom(self, player_id)

    # def use_power(self, power_name, player_id, player_card_idx, target_player_id, target_player_card_idx)
# test_game_actions()