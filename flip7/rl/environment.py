from collections.abc import Callable
from random import Random

from flip7.agents.base_agent import BaseAgent
from flip7.agents.rl_agent import QLearningAgent
from flip7.game.player import Player
from flip7.simulation.simulator import GameSimulation


def train(
    learner: QLearningAgent,
    opponent_factory: Callable[[], list[BaseAgent]],
    games: int,
    *,
    winning_score: int = 200,
    epsilon_start: float = 1.0,
    epsilon_end: float = 0.05,
    seed: int | None = None,
    log_every: int = 500,
) -> None:
    rng = Random(seed)
    learner.training = True
    recent_round_scores: list[int] = []

    for game_index in range(games):
        progress = game_index / max(games - 1, 1)
        learner.epsilon = epsilon_start + (epsilon_end - epsilon_start) * progress

        # Rotate seats so the learner sees every starting position.
        agents = [learner, *opponent_factory()]
        rotation = game_index % len(agents)
        agents = agents[rotation:] + agents[:rotation]

        def on_round_finished(round_scores: dict[Player, int]) -> None:
            score = next(
                score
                for player, score in round_scores.items()
                if player.player_name == learner.player_name
            )
            learner.finish_round(score)
            recent_round_scores.append(score)

        GameSimulation(
            agents=agents,
            winning_score=winning_score,
            seed=rng.randrange(2 ** 32),
            on_round_finished=on_round_finished,
        ).run()

        if (game_index + 1) % log_every == 0:
            average = sum(recent_round_scores) / len(recent_round_scores)
            print(
                f"game {game_index + 1}/{games}  epsilon={learner.epsilon:.3f}  "
                f"avg round score={average:.2f}  states={len(learner.hit_values)}"
            )
            recent_round_scores.clear()
