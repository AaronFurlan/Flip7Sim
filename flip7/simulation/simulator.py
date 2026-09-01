from flip7.agents.base_agent import (
    AgentObservation,
    PlayerObservation,
)
from flip7.game.game import Flip7Game
from flip7.game.player import Player
from flip7.game.scoring import calculate_round_score

def create_player_observation(player: Player) -> PlayerObservation:
    unique_number_count = len({card.number for card in player.get_number_cards()})

    return PlayerObservation(
        player_name=player.player_name,
        total_score=player.total_score,
        current_round_score=calculate_round_score(player),
        number_of_unique_numbers=unique_number_count,
        is_active=player.is_active,
        has_second_chance=player.has_second_chance,
        has_stayed=player.has_stayed,
        has_busted=player.has_busted,
        round_cards=tuple(player.round_cards),
    )


def create_agent_observation(game: Flip7Game, player_index: int) -> AgentObservation:
    if not game.has_started:
        raise RuntimeError("An observation cannot be created before the game starts.")

    if game.current_round is None or game.current_round.has_finished:
        raise RuntimeError(
            "An observation requires an active round."
        )

    if not 0 <= player_index < len(game.players):
        raise IndexError("The player index is out of range.")

    own_player = create_player_observation(
        game.players[player_index]
    )

    other_players = tuple(
        create_player_observation(player)
        for index, player in enumerate(game.players)
        if index != player_index
    )

    return AgentObservation(
        own_player=own_player,
        other_players=other_players,
        remaining_card_count=game.deck.remaining_card_count(),
        winning_score=game.winning_score,
    )