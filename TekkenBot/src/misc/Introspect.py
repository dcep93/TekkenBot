import collections
import time

active = {}
g = collections.defaultdict(int)
def watch(parent):
    def child(*args, **kwargs):
        gkey = parent.__repr__()
        g[gkey] += 1
        id = g[gkey]
        key = (id, gkey)
        active[key] = time.time()
        rval = parent(*args, **kwargs)
        del active[key]
        return rval
    return child

def monitor():
    now = time.time()
    for key, start in active.items():
        duration = now - start
        print(key, duration)
    print(len(active))
