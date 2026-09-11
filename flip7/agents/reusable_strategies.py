from flip7.game.cards import ActionType
from flip7.agents.base_agent import TargetOption

def basic_sensible_action_strategy(
    action_type: ActionType,
    self_target: TargetOption | None,
    opponent_targets: tuple[TargetOption, ...],
) -> TargetOption:
    """Returns action card targets following some baseline sensible principles."""

    if self_target is None and not opponent_targets:
        raise ValueError(f"No valid target for {action_type!r}")

    match action_type:
        # Choose self; if impossible, choose opponent with lowest total score
        case ActionType.SECOND_CHANCE:
            if self_target is not None:
                return self_target
            else:
                return min(opponent_targets, key=lambda target: target.player.total_score)

        # Choose opponent with highest total score; if impossible, choose self
        case ActionType.FREEZE:
            if opponent_targets:
                return max(opponent_targets, key=lambda target: target.player.total_score)
            else:
                return self_target

        # Choose opponent with highest current round score; if impossible, choose self
        case ActionType.FLIP_THREE:
            if opponent_targets:
                return max(opponent_targets, key=lambda target: (target.player.current_round_score, target.player.total_score))
            else:
                return self_target

    raise ValueError(
        f"Unsupported action type: {action_type!r}"
    )