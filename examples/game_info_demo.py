from kaboom import GameEngine, get_valid_actions

SUIT_MAP = {
    "♠": "S",
    "♥": "H",
    "♦": "D",
    "♣": "C",
}


def main() -> None:
    engine = GameEngine(game_id=0, num_players=2, hand_size=4)
    state = engine.state

    # Example setup choice: each player peeks at their first two slots.
    engine.see_cards_at_start(
        {
            0: (0, 1),
            1: (0, 1),
        }
    )

    print("Kaboom game info demo")
    print(f"Phase: {state.phase.value}")
    print(f"Round: {state.round_number}")
    print(f"Deck size: {len(state.deck)}")
    print("")

    for player in state.players:
        memories = ", ".join(
            f"P{target_player_id}[{card_index}]="
            f"{card.rank.value}{SUIT_MAP.get(card.suit.value, card.suit.value)}"
            for (target_player_id, card_index), card in sorted(player.memory.items())
        )
        print(
            f"P{player.id} {player.name} | cards={len(player.hand)} | "
            f"score={player.total_score()} | memory=[{memories}]"
        )

    print("")
    print("Legal actions:")
    for action in get_valid_actions(state):
        print(f"  - {action}")


if __name__ == "__main__":
    main()
