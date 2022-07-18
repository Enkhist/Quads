from collections.abc import Iterator
import itertools
from typing import Sequence

from ..card import Card


class LookupTable:
    """
    Number of Distinct Hand Values:

    Four of a Kind   13       [(13 choose 1)]
    Straight Flush   11 
    Three of a Kind  156      [13 * 12]
    Flush            704      [(13 choose 4) - 11 straight flushes]
    Straight         11 
    Two Pair         156      [13 * 12]
    One Pair         858      [13 * (12 choose 2)]
    High Card      + 704      [(13 choose 4) - 11 straights]
    -------------------------
    TOTAL            2613

    Here we create a lookup table which maps:
        5 card hand's unique prime product => rank in range [1, 7462]

    Examples:
    * Four aces (best hand possible)            => 1
    * 6-4-3-2 unsuited (worst hand possible)    => 2613
    """
    MAX_FOUR_OF_A_KIND: int  = 13
    MAX_STRAIGHT_FLUSH: int  = 24
    MAX_THREE_OF_A_KIND: int = 180
    MAX_FLUSH: int           = 884
    MAX_STRAIGHT: int        = 895
    MAX_TWO_PAIR: int        = 1051
    MAX_PAIR: int            = 1909
    MAX_HIGH_CARD: int       = 2613

    MAX_TO_RANK_CLASS: dict[int, int] = {
        MAX_FOUR_OF_A_KIND: 0,
        MAX_STRAIGHT_FLUSH: 1,
        MAX_THREE_OF_A_KIND: 2,
        MAX_FLUSH: 3,
        MAX_STRAIGHT: 4,
        MAX_TWO_PAIR: 5,
        MAX_PAIR: 6,
        MAX_HIGH_CARD: 7
    }

    RANK_CLASS_TO_STRING: dict[int, str] = {
        0: "Four of a Kind",
        1: "Straight Flush",
        2: "Three of a Kind",
        3: "Flush",
        4: "Straight",
        5: "Two Pair",
        6: "Pair",
        7: "High Card"
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
            7680,  # int('0b1111000000000', 2), # royal flush
            3840,  # int('0b111100000000', 2),
            1920,  # int('0b11110000000', 2),
            960,   # int('0b1111000000', 2),
            480,   # int('0b111100000', 2),
            240,   # int('0b11110000', 2),
            120,   # int('0b1111000', 2),
            60,    # int('0b111100', 2),
            30,    # int('0b11110', 2),
            15,    # int('0b1111', 2),
            4103   # int('0b1000000000111', 2) # 4 high
        ]

        # now we'll dynamically generate all the other
        # flushes (including straight flushes)
        flushes = []
        gen = self.get_lexographically_next_bit_sequence(int('0b1111', 2))

        # 704 = number of high cards
        # 704 + len(str_flushes) is number of hands with all cards unique rank
        for i in range(704 + len(straight_flushes) - 1):   # we also iterate over SFs
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
        # rank 1 = Royal Flush!
        rank = LookupTable.MAX_FOUR_OF_A_KIND+1
        for sf in straight_flushes:
            prime_product = Card.prime_product_from_rankbits(sf)
            self.flush_lookup[prime_product] = rank
            rank += 1

        # we start the counting for flushes on max three of a kind, which
        # is the worst rank that a three of a kind can have (2,2,2,2,3)
        rank = LookupTable.MAX_THREE_OF_A_KIND + 1
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
        rank = LookupTable.MAX_FLUSH + 1

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
        Pair, Two Pair, Three of a Kind, Full House, and 4 of a Kind.
        """
        backwards_ranks = list(range(len(Card.INT_RANKS) - 1, -1, -1))

        # 1) Four of a Kind
        rank = 1

        # for each choice of a set of four rank
        for i in backwards_ranks:
            product = Card.PRIMES[i]**4
            self.unsuited_lookup[product] = rank
            rank += 1

        # 2) Three of a Kind
        rank = LookupTable.MAX_STRAIGHT_FLUSH + 1

        # pick three of one rank
        for r in backwards_ranks:

            kickers = backwards_ranks[:]
            kickers.remove(r)

            for kicker in kickers:
                product = Card.PRIMES[r]**3 * Card.PRIMES[kicker]
                self.unsuited_lookup[product] = rank
                rank += 1

        # 4) Two Pair
        rank = LookupTable.MAX_STRAIGHT + 1

        tpgen = itertools.combinations(tuple(backwards_ranks), 2)
        for tp in tpgen:

            pair1, pair2 = tp
            product = Card.PRIMES[pair1]**2 * Card.PRIMES[pair2]**2
            self.unsuited_lookup[product] = rank
            rank += 1



        # 5) Pair
        rank = LookupTable.MAX_TWO_PAIR + 1

        # choose a pair
        for pairrank in backwards_ranks:

            kickers = backwards_ranks[:]
            kickers.remove(pairrank)
            kgen = itertools.combinations(tuple(kickers), 2)

            for kickers_3combo in kgen:

                k1, k2 = kickers_3combo
                product = Card.PRIMES[pairrank]**2 * Card.PRIMES[k1] \
                    * Card.PRIMES[k2]
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
