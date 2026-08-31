from __future__ import annotations

from typing import TYPE_CHECKING

from flip7.actions.base_action import BaseAction

if TYPE_CHECKING:
    from flip7.game.player import Player
    from flip7.game.round import GameRound

class SecondChanceAction(BaseAction):
    def execute(
        self,
        game_round: GameRound,
        source_player: Player,
        target_player: Player,
    ) -> None:
        if target_player.has_second_chance:
            raise ValueError(
                "The target player already has a Second Chance."
            )

        target_player.has_second_chance = True