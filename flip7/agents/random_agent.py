from random import Random

from flip7.agents.base_agent import (
    AgentObservation,
    BaseAgent,
    TargetOption,
    TurnDecision,
)
from flip7.game.cards import ActionType

class RandomAgent(BaseAgent):
    def __init__(self, player_name: str, seed: int | None = None) -> None:
        super().__init__(player_name)
        self._random = Random(seed)

    def choose_hit_or_stay(self, observation: AgentObservation) -> TurnDecision:
        return self._random.choice((TurnDecision.HIT, TurnDecision.STAY))

    def choose_action_target(
        self,
        observation: AgentObservation,
        action_type: ActionType,
        valid_targets: tuple[TargetOption, ...],
    ) -> TargetOption:
        if not valid_targets:
            raise ValueError(
                "A random agent requires at least one valid target."
            )

        return self._random.choice(valid_targets)