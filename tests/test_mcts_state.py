from copy import deepcopy

import pytest

from flip7.game.cards import (
    ActionType,
    ModifierCard,
    ModifierType,
    NumberCard,
)
from flip7.mcts.state import (
    Flip7SearchState,
    SearchDecisionPhase,
    SearchPendingAction,
    SearchPlayerState,
)


def create_players() -> list[SearchPlayerState]:
    return [
        SearchPlayerState(
            player_index=0,
            player_name="Alice",
        ),
        SearchPlayerState(
            player_index=1,
            player_name="Bob",
        ),
    ]


def create_state(**overrides: object) -> Flip7SearchState:
    arguments: dict[str, object] = {
        "players": create_players(),
        "remaining_card_counts": {NumberCard(1): 1},
        "discarded_card_counts": {},
        "current_player_index": 0,
        "root_player_index": 0,
        "next_starting_player_index": 1,
        "winning_score": 200,
    }
    arguments.update(overrides)
    return Flip7SearchState(**arguments)  # type: ignore[arg-type]


def test_create_valid_turn_state() -> None:
    state = create_state()

    assert state.current_player_index == 0
    assert state.root_player_index == 0
    assert state.decision_phase is SearchDecisionPhase.TURN
    assert state.pending_action is None
    assert not state.round_finished
    assert not state.game_finished


def test_player_state_detects_number_card() -> None:
    player = SearchPlayerState(
        player_index=0,
        player_name="Alice",
        round_cards=[
            NumberCard(7),
            ModifierCard(ModifierType.ADDITIVE, 4),
        ],
    )

    assert player.has_number(7)
    assert not player.has_number(4)


def test_deepcopy_is_independent() -> None:
    original = create_state()
    copied = deepcopy(original)

    copied.players[0].total_score = 50
    copied.players[0].round_cards.append(NumberCard(4))
    copied.remaining_card_counts[NumberCard(1)] = 0
    copied.discarded_card_counts[NumberCard(2)] = 2

    assert original.players[0].total_score == 0
    assert original.players[0].round_cards == []
    assert original.remaining_card_counts[NumberCard(1)] == 1
    assert original.discarded_card_counts == {}


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("current_player_index", 2),
        ("root_player_index", 2),
        ("next_starting_player_index", 2),
    ],
)
def test_state_rejects_out_of_range_player_index(
    field_name: str,
    field_value: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="player index is out of range",
    ):
        create_state(**{field_name: field_value})


def test_state_rejects_non_contiguous_player_indices() -> None:
    players = create_players()
    players[1].player_index = 2

    with pytest.raises(
        ValueError,
        match="unique and contiguous",
    ):
        create_state(players=players)


@pytest.mark.parametrize(
    "counts_field",
    ["remaining_card_counts", "discarded_card_counts"],
)
def test_state_rejects_negative_card_count(
    counts_field: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        create_state(
            **{counts_field: {NumberCard(1): -1}}
        )


def test_action_target_phase_requires_pending_action() -> None:
    with pytest.raises(
        ValueError,
        match="requires a pending action",
    ):
        create_state(
            decision_phase=SearchDecisionPhase.ACTION_TARGET,
        )


def test_turn_phase_rejects_pending_action() -> None:
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FREEZE,
    )

    with pytest.raises(
        ValueError,
        match="cannot have a pending action",
    ):
        create_state(pending_action=pending_action)


def test_create_valid_action_target_state() -> None:
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FLIP_THREE,
    )

    state = create_state(
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
    )

    assert state.pending_action == pending_action


def test_state_rejects_out_of_range_pending_action_source() -> None:
    pending_action = SearchPendingAction(
        source_player_index=2,
        action_type=ActionType.FREEZE,
    )

    with pytest.raises(
        ValueError,
        match="source index is out of range",
    ):
        create_state(
            decision_phase=SearchDecisionPhase.ACTION_TARGET,
            pending_action=pending_action,
        )


def test_pending_action_rejects_negative_source_index() -> None:
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        SearchPendingAction(
            source_player_index=-1,
            action_type=ActionType.FREEZE,
        )


@pytest.mark.parametrize("winning_score", [0, -1])
def test_state_rejects_non_positive_winning_score(
    winning_score: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="must be positive",
    ):
        create_state(winning_score=winning_score)


def test_finished_game_requires_finished_round() -> None:
    with pytest.raises(
        ValueError,
        match="must also have a finished round",
    ):
        create_state(game_finished=True)


@pytest.mark.parametrize(
    "player",
    [
        SearchPlayerState(
            player_index=0,
            player_name="Alice",
            is_active=False,
            has_stayed=True,
        ),
        SearchPlayerState(
            player_index=0,
            player_name="Alice",
            is_active=False,
            has_busted=True,
        ),
    ],
)
def test_inactive_player_may_be_stayed_or_busted(
    player: SearchPlayerState,
) -> None:
    assert not player.is_active


@pytest.mark.parametrize(
    "status_field",
    ["has_stayed", "has_busted"],
)
def test_active_player_rejects_terminal_round_status(
    status_field: str,
) -> None:
    arguments = {
        "player_index": 0,
        "player_name": "Alice",
        status_field: True,
    }

    with pytest.raises(
        ValueError,
        match="cannot be active",
    ):
        SearchPlayerState(**arguments)  # type: ignore[arg-type]
