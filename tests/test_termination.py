"""Every fight must end.

A camping enemy that the player is content to dodge forever is not a difficulty
spike, it is a soft-lock -- and on a calculator there is no way out but pulling
the batteries. This sweep plays a wide grid of fights with an invincible pilot
(so death cannot mask a stall) and fails if any of them runs long.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness
from test_balance import Dodger

LIMIT = 2500          # 100 s at 25 fps: far beyond any legitimate wave


def sweep():
    bad = []
    total = 0
    for seed in (101, 777, 4242, 9001):
        for sec in range(5):
            for node in (1, 3, 6):
                for kind in ("N_FIGHT", "N_ELITE"):
                    total += 1
                    g, kand, ion, clock = harness.load()
                    g["keydown"] = Dodger(g).keydown
                    g["time"].sleep = lambda d: None
                    g["newrun"](1, seed)
                    g["sector"] = sec
                    g["hull"] = 9999
                    g["hullmax"] = 9999
                    n = [0]
                    real = g["hud"]

                    def spy(tag, n=n, real=real):
                        n[0] += 1
                        if n[0] > LIMIT:
                            raise TimeoutError
                        real(tag)

                    g["hud"] = spy
                    try:
                        g["fight"](g[kind], node)
                    except TimeoutError:
                        alive = [(g["et"][i], g["ey"][i]) for i in range(g["ne"])]
                        bad.append((seed, sec, node, kind, alive))
    return total, bad


def main():
    total, bad = sweep()
    print("fights swept: %d   non-terminating: %d" % (total, len(bad)))
    for b in bad[:10]:
        print("  seed=%d sector=%d node=%d %s survivors=%s" % b)
    print("PASS" if not bad else "FAIL")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
