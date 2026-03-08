# kaboom/game/game_state.py
from __future__ import annotations
import random

from dataclasses import dataclass, field
from typing import List, Optional

from ..cards.card import Card, Rank, Suit
from ..players.player import Player
from ..exceptions import InvalidActionError
from .phases import GamePhase

@dataclass(slots=True)
class GameState:
    """
    Complete mutable state of a Kaboom game.
    """
    players: List[Player]
    deck: List[Card]
    discard_pile: List[Card] = field(default_factory=list)
    phase: GamePhase = GamePhase.TURN_DRAW
    rng: random.Random = field(default_factory=random.Random)
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
        Move to next player.

        If Kaboom has been called, remaining players finish the round.
        When the turn returns to the Kaboom caller, the game ends.
        """

        n = len(self.players)

        while True:
            self.current_player_index = (self.current_player_index + 1) % n

            player = self.players[self.current_player_index]

            # If Kaboom was called and we reached the caller again → end game
            if (
                self.kaboom_called_by is not None
                and player.id == self.kaboom_called_by
            ):
                self.phase = GamePhase.GAME_OVER
                return

            # Skip inactive players (kaboom caller is inactive)
            if player.active:
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

    def ensure_deck(self) -> None:
        """
        Ensure deck has cards.
        If empty, reshuffle discard pile (except top card).
        """
        if self.deck:
            return

        if len(self.discard_pile) <= 1:
            raise InvalidActionError("No cards left to reshuffle.")

        top = self.discard_pile.pop()
        self.deck = self.discard_pile
        self.rng.shuffle(self.deck)

        self.discard_pile = [top]

    # ---------- reaction helpers ----------
    def reactable_players(self, exclude_initiator: bool = True) -> list[Player]:
        """
        Return the list of players who are eligible to react during an open
        reaction window.  By default the initiator of the reaction is excluded
        (they never react to their own discard/replace), but the caller can
        override that behavior for testing.
        """
        players = [p for p in self.players if p.active]
        if exclude_initiator and self.reaction_initiator is not None:
            players = [p for p in players if p.id != self.reaction_initiator]
        return players

    def reaction_order(self) -> list[Player]:
        """
        Return players in the order in which reaction attempts should be
        processed.  The rotation starts *after* the initiator and wraps around,
        skipping inactive players.  If no initiator is set yet, the order is the
        same as the players list.
        """
        players = self.reactable_players(exclude_initiator=False)
        if self.reaction_initiator is None:
            return players

        # find index of initiator in the players list
        ids = [p.id for p in players]
        if self.reaction_initiator not in ids:
            return players

        start = ids.index(self.reaction_initiator) + 1
        # rotate
        return players[start:] + players[:start]

    # -------- game creation convenience --------
    @classmethod
    def new_game(cls, num_players: int, hand_size: int) -> GameState:
        """Create a fresh game state with random deck and dealt hands.

        This helper centralizes the logic that previously lived in the engine
        module.  It is suitable for both the engine and external consumers.
        """
        # build full deck
        deck: list[Card] = []
        for suit in Suit:
            for rank in Rank:
                deck.append(Card(rank, suit))
        rng = random.Random()
        rng.shuffle(deck)

        # create players
        players: list[Player] = [Player(id=i, name=f"P{i+1}") for i in range(num_players)]

        # deal cards
        if len(deck) < hand_size * num_players:
            raise InvalidActionError("Not enough cards to deal hands")
        for _ in range(hand_size):
            for p in players:
                p.hand.append(deck.pop())

        return cls(players=players, deck=deck)
