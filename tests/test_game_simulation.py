from flip7.agents.base_agent import (
    AgentObservation,
    BaseAgent,
    TargetOption,
    TurnDecision,
)
from flip7.agents.random_agent import RandomAgent
from flip7.game.cards import (
    ActionCard,
    ActionType,
    NumberCard,
)
from flip7.game.deck import Deck
from flip7.simulation.simulator import GameSimulation


class ScriptedAgent(BaseAgent):
    def __init__(
        self,
        player_name: str,
        decisions: list[TurnDecision],
        target_player_index: int = 0,
    ) -> None:
        super().__init__(player_name)
        self._decisions = list(decisions)
        self._target_player_index = target_player_index
        self.target_selection_count = 0

    def choose_hit_or_stay(
        self,
        observation: AgentObservation,
    ) -> TurnDecision:
        if not self._decisions:
            raise AssertionError(
                f"{self.player_name} received an unexpected turn."
            )

        return self._decisions.pop(0)

    def choose_action_target(
        self,
        observation: AgentObservation,
        action_type: ActionType,
        valid_targets: tuple[TargetOption, ...],
    ) -> TargetOption:
        self.target_selection_count += 1

        return next(
            target
            for target in valid_targets
            if target.player_index
            == self._target_player_index
        )


def test_simulation_completes_single_round_game() -> None:
    alice = ScriptedAgent(
        "Alice",
        decisions=[TurnDecision.STAY],
    )
    bob = ScriptedAgent(
        "Bob",
        decisions=[TurnDecision.STAY],
    )

    deck = Deck(
        cards=[
            NumberCard(8),
            NumberCard(3),
        ]
    )

    simulation = GameSimulation(
        agents=[alice, bob],
        winning_score=1,
        deck=deck,
    )

    winners = simulation.run()

    assert simulation.rounds_played == 1
    assert tuple(
        player.total_score
        for player in simulation.players
    ) == (3, 8)
    assert tuple(
        winner.player_name
        for winner in winners
    ) == ("Bob",)


def test_simulation_resolves_initial_action_card() -> None:
    alice = ScriptedAgent(
        "Alice",
        decisions=[
            TurnDecision.HIT,
            TurnDecision.STAY,
        ],
        target_player_index=1,
    )
    bob = ScriptedAgent(
        "Bob",
        decisions=[],
    )

    deck = Deck(
        cards=[
            NumberCard(8),
            ActionCard(
                action_type=ActionType.FREEZE
            ),
        ]
    )

    simulation = GameSimulation(
        agents=[alice, bob],
        winning_score=1,
        deck=deck,
    )

    winners = simulation.run()

    assert alice.target_selection_count == 1
    assert simulation.players[0].total_score == 8
    assert simulation.players[1].total_score == 0
    assert tuple(
        winner.player_name
        for winner in winners
    ) == ("Alice",)


def test_two_random_agents_complete_a_game() -> None:
    simulation = GameSimulation(
        agents=[
            RandomAgent("Alice", seed=11),
            RandomAgent("Bob", seed=22),
        ],
        winning_score=20,
        seed=33,
    )

    winners = simulation.run()

    highest_score = max(
        player.total_score
        for player in simulation.players
    )

    assert simulation.rounds_played >= 1
    assert highest_score >= 20
    assert winners
    assert all(
        winner.total_score == highest_score
        for winner in winners
    )