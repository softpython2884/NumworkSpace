"""Menus, panels and the combat HUD."""

import math

import pygame

from . import data


def text(surf, art, msg, x, y, colour=data.WHITE, centre=False, right=False,
         big=False):
    font = art.font_big if big else art.font
    img = font.render(msg, False, colour)
    if centre:
        x -= img.get_width() // 2
    elif right:
        x -= img.get_width()
    surf.blit(img, (x, y))
    return img


def text_width(art, msg, big=False):
    """Width the same call to `text` would occupy, for centring a box round it."""
    font = art.font_big if big else art.font
    return font.size(msg)[0]


class Menu:
    """A vertical list with a cursor and a help line under the selection.

    The help line is the one thing the calculator version fought hardest to
    keep: a shop that does not say what it sells is a shop you buy from blind.
    """

    def __init__(self, items, hints=None, colours=None, enabled=None):
        assert items, "a menu with no items cannot be drawn or chosen from"
        self.items = items
        self.hints = hints or [""] * len(items)
        self.colours = colours or [data.WHITE] * len(items)
        self.enabled = enabled or [True] * len(items)
        self.index = 0

    def move(self, delta):
        self.index = (self.index + delta) % len(self.items)

    def key(self, event):
        """Returns the chosen index, or None."""
        if event.key in (pygame.K_UP, pygame.K_w, pygame.K_z):
            self.move(-1)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.move(1)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            return self.index
        return None

    def draw(self, surf, art, y0, t=0.0, width=300):
        x = (data.W - width) // 2
        for i, item in enumerate(self.items):
            y = y0 + i * 22
            sel = i == self.index
            colour = self.colours[i] if self.enabled[i] else data.DARK
            if sel:
                glow = 40 + int(math.sin(t * 6.0) * 12)
                pygame.draw.rect(surf, (glow, glow + 8, glow + 20),
                                 (x, y - 3, width, 20))
                pygame.draw.rect(surf, colour, (x, y - 3, width, 20), 1)
                pygame.draw.rect(surf, colour, (x + 4, y + 4, 3, 3))
            text(surf, art, item, x + 14, y, colour)
        if self.hints[self.index]:
            text(surf, art, self.hints[self.index], data.W // 2,
                 y0 + len(self.items) * 22 + 14, data.GREY, centre=True)


def panel(surf, art, title, colour, subtitle=None):
    surf.fill(data.VOID)
    pygame.draw.rect(surf, colour, (0, 0, data.W, 3))
    text(surf, art, title, data.W // 2, 18, colour, centre=True, big=True)
    if subtitle:
        text(surf, art, subtitle, data.W // 2, 54, data.GREY, centre=True)


def draw_hud(surf, art, run, tag, boss=None):
    pygame.draw.rect(surf, (0, 0, 0), (0, 0, data.W, data.HUD_H))
    pygame.draw.line(surf, data.DARK, (0, data.HUD_H - 1),
                     (data.W, data.HUD_H - 1))

    # hull as pips: reads faster than a number when you are being shot at
    for i in range(run.max_hull):
        full = i < run.hull
        colour = data.GREEN if run.hull > run.max_hull * 0.35 else data.RED
        pygame.draw.rect(surf, colour if full else data.DARK,
                         (8 + i * 6, 9, 4, 9), 0 if full else 1)

    bx = 8 + run.max_hull * 6 + 12
    for i in range(run.max_bombs):
        pygame.draw.rect(surf, data.ORANGE if i < run.bombs else data.DARK,
                         (bx + i * 9, 9, 7, 9), 0 if i < run.bombs else 1)

    text(surf, art, "%07d" % run.score, data.W // 2, 8, data.WHITE, centre=True)
    text(surf, art, "%d" % run.crystals, data.W - 96, 8, data.CYAN, right=True)
    pygame.draw.rect(surf, data.CYAN, (data.W - 92, 11, 4, 4))
    text(surf, art, tag, data.W - 10, 8, data.GREY, right=True)

    if boss is not None and boss.hp > 0:
        bar_w = min(300, data.PLAY_R - data.PLAY_L - 60)
        x0 = (data.W - bar_w) // 2
        y0 = data.HUD_H + 4
        w = int(bar_w * max(0.0, boss.hp / boss.max_hp))
        pygame.draw.rect(surf, data.DARK, (x0, y0, bar_w, 4))
        # blue while armoured: the bar should say why shots are bouncing
        pygame.draw.rect(surf, data.BLUE if boss.shielded else data.RED,
                         (x0, y0, w, 4))
        pods = getattr(boss, "pods", [])
        for i, pod in enumerate(pods):
            px = x0 + bar_w + 6 + i * 8
            pygame.draw.rect(surf, data.BLUE if pod.alive else data.DARK,
                             (px, y0 - 1, 6, 6), 0 if pod.alive else 1)
