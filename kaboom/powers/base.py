# kaboom/powers/base.py
from abc import ABC, abstractmethod
from ..game.game_state import GameState
from ..game.actions import UsePower
from ..cards.card import Card


class Power(ABC):
    """
    Base class for all power card behaviours.

    A power decides:
    1. Whether it can be applied for a given card.
    2. How it mutates the game state when used.
    """
    @abstractmethod
    def can_apply(self, state: GameState, actor_id: int, card: Card) -> bool:
        ...

    @abstractmethod
    def apply(self, state: GameState, action: UsePower) -> None:
        ...
