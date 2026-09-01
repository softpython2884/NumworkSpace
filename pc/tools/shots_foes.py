"""One screenshot per late-game enemy, caught doing the thing it exists to do.

A sprite sheet shows what they look like; it does not show that a lancer's beam
is a column you have to leave, or that sector 5 fields twice what sector 3 does.
"""

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

# label, sector index, the kind that has to be on screen
SCENES = (("SECTOR 3   a LANCER firing", 2, data.LANCER_ID),
          ("SECTOR 5   SPINNER rings", 4, data.SPINNER_ID),
          ("THE VOID   PHANTOMs, which dash", 6, data.PHANTOM_ID))


def capture(sector, want, seconds=80.0):
    art = Art()
    art.load_fonts()
    run = Run(1, 1, seed=11)
    run.sector = sector
    run.node = 5
    run.upgrades[data.U_SPREAD] = 2
    run.upgrades[data.U_DMG] = 1
    run.score = 4000 + sector * 600
    combat = Combat(run, data.N_FIGHT, art)
    bot = Bot(combat, 0)
    best = None
    for _ in range(int(seconds * 60)):
        mv, bomb = bot.inputs()
        combat.update(DT, {"move0": mv, "bomb": False})
        if combat.result is not None:
            break
        if not any(e.kind == want for e in combat.enemies):
            continue
        if combat.flash.amount >= 0.05:
            continue            # a hull hit washes the whole arena red
        firing = any(e.beam is not None and e.beam.firing
                     for e in combat.enemies)
        score = len(combat.enemies) + (70 if firing else 0)
        if best is None or score > best[0]:
            surf = pygame.Surface((data.W, data.H))
            combat.draw(surf)
            ui.draw_hud(surf, art, run, combat.tag)
            best = (score, surf.copy())
    return best


def main():
    pygame.init()
    pygame.display.set_mode((data.W, data.H))
    data.set_viewport(480, 270)
    art = Art()
    art.load_fonts()

    print("late-game enemies:")
    shots = []
    for label, sector, want in SCENES:
        got = capture(sector, want)
        if got is None:
            print("  %-34s NOT FOUND" % label)
            return 1
        shots.append((label, got[1]))
        print("  %-34s captured" % label)

    pad = 16
    sheet = pygame.Surface((data.W + pad * 2,
                            (data.H + pad + 14) * len(shots) + pad))
    sheet.fill(data.VOID)
    for i, (label, surf) in enumerate(shots):
        y = pad + i * (data.H + pad + 14)
        ui.text(sheet, art, label, pad, y - 12, data.CYAN)
        sheet.blit(surf, (pad, y))
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "pc-foes.png")
    pygame.image.save(sheet, path)
    print("wrote %s %s" % (os.path.relpath(path, os.path.dirname(PC)),
                           sheet.get_size()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
