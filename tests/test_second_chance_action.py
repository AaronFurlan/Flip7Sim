import pytest

from flip7.actions.second_chance_action import (
    SecondChanceAction,
)
from flip7.game.cards import NumberCard
from flip7.game.deck import Deck
from flip7.game.player import Player
from flip7.game.round import GameRound


def create_started_round() -> tuple[
    GameRound,
    Player,
    Player,
]:
    alice = Player("Alice")
    bob = Player("Bob")

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    return game_round, alice, bob


def test_second_chance_is_assigned_to_target() -> None:
    game_round, alice, bob = create_started_round()

    action = SecondChanceAction()
    action.execute(
        game_round=game_round,
        source_player=alice,
        target_player=bob,
    )

    assert bob.has_second_chance
    assert not alice.has_second_chance


def test_player_cannot_receive_second_chance_twice() -> None:
    game_round, alice, bob = create_started_round()
    bob.has_second_chance = True

    action = SecondChanceAction()

    with pytest.raises(ValueError):
        action.execute(
            game_round=game_round,
            source_player=alice,
            target_player=bob,
        )

    assert bob.has_second_chance
