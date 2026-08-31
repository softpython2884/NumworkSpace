# NOVA - shared data, state and primitives.  MIT licence.
#
# `from novad import ...` copies values, not bindings, so a plain global mutated
# in one module would silently not change in another. All mutable state
# therefore lives in lists, shared by reference. Indexing a list is also faster
# than a global lookup in MicroPython, so this costs nothing at runtime.

from kandinsky import fill_rect, draw_string, set_pixel
from ion import keydown
import ion
import time

W = 320
H = 222
TOP = 18
BOT = 222
PY = 208
PW = 14
PH = 10

BLK = (0, 0, 0)
WHT = (255, 255, 255)
GRY = (128, 140, 160)
DRK = (38, 44, 58)
CYN = (60, 235, 255)
ORG = (255, 150, 30)
RED = (255, 70, 70)
GRN = (80, 255, 130)
YLW = (255, 225, 60)
VLT = (200, 120, 255)
SEC = (CYN, GRN, VLT, ORG, RED)
STC = ((96, 104, 134), (228, 234, 255))
ST = [0] * 24

# Controls, bound here so the game loop never pays for an `ion.` attribute
# lookup, and chosen so no reachable combination can ghost on the diode-less
# 9x6 keyboard matrix. KEY_BACK is never read: Epsilon may interrupt on it.
KL = ion.KEY_LEFT
KR = ion.KEY_RIGHT
KU = ion.KEY_UP
KD = ion.KEY_DOWN
K4 = ion.KEY_FOUR
K6 = ion.KEY_SIX
KO = ion.KEY_OK
KE = ion.KEY_EXE
KB = ion.KEY_BACKSPACE
MK = (KU, KD, KL, KR, KO, KE, KB)

# shared scalars
HULL = 0
HMAX = 1
CRY = 2
SCORE = 3
SECT = 4
BOMB = 5
BMAX = 6
NB = 7
NE = 8
NF = 9
NP = 10
RS = 11
NODE = 12
CLEAR = 13
S = [0] * 14
S[RS] = 1

URATE = 0
UDMG = 1
USPR = 2
USPD = 3
UPRC = 4
UBMB = 5
UHUL = 6
UGRD = 7
UP = [0] * 8

# name, upgrade, price, what it does -- shown under the highlighted line
SHOP = (
    ("RAPID FIRE", URATE, 30, "SHOOT 2 FRAMES SOONER"),
    ("HEAVY ROUNDS", UDMG, 34, "+1 DAMAGE PER SHOT"),
    ("SPREAD BARREL", USPR, 46, "+1 CANNON, WIDER ARC"),
    ("THRUSTERS", USPD, 24, "+1 PIXEL OF SPEED"),
    ("PIERCING AMMO", UPRC, 54, "SHOTS PASS THROUGH KILLS"),
    ("OVERDRIVE CELL", UBMB, 40, "+1 BOMB PER NODE"),
    ("HULL PLATING", UHUL, 44, "+2 MAX HULL, HEALS 2"),
    ("SCAVENGER", UGRD, 30, "+1 CRYSTAL PER KILL"),
)

# Enemy tables. One bytes object each: a six-int tuple is six pointers plus a
# header, a six-byte string is six bytes.
BOSS = 5
EW = b"\x0a\x0a\x0c\x08\x10\x30"   # hitbox width
EH = b"\x08\x08\x0a\x0a\x0c\x16"   # hitbox height
EHP = b"\x01\x01\x03\x01\x06\x01"  # base hit points
EPT = b"\x02\x03\x05\x04\x08\x64"  # score / 5
ESP = b"\x02\x02\x00\x05\x01\x00"  # fall speed (0 = handled specially)
EFR = b"\x6e\x00\x37\x00\x46\x22"  # frames between shots, 0 = never

# Three (dx, dy, w, h) rects per ship, packed twelve bytes each.
SPR = (b"\x00\x00\x0a\x03\x03\x03\x04\x03\x04\x06\x02\x02"
       b"\x00\x01\x03\x05\x07\x01\x03\x05\x03\x00\x04\x08"
       b"\x00\x00\x0c\x05\x02\x05\x08\x03\x04\x08\x04\x02"
       b"\x00\x00\x08\x03\x02\x03\x04\x04\x03\x07\x02\x03"
       b"\x00\x00\x10\x06\x02\x06\x0c\x04\x06\x0a\x04\x02"
       b"\x00\x00\x30\x0a\x06\x0a\x24\x08\x12\x12\x0c\x04")
PSPR = b"\x06\x00\x02\x03\x04\x03\x06\x03\x00\x06\x0e\x04"

# barrel offsets per spread level: (x offset, horizontal drift)
SPREAD = (((0, 0),), ((-5, 0), (5, 0)), ((-5, -1), (0, 0), (5, 1)),
          ((-6, -2), (-2, 0), (2, 0), (6, 2)))



def srnd(s):
    S[RS] = (s & 0xFFFF) or 1


def rnd(n):
    """16-bit xorshift. Everything stays under 2**16 so MicroPython never
    promotes to a big int, which would allocate. Period 65535, uniform."""
    x = S[RS]
    x ^= (x << 7) & 0xFFFF
    x ^= x >> 9
    x ^= (x << 8) & 0xFFFF
    S[RS] = x
    return x % n


def spr(pk, o, x, y, c):
    fr = fill_rect
    fr(x + pk[o], y + pk[o + 1], pk[o + 2], pk[o + 3], c)
    fr(x + pk[o + 4], y + pk[o + 5], pk[o + 6], pk[o + 7], c)
    fr(x + pk[o + 8], y + pk[o + 9], pk[o + 10], pk[o + 11], c)


def txt(s, x, y, c=WHT, b=BLK):
    draw_string(s, x, y, c, b)


def ctr(s, y, c=WHT, b=BLK):
    draw_string(s, (W - 10 * len(s)) >> 1, y, c, b)


def wipe():
    fill_rect(0, 0, W, H, BLK)


def panel(head, tc):
    wipe()
    fill_rect(0, 0, W, 3, tc)
    ctr(head, 8, tc)


def anykey():
    for k in MK:
        if keydown(k):
            return True
    return False


def mkey():
    """Menus block, which costs nothing once we sleep between polls. Waiting for
    a full release first stops a key held from the last screen leaking in."""
    while anykey():
        time.sleep(0.02)
    while True:
        for k in MK:
            if keydown(k):
                return k
        time.sleep(0.02)


# HUD fields remember what they last drew: draw_string repaints a 10x18 band per
# character and is by far the most expensive call in the game.
HS = [-1, -1, -1, ""]


def hud_reset():
    HS[0] = -1
    HS[1] = -1
    HS[2] = -1
    HS[3] = ""
    fill_rect(0, 0, W, TOP, BLK)
    fill_rect(0, TOP - 1, W, 1, DRK)


def hud(tag):
    """Each field redraws only when its value changed: draw_string repaints a
    10x18 band per character and is the most expensive call in the game."""
    h = S[HULL]
    if HS[0] != h:
        HS[0] = h
        m = S[HMAX]
        txt("%2d" % h, 2, 0, GRN if h * 3 > m * 2 else (YLW if h * 3 > m else RED))
    if HS[1] != S[BOMB]:
        HS[1] = S[BOMB]
        txt("*%d" % S[BOMB], 30, 0, ORG)
    if HS[2] != S[SCORE]:
        HS[2] = S[SCORE]
        txt("%06d %04d" % (S[SCORE], S[CRY]), 74, 0, WHT)
    if HS[3] != tag:
        HS[3] = tag
        txt(tag, 246, 0, GRY)
