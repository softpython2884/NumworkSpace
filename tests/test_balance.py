"""Simulate whole runs with a dodging pilot to check the difficulty curve.

A sweeping bot walks into everything and tells us nothing about balance. This
one scores the danger to its left and right and moves away from it, which is a
rough but honest stand-in for a human player.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness


class Dodger:
    def __init__(self, g):
        self.g = g
        self.want = [0, 0]
        self.tick = 0

    def _decide(self, pi):
        g = self.g
        me = g["plx"][pi] + 7
        left = right = 0
        # incoming enemy fire, weighted by how close it is
        for i in range(g["nf"]):
            dy = g["PY"] - g["fy"][i]
            if 0 < dy < 90:
                dx = g["fx"][i] - me
                w = 90 - dy
                if -26 < dx < 0:
                    left += w
                elif 0 <= dx < 26:
                    right += w
        for i in range(g["ne"]):
            dy = g["PY"] - g["ey"][i]
            if 0 < dy < 110:
                dx = g["ex"][i] - me
                w = 60 - (dy >> 1)
                # widen the no-go zone as it closes: lining up under a ship
                # about to land on you is not aiming, it is a collision
                near = 42 if dy < 64 else 30
                if -near < dx < 0:
                    left += w
                elif 0 <= dx < near:
                    right += w
        if left or right:
            if left > right:
                return 1
            if right > left:
                return -1
        # nothing dangerous: go collect the nearest pickup
        best = None
        for i in range(g["npk"]):
            d = g["px"][i] - me
            if best is None or abs(d) < abs(best):
                best = d
        if best is not None and abs(best) > 6:
            return 1 if best > 0 else -1
        # otherwise line up under a target and actually shoot it -- a human
        # does not spend a boss fight running away from it
        tgt = None
        for i in range(g["ne"]):
            d = g["ex"][i] + (g["EWD"][g["et"][i]] >> 1) - me
            if tgt is None or abs(d) < abs(tgt):
                tgt = d
        if tgt is not None and abs(tgt) > 4:
            return 1 if tgt > 0 else -1
        return 0

    def keydown(self, k):
        g = self.g
        self.tick += 1
        if self.tick % 2 == 1:
            self.want[0] = self._decide(0)
            if g["pon"][1]:
                self.want[1] = self._decide(1)
        if k == g["K_L"]:
            return self.want[0] < 0
        if k == g["K_R"]:
            return self.want[0] > 0
        if k == g["K_4"]:
            return self.want[1] < 0
        if k == g["K_6"]:
            return self.want[1] > 0
        if k == g["K_EXE"]:
            # fire the overdrive when the screen gets genuinely busy
            return g["nf"] + g["ne"] > 12 and self.tick % 7 == 0
        return False


def full_run(seed, players=1, buy=True, difficulty=1, verbose=False):
    """Play a whole run: real fights, scripted meta-screens."""
    g, kand, ion, clock = harness.load()
    g["diff"] = difficulty
    g["keydown"] = Dodger(g).keydown
    g["menukey"] = lambda: g["K_OK"]
    g["flash"] = lambda m, c: None
    g["time"].sleep = lambda d: None

    log = []

    # Shop policy: always buy the cheapest affordable upgrade, twice per visit.
    def shop():
        if not buy:
            return
        for _ in range(3):
            ids = g["offers"](3)
            best, bp = None, 10 ** 9
            for i in ids:
                p = g["price"](i)
                if p <= g["cry"] and p < bp:
                    best, bp = i, p
            if best is None:
                return
            g["cry"] -= bp
            g["grant"](g["SHOP"][best][1])
    g["shop"] = shop

    def reward(big):
        ids = g["offers"](3)
        if ids:
            g["grant"](g["SHOP"][ids[0]][1])
    g["reward"] = reward

    # Route choice: always take the first reachable node.
    def choose_node():
        for r in range(g["MROWS"]):
            if abs(r - g["mrow"]) <= 1 and g["mt"][(g["mcol"] + 1) * g["MROWS"] + r] >= 0:
                return r
        return -1
    g["choose_node"] = choose_node
    g["draw_map"] = lambda sel: None

    real_fight = g["fight"]
    frames = [0]

    def fight(kind, idx):
        hb = g["hull"]
        n0 = [0]
        real_hud = g["hud"]

        def spy(tag):
            n0[0] += 1
            if n0[0] > 8000:
                raise RuntimeError("fight did not terminate")
            real_hud(tag)
        g["hud"] = spy
        won = real_fight(kind, idx)
        g["hud"] = real_hud
        frames[0] += n0[0]
        log.append((g["sector"], idx, kind, n0[0], hb - g["hull"], won))
        return won
    g["fight"] = fight

    g["newrun"](players, seed)
    # Endless mode would never return: stop the run at the campaign's end.
    g["menu"] = lambda items, cols, y0: (1 if "ENTER THE VOID" in items else 0)
    won = g["play"]()
    return {
        "won": won,
        "sector": g["sector"],
        "score": g["score"],
        "hull": g["hull"],
        "hullmax": g["hullmax"],
        "cry": g["cry"],
        "up": list(g["up"]),
        "fights": len(log),
        "frames": frames[0],
        "minutes": frames[0] * 0.04 / 60,
        "log": log,
    }


def main():
    print("=== solo runs, dodging pilot, buying upgrades ===")
    print("%6s %8s %8s %8s %7s %9s" %
          ("seed", "reached", "score", "fights", "hull", "minutes"))
    reached = []
    mins = []
    for seed in (101, 777, 1234, 4242, 9001, 31415, 60007, 12):
        r = full_run(seed)
        reached.append(r["sector"] + (1 if r["won"] else 0))
        mins.append(r["minutes"])
        print("%6d %8s %8d %8d %7s %9.1f" %
              (seed, ("WON" if r["won"] else "S%d" % (r["sector"] + 1)),
               r["score"], r["fights"], "%d/%d" % (r["hull"], r["hullmax"]),
               r["minutes"]))

    print()
    print("=== no upgrades bought (floor of the difficulty curve) ===")
    for seed in (101, 4242, 9001):
        r = full_run(seed, buy=False)
        print("  seed %-6d reached %-4s after %d fights" %
              (seed, ("WON" if r["won"] else "S%d" % (r["sector"] + 1)), r["fights"]))

    print()
    print("=== co-op, two dodging pilots ===")
    for seed in (101, 4242):
        r = full_run(seed, players=2)
        print("  seed %-6d reached %-4s  score %d  %.1f min" %
              (seed, ("WON" if r["won"] else "S%d" % (r["sector"] + 1)),
               r["score"], r["minutes"]))

    print()
    print("=== difficulty curve (win rate over 10 seeds) ===")
    seeds = (101, 777, 1234, 4242, 9001, 31415, 60007, 12, 5150, 27182)
    for d, name in enumerate(("CADET", "PILOT", "ACE")):
        wins = 0
        depth = 0
        mm = 0.0
        for sd in seeds:
            r = full_run(sd, difficulty=d)
            wins += 1 if r["won"] else 0
            depth += r["sector"] + (1 if r["won"] else 0)
            mm += r["minutes"]
        print("  %-6s  win rate %3d%%   avg depth %.1f/5   avg %.1f min combat"
              % (name, wins * 10, depth / len(seeds), mm / len(seeds)))

    print()
    avg_reach = sum(reached) / len(reached)
    avg_min = sum(mins) / len(mins)
    print("average sector reached : %.1f / 5" % avg_reach)
    print("average run length     : %.1f min of combat" % avg_min)
    return 0


if __name__ == "__main__":
    sys.exit(main())
