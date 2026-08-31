"""Sector maps must be walkable and must pace every route the same way."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness


def reachable(g):
    """Rows reachable per column, walking forward from the entry node."""
    MR = g["MROWS"]
    mt = g["mt"]
    seen = [set() for _ in range(g["MCOLS"])]
    seen[0].add(1)
    for c in range(g["MCOLS"] - 1):
        for r in seen[c]:
            for r2 in range(MR):
                if abs(r2 - r) <= 1 and mt[(c + 1) * MR + r2] >= 0:
                    seen[c + 1].add(r2)
    return seen


def main():
    g, kand, ion, clock = harness.load()
    MR = g["MROWS"]
    MC = g["MCOLS"]
    N_SHOP, N_REST, N_BOSS = g["N_SHOP"], g["N_REST"], g["N_BOSS"]

    orphans = 0
    dead_ends = 0
    no_shop = 0
    no_rest = 0
    no_boss = 0
    widths = []
    maps = 400

    for seed in range(1, maps + 1):
        g["srnd"](seed)
        g["genmap"]()
        mt = g["mt"]
        seen = reachable(g)

        # 1. every placed node must be reachable from the entry
        for c in range(MC):
            for r in range(MR):
                if mt[c * MR + r] >= 0 and r not in seen[c]:
                    orphans += 1
        # 2. no column may be empty (the route would dead-end)
        for c in range(MC):
            if not seen[c]:
                dead_ends += 1
                break
        # 3. every route must pass a trader and a repair bay
        if any(mt[4 * MR + r] != N_SHOP for r in seen[4]) or not seen[4]:
            no_shop += 1
        if any(mt[6 * MR + r] != N_REST for r in seen[6]) or not seen[6]:
            no_rest += 1
        # 4. the boss must be there and reachable
        if mt[(MC - 1) * MR + 1] != N_BOSS or 1 not in seen[MC - 1]:
            no_boss += 1
        widths.append(sum(len(s) for s in seen) / MC)

    print("maps generated              : %d" % maps)
    print("unreachable nodes           : %d" % orphans)
    print("maps with a dead-end column : %d" % dead_ends)
    print("routes missing a trader     : %d" % no_shop)
    print("routes missing a repair bay : %d" % no_rest)
    print("maps missing a boss         : %d" % no_boss)
    print("average reachable width     : %.2f of %d rows" %
          (sum(widths) / len(widths), MR))

    ok = not (orphans or dead_ends or no_shop or no_rest or no_boss)
    # A map where every column is fully reachable offers no real choice.
    branching = 1.15 < sum(widths) / len(widths) < 2.95
    if not branching:
        print("FAIL: maps are not branching enough to feel like a choice")
    print("PASS" if ok and branching else "FAIL")
    return 0 if ok and branching else 1


if __name__ == "__main__":
    sys.exit(main())
