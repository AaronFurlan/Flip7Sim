from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from flip7.agents.mcts_agent import MCTSAgent


__all__ = ["MCTSAgent"]


def __getattr__(name: str) -> Any:
    if name == "MCTSAgent":
        from flip7.agents.mcts_agent import MCTSAgent

        return MCTSAgent

    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )
