from flip7.agents.base_agent import (
    AgentObservation,
    BaseAgent,
    PlayerObservation,
    TargetOption,
    TurnDecision,
)
from flip7.game.constants import DEFAULT_WINNING_SCORE
from flip7.game.deck import Deck
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

    game_round = game.current_round

    if (
        not own_player.is_active
        or not game_round.is_initial_deal_complete
        or game_round.pending_action is not None
    ):
        valid_turn_decisions = ()

    elif own_player.round_cards:
        valid_turn_decisions = (
            TurnDecision.HIT,
            TurnDecision.STAY,
        )

    else:
        valid_turn_decisions = (
            TurnDecision.HIT,
        )

    return AgentObservation(
        own_player=own_player,
        other_players=other_players,
        remaining_card_count=game.deck.remaining_card_count(),
        winning_score=game.winning_score,
        valid_turn_decisions=valid_turn_decisions,
    )

def create_valid_target_options(game: Flip7Game) -> tuple[TargetOption, ...]:
    if not game.has_started:
        raise RuntimeError("Target options cannot be created before the game starts.")

    game_round = game.current_round

    if game_round is None or game_round.has_finished:
        raise RuntimeError("Target options require an active round.")

    if game_round.pending_action is None:
        raise RuntimeError("Target options require a pending action.")

    valid_targets = game_round.get_valid_action_targets()
    target_options: list[TargetOption] = []

    for target_player in valid_targets:
        player_index = next(
            (
                index
                for index, player in enumerate(game.players)
                if player is target_player
            ),
            None,
        )

        if player_index is None:
            raise RuntimeError("An action target does not belong to the game.")

        target_options.append(
            TargetOption(
                player_index=player_index,
                player=create_player_observation(target_player),
            )
        )

    return tuple(target_options)

class GameSimulation:
    def __init__(
        self,
        agents: list[BaseAgent],
        winning_score: int = DEFAULT_WINNING_SCORE,
        seed: int | None = None,
        deck: Deck | None = None,
    ) -> None:
        self.agents = list(agents)
        self.players = [Player(agent.player_name) for agent in self.agents]

        self.game = Flip7Game(
            players=self.players,
            winning_score=winning_score,
            seed=seed,
            deck=deck,
        )

        self.rounds_played = 0

    def run(self) -> list[Player]:
        self.game.start_game()

        while True:
            self._play_current_round()

            game_round = self.game.current_round

            if game_round is None:
                raise RuntimeError("The simulation has no active round.")

            game_round.finish_round()
            self.rounds_played += 1

            if self.game.is_game_finished():
                return self.game.get_winners()

            self.game.start_new_round()

    def _play_current_round(self) -> None:
        game_round = self.game.current_round

        if game_round is None:
            raise RuntimeError(
                "The simulation has no active round."
            )

        current_player_index = 0

        while not game_round.is_round_finished():
            if game_round.pending_action is not None:
                self._resolve_pending_action()
                continue

            if not game_round.is_initial_deal_complete:
                game_round.continue_starting_deal()
                continue

            player = self.players[current_player_index]

            current_player_index = (
                current_player_index + 1
            ) % len(self.players)

            if not player.is_active:
                continue

            observation = create_agent_observation(
                game=self.game,
                player_index=self.players.index(player),
            )

            decision = self.agents[
                self.players.index(player)
            ].choose_hit_or_stay(observation)

            if decision is TurnDecision.HIT:
                game_round.draw_card_for_player(player)

            elif decision is TurnDecision.STAY:
                game_round.player_stays(player)

            else:
                raise RuntimeError(f"Unsupported turn decision: {decision!r}")

    def _resolve_pending_action(self) -> None:
        game_round = self.game.current_round

        if game_round is None:
            raise RuntimeError("The simulation has no active round.")

        pending_action = game_round.pending_action

        if pending_action is None:
            raise RuntimeError("The simulation has no pending action.")

        source_player_index = next(
            (
                index
                for index, player in enumerate(self.players)
                if player is pending_action.source_player
            ),
            None,
        )

        if source_player_index is None:
            raise RuntimeError("The action source does not belong to the simulation.")

        observation = create_agent_observation(
            game=self.game,
            player_index=source_player_index,
        )
        valid_targets = create_valid_target_options(self.game)

        chosen_target = self.agents[
            source_player_index
        ].choose_action_target(
            observation=observation,
            action_type=pending_action.card.action_type,
            valid_targets=valid_targets,
        )

        if chosen_target not in valid_targets:
            raise RuntimeError(
                "The agent selected an invalid action target."
            )

        target_player = self.players[
            chosen_target.player_index
        ]

        game_round.resolve_pending_action(target_player)