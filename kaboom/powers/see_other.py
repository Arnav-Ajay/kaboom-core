from kaboom.game.actions import UsePower
from kaboom.powers.base import Power
from kaboom.cards.card import Rank
from kaboom.game.game_state import GameState


class SeeOtherPower(Power):
    VALID_RANKS = {Rank.NINE, Rank.TEN}

    def can_apply(self, state, actor_id, card):
        return card.rank in self.VALID_RANKS

    def apply(self, state: GameState, action: UsePower) -> None:
        card = state.players[action.target_player_id].hand[
            action.target_card_index
        ]
        state.players[action.actor_id].remember(
            action.target_player_id,
            action.target_card_index,
            card,
        )

