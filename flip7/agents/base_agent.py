from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum

from flip7.game.cards import ActionType, Card


class TurnDecision(StrEnum):
    HIT = "hit"
    STAY = "stay"

@dataclass(frozen=True, slots=True)
class PlayerObservation:
    player_name: str
    total_score: int
    current_round_score: int
    number_of_unique_numbers: int
    is_active: bool
    has_second_chance: bool
    has_stayed: bool = False
    has_busted: bool = False
    round_cards: tuple[Card, ...] = ()

@dataclass(frozen=True, slots=True)
class DeckCardObservation:
    card: Card
    remaining_count: int

    def __post_init__(self) -> None:
        if self.remaining_count < 0:
            raise ValueError("The remaining card count cannot be negative.")

@dataclass(frozen=True, slots=True)
class AgentObservation:
    own_player: PlayerObservation
    other_players: tuple[PlayerObservation, ...]
    remaining_card_count: int
    winning_score: int
    valid_turn_decisions: tuple[TurnDecision, ...] = (
        TurnDecision.HIT,
        TurnDecision.STAY,
    )
    deck_card_counts: tuple[DeckCardObservation, ...] = ()

@dataclass(frozen=True, slots=True)
class TargetOption:
    player_index: int
    player: PlayerObservation


class BaseAgent(ABC):
    def __init__(self, player_name: str) -> None:
        if not player_name.strip():
            raise ValueError("The agent player name must not be empty.")

        self.player_name = player_name

    @abstractmethod
    def choose_hit_or_stay(
        self,
        observation: AgentObservation,
    ) -> TurnDecision:
        raise NotImplementedError

    @abstractmethod
    def choose_action_target(
        self,
        observation: AgentObservation,
        action_type: ActionType,
        valid_targets: tuple[TargetOption, ...],
    ) -> TargetOption:
        raise NotImplementedError