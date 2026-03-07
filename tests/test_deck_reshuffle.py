def test_deck_reshuffles_when_empty(simple_game_state):

    state = simple_game_state

    # empty the deck
    state.deck = []

    # put cards in discard
    state.discard_pile = state.players[0].hand[:]

    state.ensure_deck()

    assert len(state.deck) > 0
    assert len(state.discard_pile) == 1