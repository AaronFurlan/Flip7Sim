import pytest

from flip7.game.cards import (
    ActionCard,
    ActionType,
    ModifierCard,
    ModifierType,
    NumberCard,
)
from flip7.agents.base_agent import (
    AgentObservation,
    BaseAgent,
    DeckCardObservation,
    PendingActionObservation,
    TargetOption,
    TurnDecision,
)
from flip7.agents.random_agent import RandomAgent
from flip7.agents.threshold_agent import SimpleThresholdAgent
from flip7.mcts.agent_adapter import (
    AgentPolicyAdapter,
    create_agent_observation,
    create_player_observation,
    create_target_options,
)
from flip7.mcts.action import (
    Flip7SearchAction,
    SearchActionType,
)
from flip7.mcts.state import (
    Flip7SearchState,
    SearchDecisionPhase,
    SearchPendingAction,
    SearchPlayerState,
)


def create_state(**overrides: object) -> Flip7SearchState:
    arguments: dict[str, object] = {
        "players": [
            SearchPlayerState(2, "Charlie"),
            SearchPlayerState(0, "Alice"),
            SearchPlayerState(
                1,
                "Bob",
                total_score=30,
                round_cards=[NumberCard(5)],
            ),
        ],
        "remaining_card_counts": {
            NumberCard(1): 2,
            NumberCard(2): 1,
        },
        "discarded_card_counts": {
            NumberCard(9): 1,
        },
        "current_player_index": 1,
        "root_player_index": 0,
        "next_starting_player_index": 2,
        "winning_score": 150,
        "queued_actions": [
            SearchPendingAction(
                source_player_index=2,
                action_type=ActionType.FREEZE,
            )
        ],
    }
    arguments.update(overrides)
    return Flip7SearchState(**arguments)  # type: ignore[arg-type]


class InvalidTargetAgent(BaseAgent):
    def choose_hit_or_stay(
        self,
        observation: AgentObservation,
    ) -> TurnDecision:
        return TurnDecision.HIT

    def choose_action_target(
        self,
        observation: AgentObservation,
        action_type: ActionType,
        valid_targets: tuple[TargetOption, ...],
    ) -> TargetOption:
        return TargetOption(
            player_index=99,
            player=valid_targets[0].player,
        )


def test_create_player_observation_maps_all_fields() -> None:
    round_cards = [
        NumberCard(4),
        NumberCard(6),
        ModifierCard(ModifierType.MULTIPLIER, 2),
        ModifierCard(ModifierType.ADDITIVE, 3),
        ActionCard(ActionType.SECOND_CHANCE),
    ]
    player_state = SearchPlayerState(
        player_index=2,
        player_name="Charlie",
        total_score=40,
        round_cards=round_cards,
        is_active=False,
        has_stayed=True,
        has_second_chance=True,
    )

    observation = create_player_observation(player_state)

    assert observation.player_index == 2
    assert observation.player_name == "Charlie"
    assert observation.total_score == 40
    assert observation.current_round_score == 23
    assert observation.number_of_unique_numbers == 2
    assert not observation.is_active
    assert observation.has_stayed
    assert not observation.has_busted
    assert observation.has_second_chance
    assert observation.round_cards == tuple(round_cards)


def test_create_player_observation_counts_unique_numbers() -> None:
    player_state = SearchPlayerState(
        player_index=0,
        player_name="Alice",
        round_cards=[
            NumberCard(5),
            NumberCard(5),
            NumberCard(8),
        ],
        is_active=False,
        has_busted=True,
    )

    observation = create_player_observation(player_state)

    assert observation.number_of_unique_numbers == 2
    assert observation.current_round_score == 0
    assert observation.has_busted


def test_player_observation_has_independent_card_collection() -> None:
    player_state = SearchPlayerState(
        player_index=0,
        player_name="Alice",
        round_cards=[NumberCard(3)],
    )

    observation = create_player_observation(player_state)
    player_state.round_cards.append(NumberCard(7))

    assert observation.round_cards == (NumberCard(3),)


def test_create_agent_observation_maps_complete_state() -> None:
    state = create_state()

    observation = create_agent_observation(
        state=state,
        player_index=1,
    )

    assert observation.own_player.player_name == "Bob"
    assert tuple(
        player.player_name
        for player in observation.other_players
    ) == ("Alice", "Charlie")
    assert observation.valid_turn_decisions == (
        TurnDecision.HIT,
        TurnDecision.STAY,
    )
    assert observation.remaining_card_count == 3
    assert observation.deck_content == [
        NumberCard(1),
        NumberCard(1),
        NumberCard(2),
    ]
    assert observation.deck_card_counts == (
        DeckCardObservation(NumberCard(1), 2),
        DeckCardObservation(NumberCard(2), 1),
    )
    assert observation.discarded_card_counts == (
        DeckCardObservation(NumberCard(9), 1),
    )
    assert observation.queued_actions == (
        PendingActionObservation(
            source_player_index=2,
            action_type=ActionType.FREEZE,
        ),
    )
    assert observation.own_player_index == 1
    assert observation.next_starting_player_index == 2
    assert observation.winning_score == 150


def test_player_without_cards_can_only_hit() -> None:
    players = [
        SearchPlayerState(0, "Alice"),
        SearchPlayerState(1, "Bob"),
    ]
    state = create_state(
        players=players,
        current_player_index=0,
        root_player_index=0,
        next_starting_player_index=1,
        queued_actions=[],
    )

    observation = create_agent_observation(state, 0)

    assert observation.valid_turn_decisions == (
        TurnDecision.HIT,
    )


def test_action_target_phase_has_no_turn_decisions() -> None:
    pending_action = SearchPendingAction(
        source_player_index=1,
        action_type=ActionType.FLIP_THREE,
    )
    state = create_state(
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
    )

    observation = create_agent_observation(state, 1)

    assert observation.valid_turn_decisions == ()


def test_agent_observation_requires_current_player() -> None:
    state = create_state()

    try:
        create_agent_observation(state, 0)
    except ValueError as error:
        assert str(error) == (
            "The observation must belong to the current player."
        )
    else:
        raise AssertionError("Expected ValueError")


def test_create_target_options_preserves_action_order() -> None:
    state = create_state()
    valid_actions = (
        Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=2,
        ),
        Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=0,
        ),
    )

    target_options = create_target_options(
        state=state,
        valid_actions=valid_actions,
    )

    assert tuple(
        target.player_index
        for target in target_options
    ) == (2, 0)
    assert tuple(
        target.player.player_name
        for target in target_options
    ) == ("Charlie", "Alice")
    assert target_options[0].player.player_index == 2
    assert target_options[1].player.player_index == 0


def test_create_target_options_accepts_empty_actions() -> None:
    assert create_target_options(create_state(), ()) == ()


@pytest.mark.parametrize(
    "action_type",
    [SearchActionType.HIT, SearchActionType.STAY],
)
def test_create_target_options_rejects_turn_action(
    action_type: SearchActionType,
) -> None:
    action = Flip7SearchAction(action_type)

    with pytest.raises(
        ValueError,
        match="Target options require target actions",
    ):
        create_target_options(create_state(), (action,))


def test_create_target_options_rejects_unknown_player() -> None:
    action = Flip7SearchAction(
        SearchActionType.ACTION_TARGET,
        target_player_index=9,
    )

    with pytest.raises(
        ValueError,
        match="references an unknown player",
    ):
        create_target_options(create_state(), (action,))


def test_policy_adapter_uses_threshold_agent_to_hit() -> None:
    valid_actions = (
        Flip7SearchAction(SearchActionType.HIT),
        Flip7SearchAction(SearchActionType.STAY),
    )
    adapter = AgentPolicyAdapter(
        SimpleThresholdAgent("Simulated opponent")
    )

    selected_action = adapter.choose_action(
        state=create_state(),
        valid_actions=valid_actions,
    )

    assert selected_action == Flip7SearchAction(
        SearchActionType.HIT
    )


def test_policy_adapter_uses_threshold_agent_to_stay() -> None:
    players = [
        SearchPlayerState(0, "Alice"),
        SearchPlayerState(
            1,
            "Bob",
            round_cards=[NumberCard(11), NumberCard(12)],
        ),
        SearchPlayerState(2, "Charlie"),
    ]
    valid_actions = (
        Flip7SearchAction(SearchActionType.HIT),
        Flip7SearchAction(SearchActionType.STAY),
    )
    adapter = AgentPolicyAdapter(
        SimpleThresholdAgent("Simulated opponent")
    )

    selected_action = adapter.choose_action(
        state=create_state(players=players),
        valid_actions=valid_actions,
    )

    assert selected_action == Flip7SearchAction(
        SearchActionType.STAY
    )


def test_policy_adapter_uses_threshold_agent_for_target() -> None:
    players = [
        SearchPlayerState(0, "Alice", total_score=20),
        SearchPlayerState(1, "Bob", total_score=30),
        SearchPlayerState(2, "Charlie", total_score=80),
    ]
    pending_action = SearchPendingAction(
        source_player_index=1,
        action_type=ActionType.FREEZE,
    )
    valid_actions = tuple(
        Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=player_index,
        )
        for player_index in (0, 1, 2)
    )
    state = create_state(
        players=players,
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
    )
    adapter = AgentPolicyAdapter(
        SimpleThresholdAgent("Simulated opponent")
    )

    selected_action = adapter.choose_action(
        state=state,
        valid_actions=valid_actions,
    )

    assert selected_action == Flip7SearchAction(
        SearchActionType.ACTION_TARGET,
        target_player_index=2,
    )


def test_policy_adapter_can_use_random_agent() -> None:
    valid_actions = (
        Flip7SearchAction(SearchActionType.HIT),
    )
    adapter = AgentPolicyAdapter(
        RandomAgent("Simulated opponent", seed=42)
    )

    selected_action = adapter.choose_action(
        state=create_state(),
        valid_actions=valid_actions,
    )

    assert selected_action == valid_actions[0]


def test_policy_adapter_rejects_empty_actions() -> None:
    adapter = AgentPolicyAdapter(
        SimpleThresholdAgent("Simulated opponent")
    )

    with pytest.raises(
        ValueError,
        match="requires valid actions",
    ):
        adapter.choose_action(create_state(), ())


def test_policy_adapter_rejects_invalid_turn_action() -> None:
    players = [
        SearchPlayerState(0, "Alice"),
        SearchPlayerState(
            1,
            "Bob",
            round_cards=[NumberCard(11), NumberCard(12)],
        ),
        SearchPlayerState(2, "Charlie"),
    ]
    adapter = AgentPolicyAdapter(
        SimpleThresholdAgent("Simulated opponent")
    )

    with pytest.raises(
        ValueError,
        match="selected an invalid turn action",
    ):
        adapter.choose_action(
            state=create_state(players=players),
            valid_actions=(
                Flip7SearchAction(SearchActionType.HIT),
            ),
        )


def test_policy_adapter_rejects_invalid_target() -> None:
    pending_action = SearchPendingAction(
        source_player_index=1,
        action_type=ActionType.FREEZE,
    )
    state = create_state(
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
    )
    valid_actions = (
        Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=0,
        ),
    )
    adapter = AgentPolicyAdapter(
        InvalidTargetAgent("Invalid agent")
    )

    with pytest.raises(
        ValueError,
        match="selected an invalid target",
    ):
        adapter.choose_action(
            state=state,
            valid_actions=valid_actions,
        )
