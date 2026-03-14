# kaboom/game/results.py
from dataclasses import dataclass
from typing import Optional
from ..cards.card import Card

@dataclass(slots=True)
class ActionResult:
    action: str
    actor_id: int
    card: Card | None = None
    peeked_indices: tuple[int, ...] | None = None
    power_name: str | None = None
    target_player_id: int | None = None
    target_card_index: int | None = None
    second_target_player_id: int | None = None
    second_target_card_index: int | None = None
    discarded_rank: str | None = None
    phase_before: str | None = None
    phase_after: str | None = None
    next_player_id: int | None = None
    reaction_opened: bool = False
    reaction_closed: bool = False
    pending_power_created: bool = False
    pending_power_resolved: bool = False
    pending_power_cancelled: bool = False
    instant_winner: Optional[int] = None

@dataclass(slots=True)
class ReactionResult:
    success: bool
    actor_id: int | None = None
    reaction_type: str | None = None
    revealed_card: Card | None = None
    penalty_card: Card | None = None
    wrong_guess_count: int | None = None
    wrong_guess_limit_reached: bool = False
    reaction_continues: bool = False
    target_player_id: int | None = None
    target_card_index: int | None = None
    discarded_rank: str | None = None
    phase_before: str | None = None
    phase_after: str | None = None
    next_player_id: int | None = None
    penalty_applied: bool = False
    instant_win_player: Optional[int] = None
    cancelled_pending_power: bool = False


GameResult = ActionResult | ReactionResult
