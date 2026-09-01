"""Turn the text sprites into pygame surfaces, and draw the retro frame.

Everything renders onto a 480x270 surface which is then blown up by a whole
number to fill the window. That integer scale is what keeps the pixels square
and hard-edged; scaling by a fraction would smear them and lose the look.
"""

import pygame

from . import data


def build_sprite(art, palette, mirror=True):
    """One text sprite -> a per-pixel-alpha surface.

    The art holds the left half plus the centre column; with mirror=True the
    right half is reflected in, so a ship is symmetric by construction and
    there is half as much of it to draw by hand.
    """
    rows = art.split("\n")
    half = max(len(r) for r in rows)
    rows = [r.ljust(half, ".") for r in rows]
    if mirror:
        rows = [r + r[-2::-1] for r in rows]
    w = len(rows[0])
    h = len(rows)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            colour = palette.get(ch)
            if colour is not None:
                surf.set_at((x, y), colour)
    return surf


def shade(colour, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in colour)


def white_out(surface):
    """A solid-white copy, used to flash a ship on the frame it is hit."""
    flash = surface.copy()
    flash.fill(data.WHITE, special_flags=pygame.BLEND_RGB_MAX)
    return flash


class Art:
    """Every surface the game draws, built once at startup.

    Enemies are tinted per sector, so each of the five accents gets its own set
    of surfaces plus a white flash copy. That is 60 small surfaces -- nothing on
    a PC, and it means no per-frame tinting work.
    """

    def __init__(self):
        self.players = [
            build_sprite(data.PLAYER_1, data.P1_PAL),
            build_sprite(data.PLAYER_2, data.P2_PAL),
        ]
        self.player_flash = [white_out(s) for s in self.players]
        self.crystal = build_sprite(data.CRYSTAL, data.CRYSTAL_PAL)
        self.repair = build_sprite(data.REPAIR, data.REPAIR_PAL)

        self.enemies = []       # [sector][type]
        self.enemy_flash = []
        for accent in data.SECTOR_COLOURS:
            pal = {"a": accent, "d": shade(accent, 0.55), "w": data.WHITE}
            row = [build_sprite(art, pal) for art in data.ENEMY_ART]
            self.enemies.append(row)
            self.enemy_flash.append([white_out(s) for s in row])

        # Bosses always read as a threat, whatever the sector's accent is.
        boss_pal = {"a": data.RED, "d": data.RED_D, "w": data.WHITE}
        self.bosses = [build_sprite(art, boss_pal) for art in data.BOSS_ART]
        self.boss_flashes = [white_out(s) for s in self.bosses]
        self.pod = build_sprite(data.BOSS_POD, boss_pal)
        self.pod_flash = white_out(self.pod)
        self.pod_dead = build_sprite(
            data.BOSS_POD, {"a": data.DARK, "d": data.DARK, "w": data.DARK})
        # kept for the plain enemy table, which still lists a boss at index 5
        self.boss = self.bosses[0]
        self.boss_flash = self.boss_flashes[0]

        self.font = None
        self.font_big = None

    def load_fonts(self):
        """A bitmap-ish font. pygame's default is smooth, which fights the
        pixels, so we ask for the smallest crisp option available."""
        pygame.font.init()
        self.font = pygame.font.SysFont("dejavusansmono,couriernew,monospace", 11)
        self.font_big = pygame.font.SysFont("dejavusansmono,couriernew,monospace",
                                            26, bold=True)

    def boss_surface(self, index, flashing=False):
        i = index % len(self.bosses)
        return (self.boss_flashes if flashing else self.bosses)[i]

    def enemy_surface(self, sector, kind, flashing=False):
        if kind == data.BOSS_ID:
            return self.boss_flash if flashing else self.boss
        s = sector % len(data.SECTOR_COLOURS)
        return (self.enemy_flash if flashing else self.enemies)[s][kind]


def text(surface, art, msg, x, y, colour=data.WHITE, centre=False, big=False):
    font = art.font_big if big else art.font
    img = font.render(msg, False, colour)
    if centre:
        x -= img.get_width() // 2
    surface.blit(img, (x, y))
    return img.get_width()


def text_width(art, msg, big=False):
    font = art.font_big if big else art.font
    return font.size(msg)[0]
