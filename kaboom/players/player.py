# kaboom/players/player.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Tuple

from kaboom.cards.card import Card


@dataclass(slots=True)
class Player:
    """
    Represents a single player and their private state.
    """
    id: int
    name: str

    hand: List[Card] = field(default_factory=list)

    # Tracks which cards THIS player has seen
    # (player_id, card_index) → Card
    memory: Dict[Tuple[int, int], Card] = field(default_factory=dict)

    active: bool = True      # False after Kaboom call
    revealed: bool = False  # True only at final reveal

    def card_count(self) -> int:
        return len(self.hand)

    def total_score(self) -> int:
        return sum(card.score_value for card in self.hand)

    def remove_card(self, index: int) -> Card:
        return self.hand.pop(index)

    def add_card(self, card: Card) -> None:
        self.hand.append(card)

    def remember(self, player_id: int, card_index: int, card: Card) -> None:
        """
        Store knowledge gained via a power.
        """
        self.memory[(player_id, card_index)] = card

    def forget_all(self) -> None:
        """
        Used after blind swaps or Kaboom.
        """
        self.memory.clear()
