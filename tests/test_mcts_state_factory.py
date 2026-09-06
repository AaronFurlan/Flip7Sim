import pytest

from flip7.agents.base_agent import (
    AgentObservation,
    DeckCardObservation,
    PendingActionObservation,
    PlayerObservation,
    TurnDecision,
)
from flip7.game.cards import (
    ActionType,
    NumberCard,
)
from flip7.mcts.state import SearchDecisionPhase
from flip7.mcts.state_factory import (
    create_card_count_dictionary,
    create_search_player_state,
    create_search_state,
)


def create_player_observation(
    player_index: int | None,
    player_name: str,
    *,
    total_score: int = 0,
    round_cards: tuple[NumberCard, ...] = (),
) -> PlayerObservation:
    return PlayerObservation(
        player_name=player_name,
        total_score=total_score,
        current_round_score=0,
        number_of_unique_numbers=len(round_cards),
        is_active=True,
        has_second_chance=False,
        round_cards=round_cards,
        player_index=player_index,
    )


def create_observation(
    **overrides: object,
) -> AgentObservation:
    arguments: dict[str, object] = {
        "own_player": create_player_observation(
            1,
            "Bob",
            total_score=40,
            round_cards=(NumberCard(4),),
        ),
        "other_players": (
            create_player_observation(
                0,
                "Alice",
                total_score=25,
            ),
        ),
        "remaining_card_count": 3,
        "winning_score": 150,
        "valid_turn_decisions": (
            TurnDecision.HIT,
            TurnDecision.STAY,
        ),
        "deck_card_counts": (
            DeckCardObservation(NumberCard(1), 1),
            DeckCardObservation(NumberCard(2), 2),
        ),
        "discarded_card_counts": (
            DeckCardObservation(NumberCard(3), 1),
        ),
        "queued_actions": (
            PendingActionObservation(
                source_player_index=0,
                action_type=ActionType.FREEZE,
            ),
        ),
        "own_player_index": 1,
        "next_starting_player_index": 0,
    }
    arguments.update(overrides)
    return AgentObservation(**arguments)  # type: ignore[arg-type]


def test_create_search_player_state_maps_observation() -> None:
    observation = create_player_observation(
        2,
        "Charlie",
        total_score=80,
        round_cards=(NumberCard(7),),
    )

    state = create_search_player_state(observation)

    assert state.player_index == 2
    assert state.player_name == "Charlie"
    assert state.total_score == 80
    assert state.round_cards == [NumberCard(7)]
    assert state.round_cards is not observation.round_cards


def test_search_player_requires_index() -> None:
    observation = create_player_observation(
        None,
        "Alice",
    )

    with pytest.raises(
        ValueError,
        match="requires a player index",
    ):
        create_search_player_state(observation)


def test_create_card_count_dictionary_maps_counts() -> None:
    observations = (
        DeckCardObservation(NumberCard(1), 1),
        DeckCardObservation(NumberCard(2), 2),
    )

    assert create_card_count_dictionary(observations) == {
        NumberCard(1): 1,
        NumberCard(2): 2,
    }


def test_card_count_dictionary_rejects_duplicate_card() -> None:
    observations = (
        DeckCardObservation(NumberCard(4), 1),
        DeckCardObservation(NumberCard(4), 0),
    )

    with pytest.raises(
        ValueError,
        match="occurs more than once",
    ):
        create_card_count_dictionary(observations)


def test_create_turn_search_state() -> None:
    state = create_search_state(create_observation())

    assert [player.player_index for player in state.players] == [0, 1]
    assert [player.player_name for player in state.players] == [
        "Alice",
        "Bob",
    ]
    assert state.current_player_index == 1
    assert state.root_player_index == 1
    assert state.next_starting_player_index == 0
    assert state.winning_score == 150
    assert state.decision_phase is SearchDecisionPhase.TURN
    assert state.pending_action is None
    assert state.remaining_card_counts == {
        NumberCard(1): 1,
        NumberCard(2): 2,
    }
    assert state.discarded_card_counts == {
        NumberCard(3): 1,
    }
    assert len(state.queued_actions) == 1
    assert state.queued_actions[0].source_player_index == 0
    assert (
        state.queued_actions[0].action_type
        is ActionType.FREEZE
    )


def test_create_action_target_search_state() -> None:
    state = create_search_state(
        create_observation(),
        pending_action_type=ActionType.FLIP_THREE,
    )

    assert (
        state.decision_phase
        is SearchDecisionPhase.ACTION_TARGET
    )
    assert state.pending_action is not None
    assert state.pending_action.source_player_index == 1
    assert (
        state.pending_action.action_type
        is ActionType.FLIP_THREE
    )


def test_search_state_does_not_share_mutable_collections() -> None:
    observation = create_observation()
    state = create_search_state(observation)

    state.players[1].round_cards.append(NumberCard(8))
    state.remaining_card_counts[NumberCard(1)] = 0
    state.discarded_card_counts[NumberCard(3)] = 0

    assert observation.own_player.round_cards == (
        NumberCard(4),
    )
    assert observation.deck_card_counts[0].remaining_count == 1
    assert (
        observation.discarded_card_counts[0].remaining_count
        == 1
    )


def test_search_state_rejects_mismatched_own_player_index() -> None:
    observation = create_observation(
        own_player_index=0,
    )

    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        create_search_state(observation)


def test_search_state_rejects_other_player_without_index() -> None:
    observation = create_observation(
        other_players=(
            create_player_observation(None, "Alice"),
        ),
    )

    with pytest.raises(
        ValueError,
        match="requires a player index",
    ):
        create_search_state(observation)


def test_search_state_rejects_incomplete_card_counts() -> None:
    observation = create_observation(
        remaining_card_count=4,
    )

    with pytest.raises(
        ValueError,
        match="do not match",
    ):
        create_search_state(observation)


def test_state_factory_functions_are_publicly_exported() -> None:
    from flip7.mcts import (
        create_card_count_dictionary as exported_count_factory,
        create_search_player_state as exported_player_factory,
        create_search_state as exported_state_factory,
    )

    assert exported_count_factory is create_card_count_dictionary
    assert exported_player_factory is create_search_player_state
    assert exported_state_factory is create_search_state
