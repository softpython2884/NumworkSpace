"""Simulate whole runs to check the difficulty curve and how long a run lasts.

The pilot in bot.py has perfect information and perfect reflexes but a naive
strategy, so it should out-perform a person on a calculator keypad. A win rate
that looks fair for the bot is a real challenge for a human.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness
from bot import Dodger


def full_run(seed, players=1, buy=True, cap_sectors=5):
    g, kand, ion, clock = harness.load()
    g["keydown"] = Dodger(g).keydown
    g["mkey"] = lambda: g["KO"]
    g["time"].sleep = lambda d: None
    S = g["S"]
    # play() seeds from the clock, which the fake clock makes identical every
    # run; pin it to the test's seed instead.
    real_srnd = g["srnd"]
    g["srnd"] = lambda _v, s=seed, f=real_srnd: f(s)

    # Route policy: alternate pushing for loot and taking the safe option.
    picks = [0]

    def choose():
        n = S[g["NODE"]]
        if n >= 6:
            return 5
        picks[0] += 1
        opts = [0, 1, 2] if n & 1 else [0, 1, 3]
        # heal when hurt, otherwise shop, otherwise fight
        if 3 in opts and S[g["HULL"]] * 5 < S[g["HMAX"]] * 3:
            return 3
        if 2 in opts and S[g["CRY"]] >= 60:
            return 2
        return opts[1] if picks[0] % 3 == 0 else opts[0]
    g["choose"] = choose

    # Shop policy: buy the cheapest affordable upgrade, up to three times.
    def trade(free):
        ids = g["offers"]()
        if not ids:
            return
        if free:
            g["grant"](g["SHOP"][ids[0]][1])
            return
        if not buy:
            return
        for _ in range(3):
            ids = g["offers"]()
            best, bp = None, 10 ** 9
            for i in ids:
                p = g["cost"](i)
                if p <= S[g["CRY"]] and p < bp:
                    best, bp = i, p
            if best is None:
                return
            S[g["CRY"]] -= bp
            g["grant"](g["SHOP"][best][1])
    g["trade"] = trade

    log = []
    frames = [0]
    real_fight = g["fight"]

    def fight(kind):
        hb = S[g["HULL"]]
        n = [0]
        real = g["hud"]

        def spy(tag):
            n[0] += 1
            if n[0] > 8000:
                raise RuntimeError("fight did not terminate")
            real(tag)
        g["hud"] = spy
        won = real_fight(kind)
        g["hud"] = real
        frames[0] += n[0]
        log.append((S[g["SECT"]], S[g["NODE"]], kind, n[0], hb - S[g["HULL"]], won))
        return won
    g["fight"] = fight

    # play() loops forever in the Void; stop it at the campaign's end
    real_play = g["play"]

    def guard(tag, real=g["hud"]):
        return real(tag)

    won = [None]

    def runner():
        try:
            return real_play(players)
        except _Done:
            return True
    class _Done(Exception):
        pass

    # bound the number of sectors by watching the sector counter
    real_panel = g["panel"]

    def panel(head, tc):
        if S[g["SECT"]] >= cap_sectors:
            raise _Done
        return real_panel(head, tc)
    g["panel"] = panel

    try:
        result = real_play(players)
    except _Done:
        result = True
    return {"won": result, "sector": S[g["SECT"]], "score": S[g["SCORE"]],
            "hull": S[g["HULL"]], "hullmax": S[g["HMAX"]], "cry": S[g["CRY"]],
            "up": list(g["UP"]), "fights": len(log), "frames": frames[0],
            "minutes": frames[0] * 0.04 / 60, "log": log}


def main():
    seeds = (101, 777, 1234, 4242, 9001, 31415, 60007, 12)
    print("=== solo runs, dodging pilot, buying upgrades ===")
    print("%6s %9s %8s %7s %8s %8s" %
          ("seed", "reached", "score", "fights", "hull", "minutes"))
    reach = []
    mins = []
    for s in seeds:
        r = full_run(s)
        depth = r["sector"] + (1 if r["won"] else 0)
        reach.append(depth)
        mins.append(r["minutes"])
        print("%6d %9s %8d %7d %8s %8.1f" %
              (s, "WON" if r["won"] else "S%d" % (r["sector"] + 1), r["score"],
               r["fights"], "%d/%d" % (r["hull"], r["hullmax"]), r["minutes"]))

    print("\n=== no upgrades bought (floor of the curve) ===")
    for s in (101, 4242, 9001):
        r = full_run(s, buy=False)
        print("  seed %-6d %s after %d fights" %
              (s, "WON" if r["won"] else "died in S%d" % (r["sector"] + 1),
               r["fights"]))

    print("\n=== co-op, two dodging pilots ===")
    for s in (101, 4242):
        r = full_run(s, players=2)
        print("  seed %-6d %s  score %d  %.1f min" %
              (s, "WON" if r["won"] else "died in S%d" % (r["sector"] + 1),
               r["score"], r["minutes"]))

    print()
    print("average sector reached : %.1f / 5" % (sum(reach) / len(reach)))
    print("average combat time    : %.1f min per run" % (sum(mins) / len(mins)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
