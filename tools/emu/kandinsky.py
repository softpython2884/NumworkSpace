"""Headless re-implementation of the NumWorks `kandinsky` module.

Lets NOVA run on a PC (and in CI) without a calculator or a display. On top of
mirroring the real API it records what the game asks the screen to do, which is
the only honest way to reason about framerate on the device: on Epsilon the cost
of a frame is dominated by (a) the number of Python->C calls and (b) the number
of pixels those calls actually touch.

Reference API (NumWorks manual, MicroPython 1.17):
    color(r, g, b)
    set_pixel(x, y, color)
    get_pixel(x, y) -> (r, g, b)
    draw_string(text, x, y, [color], [background])
    fill_rect(x, y, width, height, color)
"""

WIDTH = 320
HEIGHT = 222

# Epsilon renders text with a 10x18 px large font in the Python console.
CHAR_W = 10
CHAR_H = 18

_BG_DEFAULT = (248, 252, 248)

# --- framebuffer -----------------------------------------------------------
# One RGB triplet per pixel, flat, so a whole-screen read stays cheap.
_fb = bytearray(WIDTH * HEIGHT * 3)


class Stats:
    """Draw-call accounting for the benchmark harness."""

    __slots__ = ("fill_rect", "set_pixel", "draw_string", "get_pixel", "pixels")

    def __init__(self):
        self.reset()

    def reset(self):
        self.fill_rect = 0
        self.set_pixel = 0
        self.draw_string = 0
        self.get_pixel = 0
        self.pixels = 0

    @property
    def calls(self):
        """Python->C calls, the fixed-cost part of a frame."""
        return self.fill_rect + self.set_pixel + self.draw_string + self.get_pixel

    def snapshot(self):
        return {
            "fill_rect": self.fill_rect,
            "set_pixel": self.set_pixel,
            "draw_string": self.draw_string,
            "get_pixel": self.get_pixel,
            "calls": self.calls,
            "pixels": self.pixels,
        }


stats = Stats()


def _norm(c):
    """Accept both `color()` results and raw (r, g, b) tuples, like Epsilon."""
    if isinstance(c, int):
        # Epsilon packs colors as RGB565 internally; a bare int is accepted.
        return (((c >> 11) & 0x1F) << 3, ((c >> 5) & 0x3F) << 2, (c & 0x1F) << 3)
    r, g, b = c
    return (int(r) & 0xFF, int(g) & 0xFF, int(b) & 0xFF)


def color(r, g, b):
    return (int(r) & 0xFF, int(g) & 0xFF, int(b) & 0xFF)


def fill_rect(x, y, w, h, c):
    stats.fill_rect += 1
    x, y, w, h = int(x), int(y), int(w), int(h)
    # Epsilon clips silently; mirror that so off-screen writes never raise.
    if w <= 0 or h <= 0:
        return
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(WIDTH, x + w), min(HEIGHT, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    r, g, b = _norm(c)
    row = bytes((r, g, b)) * (x1 - x0)
    span = (x1 - x0) * 3
    for yy in range(y0, y1):
        off = (yy * WIDTH + x0) * 3
        _fb[off:off + span] = row
    stats.pixels += (x1 - x0) * (y1 - y0)


def set_pixel(x, y, c):
    stats.set_pixel += 1
    x, y = int(x), int(y)
    if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
        return
    r, g, b = _norm(c)
    off = (y * WIDTH + x) * 3
    _fb[off] = r
    _fb[off + 1] = g
    _fb[off + 2] = b
    stats.pixels += 1


def get_pixel(x, y):
    stats.get_pixel += 1
    x, y = int(x), int(y)
    if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
        return (0, 0, 0)
    off = (y * WIDTH + x) * 3
    return (_fb[off], _fb[off + 1], _fb[off + 2])


def draw_string(text, x, y, c=(0, 0, 0), background=_BG_DEFAULT):
    """Blocky stand-in: we only need the footprint and the cost, not the glyphs."""
    stats.draw_string += 1
    text = str(text)
    x, y = int(x), int(y)
    w = CHAR_W * len(text)
    # Background band, as Epsilon does.
    _blit_band(x, y, w, CHAR_H, background)
    fg = _norm(c)
    for i, ch in enumerate(text):
        if ch == " ":
            continue
        _blit_band(x + i * CHAR_W + 1, y + 3, CHAR_W - 3, CHAR_H - 7, fg)
    stats.pixels += w * CHAR_H


def _blit_band(x, y, w, h, c):
    """Paint without touching the call counters (draw_string is one call)."""
    if w <= 0 or h <= 0:
        return
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(WIDTH, x + w), min(HEIGHT, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    r, g, b = _norm(c)
    row = bytes((r, g, b)) * (x1 - x0)
    span = (x1 - x0) * 3
    for yy in range(y0, y1):
        off = (yy * WIDTH + x0) * 3
        _fb[off:off + span] = row


# --- test / debug helpers (not part of the calculator API) ------------------

def _reset(fill=(0, 0, 0)):
    r, g, b = _norm(fill)
    _fb[:] = bytes((r, g, b)) * (WIDTH * HEIGHT)
    stats.reset()


def _framebuffer():
    return _fb


def _save_png(path):
    """Dump the framebuffer to a PNG using only the stdlib."""
    import struct
    import zlib

    raw = bytearray()
    for y in range(HEIGHT):
        raw.append(0)  # filter type 0
        off = y * WIDTH * 3
        raw += _fb[off:off + WIDTH * 3]

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)
    return path
