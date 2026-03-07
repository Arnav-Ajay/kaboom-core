# kaboom/game/results.py
from dataclasses import dataclass
from typing import Optional

@dataclass(slots=True)
class ActionResult:
    action: str
    actor_id: int
    reaction_opened: bool = False
    reaction_closed: bool = False
    instant_winner: Optional[int] = None