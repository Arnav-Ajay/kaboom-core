# kaboom/game/results.py
from dataclasses import dataclass
from typing import Optional
from ..cards.card import Card

@dataclass(slots=True)
class ActionResult:
    action: str
    actor_id: int
    card: Card | None = None
    reaction_opened: bool = False
    reaction_closed: bool = False
    instant_winner: Optional[int] = None

@dataclass(slots=True)
class ReactionResult:
    success: bool
    penalty_applied: bool = False
    instant_win_player: Optional[int] = None