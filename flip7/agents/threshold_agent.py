from random import Random

from flip7.agents.base_agent import (
    AgentObservation,
    BaseAgent,
    TargetOption,
    TurnDecision,
)
from flip7.game.cards import ActionType

class SimpleThresholdAgent(BaseAgent):
    def __init__(self, player_name: str, seed: int | None = None) -> None:
        super().__init__(player_name)
        self._random = Random(seed)

    def choose_hit_or_stay(self, observation: AgentObservation) -> TurnDecision:
        if not observation.valid_turn_decisions:
            raise ValueError("A threshold agent requires at least one valid turn decision.")

        if observation.own_player.current_round_score < 23:
            return TurnDecision.HIT
        else:
            return TurnDecision.STAY


    def choose_action_target(
        self,
        observation: AgentObservation,
        action_type: ActionType,
        valid_targets: tuple[TargetOption, ...],
    ) -> TargetOption:
        if not valid_targets:
            raise ValueError(
                "A threshold agent requires at least one valid target."
            )

        own_target = self.find_own_target(
            observation,
            valid_targets,
        )

        opponent_targets = self.get_opponent_targets(
            observation,
            valid_targets,
        )



        if action_type is ActionType.SECOND_CHANCE:
            if own_target is not None:
                return own_target
            else:
                # chooses opponent player with the lowest total score
                return min(opponent_targets, key=lambda target: target.player.total_score)

        if action_type is ActionType.FREEZE:
            possible_targets = opponent_targets or valid_targets

            return max(possible_targets, key=lambda target: target.player.total_score)

        if action_type is ActionType.FLIP_THREE:
            possible_targets = opponent_targets or valid_targets

        return max(possible_targets, key=lambda target: (target.player.current_round_score, target.player.total_score))

        raise ValueError(
            f"Unsupported action type: {action_type!r}"
        )
