from flip7.agents.base_agent import (
    AgentObservation,
    BaseAgent,
    TargetOption,
    TurnDecision,
)
from flip7.game.cards import ActionType

class AlwaysHitAgent(BaseAgent):
    def __init__(self, player_name: str, player_index: int) -> None:
        super().__init__(player_name)
        self.player_index = player_index

    def choose_hit_or_stay(self, observation: AgentObservation) -> TurnDecision:
        if not observation.valid_turn_decisions:
            raise ValueError("An always-hit agent requires at least one valid turn decision.")

        return TurnDecision.HIT

    def choose_action_target(
        self,
        observation: AgentObservation,
        action_type: ActionType,
        valid_targets: tuple[TargetOption, ...],
    ) -> TargetOption:
        if not valid_targets:
            raise ValueError(
                "An always-hit agent requires at least one valid target."
            )

        target = None
        for t in valid_targets:
            if t.player_index == self.player_index:
                target = t
                break

        if target is None:
            raise ValueError(
                f"No valid target found for player index {self.player_index}."
            )

        return target