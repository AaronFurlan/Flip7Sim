from collections.abc import Iterable
from random import Random

from flip7.game.cards import (
    ActionCard,
    ActionType,
    Card,
    ModifierCard,
    ModifierType,
    NumberCard,
)

MINIMUM_NUMBER = 0
MAXIMUM_NUMBER = 12

ADDITIVE_MODIFIER_VALUES = (2, 4, 6, 8, 10)
MULTIPLIER_VALUE = 2

ACTION_CARD_COPIES = 3

class DeckEmptyError(RuntimeError):
    """Raised when no card can be drawn from the deck."""

class Deck:
    def __init__(self, seed: int | None = None) -> None:
        self._random = Random(seed)
        self._cards = self.create_standard_deck()
        self._discard_pile: list[Card] = []

    @staticmethod
    def create_standard_deck() -> list[Card]:
        cards: list[Card] = []

        for number in range(
            MINIMUM_NUMBER,
            MAXIMUM_NUMBER + 1
        ):
            number_of_copies = 1 if number == 0 else number

            for _ in range(number_of_copies):
                cards.append(NumberCard(number))

        for modifier_value in ADDITIVE_MODIFIER_VALUES:
            cards.append(
                ModifierCard(
                    modifier_type=ModifierType.ADDITIVE,
                    value=modifier_value
                )
            )

        cards.append(
            ModifierCard(
                modifier_type=ModifierType.MULTIPLIER,
                value=MULTIPLIER_VALUE,
            )
        )

        for action_type in ActionType:
            for _ in range(ACTION_CARD_COPIES):
                cards.append(ActionCard(action_type))

        return cards

    def shuffle(self) -> None:
        self._random.shuffle(self._cards)

    def remaining_card_count(self) -> int:
        return len(self._cards)

    def is_empty(self) -> bool:
        return not self._cards

    def draw_card(self) -> Card:
        if self.is_empty():
            self._reshuffle_discard_pile()

        if self.is_empty():
            raise DeckEmptyError(
                "Cannot draw a card from an empty deck."
            )

        return self._cards.pop()

    def discard_card(self, card: Card) -> None:
        self._discard_pile.append(card)

    def discard_cards(self, cards: Iterable[Card]) -> None:
        self._discard_pile.extend(cards)

    def discarded_card_count(self) -> int:
        return len(self._discard_pile)

    def _reshuffle_discard_pile(self) -> None:
        if not self._discard_pile:
            return

        self._cards.extend(self._discard_pile)
        self._discard_pile.clear()
        self.shuffle()