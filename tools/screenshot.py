"""Render real game screens to PNG through the headless kandinsky stub.

Same code path as the calculator, so what comes out is what the device shows
(modulo the stub's blocky stand-in font).
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
import harness
from test_balance import Dodger

OUT = os.path.join(ROOT, "docs", "img")


def shot(name, kand):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".png")
    kand._save_png(path)
    print("  %-18s %s" % (name, os.path.relpath(path, ROOT)))


def main():
    g, kand, ion, clock = harness.load()
    g["time"].sleep = lambda d: None

    # --- title -------------------------------------------------------------
    g["srnd"](7)
    g["wipe"]()
    for _ in range(40):
        g["set_pixel"](g["rnd"](320), 30 + g["rnd"](192), g["SCOL"][g["rnd"](3)])
    g["fill_rect"](0, 40, 320, 3, g["CYN"])
    g["centre"]("N O V A", 52, g["WHT"])
    g["fill_rect"](0, 74, 320, 3, g["CYN"])
    g["centre"]("A ROGUE-LITE FOR NUMWORKS", 80, g["GRY"])
    items = ["SOLO", "CO-OP  2 PLAYERS", "SEEDED RUN", "DIFFICULTY  PILOT", "CONTROLS"]
    cols = [g["CYN"], g["VLT"], g["YLW"], g["ORG"], g["GRY"]]
    for j, it in enumerate(items):
        y = 108 + j * 22
        g["fill_rect"](20, y, 280, 20, g["GRY"] if j == 0 else g["BLK"])
        g["text"](it, 28, y + 1, g["BLK"] if j == 0 else cols[j],
                  g["GRY"] if j == 0 else g["BLK"])
    shot("01-title", kand)

    # --- sector map --------------------------------------------------------
    g["newrun"](1, 4242)
    g["genmap"]()
    g["cry"] = 84
    g["hull"] = 8
    g["draw_map"](1)
    shot("02-map", kand)

    # --- mid-fight ---------------------------------------------------------
    g["keydown"] = Dodger(g).keydown
    g["newrun"](1, 4242)
    g["sector"] = 2
    g["up"][g["U_SPREAD"]] = 2
    g["up"][g["U_DMG"]] = 1
    g["cry"] = 120
    frames = [0]
    real = g["hud"]

    def spy(tag, frames=frames, real=real):
        frames[0] += 1
        real(tag)
        # wait for a frame that is actually busy, not a lull between waves
        if frames[0] > 120 and g["ne"] >= 4 and g["nb"] >= 3:
            shot("03-fight", kand)
            raise SystemExit
        if frames[0] > 1500:
            raise SystemExit
    g["hud"] = spy
    try:
        g["fight"](g["N_FIGHT"], 4)
    except SystemExit:
        pass

    # --- boss --------------------------------------------------------------
    g2, kand2, ion2, clock2 = harness.load()
    g2["time"].sleep = lambda d: None
    g2["keydown"] = Dodger(g2).keydown
    g2["newrun"](1, 101)
    g2["sector"] = 3
    g2["up"][g2["U_SPREAD"]] = 2
    g2["up"][g2["U_DMG"]] = 2
    f2 = [0]
    real2 = g2["hud"]

    def spy2(tag, f2=f2, real2=real2):
        f2[0] += 1
        real2(tag)
        if f2[0] == 140:
            shot("04-boss", kand2)
        if f2[0] > 140:
            raise SystemExit
    g2["hud"] = spy2
    try:
        g2["fight"](g2["N_BOSS"], 7)
    except SystemExit:
        pass

    # --- trader ------------------------------------------------------------
    g3, kand3, ion3, clock3 = harness.load()
    g3["time"].sleep = lambda d: None
    g3["newrun"](1, 9001)
    g3["cry"] = 96
    g3["up"][g3["U_DMG"]] = 1
    shots = [0]
    real3 = g3["menukey"]

    def once():
        shots[0] += 1
        if shots[0] == 1:
            shot("05-trader", kand3)
        raise SystemExit
    g3["menukey"] = once
    try:
        g3["shop"]()
    except SystemExit:
        pass
    return 0


if __name__ == "__main__":
    print("rendering screens:")
    sys.exit(main())
