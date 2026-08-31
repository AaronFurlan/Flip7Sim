import pytest

from flip7.game.cards import (
    ActionCard,
    ActionType,
    CardType,
    ModifierCard,
    ModifierType,
    NumberCard,
)

def test_number_card_stores_number_and_type() -> None:
    card = NumberCard(7)

    assert card.number == 7
    assert card.card_type is CardType.NUMBER

def test_number_card_has_readable_string() -> None:
    card = NumberCard(7)

    assert str(card) == "Number 7"

@pytest.mark.parametrize("invalid_number", [-1, 13])
def test_number_card_rejects_invalid_number(invalid_number: int) -> None:
    with pytest.raises(ValueError):
        NumberCard(invalid_number)

def test_additive_modifier_stores_its_data() -> None:
    card = ModifierCard(
        modifier_type=ModifierType.ADDITIVE,
        value=6,
    )

    assert card.card_type is CardType.MODIFIER
    assert card.modifier_type is ModifierType.ADDITIVE
    assert card.value == 6
    assert str(card) == "Modifier +6"


def test_multiplier_modifier_stores_its_data() -> None:
    card = ModifierCard(
        modifier_type=ModifierType.MULTIPLIER,
        value=2,
    )

    assert card.card_type is CardType.MODIFIER
    assert card.modifier_type is ModifierType.MULTIPLIER
    assert card.value == 2
    assert str(card) == "Modifier x2"


@pytest.mark.parametrize(
    ("modifier_type", "invalid_value"),
    [
        (ModifierType.ADDITIVE, 0),
        (ModifierType.MULTIPLIER, 1),
    ],
)
def test_modifier_rejects_invalid_value(
    modifier_type: ModifierType,
    invalid_value: int,
) -> None:
    with pytest.raises(ValueError):
        ModifierCard(
            modifier_type=modifier_type,
            value=invalid_value,
        )

@pytest.mark.parametrize(
    ("action_type", "expected_string"),
    [
        (ActionType.FREEZE, "Action Freeze"),
        (ActionType.FLIP_THREE, "Action Flip Three"),
        (
            ActionType.SECOND_CHANCE,
            "Action Second Chance",
        ),
    ],
)
def test_action_card_stores_its_data(
    action_type: ActionType,
    expected_string: str,
) -> None:
    card = ActionCard(action_type=action_type)

    assert card.card_type is CardType.ACTION
    assert card.action_type is action_type
    assert str(card) == expected_string