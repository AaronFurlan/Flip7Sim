from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flip7.game.player import Player
    from flip7.game.round import GameRound


class BaseAction(ABC):
    @abstractmethod
    def execute(
        self,
        game_round: GameRound,
        source_player: Player,
        target_player: Player,
    ) -> None:
        raise NotImplementedError