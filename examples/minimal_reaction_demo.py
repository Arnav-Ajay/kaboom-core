# ecamples/minimal_reaction_demo.py
from kaboom.cards import Card, Rank, Suit
from kaboom.players import Player
from kaboom.game import GameState
from kaboom.game import apply_action
from kaboom.game import Draw, Discard, Replace
from kaboom.game import react_discard_own_cards

def _shuffle_deck(deck):
    import random
    random.shuffle(deck)
    return deck

def _create_deck():
    deck = []
    for suit in Suit:
        for rank in Rank:
            deck.append(Card(rank, suit))
    return _shuffle_deck(deck)

def _create_players(num_players):
    return [Player(id=i, name=f"P{i+1}") for i in range(num_players)]

def _assign_hands(players, deck, hand_size=4):
    for player in players:
        player.hand = []

    for _ in range(hand_size):
        for player in players:
            player.hand.append(deck.pop())

def game_start():

    players = _create_players(2)
    deck = _create_deck()
    _assign_hands(players, deck)

    state = GameState(
        players=players,
        deck=deck,
        discard_pile=[],
        current_player_index=0,
        round_number=1,
        drawn_card = None,
        reaction_rank = None,
        reaction_initiator = None,
        reaction_open = False,

        kaboom_called_by = None,
        instant_winner = None
    )

    return state

def _see_cards_at_start(state: GameState):
    # each player can see 2 of their own cards
    for player in state.players:
        # print(f"{player.name} sees: {player.hand[:2]}")
        player.remember(player.id, 0, player.hand[0])
        player.remember(player.id, 1, player.hand[1])

def simulate_turn(state: GameState):
    apply_action(state, Draw(actor_id=state.current_player().id))
    memory = state.current_player().memory
    print(f"{state.current_player().name} sees drawn card: {state.drawn_card}")
    print("Current Player's Memory: ", memory)
    curret_drawn_card = state.drawn_card
    print("\nCurrent Drwan Card from State :", curret_drawn_card)

    if memory:
        for (p, i), c in memory.items():
            if state.drawn_card.score_value < c.score_value:
                print(f"Player Replaces {state.drawn_card} with {c}")
                apply_action(state, Replace(actor_id=state.current_player().id, target_index=i))
                
                state.round_number +=1
                return state

    apply_action(state, Discard(actor_id=state.current_player().id))

    state.round_number +=1
    return state



def main():
    state = game_start()
    _see_cards_at_start(state)

    print("Initial state: \n\tNumber of players:", len(state.players))
    print("\tDeck size:", len(state.deck))
    print("\tPlayer 1 hand:", state.players[0].hand)
    print("\tPlayer 2 hand:", state.players[1].hand)
    print("\tRound Numer:", state.round_number)
    print("\tDiscard pile size:", len(state.discard_pile) if state.discard_pile else "Empty")

    print("\nSimulating turn...\n")
    new_state = simulate_turn(state)
    print("New state: \n\tNumber of players:", len(new_state.players))
    print("\tDeck size:", len(new_state.deck))
    print("\tPlayer 1 hand:", new_state.players[0].hand)
    print("\tPlayer 2 hand:", new_state.players[1].hand)
    print("\tRound Numer:", new_state.round_number)
    print("\tDiscard pile size:", len(new_state.discard_pile) if new_state.discard_pile else "Empty")

    print("Player 1 memory:", new_state.players[0].memory)

if __name__ == "__main__":
    main()