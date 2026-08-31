"""The keypad has no anti-ghosting diodes.

On a scanned matrix without diodes, three keys where two share a row and two
share a column make the scan report a fourth key nobody pressed. Two keys are
always safe. This test pins the control scheme to combinations that cannot
ghost, so nobody "simplifies" the bindings later and breaks co-op silently.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness


def main():
    g, kand, ion, clock = harness.load()
    L, R = g["K_L"], g["K_R"]
    P4, P6 = g["K_4"], g["K_6"]
    EXE, OK = g["K_EXE"], g["K_OK"]

    print("key positions in the 9x6 scan matrix")
    for name, k in (("P1 left", L), ("P1 right", R), ("P2 left", P4),
                    ("P2 right", P6), ("overdrive EXE", EXE), ("solo OK", OK)):
        print("   %-14s %s" % (name, ion.matrix_position(k)))
    print()

    bad = []
    # Every combination two co-op players plus the shared overdrive can produce.
    coop = []
    for a in (None, L, R):
        for b in (None, P4, P6):
            for c in (None, EXE):
                combo = [k for k in (a, b, c) if k is not None]
                if len(combo) > 1:
                    coop.append(combo)
    for combo in coop:
        if ion.ghosts(combo):
            bad.append(("co-op", combo))

    # Solo may also use OK, and can only ever hold two keys.
    for a in (L, R):
        for c in (EXE, OK):
            if ion.ghosts([a, c]):
                bad.append(("solo", [a, c]))

    print("co-op combinations checked : %d" % len(coop))
    print("solo combinations checked  : 4")

    # Sanity check the detector itself: a known-bad trio must be flagged.
    trap = [L, P4, OK]     # rows 0/6, columns 0/0 and 0/4 -> ghosts
    if not ion.ghosts(trap):
        print("FAIL: the ghosting model itself is broken")
        return 1
    print("detector self-check        : a known-bad trio is correctly rejected")

    if bad:
        for tag, combo in bad:
            print("FAIL %s: %s can ghost" % (tag, combo))
        return 1
    print("\nPASS: no legal combination can ghost")
    return 0


if __name__ == "__main__":
    sys.exit(main())
