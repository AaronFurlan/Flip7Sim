import pytest

from flip7.mcts.action import (
    Flip7SearchAction,
    SearchActionType,
)


def test_turn_actions_do_not_require_a_target() -> None:
    hit = Flip7SearchAction(SearchActionType.HIT)
    stay = Flip7SearchAction(SearchActionType.STAY)

    assert hit.target_player_index is None
    assert stay.target_player_index is None


def test_search_actions_are_hashable() -> None:
    action = Flip7SearchAction(
        SearchActionType.ACTION_TARGET,
        target_player_index=1,
    )

    assert {action: "selected"}[action] == "selected"


def test_target_actions_use_player_index_for_identity() -> None:
    first_target = Flip7SearchAction(
        SearchActionType.ACTION_TARGET,
        target_player_index=0,
    )
    second_target = Flip7SearchAction(
        SearchActionType.ACTION_TARGET,
        target_player_index=1,
    )

    assert first_target != second_target


def test_target_action_requires_player_index() -> None:
    with pytest.raises(
        ValueError,
        match="requires a player index",
    ):
        Flip7SearchAction(SearchActionType.ACTION_TARGET)


def test_target_action_rejects_negative_player_index() -> None:
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=-1,
        )


@pytest.mark.parametrize(
    "action_type",
    [SearchActionType.HIT, SearchActionType.STAY],
)
def test_turn_action_rejects_target(
    action_type: SearchActionType,
) -> None:
    with pytest.raises(
        ValueError,
        match="cannot contain a target",
    ):
        Flip7SearchAction(
            action_type,
            target_player_index=0,
        )
