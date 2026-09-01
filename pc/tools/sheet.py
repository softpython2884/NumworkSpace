"""Render every sprite onto one magnified sheet, so they can be eyeballed."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
pygame.display.set_mode((64, 64))

from nova.art import Art
from nova import data

art = Art()
art.load_fonts()

ZOOM = 6
items = [("player 1", art.players[0]), ("player 2", art.players[1]),
         ("crystal", art.crystal), ("repair", art.repair)]
names = ("grunt", "weaver", "turret", "rusher", "tank", "boss")
for i, n in enumerate(names):
    items.append((n, art.enemy_surface(2, i)))

pad = 14
cols = 5
cw = max(s.get_width() for _, s in items) * ZOOM + pad * 2
ch = max(s.get_height() for _, s in items) * ZOOM + pad * 2 + 16
rows = (len(items) + cols - 1) // cols
sheet = pygame.Surface((cw * cols, ch * rows))
sheet.fill(data.VOID)

for i, (name, surf) in enumerate(items):
    cx = (i % cols) * cw
    cy = (i // cols) * ch
    big = pygame.transform.scale(surf, (surf.get_width() * ZOOM,
                                        surf.get_height() * ZOOM))
    sheet.blit(big, (cx + (cw - big.get_width()) // 2, cy + pad + 14))
    img = art.font.render("%s %dx%d" % (name, surf.get_width(), surf.get_height()),
                          False, data.GREY)
    sheet.blit(img, (cx + 6, cy + 2))

out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "..", "docs", "img", "pc-sprites.png")
out = os.path.normpath(out)
os.makedirs(os.path.dirname(out), exist_ok=True)
pygame.image.save(sheet, out)
print("wrote", out, sheet.get_size())
