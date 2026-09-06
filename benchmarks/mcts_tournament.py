import argparse
from dataclasses import dataclass
from time import perf_counter

from flip7.agents import MCTSAgent
from flip7.agents.threshold_agent import SimpleThresholdAgent
from flip7.simulation.simulator import GameSimulation


@dataclass(slots=True)
class TournamentResult:
    games: int = 0
    mcts_wins: int = 0
    threshold_wins: int = 0
    ties: int = 0
    mcts_score_total: int = 0
    threshold_score_total: int = 0
    rounds_total: int = 0
    elapsed_seconds: float = 0.0

    def record_game(
            self,
            mcts_score: int,
            threshold_score: int,
            rounds: int,
    ) -> None:
        self.games += 1
        self.mcts_score_total += mcts_score
        self.threshold_score_total += threshold_score
        self.rounds_total += rounds

        if mcts_score > threshold_score:
            self.mcts_wins += 1
        elif threshold_score > mcts_score:
            self.threshold_wins += 1
        else:
            self.ties += 1

    @property
    def mcts_win_rate(self) -> float:
        return self.mcts_wins / self.games

    @property
    def average_mcts_score(self) -> float:
        return self.mcts_score_total / self.games

    @property
    def average_threshold_score(self) -> float:
        return self.threshold_score_total / self.games

    @property
    def average_score_difference(self) -> float:
        return (
            self.mcts_score_total
            - self.threshold_score_total
        ) / self.games

    @property
    def average_rounds(self) -> float:
        return self.rounds_total / self.games


def run_tournament(
        games: int,
        simulations: int,
        exploration_weight: float,
        max_depth: int,
        winning_score: int,
        seed: int,
) -> TournamentResult:
    if games <= 0:
        raise ValueError(
            "The number of tournament games must be positive."
        )

    result = TournamentResult()
    started_at = perf_counter()

    for game_number in range(games):
        game_seed = seed + game_number
        simulated_opponent = SimpleThresholdAgent(
            "Simulated Threshold"
        )
        rollout_agent = SimpleThresholdAgent(
            "Rollout Threshold"
        )
        mcts_agent = MCTSAgent(
            "Monte",
            simulations=simulations,
            exploration_weight=exploration_weight,
            max_depth=max_depth,
            seed=seed + 10_000 + game_number,
            opponent_agent=simulated_opponent,
            rollout_agent=rollout_agent,
        )
        threshold_agent = SimpleThresholdAgent("Threshold")

        if game_number % 2 == 0:
            agents = [mcts_agent, threshold_agent]
        else:
            agents = [threshold_agent, mcts_agent]

        simulation = GameSimulation(
            agents=agents,
            winning_score=winning_score,
            seed=game_seed,
        )
        simulation.run()

        scores = {
            player.player_name: player.total_score
            for player in simulation.players
        }

        result.record_game(
            mcts_score=scores["Monte"],
            threshold_score=scores["Threshold"],
            rounds=simulation.rounds_played,
        )

    result.elapsed_seconds = perf_counter() - started_at
    return result


def print_result(
        result: TournamentResult,
        simulations: int,
        exploration_weight: float,
        max_depth: int,
) -> None:
    print(
        f"Configuration: simulations={simulations}, "
        f"exploration_weight={exploration_weight}, "
        f"max_depth={max_depth}"
    )
    print(f"Games: {result.games}")
    print(
        f"MCTS wins: {result.mcts_wins} "
        f"({result.mcts_win_rate:.1%})"
    )
    print(f"Threshold wins: {result.threshold_wins}")
    print(f"Ties: {result.ties}")
    print(
        f"Average scores: MCTS={result.average_mcts_score:.1f}, "
        f"Threshold={result.average_threshold_score:.1f}"
    )
    print(
        "Average score difference: "
        f"{result.average_score_difference:+.1f}"
    )
    print(f"Average rounds: {result.average_rounds:.1f}")
    print(f"Elapsed: {result.elapsed_seconds:.2f} seconds")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--simulations", type=int, default=100)
    parser.add_argument(
        "--exploration-weight",
        type=float,
        default=0.9,
    )
    parser.add_argument("--max-depth", type=int, default=30)
    parser.add_argument("--winning-score", type=int, default=100)
    parser.add_argument("--seed", type=int, default=1000)
    arguments = parser.parse_args()

    result = run_tournament(
        games=arguments.games,
        simulations=arguments.simulations,
        exploration_weight=arguments.exploration_weight,
        max_depth=arguments.max_depth,
        winning_score=arguments.winning_score,
        seed=arguments.seed,
    )
    print_result(
        result=result,
        simulations=arguments.simulations,
        exploration_weight=arguments.exploration_weight,
        max_depth=arguments.max_depth,
    )


if __name__ == "__main__":
    main()
