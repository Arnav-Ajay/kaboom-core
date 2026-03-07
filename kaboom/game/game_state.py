# kaboom/game/game_state.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from kaboom.cards.card import Card
from kaboom.players.player import Player
from kaboom.exceptions import InvalidActionError

@dataclass(slots=True)
class GameState:
    """
    Complete mutable state of a Kaboom game.
    """
    players: List[Player]
    deck: List[Card]
    discard_pile: List[Card] = field(default_factory=list)

    current_player_index: int = 0
    round_number: int = 1

    # Drawn card awaiting action
    drawn_card: Optional[Card] = None

    # Reaction state
    reaction_rank: Optional[str] = None
    reaction_initiator: Optional[int] = None
    reaction_open: bool = False

    # Kaboom
    kaboom_called_by: Optional[int] = None
    instant_winner: Optional[int] = None

    def active_players(self) -> List[Player]:
        return [p for p in self.players if p.active]

    def current_player(self) -> Player:
        return self.players[self.current_player_index]

    def advance_turn(self) -> None:
        """
        Move to next active player.
        """
        if self.kaboom_called_by is not None:
            return

        n = len(self.players)
        for _ in range(n):
            self.current_player_index = (self.current_player_index + 1) % n
            if self.players[self.current_player_index].active:
                break

        if self.current_player_index == 0:
            self.round_number += 1

    def top_discard(self) -> Optional[Card]:
        return self.discard_pile[-1] if self.discard_pile else None
    
    def resolve_player(self, player_id: int) -> Player:
        for p in self.players:
            if p.id == player_id:
                return p
        raise InvalidActionError("Unknown player_id")
