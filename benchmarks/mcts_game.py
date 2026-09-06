from time import perf_counter

from flip7.agents import MCTSAgent
from flip7.agents.threshold_agent import SimpleThresholdAgent
from flip7.simulation.simulator import GameSimulation


def main() -> None:
    simulated_opponent = SimpleThresholdAgent(
        "Simulated Threshold"
    )
    rollout_agent = SimpleThresholdAgent(
        "Rollout Threshold"
    )
    simulation = GameSimulation(
        agents=[
            MCTSAgent(
                "Monte",
                simulations=100,
                max_depth=30,
                seed=42,
                opponent_agent=simulated_opponent,
                rollout_agent=rollout_agent,
            ),
            SimpleThresholdAgent("Threshold"),
        ],
        winning_score=100,
        seed=37,
    )

    started_at = perf_counter()
    winners = simulation.run()
    elapsed_seconds = perf_counter() - started_at

    print(f"Elapsed: {elapsed_seconds:.3f} seconds")
    print(f"Rounds: {simulation.rounds_played}")
    print(
        "Scores: "
        + ", ".join(
            f"{player.player_name}={player.total_score}"
            for player in simulation.players
        )
    )
    print(
        "Winners: "
        + ", ".join(winner.player_name for winner in winners)
    )


if __name__ == "__main__":
    main()
