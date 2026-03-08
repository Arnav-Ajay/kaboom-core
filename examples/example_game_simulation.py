import random
import datetime
from pathlib import Path

from kaboom import GameEngine, GamePhase, apply_action, get_valid_actions

random.seed(42)

# -------------------------------------------------
# Logging Setup
# -------------------------------------------------

LOG_DIR = Path("examples/simulation_logs")
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / f"game_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"


def log(message: str):
    print(message)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")


# -------------------------------------------------
# Simulation
# -------------------------------------------------

engine = GameEngine(game_id=0, num_players=4, hand_size=4)
state = engine.state

log("====== Kaboom Simulation Start ======")
log(f"Players: {len(state.players)}")
log("")

turn_counter = 0


while state.phase != GamePhase.GAME_OVER:

    player = state.current_player()

    if not player.active:
        log(f"[SKIP] Player P{player.id} inactive -> advancing turn")
        state.advance_turn()
        continue

    turn_counter += 1

    log("----------------------------------")
    log(f"Turn #{turn_counter}")
    log(f"Round: {state.round_number}")
    log(f"Player: P{player.id}")
    log(f"Phase: {state.phase}")
    log(f"Hand: {[str(c) for c in player.hand]}")

    actions = get_valid_actions(state)

    if not actions:
        log("No valid actions. Ending simulation.")
        break

    action = random.choice(actions)

    log(f"Action chosen: {type(action).__name__}")

    try:
        results = apply_action(state, action)

        for r in results:
            log(f"Result -> {r}")

    except Exception as e:
        log(f"[ERROR] {e}")
        break


# -------------------------------------------------
# End Game Summary
# -------------------------------------------------

log("")
log("====== Game Finished ======")

scores = [p.total_score() for p in state.players]

for p in state.players:
    log(f"Player P{p.id} | Active: {p.active} | Score: {p.total_score()}")

winner = min(state.players, key=lambda p: p.total_score())

log("")
log(f"Winner: P{winner.id}")
log(f"Final Scores: {scores}")
log("")
log(f"Total Turns: {turn_counter}")
log("Log saved to: " + str(log_file))