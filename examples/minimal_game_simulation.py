from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from kaboom import GameEngine, GamePhase, PowerType


@dataclass(frozen=True)
class SimulationConfig:
    num_players: int = 4
    hand_size: int = 4
    round_limit: int = 100
    random_seed: Optional[int] = 42
    reaction_notice_prob: float = 0.70
    guess_own_prob: float = 0.20
    guess_other_prob: float = 0.15
    kaboom_random_prob: float = 0.08
    kaboom_score_threshold: int = 10
    verbose: bool = True


class FormalKaboomSimulation:
    """Production-style Kaboom engine simulation.

    Goals:
    - Exercise the core engine through its public wrapper methods.
    - Keep simulation policy separate from engine rules.
    - Avoid dead code, duplicated logic, and manual phase cleanup.
    - Resolve reaction windows immediately after a triggering discard/replace.
    """

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.random = random.Random(config.random_seed)
        self.engine = GameEngine(
            game_id=0,
            num_players=config.num_players,
            hand_size=config.hand_size,
        )

        if config.random_seed is not None:
            self.engine.state.rng.seed(config.random_seed)

        self.engine.see_cards_at_start()
        self.turn_count = 0
        self.kaboom_round: Optional[int] = None
        self.players_acted_after_kaboom: set[int] = set()

    # ---------------------------------------------------------------------
    # Formatting / logging
    # ---------------------------------------------------------------------
    def _card_str(self, card) -> Optional[str]:
        if card is None:
            return None
        suit_map = {"♠": "S", "♥": "H", "♦": "D", "♣": "C"}
        suit_str = suit_map.get(card.suit.value, card.suit.name[0])
        return f"{card.rank.value}{suit_str}"

    def _hand_str(self, player_id: int) -> list[str]:
        player = self.engine.state.resolve_player(player_id)
        return [self._card_str(card) for card in player.hand]

    def _log(self, message: str) -> None:
        if self.config.verbose:
            print(message)

    def _print_state_snapshot(self) -> None:
        state = self.engine.state
        self._log("\n[STATE] Game State")
        self._log(f"[STATE] Deck: {len(state.deck)}")
        self._log(f"[STATE] Discard pile: {len(state.discard_pile)}")
        self._log(f"[STATE] Active players: {[p.name for p in state.active_players()]}")
        self._log(f"[STATE] Current player: {state.current_player().name}")
        self._log(f"[STATE] Phase: {state.phase}")
        self._log(f"[STATE] Round: {state.round_number}")
        self._log(f"[STATE] Drawn card: {self._card_str(state.drawn_card)}")
        self._log(f"[STATE] Reaction rank: {state.reaction_rank}")
        self._log(f"[STATE] Reaction initiator: {state.reaction_initiator}")
        self._log(f"[STATE] Reaction open: {state.reaction_open}")
        self._log(f"[STATE] Kaboom called by: {state.kaboom_called_by}")
        self._log(f"[STATE] Instant winner: {state.instant_winner}")

    # ---------------------------------------------------------------------
    # Simulation policy helpers
    # ---------------------------------------------------------------------
    def _should_call_kaboom(self, player_id: int) -> bool:
        state = self.engine.state
        player = state.resolve_player(player_id)

        if state.round_number <= 1:
            return False

        if player.total_score() < self.config.kaboom_score_threshold:
            return True

        return self.random.random() < self.config.kaboom_random_prob

    def _memory_known_self_cards(self, player_id: int) -> list[tuple[int, object]]:
        player = self.engine.state.resolve_player(player_id)
        return [
            (idx, card)
            for (pid, idx), card in player.memory.items()
            if pid == player_id and idx < len(player.hand)
        ]

    def _choose_replace_index(self, player_id: int, drawn_card) -> Optional[int]:
        known_cards = self._memory_known_self_cards(player_id)
        if not known_cards:
            return None

        highest_known_idx, highest_known_card = max(
            known_cards,
            key=lambda item: item[1].score_value,
        )

        if drawn_card.score_value < highest_known_card.score_value:
            return highest_known_idx

        return None

    def _power_type_for_drawn_card(self, drawn_card) -> Optional[PowerType]:
        rank = drawn_card.rank.value
        suit = drawn_card.suit.value

        if rank in {"7", "8"}:
            return PowerType.SEE_SELF
        if rank in {"9", "10"}:
            return PowerType.SEE_OTHER
        if rank in {"J", "Q"}:
            return PowerType.BLIND_SWAP
        if rank == "K" and suit in {"♠", "♣"}:
            return PowerType.SEE_AND_SWAP
        return None

    def _try_use_power(self, player_id: int) -> bool:
        state = self.engine.state
        current_player = state.resolve_player(player_id)
        drawn_card = state.drawn_card
        power_type = self._power_type_for_drawn_card(drawn_card)

        if power_type is None:
            return False

        try:
            if power_type == PowerType.SEE_SELF:
                self.engine.use_power(
                    power_name=power_type,
                    player=current_player,
                    target_player_id=player_id,
                    target_card_index=0,
                )
                self._log(f"[TURN] {current_player.name} used {power_type.value} on own index 0")
                return True

            target_player_id = (player_id + 1) % self.config.num_players

            if power_type == PowerType.SEE_OTHER:
                self.engine.use_power(
                    power_name=power_type,
                    player=current_player,
                    target_player_id=target_player_id,
                    target_card_index=0,
                )
                self._log(f"[TURN] {current_player.name} used {power_type.value} on P{target_player_id + 1}")
                return True

            if power_type in {PowerType.BLIND_SWAP, PowerType.SEE_AND_SWAP}:
                self.engine.use_power(
                    power_name=power_type,
                    player=current_player,
                    target_player_id=player_id,
                    target_card_index=0,
                    second_target_player_id=target_player_id,
                    second_target_card_index=0,
                )
                self._log(f"[TURN] {current_player.name} used {power_type.value} with P{target_player_id + 1}")
                return True

        except Exception as exc:
            self._log(f"[TURN] Power use failed for {current_player.name}: {exc}")
            return False

        return False

    # ---------------------------------------------------------------------
    # Reaction simulation
    # ---------------------------------------------------------------------
    def _simulate_reactions(self) -> None:
        state = self.engine.state

        if not state.reaction_open:
            return

        rank = state.reaction_rank

        for player in self.engine.reaction_order():
            if player.id == state.reaction_initiator:
                continue

            if self.random.random() > self.config.reaction_notice_prob:
                continue

            own_matches = [
                idx
                for (pid, idx), card in player.memory.items()
                if pid == player.id
                and idx < len(player.hand)
                and card.rank.value == rank
            ]

            if own_matches:
                idx = own_matches[0]
                try:
                    result = self.engine.react_discard_own_card(player.id, idx)
                    self._log(f"[REACTION] {player.name} discarded own card at index {idx}")
                    if result.penalty_applied:
                        self._log(f"[REACTION] Penalty applied to {player.name}")
                    return
                except Exception as exc:
                    self._log(f"[REACTION] Own-card reaction failed for {player.name}: {exc}")

            other_targets = [
                (pid, idx)
                for (pid, idx), card in player.memory.items()
                if pid != player.id and card.rank.value == rank
            ]

            if other_targets and player.hand:
                pid, idx = other_targets[0]
                target = state.resolve_player(pid)
                if idx < len(target.hand):
                    try:
                        result = self.engine.react_discard_other_card(player.id, pid, idx, 0)
                        self._log(
                            f"[REACTION] {player.name} discarded {target.name}'s card at index {idx} "
                            f"and gave own index 0"
                        )
                        if result.penalty_applied:
                            self._log(f"[REACTION] Penalty applied to {player.name}")
                        return
                    except Exception as exc:
                        self._log(f"[REACTION] Other-card reaction failed for {player.name}: {exc}")

            if player.hand and self.random.random() < self.config.guess_own_prob:
                guess_idx = self.random.randint(0, len(player.hand) - 1)
                try:
                    result = self.engine.react_discard_own_card(player.id, guess_idx)
                    self._log(f"[REACTION] {player.name} guessed own card at index {guess_idx}")
                    if result.penalty_applied:
                        self._log(f"[REACTION] Wrong guess penalty applied to {player.name}")
                    return
                except Exception:
                    pass

            if player.hand and self.random.random() < self.config.guess_other_prob:
                candidates = [p for p in state.players if p.id != player.id and p.hand]
                if not candidates:
                    continue
                target = self.random.choice(candidates)
                guess_idx = self.random.randint(0, len(target.hand) - 1)
                try:
                    result = self.engine.react_discard_other_card(player.id, target.id, guess_idx, 0)
                    self._log(f"[REACTION] {player.name} guessed {target.name}'s card at index {guess_idx}")
                    if result.penalty_applied:
                        self._log(f"[REACTION] Wrong guess penalty applied to {player.name}")
                    return
                except Exception:
                    pass

        if state.reaction_open:
            self._log(f"[REACTION] Closing reaction window for rank {state.reaction_rank}")
            self.engine.close_reaction()

    # ---------------------------------------------------------------------
    # Turn execution
    # ---------------------------------------------------------------------
    def _handle_kaboom_progress(self) -> bool:
        state = self.engine.state
        current_player = state.current_player()

        if state.kaboom_called_by is None:
            return False

        if self.kaboom_round is None:
            self.kaboom_round = state.round_number
            caller_name = state.players[state.kaboom_called_by].name
            self._log(f"[GAME] Kaboom called by {caller_name} in round {self.kaboom_round}")

        active_player_ids = {p.id for p in state.active_players()}
        if active_player_ids.issubset(self.players_acted_after_kaboom):
            self._log("[GAME] All active players have acted after Kaboom. Ending simulation.")
            return True

        self.players_acted_after_kaboom.add(current_player.id)
        return False

    def _advance_if_inactive(self) -> bool:
        current_player = self.engine.state.current_player()
        if current_player.active:
            return False
        self.engine.state.advance_turn()
        return True

    def _execute_turn(self) -> None:
        state = self.engine.state
        current_player = state.current_player()

        if state.phase == GamePhase.TURN_DRAW:
            self._log(f"\n[TURN] Starting turn for {current_player.name}")
            self._log(f"[TURN] Hand: {self._hand_str(current_player.id)}")

            if self._should_call_kaboom(current_player.id):
                self.engine.call_kaboom(current_player.id)
                self._log(f"[KABOOM] {current_player.name} called Kaboom")
                return

            result = self.engine.draw_card(current_player.id)
            drawn_card = result[0].card
            self._log(f"[TURN] {current_player.name} drew {self._card_str(drawn_card)}")
            return

        if state.phase == GamePhase.TURN_RESOLVE:
            drawn_card = state.drawn_card
            self._log(f"[TURN] Resolving {self._card_str(drawn_card)} for {current_player.name}")

            if self._try_use_power(current_player.id):
                return

            replace_index = self._choose_replace_index(current_player.id, drawn_card)
            if replace_index is not None:
                self.engine.replace_card(current_player.id, replace_index)
                current_player.remember(current_player.id, replace_index, drawn_card)
                self._log(
                    f"[TURN] {current_player.name} replaced index {replace_index} "
                    f"with {self._card_str(drawn_card)}"
                )
                return

            self.engine.discard_card(current_player.id)
            self._log(f"[TURN] {current_player.name} discarded {self._card_str(drawn_card)}")
            return

        raise RuntimeError(f"Unexpected phase during simulation: {state.phase}")

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def run(self) -> None:
        self._log("\n[MESSAGE] Starting formal Kaboom simulation\n")
        self._log(f"[CONFIG] Players: {self.config.num_players}")
        self._log(f"[CONFIG] Hand size: {self.config.hand_size}")
        self._log(f"[CONFIG] Round limit: {self.config.round_limit}")
        self._log(f"[CONFIG] Seed: {self.config.random_seed}")

        for player in self.engine.state.players:
            self._log(f"[SETUP] {player.name}: {self._hand_str(player.id)}")

        self._print_state_snapshot()

        observed_round = 0
        while (
            self.engine.state.phase != GamePhase.GAME_OVER
            and self.engine.state.round_number <= self.config.round_limit
        ):
            if observed_round < self.engine.state.round_number:
                observed_round = self.engine.state.round_number
                self._log(f"\n############## [Round {observed_round}] ##############\n")

            if self._handle_kaboom_progress():
                break

            if self._advance_if_inactive():
                continue

            self._execute_turn()

            if self.engine.state.reaction_open:
                self._simulate_reactions()

            self.turn_count += 1
            self._print_state_snapshot()

        self._print_final_results()

    def _print_final_results(self) -> None:
        players = self.engine.state.players
        scores = [player.total_score() for player in players]

        self._log(f"\n[FINAL] Scores: {scores}")

        if self.engine.state.kaboom_called_by is not None:
            caller = players[self.engine.state.kaboom_called_by].name
            self._log(f"[FINAL] Kaboom called by: {caller}")

        if self.engine.state.instant_winner is not None:
            winner = players[self.engine.state.instant_winner].name
            self._log(f"[FINAL] Instant winner: {winner}")
        else:
            min_score = min(scores)
            winners = [player.name for player in players if player.total_score() == min_score]
            if len(winners) == 1:
                self._log(f"[FINAL] Winner: {winners[0]}")
            else:
                self._log(f"[FINAL] Winners: {', '.join(winners)}")

        self._log(
            f"[FINAL] Simulation ended at round {self.engine.state.round_number}, "
            f"total turns: {self.turn_count}"
        )


def main() -> None:
    simulation = FormalKaboomSimulation(SimulationConfig())
    simulation.run()


if __name__ == "__main__":
    main()
