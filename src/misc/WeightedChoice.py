from random import random
from bisect import bisect

#>>> weighted_choice([("WHITE",90), ("RED",8), ("GREEN",2)]) -> 'WHITE

def weighted_choice(choices):
    values, weights = zip(*choices)
    total = 0
    cum_weights = []
    for w in weights:
        total += w
        cum_weights.append(total)
    x = random() * total
    i = bisect(cum_weights, x)
    return values[i]