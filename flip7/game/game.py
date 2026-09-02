from flip7.game.constants import DEFAULT_WINNING_SCORE, MINIMUM_PLAYER_COUNT
from flip7.game.deck import Deck
from flip7.game.player import Player
from flip7.game.round import GameRound

class GameStateError(RuntimeError):
    """Raised when an operation is invalid for the game state."""

class Flip7Game:
    def __init__(
            self,
            players: list[Player],
            winning_score: int = DEFAULT_WINNING_SCORE,
            seed: int | None = None,
            deck: Deck | None = None,
    ) -> None:
        if len(players) < MINIMUM_PLAYER_COUNT:
            raise ValueError(f"At least {MINIMUM_PLAYER_COUNT} player(s) are required.")
        if winning_score <= 0:
            raise ValueError("The winning score must be positive.")
        if deck is not None and seed is not None:
            raise ValueError("Pass either a seed or a custom deck, not both.")

        self.players = list(players)
        self.winning_score = winning_score
        self.current_round: GameRound | None = None
        self.has_started = False
        self._next_starting_player_index = 0
        self._uses_custom_deck = deck is not None

        if deck is None:
            self.deck = Deck(seed=seed)
        else:
            self.deck = deck

    def start_game(self) -> GameRound:
        if self.has_started:
            raise GameStateError("The game has already started.")

        for player in self.players:
            player.total_score = 0
            player.reset_for_new_round()

        if not self._uses_custom_deck:
            self.deck.shuffle()

        self._next_starting_player_index = 0

        self.has_started = True

        return self.start_new_round()

    def start_new_round(self) -> GameRound:
        if not self.has_started:
            raise GameStateError("The game has not started.")

        if self.current_round is not None and not self.current_round.has_finished:
            raise GameStateError("A round is already in progress.")

        if self.is_game_finished():
            raise GameStateError("The game is already finished.")

        starting_player_index = self._next_starting_player_index

        self.current_round = GameRound(
            players=self.players,
            deck=self.deck,
            starting_player_index=starting_player_index,
        )

        self.current_round.start_round()

        self._next_starting_player_index = (starting_player_index + 1) % len(self.players)

        return self.current_round

    def is_game_finished(self) -> bool:
        if not self.has_started:
            raise GameStateError("The game has not started.")

        if self.current_round is not None and not self.current_round.has_finished:
            return False

        return any(player.total_score >= self.winning_score for player in self.players)

    def get_winners(self) -> list[Player]:
        if not self.is_game_finished():
            return []

        highest_score = max(player.total_score for player in self.players)

        return [player for player in self.players if player.total_score == highest_score]

