# kaboom/powers/see_and_swap.py
from kaboom.powers.base import Power
from kaboom.cards.card import Rank, Suit
from kaboom.game.game_state import GameState
from kaboom.game.actions import UsePower


class SeeAndSwapPower(Power):
    def can_apply(self, state, actor_id, card):
        return card.rank == Rank.K and card.suit in {
            Suit.SPADES,
            Suit.CLUBS,
        }

    def apply(self, state: GameState, action: UsePower) -> None:
        p1 = state.resolve_player(action.target_player_id)
        p2 = state.resolve_player(action.second_target_player_id)

        c1 = p1.hand[action.target_card_index]
        c2 = p2.hand[action.second_target_card_index]

        state.resolve_player(action.actor_id).remember(
            action.target_player_id, action.target_card_index, c2
        )
        state.resolve_player(action.actor_id).remember(
            action.second_target_player_id,
            action.second_target_card_index,
            c1,
        )

        p1.hand[action.target_card_index], p2.hand[
            action.second_target_card_index
        ] = c2, c1

        # update memory for all players: cards have swapped between p1 and p2
        def _shift_mem(player_list, id_a, idx_a, id_b, idx_b):
            # rebuild memory mapping to reflect swapped positions
            for pl in player_list:
                new_mem = {}
                for (pid, ci), card in pl.memory.items():
                    if pid == id_a and ci == idx_a:
                        new_mem[(id_b, idx_b)] = card
                    elif pid == id_b and ci == idx_b:
                        new_mem[(id_a, idx_a)] = card
                    else:
                        new_mem[(pid, ci)] = card
                pl.memory = new_mem
        _shift_mem(state.players, p1.id, action.target_card_index, p2.id, action.second_target_card_index)

