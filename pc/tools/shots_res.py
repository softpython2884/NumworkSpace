"""Render the same scene at several display resolutions, to check the framing."""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
PC = os.path.dirname(HERE)
sys.path.insert(0, PC)
sys.path.insert(0, os.path.join(PC, "tests"))

import pygame

from bot import Bot
from nova import data, ui
from nova.art import Art
from nova.combat import Combat
from nova.run import Run

OUT = os.path.normpath(os.path.join(PC, "..", "docs", "img"))
DT = 1 / 60.0


def shoot(label, sw, sh, name):
    pygame.display.set_mode((sw, sh))
    scale = data.pick_scale(sw, sh)
    cw = max(data.MIN_CANVAS_W, sw // scale)
    ch = max(data.MIN_CANVAS_H, sh // scale)
    data.set_viewport(cw, ch)

    art = Art()
    art.load_fonts()
    run = Run(1, 1, seed=9)
    run.sector = 2
    run.node = 4
    run.upgrades[data.U_SPREAD] = 2
    run.upgrades[data.U_DMG] = 1
    run.crystals = 44
    run.score = 3185
    combat = Combat(run, data.N_FIGHT, art)
    bots = [Bot(combat, 0)]
    t = 0.0
    while t < 60.0:
        mv, _ = bots[0].inputs()
        combat.update(DT, {"move0": mv, "bomb": False})
        t += DT
        if combat.result is not None:
            break
        if t > 3.0 and len(combat.enemies) >= 4 and combat.particles.n > 20:
            break
    canvas = pygame.Surface((cw, ch))
    combat.draw(canvas)
    ui.draw_hud(canvas, art, run, combat.tag)

    # show it at 2x game pixels regardless of the real scale, so the shots are
    # comparable on the page
    out = pygame.transform.scale(canvas, (cw * 2, ch * 2))
    path = os.path.join(OUT, name + ".png")
    pygame.image.save(out, path)
    print("  %-22s %-11s canvas %dx%d  arena %dx%d" %
          (label, "%dx%d" % (sw, sh), cw, ch, data.PLAY_R - data.PLAY_L,
           data.BOT - data.TOP))


def main():
    pygame.init()
    print("rendering the same scene at several resolutions:")
    shoot("ultrawide 21:9", 3440, 1440, "pc-res-ultrawide")
    shoot("laptop 1366x768", 1366, 768, "pc-res-laptop")
    shoot("1080p 16:9", 1920, 1080, "pc-res-1080p")
    return 0


if __name__ == "__main__":
    sys.exit(main())
