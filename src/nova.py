# NOVA - a space rogue-lite for the NumWorks calculator.  MIT licence.
# https://github.com/softpython2884/NumworkSpace
#
# Run this one. It is deliberately the largest module: MicroPython compiles the
# entry module first, while the heap is still empty, and holds a whole module's
# parse tree in RAM at once. Everything it imports is compiled afterwards, with
# less room -- so the small modules go there.

from novad import (BLK, BMAX, BOMB, BOSS, BOT, CLEAR, CRY, CYN, DRK, EH, EW,
    GRN, GRY, H, HMAX, HULL, K4, K6, KE, KL, KO, KR, NB, NE, NF, NODE, ORG,
    PH, PSPR, PW, PY, RED, S, SCORE, SEC, SECT, SPR, ST, STC, TOP, UGRD, UP,
    USPD, VLT, W, WHT, YLW, ctr, fill_rect, hud, hud_reset, keydown, mkey,
    panel, rnd, set_pixel, spr, srnd, time, wipe)
from novae import (B, E, F, NEM, PC, PI, PON, PX, bosshp, hatch, menu,
    overdrive)
from novaf import bullets, efly, enemies, timers
from novag import choose, trade

FRAME = 0.04                        # 25 fps ceiling
COST = b"\x01\x02\x03\x02\x05"      # threat cost per enemy type




def paint(acc, frame, bl):
    """Draw every entity, or blank it: one pass, two colour schemes.

    Called with bl=1 before the update to erase everything where it stands, and
    bl=0 after to redraw the survivors. Erase-all-then-draw-all keeps the
    picture clean, and it is why the screen itself is never cleared: a frame
    repaints a few thousand pixels rather than all 71040.
    """
    fr = fill_rect
    for o in range(0, S[NB] * 4, 4):
        fr(B[o], B[o + 1], 2, 6, BLK if bl else YLW)
    for o in range(0, S[NE] * 6, 6):
        t = E[o + 2]
        if bl:
            fr(E[o], E[o + 1], EW[t], EH[t] + 2, BLK)
        else:
            spr(SPR, t * 12, E[o], E[o + 1], RED if t == BOSS else acc)
    for o in range(0, S[NF] * 4, 4):
        fr(F[o], F[o + 1], 3, 5, BLK if bl else ORG)
    for i in range(2):
        if PON[i]:
            if bl:
                fr(PX[i], PY, PW, PH, BLK)
            elif not PI[i] or frame & 2:
                spr(PSPR, 0, PX[i], PY, CYN if i == 0 else VLT)


def fight(kind):
    """One combat node. True if the player cleared it.

    A frame, in order: read keys, step the starfield, ERASE every entity and
    update it, DRAW the survivors, refresh only the HUD fields that changed,
    then sleep off what is left of the budget.
    """
    S[NB] = 0
    S[NE] = 0
    S[NF] = 0
    wipe()
    hud_reset()
    for i in range(0, 24, 2):
        ST[i] = rnd(W)
        ST[i + 1] = TOP + rnd(BOT - TOP)

    sec = S[SECT]
    acc = SEC[sec % 5]
    boss = kind == 5
    bhp = 1
    budget = 15 + sec * 9 + S[NODE] * 3
    # Capped: uncapped, deep runs make waves longer rather than harder, and a
    # three-minute fight is exhausting, not exciting.
    if budget > 84:
        budget = 84
    if kind == 1:
        budget = (budget * 7) // 5
    if boss:
        budget = 0
        bhp = bosshp(sec)
        E[0:6] = (136, TOP + 4, BOSS, bhp, 1, 30)
        S[NE] = 1
    pool = 2 + sec
    if pool > 5:
        pool = 5
    tag = "BOSS" if boss else ("S%d-%d" % (sec + 1, S[NODE] + 1))
    boost = 4 + sec * 3
    stimer = 30
    frame = 0
    tnext = time.monotonic()
    held = True          # a key still down from the last screen is not a press

    while True:
        frame += 1
        # Erase first, then read the keys: moving the ship before the erase
        # pass would blank the position it is about to occupy and leave the one
        # it just left painted on screen.
        paint(acc, frame, 1)
        sp = set_pixel
        for i in range(0, 24, 2):
            y = ST[i + 1]
            sp(ST[i], y, BLK)
            if i & 2 or frame & 1:
                y += 1
                if y >= BOT:
                    y = TOP
                    ST[i] = rnd(W)
                ST[i + 1] = y
            sp(ST[i], y, STC[1 if i & 2 else 0])

        kd = keydown
        sp = 5 + UP[USPD]
        if kd(KL):
            v = PX[0] - sp
            PX[0] = v if v > 0 else 0
        if kd(KR):
            v = PX[0] + sp
            PX[0] = v if v < W - PW else W - PW
        if PON[1]:
            if kd(K4):
                v = PX[1] - sp
                PX[1] = v if v > 0 else 0
            if kd(K6):
                v = PX[1] + sp
                PX[1] = v if v < W - PW else W - PW
        ov = kd(KE) or (not PON[1] and kd(KO))
        if ov and not held and S[BOMB] > 0:
            overdrive()
        held = ov

        bullets()
        enemies(frame, boost)
        efly()
        timers()

        if budget > 0:
            stimer -= 1
            if stimer <= 0 and S[NE] < NEM - 1:
                t = rnd(pool)
                budget -= COST[t]
                stimer = hatch(t, sec)

        paint(acc, frame, 0)
        if boss and S[NE]:
            n = (180 * E[3]) // bhp
            fill_rect(70, 20, n, 3, RED)
            fill_rect(70 + n, 20, 180 - n, 3, DRK)
        hud(tag)

        if S[HULL] <= 0:
            return False
        if S[NE] == 0 and (boss or (budget <= 0 and S[NF] == 0)):
            return True

        # Cap the pace so the game feels the same on every model. If a frame
        # overruns we simply do not sleep, and never try to catch up: catching
        # up would teleport entities through each other.
        t = time.monotonic()
        d = tnext - t
        if d > 0:
            time.sleep(d)
            tnext += FRAME
        else:
            tnext = t + FRAME


def title():
    wipe()
    for _ in range(44):
        set_pixel(rnd(W), 26 + rnd(H - 26), (120, 130, 165))
    fill_rect(0, 34, W, 2, CYN)
    fill_rect(0, 72, W, 2, CYN)
    ctr("N O V A", 46, WHT)
    ctr("A ROGUE-LITE FOR NUMWORKS", 76, GRY)
    return 1 + menu(["SOLO", "CO-OP  2 PLAYERS"], [CYN, VLT], 118,
                    ["ARROWS MOVE, FIRE IS AUTO, EXE BOMBS",
                     "P1 ARROWS, P2 KEYS 4 AND 6"])


def play(np_):
    for i in range(8):
        UP[i] = 0
    # Two ships are two things to hit but share one hull bar, so co-op needs a
    # deeper bar or it is strictly harder than solo -- which it should not be.
    S[HMAX] = 12 + (6 if np_ > 1 else 0)
    S[HULL] = S[HMAX]
    S[CRY] = 0
    S[SCORE] = 0
    S[SECT] = 0
    S[CLEAR] = 0
    S[BMAX] = 2
    PON[1] = 1 if np_ > 1 else 0
    PX[0] = 90 if np_ > 1 else 153
    PX[1] = 216
    for i in range(2):
        PC[i] = 4
        PI[i] = 0
    srnd(int(time.monotonic() * 977))

    while True:
        S[NODE] = 0
        while S[NODE] < 7:
            k = choose()
            S[NODE] += 1
            S[BOMB] = S[BMAX]
            if k == 2:
                trade(0)
            elif k == 3:
                panel("REPAIR BAY", GRN)
                S[HULL] = min(S[HMAX], S[HULL] + 5)
                ctr("HULL RESTORED", 90, GRN)
                ctr("OK", 180, GRY)
                mkey()
            else:
                if not fight(k):
                    return False
                if k:
                    trade(1)
                else:
                    S[CRY] += 6 + UP[UGRD] * 3
        S[SECT] += 1
        sec = S[SECT]
        # Five sectors are the campaign. The Void past them is what keeps the
        # cartridge in the machine: same rules, no ceiling, one score.
        if sec == 5:
            S[CLEAR] = 1
        panel("VICTORY" if sec == 5 else "SECTOR CLEARED", SEC[(sec - 1) % 5])
        ctr("THE VOID HAS NO EDGE" if sec >= 5 else
            ("ENTERING SECTOR %d" % (sec + 1)), 88, VLT if sec >= 5 else WHT)
        ctr("SCORE %06d" % S[SCORE], 116, YLW)
        ctr("OK", 180, GRY)
        mkey()

def main():
    while True:
        won = play(title())
        sec = S[SECT]
        panel("RUN COMPLETE" if won else "SHIP LOST", GRN if won else RED)
        ctr(("VOID DEPTH %d" % (sec - 4)) if sec > 4 else
            ("SECTOR %d" % (sec + 1)), 60, VLT if sec > 4 else WHT)
        ctr("SCORE %06d" % S[SCORE], 86, YLW)
        if S[CLEAR]:
            ctr("CAMPAIGN CLEARED", 136, GRN)
        ctr("OK TO CONTINUE", 186, GRY)
        mkey()


main()
