from flip7.agents.random_agent import RandomAgent
from flip7.agents.always_hit_agent import AlwaysHitAgent
from flip7.agents.algorithmic_numbers_only_agent import AlgorithmicNumbersOnlyAgent
from flip7.agents.threshold_agent import SimpleThresholdAgent
from flip7.agents.mcts_agent import MCTSAgent
from flip7.agents.rl_agent import QLearningAgent
from flip7.simulation.simulator import GameSimulation


def main() -> None:
    agents = [
        RandomAgent("RandyRandom", seed=11),
        AlwaysHitAgent("Ballsy"),
        AlgorithmicNumbersOnlyAgent("Rainman"),
        SimpleThresholdAgent("ConnyConservative"),
        # MCTSAgent("Cortana"), # Slow; (Calculates 200 simulations per turn)
        QLearningAgent("Quinn", q_table_path="q_table.json", epsilon=0.0, training=False),
    ]

    simulation = GameSimulation(
        agents=agents,
        winning_score=10000,
        seed=40,
        reporter=print,
    )

    winners = simulation.run()

    print()

    print("Flip 7 simulation finished")
    print(f"Rounds played: {simulation.rounds_played}")
    print()
    print("Final scores:")

    winner_score = winners[0].total_score
    for player in sorted(
        simulation.players,
        key=lambda p: p.total_score,
        reverse=True,
    ):
        string = (
            f"  {player.player_name}: "
            f"{player.total_score} points"
        )
        if player not in winners:
            if winner_score > 0:
                deficit = 100.0 * (winner_score - player.total_score) / winner_score
                string += f" (-{deficit:.1f}%)"
        print(string)

    print()

    winner_names = ", ".join(
        winner.player_name
        for winner in winners
    )

    if len(winners) == 1:
        print(f"Winner: {winner_names}")
    else:
        print(f"Winners: {winner_names}")


if __name__ == "__main__":
    main()