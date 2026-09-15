def calculate_round_reward(round_score: int) -> float:
    """Terminal reward for one round. A bust yields a round score of 0."""
    return float(round_score)