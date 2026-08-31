# NOVA - a space rogue-lite for the NumWorks graphing calculator.
# MIT licensed. See LICENSE.
#
# This is the readable source. `python3 tools/build.py` strips it down into
# dist/nova.py, which is what you actually paste into the calculator.
#
# Design constraints this file is built around:
#   * 32 KB of MicroPython heap holds the bytecode AND every runtime object,
#     so: no classes, no dicts, no closures, no allocation inside the game loop.
#   * kandinsky has no blit and no back buffer, so we never clear the screen:
#     every moving thing erases itself at its old position and redraws at the
#     new one. A frame costs ~60 calls instead of 71040 pixels.
#   * ion.keydown is a matrix poll with no diodes, so the controls stay inside
#     combinations that cannot ghost (see docs/OPTIMIZATION.md).

from kandinsky import fill_rect, draw_string, set_pixel
from ion import keydown
import ion
import time

# ---------------------------------------------------------------------------
# Controls.
#
# Bound to module-level names so the game loop never pays for an `ion.` attribute
# lookup, and chosen so no legal combination can ghost on the diode-less 9x6
# keyboard matrix (proved in tests/test_controls.py):
#
#   P1  left / right          P2  4 / 6          overdrive  EXE (both players)
#
# In solo, OK is also accepted for overdrive: with a single player only two keys
# are ever down at once, and two keys can never ghost.
# KEY_BACK is deliberately unused -- Epsilon may interrupt the script on it.
# ---------------------------------------------------------------------------
K_L = ion.KEY_LEFT
K_R = ion.KEY_RIGHT
K_U = ion.KEY_UP
K_D = ion.KEY_DOWN
K_4 = ion.KEY_FOUR
K_6 = ion.KEY_SIX
K_OK = ion.KEY_OK
K_EXE = ion.KEY_EXE
K_DEL = ion.KEY_BACKSPACE

# ---------------------------------------------------------------------------
# Screen
# ---------------------------------------------------------------------------
W = 320
H = 222
HUD_H = 18          # one text line: Epsilon's font is 10x18
TOP = HUD_H          # first playable row
BOT = H              # exclusive
PY = BOT - 14        # ships fly on this fixed row

# ---------------------------------------------------------------------------
# Palette. Tuples, not kandinsky.color() objects: same result, one less call
# and one less object on the heap.
# ---------------------------------------------------------------------------
BLK = (0, 0, 0)
WHT = (255, 255, 255)
GRY = (110, 120, 140)
DRK = (40, 46, 60)
CYN = (0, 230, 255)
ORG = (255, 150, 0)
RED = (255, 60, 60)
GRN = (60, 255, 120)
YLW = (255, 235, 60)
VLT = (190, 100, 255)
BLU = (80, 140, 255)

# Sector accent colours, one per sector, used for enemies and map chrome.
SECC = (CYN, GRN, VLT, ORG, RED)

# ---------------------------------------------------------------------------
# Deterministic RNG: 16-bit xorshift.
#
# Every value stays under 2**16, so MicroPython never promotes to big ints
# (which would allocate). Same seed -> same sector -> same waves, which is what
# makes seeded runs shareable.
# ---------------------------------------------------------------------------
rs = 1

def srnd(s):
    global rs
    rs = (s & 0xFFFF) or 1

def rnd(n):
    global rs
    x = rs
    x ^= (x << 7) & 0xFFFF
    x ^= x >> 9
    x ^= (x << 8) & 0xFFFF
    rs = x
    return x % n

# ---------------------------------------------------------------------------
# Entity pools.
#
# Parallel lists of ints, not objects: `ex[i]` is one index operation, whereas
# a class attribute is a dict lookup and an object header we cannot afford.
#
# Pools are *compacted*: live entities occupy slots 0..n-1, so loops run over
# range(n) with no "is it alive?" test. Killing entity i swaps the last live
# entity into slot i and decrements n. Nothing is ever allocated or freed
# during a fight, so the garbage collector never runs mid-frame.
# ---------------------------------------------------------------------------
NB = 12          # player bullets
NE = 12          # enemies
NF = 16          # enemy bullets
NP = 6           # pickups
NS = 14          # background stars

# player bullets: x, y, dx (for spread shots), damage
bx = [0] * NB; by = [0] * NB; bd = [0] * NB; bg = [0] * NB
nb = 0

# enemies: x, y, type, hp, param (drift/anchor), fire cooldown
ex = [0] * NE; ey = [0] * NE; et = [0] * NE
eh = [0] * NE; ep = [0] * NE; ec = [0] * NE
ne = 0

# enemy bullets: x, y, dx, dy
fx = [0] * NF; fy = [0] * NF; fu = [0] * NF; fv = [0] * NF
nf = 0

# pickups: x, y, kind (0 = crystal, 1 = repair)
px = [0] * NP; py = [0] * NP; pk = [0] * NP
npk = 0

# stars: x, y, layer (0 = far/slow .. 2 = near/fast)
sx = [0] * NS; sy = [0] * NS; sl = [0] * NS

# ---------------------------------------------------------------------------
# Enemy archetypes.
#
# Sprites are tuples of (dx, dy, w, h) rectangles. Two rects each: enough to
# read as a ship, cheap enough to draw twelve of them per frame.
# ---------------------------------------------------------------------------
T_GRUNT = 0
T_WEAVE = 1
T_TURRET = 2
T_RUSH = 3
T_TANK = 4
T_BOSS = 5

ESPR = (
    ((0, 2, 10, 4), (3, 0, 4, 8)),        # grunt   - blunt wedge
    ((0, 0, 10, 3), (3, 3, 4, 5)),        # weaver  - T shape
    ((0, 0, 12, 6), (4, 6, 4, 4)),        # turret  - heavy head
    ((2, 0, 4, 10), (0, 6, 8, 4)),        # rusher  - dart
    ((0, 0, 16, 8), (2, 8, 12, 4)),       # tank    - slab
    ((0, 0, 48, 14), (8, 14, 32, 8)),     # boss    - block
)
EWD = (10, 10, 12, 8, 16, 48)             # hitbox width per type
EHT = (8, 8, 10, 10, 12, 22)              # hitbox height per type
EHP = (1, 1, 3, 1, 6, 60)                 # base hit points
EPTS = (10, 15, 25, 20, 40, 500)          # score value

# ---------------------------------------------------------------------------
# Upgrades. Everything the ship can become is 12 small integers, so a build is
# cheap to hold, cheap to apply, and cheap to encode into a resume code.
# ---------------------------------------------------------------------------
U_RATE = 0       # -2 frames of fire cooldown per level
U_DMG = 1        # +1 bullet damage per level
U_SPREAD = 2     # +1 barrel per level (1 -> 2 -> 3 -> 4)
U_SPD = 3        # +1 px/frame of ship speed
U_BSPD = 4       # +2 px/frame of bullet speed
U_PIERCE = 5     # bullets survive a kill
U_SHIELD = 6     # absorbs a hit, recharges over time
U_MAG = 7        # pickups drift toward the ship
U_BOMB = 8       # +1 max overdrive charge
U_HULL = 9       # +1 max hull
U_GREED = 10     # +50% crystals per level
U_REGEN = 11     # +1 hull repaired at each map node

UMAX = 12
up = [0] * UMAX

# name, upgrade index, price. Kept short: every character is a byte of storage.
SHOP = (
    ("RAPID FIRE", U_RATE, 30),
    ("HEAVY ROUNDS", U_DMG, 35),
    ("SPREAD BARREL", U_SPREAD, 45),
    ("THRUSTERS", U_SPD, 25),
    ("RAILGUN", U_BSPD, 25),
    ("PIERCING AMMO", U_PIERCE, 55),
    ("DEFLECTOR", U_SHIELD, 50),
    ("TRACTOR BEAM", U_MAG, 20),
    ("OVERDRIVE CELL", U_BOMB, 40),
    ("HULL PLATING", U_HULL, 45),
    ("SCAVENGER", U_GREED, 30),
    ("NANOREPAIR", U_REGEN, 40),
)

# ---------------------------------------------------------------------------
# Ship state. Index 0 is player 1, index 1 is player 2 (co-op only).
# Hull and crystals are shared: co-op should feel like one crew, not a race.
# ---------------------------------------------------------------------------
plx = [40, 240]
ppx = [40, 240]      # position drawn last frame, so we erase exactly that
pon = [1, 0]         # is this ship in play
pcd = [0, 0]         # frames until the next shot
psh = [0, 0]         # deflector charge (0 = down, 1 = up)
pst = [0, 0]         # deflector recharge timer
piv = [0, 0]         # invulnerability frames after a hit

PW = 14              # ship hitbox
PH = 10
PSPR = ((5, 0, 4, 4), (0, 4, 14, 4), (2, 8, 10, 2))

# ---------------------------------------------------------------------------
# Run state
#
# Difficulty is three numbers, not three code paths: starting hull, a percentage
# applied to each fight's threat budget, and how much faster enemies shoot.
# ---------------------------------------------------------------------------
DHULL = (14, 10, 7)
DBUD = (68, 112, 160)
DFIRE = (0, 4, 9)
DNAME = ("CADET", "PILOT", "ACE")
diff = 1

hull = 10
hullmax = 10
cry = 0
score = 0
sector = 0
bombs = 2
bombmax = 2
players = 1
seed0 = 0
cleared = 0

# ---------------------------------------------------------------------------
# Sector map: a 3-row by 8-column grid. Column 0 is the entry, column 7 is the
# boss. -1 marks an empty cell. Flat list of 24 ints: the whole map costs less
# than one Python object would.
# ---------------------------------------------------------------------------
MCOLS = 8
MROWS = 3
N_FIGHT = 0
N_ELITE = 1
N_SHOP = 2
N_EVENT = 3
N_REST = 4
N_BOSS = 5

mt = [-1] * (MCOLS * MROWS)
mdone = [0] * (MCOLS * MROWS)
mcol = 0
mrow = 1

# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------

def clr(x, y, w, h):
    fill_rect(x, y, w, h, BLK)


def sprite(spr, x, y, c):
    """Draw a tuple of (dx, dy, w, h) rects. Local binding of fill_rect is not
    a micro-optimisation here: it is called up to 30 times per frame."""
    fr = fill_rect
    for r in spr:
        fr(x + r[0], y + r[1], r[2], r[3], c)


def text(s, x, y, c=WHT, b=BLK):
    draw_string(s, x, y, c, b)


def centre(s, y, c=WHT, b=BLK):
    draw_string(s, (W - 10 * len(s)) >> 1, y, c, b)


def wipe():
    """Full-screen clear. Only ever used between screens, never in a frame."""
    fill_rect(0, 0, W, H, BLK)


def bar(x, y, w, h, cur, mx, c):
    """Filled gauge. Two rects, whatever the value."""
    if mx <= 0:
        return
    f = (w * cur) // mx
    if f < 0:
        f = 0
    elif f > w:
        f = w
    fill_rect(x, y, f, h, c)
    fill_rect(x + f, y, w - f, h, DRK)

# ---------------------------------------------------------------------------
# HUD. Redrawn per field, and only when that field changed: draw_string repaints
# a 10x18 background band per character, which is the single most expensive
# call in the whole game.
# ---------------------------------------------------------------------------
h_hull = -1
h_score = -1
h_cry = -1
h_bomb = -1
h_tag = ""


def hud_reset():
    global h_hull, h_score, h_cry, h_bomb, h_tag
    h_hull = -1; h_score = -1; h_cry = -1; h_bomb = -1; h_tag = ""
    fill_rect(0, 0, W, HUD_H, BLK)
    fill_rect(0, HUD_H - 1, W, 1, DRK)


def hud(tag):
    global h_hull, h_score, h_cry, h_bomb, h_tag
    if h_hull != hull:
        h_hull = hull
        c = GRN if hull * 3 > hullmax * 2 else (YLW if hull * 3 > hullmax else RED)
        bar(2, 4, 56, 10, hull, hullmax, c)
    if h_bomb != bombs:
        h_bomb = bombs
        for i in range(4):
            fill_rect(63 + i * 9, 5, 7, 8, ORG if i < bombs else DRK)
    if h_score != score:
        h_score = score
        text("%06d" % score, 104, 0, WHT)
    if h_cry != cry:
        h_cry = cry
        text("%04d" % cry, 178, 0, CYN)
    if h_tag != tag:
        h_tag = tag
        text(tag, 246, 0, GRY)


# ---------------------------------------------------------------------------
# Parallax starfield.
#
# Three layers moving at 1 px every 1, 2 and 3 frames. Stars that do not move
# this frame cost nothing at all, which is why the field is grouped by layer
# instead of accumulating a per-star sub-pixel position.
# ---------------------------------------------------------------------------
SCOL = ((55, 60, 80), (120, 130, 160), (225, 230, 255))


def stars_init():
    for i in range(NS):
        sx[i] = rnd(W)
        sy[i] = TOP + rnd(BOT - TOP)
        sl[i] = i % 3


def stars_draw():
    sp = set_pixel
    for i in range(NS):
        sp(sx[i], sy[i], SCOL[sl[i]])


def stars_step(frame):
    sp = set_pixel
    for i in range(NS):
        l = sl[i]
        # layer 2 every frame, layer 1 every 2nd, layer 0 every 3rd
        if l == 2 or (l == 1 and not frame & 1) or (l == 0 and not frame % 3):
            y = sy[i]
            sp(sx[i], y, BLK)
            y += 1
            if y >= BOT:
                y = TOP
                sx[i] = rnd(W)
            sy[i] = y
            sp(sx[i], y, SCOL[l])

# ---------------------------------------------------------------------------
# Explosions: a white flash that lives for a couple of frames. Cheap punch.
# ---------------------------------------------------------------------------
NX = 5
xx = [0] * NX; xy = [0] * NX; xt = [0] * NX
nx = 0


def boom(x, y, s):
    global nx
    if nx < NX:
        xx[nx] = x; xy[nx] = y; xt[nx] = s
        nx += 1


# ---------------------------------------------------------------------------
# Pool operations.
#
# All removals are swap-with-last. All update loops walk *backwards*, so the
# entity swapped into slot i always comes from a slot we already handled this
# frame: no entity is skipped and none is updated twice.
# ---------------------------------------------------------------------------

def kill_b(i):
    global nb
    nb -= 1
    if i != nb:
        bx[i] = bx[nb]; by[i] = by[nb]; bd[i] = bd[nb]; bg[i] = bg[nb]


def kill_e(i):
    global ne
    ne -= 1
    if i != ne:
        ex[i] = ex[ne]; ey[i] = ey[ne]; et[i] = et[ne]
        eh[i] = eh[ne]; ep[i] = ep[ne]; ec[i] = ec[ne]


def kill_f(i):
    global nf
    nf -= 1
    if i != nf:
        fx[i] = fx[nf]; fy[i] = fy[nf]; fu[i] = fu[nf]; fv[i] = fv[nf]


def kill_p(i):
    global npk
    npk -= 1
    if i != npk:
        px[i] = px[npk]; py[i] = py[npk]; pk[i] = pk[npk]


def spawn_e(t, x, y, p, hp):
    global ne
    if ne < NE:
        ex[ne] = x; ey[ne] = y; et[ne] = t
        eh[ne] = hp; ep[ne] = p; ec[ne] = 20 + rnd(40)
        ne += 1


def spawn_f(x, y, u, v):
    global nf
    if nf < NF:
        fx[nf] = x; fy[nf] = y; fu[nf] = u; fv[nf] = v
        nf += 1


def spawn_p(x, y, k):
    global npk
    if npk < NP:
        px[npk] = x; py[npk] = y; pk[npk] = k
        npk += 1


# Barrel offsets per spread level: (x offset, horizontal drift per frame).
SPREAD = (
    ((0, 0),),
    ((-5, 0), (5, 0)),
    ((-5, -1), (0, 0), (5, 1)),
    ((-6, -2), (-2, 0), (2, 0), (6, 2)),
)


def shoot(pi):
    """Auto-fire. The player never presses a fire button, which keeps the
    control scheme at two keys per player and out of ghosting range."""
    global nb
    dmg = 1 + up[U_DMG]
    pierce = up[U_PIERCE]
    for o in SPREAD[up[U_SPREAD] if up[U_SPREAD] < 4 else 3]:
        if nb >= NB:
            return
        bx[nb] = plx[pi] + 6 + o[0]
        by[nb] = PY - 6
        bd[nb] = o[1]
        bg[nb] = dmg + (100 if pierce else 0)   # flag packed into the damage
        nb += 1

# ---------------------------------------------------------------------------
# Combat.
#
# One frame, in order:
#   1. poll keys
#   2. step the starfield (drawn under everything, repairs itself as it scrolls)
#   3. ERASE every moving entity at its current position, then update it
#   4. DRAW every surviving entity at its new position
#   5. refresh only the HUD fields that changed
#   6. sleep off the remainder of the frame budget
#
# Erase-all-then-draw-all is what keeps the picture clean: an entity is never
# drawn before another entity has had the chance to erase itself over it.
# ---------------------------------------------------------------------------
FRAME = 0.04                     # 25 fps ceiling; slower hardware just drops below it
ESPD = (2, 2, 2, 5, 1, 0)        # vertical speed per enemy type
FIRE = (110, 0, 55, 0, 70, 34)   # base frames between shots (0 = never fires)


def fight(kind, idx):
    """Run one combat node. Returns True if the player cleared it."""
    global nb, ne, nf, npk, nx, hull, cry, score, bombs

    nb = ne = nf = npk = nx = 0
    wipe()
    hud_reset()
    stars_init()
    stars_draw()

    acc = SECC[sector % 5]
    boss = kind == N_BOSS
    elite = kind == N_ELITE

    # Threat budget, spent on enemies as the fight goes on. Difficulty scales
    # with sector and depth into the sector rather than with raw enemy speed,
    # which keeps every wave readable.
    budget = ((14 + sector * 9 + idx * 3) * DBUD[diff]) // 100
    # Cap it. Deep in the Void an uncapped budget makes waves *longer*, not
    # harder -- a three-minute fight is exhausting, not exciting. Past this
    # point difficulty rides on enemy hit points and rate of fire instead.
    if budget > 84:
        budget = 84
    if elite:
        budget = (budget * 7) // 5
    bhp = 0
    if boss:
        budget = 0
        # Scale the boss to the guns the player actually brought. A flat pool
        # means eight seconds with a maxed build and two minutes without one;
        # this keeps every boss around twenty seconds of sustained fire.
        rate0 = 9 - (up[U_RATE] << 1)
        if rate0 < 3:
            rate0 = 3
        dps = (1 + up[U_DMG]) * len(SPREAD[up[U_SPREAD] if up[U_SPREAD] < 4 else 3]) * 25 // rate0
        bhp = 30 + sector * 4 + dps * 7
        spawn_e(T_BOSS, 136, TOP + 4, 1, bhp)

    COST = (1, 2, 3, 2, 5)
    # Enemy types unlocked as sectors go by: sector 0 sees grunts and weavers.
    pool_n = 2 + sector
    if pool_n > 5:
        pool_n = 5

    tag = "BOSS" if boss else ("S%d-%d" % (sector + 1, idx + 1))
    stimer = 30
    frame = 0
    rate_boost = DFIRE[diff] + sector * 3   # later sectors shoot faster
    tnext = time.monotonic()
    # Start "held" so a key still down from the previous screen cannot fire.
    ovr_prev = True

    while True:
        frame += 1

        # ---- 1. input ------------------------------------------------------
        kd = keydown
        spd = 5 + up[U_SPD]
        if kd(K_L):
            v = plx[0] - spd
            plx[0] = v if v > 0 else 0
        if kd(K_R):
            v = plx[0] + spd
            plx[0] = v if v < W - PW else W - PW
        if pon[1]:
            if kd(K_4):
                v = plx[1] - spd
                plx[1] = v if v > 0 else 0
            if kd(K_6):
                v = plx[1] + spd
                plx[1] = v if v < W - PW else W - PW
            ovr = kd(K_EXE)
        else:
            ovr = kd(K_EXE) or kd(K_OK)
        fire_ovr = ovr and not ovr_prev
        ovr_prev = ovr

        if kd(K_DEL):
            if pause() == 0:
                return False
            wipe(); hud_reset(); stars_draw()
            tnext = time.monotonic()

        # ---- overdrive: clears every enemy bullet, damages everything ------
        if fire_ovr and bombs > 0:
            bombs -= 1
            fill_rect(0, TOP, W, BOT - TOP, (255, 255, 255))
            fill_rect(0, TOP, W, BOT - TOP, BLK)
            stars_draw()
            nf = 0
            i = ne - 1
            while i >= 0:
                eh[i] -= 4
                if eh[i] <= 0:
                    score += EPTS[et[i]]
                    boom(ex[i], ey[i], 4)
                    kill_e(i)
                i -= 1

        # ---- 2. starfield --------------------------------------------------
        stars_step(frame)

        # ---- 3a. erase everything -----------------------------------------
        fr = fill_rect
        for i in range(nb):
            fr(bx[i], by[i], 2, 6, BLK)
        for i in range(ne):
            t = et[i]
            fr(ex[i], ey[i], EWD[t], EHT[t] + 2, BLK)
        for i in range(nf):
            fr(fx[i], fy[i], 3, 5, BLK)
        for i in range(npk):
            fr(px[i], py[i], 5, 5, BLK)
        for i in range(nx):
            fr(xx[i], xy[i], 12, 12, BLK)
        for i in range(2):
            if pon[i]:
                fr(ppx[i], PY, PW, PH, BLK)

        # ---- 3b. player bullets: move, then hit-test against enemies -------
        i = nb - 1
        bspd = 9 + (up[U_BSPD] << 1)
        while i >= 0:
            y = by[i] - bspd
            if y < TOP:
                kill_b(i)
                i -= 1
                continue
            by[i] = y
            x = bx[i] + bd[i]
            bx[i] = x
            g = bg[i]
            dmg = g % 100
            j = ne - 1
            gone = False
            while j >= 0:
                # y first: it separates far more pairs than x does here
                ty = ey[j]
                if y < ty + EHT[et[j]] and y + 6 > ty:
                    tx = ex[j]
                    if x < tx + EWD[et[j]] and x + 2 > tx:
                        eh[j] -= dmg
                        if eh[j] <= 0:
                            t = et[j]
                            score += EPTS[t]
                            boom(tx, ty, 3 if t != T_BOSS else 8)
                            # crystals, plus the odd repair from bigger ships
                            if t == T_BOSS:
                                for _ in range(5):
                                    spawn_p(tx + 8 + rnd(32), ty + 8, 0)
                            elif rnd(10) < 6:
                                spawn_p(tx + 3, ty + 3, 1 if rnd(8) == 0 else 0)
                            kill_e(j)
                        else:
                            boom(x - 4, y - 4, 1)
                        if g < 100:          # not piercing: bullet is spent
                            gone = True
                            break
                j -= 1
            if gone:
                kill_b(i)
            i -= 1

        # ---- 3c. enemies: move, shoot, ram --------------------------------
        i = ne - 1
        while i >= 0:
            t = et[i]
            x = ex[i]
            y = ey[i]
            if t == T_WEAVE:
                x += ep[i]
                if x < 0 or x > W - EWD[t]:
                    ep[i] = -ep[i]
                    x = 0 if x < 0 else W - EWD[t]
                y += 2
            elif t == T_TURRET:
                if y < ep[i]:
                    y += 2
                elif frame & 1:
                    # The anchor itself sinks, one pixel every other frame. A
                    # turret gets to camp and shell you, but it always ends up
                    # in your face or off the bottom -- a fight can never stall
                    # on an enemy the player is happy to ignore.
                    ep[i] += 1
            elif t == T_BOSS:
                x += ep[i]
                if x < 4 or x > W - 52:
                    ep[i] = -ep[i]
                # It presses down, a pixel every ten frames. Kill it or it
                # lands on you: a boss fight is always bounded, and deep in the
                # Void -- where the ship's damage has capped but the boss pool
                # has not -- the run ends in a death rather than a stalemate.
                if not frame % 10:
                    y += 1
            else:
                y += ESPD[t]
            ex[i] = x
            ey[i] = y

            if y > BOT:
                kill_e(i)
                i -= 1
                continue

            # firing
            f = FIRE[t]
            if f:
                c = ec[i] - 1
                if c <= 0:
                    c = f - rate_boost - rnd(20)
                    if c < 14:
                        c = 14
                    cx = x + (EWD[t] >> 1)
                    cy = y + EHT[t]
                    # aim: horizontal offset shifted down to a -2..2 drift,
                    # no division and no trigonometry in the hot path
                    d = (plx[0] + 7 - cx) >> 5
                    if d > 2:
                        d = 2
                    elif d < -2:
                        d = -2
                    if t == T_BOSS:
                        spawn_f(cx - 18, cy, -1, 4)
                        spawn_f(cx, cy, d, 4)
                        spawn_f(cx + 18, cy, 1, 4)
                    elif t == T_TANK:
                        spawn_f(cx - 6, cy, d - 1, 3)
                        spawn_f(cx + 6, cy, d + 1, 3)
                    else:
                        spawn_f(cx, cy, d, 4)
                ec[i] = c

            # ramming a ship
            hh = EHT[t]
            if y + hh > PY and y < PY + PH:
                ww = EWD[t]
                for pi in range(2):
                    if pon[pi] and not piv[pi]:
                        hx = plx[pi] + 4
                        if x < hx + 6 and x + ww > hx:
                            hurt(pi)
                            if t != T_BOSS:
                                eh[i] = 0
                                boom(x, y, 3)
                                kill_e(i)
                            break
            i -= 1

        # ---- 3d. enemy bullets --------------------------------------------
        i = nf - 1
        while i >= 0:
            y = fy[i] + fv[i]
            x = fx[i] + fu[i]
            if y > BOT or x < 0 or x > W:
                kill_f(i)
                i -= 1
                continue
            fy[i] = y
            fx[i] = x
            if y + 5 > PY and y < PY + PH:
                for pi in range(2):
                    if pon[pi] and not piv[pi]:
                        hx = plx[pi] + 4
                        if x < hx + 6 and x + 3 > hx:
                            hurt(pi)
                            kill_f(i)
                            break
            i -= 1

        # ---- 3e. pickups ---------------------------------------------------
        i = npk - 1
        while i >= 0:
            y = py[i] + 2
            x = px[i]
            if up[U_MAG] and y > TOP + 40:
                # tractor beam: drift toward the nearest ship
                best = plx[0]
                if pon[1] and abs(plx[1] - x) < abs(best - x):
                    best = plx[1]
                d = best + 4 - x
                if d > 1:
                    x += 2
                elif d < -1:
                    x -= 2
            if y > BOT:
                kill_p(i)
                i -= 1
                continue
            py[i] = y
            px[i] = x
            for pi in range(2):
                if pon[pi] and y + 5 > PY and y < PY + PH:
                    hx = plx[pi]
                    if x < hx + PW and x + 5 > hx:
                        if pk[i]:
                            if hull < hullmax:
                                hull += 1
                        else:
                            cry += 2 + up[U_GREED]
                            score += 5
                        kill_p(i)
                        break
            i -= 1

        # ---- 3f. explosions, ship timers, spawning -------------------------
        i = nx - 1
        while i >= 0:
            xt[i] -= 1
            if xt[i] <= 0:
                nx -= 1
                if i != nx:
                    xx[i] = xx[nx]; xy[i] = xy[nx]; xt[i] = xt[nx]
            i -= 1

        rate = 9 - (up[U_RATE] << 1)
        if rate < 3:
            rate = 3
        for pi in range(2):
            if not pon[pi]:
                continue
            if piv[pi]:
                piv[pi] -= 1
            c = pcd[pi] - 1
            if c <= 0:
                shoot(pi)
                c = rate
            pcd[pi] = c
            if up[U_SHIELD] and not psh[pi]:
                pst[pi] -= 1
                if pst[pi] <= 0:
                    psh[pi] = 1

        if budget > 0:
            stimer -= 1
            if stimer <= 0 and ne < NE - 1:
                t = rnd(pool_n)
                budget -= COST[t]
                w = EWD[t]
                hp = EHP[t] + (sector >> 1)
                p = -2 + (rnd(2) << 2) if t == T_WEAVE else TOP + 20 + rnd(50)
                spawn_e(t, 4 + rnd(W - w - 8), TOP - EHT[t], p, hp)
                stimer = 16 + rnd(22) - sector * 2
                if stimer < 7:
                    stimer = 7

        # ---- 4. draw everything at its new position ------------------------
        for i in range(nb):
            fr(bx[i], by[i], 2, 6, YLW)
        for i in range(ne):
            t = et[i]
            sprite(ESPR[t], ex[i], ey[i], RED if t == T_BOSS else acc)
        for i in range(nf):
            fr(fx[i], fy[i], 3, 5, ORG)
        for i in range(npk):
            fr(px[i], py[i], 5, 5, GRN if pk[i] else CYN)
        for i in range(nx):
            s = xt[i]
            fr(xx[i] + 4 - s, xy[i] + 4 - s, s << 1, s << 1, WHT if s > 2 else ORG)
        for i in range(2):
            if pon[i]:
                x = plx[i]
                ppx[i] = x
                # blink while invulnerable: skipping the draw is free
                if not piv[i] or frame & 2:
                    sprite(PSPR, x, PY, CYN if i == 0 else VLT)
                    if up[U_SHIELD] and psh[i]:
                        fr(x - 1, PY + PH, PW + 2, 1, BLU)

        # ---- 5. HUD --------------------------------------------------------
        if boss and ne:
            bar(70, HUD_H + 2, 180, 4, eh[0], bhp, RED)
        hud(tag)

        # ---- outcome -------------------------------------------------------
        if hull <= 0:
            return False
        if not boss and budget <= 0 and ne == 0 and nf == 0:
            return True
        if boss and ne == 0:
            for _ in range(8):
                spawn_p(60 + rnd(200), TOP + 40 + rnd(60), 0)
            return True

        # ---- 6. frame limiter ----------------------------------------------
        # Cap the pace so the game feels identical on every model; if a frame
        # overruns we simply do not sleep, and never try to catch up (that would
        # teleport entities through each other).
        t = time.monotonic()
        d = tnext - t
        if d > 0:
            time.sleep(d)
            tnext += FRAME
        else:
            tnext = t + FRAME


def hurt(pi):
    """A ship took a hit. Deflector first, then the shared hull."""
    global hull
    if psh[pi]:
        psh[pi] = 0
        pst[pi] = 170
        piv[pi] = 20
        boom(plx[pi], PY - 4, 4)
        return
    hull -= 1
    piv[pi] = 45
    boom(plx[pi], PY - 4, 5)

# ---------------------------------------------------------------------------
# Menu input. Menus are not real-time, so blocking is fine and costs no battery
# once we sleep between polls. Every menu waits for a full release first, so a
# key held from the previous screen never leaks a phantom press.
# ---------------------------------------------------------------------------
MKEYS = (K_U, K_D, K_L, K_R, K_OK, K_EXE, K_DEL)


def anykey():
    for k in MKEYS:
        if keydown(k):
            return True
    return False


def menukey():
    while anykey():
        time.sleep(0.02)
    while True:
        for k in MKEYS:
            if keydown(k):
                return k
        time.sleep(0.02)


def pause():
    """Returns 1 to resume, 0 to abandon the run."""
    fill_rect(60, 80, 200, 62, DRK)
    fill_rect(62, 82, 196, 58, BLK)
    centre("PAUSED", 92, WHT)
    centre("OK  RESUME", 112, GRY)
    while True:
        k = menukey()
        if k == K_OK or k == K_EXE or k == K_DEL:
            return 1
        if k == K_L:
            return 0


# ---------------------------------------------------------------------------
# Sector map.
#
# Generated forward from the current column, so every node placed is reachable
# by construction -- no connectivity pass, no backtracking, no wasted bytes.
# ---------------------------------------------------------------------------
NCH = ("X", "!", "$", "?", "+", "@")
NCOL = (GRY, ORG, YLW, CYN, GRN, RED)
NNAME = ("PATROL", "ELITE", "TRADER", "SIGNAL", "REPAIR", "WARLORD")


def node_type(c):
    """Column 4 is always a trader and column 6 always a repair bay, on every
    row. Whichever route the player takes, the pacing is the same:
    fight, fight, fight, TRADE, fight, fight, REPAIR, BOSS."""
    if c == 1:
        return N_FIGHT
    if c == 4:
        return N_SHOP
    if c == 6:
        return N_REST
    r = rnd(100)
    if r < 46:
        return N_FIGHT
    if r < 70:
        return N_ELITE
    return N_EVENT


def genmap():
    global mcol, mrow
    for i in range(MCOLS * MROWS):
        mt[i] = -1
        mdone[i] = 0
    mt[1] = N_FIGHT            # column 0, row 1: the entry node
    mcol = 0
    mrow = 1
    cur = [1]
    for c in range(1, MCOLS - 1):
        nxt = []
        for r in cur:
            for _ in range(1 + rnd(2)):
                nr = r + rnd(3) - 1
                if nr < 0:
                    nr = 0
                elif nr >= MROWS:
                    nr = MROWS - 1
                if nr not in nxt:
                    nxt.append(nr)
        for r in nxt:
            mt[c * MROWS + r] = node_type(c)
        cur = nxt
    mt[(MCOLS - 1) * MROWS + 1] = N_BOSS


MX0 = 14
MDX = 38
MY0 = 52
MDY = 44


def node_xy(c, r):
    return (MX0 + c * MDX, MY0 + r * MDY)


def link(x0, y0, x1, y1, c):
    """Elbow connector: three rects instead of a per-pixel diagonal."""
    xm = (x0 + x1) >> 1
    fill_rect(x0, y0, xm - x0, 2, c)
    if y1 != y0:
        fill_rect(xm, y0 if y1 > y0 else y1, 2, abs(y1 - y0) + 2, c)
    fill_rect(xm, y1, x1 - xm, 2, c)


def draw_map(sel):
    wipe()
    text("SECTOR %d" % (sector + 1), 6, 2, SECC[sector % 5])
    text("%04d" % cry, 178, 2, CYN)
    text("HULL %d" % hull, 240, 2, GRN if hull > 2 else RED)

    # connectors first, so nodes paint over their ends
    for c in range(MCOLS - 1):
        for r in range(MROWS):
            if mt[c * MROWS + r] < 0:
                continue
            x0, y0 = node_xy(c, r)
            for r2 in range(MROWS):
                if mt[(c + 1) * MROWS + r2] < 0 or abs(r2 - r) > 1:
                    continue
                x1, y1 = node_xy(c + 1, r2)
                lit = (c == mcol and r == mrow)
                link(x0 + 20, y0 + 9, x1, y1 + 9, WHT if lit else DRK)

    for c in range(MCOLS):
        for r in range(MROWS):
            t = mt[c * MROWS + r]
            if t < 0:
                continue
            x, y = node_xy(c, r)
            here = (c == mcol and r == mrow)
            pick = (c == mcol + 1 and r == sel)
            if mdone[c * MROWS + r]:
                fill_rect(x, y, 20, 20, DRK)
                text(".", x + 5, y, GRY, DRK)
            else:
                bc = WHT if pick else (DRK if not here else GRY)
                fill_rect(x, y, 20, 20, bc)
                fill_rect(x + 2, y + 2, 16, 16, BLK)
                text(NCH[t], x + 5, y + 1, NCOL[t], BLK)
            if here:
                fill_rect(x + 4, y + 22, 12, 3, CYN)

    # Bottom band: cleared in one go, below the lowest node row (140 + 20 for
    # the node, + 5 for the "you are here" marker) so nothing overlaps.
    sel_t = mt[(mcol + 1) * MROWS + sel] if mcol + 1 < MCOLS else -1
    fill_rect(0, 170, W, H - 170, BLK)
    centre("UP/DOWN + OK", 172, GRY)
    if sel_t >= 0:
        centre(NNAME[sel_t], 196, NCOL[sel_t])


def choose_node():
    """Pick one of the reachable nodes in the next column. Returns its row."""
    opts = []
    for r in range(MROWS):
        if abs(r - mrow) <= 1 and mt[(mcol + 1) * MROWS + r] >= 0:
            opts.append(r)
    if not opts:
        return -1
    i = 0
    while True:
        draw_map(opts[i])
        k = menukey()
        if k == K_U and i > 0:
            i -= 1
        elif k == K_D and i < len(opts) - 1:
            i += 1
        elif k == K_OK or k == K_EXE:
            return opts[i]


# ---------------------------------------------------------------------------
# Trader, rewards and events
# ---------------------------------------------------------------------------

def offers(n):
    """Pick n distinct upgrades that are not already maxed out."""
    out = []
    tries = 0
    while len(out) < n and tries < 40:
        tries += 1
        i = rnd(len(SHOP))
        if i not in out and up[SHOP[i][1]] < 3:
            out.append(i)
    return out


def price(i):
    """Each level of the same upgrade costs half again as much."""
    return SHOP[i][2] + (SHOP[i][2] * up[SHOP[i][1]]) // 2


def panel(head, tc):
    wipe()
    fill_rect(0, 0, W, 3, tc)
    centre(head, 10, tc)


def menu(items, cols, y0):
    """Vertical list with a cursor. Returns the chosen index."""
    i = 0
    n = len(items)
    while True:
        for j in range(n):
            y = y0 + j * 22
            fill_rect(20, y, 280, 20, GRY if j == i else BLK)
            text(items[j], 28, y + 1, BLK if j == i else cols[j],
                 GRY if j == i else BLK)
        k = menukey()
        if k == K_U:
            i = n - 1 if i == 0 else i - 1
        elif k == K_D:
            i = 0 if i == n - 1 else i + 1
        elif k == K_OK or k == K_EXE:
            return i


def shop():
    global cry, hull, hullmax
    ids = offers(3)
    while True:
        items = []
        cols = []
        for i in ids:
            lv = up[SHOP[i][1]]
            p = price(i)
            items.append("%-15s%3d%s" % (SHOP[i][0], p, "*" * lv))
            cols.append(YLW if cry >= p else DRK)
        items.append("%-15s %2d" % ("REPAIR HULL", 18))
        cols.append(GRN if cry >= 18 and hull < hullmax else DRK)
        items.append("LEAVE")
        cols.append(WHT)
        panel("TRADER", YLW)
        text("%04d" % cry, 178, 30, CYN)
        c = menu(items, cols, 60)
        if c == len(items) - 1:
            return
        if c == len(items) - 2:
            if cry >= 18 and hull < hullmax:
                cry -= 18
                hull += 2
                if hull > hullmax:
                    hull = hullmax
            continue
        i = ids[c]
        p = price(i)
        if cry >= p and up[SHOP[i][1]] < 3:
            cry -= p
            grant(SHOP[i][1])


def grant(u):
    global hullmax, hull, bombmax, bombs
    up[u] += 1
    if u == U_HULL:
        hullmax += 2
        hull += 2
    elif u == U_BOMB:
        bombmax += 1
        bombs += 1


def reward(big):
    """Free upgrade pick after an elite fight or a boss."""
    ids = offers(3)
    if not ids:
        return
    if not big:
        ids = ids[:2]
    panel("SALVAGE", CYN)
    centre("CHOOSE ONE", 34, GRY)
    items = []
    cols = []
    for i in ids:
        items.append("%-16s%s" % (SHOP[i][0], "*" * up[SHOP[i][1]]))
        cols.append(CYN)
    c = menu(items, cols, 70)
    grant(SHOP[ids[c]][1])


# title, prompt, label A, effect A, value A, label B, effect B, value B
# effects: 0 crystals, 1 risky salvage, 2 repair, 3 ambush, 4 nothing,
#          5 free upgrade, 6 buy max hull
EVT = (
    ("DERELICT HULK", "IT IS VENTING ATMOSPHERE", "SALVAGE", 1, 26, "MOVE ON", 0, 8),
    ("DISTRESS BEACON", "THE SIGNAL LOOPS", "ANSWER", 3, 0, "IGNORE", 0, 10),
    ("FUEL DEPOT", "ABANDONED, MOSTLY", "SIPHON", 0, 22, "REPAIR HERE", 2, 3),
    ("DRIFTING ENGINEER", "SHE WANTS PASSAGE", "TAKE HER IN", 5, 0, "REFUSE", 0, 14),
    ("ASTEROID FIELD", "DENSE, AND VERY QUIET", "CUT THROUGH", 1, 30, "GO AROUND", 4, 0),
    ("VOID SHRINE", "PILGRIMS TRADED HERE", "OFFER 25", 6, 25, "STEAL", 3, 0),
)


def event(idx):
    global cry, hull, hullmax
    e = EVT[rnd(len(EVT))]
    panel(e[0], VLT)
    centre(e[1], 40, GRY)
    c = menu([e[2], e[5]], [VLT, VLT], 90)
    fx_, val = (e[3], e[4]) if c == 0 else (e[6], e[7])
    if fx_ == 0:
        cry += val
        flash("+%d CRYSTALS" % val, CYN)
    elif fx_ == 1:
        if rnd(10) < 6:
            cry += val
            flash("+%d CRYSTALS" % val, CYN)
        else:
            hull -= 2
            flash("HULL BREACH  -2", RED)
    elif fx_ == 2:
        hull = min(hullmax, hull + val)
        flash("HULL REPAIRED", GRN)
    elif fx_ == 3:
        flash("AMBUSH!", RED)
        return fight(N_ELITE, idx)
    elif fx_ == 5:
        flash("SHE OWES YOU ONE", VLT)
        reward(False)
    elif fx_ == 6:
        if cry >= val:
            cry -= val
            hullmax += 2
            hull += 2
            flash("MAX HULL +2", GRN)
        else:
            flash("NOT ENOUGH", DRK)
    return True


def flash(msg, c):
    fill_rect(0, 150, W, 24, BLK)
    centre(msg, 152, c)
    time.sleep(1.1)


# ---------------------------------------------------------------------------
# Numeric entry, used for seeds. Digit keys are not contiguous in the matrix,
# so they live in a lookup table indexed by the digit itself.
# ---------------------------------------------------------------------------
DIGIT = (ion.KEY_ZERO, ion.KEY_ONE, ion.KEY_TWO, ion.KEY_THREE, ion.KEY_FOUR,
         ion.KEY_FIVE, ion.KEY_SIX, ion.KEY_SEVEN, ion.KEY_EIGHT, ion.KEY_NINE)


def numinput(head, maxlen):
    panel(head, CYN)
    centre("TYPE DIGITS, OK TO START", 40, GRY)
    s = ""
    while True:
        fill_rect(60, 90, 200, 24, DRK)
        text(s + "_", 68, 92, WHT, DRK)
        while True:
            hit = -1
            for d in range(10):
                if keydown(DIGIT[d]):
                    hit = d
                    break
            if hit >= 0:
                if len(s) < maxlen:
                    s += chr(48 + hit)
                break
            if keydown(K_DEL):
                s = s[:-1]
                break
            if keydown(K_OK) or keydown(K_EXE):
                return int(s) if s else 0
            time.sleep(0.02)
        while anykey() or [1 for d in range(10) if keydown(DIGIT[d])]:
            time.sleep(0.02)


# ---------------------------------------------------------------------------
# Title, help and end screens
# ---------------------------------------------------------------------------

def title():
    """Returns (player count, seed)."""
    global diff
    while True:
        wipe()
        for i in range(40):
            set_pixel(rnd(W), 30 + rnd(H - 30), SCOL[rnd(3)])
        fill_rect(0, 40, W, 3, CYN)
        centre("N O V A", 52, WHT)
        fill_rect(0, 74, W, 3, CYN)
        centre("A ROGUE-LITE FOR NUMWORKS", 80, GRY)
        c = menu(["SOLO", "CO-OP  2 PLAYERS", "SEEDED RUN",
                  "DIFFICULTY  " + DNAME[diff], "CONTROLS"],
                 [CYN, VLT, YLW, ORG, GRY], 108)
        if c == 0:
            return 1, time.monotonic().__int__() & 0xFFFF
        if c == 1:
            return 2, time.monotonic().__int__() & 0xFFFF
        if c == 2:
            return 1, numinput("SEEDED RUN", 5) & 0xFFFF
        if c == 3:
            diff = (diff + 1) % 3
        else:
            helpscreen()


def helpscreen():
    panel("CONTROLS", GRY)
    text("P1      LEFT / RIGHT ARROWS", 14, 40, CYN)
    text("P2      KEYS 4 AND 6", 14, 62, VLT)
    text("FIRE    AUTOMATIC", 14, 84, YLW)
    text("BOMB    EXE  (SOLO: ALSO OK)", 14, 106, ORG)
    text("PAUSE   BACKSPACE", 14, 128, GRY)
    centre("CLEAR 5 SECTORS TO WIN", 168, WHT)
    centre("OK", 194, GRY)
    menukey()


def endscreen(won):
    panel("RUN COMPLETE" if won else "SHIP LOST", GRN if won else RED)
    if sector >= 5:
        centre("VOID DEPTH %d" % (sector - 4), 60, VLT)
    else:
        centre("SECTOR %d" % (sector + 1), 60, WHT)
    centre("SCORE %06d" % score, 84, YLW)
    centre("SEED %05d  %s" % (seed0, DNAME[diff]), 108, GRY)
    if cleared:
        centre("CAMPAIGN CLEARED", 136, GRN)
    centre("OK TO CONTINUE", 190, GRY)
    menukey()


# ---------------------------------------------------------------------------
# Run driver
# ---------------------------------------------------------------------------

def newrun(np_, seed):
    global hull, hullmax, cry, score, sector, bombs, bombmax, players, seed0
    global rs, cleared
    for i in range(UMAX):
        up[i] = 0
    # Two ships are two things to hit but only one hull bar, so co-op needs a
    # deeper bar or it is strictly harder than solo -- which it should not be.
    hullmax = DHULL[diff] + (6 if np_ > 1 else 0)
    hull = hullmax
    cry = 0
    score = 0
    sector = 0
    cleared = 0
    bombs = 2
    bombmax = 2
    players = np_
    seed0 = seed
    srnd(seed)
    pon[0] = 1
    pon[1] = 1 if np_ > 1 else 0
    plx[0] = 90 if np_ > 1 else 153
    plx[1] = 216
    for i in range(2):
        ppx[i] = plx[i]
        pcd[i] = 4
        psh[i] = 0
        pst[i] = 0
        piv[i] = 0


def play():
    global sector, mcol, mrow, bombs, hull, cry, cleared
    while True:
        genmap()
        while True:
            r = choose_node()
            if r < 0:
                break
            mcol += 1
            mrow = r
            k = mt[mcol * MROWS + mrow]
            mdone[mcol * MROWS + mrow] = 1
            bombs = bombmax           # overdrive refills between nodes
            if up[U_REGEN] and hull < hullmax:
                hull = min(hullmax, hull + up[U_REGEN])

            if k == N_SHOP:
                shop()
            elif k == N_REST:
                panel("REPAIR BAY", GRN)
                hull = min(hullmax, hull + 4)
                centre("HULL RESTORED", 90, GRN)
                centre("OK", 180, GRY)
                menukey()
            elif k == N_EVENT:
                if not event(mcol):
                    return False
            else:
                if not fight(k, mcol):
                    return False
                if k == N_ELITE:
                    reward(False)
                elif k == N_BOSS:
                    reward(True)
                else:
                    cry += 6 + up[U_GREED] * 3
            if mcol >= MCOLS - 1:
                break
        sector += 1
        if sector == 5:
            # The five sectors are the campaign. The Void is what keeps the
            # cartridge in the machine: same rules, no ceiling, one score.
            cleared = 1
            panel("VICTORY", GRN)
            centre("FIVE SECTORS CLEARED", 62, GRN)
            centre("SCORE %06d" % score, 86, YLW)
            centre("THE VOID HAS NO EDGE", 112, VLT)
            if menu(["ENTER THE VOID", "END RUN HERE"], [VLT, WHT], 146) == 1:
                return True
        else:
            panel("SECTOR CLEARED", SECC[(sector - 1) % 5])
            centre("ENTERING SECTOR %d" % (sector + 1), 90, WHT)
            centre("OK", 180, GRY)
            menukey()


def main():
    while True:
        np_, seed = title()
        newrun(np_, seed)
        won = play()
        endscreen(won)


main()
