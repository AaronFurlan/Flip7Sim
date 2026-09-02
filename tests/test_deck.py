from collections import Counter

import pytest

from flip7.game.cards import (
    ActionCard,
    ActionType,
    Card,
    ModifierCard,
    ModifierType,
    NumberCard,
)
from flip7.game.deck import Deck, DeckEmptyError

def test_standard_deck_contains_94_cards() -> None:
    cards = Deck.create_standard_deck()

    assert len(cards) == 94


def test_standard_deck_has_correct_number_card_counts() -> None:
    cards = Deck.create_standard_deck()

    actual_counts = Counter(
        card.number
        for card in cards
        if isinstance(card, NumberCard)
    )

    expected_counts = {0: 1}

    for number in range(1, 13):
        expected_counts[number] = number

    assert actual_counts == expected_counts


def test_standard_deck_has_correct_modifier_cards() -> None:
    cards = Deck.create_standard_deck()

    actual_counts = Counter(
        (card.modifier_type, card.value)
        for card in cards
        if isinstance(card, ModifierCard)
    )

    expected_counts = {
        (ModifierType.ADDITIVE, 2): 1,
        (ModifierType.ADDITIVE, 4): 1,
        (ModifierType.ADDITIVE, 6): 1,
        (ModifierType.ADDITIVE, 8): 1,
        (ModifierType.ADDITIVE, 10): 1,
        (ModifierType.MULTIPLIER, 2): 1,
    }

    assert actual_counts == expected_counts


def test_standard_deck_has_correct_action_cards() -> None:
    cards = Deck.create_standard_deck()

    actual_counts = Counter(
        card.action_type
        for card in cards
        if isinstance(card, ActionCard)
    )

    expected_counts = {
        ActionType.FREEZE: 3,
        ActionType.FLIP_THREE: 3,
        ActionType.SECOND_CHANCE: 3,
    }

    assert actual_counts == expected_counts

def test_draw_card_removes_exactly_one_card() -> None:
    deck = Deck()
    count_before_drawing = deck.remaining_card_count()

    drawn_card = deck.draw_card()

    assert isinstance(drawn_card, Card)
    assert deck.remaining_card_count() == count_before_drawing - 1


def test_same_seed_produces_same_card_order() -> None:
    first_deck = Deck(seed=42)
    second_deck = Deck(seed=42)

    first_deck.shuffle()
    second_deck.shuffle()

    first_draws = [
        first_deck.draw_card()
        for _ in range(10)
    ]
    second_draws = [
        second_deck.draw_card()
        for _ in range(10)
    ]

    assert first_draws == second_draws


def test_empty_deck_is_detected() -> None:
    deck = Deck()

    while not deck.is_empty():
        deck.draw_card()

    assert deck.remaining_card_count() == 0
    assert deck.is_empty()

    with pytest.raises(DeckEmptyError):
        deck.draw_card()

def test_discard_card_adds_card_to_discard_pile() -> None:
    deck = Deck()
    drawn_card = deck.draw_card()

    deck.discard_card(drawn_card)

    assert deck.remaining_card_count() == 93
    assert deck.discarded_card_count() == 1


def test_discard_cards_adds_multiple_cards() -> None:
    deck = Deck()
    drawn_cards = [
        deck.draw_card()
        for _ in range(3)
    ]

    deck.discard_cards(drawn_cards)

    assert deck.remaining_card_count() == 91
    assert deck.discarded_card_count() == 3


def test_draw_card_reshuffles_discard_pile_when_needed() -> None:
    deck = Deck(seed=42)

    all_drawn_cards = [
        deck.draw_card()
        for _ in range(94)
    ]
    cards_to_discard = all_drawn_cards[:3]

    deck.discard_cards(cards_to_discard)

    assert deck.is_empty()
    assert deck.discarded_card_count() == 3

    redrawn_cards = [
        deck.draw_card()
        for _ in range(3)
    ]

    assert Counter(redrawn_cards) == Counter(cards_to_discard)
    assert deck.remaining_card_count() == 0
    assert deck.discarded_card_count() == 0

def test_deck_can_use_custom_cards() -> None:
    custom_cards = [
        NumberCard(3),
        NumberCard(7),
    ]
    deck = Deck(cards=custom_cards)

    assert deck.remaining_card_count() == 2
    assert deck.draw_card() == NumberCard(7)
    assert deck.draw_card() == NumberCard(3)
    assert deck.is_empty()

    assert custom_cards == [
        NumberCard(3),
        NumberCard(7),
    ]

def test_remaining_card_counts_include_depleted_types() -> None:
    freeze_card = ActionCard(
        action_type=ActionType.FREEZE
    )

    deck = Deck(
        cards=[
            NumberCard(2),
            NumberCard(2),
            freeze_card,
        ]
    )

    counts_before_draw = deck.remaining_card_counts()

    assert counts_before_draw[NumberCard(2)] == 2
    assert counts_before_draw[freeze_card] == 1

    assert deck.draw_card() == freeze_card

    counts_after_draw = deck.remaining_card_counts()

    assert counts_after_draw[NumberCard(2)] == 2
    assert counts_after_draw[freeze_card] == 0
    assert sum(counts_after_draw.values()) == 2