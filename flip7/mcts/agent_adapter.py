from flip7.agents.base_agent import (
    AgentObservation,
    BaseAgent,
    DeckCardObservation,
    PendingActionObservation,
    PlayerObservation,
    TargetOption,
    TurnDecision,
)
from flip7.game.cards import NumberCard
from flip7.game.player import Player
from flip7.game.scoring import calculate_round_score
from flip7.mcts.state import (
    Flip7SearchState,
    SearchDecisionPhase,
    SearchPlayerState,
)
from flip7.mcts.action import (
    Flip7SearchAction,
    SearchActionType,
)


def create_player_observation(
    player_state: SearchPlayerState,
) -> PlayerObservation:
    scoring_player = Player(player_state.player_name)
    scoring_player.total_score = player_state.total_score
    scoring_player.round_cards = list(player_state.round_cards)
    scoring_player.is_active = player_state.is_active
    scoring_player.has_stayed = player_state.has_stayed
    scoring_player.has_busted = player_state.has_busted
    scoring_player.has_second_chance = (
        player_state.has_second_chance
    )

    unique_number_count = len({
        card.number
        for card in player_state.round_cards
        if isinstance(card, NumberCard)
    })

    return PlayerObservation(
        player_name=player_state.player_name,
        total_score=player_state.total_score,
        current_round_score=calculate_round_score(
            scoring_player
        ),
        number_of_unique_numbers=unique_number_count,
        is_active=player_state.is_active,
        has_second_chance=player_state.has_second_chance,
        has_stayed=player_state.has_stayed,
        has_busted=player_state.has_busted,
        round_cards=tuple(player_state.round_cards),
        player_index=player_state.player_index,
    )

def create_agent_observation(
    state: Flip7SearchState,
    player_index: int,
) -> AgentObservation:
    if player_index != state.current_player_index:
        raise ValueError(
            "The observation must belong to the current player."
        )

    sorted_players = sorted(
        state.players,
        key=lambda player: player.player_index,
    )

    player_observations = {
        player.player_index: create_player_observation(player)
        for player in sorted_players
    }

    own_player = player_observations.get(player_index)

    if own_player is None:
        raise ValueError(
            "The requested player does not exist."
        )

    other_players = tuple(
        observation
        for index, observation
        in player_observations.items()
        if index != player_index
    )

    if (
        state.decision_phase is SearchDecisionPhase.TURN
        and own_player.is_active
        and not state.round_finished
    ):
        valid_turn_decisions = [TurnDecision.HIT]

        if own_player.round_cards:
            valid_turn_decisions.append(TurnDecision.STAY)

        valid_turn_decisions_tuple = tuple(
            valid_turn_decisions
        )
    else:
        valid_turn_decisions_tuple = ()

    deck_content = [
        card
        for card, count in state.remaining_card_counts.items()
        for _ in range(count)
    ]

    deck_card_counts = tuple(
        DeckCardObservation(
            card=card,
            remaining_count=count,
        )
        for card, count in state.remaining_card_counts.items()
    )

    discarded_card_counts = tuple(
        DeckCardObservation(
            card=card,
            remaining_count=count,
        )
        for card, count in state.discarded_card_counts.items()
    )

    queued_actions = tuple(
        PendingActionObservation(
            source_player_index=action.source_player_index,
            action_type=action.action_type,
        )
        for action in state.queued_actions
    )

    return AgentObservation(
        own_player=own_player,
        other_players=other_players,
        remaining_card_count=len(deck_content),
        winning_score=state.winning_score,
        deck_content=deck_content,
        valid_turn_decisions=valid_turn_decisions_tuple,
        deck_card_counts=deck_card_counts,
        discarded_card_counts=discarded_card_counts,
        queued_actions=queued_actions,
        own_player_index=player_index,
        next_starting_player_index=(
            state.next_starting_player_index
        ),
    )

def create_target_options(
    state: Flip7SearchState,
    valid_actions: tuple[Flip7SearchAction, ...],
) -> tuple[TargetOption, ...]:
    target_options: list[TargetOption] = []

    for action in valid_actions:
        if (
            action.action_type
            is not SearchActionType.ACTION_TARGET
            or action.target_player_index is None
        ):
            raise ValueError(
                "Target options require target actions."
            )

        player_state = next(
            (
                player
                for player in state.players
                if (
                    player.player_index
                    == action.target_player_index
                )
            ),
            None,
        )

        if player_state is None:
            raise ValueError(
                "A target action references an unknown player."
            )

        target_options.append(
            TargetOption(
                player_index=player_state.player_index,
                player=create_player_observation(
                    player_state
                ),
            )
        )

    return tuple(target_options)

class AgentPolicyAdapter:
    """Uses an existing agent inside an MCTS simulation."""

    def __init__(self, agent: BaseAgent) -> None:
        self.agent = agent

    def choose_action(
        self,
        state: Flip7SearchState,
        valid_actions: tuple[Flip7SearchAction, ...],
    ) -> Flip7SearchAction:
        if not valid_actions:
            raise ValueError(
                "The agent adapter requires valid actions."
            )

        observation = create_agent_observation(
            state=state,
            player_index=state.current_player_index,
        )

        if state.decision_phase is SearchDecisionPhase.TURN:
            return self._choose_turn_action(
                observation=observation,
                valid_actions=valid_actions,
            )

        if (
            state.decision_phase
            is SearchDecisionPhase.ACTION_TARGET
        ):
            return self._choose_target_action(
                state=state,
                observation=observation,
                valid_actions=valid_actions,
            )

        raise ValueError(
            "The search state has an unsupported decision phase."
        )

    def _choose_turn_action(
        self,
        observation: AgentObservation,
        valid_actions: tuple[Flip7SearchAction, ...],
    ) -> Flip7SearchAction:
        decision = self.agent.choose_hit_or_stay(
            observation
        )

        if decision is TurnDecision.HIT:
            selected_action = Flip7SearchAction(
                SearchActionType.HIT
            )

        elif decision is TurnDecision.STAY:
            selected_action = Flip7SearchAction(
                SearchActionType.STAY
            )

        else:
            raise ValueError(
                "The agent returned an unsupported turn decision."
            )

        if selected_action not in valid_actions:
            raise ValueError(
                "The agent selected an invalid turn action."
            )

        return selected_action

    def _choose_target_action(
        self,
        state: Flip7SearchState,
        observation: AgentObservation,
        valid_actions: tuple[Flip7SearchAction, ...],
    ) -> Flip7SearchAction:
        pending_action = state.pending_action

        if pending_action is None:
            raise RuntimeError(
                "A target decision requires a pending action."
            )

        valid_targets = create_target_options(
            state=state,
            valid_actions=valid_actions,
        )

        selected_target = self.agent.choose_action_target(
            observation=observation,
            action_type=pending_action.action_type,
            valid_targets=valid_targets,
        )

        selected_action = Flip7SearchAction(
            action_type=SearchActionType.ACTION_TARGET,
            target_player_index=(
                selected_target.player_index
            ),
        )

        if selected_action not in valid_actions:
            raise ValueError(
                "The agent selected an invalid target."
            )

        return selected_action