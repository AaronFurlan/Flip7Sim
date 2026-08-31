from flip7.game.cards import ModifierType
from flip7.game.player import Player

FLIP_SEVEN_CARD_COUNT = 7
FLIP_SEVEN_BONUS = 15

def calculate_round_score(player: Player) -> int:
    if player.has_busted:
        return 0

    number_cards = player.get_number_cards()
    modifier_cards = player.get_modifier_cards()

    number_card_score = sum(
        card.number
        for card in number_cards
    )

    multiplied_number_score = number_card_score

    for card in modifier_cards:
        if card.modifier_type is ModifierType.MULTIPLIER:
            multiplied_number_score *= card.value

    additive_bonus = sum(
        card.value
        for card in modifier_cards
        if card.modifier_type is ModifierType.ADDITIVE
    )

    round_score = multiplied_number_score + additive_bonus

    unique_number_count = len({
        card.number
        for card in number_cards
    })

    if unique_number_count >= FLIP_SEVEN_CARD_COUNT:
        round_score += FLIP_SEVEN_BONUS

    return round_score