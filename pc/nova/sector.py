"""The branching sector map, back in full.

The calculator build drew this as a node graph, then as a route table, then had
to throw it away entirely for a three-line menu -- the parse tree would not fit
in 32 KB. Here it is again, with real diagonals this time.
"""

import math

from . import data

COLS = 8
ROWS = 3


class SectorMap:
    def __init__(self, rng, sector):
        self.rng = rng
        self.sector = sector
        self.nodes = {}          # (col, row) -> node kind
        self.links = {}          # (col, row) -> [(col+1, row2), ...]
        self.done = set()
        self.col = 0
        self.row = 1
        self.generate()

    def generate(self):
        """Grown forward from the entry node, so every node placed is reachable
        by construction -- no connectivity pass, no backtracking.

        Column 4 is always a trader and column 6 always a repair bay: whichever
        route the player takes, the pacing is the same. That rule came out of
        simulating runs on the calculator, where routes that missed both put the
        win rate at 12%.
        """
        self.nodes[(0, 1)] = data.N_FIGHT
        current = [1]
        for col in range(1, COLS - 1):
            nxt = []
            for row in current:
                for _ in range(1 + self.rng.randrange(2)):
                    r = max(0, min(ROWS - 1, row + self.rng.randrange(-1, 2)))
                    if r not in nxt:
                        nxt.append(r)
            for r in nxt:
                self.nodes[(col, r)] = self.pick_kind(col)
            current = nxt
        self.nodes[(COLS - 1, 1)] = data.N_BOSS

        for (col, row) in self.nodes:
            outs = []
            for r2 in range(ROWS):
                if abs(r2 - row) <= 1 and (col + 1, r2) in self.nodes:
                    outs.append((col + 1, r2))
            self.links[(col, row)] = outs

    def pick_kind(self, col):
        if col == 1:
            return data.N_FIGHT
        if col == 4:
            return data.N_SHOP
        if col == 6:
            return data.N_REST
        roll = self.rng.random()
        if roll < 0.42:
            return data.N_FIGHT
        if roll < 0.66:
            return data.N_ELITE
        return data.N_EVENT

    def options(self):
        return self.links.get((self.col, self.row), [])

    def advance(self, node):
        self.done.add((self.col, self.row))
        self.col, self.row = node
        return self.nodes[node]

    def finished(self):
        return self.col >= COLS - 1


# --- drawing -------------------------------------------------------------
X0, DX = 42, 54
Y0, DY = 92, 52


def node_pos(col, row):
    return X0 + col * DX, Y0 + row * DY


def draw_map(surf, art, smap, run, selected, t):
    import pygame

    surf.fill(data.VOID)
    accent = data.SECTOR_COLOURS[run.sector % 5]

    label = ("VOID %d" % (run.sector - 4)) if run.sector > 4 else \
            ("SECTOR %d" % (run.sector + 1))
    art_mod_text(surf, art, label, 14, 14, accent, big=True)
    art_mod_text(surf, art, "%d CRYSTALS" % run.crystals, data.W - 14, 20,
                 data.CYAN, right=True)
    art_mod_text(surf, art, "HULL %d/%d" % (run.hull, run.max_hull),
                 data.W - 14, 34,
                 data.GREEN if run.hull > run.max_hull * 0.35 else data.RED,
                 right=True)

    here = (smap.col, smap.row)
    reachable = set(smap.options())

    for (col, row), outs in smap.links.items():
        x, y = node_pos(col, row)
        for (c2, r2) in outs:
            x2, y2 = node_pos(c2, r2)
            live = (col, row) == here
            colour = data.WHITE if live else data.DARK
            pygame.draw.line(surf, colour, (x + 9, y), (x2 - 9, y2), 1)

    for (col, row), kind in sorted(smap.nodes.items()):
        x, y = node_pos(col, row)
        cleared = (col, row) in smap.done
        is_here = (col, row) == here
        is_pick = (col, row) == selected
        colour = data.NODE_COLOUR[kind]
        if cleared:
            pygame.draw.rect(surf, data.DARK, (x - 8, y - 8, 16, 16), 1)
        else:
            if is_pick:
                # a soft pulse so the choice is unmistakable
                r = 11 + int(math.sin(t * 7.0) * 1.6)
                pygame.draw.rect(surf, data.WHITE, (x - r, y - r, r * 2, r * 2), 1)
            pygame.draw.rect(surf, colour, (x - 8, y - 8, 16, 16),
                             0 if is_pick else 1)
            glyph = data.NODE_GLYPH[kind]
            art_mod_text(surf, art, glyph, x, y - 7,
                         data.VOID if is_pick else colour, centre=True)
        if is_here:
            pygame.draw.rect(surf, accent, (x - 3, y + 12, 6, 3))

    if selected in smap.nodes:
        kind = smap.nodes[selected]
        art_mod_text(surf, art, data.NODE_NAME[kind], data.W // 2, 224,
                     data.NODE_COLOUR[kind], centre=True, big=False)
        art_mod_text(surf, art, data.NODE_HINT[kind], data.W // 2, 240,
                     data.GREY, centre=True)
    art_mod_text(surf, art, "UP/DOWN  choose      ENTER  jump", data.W // 2, 256,
                 data.DARK, centre=True)


def art_mod_text(surf, art, msg, x, y, colour, centre=False, right=False,
                 big=False):
    font = art.font_big if big else art.font
    img = font.render(msg, False, colour)
    if centre:
        x -= img.get_width() // 2
    elif right:
        x -= img.get_width()
    surf.blit(img, (x, y))
