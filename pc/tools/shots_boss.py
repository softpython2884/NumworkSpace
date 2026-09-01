"""One screenshot per boss, caught mid-mechanic."""

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

# what to wait for, so each shot shows the boss doing its thing
# `flash <= 0` everywhere: catching a boss mid hit-flash paints it solid white
# and the shot shows nothing about the fight.
WAIT = {
    0: lambda c: len(c.shots) >= 8 and c.boss.flash <= 0,
    1: lambda c: len(c.enemies) >= 3 and c.boss.flash <= 0 and c.flash.amount < 0.05,
    2: lambda c: c.boss.beams and c.boss.beams[0].firing and c.boss.flash <= 0,
    3: lambda c: (any(not p.alive for p in c.boss.pods) and len(c.shots) > 3
                  and c.boss.flash <= 0),
    4: lambda c: (c.boss.beams and len(c.shots) > 5 and c.boss.flash <= 0
                  and c.flash.amount < 0.05),
}


def main():
    pygame.init()
    pygame.display.set_mode((data.W, data.H))
    data.set_viewport(480, 270)
    art = Art()
    art.load_fonts()
    print("boss screenshots:")
    shots = []
    for i, name in enumerate(data.BOSS_NAME):
        run = Run(1, 1, seed=11)
        run.sector = i
        run.node = 7
        run.upgrades[data.U_DMG] = min(2, i)
        run.upgrades[data.U_SPREAD] = min(2, i)
        run.score = 4000 + i * 1500
        combat = Combat(run, data.N_BOSS, art)
        combat.intro_t = 0.0
        bot = Bot(combat, 0)
        t = 0.0
        want = WAIT[i]
        while t < 90.0:
            mv, _ = bot.inputs()
            combat.update(DT, {"move0": mv, "bomb": False})
            t += DT
            if combat.result is not None or combat.boss is None:
                break
            if t > 3.0 and want(combat):
                break
        canvas = pygame.Surface((data.W, data.H))
        combat.draw(canvas)
        ui.draw_hud(canvas, art, run, combat.tag, combat.boss)
        shots.append((name, canvas.copy()))
        print("  %-12s caught at %.1fs" % (name, t))

    # one sheet, two columns
    zoom = 1
    cw, ch = data.W * zoom, data.H * zoom
    pad = 18
    sheet = pygame.Surface((cw * 2 + pad * 3, (ch + pad + 14) * 3 + pad))
    sheet.fill(data.VOID)
    for i, (name, canvas) in enumerate(shots):
        col, row = i % 2, i // 2
        x = pad + col * (cw + pad)
        y = pad + row * (ch + pad + 14)
        sheet.blit(pygame.transform.scale(canvas, (cw, ch)), (x, y + 14))
        sheet.blit(art.font.render(name, False, data.RED), (x, y))
    path = os.path.join(OUT, "pc-bosses.png")
    pygame.image.save(sheet, path)
    print("wrote", os.path.relpath(path, os.path.dirname(PC)), sheet.get_size())
    return 0


if __name__ == "__main__":
    sys.exit(main())
