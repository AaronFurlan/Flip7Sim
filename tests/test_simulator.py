import pytest

from flip7.game.cards import (
    ActionCard,
    ActionType,
    ModifierCard,
    ModifierType,
    NumberCard,
)
from flip7.game.deck import Deck
from flip7.game.game import Flip7Game
from flip7.game.player import Player
from flip7.simulation.simulator import (
    create_agent_observation,
    create_deck_card_observations,
    create_player_observation,
    create_valid_target_options,
)


def create_started_game() -> Flip7Game:
    players = [
        Player("Alice"),
        Player("Bob"),
    ]

    deck = Deck(
        cards=[
            NumberCard(8),
            NumberCard(3),
        ]
    )

    game = Flip7Game(
        players=players,
        winning_score=150,
        deck=deck,
    )
    game.start_game()

    return game


def test_create_player_observation_maps_player_state() -> None:
    player = Player("Alice")
    player.total_score = 80
    player.add_card(NumberCard(4))
    player.add_card(NumberCard(7))
    player.add_card(
        ModifierCard(
            modifier_type=ModifierType.ADDITIVE,
            value=2,
        )
    )
    player.has_second_chance = True
    player.has_stayed = True
    player.is_active = False

    observation = create_player_observation(player)

    assert observation.player_name == "Alice"
    assert observation.total_score == 80
    assert observation.current_round_score == 13
    assert observation.number_of_unique_numbers == 2
    assert observation.is_active is False
    assert observation.has_second_chance is True
    assert observation.has_stayed is True
    assert observation.has_busted is False
    assert observation.round_cards == tuple(player.round_cards)


def test_player_observation_uses_card_snapshot() -> None:
    player = Player("Alice")
    player.add_card(NumberCard(4))

    observation = create_player_observation(player)

    player.add_card(NumberCard(7))

    assert observation.round_cards == (NumberCard(4),)


def test_create_agent_observation_maps_game_state() -> None:
    game = create_started_game()

    observation = create_agent_observation(
        game=game,
        player_index=0,
    )

    assert observation.own_player.player_name == "Alice"
    assert observation.own_player.current_round_score == 3

    assert len(observation.other_players) == 1
    assert observation.other_players[0].player_name == "Bob"
    assert observation.other_players[0].current_round_score == 8

    assert observation.remaining_card_count == 0
    assert observation.winning_score == 150


def test_agent_observation_requires_started_game() -> None:
    game = Flip7Game(
        players=[
            Player("Alice"),
            Player("Bob"),
        ]
    )

    with pytest.raises(
        RuntimeError,
        match="before the game starts",
    ):
        create_agent_observation(game, player_index=0)


def test_agent_observation_rejects_invalid_player_index() -> None:
    game = create_started_game()

    with pytest.raises(
        IndexError,
        match="out of range",
    ):
        create_agent_observation(game, player_index=2)


def test_agent_observation_requires_active_round() -> None:
    game = create_started_game()
    game_round = game.current_round

    assert game_round is not None

    game_round.player_stays(game.players[0])
    game_round.player_stays(game.players[1])
    game_round.finish_round()

    with pytest.raises(
        RuntimeError,
        match="active round",
    ):
        create_agent_observation(game, player_index=0)

def create_game_with_pending_action(
    action_type: ActionType,
) -> Flip7Game:
    players = [
        Player("Alice"),
        Player("Bob"),
    ]

    deck = Deck(
        cards=[
            NumberCard(8),
            ActionCard(action_type=action_type),
        ]
    )

    game = Flip7Game(
        players=players,
        deck=deck,
    )
    game.start_game()

    return game


def test_create_valid_target_options_maps_players() -> None:
    game = create_game_with_pending_action(
        ActionType.FREEZE
    )

    target_options = create_valid_target_options(game)

    assert tuple(
        option.player_index
        for option in target_options
    ) == (0, 1)

    assert tuple(
        option.player.player_name
        for option in target_options
    ) == ("Alice", "Bob")


def test_target_options_use_round_target_rules() -> None:
    game = create_game_with_pending_action(
        ActionType.SECOND_CHANCE
    )

    game.players[1].has_second_chance = True

    target_options = create_valid_target_options(game)

    assert len(target_options) == 1
    assert target_options[0].player_index == 0
    assert target_options[0].player.player_name == "Alice"


def test_target_options_require_pending_action() -> None:
    game = create_started_game()

    with pytest.raises(
        RuntimeError,
        match="pending action",
    ):
        create_valid_target_options(game)


def test_target_options_require_started_game() -> None:
    game = Flip7Game(
        players=[
            Player("Alice"),
            Player("Bob"),
        ]
    )

    with pytest.raises(
        RuntimeError,
        match="before the game starts",
    ):
        create_valid_target_options(game)

def test_deck_card_observations_are_sorted() -> None:
    deck = Deck()

    observations = create_deck_card_observations(deck)

    number_observations = observations[:13]
    action_observations = observations[13:16]
    modifier_observations = observations[16:]

    assert tuple(
        observation.card.number
        for observation in number_observations
        if isinstance(observation.card, NumberCard)
    ) == tuple(range(13))

    assert tuple(
        observation.card.action_type
        for observation in action_observations
        if isinstance(observation.card, ActionCard)
    ) == (
        ActionType.FREEZE,
        ActionType.FLIP_THREE,
        ActionType.SECOND_CHANCE,
    )

    assert tuple(
        (
            observation.card.modifier_type,
            observation.card.value,
        )
        for observation in modifier_observations
        if isinstance(observation.card, ModifierCard)
    ) == (
        (ModifierType.ADDITIVE, 2),
        (ModifierType.ADDITIVE, 4),
        (ModifierType.ADDITIVE, 6),
        (ModifierType.ADDITIVE, 8),
        (ModifierType.ADDITIVE, 10),
        (ModifierType.MULTIPLIER, 2),
    )

def test_agent_observation_contains_deck_counts() -> None:
    game = create_started_game()

    observation = create_agent_observation(
        game=game,
        player_index=0,
    )

    assert sum(
        card.remaining_count
        for card in observation.deck_card_counts
    ) == observation.remaining_card_count

    assert all(
        card.remaining_count == 0
        for card in observation.deck_card_counts
    )