"""Render real game screens to PNG through the headless kandinsky stub.

Same code path as the calculator, so what comes out is what the device shows
(modulo the stub's blocky stand-in font).
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
import harness
from bot import Dodger

OUT = os.path.join(ROOT, "docs", "img")


def shot(name, kand):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".png")
    kand._save_png(path)
    print("  %-16s %s" % (name, os.path.relpath(path, ROOT)))


def prep(g, sector, node, players=1, upgrades=None, cry=0):
    S = g["S"]
    g["keydown"] = Dodger(g).keydown
    g["time"].sleep = lambda d: None
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
    S[g["HMAX"]] = 12 + (6 if players > 1 else 0)
    S[g["HULL"]] = S[g["HMAX"]] - 3
    S[g["CRY"]] = cry
    S[g["SCORE"]] = 1250
    S[g["SECT"]] = sector
    S[g["NODE"]] = node
    S[g["BMAX"]] = 2
    S[g["BOMB"]] = 2
    g["srnd"](4242)


def grab_fight(name, sector, node, players=1, upgrades=None, when=None):
    g, kand, ion, clock = harness.load()
    prep(g, sector, node, players, upgrades)
    frames = [0]
    real = g["hud"]
    S = g["S"]

    def spy(tag, frames=frames, real=real):
        frames[0] += 1
        real(tag)
        if frames[0] > 90 and (when is None or when(g, S)):
            shot(name, kand)
            raise SystemExit
        if frames[0] > 2000:
            raise SystemExit

    g["hud"] = spy
    try:
        g["fight"](5 if node > 6 else 0)
    except SystemExit:
        pass


def main():
    print("rendering screens:")

    # title
    g, kand, ion, clock = harness.load()
    g["time"].sleep = lambda d: None
    g["mkey"] = lambda: g["KO"]
    g["srnd"](7)
    real_menu = g["menu"]
    def once(items, cols, y0, foot):
        for j, it in enumerate(items):
            y = y0 + j * 21
            g["fill_rect"](16, y, 288, 19, g["GRY"] if j == 0 else g["BLK"])
            g["txt"](it, 22, y, g["BLK"] if j == 0 else cols[j],
                     g["GRY"] if j == 0 else g["BLK"])
        g["fill_rect"](0, 196, g["W"], 22, g["BLK"])
        g["ctr"](foot[0], 198, g["GRY"])
        shot("01-title", kand)
        raise SystemExit
    g["menu"] = once
    try:
        g["title"]()
    except SystemExit:
        pass

    # jump choice
    g, kand, ion, clock = harness.load()
    prep(g, 1, 3, cry=88)
    g["menu"] = once_menu = lambda items, cols, y0, foot: _menu_shot(
        g, kand, items, cols, y0, foot, "02-jump")
    try:
        g["choose"]()
    except SystemExit:
        pass

    # trader
    g, kand, ion, clock = harness.load()
    prep(g, 2, 4, cry=96, upgrades={"UDMG": 1})
    g["menu"] = lambda items, cols, y0, foot: _menu_shot(
        g, kand, items, cols, y0, foot, "03-trader")
    try:
        g["trade"](0)
    except SystemExit:
        pass

    # busy fight, and a boss
    grab_fight("04-fight", 2, 4, upgrades={"USPR": 2, "UDMG": 1},
               when=lambda g, S: S[g["NE"]] >= 4 and S[g["NB"]] >= 3)
    grab_fight("05-boss", 3, 7, upgrades={"USPR": 2, "UDMG": 2},
               when=lambda g, S: S[g["NB"]] >= 2)
    return 0


def _menu_shot(g, kand, items, cols, y0, foot, name):
    for j, it in enumerate(items):
        y = y0 + j * 21
        g["fill_rect"](16, y, 288, 19, g["GRY"] if j == 0 else g["BLK"])
        g["txt"](it, 22, y, g["BLK"] if j == 0 else cols[j],
                 g["GRY"] if j == 0 else g["BLK"])
    g["fill_rect"](0, 196, g["W"], 22, g["BLK"])
    g["ctr"](foot[0], 198, g["GRY"])
    shot(name, kand)
    raise SystemExit


if __name__ == "__main__":
    sys.exit(main())
