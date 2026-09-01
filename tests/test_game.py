import pytest

from flip7.game.cards import NumberCard
from flip7.game.deck import Deck
from flip7.game.game import Flip7Game, GameStateError
from flip7.game.player import Player


@pytest.mark.parametrize("player_count", [0, 1])
def test_game_requires_at_least_two_players(
    player_count: int,
) -> None:
    players = [
        Player(f"Player {index}")
        for index in range(player_count)
    ]

    with pytest.raises(ValueError):
        Flip7Game(players=players)


@pytest.mark.parametrize("winning_score", [0, -1])
def test_winning_score_must_be_positive(
    winning_score: int,
) -> None:
    with pytest.raises(ValueError):
        Flip7Game(
            players=[
                Player("Alice"),
                Player("Bob"),
            ],
            winning_score=winning_score,
        )


def test_seed_and_custom_deck_cannot_be_combined() -> None:
    with pytest.raises(ValueError):
        Flip7Game(
            players=[
                Player("Alice"),
                Player("Bob"),
            ],
            seed=42,
            deck=Deck(),
        )


def test_game_copies_player_list() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    players = [alice, bob]

    game = Flip7Game(players=players)

    players.clear()

    assert game.players == [alice, bob]


def test_start_game_resets_scores_and_starts_round() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    alice.total_score = 100
    bob.total_score = 50

    game = Flip7Game(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )

    current_round = game.start_game()

    assert game.has_started
    assert game.current_round is current_round
    assert current_round.has_started
    assert current_round.is_initial_deal_complete

    assert alice.total_score == 0
    assert bob.total_score == 0
    assert alice.round_cards == [NumberCard(1)]
    assert bob.round_cards == [NumberCard(2)]


def test_game_cannot_be_started_twice() -> None:
    game = Flip7Game(
        players=[
            Player("Alice"),
            Player("Bob"),
        ],
        deck=Deck(
            cards=[
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game.start_game()

    with pytest.raises(GameStateError):
        game.start_game()

def finish_current_round_by_staying(
    game: Flip7Game,
) -> None:
    current_round = game.current_round

    assert current_round is not None

    for player in game.players:
        if player.is_active:
            current_round.player_stays(player)

    current_round.finish_round()

def test_new_round_cannot_start_before_game() -> None:
    game = Flip7Game(
        players=[
            Player("Alice"),
            Player("Bob"),
        ]
    )

    with pytest.raises(GameStateError):
        game.start_new_round()


def test_new_round_cannot_start_while_round_is_running() -> None:
    game = Flip7Game(
        players=[
            Player("Alice"),
            Player("Bob"),
        ],
        deck=Deck(
            cards=[
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game.start_game()

    with pytest.raises(GameStateError):
        game.start_new_round()


def test_new_round_can_start_after_previous_round() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    game = Flip7Game(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )

    first_round = game.start_game()
    finish_current_round_by_staying(game)

    second_round = game.start_new_round()

    assert second_round is not first_round
    assert game.current_round is second_round
    assert second_round.has_started
    assert second_round.is_initial_deal_complete

    assert len(alice.round_cards) == 1
    assert len(bob.round_cards) == 1


def test_game_does_not_finish_during_running_round() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    game = Flip7Game(
        players=[alice, bob],
        winning_score=10,
        deck=Deck(
            cards=[
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game.start_game()

    alice.total_score = 10

    assert not game.is_game_finished()
    assert game.get_winners() == []


def test_game_detects_winner_after_finished_round() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    game = Flip7Game(
        players=[alice, bob],
        winning_score=2,
        deck=Deck(
            cards=[
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game.start_game()
    finish_current_round_by_staying(game)

    assert game.is_game_finished()
    assert game.get_winners() == [bob]

    with pytest.raises(GameStateError):
        game.start_new_round()


def test_game_supports_multiple_winners() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    game = Flip7Game(
        players=[alice, bob],
        winning_score=5,
        deck=Deck(
            cards=[
                NumberCard(5),
                NumberCard(5),
            ]
        ),
    )
    game.start_game()
    finish_current_round_by_staying(game)

    assert game.is_game_finished()
    assert game.get_winners() == [
        alice,
        bob,
    ]