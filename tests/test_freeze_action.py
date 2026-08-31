from flip7.actions.freeze_action import FreezeAction
from flip7.game.cards import NumberCard
from flip7.game.deck import Deck
from flip7.game.player import Player
from flip7.game.round import GameRound
from flip7.game.scoring import calculate_round_score


def test_freeze_stops_target_and_preserves_score() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(8),
                NumberCard(7),
            ]
        ),
    )
    game_round.start_round()

    score_before_freeze = calculate_round_score(alice)

    action = FreezeAction()
    action.execute(
        game_round=game_round,
        source_player=bob,
        target_player=alice,
    )

    assert not alice.is_active
    assert not alice.has_stayed
    assert not alice.has_busted
    assert calculate_round_score(alice) == score_before_freeze