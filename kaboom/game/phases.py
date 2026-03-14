# kaboom/game/phases.py
from enum import Enum

class GamePhase(str, Enum):
    OPENING_PEEK = "opening_peek"
    TURN_DRAW = "turn_draw"
    TURN_RESOLVE = "turn_resolve"
    REACTION = "reaction"
    GAME_OVER = "game_over"
