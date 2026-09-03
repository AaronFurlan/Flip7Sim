from flip7.agents.base_agent import (
    AgentObservation,
    BaseAgent,
    Card,
    TargetOption,
    TurnDecision,
)
from flip7.game.cards import (
    CardType,
    ModifierType,
    ActionType
)

class AlgorithmicNumbersOnlyAgent(BaseAgent):
    def __init__(self, player_name: str) -> None:
        super().__init__(player_name)

    def choose_hit_or_stay(self, observation: AgentObservation) -> TurnDecision:
        if not observation.valid_turn_decisions:
            raise ValueError("An algorithmic numbers-only agent requires at least one valid turn decision.")

        standing_score = observation.own_player.total_score
        accumulated_deck_score = 0
        evaluated_cards = 0
        
        for card in observation.deck_content:
            match card.card_type:
                case CardType.NUMBER:
                    evaluated_cards += 1
                    if card not in observation.own_player.round_cards:          # TODO: Add check for Second Chance
                        accumulated_deck_score += standing_score + card.number

                case CardType.MODIFIER:
                    match card.modifier_type:
                        case ModifierType.ADDITIVE:
                            evaluated_cards += 1
                            accumulated_deck_score += standing_score + card.value

                        case ModifierType.MULTIPLIER:
                            evaluated_cards += 1
                            accumulated_deck_score += standing_score * card.value

                case CardType.ACTION:
                    match card.action_type:
                        case ActionType.SECOND_CHANCE:
                            pass

                        case ActionType.FREEZE:
                            pass

                        case ActionType.FLIP_THREE:
                            pass

        if evaluated_cards == 0: return TurnDecision.STAY
        else: projected_score = accumulated_deck_score / evaluated_cards

        if projected_score > standing_score: return TurnDecision.HIT
        else: return TurnDecision.STAY

    def choose_action_target(
        self,
        observation: AgentObservation,
        action_type: ActionType,
        valid_targets: tuple[TargetOption, ...],
    ) -> TargetOption:
        if not valid_targets:
            raise ValueError(
                "An algorithmic numbers-only agent requires at least one valid target."
            )

        target = None
        for t in valid_targets:
            if t.player.player_name == self.player_name:
                target = t
                break

        if target is None:
            return valid_targets[0]  # TODO: Remove this line once the bug with agents acting while already out of the round
            raise ValueError(
                f"No valid target found for player name {self.player_name}."
            )

        return target