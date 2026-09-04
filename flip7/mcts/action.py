from dataclasses import dataclass
from enum import StrEnum


class SearchActionType(StrEnum):
    HIT = "hit"
    STAY = "stay"
    ACTION_TARGET = "action_target"


@dataclass(frozen=True, slots=True)
class Flip7SearchAction:
    action_type: SearchActionType
    target_player_index: int | None = None

    def __post_init__(self) -> None:
        if self.action_type is SearchActionType.ACTION_TARGET:
            if self.target_player_index is None:
                raise ValueError("A target action requires a player index.")

            if self.target_player_index < 0:
                raise ValueError("The target player index cannot be negative.")

            return

        if self.target_player_index is not None:
            raise ValueError("Hit and stay actions cannot contain a target.")