import pytest

from flip7.agents.base_agent import (
    PendingActionObservation,
)
from flip7.game.cards import (
    ActionCard,
    ActionType,
    NumberCard,
)
from flip7.game.deck import Deck
from flip7.game.game import Flip7Game
from flip7.game.player import Player
from flip7.game.round import (
    GameRound,
    PendingAction,
)
from flip7.simulation.simulator import (
    create_agent_observation,
    create_player_observation,
    create_valid_target_options,
)


def create_started_game() -> Flip7Game:
    game = Flip7Game(
        players=[Player("Alice"), Player("Bob")],
        winning_score=150,
        deck=Deck(
            cards=[
                NumberCard(9),
                NumberCard(8),
                NumberCard(3),
            ]
        ),
    )
    game.start_game()
    return game


def test_player_observation_accepts_optional_player_index() -> None:
    observation = create_player_observation(
        Player("Alice"),
        player_index=2,
    )

    assert observation.player_index == 2


def test_discarded_card_counts_include_catalog_types() -> None:
    number_card = NumberCard(4)
    freeze_card = ActionCard(ActionType.FREEZE)
    deck = Deck(cards=[number_card, freeze_card])

    assert deck.draw_card() == freeze_card
    deck.discard_card(freeze_card)

    counts = deck.discarded_card_counts()

    assert counts[freeze_card] == 1
    assert counts[number_card] == 0


def test_discarded_card_counts_are_a_snapshot() -> None:
    card = NumberCard(4)
    deck = Deck(cards=[card])
    deck.draw_card()
    deck.discard_card(card)

    counts = deck.discarded_card_counts()
    counts[card] = 99

    assert deck.discarded_card_counts()[card] == 1


def test_next_starting_player_index_is_public() -> None:
    game = create_started_game()

    assert game.current_round is not None
    assert game.current_round.starting_player_index == 0
    assert game.next_starting_player_index == 1


def test_queued_action_snapshot_is_immutable() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(cards=[NumberCard(2), NumberCard(1)]),
    )
    game_round.start_round()
    game_round.pending_action = PendingAction(
        source_player=alice,
        card=ActionCard(ActionType.FREEZE),
    )
    first_queued_action = PendingAction(
        source_player=bob,
        card=ActionCard(ActionType.FLIP_THREE),
    )
    game_round.queue_pending_actions([first_queued_action])

    snapshot = game_round.get_queued_actions()

    game_round.queue_pending_actions([
        PendingAction(
            source_player=alice,
            card=ActionCard(ActionType.SECOND_CHANCE),
        )
    ])

    assert snapshot == (first_queued_action,)
    assert len(game_round.get_queued_actions()) == 2


def test_agent_observation_contains_search_context() -> None:
    game = create_started_game()
    game_round = game.current_round

    assert game_round is not None

    discarded_card = game.deck.draw_card()
    game.deck.discard_card(discarded_card)

    game_round.pending_action = PendingAction(
        source_player=game.players[0],
        card=ActionCard(ActionType.FREEZE),
    )
    game_round.queue_pending_actions([
        PendingAction(
            source_player=game.players[1],
            card=ActionCard(ActionType.FLIP_THREE),
        )
    ])

    observation = create_agent_observation(
        game=game,
        player_index=0,
    )

    discarded_counts = {
        item.card: item.remaining_count
        for item in observation.discarded_card_counts
    }

    assert observation.own_player_index == 0
    assert observation.own_player.player_index == 0
    assert observation.other_players[0].player_index == 1
    assert observation.next_starting_player_index == 1
    assert discarded_counts[discarded_card] == 1
    assert observation.queued_actions == (
        PendingActionObservation(
            source_player_index=1,
            action_type=ActionType.FLIP_THREE,
        ),
    )


def test_target_observation_contains_player_index() -> None:
    game = create_started_game()
    game_round = game.current_round

    assert game_round is not None

    game_round.pending_action = PendingAction(
        source_player=game.players[0],
        card=ActionCard(ActionType.FREEZE),
    )

    targets = create_valid_target_options(game)

    assert all(
        target.player.player_index == target.player_index
        for target in targets
    )


def test_pending_action_observation_rejects_negative_index() -> None:
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        PendingActionObservation(
            source_player_index=-1,
            action_type=ActionType.FREEZE,
        )
