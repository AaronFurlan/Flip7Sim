# Flip7Sim

A Python simulation of the card game **Flip 7** with interchangeable decision-making agents.

## Current features

- Complete Flip 7 deck and scoring
- Number, modifier, and action cards
- Freeze, Flip Three, and Second Chance
- Multi-round games with winner detection
- Algorithm-independent agent interface
- Monte Carlo Tree Search agent with opponent rollouts
- Reproducible Random-vs-Random simulations
- Automated tests with pytest

## Setup

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install pytest
```

## Run a simulation
```powershell
python main.py
```

## MCTS Agent

```python
from flip7.agents import MCTSAgent

agent = MCTSAgent(
    "Monte",
    simulations=100,
    max_depth=30,
    seed=42,
)
```

Higher `simulations` values improve the search at the cost of runtime. The
agent simulates opponent turns and can search across multiple rounds. Existing
agents can be supplied as `opponent_agent` and `rollout_agent`; both default to
`SimpleThresholdAgent`.

Run the reproducible MCTS benchmark with:

```powershell
python -m benchmarks.mcts_game
```

Run a tournament with alternating seat positions:

```powershell
python -m benchmarks.mcts_tournament --games 20
```

The current MCTS defaults are `200` simulations, an exploration weight of
`0.9`, and a maximum search depth of `20`.

## Run tests
```powershell
python -m pytest -v
```

## Agent Observation
```Python
AgentObservation(
    own_player=PlayerObservation(
        player_name="Alice",
        total_score=84,
        current_round_score=23,
        number_of_unique_numbers=3,
        is_active=True,
        has_second_chance=False,
        has_stayed=False,
        has_busted=False,
        round_cards=(
            NumberCard(number=4),
            NumberCard(number=9),
            ModifierCard(
                modifier_type=ModifierType.ADDITIVE,
                value=10,
            ),
        ),
    ),

    other_players=(
        PlayerObservation(
            player_name="Bob",
            total_score=112,
            current_round_score=18,
            number_of_unique_numbers=2,
            is_active=True,
            has_second_chance=True,
            has_stayed=False,
            has_busted=False,
            round_cards=(
                NumberCard(number=7),
                NumberCard(number=11),
                ActionCard(
                    action_type=ActionType.SECOND_CHANCE,
                ),
            ),
        ),
    ),

    remaining_card_count=73,
    winning_score=200,

    valid_turn_decisions=(
        TurnDecision.HIT,
        TurnDecision.STAY,
    ),

    deck_card_counts=(
        # Zahlenkarten: numerisch sortiert
        DeckCardObservation(
            card=NumberCard(number=0),
            remaining_count=1,
        ),
        DeckCardObservation(
            card=NumberCard(number=1),
            remaining_count=1,
        ),
        DeckCardObservation(
            card=NumberCard(number=2),
            remaining_count=2,
        ),

        # ... Number 3 bis Number 11 ...

        DeckCardObservation(
            card=NumberCard(number=12),
            remaining_count=10,
        ),

        # Aktionskarten
        DeckCardObservation(
            card=ActionCard(
                action_type=ActionType.FREEZE,
            ),
            remaining_count=2,
        ),
        DeckCardObservation(
            card=ActionCard(
                action_type=ActionType.FLIP_THREE,
            ),
            remaining_count=3,
        ),
        DeckCardObservation(
            card=ActionCard(
                action_type=ActionType.SECOND_CHANCE,
            ),
            remaining_count=1,
        ),

        # Modifierkarten
        DeckCardObservation(
            card=ModifierCard(
                modifier_type=ModifierType.ADDITIVE,
                value=2,
            ),
            remaining_count=1,
        ),

        # ... +4, +6 und +8 ...

        DeckCardObservation(
            card=ModifierCard(
                modifier_type=ModifierType.ADDITIVE,
                value=10,
            ),
            remaining_count=0,
        ),
        DeckCardObservation(
            card=ModifierCard(
                modifier_type=ModifierType.MULTIPLIER,
                value=2,
            ),
            remaining_count=1,
        ),
    ),
)
```

## Simple Threshold Agent

```Python
class ThresholdAgent(BaseAgent):
    def choose_hit_or_stay(
        self,
        observation: AgentObservation,
    ) -> TurnDecision:
        if (
            TurnDecision.STAY
            not in observation.valid_turn_decisions
        ):
            return TurnDecision.HIT

        if observation.own_player.current_round_score >= 20:
            return TurnDecision.STAY

        return TurnDecision.HIT

    def choose_action_target(
        self,
        observation: AgentObservation,
        action_type: ActionType,
        valid_targets: tuple[TargetOption, ...],
    ) -> TargetOption:
        if not valid_targets:
            raise ValueError(
                "The agent requires at least one valid target."
            )

        best_target = valid_targets[0]

        for target in valid_targets[1:]:
            if (
                target.player.total_score
                > best_target.player.total_score
            ):
                best_target = target

        return best_target
```
