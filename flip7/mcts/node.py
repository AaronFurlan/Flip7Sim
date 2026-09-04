from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass, field
from typing import Generic, TypeVar


ActionType = TypeVar("ActionType", bound=Hashable)


@dataclass(slots=True)
class MCTSNode(Generic[ActionType]):
    parent: MCTSNode[ActionType] | None = None
    action: ActionType | None = None

    visits: int = 0
    total_reward: float = 0.0

    children: dict[
        ActionType,
        MCTSNode[ActionType],
    ] = field(default_factory=dict)

    @property
    def average_reward(self) -> float:
        if self.visits == 0:
            return 0.0

        return self.total_reward / self.visits

    def get_untried_actions(
        self,
        valid_actions: tuple[ActionType, ...],
    ) -> tuple[ActionType, ...]:
        return tuple(
            action
            for action in valid_actions
            if action not in self.children
        )

    def add_child(
        self,
        action: ActionType,
    ) -> MCTSNode[ActionType]:
        if action in self.children:
            raise ValueError(
                "A child for this action already exists."
            )

        child = MCTSNode(
            parent=self,
            action=action,
        )
        self.children[action] = child

        return child

    def update(self, reward: float) -> None:
        self.visits += 1
        self.total_reward += reward
