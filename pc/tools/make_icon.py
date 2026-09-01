"""Draw the application icon and write it as .ico and .png.

No Pillow: pygame renders the frames and the ICO container is assembled by
hand. The format is a six-byte header, one sixteen-byte directory entry per
size, then the image payloads -- PNG payloads are legal in ICO since Vista and
every current tool reads them.
"""

import io
import os
import struct
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
PC = os.path.dirname(HERE)
sys.path.insert(0, PC)

import pygame

from nova import data

SIZES = (16, 24, 32, 48, 64, 128, 256)

# The icon is its own drawing, not the in-game sprite blown up: at 16 px the
# ship needs to be chunkier and the exhaust brighter than it is in play.
# Every row must be the SAME width: the last column is the mirror axis, and a
# short row leaves that axis transparent -- which drew a black seam straight
# down the middle of the ship.
SHIP = """
.......w
......ww
......wc
.....wcc
.....wcc
....wccc
....wccc
...wcccc
..wccccc
.wcccccc
wccccccc
wcc..ccc
wc...ccc
w....ccc
.....dcc
....o.cc
....oo.c
""".strip("\n")


def build_ship(scale):
    rows = SHIP.split("\n")
    half = max(len(r) for r in rows)
    assert all(len(r) == half for r in rows), (
        "every row must be the same width, or the mirror axis goes transparent")
    rows = [r.ljust(half, ".") for r in rows]
    rows = [r + r[-2::-1] for r in rows]
    w, h = len(rows[0]), len(rows)
    surf = pygame.Surface((w * scale, h * scale), pygame.SRCALPHA)
    pal = {"c": data.CYAN, "w": data.WHITE, "d": data.CYAN_D, "o": data.ORANGE}
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            col = pal.get(ch)
            if col:
                surf.fill(col, (x * scale, y * scale, scale, scale))
    return surf


def render(size):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    # rounded dark plate
    r = max(2, size // 8)
    pygame.draw.rect(surf, data.VOID, (0, 0, size, size), border_radius=r)
    pygame.draw.rect(surf, (34, 40, 56), (0, 0, size, size), max(1, size // 32),
                     border_radius=r)

    if size >= 32:
        step = max(2, size // 12)
        for i, (sx, sy) in enumerate(((0.18, 0.20), (0.78, 0.16), (0.30, 0.74),
                                      (0.86, 0.62), (0.62, 0.30))):
            c = data.GREY if i % 2 else (74, 84, 110)
            surf.fill(c, (int(sx * size), int(sy * size),
                          max(1, step // 2), max(1, step // 2)))

    ship = build_ship(1)
    sw, sh = ship.get_size()
    target_h = int(size * 0.74)
    scale = max(1, target_h // sh)
    ship = pygame.transform.scale(ship, (sw * scale, sh * scale))
    surf.blit(ship, ((size - ship.get_width()) // 2,
                     (size - ship.get_height()) // 2))
    return surf


def png_bytes(surface):
    buf = io.BytesIO()
    pygame.image.save(surface, buf, "icon.png")
    return buf.getvalue()


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    os.makedirs(os.path.join(PC, "assets"), exist_ok=True)

    payloads = []
    for size in SIZES:
        payloads.append((size, png_bytes(render(size))))

    header = struct.pack("<HHH", 0, 1, len(payloads))
    offset = len(header) + 16 * len(payloads)
    entries = b""
    blob = b""
    for size, data_bytes in payloads:
        dim = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32,
                               len(data_bytes), offset)
        blob += data_bytes
        offset += len(data_bytes)

    ico_path = os.path.join(PC, "assets", "nova.ico")
    with open(ico_path, "wb") as fh:
        fh.write(header + entries + blob)

    png_path = os.path.join(PC, "assets", "nova.png")
    pygame.image.save(render(256), png_path)

    print("wrote %s  (%d sizes, %d bytes)" %
          (os.path.relpath(ico_path, os.path.dirname(PC)), len(payloads),
           os.path.getsize(ico_path)))
    print("wrote %s  (256x256)" % os.path.relpath(png_path, os.path.dirname(PC)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
