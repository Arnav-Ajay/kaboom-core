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
        actor = state.resolve_player(action.actor_id)
        target = state.resolve_player(action.target_player_id)

        actor.hand[action.target_card_index], target.hand[
            action.second_target_card_index
        ] = (
            target.hand[action.second_target_card_index],
            actor.hand[action.target_card_index],
        )

        actor.forget_all()
        target.forget_all()
