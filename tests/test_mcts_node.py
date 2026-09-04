import pytest

from flip7.mcts.node import MCTSNode


def test_new_node_has_empty_statistics() -> None:
    node = MCTSNode()

    assert node.parent is None
    assert node.action is None
    assert node.visits == 0
    assert node.total_reward == 0.0
    assert node.average_reward == 0.0
    assert node.children == {}


def test_add_child_connects_parent_and_child() -> None:
    parent = MCTSNode()

    child = parent.add_child("hit")

    assert child.parent is parent
    assert child.action == "hit"
    assert parent.children["hit"] is child


def test_duplicate_child_is_rejected() -> None:
    node = MCTSNode()
    node.add_child("hit")

    with pytest.raises(
        ValueError,
        match="already exists",
    ):
        node.add_child("hit")


def test_get_untried_actions() -> None:
    node = MCTSNode()
    node.add_child("hit")

    untried_actions = node.get_untried_actions(
        ("hit", "stay")
    )

    assert untried_actions == ("stay",)


def test_update_adds_visit_and_reward() -> None:
    node = MCTSNode()

    node.update(10.0)
    node.update(20.0)

    assert node.visits == 2
    assert node.total_reward == 30.0
    assert node.average_reward == 15.0

