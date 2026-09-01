"""Palette, sprites and tables for the PC build.

The calculator version had to pack ships into three rectangles and enemy stats
into `bytes` objects. None of that applies here, so the sprites are real pixel
art and the tables are readable. What carries over is the look: a small fixed
palette, chunky pixels, nothing anti-aliased.
"""

# --- viewport ------------------------------------------------------------
# The canvas is sized to the display, then blown up by a WHOLE number, so a
# game pixel is always a hard square. Its dimensions therefore change with the
# monitor: 480x270 on 1080p, 688x288 on a 3440x1440 ultrawide, 455x256 on a
# 1366x768 laptop.
#
# The playfield does NOT change with it. On a vertical shmup the width of the
# arena is a difficulty setting -- give an ultrawide player 40% more room to
# dodge in and it is a different, easier game. So the arena keeps a fixed size,
# centred, and the extra canvas becomes starfield and side panels.
#
# W/H are the canvas; TOP/BOT/PLAY_L/PLAY_R bound the arena. Modules read them
# through `data.`, never by copying, so a resize takes effect everywhere at
# once.

ARENA_W = 480          # arena size in game units, on any monitor
ARENA_H = 244
MIN_CANVAS_W = 440     # below this the arena shrinks to fit
MIN_CANVAS_H = 250
HUD_H = 26

W = 480
H = 270
TOP = HUD_H
BOT = 270
PLAY_L = 0
PLAY_R = 480


def pick_scale(screen_w, screen_h):
    """Largest whole-number zoom that still shows a usable canvas."""
    return max(1, min(screen_w // MIN_CANVAS_W, screen_h // MIN_CANVAS_H))


def set_viewport(canvas_w, canvas_h):
    """Resize the canvas and re-centre the arena inside it."""
    global W, H, TOP, BOT, PLAY_L, PLAY_R
    W = canvas_w
    H = canvas_h
    play_w = min(ARENA_W, canvas_w)
    play_h = min(ARENA_H, canvas_h - HUD_H)
    PLAY_L = (canvas_w - play_w) // 2
    PLAY_R = PLAY_L + play_w
    TOP = HUD_H + (canvas_h - HUD_H - play_h) // 2
    BOT = TOP + play_h


def arena_rect():
    return (PLAY_L, TOP, PLAY_R - PLAY_L, BOT - TOP)

# --- palette -------------------------------------------------------------
BLACK = (10, 12, 18)
VOID = (16, 19, 28)
WHITE = (236, 244, 255)
GREY = (122, 136, 162)
DARK = (44, 52, 70)
CYAN = (72, 226, 255)
CYAN_D = (28, 132, 176)
VIOLET = (196, 122, 255)
VIOLET_D = (112, 62, 168)
GREEN = (96, 240, 140)
GREEN_D = (42, 148, 84)
YELLOW = (255, 220, 88)
ORANGE = (255, 150, 52)
RED = (255, 82, 82)
RED_D = (168, 40, 48)
PINK = (255, 122, 178)
BLUE = (96, 152, 255)

# One accent per sector, reused for enemy tinting and UI chrome.
SECTOR_COLOURS = (CYAN, GREEN, VIOLET, ORANGE, RED)


def SEC_ACCENT(sector):
    return SECTOR_COLOURS[sector % len(SECTOR_COLOURS)]

# Star layers: colour and pixels per frame.
STAR_LAYERS = ((62, 70, 96, 0.35), (110, 124, 156, 0.7), (206, 216, 244, 1.25))

# --- sprites -------------------------------------------------------------
# Drawn as text so they can be edited by hand. Each character maps to a colour
# through the sprite's own palette dict; a space is transparent.

# Sprites are drawn as their LEFT HALF plus the centre column; build_sprite
# mirrors them. Symmetry comes free and there is half as much to draw by hand.
#   c/v = hull    w = highlight    d = dark trim    o = engine glow
#   a = sector accent (enemies only)   . = transparent

PLAYER_1 = """
......w
......w
.....wc
.....wc
....wcc
....wcc
...wccc
...wccc
..wcccc
.wccccc
wcccccc
wcc.ccc
wc..ccc
w...ccc
.....dc
....o.c
....oo.
""".strip("\n")

PLAYER_2 = """
......w
......w
.....wv
.....wv
....wvv
....wvv
...wvvv
...wvvv
..wvvvv
.wvvvvv
wvvvvvv
wvv.vvv
wv..vvv
w...vvv
.....dv
....o.v
....oo.
""".strip("\n")

# Enemies point downward: the nose is at the bottom.
GRUNT = """
aaaaaa
aaaaaa
awwwaa
awwwaa
.aaaaa
.aaaaa
..addd
..aaaa
...aaa
...aaa
....aa
""".strip("\n")

WEAVER = """
aa...a
aa..aa
.aa.aa
.aaaaa
..awwa
..awwa
.aaaaa
.aa.aa
aa..aa
aa...a
a....a
""".strip("\n")

TURRET = """
...aaa
..aaaa
.aaaaa
aaaaaa
aawwwa
aawwwa
aaaaaa
.aaaaa
..addd
..addd
...aaa
....aa
""".strip("\n")

RUSHER = """
....aa
....aa
...aaa
...aaa
..awwa
..awwa
..aaaa
...aaa
...aaa
....aa
....aa
....da
.....a
""".strip("\n")

TANK = """
..aaaaaaa
.aaaaaaaa
aaaaaaaaa
aaaawwwaa
aaaawwwaa
aaaaaaaaa
addaaaadd
addaaaadd
aaaaaaaaa
.aaaaaaaa
..aaaaaaa
...aa.ddd
....a.ddd
""".strip("\n")

# --- bosses --------------------------------------------------------------
# One per sector, each with its own silhouette and its own trick. Drawn as the
# left half plus the centre column, like everything else.

# 1. SENTINEL -- a gun platform. Fans of shots, nothing clever.
BOSS_SENTINEL = """
.........aaaaaaaaaa
.......aaaaaaaaaaaa
.....aaaaaaaaaaaaaa
...aaaaaaaawwwwwwaa
..aaaaaaawwwwwwwwaa
.aaaaaaaawwwwwwwwaa
aaaaaaaaaawwwwwwwaa
aaddaaaaaaaaaaaaaaa
aaddaaaaaaaaaaaaaaa
aaddaaaaaaaddddddaa
.aaaaaaaaaaddddddaa
..aaaaaaaaaddddddaa
...aaaaaaaaaaaaaaaa
....aaaa.aaaaaaaaaa
.....dd...aaaaaaaaa
..........aaaddddaa
...........aadddd.a
""".strip("\n")

# 2. HIVE -- a carrier. Opens its bays and sends escorts at you.
BOSS_HIVE = """
......aaaaaaaaaaaaa
....aaaaaaaaaaaaaaa
..aaaaaaaaaaaaaaaaa
.aaaaaaaaaaaaaaaaaa
aaaaawwwaaaaawwwaaa
aaaawwwwwaaawwwwwaa
aaaawwwwwaaawwwwwaa
aaaaawwwaaaaawwwaaa
aaaaaaaaaaaaaaaaaaa
aaddddaaaaaaddddaaa
aaddddaaaaaaddddaaa
aaddddaaaaaaddddaaa
.aaaaaaaaaaaaaaaaaa
..aaaaaaaaaaaaaaaaa
...aaaaaaaaaaaaaaaa
.....aaaa...aaaaaaa
.......d.....ddaaaa
""".strip("\n")

# 3. LANCE -- one enormous cannon. Telegraphs, then fires a beam.
BOSS_LANCE = """
............aaaaaaa
..........aaaaaaaaa
........aaaaaaaaaaa
......aaaaaaaaaaaaa
....aaaaaaaaaaaaaaa
..aaaaaaaaawwwwwwaa
.aaaaaaaaawwwwwwwaa
aaaaaaaaaawwwwwwwaa
aaaaaaaaaaaawwwwaaa
.aaaaaaaaaaaaaaaaaa
..aaaaaaaaaaaaaaaaa
...aaaaaaaaddddddaa
....aaaaaaaddddddaa
.....aaaaaaddddddaa
......aaaaaddddddaa
.......aaaaddddddaa
........aaaddddddaa
.........aadddddd.a
""".strip("\n")

# 4. BULWARK -- a core behind two turret pods. Break the pods first.
BOSS_BULWARK = """
.......aaaaaaaaaaaa
.....aaaaaaaaaaaaaa
...aaaaaaaaaaaaaaaa
..aaaaaaaaaaaaaaaaa
.aaaaaaaaawwwwwwwaa
.aaaaaaaawwwwwwwwwa
aaaaaaaaawwwwwwwwwa
aaaaaaaaaawwwwwwwaa
aaaaaaaaaaaaaaaaaaa
.aaaaaaaaaaaaaaaaaa
..aaaaaaaaddddddaaa
...aaaaaaaddddddaaa
....aaaaaaaaaaaaaaa
.....aaaaaaaaaaaaaa
.......aaaa..aaaaaa
.........d....ddaaa
""".strip("\n")

# 5. WARDEN -- everything at once. The campaign's last word.
BOSS_WARDEN = """
..........aaaaaaaaa
........aaaaaaaaaaa
......aaaaaaaaaaaaa
....aaaaaawwwwwwwaa
..aaaaaawwwwwwwwwaa
.aaaaaawwwwwwwwwwaa
aaaaaaawwwwwwwwwwaa
aaaaaaaawwwwwwwwwaa
aaddaaaaaawwwwwwaaa
aaddaaaaaaaaaaaaaaa
aaddaaaaddddddddaaa
aaaaaaaaddddddddaaa
.aaaaaaaddddddddaaa
..aaaaaaddddddddaaa
...aaaaaaaaaaaaaaaa
....aaaaa..aaaaaaaa
......dd....ddaaaaa
.............ddd.aa
""".strip("\n")

BOSS_ART = (BOSS_SENTINEL, BOSS_HIVE, BOSS_LANCE, BOSS_BULWARK, BOSS_WARDEN)
BOSS_NAME = ("SENTINEL", "HIVE MOTHER", "LANCE", "BULWARK", "WARDEN")
BOSS_TELL = ("Fans of fire. Read the gaps.",
             "It launches escorts. Cut them down.",
             "It charges a beam. Do not be there.",
             "Break the pods before the core.",
             "All of it, at once.")

# A turret pod: destructible, sits either side of BULWARK and WARDEN.
BOSS_POD = """
..aaaa
.aawwa
aawwwa
aawwwa
.aawwa
..addd
...aaa
""".strip("\n")

CRYSTAL = """
..w
.wc
wcc
wcc
.wc
..w
""".strip("\n")

REPAIR = """
..g
.gw
gww
gww
.gw
..g
""".strip("\n")

# palettes: character -> colour
P1_PAL = {"c": CYAN, "w": WHITE, "o": ORANGE}
P2_PAL = {"v": VIOLET, "w": WHITE, "o": ORANGE}
CRYSTAL_PAL = {"w": WHITE, "c": CYAN}
REPAIR_PAL = {"w": WHITE, "g": GREEN}

# Enemies are tinted per sector at load time: 'a' is the accent, 'd' its dark
# shade, 'w' stays white.
GRUNT_ID, WEAVER_ID, TURRET_ID, RUSHER_ID, TANK_ID, BOSS_ID = range(6)
ENEMY_ART = (GRUNT, WEAVER, TURRET, RUSHER, TANK, BOSS_SENTINEL)

ENEMY_HP = (2, 2, 6, 2, 12, 1)
ENEMY_SCORE = (10, 15, 25, 20, 40, 500)
ENEMY_SPEED = (46, 42, 40, 118, 22, 0)      # pixels per second
ENEMY_FIRE = (2.6, 0.0, 1.4, 0.0, 1.9, 0.8)  # seconds between shots, 0 = never
ENEMY_COST = (1, 2, 3, 2, 5, 0)             # threat budget

# --- upgrades ------------------------------------------------------------
# All twelve are back: the calculator build could only afford eight.
(U_RATE, U_DMG, U_SPREAD, U_SPEED, U_BULLET, U_PIERCE, U_SHIELD, U_MAGNET,
 U_BOMB, U_HULL, U_GREED, U_REGEN) = range(12)
UPGRADE_COUNT = 12

SHOP = (
    ("RAPID FIRE", U_RATE, 30, "Fire 15% faster"),
    ("HEAVY ROUNDS", U_DMG, 34, "+1 damage per shot"),
    ("SPREAD BARREL", U_SPREAD, 46, "+1 cannon, wider arc"),
    ("THRUSTERS", U_SPEED, 24, "+18% ship speed"),
    ("RAILGUN", U_BULLET, 24, "Shots fly 25% faster"),
    ("PIERCING AMMO", U_PIERCE, 54, "Shots pass through kills"),
    ("DEFLECTOR", U_SHIELD, 50, "Soaks a hit, recharges in 8s"),
    ("TRACTOR BEAM", U_MAGNET, 20, "Crystals drift toward you"),
    ("OVERDRIVE CELL", U_BOMB, 40, "+1 bomb per node"),
    ("HULL PLATING", U_HULL, 44, "+2 max hull, heals 2"),
    ("SCAVENGER", U_GREED, 30, "+1 crystal per pickup"),
    ("NANOREPAIR", U_REGEN, 40, "+1 hull at every node"),
)

# --- difficulty ----------------------------------------------------------
DIFFICULTIES = (
    ("CADET", 16, 0.70, 0.0, "Forgiving. Learn the patterns."),
    ("PILOT", 12, 1.00, 0.15, "The intended fight."),
    ("ACE", 9, 1.35, 0.35, "Fast, dense, unkind."),
)

# --- map nodes -----------------------------------------------------------
(N_FIGHT, N_ELITE, N_SHOP, N_EVENT, N_REST, N_BOSS) = range(6)
NODE_NAME = ("PATROL", "ELITE PATROL", "TRADER", "SIGNAL", "REPAIR BAY",
             "WARLORD")
NODE_GLYPH = ("x", "!", "$", "?", "+", "@")
NODE_COLOUR = (GREY, ORANGE, YELLOW, CYAN, GREEN, RED)
NODE_HINT = ("Crystals, and a little trouble",
             "Harder. It pays in upgrades",
             "Spend your crystals here",
             "Something out there is transmitting",
             "Patch the hull back up",
             "The sector boss. Good luck.")

# --- events --------------------------------------------------------------
# title, line, (label, effect, value) x2
# effects: crystals, risky, repair, ambush, nothing, freeupgrade, maxhull
EVENTS = (
    ("DERELICT HULK", "It is venting atmosphere.",
     ("SALVAGE IT", "risky", 26), ("MOVE ON", "crystals", 8)),
    ("DISTRESS BEACON", "The signal loops, unanswered.",
     ("ANSWER IT", "ambush", 0), ("IGNORE IT", "crystals", 12)),
    ("FUEL DEPOT", "Abandoned. Mostly.",
     ("SIPHON FUEL", "crystals", 24), ("PATCH UP HERE", "repair", 3)),
    ("DRIFTING ENGINEER", "She wants passage, and owes you one.",
     ("TAKE HER IN", "freeupgrade", 0), ("REFUSE", "crystals", 16)),
    ("ASTEROID FIELD", "Dense, and very quiet.",
     ("CUT THROUGH", "risky", 32), ("GO AROUND", "nothing", 0)),
    ("VOID SHRINE", "Pilgrims traded here once.",
     ("OFFER 25", "maxhull", 25), ("TAKE WHAT IS LEFT", "ambush", 0)),
)
