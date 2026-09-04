from random import Random

from flip7.game.cards import ActionType
from flip7.game.player import Player
from flip7.game.scoring import calculate_round_score
from flip7.mcts.action import (
    Flip7SearchAction,
    SearchActionType,
)
from flip7.mcts.state import (
    Flip7SearchState,
    SearchDecisionPhase,
    SearchPlayerState,
)


class Flip7SearchModel:
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

        if (
            state.decision_phase
            is SearchDecisionPhase.ACTION_TARGET
        ):
            return self._get_valid_target_actions(state)

        return self._get_valid_turn_actions(state)

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
        raise NotImplementedError(
            "Search transitions are implemented "
            "in step 4.2."
        )

    def is_terminal(
        self,
        state: Flip7SearchState,
    ) -> bool:
        return state.game_finished

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

        best_opponent_score = max(opponent_scores)
        score_difference = (
            root_score - best_opponent_score
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

    def _get_evaluated_score(
        self,
        player_state: SearchPlayerState,
    ) -> int:
        player = Player(player_state.player_name)
        player.total_score = player_state.total_score
        player.round_cards = list(
            player_state.round_cards
        )
        player.is_active = player_state.is_active
        player.has_stayed = player_state.has_stayed
        player.has_busted = player_state.has_busted
        player.has_second_chance = (
            player_state.has_second_chance
        )

        return (
            player.total_score
            + calculate_round_score(player)
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