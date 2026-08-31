"""Drive real fights headless and measure what a frame costs."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness


class Bot:
    """A pilot that sweeps left and right, so ships, bullets and pickups all
    move and collide instead of sitting in a corner."""

    def __init__(self, g, ion, period=34):
        self.g = g
        self.ion = ion
        self.n = 0
        self.period = period

    def keydown(self, k):
        self.n += 1
        phase = (self.n // self.period) & 1
        if k == self.g["K_L"] or k == self.g["K_4"]:
            return phase == 0
        if k == self.g["K_R"] or k == self.g["K_6"]:
            return phase == 1
        return False


def run_fight(kind_name, sector, node, players=1, upgrades=None, max_frames=6000):
    g, kand, ion, clock = harness.load()
    g["keydown"] = Bot(g, ion).keydown
    g["newrun"](players, 4242)
    g["sector"] = sector
    if upgrades:
        for u, lv in upgrades.items():
            g["up"][g[u]] = lv

    frames = [0]
    peak = [0]
    total = [0]
    real_hud = g["hud"]

    def hud_spy(tag):
        # hud() runs exactly once per frame: use it as the frame boundary and
        # sample the draw-call cost of the frame that just finished.
        c = kand.stats.calls
        frames[0] += 1
        d = c - total[0]
        total[0] = c
        if frames[0] > 2 and d > peak[0]:
            peak[0] = d
        if frames[0] > max_frames:
            raise RuntimeError("fight did not terminate")
        real_hud(tag)

    g["hud"] = hud_spy
    kand.stats.reset()
    total[0] = 0
    won = g["fight"](g[kind_name], node)
    n = frames[0] or 1
    return {
        "won": won,
        "frames": n,
        "avg_calls": kand.stats.calls / n,
        "peak_calls": peak[0],
        "avg_px": kand.stats.pixels / n,
        "hull": g["hull"],
        "score": g["score"],
        "seconds": n * 0.04,
    }


def main():
    rows = []
    cases = [
        ("N_FIGHT", 0, 1, 1, None, "sector 1, first patrol"),
        ("N_FIGHT", 2, 4, 1, None, "sector 3, deep"),
        ("N_ELITE", 4, 6, 1, None, "sector 5, elite"),
        ("N_BOSS", 4, 7, 1, None, "sector 5, boss"),
        ("N_FIGHT", 4, 6, 2, None, "sector 5, co-op"),
        ("N_FIGHT", 4, 6, 1,
         {"U_SPREAD": 3, "U_RATE": 3, "U_BSPD": 3, "U_PIERCE": 1},
         "sector 5, maxed guns (worst case)"),
    ]
    ok = True
    for kind, sec, node, pl, ups, label in cases:
        r = run_fight(kind, sec, node, pl, ups)
        rows.append((label, r))
        if r["peak_calls"] > 220:
            ok = False

    print("%-36s %6s %7s %7s %8s %6s" %
          ("scenario", "frames", "avg", "peak", "px/frame", "result"))
    print("-" * 76)
    for label, r in rows:
        print("%-36s %6d %7.1f %7d %8.0f %6s" %
              (label, r["frames"], r["avg_calls"], r["peak_calls"],
               r["avg_px"], "WON" if r["won"] else "LOST"))
    print()
    print("Budget: a frame at 25 fps is 40 ms. Epsilon runs roughly 6000")
    print("kandinsky calls/s, so ~240 calls is the ceiling for a full frame.")
    print("PASS" if ok else "FAIL: a scenario exceeded the call budget")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
