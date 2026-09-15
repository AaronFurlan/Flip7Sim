from flip7.agents.base_agent import AgentObservation, TurnDecision

ACTIONS: tuple[TurnDecision, ...] = (TurnDecision.HIT, TurnDecision.STAY)


def get_valid_actions(observation: AgentObservation) -> tuple[TurnDecision, ...]:
    return tuple(action for action in ACTIONS if action in observation.valid_turn_decisions)

