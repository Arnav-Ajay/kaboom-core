# kaboom/game/game_state.py
from __future__ import annotations
import random

from dataclasses import dataclass, field
from typing import List, Optional

from ..cards.card import Card, Rank, Suit
from ..players.player import Player
from ..exceptions import InvalidActionError
from .phases import GamePhase
from .actions import UsePower

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
    opening_peek_complete: bool = True
    opening_peek_pending_player_ids: list[int] = field(default_factory=list)

    # Drawn card awaiting action
    drawn_card: Optional[Card] = None
    pending_power_action: Optional[UsePower] = None

    # Reaction state
    reaction_rank: Optional[str] = None
    reaction_initiator: Optional[int] = None
    reaction_open: bool = False
    reaction_wrong_guess_counts: dict[int, int] = field(default_factory=dict)
    max_wrong_reaction_attempts_per_player: int = 1

    # Kaboom
    kaboom_called_by: Optional[int] = None
    instant_winner: Optional[int] = None
    pending_game_over_after_reaction: bool = False

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
                if self.reaction_open:
                    self.pending_game_over_after_reaction = True
                    continue
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

    # ---------- memory helpers ----------
    def forget_position_everywhere(self, player_id: int, card_index: int) -> None:
        for player in self.players:
            player.forget_position(player_id, card_index)

    def remember_position_everywhere(self, player_id: int, card_index: int, card: Card) -> None:
        for player in self.players:
            player.remember(player_id, card_index, card)

    def shift_memories_after_removal(self, player_id: int, removed_index: int) -> None:
        """
        Update every player's memory after a card is removed from a hand.

        The removed position becomes invalid and all later indices for that hand
        shift left by one.
        """
        for player in self.players:
            new_memory = {}
            for (pid, idx), card in player.memory.items():
                if pid != player_id:
                    new_memory[(pid, idx)] = card
                elif idx < removed_index:
                    new_memory[(pid, idx)] = card
                elif idx > removed_index:
                    new_memory[(pid, idx - 1)] = card
            player.memory = new_memory

    def shift_memories_after_swap(
        self,
        first_player_id: int,
        first_card_index: int,
        second_player_id: int,
        second_card_index: int,
    ) -> None:
        """
        Move remembered positions after two cards swap locations.

        Any memory entry about one swapped slot now points at the other slot.
        """
        for player in self.players:
            new_memory = {}
            for (pid, idx), card in player.memory.items():
                if pid == first_player_id and idx == first_card_index:
                    new_memory[(second_player_id, second_card_index)] = card
                elif pid == second_player_id and idx == second_card_index:
                    new_memory[(first_player_id, first_card_index)] = card
                else:
                    new_memory[(pid, idx)] = card
            player.memory = new_memory

    def remember_replaced_card(self, actor_id: int, target_player_id: int, card_index: int, card: Card) -> None:
        """
        A replacement changes the hidden card at a known position.

        Everyone else's knowledge of that slot becomes stale, but the actor knows
        the new card because they drew and placed it.
        """
        self.forget_position_everywhere(target_player_id, card_index)
        self.resolve_player(actor_id).remember(target_player_id, card_index, card)

    def clear_pending_power(self) -> Optional[UsePower]:
        pending = self.pending_power_action
        self.pending_power_action = None
        return pending

    def open_reaction(self, rank: str, initiator_id: int) -> None:
        self.reaction_rank = rank
        self.reaction_initiator = initiator_id
        self.reaction_open = True
        self.reaction_wrong_guess_counts = {}
        self.phase = GamePhase.REACTION

    def can_attempt_reaction(self, actor_id: int) -> bool:
        return self.reaction_wrong_guess_counts.get(actor_id, 0) < self.max_wrong_reaction_attempts_per_player

    def record_wrong_reaction_attempt(self, actor_id: int) -> int:
        count = self.reaction_wrong_guess_counts.get(actor_id, 0) + 1
        self.reaction_wrong_guess_counts[actor_id] = count
        return count

    def required_opening_peek_count(self, player_id: int) -> int:
        player = self.resolve_player(player_id)
        return min(2, len(player.hand))

    def apply_opening_peek(self, player_id: int, card_indices: tuple[int, ...]) -> None:
        """
        Apply a player's one-time opening peek to explicitly chosen hand slots.
        """
        if self.opening_peek_complete:
            raise InvalidActionError("Opening peek has already been completed.")
        if self.phase != GamePhase.OPENING_PEEK:
            raise InvalidActionError("Opening peek is only available during setup.")

        current = self.current_player()
        if current.id != player_id:
            raise InvalidActionError("It is not this player's opening peek.")

        expected = self.required_opening_peek_count(player_id)
        normalized = tuple(card_indices)

        if len(normalized) != expected:
            raise InvalidActionError(f"Opening peek requires exactly {expected} card indices.")
        if len(set(normalized)) != len(normalized):
            raise InvalidActionError("Opening peek indices must be distinct.")

        player = self.resolve_player(player_id)
        for index in normalized:
            if index < 0 or index >= len(player.hand):
                raise InvalidActionError("card_index out of range.")

        for index in normalized:
            player.remember(player.id, index, player.hand[index])

    def advance_opening_peek(self) -> None:
        """
        Advance setup to the next player's opening peek, or start round 1.
        """
        if self.opening_peek_complete:
            raise InvalidActionError("Opening peek has already been completed.")

        current_player_id = self.current_player().id
        if not self.opening_peek_pending_player_ids:
            raise InvalidActionError("No opening peek players remain.")
        if self.opening_peek_pending_player_ids[0] != current_player_id:
            raise InvalidActionError("Opening peek order is out of sync.")

        self.opening_peek_pending_player_ids.pop(0)
        if not self.opening_peek_pending_player_ids:
            self.opening_peek_complete = True
            self.phase = GamePhase.TURN_DRAW
            self.current_player_index = 0
            return

        next_player_id = self.opening_peek_pending_player_ids[0]
        for index, player in enumerate(self.players):
            if player.id == next_player_id:
                self.current_player_index = index
                return
        raise InvalidActionError("Opening peek player order contains an unknown player.")

    # ---------- reaction helpers ----------
    def reactable_players(self, exclude_initiator: bool = False) -> list[Player]:
        """
        Return the list of players who are eligible to react during an open
        reaction window. By default the initiator is included because they may
        now compete for the same discard event. Callers may still exclude the
        initiator explicitly when needed.
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

        return cls(
            players=players,
            deck=deck,
            phase=GamePhase.OPENING_PEEK,
            current_player_index=0,
            round_number=1,
            opening_peek_complete=False,
            opening_peek_pending_player_ids=[player.id for player in players],
        )
