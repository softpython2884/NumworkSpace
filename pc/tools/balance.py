"""Measure the two things a shmup can get quietly wrong: pacing and the boss.

Win rate alone hides both. A run can be won every time while the boss is a
formality, and a map can be a branching graph on screen while every branch
leads to the same place. So this reports:

  the map     how many repair bays a sector offers, and whether one is always
              reachable -- if it is, the route choice is decoration
  the boss    hull on entering the fight, hull lost in it, and how often the
              player walks out untouched

Run it before and after touching sector.py or boss.py. Numbers, not vibes.

    python3 pc/tools/balance.py            # the standard set
    python3 pc/tools/balance.py 24         # more seeds, slower, steadier
"""

import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
PC = os.path.dirname(HERE)
sys.path.insert(0, PC)
sys.path.insert(0, os.path.join(PC, "tests"))

import pygame

import test_run
from nova import data, sector

SEEDS = (1, 7, 42, 101, 777, 2024, 31415, 60007, 8, 13, 271, 1618)


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


# --- the map -------------------------------------------------------------
def map_stats(samples=400):
    """Generate maps and ask what the player is actually being offered.

    `forced` is the number that matters: a sector where every path from the
    entrance crosses a repair bay has not given the player a choice, it has
    given them a corridor.
    """
    rests = []
    shops = []
    forced_rest = 0
    forced_shop = 0
    rest_before_boss = 0
    for i in range(samples):
        rng = random.Random(i)
        smap = sector.SectorMap(rng, i % 5)
        kinds = list(smap.nodes.values())
        rests.append(kinds.count(data.N_REST))
        shops.append(kinds.count(data.N_SHOP))
        if every_path_crosses(smap, data.N_REST):
            forced_rest += 1
        if every_path_crosses(smap, data.N_SHOP):
            forced_shop += 1
        last = sector.COLS - 2
        if any(k == data.N_REST for (c, _r), k in smap.nodes.items()
               if c == last):
            rest_before_boss += 1
    return {
        "rest_per_map": mean(rests),
        "shop_per_map": mean(shops),
        "maps_with_rest": 100.0 * sum(1 for r in rests if r) / samples,
        "forced_rest": 100.0 * forced_rest / samples,
        "forced_shop": 100.0 * forced_shop / samples,
        "rest_last_col": 100.0 * rest_before_boss / samples,
    }


def every_path_crosses(smap, kind):
    """True when no route from the entrance to the boss avoids `kind`.

    Walked forwards: a node is 'avoidable' when it is reachable by a path that
    has met no node of this kind yet. If the boss is avoidable, a clean route
    exists.
    """
    start = (0, 1)
    clean = set()
    if smap.nodes[start] != kind:
        clean.add(start)
    for col in range(sector.COLS - 1):
        for (c, r) in list(clean):
            if c != col:
                continue
            for nxt in smap.links.get((c, r), []):
                if smap.nodes[nxt] != kind:
                    clean.add(nxt)
    return not any(c == sector.COLS - 1 for (c, _r) in clean)


# --- the fights ----------------------------------------------------------
def run_set(seeds, difficulty, by_sector=None):
    """Play the seeds and total up what the boss fights cost.

    `by_sector` accumulates the same figures per sector, because the average
    across a campaign hides the thing worth knowing: whether the *first* boss
    a player meets is a fight or a formality.
    """
    wins = 0
    boss_dmg = []
    boss_entry = []
    boss_time = []
    untouched = 0
    minutes = []
    for s in seeds:
        r = test_run.run_once(s, difficulty=difficulty)
        wins += r["won"]
        minutes.append(r["minutes"])
        for (sec, _node, kind, t, hull0, lost, _res) in r["log"]:
            if kind != data.N_BOSS:
                continue
            boss_dmg.append(lost)
            boss_entry.append(hull0 / r["max_hull"])
            boss_time.append(t)
            if lost == 0:
                untouched += 1
            if by_sector is not None:
                row = by_sector.setdefault(min(sec, 5), [0, 0.0, 0.0, 0])
                row[0] += 1
                row[1] += lost
                row[2] += t
                row[3] += (lost == 0)
    n = max(1, len(boss_dmg))
    return {
        "wins": wins,
        "runs": len(seeds),
        "boss_fights": len(boss_dmg),
        "boss_dmg": mean(boss_dmg),
        "boss_entry": mean(boss_entry),
        "boss_time": mean(boss_time),
        "untouched": 100.0 * untouched / n,
        "minutes": mean(minutes),
    }


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 8
    seeds = SEEDS[:count] if count <= len(SEEDS) else \
        tuple(range(1, count + 1))
    pygame.init()

    m = map_stats()
    print("=== the map (400 generated sectors) ===")
    print("  repair bays per sector    : %.2f" % m["rest_per_map"])
    print("  sectors offering one      : %.0f%%" % m["maps_with_rest"])
    print("  every route crosses one   : %.0f%%   <- 100%% means no choice"
          % m["forced_rest"])
    print("  repair in the last column : %.0f%%   <- full hull at the boss"
          % m["rest_last_col"])
    print("  traders per sector        : %.2f" % m["shop_per_map"])
    print("  every route crosses one   : %.0f%%" % m["forced_shop"])

    names = ("GRUNT", "WEAVER", "TURRET", "RUSHER", "TANK", "BOSS",
             "LANCER", "SPINNER", "PHANTOM")
    print("\n=== the roster, sector by sector ===")
    seen = set()
    for sec in range(7):
        kinds = set(data.roster(sec))
        fresh = sorted(kinds - seen)
        seen = kinds
        print("  %-8s %2d kinds   new: %s"
              % ("VOID %d" % (sec - 4) if sec > 4 else "sector %d" % (sec + 1),
                 len(kinds), ", ".join(names[k] for k in fresh) or "-"))

    # A figure that does not depend on the pilot at all: how long a boss
    # survives someone who lands every shot. This is the number the game is
    # tuned on, because the test pilot is a dodger -- it holds its line on a
    # boss about 31% of the time -- and tuning to that is what let a sector-5
    # boss die in under four seconds to anybody who aimed.
    print("\n=== boss hit points, against a player who lands everything ===")
    print("%-9s %10s %9s %11s" % ("sector", "boss hp", "dps", "seconds"))
    for sec in (0, 2, 4, 5):
        run = test_run.Run(1, 1, seed=1)
        run.sector = sec
        for u in (data.U_DMG, data.U_SPREAD, data.U_RATE):
            run.upgrades[u] = min(3, sec)
        c = test_run.Combat(run, data.N_BOSS, test_run.ART)
        rate = 0.16 * (0.85 ** run.upgrades[data.U_RATE])
        barrels = len(test_run.ent.SPREADS[min(run.upgrades[data.U_SPREAD], 3)])
        dps = (1 + run.upgrades[data.U_DMG]) * barrels / rate
        print("%-9s %10d %9.1f %10.1fs"
              % ("VOID" if sec > 4 else "sector %d" % (sec + 1),
                 c.boss.max_hp, dps, c.boss.max_hp / dps))

    print("\n=== fights (%d seeds per tier) ===" % len(seeds))
    print("%-7s %6s %8s %9s %8s %10s %8s" %
          ("tier", "won", "boss hp", "dmg taken", "no dmg", "boss secs",
           "minutes"))
    per_sector = {}
    for d, row in enumerate(data.DIFFICULTIES):
        # only the middle tier feeds the per-sector table: it is the intended
        # fight, and mixing tiers into one average says nothing about either
        r = run_set(seeds, d, per_sector if d == 1 else None)
        print("%-7s %2d/%-3d %7.0f%% %9.1f %7.0f%% %10.1f %8.1f" %
              (row[0], r["wins"], r["runs"], 100 * r["boss_entry"],
               r["boss_dmg"], r["untouched"], r["boss_time"], r["minutes"]))

    print("\n=== boss by sector, %s ===" % data.DIFFICULTIES[1][0])
    print("%-12s %7s %10s %10s %8s" %
          ("boss", "fights", "dmg taken", "secs", "no dmg"))
    for sec in sorted(per_sector):
        count, dmg, secs, clean = per_sector[sec]
        name = data.BOSS_NAME[sec % len(data.BOSS_NAME)]
        label = "S%d %s" % (sec + 1, name)
        print("%-12s %7d %10.1f %10.1f %7.0f%%" %
              (label[:12], count, dmg / count, secs / count,
               100.0 * clean / count))

    print("\nboss hp   = hull on entering the fight, as %% of the bar")
    print("dmg taken = hull lost in the boss fight")
    print("no dmg    = boss fights finished without a scratch")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
