"""Render each screen to PNG, so the game can actually be looked at."""

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

from bot import Bot
from nova import data, sector, ui
from nova.combat import Combat
from nova.game import Game
from nova.run import Run

OUT = os.path.normpath(os.path.join(PC, "..", "docs", "img"))
DT = 1 / 60.0


def save(name, canvas, zoom=2, crt=None):
    os.makedirs(OUT, exist_ok=True)
    big = pygame.transform.scale(canvas, (data.W * zoom, data.H * zoom))
    if crt is not None:
        big.blit(pygame.transform.scale(crt, big.get_size()), (0, 0))
    path = os.path.join(OUT, name + ".png")
    pygame.image.save(big, path)
    print("  %-18s %s" % (name, os.path.relpath(path, os.path.dirname(PC))))


def fly_until(combat, condition, players=1, limit=90.0):
    bots = [Bot(combat, i) for i in range(players)]
    t = 0.0
    while t < limit:
        inp = {"bomb": False}
        for b in bots:
            mv, bb = b.inputs()
            inp["move%d" % b.i] = mv
        combat.update(DT, inp)
        t += DT
        if combat.result is not None:
            return False
        if t > 2.0 and condition(combat):
            return True
    return False


def main():
    print("rendering PC screens:")
    g = Game(scale=1, crt=True)
    c = g.canvas

    # title
    g.enter_title()
    for _ in range(120):
        g.update(DT)
    g.draw_title(c)
    save("pc-01-title", c)

    # sector map
    g.start_run(1)
    g.run.crystals = 74
    g.run.hull = 9
    g.map.done.add((0, 1))
    g.map.col, g.map.row = 1, 1
    opts = g.map.options()
    sector.draw_map(c, g.art, g.map, g.run, opts[0] if opts else None, 1.2)
    save("pc-02-map", c)

    # a busy fight
    run = Run(1, 1, seed=9)
    run.sector = 2
    run.node = 4
    run.upgrades[data.U_SPREAD] = 2
    run.upgrades[data.U_DMG] = 1
    run.crystals = 40
    run.score = 3120
    combat = Combat(run, data.N_FIGHT, g.art)
    fly_until(combat, lambda c: len(c.enemies) >= 4 and c.particles.n > 30)
    combat.draw(c)
    ui.draw_hud(c, g.art, run, combat.tag)
    save("pc-03-fight", c)
    save("pc-03-fight-crt", c, crt=g.crt)

    # boss, mid-phase
    run = Run(1, 1, seed=4)
    run.sector = 3
    run.node = 7
    run.upgrades[data.U_SPREAD] = 2
    run.upgrades[data.U_DMG] = 2
    run.score = 8400
    combat = Combat(run, data.N_BOSS, g.art)
    # wait for a busy frame where the boss is not mid-flash, or the shot
    # catches it painted solid white
    fly_until(combat, lambda c: c.boss.hp < c.boss.max_hp * 0.55
              and len(c.shots) > 10 and c.boss.flash <= 0 and c.particles.n > 20)
    combat.draw(c)
    ui.draw_hud(c, g.art, run, combat.tag, combat.boss)
    save("pc-04-boss", c)

    # trader
    g.run = Run(1, 1, seed=3)
    g.run.crystals = 96
    g.run.upgrades[data.U_DMG] = 1
    g.enter_trader(free=False)
    g.draw_trader(c)
    save("pc-05-trader", c)

    # event
    g.enter_event()
    g.event = data.EVENTS[0]
    g.menu = ui.Menu([g.event[2][0], g.event[3][0]], ["", ""],
                     [data.VIOLET, data.VIOLET])
    g.draw_event(c)
    save("pc-06-event", c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
