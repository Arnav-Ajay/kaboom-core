import random

from kaboom import GameEngine, GamePhase, PowerType, UsePower, apply_action, get_valid_actions


def materialize_action(engine: GameEngine, action):
    if not isinstance(action, UsePower):
        return action

    state = engine.state
    actor = state.resolve_player(action.actor_id)

    if action.power_name == PowerType.SEE_SELF:
        return UsePower(
            actor_id=actor.id,
            power_name=action.power_name,
            source_card=action.source_card,
            target_card_index=0,
        )

    if action.power_name == PowerType.SEE_OTHER:
        target_player = next(player for player in state.players if player.id != actor.id)
        return UsePower(
            actor_id=actor.id,
            power_name=action.power_name,
            source_card=action.source_card,
            target_player_id=target_player.id,
            target_card_index=0,
        )

    if action.power_name in {PowerType.BLIND_SWAP, PowerType.SEE_AND_SWAP}:
        target_player = next(player for player in state.players if player.id != actor.id)
        return UsePower(
            actor_id=actor.id,
            power_name=action.power_name,
            source_card=action.source_card,
            target_player_id=actor.id,
            target_card_index=0,
            second_target_player_id=target_player.id,
            second_target_card_index=0,
        )

    return action


def main() -> None:
    rng = random.Random(42)
    engine = GameEngine(game_id=0, num_players=4, hand_size=4)
    state = engine.state

    step_limit = 200
    steps = 0

    while state.phase != GamePhase.GAME_OVER and steps < step_limit:
        current_player = state.current_player()
        if not current_player.active:
            state.advance_turn()
            continue

        actions = get_valid_actions(state)
        if not actions:
            break

        action = materialize_action(engine, rng.choice(actions))
        results = apply_action(state, action)
        print(f"step={steps} phase={state.phase.value} action={action} results={results}")
        steps += 1

    print("")
    print("Simulation finished")
    print(f"Final phase: {state.phase.value}")
    print(f"Winner: {engine.get_winner()}")
    print(f"Scores: {engine.get_scores()}")


if __name__ == "__main__":
    main()
