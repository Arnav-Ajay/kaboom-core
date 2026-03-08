# kaboom/engine.py

from dataclasses import dataclass
from typing import List
from ..cards.card import Card
from ..players.player import Player
from .game_state import GameState
from .turn import apply_action
from .actions import Draw, Discard, Replace, CallKaboom, UsePower
from .reaction import (
    react_discard_own_card,
    react_discard_other_card,
    react_discard_own_cards,
    react_discard_other_cards,
    close_reaction,
)
from ..powers.types import PowerType
from .phases import GamePhase
from .results import ActionResult
from ..exceptions import InvariantViolationError

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
            raise InvariantViolationError(f"Max Players Allowed: {MAX_PLAYERS}. You added {self.num_players}. Ideal number 4")
        
        if self.hand_size > 6:
            raise InvariantViolationError(f"Max Hand Allowed: {MAX_HAND_SIZE}. You added {self.hand_size}. Ideal number 4")
        # self.state = new_game(self.num_players, self.hand_size)
        self.state = GameState.new_game(self.num_players, self.hand_size)

    # --------- convenience helpers ---------
    def see_cards_at_start(self) -> None:
        """Each player remembers their first two cards.

        This mirrors the vision rule at game start: players look at any two cards
        in their own hand and then put them back face‑down. We update the memory
        so AI/simulation code can refer to known cards.
        """
        for player in self.state.players:
            for i, card in enumerate(player.hand[:2]):
                player.remember(player.id, i, card)

    def save_to_memory(self, player: Player, player_id: int, card_idx: int, card: Card) -> None:
        """
        Adds card to memory
        Helper function for AI Agents and Simulations.
        No real implication on real game.
        """
        player.remember(player_id, card_idx, card)

    def draw_card(self, player_id: int) -> ActionResult:
        """ Draw a card from deck """
        return apply_action(self.state, Draw(actor_id=player_id))

    def replace_card(self, player_id: int, card_idx: int) -> ActionResult:
        """ Replace the drawn card from one of the card at hand """
        return apply_action(self.state, Replace(actor_id=player_id, target_index=card_idx))

    def discard_card(self, player_id: int) -> ActionResult:
        """ Discard the drawn card to discard pile """
        return apply_action(self.state, Discard(actor_id=player_id))

    def call_kaboom(self, player_id: int) -> ActionResult:
        """ 
        after round 1, any player can call 'Kaboom'
        after which the player's cards will be revealed and becomes inactive.
        all other players play 1 more turn
        game ends with it's the player's turn again.
        """
        return apply_action(self.state, CallKaboom(actor_id=player_id))

    def use_power(self, power_name: PowerType, player: Player, target_player_id: int,
                  target_card_index: int, second_target_player_id: int = None,
                  second_target_card_index: int = None) -> ActionResult:
        """
        Use Power for Special Cards:
        power_name: 'see_self' (on 7, 8), 'see_other' (on 9, 10), 'blind_swap' (J, Q), 'see_and_swap' (Black K - spades and clubs)
        player: current player using the power
        target_player_id: id for player 1
        target_card_index: index for card of player 1
        second_target_player_id: id for player 2 (only for 'blind_swap' and 'see_and_swap')
        second_target_card_index: index for card of player 2 (only for 'blind_swap' and 'see_and_swap')

        """
        return apply_action(self.state, 
                            UsePower(actor_id=player.id, power_name=power_name, 
                                     source_card=self.state.drawn_card, target_player_id=target_player_id,
                                     target_card_index=target_card_index,
                                     second_target_player_id=second_target_player_id,
                                     second_target_card_index=second_target_card_index)
                                     )

    # ==================== Reaction Actions ====================
    
    def react_discard_own_card(self, actor_id: int, card_index: int):
        """React by discarding a matching card from own hand."""
        return react_discard_own_card(self.state, actor_id, card_index)
    
    def react_discard_other_card(self, actor_id: int, target_player_id: int, 
                                 target_card_index: int, give_card_index: int):
        """React by discarding a matching card from another player's hand and giving them a card."""
        return react_discard_other_card(self.state, actor_id, target_player_id, 
                                       target_card_index, give_card_index)
    
    def react_discard_own_cards(self, actor_id: int, card_indices: List[int]):
        """React by discarding multiple matching cards from own hand."""
        return react_discard_own_cards(self.state, actor_id, card_indices)
    
    def react_discard_other_cards(self, actor_id: int, target_player_id: int,
                                  target_card_indices: List[int], give_card_indices: List[int]):
        """React by discarding multiple matching cards from another player's hand and giving them cards."""
        return react_discard_other_cards(self.state, actor_id, target_player_id,
                                        target_card_indices, give_card_indices)
    
    def close_reaction(self):
        """Close the reaction window without reacting."""
        close_reaction(self.state)

    # ---- helpers mirroring GameState's reaction utilities ----
    def reactable_players(self, exclude_initiator: bool = True):
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
