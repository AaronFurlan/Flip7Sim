import pytest

from flip7.game.cards import (
    ActionCard,
    ActionType,
    ModifierCard,
    ModifierType,
    NumberCard,
)
from flip7.game.deck import Deck
from flip7.game.player import Player
from flip7.game.round import (
    GameRound,
    PendingAction,
    RoundStateError,
    DrawReason,
)

def create_started_round() -> tuple[
    GameRound,
    Player,
    Player,
]:
    alice = Player("Alice")
    bob = Player("Bob")

    deck = Deck(
        cards=[
            NumberCard(1),
            NumberCard(2),
        ]
    )
    game_round = GameRound(
        players=[alice, bob],
        deck=deck,
    )
    game_round.start_round()

    return game_round, alice, bob


@pytest.mark.parametrize("player_count", [0, 1])
def test_round_requires_at_least_two_players(
    player_count: int,
) -> None:
    players = [
        Player(f"Player {index}")
        for index in range(player_count)
    ]

    with pytest.raises(ValueError):
        GameRound(
            players=players,
            deck=Deck(),
        )


def test_round_copies_the_player_list() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    players = [alice, bob]

    game_round = GameRound(
        players=players,
        deck=Deck(),
    )

    players.clear()

    assert game_round.players == [alice, bob]


def test_start_round_resets_player_state() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    alice.total_score = 50
    alice.has_busted = True
    bob.has_stayed = True

    deck = Deck(
        cards=[
            NumberCard(2),
            NumberCard(1),
        ]
    )
    game_round = GameRound(
        players=[alice, bob],
        deck=deck,
    )

    game_round.start_round()

    assert game_round.has_started
    assert not game_round.has_finished

    assert alice.total_score == 50
    assert not alice.has_busted
    assert not bob.has_stayed


def test_started_round_cannot_be_started_again() -> None:
    game_round = GameRound(
        players=[
            Player("Alice"),
            Player("Bob"),
        ],
        deck=Deck(),
    )

    game_round.start_round()

    with pytest.raises(RoundStateError):
        game_round.start_round()

def test_process_new_number_adds_card() -> None:
    game_round, alice, _ = create_started_round()
    card = NumberCard(7)

    game_round.process_number_card(alice, card)

    assert card in alice.round_cards
    assert alice.is_active
    assert not alice.has_busted


def test_duplicate_number_causes_bust() -> None:
    game_round, alice, _ = create_started_round()
    alice.add_card(NumberCard(7))

    game_round.process_number_card(
        alice,
        NumberCard(7),
    )

    assert alice.get_number_cards().count(
        NumberCard(7)
    ) == 2
    assert alice.has_busted
    assert not alice.is_active


def test_second_chance_prevents_bust() -> None:
    game_round, alice, _ = create_started_round()

    second_chance_card = ActionCard(
        ActionType.SECOND_CHANCE
    )
    alice.add_card(NumberCard(7))
    alice.add_card(second_chance_card)
    alice.has_second_chance = True

    game_round.process_number_card(
        alice,
        NumberCard(7),
    )

    assert alice.get_number_cards().count(
        NumberCard(7)
    ) == 1
    assert second_chance_card not in alice.round_cards
    assert not alice.has_second_chance
    assert not alice.has_busted
    assert alice.is_active
    assert game_round.deck.discarded_card_count() == 2


def test_card_cannot_be_processed_before_round_starts() -> None:
    alice = Player("Alice")
    game_round = GameRound(
        players=[alice, Player("Bob")],
        deck=Deck(cards=[]),
    )

    with pytest.raises(RoundStateError):
        game_round.process_number_card(
            alice,
            NumberCard(7),
        )


def test_inactive_player_cannot_receive_number_card() -> None:
    game_round, alice, _ = create_started_round()
    alice.is_active = False

    with pytest.raises(RoundStateError):
        game_round.process_number_card(
            alice,
            NumberCard(7),
        )


def test_player_from_another_round_is_rejected() -> None:
    game_round, _, _ = create_started_round()
    outsider = Player("Charlie")

    with pytest.raises(ValueError):
        game_round.process_number_card(
            outsider,
            NumberCard(7),
        )

def test_process_modifier_card_adds_card() -> None:
    game_round, alice, _ = create_started_round()

    modifier_card = ModifierCard(
        modifier_type=ModifierType.ADDITIVE,
        value=6,
    )

    game_round.process_modifier_card(
        alice,
        modifier_card,
    )

    assert modifier_card in alice.round_cards
    assert alice.is_active
    assert not alice.has_busted

def test_draw_number_card_processes_number() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    number_card = NumberCard(7)

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                number_card,
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    drawn_card = game_round.draw_card_for_player(alice)

    assert drawn_card == number_card
    assert number_card in alice.round_cards
    assert game_round.deck.remaining_card_count() == 0


def test_draw_modifier_card_processes_modifier() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    modifier_card = ModifierCard(
        modifier_type=ModifierType.ADDITIVE,
        value=6,
    )

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(cards=[
            modifier_card,
            NumberCard(2),
            NumberCard(1),
        ]),
    )
    game_round.start_round()

    drawn_card = game_round.draw_card_for_player(alice)

    assert drawn_card == modifier_card
    assert modifier_card in alice.round_cards


def test_draw_action_card_creates_pending_action() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    action_card = ActionCard(ActionType.FREEZE)

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(cards=[
            action_card,
            NumberCard(2),
            NumberCard(1),
        ]),
    )
    game_round.start_round()

    drawn_card = game_round.draw_card_for_player(alice)

    assert drawn_card == action_card
    assert game_round.pending_action == PendingAction(
        source_player=alice,
        card=action_card,
    )
    assert action_card not in alice.round_cards


def test_pending_action_blocks_next_draw() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(7),
                ActionCard(ActionType.FREEZE),
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    game_round.draw_card_for_player(alice)

    with pytest.raises(RoundStateError):
        game_round.draw_card_for_player(alice)

    assert game_round.deck.remaining_card_count() == 1

def test_start_round_deals_one_card_to_each_player() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )

    game_round.start_round()

    assert alice.round_cards == [NumberCard(1)]
    assert bob.round_cards == [NumberCard(2)]
    assert game_round.is_initial_deal_complete
    assert game_round.deck.is_empty()


def test_action_card_pauses_initial_deal() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    action_card = ActionCard(ActionType.FREEZE)

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(2),
                action_card,
            ]
        ),
    )

    game_round.start_round()

    assert game_round.pending_action == PendingAction(
        source_player=alice,
        card=action_card,
    )
    assert not game_round.is_initial_deal_complete
    assert alice.round_cards == []
    assert bob.round_cards == []
    assert game_round.deck.remaining_card_count() == 1

    with pytest.raises(RoundStateError):
        game_round.continue_starting_deal()

def test_resolve_freeze_stops_selected_target() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    action_card = ActionCard(ActionType.FREEZE)

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                action_card,
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    game_round.draw_card_for_player(alice)
    game_round.resolve_pending_action(bob)

    assert game_round.pending_action is None
    assert action_card in bob.round_cards
    assert not bob.is_active
    assert not bob.has_stayed
    assert not bob.has_busted


def test_freeze_continues_paused_initial_deal() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    action_card = ActionCard(ActionType.FREEZE)

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(2),
                action_card,
            ]
        ),
    )

    game_round.start_round()

    assert game_round.pending_action is not None
    assert not game_round.is_initial_deal_complete

    game_round.resolve_pending_action(bob)

    assert game_round.pending_action is None
    assert game_round.is_initial_deal_complete

    assert action_card in bob.round_cards
    assert not bob.is_active
    assert bob.get_number_cards() == []

    assert game_round.deck.remaining_card_count() == 1


def test_resolve_action_requires_pending_action() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    with pytest.raises(RoundStateError):
        game_round.resolve_pending_action(alice)

def test_player_can_stay_after_initial_deal() -> None:
    game_round, alice, _ = create_started_round()

    game_round.player_stays(alice)

    assert alice.has_stayed
    assert not alice.is_active
    assert not alice.has_busted


def test_player_without_cards_cannot_stay() -> None:
    game_round, alice, _ = create_started_round()
    alice.round_cards.clear()

    with pytest.raises(RoundStateError):
        game_round.player_stays(alice)


def test_player_cannot_stay_with_pending_action() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                ActionCard(ActionType.FREEZE),
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()
    game_round.draw_card_for_player(alice)

    with pytest.raises(RoundStateError):
        game_round.player_stays(alice)


def test_round_finishes_when_no_active_players_remain() -> None:
    game_round, alice, bob = create_started_round()

    game_round.player_stays(alice)

    assert not game_round.is_round_finished()

    game_round.player_stays(bob)

    assert game_round.is_round_finished()


def test_round_finishes_when_player_flips_seven() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(12),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    for number in range(2, 8):
        game_round.process_number_card(
            alice,
            NumberCard(number),
        )

    assert game_round.check_for_flip_seven(alice)
    assert game_round.is_round_finished()
    assert alice.is_active

def test_finish_round_transfers_scores_and_discards_cards() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    alice.total_score = 20

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(10),
                NumberCard(5),
            ]
        ),
    )
    game_round.start_round()

    game_round.player_stays(alice)
    game_round.player_stays(bob)

    round_scores = game_round.finish_round()

    assert round_scores == {
        alice: 5,
        bob: 10,
    }
    assert alice.total_score == 25
    assert bob.total_score == 10

    assert alice.round_cards == []
    assert bob.round_cards == []
    assert game_round.deck.discarded_card_count() == 2

    assert game_round.has_finished
    assert not alice.is_active
    assert not bob.is_active


def test_busted_player_receives_zero_round_points() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(8),
                NumberCard(7),
            ]
        ),
    )
    game_round.start_round()

    game_round.process_number_card(
        alice,
        NumberCard(7),
    )
    game_round.player_stays(bob)

    round_scores = game_round.finish_round()

    assert round_scores[alice] == 0
    assert round_scores[bob] == 8
    assert alice.total_score == 0
    assert bob.total_score == 8

    assert game_round.deck.discarded_card_count() == 3


def test_round_cannot_finish_while_players_are_active() -> None:
    game_round, _, _ = create_started_round()

    with pytest.raises(RoundStateError):
        game_round.finish_round()


def test_round_cannot_be_finished_twice() -> None:
    game_round, alice, bob = create_started_round()

    game_round.player_stays(alice)
    game_round.player_stays(bob)
    game_round.finish_round()

    alice_score_after_first_finish = alice.total_score
    bob_score_after_first_finish = bob.total_score

    with pytest.raises(RoundStateError):
        game_round.finish_round()

    assert alice.total_score == alice_score_after_first_finish
    assert bob.total_score == bob_score_after_first_finish

def test_resolve_second_chance_assigns_card_to_target() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    action_card = ActionCard(
        ActionType.SECOND_CHANCE
    )

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                action_card,
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    game_round.draw_card_for_player(alice)
    game_round.resolve_pending_action(bob)

    assert game_round.pending_action is None
    assert bob.has_second_chance
    assert action_card in bob.round_cards
    assert not alice.has_second_chance


def test_second_chance_rejects_target_that_already_has_one() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    action_card = ActionCard(
        ActionType.SECOND_CHANCE
    )

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                action_card,
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()
    bob.has_second_chance = True

    game_round.draw_card_for_player(alice)

    with pytest.raises(ValueError):
        game_round.resolve_pending_action(bob)

    assert game_round.pending_action == PendingAction(
        source_player=alice,
        card=action_card,
    )
    assert action_card not in bob.round_cards


def test_second_chance_is_consumed_by_duplicate_number() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    second_chance_card = ActionCard(
        ActionType.SECOND_CHANCE
    )

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(1),
                second_chance_card,
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    game_round.draw_card_for_player(alice)
    game_round.resolve_pending_action(alice)

    assert alice.has_second_chance
    assert second_chance_card in alice.round_cards

    game_round.draw_card_for_player(alice)

    assert not alice.has_second_chance
    assert not alice.has_busted
    assert alice.is_active

    assert alice.get_number_cards().count(
        NumberCard(1)
    ) == 1
    assert second_chance_card not in alice.round_cards
    assert game_round.deck.discarded_card_count() == 2

def test_resolve_flip_three_draws_cards_for_target() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    flip_three_card = ActionCard(
        ActionType.FLIP_THREE
    )

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(5),
                NumberCard(4),
                NumberCard(3),
                flip_three_card,
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    game_round.draw_card_for_player(alice)
    game_round.resolve_pending_action(bob)

    assert flip_three_card in bob.round_cards
    assert bob.get_number_cards() == [
        NumberCard(2),
        NumberCard(3),
        NumberCard(4),
        NumberCard(5),
    ]

    assert game_round.pending_action is None
    assert bob.is_active
    assert not bob.has_busted
    assert game_round.deck.is_empty()

def test_flip_three_stops_when_target_flips_seven() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    flip_three_card = ActionCard(
        ActionType.FLIP_THREE
    )

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(9),
                NumberCard(8),
                NumberCard(7),
                flip_three_card,
                NumberCard(12),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    for number in range(2, 7):
        game_round.process_number_card(
            alice,
            NumberCard(number),
        )

    game_round.draw_card_for_player(bob)
    game_round.resolve_pending_action(alice)

    assert game_round.check_for_flip_seven(alice)
    assert game_round.is_round_finished()

    assert game_round.deck.remaining_card_count() == 2
    assert game_round.pending_action is None

def test_nested_flip_three_is_resolved_after_outer_draws() -> None:
    alice = Player("Alice")
    bob = Player("Bob")

    outer_flip_three = ActionCard(
        ActionType.FLIP_THREE
    )
    inner_flip_three = ActionCard(
        ActionType.FLIP_THREE
    )

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                NumberCard(7),
                NumberCard(6),
                NumberCard(5),
                NumberCard(4),
                NumberCard(3),
                inner_flip_three,
                outer_flip_three,
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    game_round.draw_card_for_player(alice)
    game_round.resolve_pending_action(bob)

    assert game_round.pending_action == PendingAction(
        source_player=bob,
        card=inner_flip_three,
    )

    assert bob.get_number_cards() == [
        NumberCard(2),
        NumberCard(3),
        NumberCard(4),
    ]

    game_round.resolve_pending_action(alice)

    assert game_round.pending_action is None

    assert alice.get_number_cards() == [
        NumberCard(1),
        NumberCard(5),
        NumberCard(6),
        NumberCard(7),
    ]

    assert outer_flip_three in bob.round_cards
    assert inner_flip_three in alice.round_cards
    assert game_round.deck.is_empty()

def test_no_pending_action_has_no_valid_targets() -> None:
    game_round, _, _ = create_started_round()

    assert game_round.get_valid_action_targets() == []


def test_action_targets_include_only_active_players() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    charlie = Player("Charlie")

    game_round = GameRound(
        players=[alice, bob, charlie],
        deck=Deck(
            cards=[
                ActionCard(ActionType.FREEZE),
                NumberCard(3),
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    game_round.player_stays(charlie)
    game_round.draw_card_for_player(alice)

    assert game_round.get_valid_action_targets() == [
        alice,
        bob,
    ]


def test_second_chance_excludes_players_that_have_one() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    charlie = Player("Charlie")

    game_round = GameRound(
        players=[alice, bob, charlie],
        deck=Deck(
            cards=[
                ActionCard(ActionType.SECOND_CHANCE),
                NumberCard(3),
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    bob.has_second_chance = True
    game_round.draw_card_for_player(alice)

    assert game_round.get_valid_action_targets() == [
        alice,
        charlie,
    ]

def test_second_chance_without_valid_target_is_discarded() -> None:
    alice = Player("Alice")
    bob = Player("Bob")
    action_card = ActionCard(
        ActionType.SECOND_CHANCE
    )

    game_round = GameRound(
        players=[alice, bob],
        deck=Deck(
            cards=[
                action_card,
                NumberCard(2),
                NumberCard(1),
            ]
        ),
    )
    game_round.start_round()

    alice.has_second_chance = True
    bob.has_second_chance = True

    game_round.draw_card_for_player(alice)

    assert game_round.pending_action is None
    assert action_card not in alice.round_cards
    assert action_card not in bob.round_cards
    assert game_round.deck.discarded_card_count() == 1

def test_round_records_initial_card_draws() -> None:
    players = [
        Player("Alice"),
        Player("Bob"),
    ]
    deck = Deck(
        cards=[
            NumberCard(8),
            NumberCard(3),
        ]
    )
    game_round = GameRound(players, deck)

    game_round.start_round()

    events = game_round.card_draw_events

    assert len(events) == 2

    assert events[0].player_index == 0
    assert events[0].player_name == "Alice"
    assert events[0].card == NumberCard(3)
    assert events[0].reason is DrawReason.INITIAL_DEAL

    assert events[1].player_index == 1
    assert events[1].player_name == "Bob"
    assert events[1].card == NumberCard(8)
    assert events[1].reason is DrawReason.INITIAL_DEAL


def test_round_records_flip_three_card_draw() -> None:
    players = [
        Player("Alice"),
        Player("Bob"),
    ]
    deck = Deck(
        cards=[
            NumberCard(9),
            NumberCard(8),
            NumberCard(4),
            NumberCard(3),
        ]
    )
    game_round = GameRound(players, deck)
    game_round.start_round()

    game_round.draw_card_for_flip_three(players[0])

    event = game_round.card_draw_events[-1]

    assert event.player_index == 0
    assert event.player_name == "Alice"
    assert event.card == NumberCard(8)
    assert event.reason is DrawReason.FLIP_THREE

def test_round_rejects_invalid_starting_player_index() -> None:
    players = [
        Player("Alice"),
        Player("Bob"),
    ]
    deck = Deck()

    with pytest.raises(
        ValueError,
        match="starting player index",
    ):
        GameRound(
            players=players,
            deck=deck,
            starting_player_index=2,
        )


def test_initial_deal_starts_at_selected_player() -> None:
    players = [
        Player("Alice"),
        Player("Bob"),
        Player("Charlie"),
    ]
    deck = Deck(
        cards=[
            NumberCard(3),
            NumberCard(2),
            NumberCard(1),
        ]
    )

    game_round = GameRound(
        players=players,
        deck=deck,
        starting_player_index=1,
    )

    game_round.start_round()

    assert tuple(
        event.player_index
        for event in game_round.card_draw_events
    ) == (1, 2, 0)

    assert players[0].round_cards == [
        NumberCard(3)
    ]
    assert players[1].round_cards == [
        NumberCard(1)
    ]
    assert players[2].round_cards == [
        NumberCard(2)
    ]


