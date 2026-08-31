# NOVA - per-frame update phases, and the between-fight screens.
# MIT licence.
#
# Carved out purely to balance module sizes: MicroPython holds a whole
# module's parse tree in RAM while compiling it, so the peak is set by the
# largest single module, not by the total.

from novad import (BOSS, BOT, EFR, EH, ESP, EW, NB, NE, NF, S, TOP, UP, URATE,
    W, rnd)
from novae import (B, E, F, PC, PI, PON, PX, efire, ekill, hitp, hurt, kill,
    shoot)



def bhit(x, y, dmg, pierce):
    """One shot against every enemy. True if the shot is spent.

    Split out of bullets() to keep nesting shallow: MicroPython holds a whole
    module's parse tree in RAM while compiling, and that tree grows with nesting
    depth far faster than with source length.
    """
    e = (S[NE] - 1) * 6
    while e >= 0:
        t = E[e + 2]
        ty = E[e + 1]
        # y first: it separates far more pairs than x does here
        if y < ty + EH[t] and y + 6 > ty:
            tx = E[e]
            if x < tx + EW[t] and x + 2 > tx:
                E[e + 3] -= dmg
                if E[e + 3] <= 0:
                    ekill(e, t, tx, ty)
                if not pierce:
                    return True
        e -= 6
    return False



def bullets():
    """Move the player's shots, then hit-test them.

    Every update loop walks backwards, so the entity swapped into slot i on a
    kill always comes from a slot already handled this frame: none is skipped,
    none is updated twice.
    """
    o = (S[NB] - 1) * 4
    while o >= 0:
        y = B[o + 1] - 11
        if y < TOP:
            kill(B, o, 4, NB)
        else:
            B[o + 1] = y
            x = B[o] + B[o + 2]
            B[o] = x
            g = B[o + 3]
            if bhit(x, y, g % 100, g > 99):
                kill(B, o, 4, NB)
        o -= 4



def volley(t, x, y, c):
    """Fire this enemy's pattern; return its next cooldown."""
    if c < 14:
        c = 14
    cx = x + (EW[t] >> 1)
    cy = y + EH[t]
    # aim with a shift, not trigonometry or division
    d = (PX[0] + 7 - cx) >> 5
    if d > 2:
        d = 2
    elif d < -2:
        d = -2
    if t == BOSS:
        efire(cx - 18, cy, -1, 4)
        efire(cx + 18, cy, 1, 4)
    efire(cx, cy, d, 4)
    return c



def enemies(frame, boost):
    o = (S[NE] - 1) * 6
    while o >= 0:
        t = E[o + 2]
        x = E[o]
        y = E[o + 1] + ESP[t]
        if t == 1:
            x += E[o + 4]
            if x < 0 or x > W - EW[t]:
                E[o + 4] = -E[o + 4]
                x = 0 if x < 0 else W - EW[t]
        elif t == 2:
            # A turret camps and shells you, but its anchor sinks a pixel every
            # other frame, so it always ends up in your face or off the bottom:
            # a fight can never stall on an enemy you are content to ignore.
            if y < E[o + 4]:
                y += 2
            elif frame & 1:
                E[o + 4] += 1
        elif t == BOSS:
            x += E[o + 4]
            if x < 4 or x > W - 52:
                E[o + 4] = -E[o + 4]
            # It presses down. Kill it or it lands on you, so a boss fight is
            # always bounded: deep in the Void, where the ship's damage has
            # capped but the boss pool has not, a run ends in a death rather
            # than a stalemate.
            if not frame % 10:
                y += 1
        E[o] = x
        E[o + 1] = y
        if y > BOT:
            kill(E, o, 6, NE)
        else:
            if EFR[t]:
                c = E[o + 5] - 1
                if c <= 0:
                    c = volley(t, x, y, EFR[t] - boost - rnd(20))
                E[o + 5] = c
            pi = hitp(x, y, EW[t], EH[t])
            if pi >= 0:
                hurt(pi)
                if t != BOSS:
                    kill(E, o, 6, NE)
        o -= 6



def efly():
    o = (S[NF] - 1) * 4
    while o >= 0:
        y = F[o + 1] + F[o + 3]
        x = F[o] + F[o + 2]
        if y > BOT or x < 0 or x > W:
            kill(F, o, 4, NF)
        else:
            F[o + 1] = y
            F[o] = x
            pi = hitp(x, y, 3, 5)
            if pi >= 0:
                hurt(pi)
                kill(F, o, 4, NF)
        o -= 4



def timers():
    rate = 9 - (UP[URATE] << 1)
    if rate < 3:
        rate = 3
    for pi in range(2):
        if PON[pi]:
            if PI[pi]:
                PI[pi] -= 1
            c = PC[pi] - 1
            if c <= 0:
                shoot(pi)
                c = rate
            PC[pi] = c
