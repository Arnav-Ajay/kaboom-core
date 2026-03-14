# kaboom/powers/blind_swap.py
from kaboom.game.actions import UsePower
from kaboom.powers.base import Power
from kaboom.cards.card import Rank
from kaboom.game.game_state import GameState


class BlindSwapPower(Power):
    VALID_RANKS = {Rank.J, Rank.Q}

    def can_apply(self, state, actor_id, card):
        return card.rank in self.VALID_RANKS

    def apply(self, state: GameState, action: UsePower) -> None:

        p1 = state.resolve_player(action.target_player_id)
        p2 = state.resolve_player(action.second_target_player_id)

        c1 = p1.hand[action.target_card_index]
        c2 = p2.hand[action.second_target_card_index]

        # handle hand shift 
        p1.hand[action.target_card_index], p2.hand[
            action.second_target_card_index
        ] = c2, c1
        state.shift_memories_after_swap(
            p1.id,
            action.target_card_index,
            p2.id,
            action.second_target_card_index,
        )
