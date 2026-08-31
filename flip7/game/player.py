from flip7.game.cards import (
    Card,
    ModifierCard,
    NumberCard,
)

class Player:
    def __init__(self, player_name: str) -> None:
        if not player_name.strip():
            raise ValueError("Player name cannot be empty.")

        self.player_name = player_name
        self.total_score = 0
        self.round_cards: list[Card] = []

        self.is_active = True
        self.has_stayed = False
        self.has_busted = False
        self.has_second_chance = False

    def reset_for_new_round(self) -> None:
        self.round_cards = []
        self.is_active = True
        self.has_stayed = False
        self.has_busted = False
        self.has_second_chance = False

    def add_card(self, card: Card) -> None:
        self.round_cards.append(card)

    def has_number(self, number: int) -> bool:
        return any(
            card.number == number
            for card in self.get_number_cards()
        )

    def get_number_cards(self) -> list[NumberCard]:
        return [
            card
            for card in self.round_cards
            if isinstance(card, NumberCard)
        ]

    def get_modifier_cards(self) -> list[ModifierCard]:
        return [
            card
            for card in self.round_cards
            if isinstance(card, ModifierCard)
        ]
