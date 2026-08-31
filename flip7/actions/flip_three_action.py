from __future__ import annotations

from typing import TYPE_CHECKING

from flip7.actions.base_action import BaseAction

if TYPE_CHECKING:
    from flip7.game.player import Player
    from flip7.game.round import GameRound, PendingAction


FLIP_THREE_DRAW_COUNT = 3


class FlipThreeAction(BaseAction):
    def execute(
        self,
        game_round: GameRound,
        source_player: Player,
        target_player: Player,
    ) -> None:
        deferred_actions: list[PendingAction] = []

        for _ in range(FLIP_THREE_DRAW_COUNT):
            if not target_player.is_active:
                break

            if game_round.check_for_flip_seven(target_player):
                break

            pending_action = (
                game_round.draw_card_for_flip_three(
                    target_player
                )
            )

            if pending_action is not None:
                deferred_actions.append(pending_action)

            if target_player.has_busted:
                break

            if game_round.check_for_flip_seven(target_player):
                break

        if (
            target_player.has_busted
            or game_round.check_for_flip_seven(target_player)
        ):
            game_round.deck.discard_cards(
                action.card
                for action in deferred_actions
            )
            return

        game_round.queue_pending_actions(deferred_actions)