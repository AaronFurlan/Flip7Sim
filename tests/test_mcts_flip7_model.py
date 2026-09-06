from random import Random

import pytest

from flip7.agents.random_agent import RandomAgent
from flip7.game.cards import (
    ActionCard,
    ActionType,
    ModifierCard,
    ModifierType,
    NumberCard,
)
from flip7.mcts.action import (
    Flip7SearchAction,
    SearchActionType,
)
from flip7.mcts.flip7_model import Flip7SearchModel
from flip7.mcts.state import (
    Flip7SearchState,
    SearchDecisionPhase,
    SearchPendingAction,
    SearchPlayerState,
)


def create_players() -> list[SearchPlayerState]:
    return [
        SearchPlayerState(
            player_index=0,
            player_name="Alice",
        ),
        SearchPlayerState(
            player_index=1,
            player_name="Bob",
        ),
    ]


def create_state(**overrides: object) -> Flip7SearchState:
    arguments: dict[str, object] = {
        "players": create_players(),
        "remaining_card_counts": {NumberCard(1): 1},
        "discarded_card_counts": {},
        "current_player_index": 0,
        "root_player_index": 0,
        "next_starting_player_index": 1,
        "winning_score": 100,
    }
    arguments.update(overrides)
    return Flip7SearchState(**arguments)  # type: ignore[arg-type]


class FirstPositionRandom(Random):
    def randrange(self, stop: int) -> int:
        if stop <= 0:
            raise ValueError("stop must be positive")

        return 0


def test_player_without_cards_can_only_hit() -> None:
    model = Flip7SearchModel()

    assert model.get_valid_actions(create_state()) == (
        Flip7SearchAction(SearchActionType.HIT),
    )


def test_player_with_cards_can_hit_or_stay() -> None:
    players = create_players()
    players[0].round_cards.append(NumberCard(5))

    actions = Flip7SearchModel().get_valid_actions(
        create_state(players=players)
    )

    assert actions == (
        Flip7SearchAction(SearchActionType.HIT),
        Flip7SearchAction(SearchActionType.STAY),
    )


def test_inactive_player_has_no_turn_action() -> None:
    players = create_players()
    players[0].is_active = False
    players[0].has_stayed = True

    assert Flip7SearchModel().get_valid_actions(
        create_state(players=players)
    ) == ()


def test_search_state_must_stop_at_root_player() -> None:
    with pytest.raises(
        RuntimeError,
        match="decision of the root player",
    ):
        Flip7SearchModel().get_valid_actions(
            create_state(current_player_index=1)
        )


def test_internal_actions_allow_opponent_turn() -> None:
    state = create_state(current_player_index=1)

    actions = (
        Flip7SearchModel()
        ._get_valid_actions_for_current_player(state)
    )

    assert actions == (
        Flip7SearchAction(SearchActionType.HIT),
    )


def test_internal_actions_allow_opponent_target_choice() -> None:
    pending_action = SearchPendingAction(
        source_player_index=1,
        action_type=ActionType.FREEZE,
    )
    state = create_state(
        current_player_index=1,
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
    )

    actions = (
        Flip7SearchModel()
        ._get_valid_actions_for_current_player(state)
    )

    assert actions == (
        Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=0,
        ),
        Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=1,
        ),
    )


def test_internal_terminal_state_has_no_actions() -> None:
    state = create_state(
        current_player_index=1,
        round_finished=True,
        game_finished=True,
    )

    actions = (
        Flip7SearchModel()
        ._get_valid_actions_for_current_player(state)
    )

    assert actions == ()


def test_default_opponent_agent_hits_below_threshold() -> None:
    players = create_players()
    players[1].round_cards.append(NumberCard(5))
    state = create_state(
        players=players,
        current_player_index=1,
    )

    action = Flip7SearchModel()._choose_opponent_action(
        state
    )

    assert action == Flip7SearchAction(
        SearchActionType.HIT
    )


def test_default_opponent_agent_stays_at_threshold() -> None:
    players = create_players()
    players[1].round_cards.extend(
        [NumberCard(11), NumberCard(12)]
    )
    state = create_state(
        players=players,
        current_player_index=1,
    )

    action = Flip7SearchModel()._choose_opponent_action(
        state
    )

    assert action == Flip7SearchAction(
        SearchActionType.STAY
    )


def test_custom_random_opponent_agent_is_used() -> None:
    players = create_players()
    players[1].round_cards.append(NumberCard(5))
    state = create_state(
        players=players,
        current_player_index=1,
    )
    model = Flip7SearchModel(
        opponent_agent=RandomAgent(
            "Simulated opponent",
            seed=0,
        )
    )

    action = model._choose_opponent_action(state)

    assert action == Flip7SearchAction(
        SearchActionType.STAY
    )


def test_default_opponent_agent_chooses_action_target() -> None:
    players = [
        SearchPlayerState(0, "Alice", total_score=20),
        SearchPlayerState(1, "Bob", total_score=30),
        SearchPlayerState(2, "Charlie", total_score=80),
    ]
    pending_action = SearchPendingAction(
        source_player_index=1,
        action_type=ActionType.FREEZE,
    )
    state = create_state(
        players=players,
        current_player_index=1,
        next_starting_player_index=2,
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
    )

    action = Flip7SearchModel()._choose_opponent_action(
        state
    )

    assert action == Flip7SearchAction(
        SearchActionType.ACTION_TARGET,
        target_player_index=2,
    )


def test_opponent_action_rejects_root_player() -> None:
    with pytest.raises(
        ValueError,
        match="requires an opponent player",
    ):
        Flip7SearchModel()._choose_opponent_action(
            create_state()
        )


def test_apply_opponent_hit_mutates_search_state() -> None:
    drawn_card = NumberCard(7)
    players = create_players()
    players[1].round_cards.append(NumberCard(5))
    state = create_state(
        players=players,
        current_player_index=1,
        remaining_card_counts={drawn_card: 1},
    )

    action = Flip7SearchModel()._apply_opponent_action(
        state=state,
        random_generator=FirstPositionRandom(),
    )

    assert action == Flip7SearchAction(
        SearchActionType.HIT
    )
    assert state.players[1].round_cards == [
        NumberCard(5),
        drawn_card,
    ]
    assert state.remaining_card_counts[drawn_card] == 0


def test_apply_opponent_stay_mutates_search_state() -> None:
    players = create_players()
    players[1].round_cards.extend(
        [NumberCard(11), NumberCard(12)]
    )
    state = create_state(
        players=players,
        current_player_index=1,
    )

    action = Flip7SearchModel()._apply_opponent_action(
        state=state,
        random_generator=FirstPositionRandom(),
    )

    assert action == Flip7SearchAction(
        SearchActionType.STAY
    )
    assert state.players[1].has_stayed
    assert not state.players[1].is_active


def test_apply_opponent_target_action_mutates_target() -> None:
    players = [
        SearchPlayerState(0, "Alice", total_score=20),
        SearchPlayerState(1, "Bob", total_score=30),
        SearchPlayerState(2, "Charlie", total_score=80),
    ]
    pending_action = SearchPendingAction(
        source_player_index=1,
        action_type=ActionType.FREEZE,
    )
    state = create_state(
        players=players,
        current_player_index=1,
        next_starting_player_index=2,
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
    )

    action = Flip7SearchModel()._apply_opponent_action(
        state=state,
        random_generator=FirstPositionRandom(),
    )

    assert action == Flip7SearchAction(
        SearchActionType.ACTION_TARGET,
        target_player_index=2,
    )
    assert not state.players[2].is_active
    assert ActionCard(
        ActionType.FREEZE
    ) in state.players[2].round_cards


def test_simulate_opponent_hit_returns_to_root() -> None:
    drawn_card = NumberCard(7)
    players = create_players()
    players[1].round_cards.append(NumberCard(5))
    state = create_state(
        players=players,
        current_player_index=1,
        remaining_card_counts={drawn_card: 1},
    )

    did_advance = Flip7SearchModel()._simulate_opponent_turn(
        state=state,
        random_generator=FirstPositionRandom(),
    )

    assert did_advance
    assert state.current_player_index == 0
    assert state.players[1].round_cards == [
        NumberCard(5),
        drawn_card,
    ]


def test_simulate_opponent_stay_can_finish_round() -> None:
    players = create_players()
    players[0].is_active = False
    players[0].has_stayed = True
    players[1].round_cards.extend(
        [NumberCard(11), NumberCard(12)]
    )
    state = create_state(
        players=players,
        current_player_index=1,
    )

    did_advance = Flip7SearchModel()._simulate_opponent_turn(
        state=state,
        random_generator=FirstPositionRandom(),
    )

    assert not did_advance
    assert state.round_finished
    assert state.current_player_index == 0
    assert state.players[1].has_stayed


def test_simulate_opponent_resolves_drawn_action() -> None:
    freeze_card = ActionCard(ActionType.FREEZE)
    players = [
        SearchPlayerState(0, "Alice", total_score=80),
        SearchPlayerState(
            1,
            "Bob",
            total_score=30,
            round_cards=[NumberCard(5)],
        ),
        SearchPlayerState(2, "Charlie", total_score=20),
    ]
    state = create_state(
        players=players,
        current_player_index=1,
        next_starting_player_index=2,
        remaining_card_counts={freeze_card: 1},
    )

    did_advance = Flip7SearchModel()._simulate_opponent_turn(
        state=state,
        random_generator=FirstPositionRandom(),
    )

    assert did_advance
    assert state.pending_action is None
    assert state.current_player_index == 2
    assert not state.players[0].is_active
    assert freeze_card in state.players[0].round_cards


def test_simulate_opponents_stops_at_root() -> None:
    players = [
        SearchPlayerState(0, "Alice"),
        SearchPlayerState(
            1,
            "Bob",
            round_cards=[NumberCard(11), NumberCard(12)],
        ),
        SearchPlayerState(
            2,
            "Charlie",
            round_cards=[NumberCard(11), NumberCard(12)],
        ),
    ]
    state = create_state(
        players=players,
        current_player_index=1,
        next_starting_player_index=2,
    )

    Flip7SearchModel()._simulate_opponents_until_root(
        state=state,
        random_generator=FirstPositionRandom(),
    )

    assert state.current_player_index == 0
    assert not state.round_finished
    assert state.players[1].has_stayed
    assert state.players[2].has_stayed


def test_simulate_opponents_stops_when_round_finishes() -> None:
    players = create_players()
    players[0].is_active = False
    players[0].has_stayed = True
    players[1].round_cards.extend(
        [NumberCard(11), NumberCard(12)]
    )
    state = create_state(
        players=players,
        current_player_index=1,
    )

    Flip7SearchModel()._simulate_opponents_until_root(
        state=state,
        random_generator=FirstPositionRandom(),
    )

    assert state.round_finished
    assert state.current_player_index == 0


def test_simulate_opponent_turn_rejects_root() -> None:
    with pytest.raises(
        ValueError,
        match="requires an opponent player",
    ):
        Flip7SearchModel()._simulate_opponent_turn(
            state=create_state(),
            random_generator=FirstPositionRandom(),
        )


def test_simulate_opponent_turn_requires_turn_phase() -> None:
    pending_action = SearchPendingAction(
        source_player_index=1,
        action_type=ActionType.FREEZE,
    )
    state = create_state(
        current_player_index=1,
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
    )

    with pytest.raises(
        RuntimeError,
        match="must begin in the turn phase",
    ):
        Flip7SearchModel()._simulate_opponent_turn(
            state=state,
            random_generator=FirstPositionRandom(),
        )


def test_automatic_opponents_play_after_root_hit() -> None:
    drawn_card = NumberCard(4)
    players = create_players()
    players[0].round_cards.append(NumberCard(3))
    players[1].round_cards.extend(
        [NumberCard(11), NumberCard(12)]
    )
    state = create_state(
        players=players,
        remaining_card_counts={drawn_card: 1},
    )
    model = Flip7SearchModel(
        automatic_opponent_turns=True
    )

    next_state = model.sample_transition(
        state=state,
        action=Flip7SearchAction(SearchActionType.HIT),
        random_generator=FirstPositionRandom(),
    )

    assert next_state.current_player_index == 0
    assert next_state.players[0].round_cards == [
        NumberCard(3),
        drawn_card,
    ]
    assert next_state.players[1].has_stayed
    assert not next_state.round_finished


def test_automatic_opponents_can_finish_round_after_root_stays() -> None:
    players = create_players()
    players[0].round_cards.append(NumberCard(5))
    players[1].round_cards.extend(
        [NumberCard(11), NumberCard(12)]
    )
    state = create_state(players=players)
    model = Flip7SearchModel(
        automatic_opponent_turns=True
    )

    next_state = model.sample_transition(
        state=state,
        action=Flip7SearchAction(SearchActionType.STAY),
        random_generator=FirstPositionRandom(),
    )

    assert next_state.round_finished
    assert model.is_terminal(next_state)
    assert next_state.players[0].has_stayed
    assert next_state.players[1].has_stayed


def test_automatic_opponents_wait_for_root_action_target() -> None:
    freeze_card = ActionCard(ActionType.FREEZE)
    players = create_players()
    players[1].round_cards.extend(
        [NumberCard(11), NumberCard(12)]
    )
    state = create_state(
        players=players,
        remaining_card_counts={freeze_card: 1},
    )
    model = Flip7SearchModel(
        automatic_opponent_turns=True
    )

    next_state = model.sample_transition(
        state=state,
        action=Flip7SearchAction(SearchActionType.HIT),
        random_generator=FirstPositionRandom(),
    )

    assert next_state.pending_action == SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FREEZE,
    )
    assert (
        next_state.decision_phase
        is SearchDecisionPhase.ACTION_TARGET
    )
    assert not next_state.players[1].has_stayed


def test_multiple_round_mode_starts_next_round() -> None:
    players = create_players()
    players[0].round_cards.extend(
        [NumberCard(11), NumberCard(12)]
    )
    players[1].round_cards.extend(
        [NumberCard(11), NumberCard(12)]
    )
    state = create_state(
        players=players,
        remaining_card_counts={
            NumberCard(1): 1,
            NumberCard(2): 1,
        },
    )
    model = Flip7SearchModel(
        simulate_multiple_rounds=True
    )

    next_state = model.sample_transition(
        state=state,
        action=Flip7SearchAction(SearchActionType.STAY),
        random_generator=FirstPositionRandom(),
    )

    assert not next_state.round_finished
    assert not next_state.game_finished
    assert next_state.current_player_index == 0
    assert next_state.next_starting_player_index == 0
    assert next_state.players[0].total_score == 23
    assert next_state.players[1].total_score == 23
    assert next_state.players[0].round_cards == [
        NumberCard(2)
    ]
    assert next_state.players[1].round_cards == [
        NumberCard(1),
        NumberCard(11),
    ]


def test_multiple_round_mode_stops_when_game_is_won() -> None:
    players = create_players()
    players[0].total_score = 80
    players[0].round_cards.extend(
        [NumberCard(11), NumberCard(12)]
    )
    players[1].round_cards.extend(
        [NumberCard(11), NumberCard(12)]
    )
    next_card = NumberCard(1)
    state = create_state(
        players=players,
        remaining_card_counts={next_card: 2},
        winning_score=100,
    )
    model = Flip7SearchModel(
        simulate_multiple_rounds=True
    )

    next_state = model.sample_transition(
        state=state,
        action=Flip7SearchAction(SearchActionType.STAY),
        random_generator=FirstPositionRandom(),
    )

    assert next_state.game_finished
    assert next_state.round_finished
    assert model.is_terminal(next_state)
    assert next_state.players[0].total_score == 103
    assert next_state.players[0].round_cards == []
    assert next_state.remaining_card_counts[next_card] == 2


def test_next_active_player_follows_player_order() -> None:
    players = [
        SearchPlayerState(0, "Alice"),
        SearchPlayerState(1, "Bob"),
        SearchPlayerState(2, "Charlie"),
    ]
    state = create_state(
        players=players,
        next_starting_player_index=2,
    )

    next_index = (
        Flip7SearchModel()
        ._get_next_active_player_index(state, 0)
    )

    assert next_index == 1


def test_next_active_player_skips_inactive_players() -> None:
    players = [
        SearchPlayerState(0, "Alice"),
        SearchPlayerState(1, "Bob", is_active=False),
        SearchPlayerState(2, "Charlie"),
    ]
    state = create_state(
        players=players,
        next_starting_player_index=2,
    )

    next_index = (
        Flip7SearchModel()
        ._get_next_active_player_index(state, 0)
    )

    assert next_index == 2


def test_next_active_player_wraps_to_start() -> None:
    players = [
        SearchPlayerState(0, "Alice"),
        SearchPlayerState(1, "Bob"),
        SearchPlayerState(2, "Charlie"),
    ]
    state = create_state(
        players=players,
        next_starting_player_index=2,
    )

    next_index = (
        Flip7SearchModel()
        ._get_next_active_player_index(state, 2)
    )

    assert next_index == 0


def test_only_active_player_can_be_returned_again() -> None:
    players = [
        SearchPlayerState(0, "Alice", is_active=False),
        SearchPlayerState(1, "Bob"),
        SearchPlayerState(2, "Charlie", is_active=False),
    ]
    state = create_state(
        players=players,
        current_player_index=1,
        next_starting_player_index=2,
    )

    next_index = (
        Flip7SearchModel()
        ._get_next_active_player_index(state, 1)
    )

    assert next_index == 1


def test_next_active_player_is_none_when_all_are_inactive() -> None:
    players = [
        SearchPlayerState(0, "Alice", is_active=False),
        SearchPlayerState(1, "Bob", is_active=False),
    ]
    state = create_state(players=players)

    next_index = (
        Flip7SearchModel()
        ._get_next_active_player_index(state, 0)
    )

    assert next_index is None


def test_next_active_player_rejects_unknown_start_index() -> None:
    with pytest.raises(
        RuntimeError,
        match="requested player does not exist",
    ):
        Flip7SearchModel()._get_next_active_player_index(
            create_state(),
            9,
        )


def test_advance_to_next_turn_moves_to_next_player() -> None:
    players = [
        SearchPlayerState(0, "Alice"),
        SearchPlayerState(1, "Bob"),
        SearchPlayerState(2, "Charlie"),
    ]
    state = create_state(
        players=players,
        next_starting_player_index=2,
    )

    did_advance = Flip7SearchModel()._advance_to_next_turn(
        state=state,
        after_player_index=0,
    )

    assert did_advance
    assert state.current_player_index == 1
    assert state.decision_phase is SearchDecisionPhase.TURN


def test_advance_to_next_turn_skips_inactive_player() -> None:
    players = [
        SearchPlayerState(0, "Alice"),
        SearchPlayerState(1, "Bob", is_active=False),
        SearchPlayerState(2, "Charlie"),
    ]
    state = create_state(
        players=players,
        next_starting_player_index=2,
    )

    did_advance = Flip7SearchModel()._advance_to_next_turn(
        state=state,
        after_player_index=0,
    )

    assert did_advance
    assert state.current_player_index == 2


def test_advance_to_next_turn_can_return_to_root() -> None:
    players = [
        SearchPlayerState(0, "Alice"),
        SearchPlayerState(1, "Bob"),
        SearchPlayerState(2, "Charlie"),
    ]
    state = create_state(
        players=players,
        current_player_index=2,
        next_starting_player_index=2,
    )

    did_advance = Flip7SearchModel()._advance_to_next_turn(
        state=state,
        after_player_index=2,
    )

    assert did_advance
    assert state.current_player_index == 0


def test_advance_to_next_turn_finishes_inactive_round() -> None:
    players = [
        SearchPlayerState(0, "Alice", is_active=False),
        SearchPlayerState(1, "Bob", is_active=False),
    ]
    state = create_state(
        players=players,
        current_player_index=1,
    )

    did_advance = Flip7SearchModel()._advance_to_next_turn(
        state=state,
        after_player_index=1,
    )

    assert not did_advance
    assert state.round_finished
    assert state.current_player_index == 0
    assert state.decision_phase is SearchDecisionPhase.TURN


def test_advance_to_next_turn_stops_after_flip_seven() -> None:
    players = create_players()
    players[0].round_cards.extend(
        NumberCard(number)
        for number in range(7)
    )
    state = create_state(players=players)

    did_advance = Flip7SearchModel()._advance_to_next_turn(
        state=state,
        after_player_index=0,
    )

    assert not did_advance
    assert state.round_finished
    assert state.current_player_index == 0


def test_advance_to_next_turn_rejects_pending_action() -> None:
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FREEZE,
    )
    state = create_state(
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
    )

    with pytest.raises(
        RuntimeError,
        match="must be resolved",
    ):
        Flip7SearchModel()._advance_to_next_turn(
            state=state,
            after_player_index=0,
        )


def test_target_actions_include_active_players_in_index_order() -> None:
    players = [
        SearchPlayerState(2, "Charlie"),
        SearchPlayerState(0, "Alice"),
        SearchPlayerState(1, "Bob"),
    ]
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FREEZE,
    )
    state = create_state(
        players=players,
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
    )

    actions = Flip7SearchModel().get_valid_actions(state)

    assert tuple(
        action.target_player_index
        for action in actions
    ) == (0, 1, 2)


def test_second_chance_excludes_ineligible_targets() -> None:
    players = [
        SearchPlayerState(0, "Alice"),
        SearchPlayerState(
            1,
            "Bob",
            has_second_chance=True,
        ),
        SearchPlayerState(
            2,
            "Charlie",
            is_active=False,
            has_stayed=True,
        ),
    ]
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.SECOND_CHANCE,
    )
    state = create_state(
        players=players,
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
    )

    assert Flip7SearchModel().get_valid_actions(state) == (
        Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=0,
        ),
    )


def test_terminal_state_has_no_valid_actions() -> None:
    state = create_state(
        current_player_index=1,
        round_finished=True,
        game_finished=True,
    )

    assert Flip7SearchModel().get_valid_actions(state) == ()
    assert Flip7SearchModel().is_terminal(state)


def test_finished_round_is_terminal_for_current_search() -> None:
    state = create_state(
        current_player_index=1,
        round_finished=True,
    )

    assert Flip7SearchModel().is_terminal(state)
    assert Flip7SearchModel().get_valid_actions(state) == ()


def test_finished_round_is_not_terminal_in_multiple_round_mode() -> None:
    state = create_state(round_finished=True)
    model = Flip7SearchModel(
        simulate_multiple_rounds=True
    )

    assert not model.is_terminal(state)


def test_non_terminal_reward_uses_current_round_scores() -> None:
    players = [
        SearchPlayerState(
            player_index=0,
            player_name="Alice",
            total_score=50,
            round_cards=[
                NumberCard(10),
                ModifierCard(ModifierType.ADDITIVE, 4),
            ],
        ),
        SearchPlayerState(
            player_index=1,
            player_name="Bob",
            total_score=40,
            round_cards=[NumberCard(5)],
        ),
    ]

    reward = Flip7SearchModel().get_reward(
        create_state(players=players)
    )

    expected_reward = 0.19

    assert reward == pytest.approx(expected_reward)


def test_default_rollout_agent_uses_threshold_decision() -> None:
    players = create_players()
    players[0].round_cards.extend(
        [NumberCard(11), NumberCard(12)]
    )
    state = create_state(players=players)
    model = Flip7SearchModel()
    valid_actions = model.get_valid_actions(state)

    action = model.choose_rollout_action(
        state=state,
        valid_actions=valid_actions,
        random_generator=Random(42),
    )

    assert action == Flip7SearchAction(SearchActionType.STAY)


def test_non_terminal_reward_is_limited_to_unit_interval() -> None:
    players = [
        SearchPlayerState(0, "Alice", total_score=500),
        SearchPlayerState(1, "Bob", total_score=0),
    ]

    assert Flip7SearchModel().get_reward(
        create_state(players=players)
    ) == 1.0


@pytest.mark.parametrize(
    ("root_score", "opponent_score", "expected_reward"),
    [
        (200, 150, 1.0),
        (150, 200, -1.0),
        (200, 200, 0.5),
    ],
)
def test_terminal_reward(
    root_score: int,
    opponent_score: int,
    expected_reward: float,
) -> None:
    players = [
        SearchPlayerState(0, "Alice", total_score=root_score),
        SearchPlayerState(1, "Bob", total_score=opponent_score),
    ]
    state = create_state(
        players=players,
        round_finished=True,
        game_finished=True,
    )

    assert Flip7SearchModel().get_reward(state) == expected_reward


def test_finish_search_round_scores_and_discards_cards() -> None:
    additive_card = ModifierCard(
        ModifierType.ADDITIVE,
        3,
    )
    players = [
        SearchPlayerState(
            0,
            "Alice",
            total_score=10,
            round_cards=[NumberCard(5), additive_card],
        ),
        SearchPlayerState(
            1,
            "Bob",
            total_score=20,
            round_cards=[NumberCard(7), NumberCard(7)],
            is_active=False,
            has_busted=True,
        ),
    ]
    state = create_state(
        players=players,
        discarded_card_counts={NumberCard(2): 1},
        current_player_index=1,
        round_finished=True,
    )

    Flip7SearchModel()._finish_search_round(state)

    assert state.players[0].total_score == 18
    assert state.players[1].total_score == 20
    assert state.players[0].round_cards == []
    assert state.players[1].round_cards == []
    assert all(
        not player.is_active
        for player in state.players
    )
    assert state.discarded_card_counts == {
        NumberCard(2): 1,
        NumberCard(5): 1,
        additive_card: 1,
        NumberCard(7): 2,
    }
    assert not state.game_finished
    assert state.current_player_index == 0


def test_finish_search_round_detects_finished_game() -> None:
    players = create_players()
    players[0].total_score = 10
    players[0].round_cards.append(NumberCard(5))
    state = create_state(
        players=players,
        winning_score=15,
        round_finished=True,
    )

    Flip7SearchModel()._finish_search_round(state)

    assert state.players[0].total_score == 15
    assert state.game_finished
    assert state.round_finished


def test_finish_search_round_rejects_unfinished_round() -> None:
    with pytest.raises(
        RuntimeError,
        match="Only a finished search round",
    ):
        Flip7SearchModel()._finish_search_round(
            create_state()
        )


def test_finish_and_start_next_search_round_rotates_and_deals() -> None:
    players = [
        SearchPlayerState(
            0,
            "Alice",
            total_score=10,
            round_cards=[NumberCard(5)],
            is_active=False,
            has_stayed=True,
            has_second_chance=True,
        ),
        SearchPlayerState(
            1,
            "Bob",
            total_score=20,
            round_cards=[NumberCard(3)],
            is_active=False,
            has_stayed=True,
        ),
    ]
    state = create_state(
        players=players,
        remaining_card_counts={
            NumberCard(7): 1,
            NumberCard(8): 1,
        },
        round_finished=True,
    )

    round_has_turn = (
        Flip7SearchModel()
        ._finish_and_start_next_search_round(
            state=state,
            random_generator=FirstPositionRandom(),
        )
    )

    assert round_has_turn
    assert not state.round_finished
    assert not state.game_finished
    assert state.players[0].total_score == 15
    assert state.players[1].total_score == 23
    assert state.players[0].round_cards == [NumberCard(8)]
    assert state.players[1].round_cards == [NumberCard(7)]
    assert all(player.is_active for player in state.players)
    assert all(
        not player.has_stayed
        and not player.has_busted
        and not player.has_second_chance
        for player in state.players
    )
    assert state.current_player_index == 1
    assert state.next_starting_player_index == 0


def test_finished_game_does_not_start_another_search_round() -> None:
    players = create_players()
    players[0].total_score = 10
    players[0].round_cards.append(NumberCard(5))
    next_card = NumberCard(7)
    state = create_state(
        players=players,
        remaining_card_counts={next_card: 1},
        winning_score=15,
        round_finished=True,
    )

    round_has_turn = (
        Flip7SearchModel()
        ._finish_and_start_next_search_round(
            state=state,
            random_generator=FirstPositionRandom(),
        )
    )

    assert not round_has_turn
    assert state.game_finished
    assert state.round_finished
    assert state.remaining_card_counts[next_card] == 1
    assert state.players[0].round_cards == []


def test_new_search_round_resolves_initial_action_card() -> None:
    freeze_card = ActionCard(ActionType.FREEZE)
    players = [
        SearchPlayerState(0, "Alice", total_score=80),
        SearchPlayerState(1, "Bob", total_score=30),
    ]
    state = create_state(
        players=players,
        remaining_card_counts={
            freeze_card: 1,
            NumberCard(9): 1,
        },
        round_finished=True,
    )

    round_has_turn = (
        Flip7SearchModel()
        ._finish_and_start_next_search_round(
            state=state,
            random_generator=FirstPositionRandom(),
        )
    )

    assert round_has_turn
    assert state.pending_action is None
    assert state.current_player_index == 1
    assert not state.players[0].is_active
    assert freeze_card in state.players[0].round_cards
    assert state.remaining_card_counts[NumberCard(9)] == 1


def test_start_next_search_round_rejects_unfinished_round() -> None:
    with pytest.raises(
        RuntimeError,
        match="Only a finished search round",
    ):
        (
            Flip7SearchModel()
            ._finish_and_start_next_search_round(
                state=create_state(),
                random_generator=FirstPositionRandom(),
            )
        )


def test_stay_transition_returns_independent_state() -> None:
    players = create_players()
    players[0].round_cards.append(NumberCard(5))
    original_state = create_state(players=players)

    next_state = Flip7SearchModel().sample_transition(
        state=original_state,
        action=Flip7SearchAction(SearchActionType.STAY),
        random_generator=Random(42),
    )

    assert next_state is not original_state
    assert next_state.players[0] is not original_state.players[0]
    assert next_state.players[0].has_stayed
    assert not next_state.players[0].is_active
    assert original_state.players[0].is_active
    assert not original_state.players[0].has_stayed


def test_stay_does_not_finish_round_while_opponent_is_active() -> None:
    players = create_players()
    players[0].round_cards.append(NumberCard(5))

    next_state = Flip7SearchModel().sample_transition(
        state=create_state(players=players),
        action=Flip7SearchAction(SearchActionType.STAY),
        random_generator=Random(42),
    )

    assert not next_state.round_finished


def test_stay_finishes_round_when_no_player_remains_active() -> None:
    players = create_players()
    players[0].round_cards.append(NumberCard(5))
    players[1].is_active = False
    players[1].has_stayed = True

    next_state = Flip7SearchModel().sample_transition(
        state=create_state(players=players),
        action=Flip7SearchAction(SearchActionType.STAY),
        random_generator=Random(42),
    )

    assert next_state.round_finished


def test_stay_is_rejected_when_player_has_no_cards() -> None:
    with pytest.raises(
        ValueError,
        match="not valid",
    ):
        Flip7SearchModel().sample_transition(
            state=create_state(),
            action=Flip7SearchAction(SearchActionType.STAY),
            random_generator=Random(42),
        )


def test_draw_random_card_reduces_its_count() -> None:
    card = NumberCard(7)
    state = create_state(
        remaining_card_counts={card: 1},
    )

    drawn_card = Flip7SearchModel()._draw_random_card(
        state=state,
        random_generator=Random(42),
    )

    assert drawn_card == card
    assert state.remaining_card_counts[card] == 0


def test_draw_random_card_ignores_zero_counts() -> None:
    unavailable_card = NumberCard(3)
    available_card = NumberCard(8)
    state = create_state(
        remaining_card_counts={
            unavailable_card: 0,
            available_card: 1,
        },
    )

    drawn_card = Flip7SearchModel()._draw_random_card(
        state=state,
        random_generator=Random(42),
    )

    assert drawn_card == available_card


def test_draw_random_card_respects_card_frequencies() -> None:
    first_card = NumberCard(1)
    second_card = NumberCard(2)
    state = create_state(
        remaining_card_counts={
            first_card: 2,
            second_card: 1,
        },
    )

    class LastPositionRandom(Random):
        def randrange(self, stop: int) -> int:
            return stop - 1

    drawn_card = Flip7SearchModel()._draw_random_card(
        state=state,
        random_generator=LastPositionRandom(),
    )

    assert drawn_card == second_card
    assert state.remaining_card_counts == {
        first_card: 2,
        second_card: 0,
    }


def test_draw_recycles_discarded_cards_when_deck_is_empty() -> None:
    discarded_card = NumberCard(9)
    state = create_state(
        remaining_card_counts={NumberCard(1): 0},
        discarded_card_counts={discarded_card: 1},
    )

    drawn_card = Flip7SearchModel()._draw_random_card(
        state=state,
        random_generator=Random(42),
    )

    assert drawn_card == discarded_card
    assert state.remaining_card_counts[discarded_card] == 0
    assert state.discarded_card_counts[discarded_card] == 0


def test_draw_from_completely_empty_search_deck_is_rejected() -> None:
    state = create_state(
        remaining_card_counts={},
        discarded_card_counts={},
    )

    with pytest.raises(
        RuntimeError,
        match="empty search deck",
    ):
        Flip7SearchModel()._draw_random_card(
            state=state,
            random_generator=Random(42),
        )


def test_same_seed_produces_same_draw_sequence() -> None:
    first_state = create_state(
        remaining_card_counts={
            NumberCard(1): 2,
            NumberCard(2): 2,
            NumberCard(3): 2,
        },
    )
    second_state = create_state(
        remaining_card_counts=dict(
            first_state.remaining_card_counts
        ),
    )
    model = Flip7SearchModel()
    first_random = Random(123)
    second_random = Random(123)

    first_sequence = [
        model._draw_random_card(first_state, first_random)
        for _ in range(6)
    ]
    second_sequence = [
        model._draw_random_card(second_state, second_random)
        for _ in range(6)
    ]

    assert first_sequence == second_sequence


def test_hit_adds_number_card_to_copied_state() -> None:
    card = NumberCard(7)
    original_state = create_state(
        remaining_card_counts={card: 1},
    )

    next_state = Flip7SearchModel().sample_transition(
        state=original_state,
        action=Flip7SearchAction(SearchActionType.HIT),
        random_generator=Random(42),
    )

    assert next_state.players[0].round_cards == [card]
    assert next_state.remaining_card_counts[card] == 0
    assert original_state.players[0].round_cards == []
    assert original_state.remaining_card_counts[card] == 1


def test_hit_adds_modifier_card() -> None:
    card = ModifierCard(ModifierType.ADDITIVE, 4)
    state = create_state(
        remaining_card_counts={card: 1},
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(SearchActionType.HIT),
        random_generator=Random(42),
    )

    assert next_state.players[0].round_cards == [card]
    assert next_state.players[0].is_active


def test_duplicate_number_causes_bust() -> None:
    duplicate_card = NumberCard(7)
    players = create_players()
    players[0].round_cards.append(duplicate_card)
    state = create_state(
        players=players,
        remaining_card_counts={duplicate_card: 1},
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(SearchActionType.HIT),
        random_generator=Random(42),
    )

    assert next_state.players[0].round_cards == [
        duplicate_card,
        duplicate_card,
    ]
    assert next_state.players[0].has_busted
    assert not next_state.players[0].is_active


def test_second_chance_prevents_duplicate_number_bust() -> None:
    duplicate_card = NumberCard(7)
    second_chance_card = ActionCard(
        ActionType.SECOND_CHANCE
    )
    players = create_players()
    players[0].round_cards = [
        duplicate_card,
        second_chance_card,
    ]
    players[0].has_second_chance = True
    state = create_state(
        players=players,
        remaining_card_counts={duplicate_card: 1},
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(SearchActionType.HIT),
        random_generator=Random(42),
    )

    assert next_state.players[0].round_cards == [duplicate_card]
    assert not next_state.players[0].has_second_chance
    assert not next_state.players[0].has_busted
    assert next_state.players[0].is_active
    assert next_state.discarded_card_counts == {
        duplicate_card: 1,
        second_chance_card: 1,
    }


def test_seventh_unique_number_finishes_round() -> None:
    players = create_players()
    players[0].round_cards = [
        NumberCard(number)
        for number in range(6)
    ]
    seventh_card = NumberCard(6)
    state = create_state(
        players=players,
        remaining_card_counts={seventh_card: 1},
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(SearchActionType.HIT),
        random_generator=Random(42),
    )

    assert seventh_card in next_state.players[0].round_cards
    assert next_state.round_finished


def test_hit_with_action_card_requests_target() -> None:
    action_card = ActionCard(ActionType.FREEZE)
    state = create_state(
        remaining_card_counts={action_card: 1},
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(SearchActionType.HIT),
        random_generator=Random(42),
    )

    assert (
        next_state.decision_phase
        is SearchDecisionPhase.ACTION_TARGET
    )
    assert next_state.pending_action == SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FREEZE,
    )
    assert action_card not in next_state.players[0].round_cards


def test_hit_discards_action_without_valid_target() -> None:
    second_chance = ActionCard(ActionType.SECOND_CHANCE)
    players = create_players()
    players[0].has_second_chance = True
    players[1].has_second_chance = True
    original_state = create_state(
        players=players,
        remaining_card_counts={second_chance: 1},
    )

    next_state = Flip7SearchModel().sample_transition(
        state=original_state,
        action=Flip7SearchAction(SearchActionType.HIT),
        random_generator=FirstPositionRandom(),
    )

    assert next_state.pending_action is None
    assert next_state.decision_phase is SearchDecisionPhase.TURN
    assert next_state.discarded_card_counts[second_chance] == 1
    assert next_state.remaining_card_counts[second_chance] == 0
    assert original_state.discarded_card_counts == {}
    assert original_state.remaining_card_counts[second_chance] == 1


def test_opponent_hit_discards_action_without_valid_target() -> None:
    second_chance = ActionCard(ActionType.SECOND_CHANCE)
    players = create_players()
    players[0].has_second_chance = True
    players[1].has_second_chance = True
    players[1].round_cards.append(NumberCard(5))
    state = create_state(
        players=players,
        current_player_index=1,
        remaining_card_counts={second_chance: 1},
    )

    action = Flip7SearchModel()._apply_opponent_action(
        state=state,
        random_generator=FirstPositionRandom(),
    )

    assert action == Flip7SearchAction(
        SearchActionType.HIT
    )
    assert state.pending_action is None
    assert state.decision_phase is SearchDecisionPhase.TURN
    assert state.discarded_card_counts[second_chance] == 1


def test_freeze_deactivates_target_in_copied_state() -> None:
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FREEZE,
    )
    state = create_state(
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=1,
        ),
        random_generator=Random(42),
    )

    freeze_card = ActionCard(ActionType.FREEZE)

    assert not next_state.players[1].is_active
    assert freeze_card in next_state.players[1].round_cards
    assert next_state.pending_action is None
    assert next_state.decision_phase is SearchDecisionPhase.TURN
    assert state.players[1].is_active
    assert freeze_card not in state.players[1].round_cards


def test_second_chance_is_assigned_to_target() -> None:
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.SECOND_CHANCE,
    )
    state = create_state(
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=1,
        ),
        random_generator=Random(42),
    )

    assert next_state.players[1].has_second_chance
    assert (
        ActionCard(ActionType.SECOND_CHANCE)
        in next_state.players[1].round_cards
    )
    assert next_state.pending_action is None


def test_action_target_rejects_inactive_player() -> None:
    players = create_players()
    players[1].is_active = False
    players[1].has_stayed = True
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FREEZE,
    )
    state = create_state(
        players=players,
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
    )

    with pytest.raises(ValueError, match="not valid"):
        Flip7SearchModel().sample_transition(
            state=state,
            action=Flip7SearchAction(
                SearchActionType.ACTION_TARGET,
                target_player_index=1,
            ),
            random_generator=Random(42),
        )


def test_second_chance_rejects_player_who_already_has_one() -> None:
    players = create_players()
    players[1].has_second_chance = True
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.SECOND_CHANCE,
    )
    state = create_state(
        players=players,
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
    )

    with pytest.raises(ValueError, match="not valid"):
        Flip7SearchModel().sample_transition(
            state=state,
            action=Flip7SearchAction(
                SearchActionType.ACTION_TARGET,
                target_player_index=1,
            ),
            random_generator=Random(42),
        )


def test_completing_action_promotes_queued_action() -> None:
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.SECOND_CHANCE,
    )
    queued_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FREEZE,
    )
    state = create_state(
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
        queued_actions=[queued_action],
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=0,
        ),
        random_generator=Random(42),
    )

    assert next_state.pending_action == queued_action
    assert next_state.queued_actions == []
    assert (
        next_state.decision_phase
        is SearchDecisionPhase.ACTION_TARGET
    )


def test_round_end_discards_queued_actions() -> None:
    players = create_players()
    players[0].is_active = False
    players[0].has_stayed = True
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FREEZE,
    )
    queued_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FLIP_THREE,
    )
    state = create_state(
        players=players,
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
        queued_actions=[queued_action],
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=1,
        ),
        random_generator=Random(42),
    )

    assert next_state.round_finished
    assert next_state.queued_actions == []
    assert next_state.discarded_card_counts[
        ActionCard(ActionType.FLIP_THREE)
    ] == 1


def test_flip_three_draws_three_cards_for_target() -> None:
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FLIP_THREE,
    )
    number_two = NumberCard(2)
    modifier = ModifierCard(ModifierType.ADDITIVE, 3)
    number_four = NumberCard(4)
    state = create_state(
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
        remaining_card_counts={
            number_two: 1,
            modifier: 1,
            number_four: 1,
        },
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=1,
        ),
        random_generator=FirstPositionRandom(),
    )

    assert next_state.players[1].round_cards == [
        ActionCard(ActionType.FLIP_THREE),
        number_two,
        modifier,
        number_four,
    ]
    assert all(
        count == 0
        for count in next_state.remaining_card_counts.values()
    )
    assert next_state.pending_action is None
    assert next_state.queued_actions == []
    assert next_state.decision_phase is SearchDecisionPhase.TURN

    assert state.players[1].round_cards == []
    assert all(
        count == 1
        for count in state.remaining_card_counts.values()
    )


def test_flip_three_stops_after_target_busts() -> None:
    players = create_players()
    players[1].round_cards.append(NumberCard(7))
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FLIP_THREE,
    )
    state = create_state(
        players=players,
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
        remaining_card_counts={
            NumberCard(7): 1,
            NumberCard(9): 1,
        },
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=1,
        ),
        random_generator=FirstPositionRandom(),
    )

    target_player = next_state.players[1]
    assert target_player.has_busted
    assert not target_player.is_active
    assert next_state.remaining_card_counts[NumberCard(9)] == 1


def test_flip_three_stops_after_flip_seven() -> None:
    players = create_players()
    players[1].round_cards.extend(
        NumberCard(number)
        for number in range(6)
    )
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FLIP_THREE,
    )
    state = create_state(
        players=players,
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
        remaining_card_counts={
            NumberCard(6): 1,
            NumberCard(9): 1,
        },
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=1,
        ),
        random_generator=FirstPositionRandom(),
    )

    assert next_state.round_finished
    assert NumberCard(6) in next_state.players[1].round_cards
    assert next_state.remaining_card_counts[NumberCard(9)] == 1


def test_flip_three_applies_drawn_second_chance_immediately() -> None:
    second_chance = ActionCard(ActionType.SECOND_CHANCE)
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FLIP_THREE,
    )
    state = create_state(
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
        remaining_card_counts={
            second_chance: 1,
            NumberCard(1): 1,
            NumberCard(2): 1,
        },
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=1,
        ),
        random_generator=FirstPositionRandom(),
    )

    target_player = next_state.players[1]
    assert target_player.has_second_chance
    assert second_chance in target_player.round_cards
    assert next_state.pending_action is None
    assert next_state.queued_actions == []


def test_flip_three_promotes_drawn_action_for_target_choice() -> None:
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FLIP_THREE,
    )
    state = create_state(
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
        remaining_card_counts={
            ActionCard(ActionType.FREEZE): 1,
            NumberCard(1): 1,
            NumberCard(2): 1,
        },
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=1,
        ),
        random_generator=FirstPositionRandom(),
    )

    assert next_state.pending_action == SearchPendingAction(
        source_player_index=1,
        action_type=ActionType.FREEZE,
    )
    assert next_state.current_player_index == 1
    assert (
        next_state.decision_phase
        is SearchDecisionPhase.ACTION_TARGET
    )


def test_flip_three_keeps_drawn_actions_in_draw_order() -> None:
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FLIP_THREE,
    )
    state = create_state(
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
        remaining_card_counts={
            ActionCard(ActionType.FREEZE): 1,
            ActionCard(ActionType.FLIP_THREE): 1,
            NumberCard(2): 1,
        },
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=1,
        ),
        random_generator=FirstPositionRandom(),
    )

    assert next_state.pending_action == SearchPendingAction(
        source_player_index=1,
        action_type=ActionType.FREEZE,
    )
    assert next_state.queued_actions == [
        SearchPendingAction(
            source_player_index=1,
            action_type=ActionType.FLIP_THREE,
        )
    ]


def test_flip_three_discards_queued_action_without_valid_target() -> None:
    players = create_players()
    players[0].has_second_chance = True
    players[1].has_second_chance = True
    second_chance = ActionCard(ActionType.SECOND_CHANCE)
    pending_action = SearchPendingAction(
        source_player_index=0,
        action_type=ActionType.FLIP_THREE,
    )
    state = create_state(
        players=players,
        decision_phase=SearchDecisionPhase.ACTION_TARGET,
        pending_action=pending_action,
        remaining_card_counts={
            second_chance: 1,
            NumberCard(1): 1,
            NumberCard(2): 1,
        },
    )

    next_state = Flip7SearchModel().sample_transition(
        state=state,
        action=Flip7SearchAction(
            SearchActionType.ACTION_TARGET,
            target_player_index=1,
        ),
        random_generator=FirstPositionRandom(),
    )

    assert next_state.pending_action is None
    assert next_state.queued_actions == []
    assert next_state.discarded_card_counts[second_chance] == 1
    assert next_state.current_player_index == 0
    assert next_state.decision_phase is SearchDecisionPhase.TURN


def test_flip7_search_model_is_publicly_exported() -> None:
    from flip7.mcts import Flip7SearchModel as ExportedModel

    assert ExportedModel is Flip7SearchModel
