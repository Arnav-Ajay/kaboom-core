# kaboom/game/actions.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from kaboom.cards.card import Card

class Action(Protocol):
    """
    Marker protocol for all turn actions.
    """
    actor_id: int

@dataclass(frozen=True, slots=True)
class Draw(Action):
    actor_id: int

@dataclass(frozen=True, slots=True)
class Discard(Action):
    actor_id: int

@dataclass(frozen=True, slots=True)
class Replace(Action):
    actor_id: int
    target_index: int   # index in player's hand

@dataclass(frozen=True, slots=True)
class UsePower(Action):
    actor_id: int
    power_name: str
    source_card: Card

    # Power-specific payload (indices, player ids, etc.)
    target_player_id: Optional[int] = None
    target_card_index: Optional[int] = None
    second_target_player_id: Optional[int] = None
    second_target_card_index: Optional[int] = None

@dataclass(frozen=True, slots=True)
class CallKaboom(Action):
    actor_id: int

@dataclass(frozen=True, slots=True)
class CloseReaction(Action):
    actor_id: int