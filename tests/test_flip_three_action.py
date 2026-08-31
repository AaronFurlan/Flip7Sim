from flip7.actions.flip_three_action import FlipThreeAction
from flip7.game.cards import (
    ActionCard,
    ActionType,
    NumberCard,
)
from flip7.game.deck import Deck
from flip7.game.player import Player
from flip7.game.round import GameRound, PendingAction


def test_flip_three_draws_three_cards() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(5),
                NumberCard(4),
                NumberCard(3),
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    action = FlipThreeAction()
    action.execute(
        game_round=game_round,
        source_player=bob,
        target_player=alice,
    )

    assert alice.get_number_cards() == [
        NumberCard(1),
        NumberCard(3),
        NumberCard(4),
        NumberCard(5),
    ]
    assert alice.is_active
    assert not alice.has_busted
    assert game_round.deck.is_empty()


def test_flip_three_stops_immediately_on_bust() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(5),
                NumberCard(4),
                NumberCard(7),
                NumberCard(2),
                NumberCard(7),
            ]
        ),
    )
    game_round.start_round()

    action = FlipThreeAction()
    action.execute(
        game_round=game_round,
        source_player=bob,
        target_player=alice,
    )

    assert alice.get_number_cards().count(
        NumberCard(7)
    ) == 2
    assert alice.has_busted
    assert not alice.is_active

    assert game_round.deck.remaining_card_count() == 2


def test_second_chance_can_be_used_during_flip_three() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    second_chance_card = ActionCard(
        ActionType.SECOND_CHANCE
    )

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(5),
                NumberCard(7),
                second_chance_card,
                NumberCard(2),
                NumberCard(7),
            ]
        ),
    )
    game_round.start_round()

    action = FlipThreeAction()
    action.execute(
        game_round=game_round,
        source_player=bob,
        target_player=alice,
    )

    assert alice.get_number_cards() == [
        NumberCard(7),
        NumberCard(5),
    ]
    assert not alice.has_second_chance
    assert second_chance_card not in alice.round_cards

    assert alice.is_active
    assert not alice.has_busted
    assert game_round.deck.discarded_card_count() == 2

def test_action_drawn_during_flip_three_is_deferred() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    freeze_card = ActionCard(ActionType.FREEZE)

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(4),
                NumberCard(3),
                freeze_card,
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    action = FlipThreeAction()
    action.execute(
        game_round=game_round,
        source_player=bob,
        target_player=alice,
    )

    assert alice.get_number_cards() == [
        NumberCard(1),
        NumberCard(3),
        NumberCard(4),
    ]
    assert game_round.pending_action == PendingAction(
        source_player=alice,
        card=freeze_card,
    )
    assert freeze_card not in alice.round_cards


def test_multiple_deferred_actions_keep_their_order() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    freeze_card = ActionCard(ActionType.FREEZE)
    flip_three_card = ActionCard(
        ActionType.FLIP_THREE
    )

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(3),
                flip_three_card,
                freeze_card,
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    action = FlipThreeAction()
    action.execute(
        game_round=game_round,
        source_player=bob,
        target_player=alice,
    )

    assert game_round.pending_action == PendingAction(
        source_player=alice,
        card=freeze_card,
    )

    game_round.resolve_pending_action(bob)

    assert game_round.pending_action == PendingAction(
        source_player=alice,
        card=flip_three_card,
    )
    assert freeze_card in bob.round_cards
    assert not bob.is_active


def test_deferred_action_is_discarded_after_bust() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    freeze_card = ActionCard(ActionType.FREEZE)

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(4),
                NumberCard(7),
                freeze_card,
                NumberCard(2),
                NumberCard(7),
            ]
        ),
    )
    game_round.start_round()

    action = FlipThreeAction()
    action.execute(
        game_round=game_round,
        source_player=bob,
        target_player=alice,
    )

    assert alice.has_busted
    assert game_round.pending_action is None
    assert game_round.deck.discarded_card_count() == 1
    assert game_round.deck.remaining_card_count() == 1