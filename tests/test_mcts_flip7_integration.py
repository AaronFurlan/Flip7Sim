from flip7.game.cards import NumberCard
from flip7.mcts.action import Flip7SearchAction
from flip7.mcts.flip7_model import Flip7SearchModel
from flip7.mcts.search import MCTSSearch
from flip7.mcts.state import (
    Flip7SearchState,
    SearchPlayerState,
)


def test_mcts_search_runs_with_flip7_model() -> None:
    players = [
        SearchPlayerState(
            player_index=0,
            player_name="Alice",
            round_cards=[NumberCard(5)],
        ),
        SearchPlayerState(
            player_index=1,
            player_name="Bob",
            round_cards=[NumberCard(11), NumberCard(12)],
        ),
    ]
    remaining_card_counts = {
        NumberCard(number): 2
        for number in range(13)
    }
    state = Flip7SearchState(
        players=players,
        remaining_card_counts=remaining_card_counts,
        discarded_card_counts={},
        current_player_index=0,
        root_player_index=0,
        next_starting_player_index=1,
        winning_score=100,
    )
    model = Flip7SearchModel(
        automatic_opponent_turns=True
    )
    search: MCTSSearch[
        Flip7SearchState,
        Flip7SearchAction,
    ] = MCTSSearch(
        model=model,
        simulations=30,
        max_depth=8,
        seed=42,
    )

    selected_action = search.find_best_action(state)

    assert selected_action in model.get_valid_actions(state)
    assert state.players[0].round_cards == [NumberCard(5)]
    assert not state.players[1].has_stayed
    assert all(
        count == 2
        for count in state.remaining_card_counts.values()
    )
