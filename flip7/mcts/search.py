from collections.abc import Hashable
from copy import deepcopy
from math import inf, log, sqrt
from random import Random
from typing import Generic, TypeVar

from flip7.mcts.model import SearchModel
from flip7.mcts.node import MCTSNode


StateType = TypeVar("StateType")
ActionType = TypeVar("ActionType", bound=Hashable)


def calculate_ucb1_score(
    node: MCTSNode[ActionType],
    exploration_weight: float,
) -> float:
    if node.parent is None:
        raise ValueError(
            "The root node has no UCB1 score."
        )

    if exploration_weight < 0:
        raise ValueError(
            "The exploration weight cannot be negative."
        )

    if node.visits == 0:
        return inf

    if node.parent.visits == 0:
        raise ValueError(
            "The parent node must have been visited."
        )

    exploration_score = exploration_weight * sqrt(
        log(node.parent.visits) / node.visits
    )

    return node.average_reward + exploration_score


def select_child(
    node: MCTSNode[ActionType],
    valid_actions: tuple[ActionType, ...],
    exploration_weight: float,
    random_generator: Random,
) -> MCTSNode[ActionType]:
    if not valid_actions:
        raise ValueError(
            "At least one valid action is required."
        )

    best_score = -inf
    best_children: list[MCTSNode[ActionType]] = []

    for action in valid_actions:
        if action not in node.children:
            raise ValueError(
                "Every valid action must be expanded "
                "before selecting a child."
            )

        child = node.children[action]

        score = calculate_ucb1_score(
            node=child,
            exploration_weight=exploration_weight,
        )

        if score > best_score:
            best_score = score
            best_children = [child]

        elif score == best_score:
            best_children.append(child)

    return random_generator.choice(best_children)

class MCTSSearch(Generic[StateType, ActionType]):
    def __init__(
        self,
        model: SearchModel[StateType, ActionType],
        simulations: int = 500,
        exploration_weight: float = 1.414,
        max_depth: int = 100,
        seed: int | None = None,
    ) -> None:
        if simulations <= 0:
            raise ValueError(
                "The number of simulations must be positive."
            )

        if exploration_weight < 0:
            raise ValueError(
                "The exploration weight cannot be negative."
            )

        if max_depth <= 0:
            raise ValueError(
                "The maximum search depth must be positive."
            )

        self.model = model
        self.simulations = simulations
        self.exploration_weight = exploration_weight
        self.max_depth = max_depth
        self.random_generator = Random(seed)

    def find_best_action(
        self,
        initial_state: StateType,
    ) -> ActionType:
        valid_actions = self.model.get_valid_actions(
            initial_state
        )

        if not valid_actions:
            raise ValueError(
                "The initial state has no valid actions."
            )

        if len(valid_actions) == 1:
            return valid_actions[0]

        if self.simulations < len(valid_actions):
            raise ValueError(
                "The number of simulations must be at least "
                "the number of valid root actions."
            )

        root: MCTSNode[ActionType] = MCTSNode()

        for _ in range(self.simulations):
            self._run_iteration(
                root=root,
                initial_state=initial_state,
            )

        return self._get_most_visited_action(
            root=root,
            valid_actions=valid_actions,
        )

    def _run_iteration(
        self,
        root: MCTSNode[ActionType],
        initial_state: StateType,
    ) -> None:
        node = root
        state = deepcopy(initial_state)
        visited_nodes = [root]
        depth = 0

        while (
            depth < self.max_depth
            and not self.model.is_terminal(state)
        ):
            valid_actions = (
                self.model.get_valid_actions(state)
            )

            if not valid_actions:
                raise RuntimeError(
                    "A non-terminal state has no valid actions."
                )

            untried_actions = node.get_untried_actions(
                valid_actions
            )

            if untried_actions:
                action = self.random_generator.choice(
                    untried_actions
                )
                node = node.add_child(action)

                state = self.model.sample_transition(
                    state=state,
                    action=action,
                    random_generator=self.random_generator,
                )

                visited_nodes.append(node)
                depth += 1
                break

            selected_child = select_child(
                node=node,
                valid_actions=valid_actions,
                exploration_weight=self.exploration_weight,
                random_generator=self.random_generator,
            )

            action = selected_child.action

            if action is None:
                raise RuntimeError(
                    "A child node must contain an action."
                )

            state = self.model.sample_transition(
                state=state,
                action=action,
                random_generator=self.random_generator,
            )

            node = selected_child
            visited_nodes.append(node)
            depth += 1

        while (
            depth < self.max_depth
            and not self.model.is_terminal(state)
        ):
            valid_actions = (
                self.model.get_valid_actions(state)
            )

            if not valid_actions:
                raise RuntimeError(
                    "A non-terminal state has no valid actions."
                )

            action = self.random_generator.choice(
                valid_actions
            )

            state = self.model.sample_transition(
                state=state,
                action=action,
                random_generator=self.random_generator,
            )

            depth += 1

        reward = self.model.get_reward(state)

        for visited_node in visited_nodes:
            visited_node.update(reward)

    def _get_most_visited_action(
        self,
        root: MCTSNode[ActionType],
        valid_actions: tuple[ActionType, ...],
    ) -> ActionType:
        best_child: MCTSNode[ActionType] | None = None

        for action in valid_actions:
            child = root.children.get(action)

            if child is None:
                continue

            if best_child is None:
                best_child = child
                continue

            if child.visits > best_child.visits:
                best_child = child

            elif (
                child.visits == best_child.visits
                and child.average_reward
                > best_child.average_reward
            ):
                best_child = child

        if best_child is None or best_child.action is None:
            raise RuntimeError(
                "The search did not expand any root action."
            )

        return best_child.action
