from enum import unique

from flip7.agents.base_agent import AgentObservation
from flip7.game.cards import NumberCard

State = tuple[int, int, int, int]

SCORE_BUCKET_SIZE = 5
MAX_SCORE_BUCKET = 12
MAX_UNIQUE_NUMBERS = 7
BUST_PROBABILITY_BUCKETS = 10


def calculate_bust_probability(observation: AgentObservation):
    """Share of remaining deck cards that would bust the own player"""
    if observation.remaining_card_count <= 0:
        return 0.0

    own_numbers = {
        card.number for card in observation.own_player.round_cards if isinstance(card, NumberCard)
    }

    busting_cards = sum(
        entry.remaining_count for entry in observation.deck_card_counts if isinstance(entry.card, NumberCard)
        and entry.card.number in own_numbers
    )

    return  busting_cards / observation.remaining_card_count

def encode_state(observation: AgentObservation) -> State:
    """Encode the observation into a state tuple"""
    own_obs = observation.own_player

    score_bucket = min(
        own_obs.current_round_score // SCORE_BUCKET_SIZE,
        MAX_SCORE_BUCKET,
    )

    unique_numbers = min(own_obs.number_of_unique_numbers, MAX_UNIQUE_NUMBERS)

    bust_bucket = min(
        int(calculate_bust_probability(observation) * BUST_PROBABILITY_BUCKETS),
        BUST_PROBABILITY_BUCKETS - 1,
    )

    return (
        score_bucket,
        unique_numbers,
        bust_bucket,
        int(own_obs.has_second_chance),
    )