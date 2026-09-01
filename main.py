from flip7.agents.random_agent import RandomAgent
from flip7.simulation.simulator import GameSimulation


def main() -> None:
    agents = [
        RandomAgent("Alice", seed=11),
        RandomAgent("Bob", seed=22),
    ]

    simulation = GameSimulation(
        agents=agents,
        winning_score=1000,
        seed=42,
    )

    winners = simulation.run()

    print("Flip 7 simulation finished")
    print(f"Rounds played: {simulation.rounds_played}")
    print()
    print("Final scores:")

    for player in simulation.players:
        print(
            f"  {player.player_name}: "
            f"{player.total_score} points"
        )

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