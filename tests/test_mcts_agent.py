import pytest

from flip7.agents.base_agent import (
    AgentObservation,
    DeckCardObservation,
    PlayerObservation,
    TargetOption,
    TurnDecision,
)
from flip7.agents.mcts_agent import MCTSAgent
from flip7.game.cards import (
    ActionType,
    NumberCard,
)


def create_player_observation(
        player_index: int,
        player_name: str,
        *,
        round_cards: tuple[NumberCard, ...] = (),
        total_score: int = 0,
        is_active: bool = True,
        has_second_chance: bool = False,
) -> PlayerObservation:
    return PlayerObservation(
        player_name=player_name,
        total_score=total_score,
        current_round_score=sum(
            card.number for card in round_cards
        ),
        number_of_unique_numbers=len({
            card.number for card in round_cards
        }),
        is_active=is_active,
        has_second_chance=has_second_chance,
        round_cards=round_cards,
        player_index=player_index,
    )


def create_observation(
        *,
        own_cards: tuple[NumberCard, ...] = (),
        other_cards: tuple[NumberCard, ...] = (
            NumberCard(11),
            NumberCard(12),
        ),
) -> AgentObservation:
    own_player = create_player_observation(
        0,
        "Alice",
        round_cards=own_cards,
    )
    other_player = create_player_observation(
        1,
        "Bob",
        round_cards=other_cards,
    )
    deck_card_counts = tuple(
        DeckCardObservation(NumberCard(number), 2)
        for number in range(13)
    )

    return AgentObservation(
        own_player=own_player,
        other_players=(other_player,),
        remaining_card_count=26,
        winning_score=100,
        valid_turn_decisions=(
            TurnDecision.HIT,
            TurnDecision.STAY,
        ),
        deck_card_counts=deck_card_counts,
        own_player_index=0,
        next_starting_player_index=1,
    )


def test_mcts_agent_hits_when_hit_is_only_action() -> None:
    agent = MCTSAgent(
        "Alice",
        simulations=10,
        max_depth=5,
        seed=42,
    )

    decision = agent.choose_hit_or_stay(
        create_observation(own_cards=())
    )

    assert decision is TurnDecision.HIT


def test_mcts_agent_returns_valid_turn_decision() -> None:
    agent = MCTSAgent(
        "Alice",
        simulations=30,
        max_depth=8,
        seed=42,
    )

    decision = agent.choose_hit_or_stay(
        create_observation(
            own_cards=(NumberCard(5),)
        )
    )

    assert decision in (
        TurnDecision.HIT,
        TurnDecision.STAY,
    )


def test_mcts_agent_returns_only_valid_target() -> None:
    own_player = create_player_observation(
        0,
        "Alice",
        round_cards=(NumberCard(5),),
        has_second_chance=True,
    )
    other_player = create_player_observation(
        1,
        "Bob",
        round_cards=(NumberCard(7),),
    )
    observation = AgentObservation(
        own_player=own_player,
        other_players=(other_player,),
        remaining_card_count=1,
        winning_score=100,
        deck_card_counts=(
            DeckCardObservation(NumberCard(1), 1),
        ),
        own_player_index=0,
        next_starting_player_index=1,
    )
    expected_target = TargetOption(
        player_index=1,
        player=other_player,
    )
    agent = MCTSAgent(
        "Alice",
        simulations=10,
        max_depth=5,
        seed=42,
    )

    selected_target = agent.choose_action_target(
        observation=observation,
        action_type=ActionType.SECOND_CHANCE,
        valid_targets=(expected_target,),
    )

    assert selected_target is expected_target


def test_mcts_agent_requires_valid_target() -> None:
    agent = MCTSAgent(
        "Alice",
        simulations=10,
        max_depth=5,
        seed=42,
    )

    with pytest.raises(
        ValueError,
        match="requires at least one valid target",
    ):
        agent.choose_action_target(
            observation=create_observation(
                own_cards=(NumberCard(5),)
            ),
            action_type=ActionType.FREEZE,
            valid_targets=(),
        )


def test_mcts_agent_validates_search_configuration() -> None:
    with pytest.raises(
        ValueError,
        match="simulations must be positive",
    ):
        MCTSAgent("Alice", simulations=0)


def test_mcts_agent_is_publicly_exported() -> None:
    from flip7.agents import MCTSAgent as ExportedAgent

    assert ExportedAgent is MCTSAgent
