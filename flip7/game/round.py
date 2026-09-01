from dataclasses import dataclass

from flip7.game.cards import (
    ActionCard,
    ActionType,
    Card,
    ModifierCard,
    NumberCard,
)
from flip7.game.deck import Deck
from flip7.game.player import Player

from flip7.actions.freeze_action import FreezeAction
from flip7.actions.second_chance_action import (
    SecondChanceAction,
)
from flip7.actions.flip_three_action import FlipThreeAction

from flip7.game.scoring import calculate_round_score


MINIMUM_PLAYER_COUNT = 2

class RoundStateError(RuntimeError):
    """Raised when an operation is invalid for the round state."""

@dataclass(frozen=True, slots=True)
class PendingAction:
    source_player: Player
    card: ActionCard

class GameRound:
    def __init__(self, players: list[Player], deck: Deck) -> None:
        if len(players) < MINIMUM_PLAYER_COUNT:
            raise ValueError("At least two players are required.")

        self.players = list(players)
        self.deck = deck

        self.has_started = False
        self.has_finished = False

        self.pending_action: PendingAction | None = None

        self.is_initial_deal_complete = False
        self._next_starting_player_index = 0

        self.round_scores: dict[Player, int] = {}

        self._queued_actions: list[PendingAction] = []

    def start_round(self) -> None:
        if self.has_started and not self.has_finished:
            raise RoundStateError(
                "The round has already started."
            )

        for player in self.players:
            player.reset_for_new_round()

        self.has_started = True
        self.has_finished = False
        self.pending_action = None

        self.is_initial_deal_complete = False
        self._next_starting_player_index = 0

        self.continue_starting_deal()

        self.round_scores = {}

        self._queued_actions = []

    def process_number_card(self, player: Player, card: NumberCard) -> None:
        self._validate_active_player(player)

        if not player.has_number(card.number):
            player.add_card(card)
            return

        if player.has_second_chance:
            self._use_second_chance(player=player, duplicate_card=card)
            return

        player.add_card(card)
        player.has_busted = True
        player.is_active = False

    def _use_second_chance(
            self,
            player: Player,
            duplicate_card: NumberCard,
    ) -> None:
        player.has_second_chance = False
        self.deck.discard_card(duplicate_card)

        second_chance_card = next(
            (
                card
                for card in player.round_cards
                if isinstance(card, ActionCard)
                   and card.action_type
                   is ActionType.SECOND_CHANCE
            ),
            None,
        )

        if second_chance_card is not None:
            player.round_cards.remove(second_chance_card)
            self.deck.discard_card(second_chance_card)

    def _validate_active_player(self, player: Player) -> None:
        if not self.has_started:
            raise RoundStateError(
                "The round has not started."
            )

        if self.has_finished:
            raise RoundStateError(
                "The round has already finished."
            )

        if player not in self.players:
            raise ValueError(
                "The player does not belong to this round."
            )

        if not player.is_active:
            raise RoundStateError(
                "An inactive player cannot receive a card."
            )

    def process_modifier_card(
        self,
        player: Player,
        card: ModifierCard,
    ) -> None:
        self._validate_active_player(player)
        player.add_card(card)

    def draw_card_for_player(self, player: Player) -> Card:
        self._validate_active_player(player)

        if self.pending_action is not None:
            raise RoundStateError("A pending action is already in progress.")

        card = self.deck.draw_card()

        if isinstance(card, NumberCard):
            self.process_number_card(player, card)

        elif isinstance(card, ModifierCard):
            self.process_modifier_card(player, card)

        elif isinstance(card, ActionCard):
            self.pending_action = PendingAction(
                source_player=player,
                card=card,
            )
            self._discard_pending_action_if_no_valid_targets()

        else:
            raise TypeError(f"Unsupported card type: {type(card).__name__}")

        return card

    def continue_starting_deal(self) -> None:
        if not self.has_started:
            raise RoundStateError(
                "The round has not started."
            )

        if self.has_finished:
            raise RoundStateError(
                "The round has already finished."
            )

        if self.pending_action is not None:
            raise RoundStateError(
                "The pending action must be resolved first."
            )

        if self.is_initial_deal_complete:
            return

        while (
            self._next_starting_player_index
            < len(self.players)
        ):
            player = self.players[
                self._next_starting_player_index
            ]
            self._next_starting_player_index += 1

            if not player.is_active:
                continue

            self.draw_card_for_player(player)

            if self.pending_action is not None:
                return

        self.is_initial_deal_complete = True

    def resolve_pending_action(self, target_player: Player) -> None:
        pending_action = self.pending_action

        if pending_action is None:
            raise RoundStateError(
                "There is no pending action to resolve."
            )

        self._validate_active_player(target_player)

        action_type = pending_action.card.action_type

        if action_type is ActionType.FREEZE:
            action = FreezeAction()

        elif action_type is ActionType.FLIP_THREE:
            action = FlipThreeAction()

        elif action_type is ActionType.SECOND_CHANCE:
            if target_player.has_second_chance:
                raise ValueError(
                    "The target player already has "
                    "a Second Chance."
                )

            action = SecondChanceAction()

        else:
            raise NotImplementedError(
                "This action type is not implemented yet."
            )

        target_player.add_card(pending_action.card)
        self.pending_action = None

        action.execute(
            game_round=self,
            source_player=pending_action.source_player,
            target_player=target_player,
        )

        self._promote_next_queued_action()

        if (
                self.pending_action is None
                and not self.is_initial_deal_complete
                and not self.is_round_finished()
        ):
            self.continue_starting_deal()

    def player_stays(self, player: Player) -> None:
        self._validate_active_player(player)

        if self.pending_action is not None:
            raise RoundStateError(
                "A pending action must be resolved first."
            )

        if not self.is_initial_deal_complete:
            raise RoundStateError(
                "A player cannot stay during the initial deal."
            )

        if not player.round_cards:
            raise RoundStateError(
                "A player needs at least one card to stay."
            )

        player.has_stayed = True
        player.is_active = False

    def check_for_flip_seven(self, player: Player) -> bool:
        if player not in self.players:
            raise ValueError(
                "The player does not belong to this round."
            )

        unique_numbers = {
            card.number
            for card in player.get_number_cards()
        }

        return (
                not player.has_busted
                and len(unique_numbers) >= 7
        )

    def is_round_finished(self) -> bool:
        if not self.has_started:
            return False

        if self.pending_action is not None:
            return False

        if any(
                self.check_for_flip_seven(player)
                for player in self.players
        ):
            return True

        return not any(
            player.is_active
            for player in self.players
        )

    def finish_round(self) -> dict[Player, int]:
        if not self.has_started:
            raise RoundStateError(
                "The round has not started."
            )

        if self.has_finished:
            raise RoundStateError(
                "The round has already finished."
            )

        if not self.is_round_finished():
            raise RoundStateError(
                "The round is not finished yet."
            )

        self.round_scores = {
            player: calculate_round_score(player)
            for player in self.players
        }

        for player, round_score in self.round_scores.items():
            player.total_score += round_score

        for player in self.players:
            self.deck.discard_cards(player.round_cards)
            player.round_cards.clear()
            player.is_active = False

        self.has_finished = True

        return dict(self.round_scores)

    def queue_pending_actions(
        self,
        actions: list[PendingAction],
    ) -> None:
        self._queued_actions = [
            *actions,
            *self._queued_actions,
        ]

        self._promote_next_queued_action()

    def _promote_next_queued_action(self) -> None:
        while self.pending_action is None and self._queued_actions:
            self.pending_action = self._queued_actions.pop(0)

            if self.get_valid_action_targets():
                return

            self.deck.discard_card(self.pending_action.card)
            self.pending_action = None

    def draw_card_for_flip_three(
        self,
        player: Player,
    ) -> PendingAction | None:
        self._validate_active_player(player)

        if self.pending_action is not None:
            raise RoundStateError(
                "A pending action must be resolved first."
            )

        card = self.deck.draw_card()

        if isinstance(card, NumberCard):
            self.process_number_card(player, card)
            return None

        if isinstance(card, ModifierCard):
            self.process_modifier_card(player, card)
            return None

        if isinstance(card, ActionCard):
            if (
                card.action_type
                is ActionType.SECOND_CHANCE
                and not player.has_second_chance
            ):
                action = SecondChanceAction()
                action.execute(
                    game_round=self,
                    source_player=player,
                    target_player=player,
                )
                player.add_card(card)
                return None

            return PendingAction(
                source_player=player,
                card=card,
            )

        raise TypeError(
            f"Unsupported card type: {type(card).__name__}"
        )

    def get_valid_action_targets(self) -> list[Player]:
        pending_action = self.pending_action

        if pending_action is None:
            return []

        valid_targets = [player for player in self.players if player.is_active]

        if pending_action.card.action_type is ActionType.SECOND_CHANCE:
            valid_targets = [player for player in valid_targets if not player.has_second_chance]

        return valid_targets

    # Only possible for second chance actions
    def _discard_pending_action_if_no_valid_targets(self) -> bool:
        if self.pending_action is None:
            return False

        if self.get_valid_action_targets():
            return False

        self.deck.discard_card(
            self.pending_action.card
        )
        self.pending_action = None

        self._promote_next_queued_action()
        return True
