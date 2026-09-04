from flip7.agents.base_agent import (
    AgentObservation,
    DeckCardObservation,
    PlayerObservation,
)
from flip7.game.cards import (
    ActionType,
    Card,
)
from flip7.mcts.state import (
    Flip7SearchState,
    SearchDecisionPhase,
    SearchPendingAction,
    SearchPlayerState,
)


def create_search_player_state(
    observation: PlayerObservation,
) -> SearchPlayerState:
    if observation.player_index is None:
        raise ValueError(
            "A player observation requires a player index "
            "for MCTS."
        )

    return SearchPlayerState(
        player_index=observation.player_index,
        player_name=observation.player_name,
        total_score=observation.total_score,
        round_cards=list(observation.round_cards),
        is_active=observation.is_active,
        has_stayed=observation.has_stayed,
        has_busted=observation.has_busted,
        has_second_chance=(
            observation.has_second_chance
        ),
    )


def create_card_count_dictionary(
    observations: tuple[
        DeckCardObservation,
        ...,
    ],
) -> dict[Card, int]:
    card_counts: dict[Card, int] = {}

    for observation in observations:
        if observation.card in card_counts:
            raise ValueError(
                "A card type occurs more than once "
                "in the card-count observations."
            )

        card_counts[observation.card] = (
            observation.remaining_count
        )

    return card_counts


def create_search_state(
    observation: AgentObservation,
    pending_action_type: ActionType | None = None,
) -> Flip7SearchState:
    if observation.own_player.player_index is None:
        raise ValueError(
            "The own player observation requires "
            "a player index for MCTS."
        )

    if (
        observation.own_player.player_index
        != observation.own_player_index
    ):
        raise ValueError(
            "The own player index does not match "
            "the agent observation."
        )

    player_observations = (
        observation.own_player,
        *observation.other_players,
    )

    players = [
        create_search_player_state(player_observation)
        for player_observation in player_observations
    ]
    players.sort(key=lambda player: player.player_index)

    remaining_card_counts = (
        create_card_count_dictionary(
            observation.deck_card_counts
        )
    )

    if (
        sum(remaining_card_counts.values())
        != observation.remaining_card_count
    ):
        raise ValueError(
            "The remaining card counts do not match "
            "the total remaining card count."
        )

    discarded_card_counts = (
        create_card_count_dictionary(
            observation.discarded_card_counts
        )
    )

    queued_actions = [
        SearchPendingAction(
            source_player_index=(
                queued_action.source_player_index
            ),
            action_type=queued_action.action_type,
        )
        for queued_action in observation.queued_actions
    ]

    if pending_action_type is None:
        decision_phase = SearchDecisionPhase.TURN
        pending_action = None
    else:
        decision_phase = (
            SearchDecisionPhase.ACTION_TARGET
        )
        pending_action = SearchPendingAction(
            source_player_index=(
                observation.own_player_index
            ),
            action_type=pending_action_type,
        )

    return Flip7SearchState(
        players=players,
        remaining_card_counts=remaining_card_counts,
        discarded_card_counts=discarded_card_counts,
        current_player_index=(
            observation.own_player_index
        ),
        root_player_index=(
            observation.own_player_index
        ),
        next_starting_player_index=(
            observation.next_starting_player_index
        ),
        winning_score=observation.winning_score,
        decision_phase=decision_phase,
        pending_action=pending_action,
        queued_actions=queued_actions,
    )