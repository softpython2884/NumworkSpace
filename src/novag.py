# NOVA - the between-fight screens.  MIT licence.
#
# Last module loaded, so the smallest: by then the heap already holds
# everything else, and MicroPython still needs room for this one's whole
# parse tree at once.

from novad import (CRY, CYN, DRK, GRN, GRY, HMAX, HULL, NODE, ORG, RED, S,
    SEC, SECT, SHOP, UP, WHT, YLW, ctr, panel, txt)
from novae import cost, grant, menu, offers

# Each jump offers the same three-way choice. It was a drawn node graph, then
# a generated route table; both cost more heap than a calculator can spare, and
# the decision -- heal, shop, or push for loot -- is what actually mattered.
JCH = ("PATROL", "ELITE PATROL", "TRADER", "REPAIR BAY", "", "WARLORD")
JCOL = (GRY, ORG, YLW, GRN, GRY, RED)
JHINT = ("CRYSTALS, AND A LITTLE TROUBLE", "HARDER. IT PAYS IN UPGRADES",
         "SPEND YOUR CRYSTALS HERE", "REPAIR 5 HULL, FREE", "",
         "THE SECTOR BOSS. GOOD LUCK.")


def choose():
    """Pick the next jump. Node 7 is always the sector boss."""
    n = S[NODE]
    if n >= 6:
        return 5
    opts = [0, 1, 2] if n & 1 else [0, 1, 3]
    panel("SECTOR %d   NODE %d" % (S[SECT] + 1, n + 1), SEC[S[SECT] % 5])
    ctr("%04d CRYSTALS   HULL %d/%d" % (S[CRY], S[HULL], S[HMAX]), 44, GRY)
    return opts[menu([JCH[t] for t in opts], [JCOL[t] for t in opts], 100,
                     [JHINT[t] for t in opts])]


def trade(free):
    """The trader, and the post-fight salvage pick: one list, either charged
    for or handed over. The line under the cursor says what the upgrade does."""
    ids = offers()
    if not ids:
        return
    while True:
        it = []
        co = []
        ft = []
        for i in ids:
            p = cost(i)
            can = free or S[CRY] >= p
            it.append("%-16s%s %s" % (SHOP[i][0], "" if free else "%3d" % p,
                                      "*" * UP[SHOP[i][1]]))
            co.append(CYN if free else (YLW if can else DRK))
            ft.append(SHOP[i][3] if can else "NEED %d CRYSTALS" % p)
        if free:
            panel("SALVAGE", CYN)
            ctr("CHOOSE ONE", 34, GRY)
            grant(SHOP[ids[menu(it, co, 90, ft)]][1])
            return
        it.append("LEAVE")
        co.append(WHT)
        ft.append("BACK TO THE JUMP MENU")
        panel("TRADER", YLW)
        txt("%04d" % S[CRY], 8, 30, CYN)
        c = menu(it, co, 70, ft)
        if c == 3:
            return
        i = ids[c]
        p = cost(i)
        if S[CRY] >= p and UP[SHOP[i][1]] < 3:
            S[CRY] -= p
            grant(SHOP[i][1])
