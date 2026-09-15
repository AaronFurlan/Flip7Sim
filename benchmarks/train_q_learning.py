import argparse

from flip7.agents.algorithmic_numbers_only_agent import AlgorithmicNumbersOnlyAgent
from flip7.agents.rl_agent import QLearningAgent
from flip7.agents.threshold_agent import SimpleThresholdAgent
from flip7.rl.environment import train


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default="q_table.json")
    args = parser.parse_args()

    learner = QLearningAgent("Quinn", seed=args.seed)

    train(
        learner,
        opponent_factory=lambda: [
            SimpleThresholdAgent("Conny"),
            AlgorithmicNumbersOnlyAgent("Rainman"),
        ],
        games=args.games,
        seed=args.seed,
    )

    learner.save(args.output)
    print(f"Saved Q-table with {len(learner.hit_values)} states to {args.output}")


if __name__ == "__main__":
    main()