from flip7.game.cards import (
    Card,
    ModifierCard,
    ModifierType,
    NumberCard,
)
from flip7.game.player import Player
from flip7.game.scoring import calculate_round_score


def create_player_with_cards(*cards: Card) -> Player:
    player = Player("Alice")

    for card in cards:
        player.add_card(card)

    return player


def test_score_with_only_number_cards() -> None:
    player = create_player_with_cards(
        NumberCard(5),
        NumberCard(10),
    )

    assert calculate_round_score(player) == 15


def test_score_with_additive_modifier() -> None:
    player = create_player_with_cards(
        NumberCard(5),
        NumberCard(10),
        ModifierCard(ModifierType.ADDITIVE, 4),
    )

    assert calculate_round_score(player) == 19


def test_multiplier_applies_to_number_cards() -> None:
    player = create_player_with_cards(
        NumberCard(5),
        NumberCard(10),
        ModifierCard(ModifierType.MULTIPLIER, 2),
    )

    assert calculate_round_score(player) == 30


def test_multiple_modifiers_use_correct_order() -> None:
    player = create_player_with_cards(
        NumberCard(5),
        NumberCard(10),
        ModifierCard(ModifierType.MULTIPLIER, 2),
        ModifierCard(ModifierType.ADDITIVE, 4),
        ModifierCard(ModifierType.ADDITIVE, 6),
    )

    assert calculate_round_score(player) == 40


def test_flip_seven_adds_15_point_bonus() -> None:
    player = create_player_with_cards(
        NumberCard(1),
        NumberCard(2),
        NumberCard(3),
        NumberCard(4),
        NumberCard(5),
        NumberCard(6),
        NumberCard(7),
    )

    assert calculate_round_score(player) == 43


def test_busted_player_scores_zero_points() -> None:
    player = create_player_with_cards(
        NumberCard(10),
        NumberCard(12),
        ModifierCard(ModifierType.ADDITIVE, 10),
    )
    player.has_busted = True

    assert calculate_round_score(player) == 0