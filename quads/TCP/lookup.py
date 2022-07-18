from collections.abc import Iterator
import itertools
from typing import Sequence

from ..card import Card


class LookupTable:
    """
    Number of Distinct Hand Values:

    Straight Flush   12
    Three of a Kind  13
    Straight         12
    Flush            274     [(13 choose 3) - 12 straight flushes]
    One Pair         156     [(13 choose 4) * (4 choose 1)]
    High Card      + 274     [(13 choose 5) - 10 straights]
    -------------------------
    TOTAL            741

    Here we create a lookup table which maps:
        3 card hand's unique prime product => rank in range [1, 741]

    Examples:
    * Miniroyal (best hand possible)        => 1
    * 5-3-2 unsuited (worst hand possible)  => 741
    """
    MAX_MINIROYAL: int       = 1
    MAX_STRAIGHT_FLUSH: int  = 12
    MAX_THREE_OF_A_KIND: int = 25
    MAX_STRAIGHT: int        = 37
    MAX_FLUSH: int           = 311
    MAX_PAIR: int            = 467
    MAX_HIGH_CARD: int       = 741

    MAX_TO_RANK_CLASS: dict[int, int] = {
        MAX_MINIROYAL: 0,
        MAX_STRAIGHT_FLUSH: 1,
        MAX_THREE_OF_A_KIND: 2,
        MAX_STRAIGHT: 3,
        MAX_FLUSH: 4,
        MAX_PAIR: 5,
        MAX_HIGH_CARD: 6
    }

    RANK_CLASS_TO_STRING: dict[int, str] = {
        0: "Mini Royal",
        1: "Straight Flush",
        2: "Three of a Kind",
        3: "Straight",
        4: "Flush",
        5: "Pair",
        6: "High Card"
    }

    def __init__(self) -> None:
        """
        Calculates lookup tables
        """
        # create dictionaries
        self.flush_lookup: dict[int, int] = {}
        self.unsuited_lookup: dict[int, int] = {}

        # create the lookup table in piecewise fashion
        # this will call straights and high cards method,
        # we reuse some of the bit sequences
        self.flushes()
        self.multiples()

    def flushes(self) -> None:
        """
        Straight flushes and flushes. 

        Lookup is done on 13 bit integer (2^13 > 7462):
        xxxbbbbb bbbbbbbb => integer hand index
        """

        # straight flushes in rank order
        straight_flushes = [
            7168,  # int('0b1110000000000', 2), # royal flush
            3854,  # int('0b111000000000', 2),
            1792,  # int('0b11100000000', 2),
            896,   # int('0b1110000000', 2),
            448,   # int('0b111000000', 2),
            224,   # int('0b11100000', 2),
            112,   # int('0b1110000', 2),
            56,    # int('0b111000', 2),
            28,    # int('0b11100', 2),
            14,    # int('0b1110', 2),
            7,     # int('0b111', 2),
            4099   # int('0b1000000000011', 2) # 3 high
        ]

        # now we'll dynamically generate all the other
        # flushes (including straight flushes)
        flushes = []
        gen = self.get_lexographically_next_bit_sequence(int('0b111', 2))

        # 274 = number of high cards
        # 1277 + len(str_flushes) is number of hands with all cards unique rank
        for i in range(274 + len(straight_flushes) - 1):   # we also iterate over SFs
            # pull the next flush pattern from our generator
            f = next(gen)

            # if this flush matches perfectly any
            # straight flush, do not add it
            notSF = True
            for sf in straight_flushes:
                # if f XOR sf == 0, then bit pattern 
                # is same, and we should not add
                if not f ^ sf:
                    notSF = False

            if notSF:
                flushes.append(f)

        # we started from the lowest straight pattern, now we want to start ranking from
        # the most powerful hands, so we reverse
        flushes.reverse()

        # now add to the lookup map:
        # start with straight flushes and the rank of 1
        # since it is the best hand in poker
        # rank 1 = Miniroyal!
        rank = 1
        for sf in straight_flushes:
            prime_product = Card.prime_product_from_rankbits(sf)
            self.flush_lookup[prime_product] = rank
            rank += 1

        # we start the counting for flushes on max straight, which
        # is the worst rank that an unsuited straight can have (2,3,5)
        rank = LookupTable.MAX_STRAIGHT + 1
        for f in flushes:
            prime_product = Card.prime_product_from_rankbits(f)
            self.flush_lookup[prime_product] = rank
            rank += 1

        # we can reuse these bit sequences for straights
        # and high cards since they are inherently related
        # and differ only by context 
        self.straight_and_highcards(straight_flushes, flushes)

    def straight_and_highcards(self, straights: Sequence[int], highcards: Sequence[int]) -> None:
        """
        Unique five card sets. Straights and highcards. 

        Reuses bit sequences from flush calculations.
        """
        rank = LookupTable.MAX_THREE_OF_A_KIND+ 1

        for s in straights:
            prime_product = Card.prime_product_from_rankbits(s)
            self.unsuited_lookup[prime_product] = rank
            rank += 1

        rank = LookupTable.MAX_PAIR + 1
        for h in highcards:
            prime_product = Card.prime_product_from_rankbits(h)
            self.unsuited_lookup[prime_product] = rank
            rank += 1

    def multiples(self) -> None:
        """
        Pair, Three of a Kind
        """
        backwards_ranks = list(range(len(Card.INT_RANKS) - 1, -1, -1))

        # 1) Three of a Kind
        rank = LookupTable.MAX_STRAIGHT_FLUSH + 1

        # pick three of one rank
        for r in backwards_ranks:
            product = Card.PRIMES[r]**3
            self.unsuited_lookup[product] = rank
            rank += 1

        # 5) Pair
        rank = LookupTable.MAX_FLUSH + 1

        # choose a pair
        for pairrank in backwards_ranks:

            kickers = backwards_ranks[:]
            kickers.remove(pairrank)

            for kicker in kickers:
                product = Card.PRIMES[pairrank]**2 * Card.PRIMES[kicker]
                self.unsuited_lookup[product] = rank
                rank += 1

    def write_table_to_disk(self, table: dict[int, int], filepath: str) -> None:
        """
        Writes lookup table to disk
        """
        with open(filepath, 'w') as f:
            for prime_prod, rank in table.items():
                f.write(str(prime_prod) + "," + str(rank) + '\n')

    def get_lexographically_next_bit_sequence(self, bits: int) -> Iterator[int]:
        """
        Bit hack from here:
        http://www-graphics.stanford.edu/~seander/bithacks.html#NextBitPermutation

        Generator even does this in poker order rank 
        so no need to sort when done! Perfect.
        """
        t = int((bits | (bits - 1))) + 1
        next = t | ((int(((t & -t) / (bits & -bits))) >> 1) - 1)
        yield next
        while True:
            t = (next | (next - 1)) + 1 
            next = t | ((((t & -t) // (next & -next)) >> 1) - 1)
            yield next
