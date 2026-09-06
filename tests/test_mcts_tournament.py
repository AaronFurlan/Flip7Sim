import pytest

from benchmarks.mcts_tournament import (
    TournamentResult,
    run_tournament,
)


def test_tournament_result_records_games() -> None:
    result = TournamentResult()

    result.record_game(100, 80, 4)
    result.record_game(90, 110, 5)
    result.record_game(100, 100, 3)

    assert result.games == 3
    assert result.mcts_wins == 1
    assert result.threshold_wins == 1
    assert result.ties == 1
    assert result.mcts_win_rate == pytest.approx(1 / 3)
    assert result.average_mcts_score == pytest.approx(290 / 3)
    assert result.average_threshold_score == pytest.approx(290 / 3)
    assert result.average_score_difference == 0
    assert result.average_rounds == 4


def test_small_tournament_completes() -> None:
    result = run_tournament(
        games=2,
        simulations=4,
        exploration_weight=0.9,
        max_depth=4,
        winning_score=20,
        seed=42,
    )

    assert result.games == 2
    assert (
        result.mcts_wins
        + result.threshold_wins
        + result.ties
    ) == 2
    assert result.elapsed_seconds >= 0


def test_tournament_requires_positive_game_count() -> None:
    with pytest.raises(
        ValueError,
        match="must be positive",
    ):
        run_tournament(
            games=0,
            simulations=4,
            exploration_weight=0.9,
            max_depth=4,
            winning_score=20,
            seed=42,
        )
