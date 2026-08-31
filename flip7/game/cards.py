from dataclasses import dataclass, field
from enum import StrEnum

class CardType(StrEnum):
    NUMBER = "number"
    MODIFIER = "modifier"
    ACTION = "action"

class ModifierType(StrEnum):
    ADDITIVE = "additive"
    MULTIPLIER = "multiplier"

class ActionType(StrEnum):
    FREEZE = "freeze"
    FLIP_THREE = "flip_three"
    SECOND_CHANCE = "second_chance"


@dataclass(frozen=True, slots=True)
class Card:
    card_type: CardType

    def __str__(self) -> str:
        return f"{self.card_type.value.title()} card"

@dataclass(frozen=True, slots=True)
class NumberCard(Card):
    number: int
    card_type: CardType = field(
        init=False,
        default=CardType.NUMBER,
    )

    def __post_init__(self) -> None:
        if not 0 <= self.number <= 12:
            raise ValueError("A number card must be between 0 and 12.")

    def __str__(self) -> str:
        return f"Number {self.number}"

@dataclass(frozen=True, slots=True)
class ModifierCard(Card):
    modifier_type: ModifierType
    value: int
    card_type: CardType = field(
        init=False,
        default=CardType.MODIFIER,
    )

    def __post_init__(self) -> None:
        if self.modifier_type is ModifierType.ADDITIVE:
            if self.value <= 0:
                raise ValueError(
                    "An additive modifier must be positive."
                )

        if self.modifier_type is ModifierType.MULTIPLIER:
            if self.value <= 1:
                raise ValueError(
                    "A multiplier must be greater than one."
                )

    def __str__(self) -> str:
        if self.modifier_type is ModifierType.ADDITIVE:
            return f"Modifier +{self.value}"

        return f"Modifier x{self.value}"

@dataclass(frozen=True, slots=True)
class ActionCard(Card):
    action_type: ActionType
    card_type: CardType = field(
        init=False,
        default=CardType.ACTION,
    )

    def __str__(self) -> str:
        readable_action_name = (
            self.action_type
            .replace("_", " ")
            .title()
        )

        return f"Action {readable_action_name}"