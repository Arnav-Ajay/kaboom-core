import random

from kaboom import GameEngine, GamePhase, apply_action, get_valid_actions

engine = GameEngine(game_id=0, num_players=2, hand_size=4)
state = engine.state

while state.phase != GamePhase.GAME_OVER:

    player = state.current_player()

    # skip inactive players (kaboom caller)
    if not player.active:
        state.advance_turn()
        continue

    actions = get_valid_actions(state)

    if not actions:
        break
    
    # Skip powers in simple random simulation
    actions = [a for a in actions if a.__class__.__name__ != "UsePower"]

    if not actions:
        continue

    action = random.choice(actions)

    apply_action(state, action)