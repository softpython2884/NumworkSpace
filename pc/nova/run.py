"""The state of one run: hull, crystals, upgrades, where you are on the map."""

import random

from . import data


class Run:
    def __init__(self, players=1, difficulty=1, seed=None):
        self.players = players
        self.difficulty = difficulty
        name, hull, budget, fire, _blurb = data.DIFFICULTIES[difficulty]
        self.diff_name = name
        self.budget_mult = budget
        self.fire_bonus = fire
        self.upgrades = [0] * data.UPGRADE_COUNT
        # Two ships are two things to hit but share one hull bar, so co-op
        # needs a deeper bar or it is strictly harder than solo.
        self.max_hull = hull + (5 if players > 1 else 0)
        self.hull = self.max_hull
        self.crystals = 0
        self.score = 0
        self.sector = 0
        self.node = 0
        self.max_bombs = 2
        self.bombs = 2
        self.cleared = False
        self.seed = seed if seed is not None else random.randrange(100000)
        self.rng = random.Random(self.seed)

    # --- upgrades --------------------------------------------------------
    def price(self, index):
        """Each level of the same upgrade costs half again as much, which
        nudges the player to broaden a build rather than stack one stat."""
        base = data.SHOP[index][2]
        return base + (base * self.upgrades[data.SHOP[index][1]]) // 2

    def can_buy(self, index):
        return (self.upgrades[data.SHOP[index][1]] < 3
                and self.crystals >= self.price(index))

    def grant(self, upgrade):
        self.upgrades[upgrade] += 1
        if upgrade == data.U_HULL:
            self.max_hull += 2
            self.hull = min(self.max_hull, self.hull + 2)
        elif upgrade == data.U_BOMB:
            self.max_bombs += 1
            self.bombs += 1

    def offers(self, count=3):
        pool = [i for i in range(len(data.SHOP))
                if self.upgrades[data.SHOP[i][1]] < 3]
        self.rng.shuffle(pool)
        return pool[:count]

    # --- healing ---------------------------------------------------------
    def heal(self, amount):
        self.hull = min(self.max_hull, self.hull + amount)

    def enter_node(self):
        self.bombs = self.max_bombs

    def enter_sector(self):
        """Nanorepair, once a sector.

        It used to run at every node: +1 hull per level, six nodes a sector,
        for as long as the run lasted. The Void has no end, so neither did
        that -- a maxed nanorepair outhealed everything the game could do,
        which is not an upgrade, it is an off switch.
        """
        if self.upgrades[data.U_REGEN]:
            self.heal(2 * self.upgrades[data.U_REGEN])

    def crystal_value(self):
        return 2 + self.upgrades[data.U_GREED]
