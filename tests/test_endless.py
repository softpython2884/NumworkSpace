"""The Void has no ceiling, so every table lookup past sector 5 must hold up.

Sector number feeds palettes, enemy pools, budgets and HUD strings. An
IndexError forty minutes into a good run is the worst possible bug on a device
that shows you no traceback.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness
from bot import Dodger
from test_termination import setup

LIMIT = 3000


def main():
    fails = []
    for sec in range(5, 40):
        g, kand, ion, clock = harness.load()
        setup(g, 1000 + sec, sec, 3)
        # Nobody reaches the Void with a stock ship; test the realistic case.
        for u in ("UDMG", "USPR", "URATE", "USPD"):
            g["UP"][g[u]] = 2
        n = [0]
        real = g["hud"]

        def spy(tag, n=n, real=real):
            n[0] += 1
            if n[0] > LIMIT:
                raise TimeoutError
            real(tag)

        g["hud"] = spy
        try:
            g["fight"](0)
            n[0] = 0
            g["S"][g["NODE"]] = 7
            g["fight"](5)
        except TimeoutError:
            fails.append((sec, "fight did not terminate"))
        except Exception as exc:
            fails.append((sec, "%s: %s" % (type(exc).__name__, exc)))

    print("sectors exercised beyond the campaign : 5..39")
    if fails:
        for sec, why in fails[:8]:
            print("  FAIL sector %d -> %s" % (sec, why))
        print("FAIL")
        return 1
    print("PASS: no lookup, budget or HUD string breaks in the Void")
    return 0


if __name__ == "__main__":
    sys.exit(main())
