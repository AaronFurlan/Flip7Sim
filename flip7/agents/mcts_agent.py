from flip7.agents.base_agent import (
    AgentObservation,
    BaseAgent,
    TargetOption,
    TurnDecision,
)
from flip7.game.cards import ActionType
from flip7.mcts.action import SearchActionType
from flip7.mcts.flip7_model import Flip7SearchModel
from flip7.mcts.search import MCTSSearch
from flip7.mcts.state_factory import create_search_state


class MCTSAgent(BaseAgent):
    def __init__(
            self,
            player_name: str,
            simulations: int = 200,
            exploration_weight: float = 0.9,
            max_depth: int = 20,
            seed: int | None = None,
            opponent_agent: BaseAgent | None = None,
            rollout_agent: BaseAgent | None = None,
            simulate_multiple_rounds: bool = True,
    ) -> None:
        super().__init__(player_name)

        model = Flip7SearchModel(
            opponent_agent=opponent_agent,
            rollout_agent=rollout_agent,
            automatic_opponent_turns=True,
            simulate_multiple_rounds=simulate_multiple_rounds,
        )

        self._search = MCTSSearch(
            model=model,
            simulations=simulations,
            exploration_weight=exploration_weight,
            max_depth=max_depth,
            seed=seed,
            rollout_policy=model.choose_rollout_action,
        )

    def choose_hit_or_stay(
            self,
            observation: AgentObservation,
    ) -> TurnDecision:
        state = create_search_state(observation)
        action = self._search.find_best_action(state)

        if action.action_type is SearchActionType.HIT:
            return TurnDecision.HIT

        if action.action_type is SearchActionType.STAY:
            return TurnDecision.STAY

        raise RuntimeError(
            "MCTS returned an action target for a turn decision."
        )

    def choose_action_target(
            self,
            observation: AgentObservation,
            action_type: ActionType,
            valid_targets: tuple[TargetOption, ...],
    ) -> TargetOption:
        if not valid_targets:
            raise ValueError(
                "An MCTS agent requires at least one valid target."
            )

        state = create_search_state(
            observation=observation,
            pending_action_type=action_type,
        )
        action = self._search.find_best_action(state)

        if (
                action.action_type
                is not SearchActionType.ACTION_TARGET
                or action.target_player_index is None
        ):
            raise RuntimeError(
                "MCTS returned a turn action for a target decision."
            )

        selected_target = next(
            (
                target
                for target in valid_targets
                if (
                    target.player_index
                    == action.target_player_index
                )
            ),
            None,
        )

        if selected_target is None:
            raise RuntimeError(
                "MCTS selected an invalid action target."
            )

        return selected_target
