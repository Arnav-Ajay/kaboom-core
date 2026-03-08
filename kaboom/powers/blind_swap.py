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

        # handle memory shift
        # if any of the 2 cards changed also contain in any player's memory - that memory location need to be updated.
        # After swap, a card that was at index A on p1 now resides at index A on p2 and
        # vice‑versa.  For every player with a memory entry pointing to one of those
        # positions we must relocate it to the new owner/index.
        def _adjust_memory_for_swap(player_list, p1_id, idx1, p2_id, idx2):
            # rebuild each player's memory dict with swapped keys; this avoids any
            # ordering issues during in-place modification and ensures both swapped
            # entries are preserved.
            for pl in player_list:
                new_mem = {}
                for (pid, ci), card in pl.memory.items():
                    if pid == p1_id and ci == idx1:
                        new_mem[(p2_id, idx2)] = card
                    elif pid == p2_id and ci == idx2:
                        new_mem[(p1_id, idx1)] = card
                    else:
                        new_mem[(pid, ci)] = card
                pl.memory = new_mem

        _adjust_memory_for_swap(state.players, p1.id, action.target_card_index, p2.id, action.second_target_card_index)
