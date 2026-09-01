"""The branching sector map, back in full.

The calculator build drew this as a node graph, then as a route table, then had
to throw it away entirely for a three-line menu -- the parse tree would not fit
in 32 KB. Here it is again, with real diagonals this time.
"""

import math

from . import data

COLS = 8
ROWS = 3

# Which columns may carry a trader or a repair bay. Not column 1 (too early to
# have earned anything) and never COLS-2, the approach to the boss.
SPECIAL_COLS = (3, 4, 5)

# How often a sector offers a repair bay at all.
#
# It used to be every sector, on every route, in the column right before the
# boss. That is not a map, it is a corridor with decorations: you could play a
# whole sector badly and still meet the warlord at full hull, so nothing that
# happened on the way there mattered. Rare is the point -- a repair should be
# a detour you plan a column ahead and pay for by missing the trader.
REST_CHANCE = 0.55
SECOND_SHOP_CHANCE = 0.3


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

        Fights and events are rolled per node; the trader and the repair bay
        are then *placed*, on single nodes rather than whole columns. Placing
        them by column was what made every route the same route.
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
        self.place_specials()

        for (col, row) in self.nodes:
            outs = []
            for r2 in range(ROWS):
                if abs(r2 - row) <= 1 and (col + 1, r2) in self.nodes:
                    outs.append((col + 1, r2))
            self.links[(col, row)] = outs

    def pick_kind(self, col):
        if col == 1:
            return data.N_FIGHT
        if col == COLS - 2:
            # The approach. Whatever route you took, the last thing before the
            # warlord costs you something: this is the column that used to hand
            # out a free repair, and with it a boss fight that began at full
            # hull no matter how the sector had gone.
            return data.N_ELITE if self.rng.random() < 0.34 else data.N_FIGHT
        roll = self.rng.random()
        if roll < 0.50:
            return data.N_FIGHT
        if roll < 0.76:
            return data.N_ELITE
        return data.N_EVENT

    def place_specials(self):
        """One trader, and less than half the time a repair bay.

        Both go in the same column when it has the room, on different rows.
        That is the whole design: crystals or hull, not both, and the choice
        was really made a column earlier when you picked the row that could
        reach the one you wanted.
        """
        by_col = {}
        for (col, row) in self.nodes:
            if col in SPECIAL_COLS:
                by_col.setdefault(col, []).append(row)
        if not by_col:
            return

        wide = sorted(c for c in by_col if len(by_col[c]) >= 2)
        home = self.rng.choice(wide or sorted(by_col))
        rows = sorted(by_col[home])
        self.rng.shuffle(rows)
        self.nodes[(home, rows[0])] = data.N_SHOP

        if self.rng.random() < REST_CHANCE:
            if len(rows) >= 2:
                self.nodes[(home, rows[1])] = data.N_REST
            else:
                spare = sorted(c for c in by_col if c != home)
                if spare:
                    col = self.rng.choice(spare)
                    self.nodes[(col, self.rng.choice(sorted(by_col[col])))] = \
                        data.N_REST

        # A second trader now and then, so a run is never starved of upgrades
        # by bad luck alone.
        if self.rng.random() < SECOND_SHOP_CHANCE:
            spare = sorted((c, r) for c in by_col for r in by_col[c]
                           if self.nodes[(c, r)] not in (data.N_SHOP,
                                                         data.N_REST))
            if spare:
                self.nodes[self.rng.choice(spare)] = data.N_SHOP

    def options(self):
        return self.links.get((self.col, self.row), [])

    def advance(self, node):
        self.done.add((self.col, self.row))
        self.col, self.row = node
        return self.nodes[node]

    def finished(self):
        return self.col >= COLS - 1


# --- drawing -------------------------------------------------------------
DX, DY = 54, 52


def node_pos(col, row):
    """Centred on whatever canvas we were given, so the map sits in the middle
    of an ultrawide instead of hugging the left edge."""
    x0 = (data.W - (COLS - 1) * DX) // 2
    y0 = (data.H - (ROWS - 1) * DY) // 2 + 8
    return x0 + col * DX, y0 + row * DY


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

    foot = data.H - 46
    if selected in smap.nodes:
        kind = smap.nodes[selected]
        art_mod_text(surf, art, data.NODE_NAME[kind], data.W // 2, foot,
                     data.NODE_COLOUR[kind], centre=True)
        art_mod_text(surf, art, data.NODE_HINT[kind], data.W // 2, foot + 16,
                     data.GREY, centre=True)
    art_mod_text(surf, art, "UP/DOWN  choose      ENTER  jump", data.W // 2,
                 data.H - 14, data.DARK, centre=True)


def art_mod_text(surf, art, msg, x, y, colour, centre=False, right=False,
                 big=False):
    font = art.font_big if big else art.font
    img = font.render(msg, False, colour)
    if centre:
        x -= img.get_width() // 2
    elif right:
        x -= img.get_width()
    surf.blit(img, (x, y))
