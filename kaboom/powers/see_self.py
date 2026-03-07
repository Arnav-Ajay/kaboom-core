# kaboom/powers/see_other.py
from kaboom.game.actions import UsePower
from kaboom.powers.base import Power
from kaboom.cards.card import Rank
from kaboom.game.game_state import GameState


class SeeSelfPower(Power):
    VALID_RANKS = {Rank.SEVEN, Rank.EIGHT}

    def can_apply(self, state, actor_id, card):
        return card.rank in self.VALID_RANKS

    def apply(self, state: GameState, action: UsePower) -> None:
        idx = action.target_card_index
        player = state.resolve_player(action.actor_id)
        card = player.hand[idx]
        player.remember(action.actor_id, idx, card)

