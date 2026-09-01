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

# The icon is its own drawing, not the in-game sprite blown up.
#
# The first one was a soft blue arrow with grey speckles behind it, filling the
# plate corner to corner. Three things were wrong with that and all three only
# show up small: the silhouette had no single strong shape, nothing separated
# it from the plate, and at 16 px the speckles and the ship merged into one
# smudge. An icon is a shape you recognise at a glance in a taskbar, not a
# picture you look at.
#
# So: a long nose, wings that jut out and stop, a dark outline computed around
# the whole thing so it never merges with what is behind it, and a genuinely
# separate chunkier drawing for the small sizes rather than a downscale.
#
# The row that reads `wd..wc` is the important one and it looks like a typo.
# It is the notch that detaches the wingtips from the fuselage. Without it the
# widths run 1-3-5-7-9-11-9-7-5-3-1 and the eye reads a diamond, not a ship --
# two attempts at this icon both ended up as a kite with a flame under it
# before the gap went in.
#
# Every row must be the SAME width: the last column is the mirror axis, and a
# short row leaves that axis transparent -- which drew a black seam straight
# down the middle of the ship.
SHIP = """
.....w
....wc
....wc
....wc
...wcc
...wcc
..wccc
.wcccc
wccccc
wdcccc
wd..wc
....wc
....wc
....of
.....o
""".strip("\n")

# 16 and 24 px get their own drawing. A downscale of the one above loses the
# notch between wing and fuselage, which is the whole silhouette.
SHIP_SMALL = """
....w
...wc
...wc
..wcc
.wccc
wcccc
w..wc
...wc
...of
....o
""".strip("\n")

PALETTE = {"c": data.CYAN, "w": data.WHITE, "d": data.CYAN_D,
           "o": data.ORANGE, "f": data.YELLOW}
OUTLINE = (10, 14, 24)


def build_ship(art, scale=1):
    rows = art.split("\n")
    half = max(len(r) for r in rows)
    assert all(len(r) == half for r in rows), (
        "every row must be the same width, or the mirror axis goes transparent")
    rows = [r + r[-2::-1] for r in rows]
    w, h = len(rows[0]), len(rows)
    # one cell of margin all round, for the outline to live in
    surf = pygame.Surface(((w + 2) * scale, (h + 2) * scale), pygame.SRCALPHA)

    filled = {}
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            col = PALETTE.get(ch)
            if col:
                filled[(x + 1, y + 1)] = col

    # A dark rim around the whole silhouette. Computed rather than drawn by
    # hand: it is exact at every size, and it is the single thing that keeps
    # the ship readable against a dark plate at 16 px.
    for (x, y) in list(filled):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in filled:
                surf.fill(OUTLINE, (n[0] * scale, n[1] * scale, scale, scale))
    for (x, y), col in filled.items():
        surf.fill(col, (x * scale, y * scale, scale, scale))
    return surf


def glow(surf, size):
    """A soft halo behind the ship.

    An earlier version drew rays out to the plate edge. They did not read as a
    nova at all -- four lines through the middle of a square read as a
    crosshair, and they collided with the border. What is left is only enough
    to lift the ship off a flat plate.
    """
    cx = cy = size // 2
    for r, col in ((size * 0.40, (23, 28, 44)),
                   (size * 0.28, (30, 38, 58)),
                   (size * 0.16, (38, 49, 74))):
        pygame.draw.circle(surf, col, (cx, cy), int(r))


def render(size):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    r = max(2, size // 8)
    pygame.draw.rect(surf, data.VOID, (0, 0, size, size), border_radius=r)
    if size >= 32:
        glow(surf, size)
    if size >= 32:
        pygame.draw.rect(surf, (46, 56, 78), (0, 0, size, size),
                         max(1, size // 28), border_radius=r)

    art = SHIP if size >= 32 else SHIP_SMALL
    ship = build_ship(art)
    sw, sh = ship.get_size()
    # Whole-number scaling, and short of the plate edge: a pixel ship at a
    # fractional scale is a blurry ship, and one that touches the border reads
    # as cramped at every size.
    scale = max(1, int(size * 0.92) // sh)
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
