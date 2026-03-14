# kaboom/engine.py

from dataclasses import dataclass

from ..cards.card import Card
from ..exceptions import InvariantViolationError
from ..players.player import Player
from ..powers.types import PowerType
from .actions import (
    OpeningPeek,
    Draw,
    Discard,
    Replace,
    CallKaboom,
    UsePower,
    CloseReaction,
    ResolvePendingPower,
)
from .game_state import GameState
from .phases import GamePhase
from .reaction import react_discard_own_card, react_discard_other_card
from .results import ActionResult, ReactionResult
from .turn import apply_action

MAX_PLAYERS = 6
MAX_HAND_SIZE = 6
DEFAULT_PLAYERS = 4
DEFAULT_HAND_SIZE = 4


@dataclass
class GameEngine:
    game_id: int
    num_players: int = DEFAULT_PLAYERS
    hand_size: int = DEFAULT_HAND_SIZE
    state: GameState = None

    def __post_init__(self):
        if self.num_players > 6:
            raise InvariantViolationError(
                f"Max Players Allowed: {MAX_PLAYERS}. You added {self.num_players}. Ideal number 4"
            )

        if self.hand_size > 6:
            raise InvariantViolationError(
                f"Max Hand Allowed: {MAX_HAND_SIZE}. You added {self.hand_size}. Ideal number 4"
            )

        self.state = GameState.new_game(self.num_players, self.hand_size)

    # --------- convenience helpers ---------
    def perform_opening_peek(
        self,
        player_id: int,
        card_indices: tuple[int, ...] | list[int],
    ) -> list[ActionResult]:
        """Apply one player's mandatory opening peek to explicitly chosen indices."""
        return apply_action(
            self.state,
            OpeningPeek(actor_id=player_id, card_indices=tuple(card_indices)),
        )

    def see_cards_at_start(
        self,
        peek_map: dict[int, tuple[int, ...] | list[int]] | None = None,
    ) -> list[ActionResult]:
        """
        Convenience helper for simulations that applies all opening peeks once.

        Callers must provide explicit chosen indices for each player.
        """
        if peek_map is None:
            raise InvariantViolationError(
                "Opening peek requires explicit indices. Use perform_opening_peek() "
                "or pass a player-to-indices mapping."
            )

        results: list[ActionResult] = []
        while not self.state.opening_peek_complete:
            player_id = self.state.current_player().id
            if player_id not in peek_map:
                raise InvariantViolationError(f"Missing opening peek indices for player {player_id}.")
            results.extend(self.perform_opening_peek(player_id, peek_map[player_id]))
        return results

    def save_to_memory(self, player: Player, player_id: int, card_idx: int, card: Card) -> None:
        """
        Adds card to memory
        Helper function for AI Agents and Simulations.
        No real implication on real game.
        """
        player.remember(player_id, card_idx, card)

    def draw_card(self, player_id: int) -> list[ActionResult]:
        """Draw a card from deck."""
        return apply_action(self.state, Draw(actor_id=player_id))

    def replace_card(self, player_id: int, card_idx: int) -> list[ActionResult]:
        """Replace the drawn card with one of the cards in hand."""
        return apply_action(self.state, Replace(actor_id=player_id, target_index=card_idx))

    def discard_card(self, player_id: int) -> list[ActionResult]:
        """Discard the drawn card to discard pile."""
        return apply_action(self.state, Discard(actor_id=player_id))

    def call_kaboom(self, player_id: int) -> list[ActionResult]:
        """
        After round 1, any player can call Kaboom.
        The caller becomes inactive and revealed, and the table completes one final round.
        """
        return apply_action(self.state, CallKaboom(actor_id=player_id))

    def use_power(
        self,
        power_name: PowerType,
        player: Player | int,
        target_player_id: int | None,
        target_card_index: int | None,
        second_target_player_id: int | None = None,
        second_target_card_index: int | None = None,
    ) -> list[ActionResult]:
        """
        Use a drawn power card by discarding it first and claiming the pending power.
        """
        actor_id = player.id if isinstance(player, Player) else player
        return apply_action(
            self.state,
            UsePower(
                actor_id=actor_id,
                power_name=power_name,
                source_card=self.state.drawn_card,
                target_player_id=target_player_id,
                target_card_index=target_card_index,
                second_target_player_id=second_target_player_id,
                second_target_card_index=second_target_card_index,
            ),
        )

    # ==================== Reaction Actions ====================
    def react_discard_own_card(self, actor_id: int, card_index: int) -> ReactionResult:
        """React by discarding a matching card from own hand."""
        return react_discard_own_card(self.state, actor_id, card_index)

    def react_discard_other_card(
        self,
        actor_id: int,
        target_player_id: int,
        target_card_index: int,
        give_card_index: int,
    ) -> ReactionResult:
        """React by discarding a matching card from another player's hand and giving them a card."""
        return react_discard_other_card(
            self.state,
            actor_id,
            target_player_id,
            target_card_index,
            give_card_index,
        )

    def close_reaction(self) -> list[ActionResult]:
        """Close the reaction window without reacting."""
        current_player = self.state.current_player()
        return apply_action(self.state, CloseReaction(actor_id=current_player.id))

    def resolve_pending_power(self, actor_id: int) -> list[ActionResult]:
        """Resolve a power that was discarded and claimed before any reaction."""
        return apply_action(self.state, ResolvePendingPower(actor_id=actor_id))

    # ---- helpers mirroring GameState's reaction utilities ----
    def reactable_players(self, exclude_initiator: bool = False):
        """Return list of players eligible to react."""
        return self.state.reactable_players(exclude_initiator)

    def reaction_order(self):
        """Return ordered list of players for processing reactions."""
        return self.state.reaction_order()

    def is_game_over(self) -> bool:
        return self.state.phase == GamePhase.GAME_OVER

    def get_scores(self) -> dict[int, int]:
        return {player.id: player.total_score() for player in self.state.players}

    def get_winner(self):
        if not self.is_game_over():
            return None

        if self.state.instant_winner is not None:
            return self.state.instant_winner

        scores = self.get_scores()
        min_score = min(scores.values())
        winners = [player_id for player_id, score in scores.items() if score == min_score]
        return winners[0] if len(winners) == 1 else winners
