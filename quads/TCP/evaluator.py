import itertools
from typing import Sequence, Optional

from ..card import Card
from .lookup import LookupTable


class Evaluator:
    """
    Evaluates hand strengths using a variant of Cactus Kev's algorithm:
    http://suffe.cool/poker/evaluator.html

    I make considerable optimizations in terms of speed and memory usage, 
    in fact the lookup table generation can be done in under a second and 
    consequent evaluations are very fast. Won't beat C, but very fast as 
    all calculations are done with bit arithmetic and table lookups. 
    """

    def __init__(self) -> None:

        self.table = LookupTable()

    def evaluate(self, hand: list[int], board: Optional[list[int]] = []) -> int:
        """
        This is the function that the user calls to get a hand rank. 

        No input validation because that's cycles!
        """
        all_cards = hand + board
        if len(all_cards) == 3:
            return self._rank(all_cards)
        else:
            return self._poolrank(all_cards)

    def _rank(self, cards: Sequence[int]) -> int:
        """
        Performs an evalution given cards in integer form, mapping them to
        a rank in the range [1, 7462], with lower ranks being more powerful.

        Variant of Cactus Kev's 5 card evaluator, though I saved a lot of memory
        space using a hash table and condensing some of the calculations. 
        """
        # if flush
        if cards[0] & cards[1] & cards[2] & 0xF000:
            handOR = (cards[0] | cards[1] | cards[2]) >> 16
            prime = Card.prime_product_from_rankbits(handOR)
            return self.table.flush_lookup[prime]

        # otherwise
        else:
            prime = Card.prime_product_from_hand(cards)
            return self.table.unsuited_lookup[prime]

    def _poolrank(self, cards: Sequence[int]) -> int:
        """
        Performs five_card_eval() on all (6 choose 5) = 6 subsets
        of 5 cards in the set of 6 to determine the best ranking, 
        and returns this ranking.
        """
        minimum = LookupTable.MAX_HIGH_CARD

        for combo in itertools.combinations(cards, 3):
            score = self._rank(combo)
            if score < minimum:
                minimum = score

        return minimum

    def get_rank_class(self, hr: int) -> int:
        """
        Returns the class of hand given the hand hand_rank
        returned from evaluate. 
        """
        if hr >= 0 and hr <= LookupTable.Max_MINIROYAL:
            return LookupTable.MAX_TO_RANK_CLASS[LookupTable.Max_MINIROYAL]
        elif hr <= LookupTable.MAX_STRAIGHT_FLUSH:
            return LookupTable.MAX_TO_RANK_CLASS[LookupTable.MAX_STRAIGHT_FLUSH]
        elif hr <= LookupTable.MAX_THREE_OF_A_KIND:
            return LookupTable.MAX_TO_RANK_CLASS[LookupTable.MAX_THREE_OF_A_KIND]
        elif hr <= LookupTable.MAX_STRAIGHT:
            return LookupTable.MAX_TO_RANK_CLASS[LookupTable.MAX_STRAIGHT]
        elif hr <= LookupTable.MAX_FLUSH:
            return LookupTable.MAX_TO_RANK_CLASS[LookupTable.MAX_FLUSH]
        elif hr <= LookupTable.MAX_PAIR:
            return LookupTable.MAX_TO_RANK_CLASS[LookupTable.MAX_PAIR]
        elif hr <= LookupTable.MAX_HIGH_CARD:
            return LookupTable.MAX_TO_RANK_CLASS[LookupTable.MAX_HIGH_CARD]
        else:
            raise Exception("Inavlid hand rank, cannot return rank class")

    def class_to_string(self, class_int: int) -> str:
        """
        Converts the integer class hand score into a human-readable string.
        """
        return LookupTable.RANK_CLASS_TO_STRING[class_int]

    def get_five_card_rank_percentage(self, hand_rank: int) -> float:
        """
        Scales the hand rank score to the [0.0, 1.0] range.
        """
        return float(hand_rank) / float(LookupTable.MAX_HIGH_CARD)


class PLOEvaluator(Evaluator):

    HAND_LENGTH = 4

    def evaluate(self, hand: list[int], board: list[int]) -> int:
        minimum = LookupTable.MAX_HIGH_CARD

        for hand_combo in itertools.combinations(hand, 2):
            for board_combo in itertools.combinations(board, 3):
                score = Evaluator._five(self, list(board_combo) + list(hand_combo))
                if score < minimum:
                    minimum = score

        return minimum
