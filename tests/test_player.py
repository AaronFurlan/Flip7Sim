import pytest

from flip7.game.cards import (
    ActionCard,
    ActionType,
    ModifierCard,
    ModifierType,
    NumberCard,
)
from flip7.game.player import Player


def test_new_player_has_correct_initial_state() -> None:
    player = Player("Alice")

    assert player.player_name == "Alice"
    assert player.total_score == 0
    assert player.round_cards == []
    assert player.is_active
    assert not player.has_stayed
    assert not player.has_busted
    assert not player.has_second_chance


@pytest.mark.parametrize("invalid_name", ["", "   "])
def test_player_rejects_empty_name(
    invalid_name: str,
) -> None:
    with pytest.raises(ValueError):
        Player(invalid_name)


def test_reset_for_new_round_preserves_total_score() -> None:
    player = Player("Alice")
    player.total_score = 50
    player.round_cards.append(NumberCard(7))
    player.is_active = False
    player.has_stayed = True
    player.has_busted = True
    player.has_second_chance = True

    player.reset_for_new_round()

    assert player.total_score == 50
    assert player.round_cards == []
    assert player.is_active
    assert not player.has_stayed
    assert not player.has_busted
    assert not player.has_second_chance

def test_add_card_adds_card_to_round_cards() -> None:
    player = Player("Alice")
    card = NumberCard(7)

    player.add_card(card)

    assert player.round_cards == [card]


def test_has_number_detects_existing_number() -> None:
    player = Player("Alice")
    player.add_card(NumberCard(7))
    player.add_card(NumberCard(10))

    assert player.has_number(7)
    assert player.has_number(10)
    assert not player.has_number(8)


def test_card_getters_return_only_matching_card_types() -> None:
    player = Player("Alice")

    first_number_card = NumberCard(3)
    second_number_card = NumberCard(8)
    modifier_card = ModifierCard(
        modifier_type=ModifierType.ADDITIVE,
        value=4,
    )
    action_card = ActionCard(ActionType.FREEZE)

    player.add_card(first_number_card)
    player.add_card(modifier_card)
    player.add_card(action_card)
    player.add_card(second_number_card)

    assert player.get_number_cards() == [
        first_number_card,
        second_number_card,
    ]
    assert player.get_modifier_cards() == [
        modifier_card,
    ]