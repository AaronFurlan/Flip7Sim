from dataclasses import replace
import pytest

from flip7.agents.base_agent import (
    AgentObservation,
    PlayerObservation,
    TargetOption,
    TurnDecision,
)
from flip7.agents.random_agent import RandomAgent
from flip7.game.cards import ActionType


def create_observation() -> AgentObservation:
    own_player = PlayerObservation(
        player_name="Alice",
        total_score=40,
        current_round_score=16,
        number_of_unique_numbers=3,
        is_active=True,
        has_second_chance=False,
    )

    opponents = (
        PlayerObservation(
            player_name="Bob",
            total_score=60,
            current_round_score=22,
            number_of_unique_numbers=4,
            is_active=True,
            has_second_chance=False,
        ),
        PlayerObservation(
            player_name="Charlie",
            total_score=30,
            current_round_score=10,
            number_of_unique_numbers=2,
            is_active=True,
            has_second_chance=True,
        ),
    )

    return AgentObservation(
        own_player=own_player,
        other_players=opponents,
        remaining_card_count=55,
        winning_score=200,
    )


def create_targets(
    observation: AgentObservation,
) -> tuple[TargetOption, ...]:
    return (
        TargetOption(
            player_index=1,
            player=observation.other_players[0],
        ),
        TargetOption(
            player_index=2,
            player=observation.other_players[1],
        ),
    )


def test_random_agent_returns_valid_turn_decision() -> None:
    agent = RandomAgent("Alice", seed=42)
    observation = create_observation()

    decision = agent.choose_hit_or_stay(observation)

    assert decision in (
        TurnDecision.HIT,
        TurnDecision.STAY,
    )


def test_random_agent_returns_valid_target() -> None:
    agent = RandomAgent("Alice", seed=42)
    observation = create_observation()
    valid_targets = create_targets(observation)

    chosen_target = agent.choose_action_target(
        observation=observation,
        action_type=ActionType.FREEZE,
        valid_targets=valid_targets,
    )

    assert chosen_target in valid_targets


def test_random_agent_rejects_empty_targets() -> None:
    agent = RandomAgent("Alice", seed=42)
    observation = create_observation()

    with pytest.raises(
        ValueError,
        match="at least one valid target",
    ):
        agent.choose_action_target(
            observation=observation,
            action_type=ActionType.FREEZE,
            valid_targets=(),
        )


def test_same_seed_produces_same_turn_decisions() -> None:
    first_agent = RandomAgent("Alice", seed=123)
    second_agent = RandomAgent("Alice", seed=123)
    observation = create_observation()

    first_decisions = tuple(
        first_agent.choose_hit_or_stay(observation)
        for _ in range(20)
    )
    second_decisions = tuple(
        second_agent.choose_hit_or_stay(observation)
        for _ in range(20)
    )

    assert first_decisions == second_decisions


def test_same_seed_produces_same_target_decisions() -> None:
    first_agent = RandomAgent("Alice", seed=123)
    second_agent = RandomAgent("Alice", seed=123)
    observation = create_observation()
    valid_targets = create_targets(observation)

    first_targets = tuple(
        first_agent.choose_action_target(
            observation,
            ActionType.FREEZE,
            valid_targets,
        )
        for _ in range(20)
    )
    second_targets = tuple(
        second_agent.choose_action_target(
            observation,
            ActionType.FREEZE,
            valid_targets,
        )
        for _ in range(20)
    )

    assert first_targets == second_targets

def test_random_agent_respects_valid_turn_decisions() -> None:
    agent = RandomAgent("Alice", seed=42)

    observation = replace(
        create_observation(),
        valid_turn_decisions=(TurnDecision.HIT,),
    )

    decisions = tuple(
        agent.choose_hit_or_stay(observation)
        for _ in range(20)
    )

    assert decisions == (TurnDecision.HIT,) * 20


def test_random_agent_rejects_empty_turn_decisions() -> None:
    agent = RandomAgent("Alice", seed=42)

    observation = replace(
        create_observation(),
        valid_turn_decisions=(),
    )

    with pytest.raises(
        ValueError,
        match="valid turn decision",
    ):
        agent.choose_hit_or_stay(observation)