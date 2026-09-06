from random import Random
from copy import deepcopy

from flip7.agents.base_agent import BaseAgent
from flip7.agents.threshold_agent import SimpleThresholdAgent
from flip7.mcts.agent_adapter import AgentPolicyAdapter

from flip7.game.cards import (
    ActionCard,
    ActionType,
    Card,
    ModifierCard,
    NumberCard,
)
from flip7.game.player import Player
from flip7.game.scoring import calculate_round_score
from flip7.mcts.action import (
    Flip7SearchAction,
    SearchActionType,
)
from flip7.mcts.state import (
    Flip7SearchState,
    SearchDecisionPhase,
    SearchPendingAction,
    SearchPlayerState,
)


class Flip7SearchModel:
    def __init__(
            self,
            opponent_agent: BaseAgent | None = None,
            rollout_agent: BaseAgent | None = None,
            automatic_opponent_turns: bool = False,
            simulate_multiple_rounds: bool = False,
    ) -> None:
        if opponent_agent is None:
            opponent_agent = SimpleThresholdAgent(
                "Simulated opponent"
            )

        self._opponent_policy = AgentPolicyAdapter(
            opponent_agent
        )

        if rollout_agent is None:
            rollout_agent = SimpleThresholdAgent(
                "Simulated root player"
            )

        self._rollout_policy = AgentPolicyAdapter(
            rollout_agent
        )
        self._simulate_multiple_rounds = (
            simulate_multiple_rounds
        )
        self._automatic_opponent_turns = (
            automatic_opponent_turns
            or simulate_multiple_rounds
        )

    def choose_rollout_action(
            self,
            state: Flip7SearchState,
            valid_actions: tuple[Flip7SearchAction, ...],
            random_generator: Random,
    ) -> Flip7SearchAction:
        del random_generator

        return self._rollout_policy.choose_action(
            state=state,
            valid_actions=valid_actions,
        )

    def get_valid_actions(
            self,
            state: Flip7SearchState,
    ) -> tuple[Flip7SearchAction, ...]:
        if self.is_terminal(state):
            return ()

        if (
                state.current_player_index
                != state.root_player_index
        ):
            raise RuntimeError(
                "The search state must stop at a decision "
                "of the root player."
            )

        return self._get_valid_actions_for_current_player(
            state
        )

    def _get_valid_actions_for_current_player(
            self,
            state: Flip7SearchState,
    ) -> tuple[Flip7SearchAction, ...]:
        if self.is_terminal(state):
            return ()

        if (
                state.decision_phase
                is SearchDecisionPhase.ACTION_TARGET
        ):
            return self._get_valid_target_actions(state)

        return self._get_valid_turn_actions(state)

    def _choose_opponent_action(
            self,
            state: Flip7SearchState,
    ) -> Flip7SearchAction:
        if (
                state.current_player_index
                == state.root_player_index
        ):
            raise ValueError(
                "An opponent action requires an opponent player."
            )

        valid_actions = (
            self._get_valid_actions_for_current_player(state)
        )

        return self._opponent_policy.choose_action(
            state=state,
            valid_actions=valid_actions,
        )

    def _get_next_active_player_index(
            self,
            state: Flip7SearchState,
            after_player_index: int,
    ) -> int | None:
        self._get_player(
            state=state,
            player_index=after_player_index,
        )

        number_of_players = len(state.players)

        for offset in range(1, number_of_players + 1):
            candidate_index = (
                                      after_player_index + offset
                              ) % number_of_players

            candidate = self._get_player(
                state=state,
                player_index=candidate_index,
            )

            if candidate.is_active:
                return candidate_index

        return None

    def _advance_to_next_turn(
            self,
            state: Flip7SearchState,
            after_player_index: int,
    ) -> bool:
        if state.pending_action is not None:
            raise RuntimeError(
                "A pending action must be resolved "
                "before advancing the turn."
            )

        self._update_round_finished(state)

        if state.round_finished:
            state.current_player_index = (
                state.root_player_index
            )
            state.decision_phase = SearchDecisionPhase.TURN
            return False

        next_player_index = (
            self._get_next_active_player_index(
                state=state,
                after_player_index=after_player_index,
            )
        )

        if next_player_index is None:
            raise RuntimeError(
                "An unfinished round requires "
                "an active player."
            )

        state.current_player_index = next_player_index
        state.decision_phase = SearchDecisionPhase.TURN

        return True

    def _get_valid_turn_actions(
        self,
        state: Flip7SearchState,
    ) -> tuple[Flip7SearchAction, ...]:
        player = self._get_player(
            state,
            state.current_player_index,
        )

        if not player.is_active:
            return ()

        actions = [
            Flip7SearchAction(SearchActionType.HIT),
        ]

        if player.round_cards:
            actions.append(
                Flip7SearchAction(SearchActionType.STAY)
            )

        return tuple(actions)

    def _get_valid_target_actions(
        self,
        state: Flip7SearchState,
    ) -> tuple[Flip7SearchAction, ...]:
        pending_action = state.pending_action

        if pending_action is None:
            raise RuntimeError(
                "The action-target phase requires "
                "a pending action."
            )

        valid_targets = [
            player
            for player in state.players
            if player.is_active
        ]

        if (
            pending_action.action_type
            is ActionType.SECOND_CHANCE
        ):
            valid_targets = [
                player
                for player in valid_targets
                if not player.has_second_chance
            ]

        valid_targets.sort(
            key=lambda player: player.player_index
        )

        return tuple(
            Flip7SearchAction(
                action_type=SearchActionType.ACTION_TARGET,
                target_player_index=player.player_index,
            )
            for player in valid_targets
        )

    def sample_transition(
            self,
            state: Flip7SearchState,
            action: Flip7SearchAction,
            random_generator: Random,
    ) -> Flip7SearchState:
        next_state = deepcopy(state)

        valid_actions = self.get_valid_actions(next_state)

        if action not in valid_actions:
            raise ValueError(
                "The selected search action is not valid "
                "for the current state."
            )

        self._apply_selected_action(
            state=next_state,
            action=action,
            random_generator=random_generator,
        )

        if self._automatic_opponent_turns:
            self._continue_after_root_action(
                state=next_state,
                random_generator=random_generator,
            )

        return next_state

    def _apply_selected_action(
            self,
            state: Flip7SearchState,
            action: Flip7SearchAction,
            random_generator: Random,
    ) -> None:
        if action.action_type is SearchActionType.STAY:
            self._apply_stay(state)
            return

        if action.action_type is SearchActionType.HIT:
            self._apply_hit(
                state=state,
                random_generator=random_generator,
            )
            return

        if (
                action.action_type
                is SearchActionType.ACTION_TARGET
        ):
            self._apply_action_target(
                state=state,
                action=action,
                random_generator=random_generator,
            )
            return

        raise ValueError(
            f"Unsupported search action: {action!r}"
        )

    def _apply_opponent_action(
            self,
            state: Flip7SearchState,
            random_generator: Random,
    ) -> Flip7SearchAction:
        action = self._choose_opponent_action(state)

        self._apply_selected_action(
            state=state,
            action=action,
            random_generator=random_generator,
        )

        return action

    def _resolve_simulated_pending_actions(
            self,
            state: Flip7SearchState,
            random_generator: Random,
    ) -> None:
        while state.pending_action is not None:
            valid_actions = (
                self._get_valid_actions_for_current_player(
                    state
                )
            )

            action = self._opponent_policy.choose_action(
                state=state,
                valid_actions=valid_actions,
            )

            self._apply_selected_action(
                state=state,
                action=action,
                random_generator=random_generator,
            )

    def _simulate_opponent_turn(
            self,
            state: Flip7SearchState,
            random_generator: Random,
    ) -> bool:
        if (
                state.current_player_index
                == state.root_player_index
        ):
            raise ValueError(
                "An opponent turn requires an opponent player."
            )

        if (
                state.decision_phase
                is not SearchDecisionPhase.TURN
        ):
            raise RuntimeError(
                "An opponent turn must begin in the turn phase."
            )

        turn_player_index = state.current_player_index

        self._apply_opponent_action(
            state=state,
            random_generator=random_generator,
        )

        self._resolve_simulated_pending_actions(
            state=state,
            random_generator=random_generator,
        )

        return self._advance_to_next_turn(
            state=state,
            after_player_index=turn_player_index,
        )

    def _simulate_opponents_until_root(
            self,
            state: Flip7SearchState,
            random_generator: Random,
    ) -> None:
        while (
                not state.round_finished
                and state.current_player_index
                != state.root_player_index
        ):
            self._simulate_opponent_turn(
                state=state,
                random_generator=random_generator,
            )

    def _continue_after_root_action(
            self,
            state: Flip7SearchState,
            random_generator: Random,
    ) -> None:
        if state.game_finished:
            return

        if state.round_finished:
            self._continue_after_finished_round(
                state=state,
                random_generator=random_generator,
            )
            return

        if state.pending_action is not None:
            if (
                    state.current_player_index
                    == state.root_player_index
            ):
                return

            self._resolve_simulated_pending_actions(
                state=state,
                random_generator=random_generator,
            )

            if state.round_finished:
                self._continue_after_finished_round(
                    state=state,
                    random_generator=random_generator,
                )
                return

        did_advance = self._advance_to_next_turn(
            state=state,
            after_player_index=state.root_player_index,
        )

        if not did_advance:
            self._continue_after_finished_round(
                state=state,
                random_generator=random_generator,
            )
            return

        self._simulate_opponents_until_root(
            state=state,
            random_generator=random_generator,
        )

        if state.round_finished:
            self._continue_after_finished_round(
                state=state,
                random_generator=random_generator,
            )

    def _continue_after_finished_round(
            self,
            state: Flip7SearchState,
            random_generator: Random,
    ) -> None:
        if not self._simulate_multiple_rounds:
            return

        while state.round_finished and not state.game_finished:
            round_has_turn = (
                self._finish_and_start_next_search_round(
                    state=state,
                    random_generator=random_generator,
                )
            )

            if state.game_finished:
                return

            if not round_has_turn:
                continue

            if (
                    state.current_player_index
                    != state.root_player_index
            ):
                self._simulate_opponents_until_root(
                    state=state,
                    random_generator=random_generator,
                )

    def _apply_stay(self, state: Flip7SearchState) -> None:
        player = self._get_player(
            state=state,
            player_index=state.current_player_index,
        )

        player.has_stayed = True
        player.is_active = False

        state.round_finished = not any(
            other_player.is_active
            for other_player in state.players
        )

    def _apply_hit(
        self,
        state: Flip7SearchState,
        random_generator: Random,
    ) -> None:
        player = self._get_player(
            state=state,
            player_index=state.current_player_index,
        )

        card = self._draw_random_card(
            state=state,
            random_generator=random_generator,
        )

        if isinstance(card, NumberCard):
            self._process_number_card(
                state=state,
                player=player,
                card=card,
            )
            self._update_round_finished(state)
            return

        if isinstance(card, ModifierCard):
            player.round_cards.append(card)
            self._update_round_finished(state)
            return

        if isinstance(card, ActionCard):
            state.pending_action = SearchPendingAction(
                source_player_index=player.player_index,
                action_type=card.action_type,
            )
            state.decision_phase = (
                SearchDecisionPhase.ACTION_TARGET
            )

            if not self._get_valid_target_actions(state):
                self._discard_card(
                    state=state,
                    card=card,
                )
                state.pending_action = None
                state.decision_phase = (
                    SearchDecisionPhase.TURN
                )

            return

        raise TypeError(
            f"Unsupported card type: {type(card).__name__}"
        )

    def _apply_action_target(
            self,
            state: Flip7SearchState,
            action: Flip7SearchAction,
            random_generator: Random,
    ) -> None:
        pending_action = state.pending_action

        if pending_action is None:
            raise RuntimeError(
                "There is no pending action."
            )

        if action.target_player_index is None:
            raise RuntimeError(
                "The target player index is missing."
            )

        target_player = self._get_player(
            state=state,
            player_index=action.target_player_index,
        )

        action_card = ActionCard(
            pending_action.action_type
        )

        if (
            pending_action.action_type
            is ActionType.FREEZE
        ):
            target_player.round_cards.append(action_card)
            self._apply_freeze(target_player)

        elif (
            pending_action.action_type
            is ActionType.SECOND_CHANCE
        ):
            target_player.round_cards.append(action_card)
            self._apply_second_chance(target_player)



        elif pending_action.action_type is ActionType.FLIP_THREE:
            target_player.round_cards.append(action_card)
            self._apply_flip_three(
                state=state,
                target_player=target_player,
                random_generator=random_generator,
            )

        else:
            raise ValueError(
                "Unsupported pending action type."
            )

        self._complete_pending_action(state)

    def _apply_freeze(
        self,
        target_player: SearchPlayerState,
    ) -> None:
        target_player.is_active = False

    def _apply_second_chance(
        self,
        target_player: SearchPlayerState,
    ) -> None:
        target_player.has_second_chance = True

    def _apply_flip_three(
        self,
        state: Flip7SearchState,
        target_player: SearchPlayerState,
        random_generator: Random,
    ) -> None:
        drawn_actions: list[SearchPendingAction] = []

        for _ in range(3):
            if not target_player.is_active:
                break

            if self._has_flip_seven(target_player):
                break

            card = self._draw_random_card(
                state=state,
                random_generator=random_generator,
            )

            pending_action = self._process_flip_three_card(
                state=state,
                target_player=target_player,
                card=card,
            )

            if pending_action is not None:
                drawn_actions.append(pending_action)

            self._update_round_finished(state)

            if state.round_finished:
                break

        state.queued_actions = [
            *drawn_actions,
            *state.queued_actions,
        ]

    def _process_flip_three_card(
        self,
        state: Flip7SearchState,
        target_player: SearchPlayerState,
        card: Card,
    ) -> SearchPendingAction | None:
        if isinstance(card, NumberCard):
            self._process_number_card(
                state=state,
                player=target_player,
                card=card,
            )
            return None

        if isinstance(card, ModifierCard):
            target_player.round_cards.append(card)
            return None

        if isinstance(card, ActionCard):
            if (
                card.action_type
                is ActionType.SECOND_CHANCE
                and not target_player.has_second_chance
            ):
                target_player.round_cards.append(card)
                self._apply_second_chance(target_player)
                return None

            return SearchPendingAction(
                source_player_index=(
                    target_player.player_index
                ),
                action_type=card.action_type,
            )

        raise TypeError(
            f"Unsupported card type: {type(card).__name__}"
        )

    def _complete_pending_action(
            self,
            state: Flip7SearchState,
    ) -> None:
        state.pending_action = None
        self._update_round_finished(state)

        if state.round_finished:
            self._discard_queued_actions(state)
            state.current_player_index = (
                state.root_player_index
            )
            state.decision_phase = SearchDecisionPhase.TURN
            return

        self._promote_next_queued_action(state)

    def _promote_next_queued_action(
        self,
        state: Flip7SearchState,
    ) -> None:
        while state.queued_actions:
            next_action = state.queued_actions.pop(0)

            state.pending_action = next_action
            state.current_player_index = (
                next_action.source_player_index
            )
            state.decision_phase = (
                SearchDecisionPhase.ACTION_TARGET
            )

            if self._get_valid_target_actions(state):
                return

            self._discard_card(
                state=state,
                card=ActionCard(
                    next_action.action_type
                ),
            )
            state.pending_action = None

        state.current_player_index = state.root_player_index
        state.decision_phase = SearchDecisionPhase.TURN

    def _discard_queued_actions(
        self,
        state: Flip7SearchState,
    ) -> None:
        for queued_action in state.queued_actions:
            self._discard_card(
                state=state,
                card=ActionCard(
                    queued_action.action_type
                ),
            )

        state.queued_actions.clear()

    def _process_number_card(
        self,
        state: Flip7SearchState,
        player: SearchPlayerState,
        card: NumberCard,
    ) -> None:
        if not player.has_number(card.number):
            player.round_cards.append(card)
            return

        if player.has_second_chance:
            self._consume_second_chance(
                state=state,
                player=player,
                duplicate_card=card,
            )
            return

        player.round_cards.append(card)
        player.has_busted = True
        player.is_active = False

    def _consume_second_chance(
        self,
        state: Flip7SearchState,
        player: SearchPlayerState,
        duplicate_card: NumberCard,
    ) -> None:
        player.has_second_chance = False

        self._discard_card(
            state=state,
            card=duplicate_card,
        )

        second_chance_card = next(
            (
                card
                for card in player.round_cards
                if (
                    isinstance(card, ActionCard)
                    and card.action_type
                    is ActionType.SECOND_CHANCE
                )
            ),
            None,
        )

        if second_chance_card is None:
            return

        player.round_cards.remove(second_chance_card)

        self._discard_card(
            state=state,
            card=second_chance_card,
        )

    def _discard_card(
        self,
        state: Flip7SearchState,
        card: Card,
    ) -> None:
        previous_count = (
            state.discarded_card_counts.get(card, 0)
        )

        state.discarded_card_counts[card] = (
            previous_count + 1
        )

    def _update_round_finished(
        self,
        state: Flip7SearchState,
    ) -> None:
        has_flip_seven = any(
            self._has_flip_seven(player)
            for player in state.players
        )

        has_active_player = any(
            player.is_active
            for player in state.players
        )

        state.round_finished = (
            has_flip_seven
            or not has_active_player
        )

    def _has_flip_seven(
        self,
        player: SearchPlayerState,
    ) -> bool:
        if player.has_busted:
            return False

        unique_numbers = {
            card.number
            for card in player.round_cards
            if isinstance(card, NumberCard)
        }

        return len(unique_numbers) >= 7

    def _draw_random_card(
        self,
        state: Flip7SearchState,
        random_generator: Random,
    ) -> Card:
        remaining_card_count = sum(
            state.remaining_card_counts.values()
        )

        if remaining_card_count == 0:
            self._recycle_discarded_cards(state)

            remaining_card_count = sum(
                state.remaining_card_counts.values()
            )

        if remaining_card_count == 0:
            raise RuntimeError(
                "Cannot draw from an empty search deck."
            )

        selected_position = random_generator.randrange(
            remaining_card_count
        )

        for card, count in state.remaining_card_counts.items():
            if count == 0:
                continue

            if selected_position < count:
                state.remaining_card_counts[card] -= 1
                return card

            selected_position -= count

        raise RuntimeError(
            "The search deck contains inconsistent counts."
        )

    def _recycle_discarded_cards(self, state: Flip7SearchState) -> None:
        for card, count in state.discarded_card_counts.items():
            previous_count = (
                state.remaining_card_counts.get(card, 0)
            )

            state.remaining_card_counts[card] = (
                previous_count + count
            )
            state.discarded_card_counts[card] = 0

    def is_terminal(
        self,
        state: Flip7SearchState,
    ) -> bool:
        if state.game_finished:
            return True

        return (
            state.round_finished
            and not self._simulate_multiple_rounds
        )

    def get_reward(
        self,
        state: Flip7SearchState,
    ) -> float:
        root_player = self._get_player(
            state,
            state.root_player_index,
        )

        if state.game_finished:
            return self._get_terminal_reward(
                state=state,
                root_player=root_player,
            )

        root_score = self._get_evaluated_score(root_player)

        opponent_scores = [
            self._get_evaluated_score(player)
            for player in state.players
            if player.player_index
            != state.root_player_index
        ]

        score_difference = (
            root_score - max(opponent_scores)
        )
        normalized_reward = (
            score_difference / state.winning_score
        )

        return max(-1.0, min(1.0, normalized_reward))

    def _get_terminal_reward(
        self,
        state: Flip7SearchState,
        root_player: SearchPlayerState,
    ) -> float:
        highest_score = max(
            player.total_score
            for player in state.players
        )

        if root_player.total_score < highest_score:
            return -1.0

        number_of_winners = sum(
            player.total_score == highest_score
            for player in state.players
        )

        return 1.0 / number_of_winners

    def _finish_search_round(
            self,
            state: Flip7SearchState,
    ) -> None:
        if not state.round_finished:
            raise RuntimeError(
                "Only a finished search round can be scored."
            )

        if state.pending_action is not None:
            raise RuntimeError(
                "A finished search round cannot have "
                "a pending action."
            )

        for player_state in state.players:
            player_state.total_score += (
                self._get_round_score(player_state)
            )

            for card in player_state.round_cards:
                self._discard_card(
                    state=state,
                    card=card,
                )

            player_state.round_cards.clear()
            player_state.is_active = False

        state.game_finished = any(
            player.total_score >= state.winning_score
            for player in state.players
        )
        state.current_player_index = state.root_player_index
        state.decision_phase = SearchDecisionPhase.TURN

    def _finish_and_start_next_search_round(
            self,
            state: Flip7SearchState,
            random_generator: Random,
    ) -> bool:
        self._finish_search_round(state)

        if state.game_finished:
            return False

        starting_player_index = (
            state.next_starting_player_index
        )
        state.next_starting_player_index = (
            starting_player_index + 1
        ) % len(state.players)

        for player in state.players:
            player.round_cards.clear()
            player.is_active = True
            player.has_stayed = False
            player.has_busted = False
            player.has_second_chance = False

        state.round_finished = False
        state.pending_action = None
        state.queued_actions.clear()
        state.decision_phase = SearchDecisionPhase.TURN

        for offset in range(len(state.players)):
            player_index = (
                starting_player_index + offset
            ) % len(state.players)
            player = self._get_player(
                state=state,
                player_index=player_index,
            )

            if not player.is_active:
                continue

            state.current_player_index = player_index

            self._apply_hit(
                state=state,
                random_generator=random_generator,
            )
            self._resolve_simulated_pending_actions(
                state=state,
                random_generator=random_generator,
            )

            if state.round_finished:
                state.current_player_index = (
                    state.root_player_index
                )
                return False

        previous_player_index = (
            starting_player_index - 1
        ) % len(state.players)
        first_active_player_index = (
            self._get_next_active_player_index(
                state=state,
                after_player_index=previous_player_index,
            )
        )

        if first_active_player_index is None:
            self._update_round_finished(state)
            state.current_player_index = (
                state.root_player_index
            )
            return False

        state.current_player_index = first_active_player_index
        state.decision_phase = SearchDecisionPhase.TURN
        return True

    def _get_round_score(
            self,
            player_state: SearchPlayerState,
    ) -> int:
        player = Player(player_state.player_name)
        player.round_cards = list(
            player_state.round_cards
        )
        player.has_busted = player_state.has_busted

        return calculate_round_score(player)

    def _get_evaluated_score(
        self,
        player_state: SearchPlayerState,
    ) -> int:
        return (
            player_state.total_score
            + self._get_round_score(player_state)
        )

    def _get_player(
        self,
        state: Flip7SearchState,
        player_index: int,
    ) -> SearchPlayerState:
        player = next(
            (
                candidate
                for candidate in state.players
                if candidate.player_index == player_index
            ),
            None,
        )

        if player is None:
            raise RuntimeError(
                "The requested player does not exist "
                "in the search state."
            )

        return player
