"""Every fight must end.

A camping enemy the player is happy to dodge forever is not a difficulty spike,
it is a soft-lock -- and on a calculator there is no way out but pulling the
batteries. This sweeps a grid of fights with an invincible pilot, so death
cannot mask a stall, and fails if any of them runs long.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness
from bot import Dodger

LIMIT = 3000          # 120 s at 25 fps: far beyond any legitimate wave


def setup(g, seed, sector, node, players=1):
    S = g["S"]
    g["keydown"] = Dodger(g).keydown
    g["PON"][1] = 1 if players > 1 else 0
    g["PX"][0] = 153
    g["PX"][1] = 216
    for i in range(2):
        g["PC"][i] = 4
        g["PI"][i] = 0
    for i in range(8):
        g["UP"][i] = 0
    S[g["HMAX"]] = 9999
    S[g["HULL"]] = 9999
    S[g["SECT"]] = sector
    S[g["NODE"]] = node
    S[g["BMAX"]] = 2
    S[g["BOMB"]] = 2
    S[g["CRY"]] = 0
    S[g["SCORE"]] = 0
    g["srnd"](seed)


def sweep():
    bad = []
    total = 0
    for seed in (101, 777, 4242, 9001):
        for sec in range(6):
            for node in (1, 3, 6):
                for kind in (0, 1):
                    total += 1
                    g, kand, ion, clock = harness.load()
                    setup(g, seed, sec, node)
                    n = [0]
                    real = g["hud"]

                    def spy(tag, n=n, real=real):
                        n[0] += 1
                        if n[0] > LIMIT:
                            raise TimeoutError
                        real(tag)

                    g["hud"] = spy
                    try:
                        g["fight"](kind)
                    except TimeoutError:
                        S = g["S"]
                        alive = [(g["E"][o + 2], g["E"][o + 1])
                                 for o in range(0, S[g["NE"]] * 6, 6)]
                        bad.append((seed, sec, node, kind, alive))
    return total, bad


def main():
    total, bad = sweep()
    print("fights swept: %d   non-terminating: %d" % (total, len(bad)))
    for b in bad[:8]:
        print("  seed=%d sector=%d node=%d kind=%d survivors=%s" % b)
    print("PASS" if not bad else "FAIL")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
