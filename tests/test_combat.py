"""Drive real fights headless and measure what a frame costs."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness
from bot import Dodger

BUDGET = 240      # ~6000 kandinsky calls/s on Epsilon, 40 ms per frame


def run_fight(kind, sector, node, players=1, upgrades=None, max_frames=6000):
    g, kand, ion, clock = harness.load()
    g["keydown"] = Dodger(g).keydown
    S = g["S"]
    g["PON"][1] = 1 if players > 1 else 0
    g["PX"][0] = 90 if players > 1 else 153
    g["PX"][1] = 216
    for i in range(2):
        g["PC"][i] = 4
        g["PI"][i] = 0
    for i in range(8):
        g["UP"][i] = 0
    if upgrades:
        for u, lv in upgrades.items():
            g["UP"][g[u]] = lv
    S[g["HMAX"]] = 10 + (6 if players > 1 else 0)
    S[g["HULL"]] = S[g["HMAX"]]
    S[g["CRY"]] = 0
    S[g["SCORE"]] = 0
    S[g["SECT"]] = sector
    S[g["NODE"]] = node
    S[g["BMAX"]] = 2
    S[g["BOMB"]] = 2
    g["srnd"](4242)

    frames = [0]
    peak = [0]
    total = [0]
    real = g["hud"]

    def spy(tag):
        # hud() runs once per frame: use it as the frame boundary
        c = kand.stats.calls
        frames[0] += 1
        d = c - total[0]
        total[0] = c
        if frames[0] > 2 and d > peak[0]:
            peak[0] = d
        if frames[0] > max_frames:
            raise RuntimeError("fight did not terminate")
        real(tag)

    g["hud"] = spy
    kand.stats.reset()
    total[0] = 0
    won = g["fight"](kind)
    n = frames[0] or 1
    return {"won": won, "frames": n, "avg": kand.stats.calls / n,
            "peak": peak[0], "px": kand.stats.pixels / n}


def main():
    cases = [
        (0, 0, 1, 1, None, "sector 1, first patrol"),
        (0, 2, 4, 1, None, "sector 3, deep"),
        (1, 4, 5, 1, None, "sector 5, elite"),
        (5, 4, 6, 1, None, "sector 5, boss"),
        (0, 4, 5, 2, None, "sector 5, co-op"),
        (0, 4, 5, 1, {"USPR": 3, "URATE": 3, "UPRC": 1}, "sector 5, maxed guns"),
    ]
    rows = []
    ok = True
    for kind, sec, node, pl, ups, label in cases:
        r = run_fight(kind, sec, node, pl, ups)
        rows.append((label, r))
        if r["peak"] > BUDGET:
            ok = False

    print("%-28s %6s %7s %7s %9s %6s" %
          ("scenario", "frames", "avg", "peak", "px/frame", "result"))
    print("-" * 68)
    for label, r in rows:
        print("%-28s %6d %7.1f %7d %9.0f %6s" %
              (label, r["frames"], r["avg"], r["peak"], r["px"],
               "WON" if r["won"] else "LOST"))
    print()
    print("A frame at 25 fps is 40 ms; Epsilon manages roughly 6000 kandinsky")
    print("calls a second, so ~%d calls is the ceiling for one frame." % BUDGET)
    print("PASS" if ok else "FAIL: a scenario exceeded the call budget")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
