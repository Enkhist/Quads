import time

from quads.deck import Deck
from quads.evaluator import Evaluator


def setup(n: int, m: int) -> tuple[list[list[int]], list[list[int]]]:

    deck = Deck()

    boards = []
    hands = []

    for _ in range(n):
        boards.append(deck.draw(m))
        hands.append(deck.draw(2))
        deck.shuffle()

    return boards, hands


n = 10000
cumtime = 0.0
evaluator = Evaluator()
boards, hands = setup(n, 5)
for i in range(len(boards)):
    start = time.time()
    evaluator.evaluate(hands[i], boards[i])
    cumtime += (time.time() - start)

avg = float(cumtime / n)
print("7 card evaluation:")
print("[*] Quads: Average time per evaluation: %f" % avg)
print("[*] Quads: Evaluations per second = %f" % (1.0 / avg))

###

cumtime = 0.0
boards, hands = setup(n, 4)
for i in range(len(boards)):
    start = time.time()
    evaluator.evaluate(hands[i], boards[i])
    cumtime += (time.time() - start)

avg = float(cumtime / n)
print("6 card evaluation:")
print("[*] Quads: Average time per evaluation: %f" % avg)
print("[*] Quads: Evaluations per second = %f" % (1.0 / avg))

###

cumtime = 0.0
boards, hands = setup(n, 3)
for i in range(len(boards)):
    start = time.time()
    evaluator.evaluate(hands[i], boards[i])
    cumtime += (time.time() - start)

avg = float(cumtime / n)
print("5 card evaluation:")
print("[*] Quads: Average time per evaluation: %f" % avg)
print("[*] Quads: Evaluations per second = %f" % (1.0 / avg))
