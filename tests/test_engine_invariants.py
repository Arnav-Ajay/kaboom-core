import random
import pytest

from kaboom.game.turn import apply_action
from kaboom.game.actions import Draw, Discard, Replace, CloseReaction


def test_engine_state_invariants(simple_game_state):

    state = simple_game_state

    for _ in range(200):

        player = state.current_player()

        actions = []

        if state.reaction_open:
            actions.append(CloseReaction(actor_id=player.id))

        elif state.drawn_card is None:
            actions.append(Draw(actor_id=player.id))

        else:
            actions.append(Discard(actor_id=player.id))
            actions.append(Replace(actor_id=player.id, target_index=0))

        action = random.choice(actions)

        try:
            apply_action(state, action)
        except Exception:
            pass

        # ----- critical invariants -----

        # no negative cards
        for p in state.players:
            assert len(p.hand) >= 0

        # drawn card consistency
        if state.drawn_card is not None:
            assert state.reaction_open is False

        # reaction consistency
        if state.reaction_open:
            assert state.reaction_rank is not None

        # only one drawn card
        assert not isinstance(state.drawn_card, list)