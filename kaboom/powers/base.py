from abc import ABC, abstractmethod
from kaboom.game.game_state import GameState
from kaboom.game.actions import UsePower


class Power(ABC):
    @abstractmethod
    def can_apply(
        self,
        state: GameState,
        actor_id: int,
        card,
    ) -> bool:
        ...

    @abstractmethod
    def apply(
        self,
        state: GameState,
        action: UsePower,
    ) -> None:
        ...
