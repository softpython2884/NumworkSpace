"""The keypad has no anti-ghosting diodes.

On a scanned matrix without diodes, three keys where two share a row and two
share a column make the scan report a fourth key nobody pressed. Two keys are
always safe. This pins the control scheme to combinations that cannot ghost, so
nobody "simplifies" the bindings later and breaks co-op silently.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness


def main():
    g, kand, ion, clock = harness.load()
    L, R, P4, P6 = g["KL"], g["KR"], g["K4"], g["K6"]
    EXE, OK = g["KE"], g["KO"]

    print("key positions in the 9x6 scan matrix")
    for name, k in (("P1 left", L), ("P1 right", R), ("P2 left", P4),
                    ("P2 right", P6), ("overdrive EXE", EXE), ("solo OK", OK)):
        print("   %-14s %s" % (name, ion.matrix_position(k)))

    bad = []
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
    for a in (L, R):
        for c in (EXE, OK):
            if ion.ghosts([a, c]):
                bad.append(("solo", [a, c]))

    print("\nco-op combinations checked : %d" % len(coop))
    print("solo combinations checked  : 4")
    if not ion.ghosts([L, P4, OK]):
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
