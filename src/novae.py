# NOVA - entities and the per-frame phases.  MIT licence.
#
# Entities live in flat lists: entity i occupies [i*w, i*w+w), so removing one
# is a single slice move instead of six assignments. Pools are compacted -- live
# entities fill slots 0..n-1 -- so loops never test whether a slot is in use,
# and nothing is allocated during a fight, so the GC never runs mid-frame.

from novad import (BLK, BMAX, BOMB, BOSS, BOT, CRY, EH, EHP, EPT, EW, GRY,
    HMAX, HULL, KD, KE, KO, KU, NB, NE, NF, PH, PY, S, SCORE, SHOP, SPREAD,
    TOP, UBMB, UDMG, UGRD, UHUL, UP, UPRC, URATE, USPR, W, WHT, ctr,
    fill_rect, mkey, rnd, txt)

NBM = 12
NEM = 12
NFM = 16

B = [0] * (NBM * 4)      # x, y, drift, damage
E = [0] * (NEM * 6)      # x, y, type, hp, param, cooldown
F = [0] * (NFM * 4)      # x, y, dx, dy

PX = [40, 240]
PC = [0, 0]
PI = [0, 0]
PON = [1, 0]


def kill(p, o, w, ci):
    """Swap the last live entity into offset o. Used by every pool."""
    n = S[ci] - 1
    S[ci] = n
    m = n * w
    if o != m:
        p[o:o + w] = p[m:m + w]


def efire(x, y, u, v):
    n = S[NF]
    if n < NFM:
        F[n * 4:n * 4 + 4] = (x, y, u, v)
        S[NF] = n + 1


def hitp(x, y, w, h):
    """Which player this box hits, or -1. The ship's hitbox is deliberately
    narrower than its sprite: a shmup should forgive near-misses."""
    if y + h > PY and y < PY + PH:
        for i in range(2):
            if PON[i] and not PI[i]:
                hx = PX[i] + 4
                if x < hx + 6 and x + w > hx:
                    return i
    return -1


def hurt(pi):
    S[HULL] -= 1
    PI[pi] = 45


def shoot(pi):
    """Auto-fire: no fire button, so each player needs only two keys and the
    controls stay clear of the keyboard matrix's ghosting cases."""
    d = 1 + UP[UDMG] + (100 if UP[UPRC] else 0)
    for off in SPREAD[UP[USPR] if UP[USPR] < 4 else 3]:
        n = S[NB]
        if n >= NBM:
            return
        B[n * 4:n * 4 + 4] = (PX[pi] + 6 + off[0], PY - 6, off[1], d)
        S[NB] = n + 1





def cost(i):
    """Each level of the same upgrade costs half again as much, which nudges
    the player to broaden a build rather than stack one stat."""
    return SHOP[i][2] + (SHOP[i][2] * UP[SHOP[i][1]]) // 2




def offers():
    out = []
    t = 0
    while len(out) < 3 and t < 30:
        t += 1
        i = rnd(8)
        if i not in out and UP[SHOP[i][1]] < 3:
            out.append(i)
    return out




def grant(u):
    UP[u] += 1
    if u == UHUL:
        S[HMAX] += 2
        S[HULL] += 2
    elif u == UBMB:
        S[BMAX] += 1
        S[BOMB] += 1





def hatch(t, sec):
    """Put one enemy on screen; return the delay before the next."""
    n = S[NE]
    p = -2 + (rnd(2) << 2) if t == 1 else TOP + 20 + rnd(50)
    E[n * 6:n * 6 + 6] = (4 + rnd(W - EW[t] - 8), TOP - EH[t], t,
                          EHP[t] + (sec >> 1), p, 20 + rnd(40))
    S[NE] = n + 1
    d = 16 + rnd(22) - sec * 2
    return d if d > 7 else 7





def overdrive():
    """Screen-clearing bomb: wipes enemy fire, hurts everything alive."""
    S[BOMB] -= 1
    fill_rect(0, TOP, W, BOT - TOP, WHT)
    fill_rect(0, TOP, W, BOT - TOP, BLK)
    S[NF] = 0
    o = (S[NE] - 1) * 6
    while o >= 0:
        E[o + 3] -= 4
        if E[o + 3] <= 0:
            ekill(o, E[o + 2], E[o], E[o + 1])
        o -= 6





def bosshp(sec):
    """Scale the boss to the guns the player actually brought: a flat pool is
    eight seconds against a maxed build and two minutes against a stock one."""
    r0 = 9 - (UP[URATE] << 1)
    if r0 < 3:
        r0 = 3
    n = len(SPREAD[UP[USPR] if UP[USPR] < 4 else 3])
    return 30 + sec * 4 + (1 + UP[UDMG]) * n * 25 // r0 * 7


def menu(items, cols, y0, foot):
    """Vertical list with a cursor; `foot` is a help line per item."""
    i = 0
    n = len(items)
    while True:
        for j in range(n):
            y = y0 + j * 21
            s = j == i
            fill_rect(16, y, 288, 19, GRY if s else BLK)
            txt(items[j], 22, y, BLK if s else cols[j], GRY if s else BLK)
        fill_rect(0, 196, W, 22, BLK)
        ctr(foot[i], 198, GRY)
        k = mkey()
        if k == KU:
            i = n - 1 if i == 0 else i - 1
        elif k == KD:
            i = 0 if i == n - 1 else i + 1
        elif k == KO or k == KE:
            return i


def ekill(e, t, tx, ty):
    """Score and salvage credit on the kill. Crystals used to drop and be
    collected; the chase was good, the pool that made it work was not
    affordable on a 32 KB heap."""
    S[SCORE] += EPT[t] * 5
    S[CRY] += (6 if t == BOSS else 1) * (2 + UP[UGRD])
    kill(E, e, 6, NE)
