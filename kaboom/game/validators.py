# kaboom/game/validators.py
from kaboom.exceptions import InvalidActionError
from kaboom.game.game_state import GameState

def validate_turn(state: GameState, actor_id: int):
    if state.current_player().id != actor_id:
        raise InvalidActionError(f"Not this player's turn.")


def validate_index(length: int, index: int, name: str):
    if index is None:
        raise InvalidActionError(f"{name} required.")
    if index < 0 or index >= length:
        raise InvalidActionError(f"{name} out of range.")