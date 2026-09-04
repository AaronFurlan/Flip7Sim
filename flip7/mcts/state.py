from dataclasses import dataclass, field
from enum import StrEnum

from flip7.game.cards import (
    ActionType,
    Card,
)
from flip7.game.constants import MINIMUM_PLAYER_COUNT


class SearchDecisionPhase(StrEnum):
    TURN = "turn"
    ACTION_TARGET = "action_target"


@dataclass(slots=True)
class SearchPlayerState:
    player_index: int
    player_name: str
    total_score: int = 0
    round_cards: list[Card] = field(default_factory=list)
    is_active: bool = True
    has_stayed: bool = False
    has_busted: bool = False
    has_second_chance: bool = False

    def __post_init__(self) -> None:
        if self.player_index < 0:
            raise ValueError(
                "The player index cannot be negative."
            )

        if not self.player_name.strip():
            raise ValueError(
                "The player name cannot be empty."
            )

        if self.total_score < 0:
            raise ValueError(
                "The total score cannot be negative."
            )

        if (
            self.is_active
            and (self.has_stayed or self.has_busted)
        ):
            raise ValueError(
                "A stayed or busted player cannot be active."
            )

    def has_number(self, number: int) -> bool:
        return any(
            getattr(card, "number", None) == number
            for card in self.round_cards
        )


@dataclass(frozen=True, slots=True)
class SearchPendingAction:
    source_player_index: int
    action_type: ActionType

    def __post_init__(self) -> None:
        if self.source_player_index < 0:
            raise ValueError(
                "The source player index cannot be negative."
            )


@dataclass(slots=True)
class Flip7SearchState:
    players: list[SearchPlayerState]
    remaining_card_counts: dict[Card, int]
    discarded_card_counts: dict[Card, int]

    current_player_index: int
    root_player_index: int
    next_starting_player_index: int
    winning_score: int

    decision_phase: SearchDecisionPhase = (
        SearchDecisionPhase.TURN
    )
    pending_action: SearchPendingAction | None = None
    queued_actions: list[SearchPendingAction] = field(
        default_factory=list
    )

    round_finished: bool = False
    game_finished: bool = False

    def __post_init__(self) -> None:
        self._validate_players()
        self._validate_player_indices()
        self._validate_card_counts()
        self._validate_decision_phase()

        if self.winning_score <= 0:
            raise ValueError(
                "The winning score must be positive."
            )

        if self.game_finished and not self.round_finished:
            raise ValueError(
                "A finished game must also have a finished round."
            )

        if self.round_finished and self.pending_action is not None:
            raise ValueError(
                "A finished round cannot have a pending action."
            )

    def _validate_players(self) -> None:
        if len(self.players) < MINIMUM_PLAYER_COUNT:
            raise ValueError(
                f"At least {MINIMUM_PLAYER_COUNT} players "
                "are required."
            )

        player_indices = {
            player.player_index
            for player in self.players
        }

        expected_indices = set(range(len(self.players)))

        if player_indices != expected_indices:
            raise ValueError(
                "Player indices must be unique and contiguous."
            )

    def _validate_player_indices(self) -> None:
        number_of_players = len(self.players)

        indices = (
            self.current_player_index,
            self.root_player_index,
            self.next_starting_player_index,
        )

        if any(
            not 0 <= index < number_of_players
            for index in indices
        ):
            raise ValueError(
                "A search-state player index is out of range."
            )

        pending_actions = list(self.queued_actions)

        if self.pending_action is not None:
            pending_actions.append(self.pending_action)

        if any(
            pending_action.source_player_index
            >= number_of_players
            for pending_action in pending_actions
        ):
            raise ValueError(
                "A pending-action source index is out of range."
            )

    def _validate_card_counts(self) -> None:
        all_counts = (
            *self.remaining_card_counts.values(),
            *self.discarded_card_counts.values(),
        )

        if any(count < 0 for count in all_counts):
            raise ValueError(
                "Card counts cannot be negative."
            )

    def _validate_decision_phase(self) -> None:
        if (
            self.decision_phase
            is SearchDecisionPhase.ACTION_TARGET
            and self.pending_action is None
        ):
            raise ValueError(
                "The action-target phase requires "
                "a pending action."
            )

        if (
            self.decision_phase
            is SearchDecisionPhase.TURN
            and self.pending_action is not None
        ):
            raise ValueError(
                "The turn phase cannot have "
                "a pending action."
            )