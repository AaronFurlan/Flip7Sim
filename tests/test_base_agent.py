from dataclasses import FrozenInstanceError

import pytest

from flip7.agents.base_agent import (
    AgentObservation,
    BaseAgent,
    PlayerObservation,
    TargetOption,
    TurnDecision,
)
from flip7.game.cards import ActionType


class IncompleteAgent(BaseAgent):
    def choose_hit_or_stay(
        self,
        observation: AgentObservation,
    ) -> TurnDecision:
        return TurnDecision.HIT


class StubAgent(BaseAgent):
    def choose_hit_or_stay(
        self,
        observation: AgentObservation,
    ) -> TurnDecision:
        return TurnDecision.STAY

    def choose_action_target(
        self,
        observation: AgentObservation,
        action_type: ActionType,
        valid_targets: tuple[TargetOption, ...],
    ) -> TargetOption:
        return valid_targets[0]


def create_observation() -> AgentObservation:
    own_player = PlayerObservation(
        player_name="Alice",
        total_score=50,
        current_round_score=18,
        number_of_unique_numbers=3,
        is_active=True,
        has_second_chance=False,
    )

    opponent = PlayerObservation(
        player_name="Bob",
        total_score=70,
        current_round_score=25,
        number_of_unique_numbers=4,
        is_active=True,
        has_second_chance=True,
    )

    return AgentObservation(
        own_player=own_player,
        other_players=(opponent,),
        remaining_card_count=60,
        winning_score=200,
    )


def test_base_agent_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        BaseAgent("Alice")


def test_incomplete_agent_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        IncompleteAgent("Alice")


def test_agent_name_must_not_be_empty() -> None:
    with pytest.raises(ValueError):
        StubAgent("   ")


def test_concrete_agent_can_choose_turn_decision() -> None:
    agent = StubAgent("Alice")
    observation = create_observation()

    decision = agent.choose_hit_or_stay(observation)

    assert decision is TurnDecision.STAY


def test_concrete_agent_can_choose_action_target() -> None:
    agent = StubAgent("Alice")
    observation = create_observation()

    target = TargetOption(
        player_index=1,
        player=observation.other_players[0],
    )

    chosen_target = agent.choose_action_target(
        observation=observation,
        action_type=ActionType.FREEZE,
        valid_targets=(target,),
    )

    assert chosen_target is target


def test_agent_observation_is_immutable() -> None:
    observation = create_observation()

    with pytest.raises(FrozenInstanceError):
        setattr(observation, "remaining_card_count", 10)
