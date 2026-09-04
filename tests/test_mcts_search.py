from math import inf, log, sqrt
from random import Random
from dataclasses import dataclass

import pytest

from flip7.mcts.node import MCTSNode
from flip7.mcts.search import (
    calculate_ucb1_score,
    select_child,
)
from flip7.mcts.search import MCTSSearch


def test_unvisited_node_has_infinite_ucb1_score() -> None:
    parent = MCTSNode(visits=1)
    child = parent.add_child("hit")

    score = calculate_ucb1_score(
        node=child,
        exploration_weight=1.414,
    )

    assert score == inf


def test_ucb1_score_uses_reward_and_exploration() -> None:
    parent = MCTSNode(visits=10)
    child = parent.add_child("hit")
    child.visits = 2
    child.total_reward = 1.0

    score = calculate_ucb1_score(
        node=child,
        exploration_weight=1.414,
    )

    expected_score = 0.5 + 1.414 * sqrt(
        log(10) / 2
    )

    assert score == pytest.approx(expected_score)


def test_select_child_prefers_higher_ucb1_score() -> None:
    parent = MCTSNode(visits=20)

    hit_child = parent.add_child("hit")
    hit_child.visits = 10
    hit_child.total_reward = 8.0

    stay_child = parent.add_child("stay")
    stay_child.visits = 10
    stay_child.total_reward = 3.0

    selected_child = select_child(
        node=parent,
        valid_actions=("hit", "stay"),
        exploration_weight=1.414,
        random_generator=Random(42),
    )

    assert selected_child is hit_child


def test_select_child_rejects_unexpanded_action() -> None:
    parent = MCTSNode(visits=1)
    parent.add_child("hit")

    with pytest.raises(
        ValueError,
        match="must be expanded",
    ):
        select_child(
            node=parent,
            valid_actions=("hit", "stay"),
            exploration_weight=1.414,
            random_generator=Random(42),
        )

class ImmediateRewardModel:
    def get_valid_actions(
        self,
        state: tuple[bool, float],
    ) -> tuple[str, ...]:
        is_terminal, _ = state

        if is_terminal:
            return ()

        return ("bad", "good")

    def sample_transition(
        self,
        state: tuple[bool, float],
        action: str,
        random_generator: Random,
    ) -> tuple[bool, float]:
        if action == "good":
            return (True, 1.0)

        return (True, 0.0)

    def is_terminal(
        self,
        state: tuple[bool, float],
    ) -> bool:
        is_terminal, _ = state
        return is_terminal

    def get_reward(
        self,
        state: tuple[bool, float],
    ) -> float:
        _, reward = state
        return reward

def test_mcts_selects_action_with_higher_reward() -> None:
    search = MCTSSearch(
        model=ImmediateRewardModel(),
        simulations=100,
        seed=42,
    )

    selected_action = search.find_best_action(
        initial_state=(False, 0.0)
    )

    assert selected_action == "good"


def test_mcts_rejects_state_without_actions() -> None:
    search = MCTSSearch(
        model=ImmediateRewardModel(),
        simulations=10,
        seed=42,
    )

    with pytest.raises(
        ValueError,
        match="no valid actions",
    ):
        search.find_best_action(
            initial_state=(True, 1.0)
        )


def test_mcts_rejects_invalid_configuration() -> None:
    with pytest.raises(
        ValueError,
        match="simulations must be positive",
    ):
        MCTSSearch(
            model=ImmediateRewardModel(),
            simulations=0,
        )


def test_mcts_requires_one_simulation_per_root_action() -> None:
    search = MCTSSearch(
        model=ImmediateRewardModel(),
        simulations=1,
    )

    with pytest.raises(
        ValueError,
        match="at least the number of valid root actions",
    ):
        search.find_best_action((False, 0.0))


@dataclass
class MutableState:
    is_terminal: bool = False
    reward: float = 0.0


class MutatingModel:
    def get_valid_actions(
        self,
        state: MutableState,
    ) -> tuple[str, ...]:
        if state.is_terminal:
            return ()

        return ("bad", "good")

    def sample_transition(
        self,
        state: MutableState,
        action: str,
        random_generator: Random,
    ) -> MutableState:
        state.is_terminal = True
        state.reward = 1.0 if action == "good" else 0.0
        return state

    def is_terminal(self, state: MutableState) -> bool:
        return state.is_terminal

    def get_reward(self, state: MutableState) -> float:
        return state.reward


def test_mcts_does_not_mutate_initial_state() -> None:
    initial_state = MutableState()
    search = MCTSSearch(
        model=MutatingModel(),
        simulations=10,
        seed=42,
    )

    assert search.find_best_action(initial_state) == "good"
    assert initial_state == MutableState()
