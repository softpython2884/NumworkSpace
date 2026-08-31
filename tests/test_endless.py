"""The Void has no ceiling, so every table lookup past sector 5 must hold up.

Sector number feeds palettes, enemy pools, budgets and HUD strings. An
IndexError forty minutes into a good run is the worst possible bug on a device
with no way to inspect the traceback.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness
from test_balance import Dodger


def main():
    fails = []
    for sec in range(5, 40):
        g, kand, ion, clock = harness.load()
        g["keydown"] = Dodger(g).keydown
        g["time"].sleep = lambda d: None
        g["newrun"](1, 1000 + sec)
        g["sector"] = sec
        # Nobody reaches the Void with a stock ship; test the realistic case.
        for u in ("U_DMG", "U_SPREAD", "U_RATE", "U_SPD"):
            g["up"][g[u]] = 2
        g["hull"] = 9999
        g["hullmax"] = 9999
        n = [0]
        real = g["hud"]

        def spy(tag, n=n, real=real):
            n[0] += 1
            if n[0] > 2500:
                raise TimeoutError
            real(tag)

        g["hud"] = spy
        try:
            g["genmap"]()
            g["draw_map"](1)
            g["fight"](g["N_FIGHT"], 3)
            n[0] = 0                     # each fight gets its own budget
            g["fight"](g["N_BOSS"], 7)
        except TimeoutError:
            fails.append((sec, "fight did not terminate"))
        except Exception as exc:
            fails.append((sec, "%s: %s" % (type(exc).__name__, exc)))

    print("sectors exercised beyond the campaign : 5..39")
    if fails:
        for sec, why in fails[:10]:
            print("  FAIL sector %d -> %s" % (sec, why))
        print("FAIL")
        return 1
    print("PASS: no lookup, budget or HUD string breaks in the Void")
    return 0


if __name__ == "__main__":
    sys.exit(main())
