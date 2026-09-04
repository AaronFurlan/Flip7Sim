from collections.abc import Hashable
from random import Random
from typing import Protocol, TypeVar

StateType = TypeVar("StateType")
SearchActionType = TypeVar(
    "SearchActionType",
    bound=Hashable,
)


class SearchModel(Protocol[StateType, SearchActionType]):
    """Rules required by the generic MCTS implementation.

    ``sample_transition`` may mutate the state it receives. MCTSSearch creates
    an independent deep copy of the initial state for every iteration.
    """

    def get_valid_actions(
        self,
        state: StateType,
    ) -> tuple[SearchActionType, ...]:
        ...

    def sample_transition(
        self,
        state: StateType,
        action: SearchActionType,
        random_generator: Random,
    ) -> StateType:
        ...

    def is_terminal(self, state: StateType) -> bool:
        ...

    def get_reward(self, state: StateType) -> float:
        ...
