"""How much frame budget the game actually uses.

60 fps means 16.7 ms a frame. This drives a deliberately heavy scene -- a late
boss with its widest pattern, plus a full particle pool -- and reports the cost
of update and draw separately.
"""

import os
import statistics
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import pygame

from bot import Bot
from nova import data, ui
from nova.art import Art
from nova.combat import Combat
from nova.run import Run

DT = 1 / 60.0
BUDGET_MS = 16.7


def measure(label, kind, sector, players=1, upgrades=None, seconds=25.0,
            hp_frac=None):
    pygame.init()
    pygame.display.set_mode((data.W, data.H))
    art = Art()
    art.load_fonts()
    run = Run(players, 2, seed=11)
    run.sector = sector
    run.node = 6
    for u in (upgrades or {}):
        run.upgrades[u] = upgrades[u]
    combat = Combat(run, kind, art)
    if hp_frac is not None and combat.boss is not None:
        # Drop it straight into the phase we actually want to measure. A boss
        # fight spends its first half in phase 0, so a timed sample of one
        # never sees the pattern that costs the most to run or to draw.
        combat.boss.hp = int(combat.boss.max_hp * hp_frac)
        combat.intro_t = 0.0
        for pod in combat.boss.pods:
            pod.hp = 0
    surf = pygame.Surface((data.W, data.H))
    bots = [Bot(combat, i) for i in range(players)]

    up_ms = []
    draw_ms = []
    peak_particles = 0
    peak_entities = 0
    t = 0.0
    while t < seconds and combat.result is None:
        inp = {"bomb": False}
        for b in bots:
            mv, bb = b.inputs()
            inp["move%d" % b.i] = mv
        t0 = time.perf_counter()
        combat.update(DT, inp)
        t1 = time.perf_counter()
        combat.draw(surf)
        ui.draw_hud(surf, art, run, combat.tag,
                    combat.boss if combat.is_boss else None)
        t2 = time.perf_counter()
        up_ms.append((t1 - t0) * 1000)
        draw_ms.append((t2 - t1) * 1000)
        peak_particles = max(peak_particles, combat.particles.n)
        peak_entities = max(peak_entities,
                            len(combat.enemies) + len(combat.shots)
                            + len(combat.bullets) + len(combat.pickups))
        t += DT

    total = [a + b for a, b in zip(up_ms, draw_ms)]
    return {"label": label, "frames": len(total),
            "avg": statistics.mean(total),
            "p99": sorted(total)[int(len(total) * 0.99)] if total else 0,
            "worst": max(total) if total else 0,
            "update": statistics.mean(up_ms), "draw": statistics.mean(draw_ms),
            "particles": peak_particles, "entities": peak_entities}


def main():
    maxed = {data.U_SPREAD: 3, data.U_RATE: 3, data.U_DMG: 3, data.U_PIERCE: 1}
    cases = [
        ("sector 1 patrol", data.N_FIGHT, 0, 1, None),
        ("sector 5 elite", data.N_ELITE, 4, 1, None),
        ("sector 5 boss", data.N_BOSS, 4, 1, None),
        ("co-op, maxed guns", data.N_FIGHT, 4, 2, maxed),
    ]
    rows = [measure(*c) for c in cases]
    # The worst case the game can actually produce: the last boss, in its final
    # phase, pods already broken so the core is running its spiral, with the
    # wall guns out and a co-op pair of maxed guns answering.
    rows.append(measure("WARDEN phase 3, co-op", data.N_BOSS, 4, 2, maxed,
                        seconds=30.0, hp_frac=0.2))
    print("%-22s %7s %7s %7s %8s %8s %6s %7s" %
          ("scene", "avg ms", "p99", "worst", "update", "draw", "parts",
           "shots"))
    print("-" * 80)
    ok = True
    for r in rows:
        print("%-22s %7.2f %7.2f %7.2f %8.2f %8.2f %6d %7d" %
              (r["label"], r["avg"], r["p99"], r["worst"], r["update"],
               r["draw"], r["particles"], r["entities"]))
        if r["p99"] > BUDGET_MS:
            ok = False
    print()
    print("60 fps budget is %.1f ms per frame." % BUDGET_MS)
    print("PASS" if ok else "FAIL: a scene exceeded the frame budget")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
