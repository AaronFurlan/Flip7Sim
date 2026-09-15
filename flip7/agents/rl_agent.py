import json
from pathlib import Path
from random import Random

from flip7.agents.base_agent import (
    AgentObservation,
    BaseAgent,
    TargetOption,
    TurnDecision,
)
from flip7.agents.reusable_strategies import basic_sensible_action_strategy
from flip7.game.cards import ActionType
from flip7.rl.action_space import get_valid_actions
from flip7.rl.observation import State, encode_state
from flip7.rl.reward import calculate_round_reward

# Used only for states the agent has never seen during training.
FALLBACK_STAY_THRESHOLD = 20


class QLearningAgent(BaseAgent):
    def __init__(
        self,
        player_name: str,
        *,
        min_learning_rate: float = 0.005,
        epsilon: float = 0.1,
        training: bool = True,
        seed: int | None = None,
        q_table_path: str | Path | None = None,
    ) -> None:
        super().__init__(player_name)

        self.min_learning_rate = min_learning_rate
        self.epsilon = epsilon
        self.training = training

        self._random = Random(seed)

        # Q(s, HIT). Q(s, STAY) is not learned: it is the current round score.
        self.hit_values: dict[State, float] = {}
        self.visit_counts: dict[State, int] = {}

        # Only set after a HIT, because only HIT decisions are learned.
        self._last_state: State | None = None

        if q_table_path is not None:
            self.load(q_table_path)

    def choose_hit_or_stay(self, observation: AgentObservation) -> TurnDecision:
        valid_actions = get_valid_actions(observation)

        if not valid_actions:
            raise ValueError("A Q-learning agent requires at least one valid turn decision.")

        state = encode_state(observation)
        stay_value = observation.own_player.current_round_score
        can_stay = TurnDecision.STAY in valid_actions

        if self.training:
            # The previous HIT led to this state; its value is the best option here.
            self._learn(self._best_value(state, stay_value, can_stay))

        if self.training and self._random.random() < self.epsilon:
            action = self._random.choice(valid_actions)
        else:
            action = self._greedy_action(state, stay_value, can_stay)

        if self.training and action is TurnDecision.HIT:
            self._last_state = state
        else:
            self._last_state = None

        return action

    def finish_round(self, round_score: int) -> None:
        """Must be called once after every round; delivers the terminal reward."""
        if self.training:
            self._learn(calculate_round_reward(round_score))

        self._last_state = None

    def _best_value(self, state: State, stay_value: int, can_stay: bool) -> float:
        hit_value = self.hit_values.get(state, 0.0)

        if can_stay:
            return max(hit_value, float(stay_value))

        return hit_value

    def _greedy_action(self, state: State, stay_value: int, can_stay: bool) -> TurnDecision:
        if not can_stay:
            return TurnDecision.HIT

        if state not in self.hit_values:
            if stay_value < FALLBACK_STAY_THRESHOLD:
                return TurnDecision.HIT
            return TurnDecision.STAY

        if self.hit_values[state] > stay_value:
            return TurnDecision.HIT

        return TurnDecision.STAY

    def _learn(self, target: float) -> None:
        if self._last_state is None:
            return

        state = self._last_state
        visits = self.visit_counts.get(state, 0) + 1
        self.visit_counts[state] = visits

        # 1/N turns the Q-value into a running average of all targets seen so far.
        learning_rate = max(1.0 / visits, self.min_learning_rate)

        old_value = self.hit_values.get(state, 0.0)
        self.hit_values[state] = old_value + learning_rate * (target - old_value)

    def choose_action_target(
        self,
        observation: AgentObservation,
        action_type: ActionType,
        valid_targets: tuple[TargetOption, ...],
    ) -> TargetOption:
        if not valid_targets:
            raise ValueError("A Q-learning agent requires at least one valid target.")

        return basic_sensible_action_strategy(
            action_type,
            self_target=self.find_own_target(observation, valid_targets),
            opponent_targets=self.get_opponent_targets(observation, valid_targets),
        )

    def save(self, path: str | Path) -> None:
        """Save the learned HIT values and visit counts to a JSON file."""
        data = {
            ",".join(str(value) for value in state): {
                "hit": hit_value,
                "visits": self.visit_counts.get(state, 0),
            }
            for state, hit_value in self.hit_values.items()
        }
        Path(path).write_text(json.dumps(data, indent=1), encoding="utf-8")

    def load(self, path: str | Path) -> None:
        """Load HIT values and visit counts from a JSON file."""
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        self.hit_values = {}
        self.visit_counts = {}

        for key, entry in raw.items():
            state = tuple(int(value) for value in key.split(","))
            self.hit_values[state] = entry["hit"]
            self.visit_counts[state] = entry["visits"]