"""Play whole runs headless, through the real state machine.

Nothing is stubbed but the display: the same Game object, the same key events,
the same combat. If a screen can dead-end or a transition can drop the run on
the floor, this is what finds it.
"""

import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import pygame

from bot import Bot
from nova import data
from nova.game import (COMBAT, EVENT, GAMEOVER, INTERLUDE, MAP, REST, TITLE,
                       TRADER, Game)

DT = 1 / 60.0

# Shared by tools/balance.py, which builds a Combat directly to read boss hit
# points without playing a fight.
from nova import entities as ent          # noqa: E402
from nova.art import Art                  # noqa: E402
from nova.combat import Combat            # noqa: E402
from nova.run import Run                  # noqa: E402

ART = Art()


def press(game, key):
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0))


class Driver:
    """Walks a run: picks routes, shops, and flies the fights."""

    def __init__(self, game, players=1, max_sectors=5, rng=None):
        self.g = game
        self.players = players
        self.max_sectors = max_sectors
        self.rng = rng or random.Random(0)
        self.fights = 0
        self.frames = 0
        self.log = []

    def choose_route(self):
        g = self.g
        opts = g.map.options()
        kinds = [g.map.nodes[o] for o in opts]
        # heal when hurt, shop when rich, otherwise take the fight
        want = None
        if g.run.hull <= g.run.max_hull * 0.5 and data.N_REST in kinds:
            want = kinds.index(data.N_REST)
        elif g.run.crystals >= 55 and data.N_SHOP in kinds:
            want = kinds.index(data.N_SHOP)
        if want is None:
            want = 0
        for _ in range((want - g.sel_index) % len(opts)):
            press(g, pygame.K_DOWN)
        press(g, pygame.K_RETURN)

    def shop(self):
        g = self.g
        if g.free_pick:
            press(g, pygame.K_RETURN)
            return
        # Try something unaffordable first when there is one: the refusal path
        # has its own feedback, and nothing else in a scripted run exercises it.
        blocked = [i for i, ok in enumerate(g.menu.enabled[:-1]) if not ok]
        if blocked:
            for _ in range((blocked[0] - g.menu.index) % len(g.menu.items)):
                press(g, pygame.K_DOWN)
            press(g, pygame.K_RETURN)
        for _ in range(6):
            buyable = [i for i, ok in enumerate(g.menu.enabled[:-1]) if ok]
            if not buyable:
                break
            target = buyable[0]
            for _ in range((target - g.menu.index) % len(g.menu.items)):
                press(g, pygame.K_DOWN)
            press(g, pygame.K_RETURN)
            if g.state != TRADER:
                return
        while g.menu.index != len(g.menu.items) - 1:
            press(g, pygame.K_DOWN)
        press(g, pygame.K_RETURN)

    def fly(self):
        g = self.g
        c = g.combat
        bots = [Bot(c, i) for i in range(self.players)]
        hull0 = g.run.hull
        t = 0.0
        while g.state == COMBAT and t < 240.0:
            inp = {}
            bomb = False
            for b in bots:
                mv, bb = b.inputs()
                inp["move%d" % b.i] = mv
                bomb = bomb or bb
            inp["bomb"] = bomb
            c.update(DT, inp)
            if c.result is not None:
                g.after_combat(c.result)
                break
            t += DT
            self.frames += 1
        self.fights += 1
        self.log.append((g.run.sector, g.run.node, c.kind, round(t, 1),
                         hull0, hull0 - g.run.hull, c.result))
        if t >= 240.0:
            raise RuntimeError("fight did not terminate: sector %d kind %d"
                               % (g.run.sector, c.kind))

    def play(self):
        g = self.g
        guard = 0
        while g.state != GAMEOVER and g.run.sector < self.max_sectors:
            guard += 1
            if guard > 400:
                raise RuntimeError("run made no progress: state %d" % g.state)
            if g.state == MAP:
                self.choose_route()
            elif g.state == COMBAT:
                self.fly()
            elif g.state == TRADER:
                self.shop()
            elif g.state == EVENT:
                if self.rng.random() < 0.5:
                    press(g, pygame.K_DOWN)
                press(g, pygame.K_RETURN)
            elif g.state == REST:
                press(g, pygame.K_RETURN)
            elif g.state == INTERLUDE:
                if g.run.sector >= self.max_sectors:
                    break
                press(g, pygame.K_RETURN)
            else:
                raise RuntimeError("unexpected state %d" % g.state)
        return g.state != GAMEOVER


def run_once(seed, players=1, difficulty=1):
    g = Game(scale=1, crt=False)
    g.difficulty = difficulty
    g.start_run(players)
    g.run.seed = seed
    g.run.rng = random.Random(seed)
    g.map = None
    g.new_sector()
    d = Driver(g, players, rng=random.Random(seed))
    won = d.play()
    return {"won": won, "sector": g.run.sector, "score": g.run.score,
            "hull": g.run.hull, "max_hull": g.run.max_hull,
            "crystals": g.run.crystals, "upgrades": list(g.run.upgrades),
            "fights": d.fights, "minutes": d.frames * DT / 60.0, "log": d.log}


def test_boss_entrance():
    """A boss must not be damageable while it is holding fire.

    It keeps its guns quiet for the length of its name card, and the player's
    do not stop: a ship parked underneath landed 5 to 25% of the boss's hull
    before the fight began, depending on sector and loadout. Free damage
    against something that cannot answer is a gap in the rules, not a reward.

    Pods count. Shielding the core and leaving BULWARK's turrets exposed would
    just move the same trick onto two of the five bosses.
    """
    from nova.art import Art
    from nova.combat import Combat
    from nova.run import Run
    art = Art()
    art.load_fonts()
    loadouts = ({}, {data.U_SPREAD: 3, data.U_RATE: 3, data.U_DMG: 3,
                     data.U_PIERCE: 1})
    for sector in range(5):
        for ups in loadouts:
            run = Run(1, 1, seed=5)
            run.sector = sector
            for u, v in ups.items():
                run.upgrades[u] = v
            c = Combat(run, data.N_BOSS, art)
            start = c.boss.max_hp
            pods = [p.hp for p in c.boss.pods]
            p = c.players[0]
            while c.intro_t > 0 and c.boss is not None:
                p.x = c.boss.x          # parked underneath, holding fire
                c.update(DT, {"move0": (0, 0), "bomb": False})
            assert c.boss is not None, "boss died during its own entrance"
            assert c.boss.hp == start, (
                "sector %d: boss lost %d hull before it acted"
                % (sector + 1, start - c.boss.hp))
            assert [p.hp for p in c.boss.pods] == pods, (
                "sector %d: a pod was damaged before the boss acted" % (sector + 1))
    print("  boss entrance: shielded until it can answer")
    return True


def test_maxed_trader():
    """A fully upgraded ship must not break the shop.

    Deep in the Void every upgrade can be at level 3, leaving nothing to offer.
    """
    import random as _r
    from nova import data
    from nova.game import GAMEOVER, REST, TRADER
    g = Game(scale=1, crt=False, sound=False)
    g.start_run(1)
    g.run.rng = _r.Random(1)
    for i in range(data.UPGRADE_COUNT):
        g.run.upgrades[i] = 3
    g.run.crystals = 500
    for free in (False, True):
        g.enter_trader(free=free)
        assert g.state in (TRADER, REST), "unexpected state %d" % g.state
        if g.state == TRADER:
            assert g.menu.items, "empty trader menu"
        else:
            g.draw_message(g.canvas)          # must not raise
    return True


def main():
    seeds = (1, 7, 42, 101, 777, 2024, 31415, 60007)
    print("=== solo runs, %s ===" % data.DIFFICULTIES[1][0])
    print("%6s %8s %9s %7s %9s %8s" %
          ("seed", "result", "score", "fights", "hull", "minutes"))
    wins = 0
    mins = []
    for s in seeds:
        r = run_once(s)
        wins += r["won"]
        mins.append(r["minutes"])
        print("%6d %8s %9d %7d %9s %8.1f" %
              (s, "WON" if r["won"] else "S%d" % (r["sector"] + 1), r["score"],
               r["fights"], "%d/%d" % (r["hull"], r["max_hull"]), r["minutes"]))

    print("\n=== difficulty curve ===")
    for d, (name, _h, _b, _f, _blurb) in enumerate(data.DIFFICULTIES):
        w = sum(run_once(s, difficulty=d)["won"] for s in seeds)
        print("  %-6s %d/%d runs won" % (name, w, len(seeds)))

    print("\n=== co-op ===")
    for s in (42, 101):
        r = run_once(s, players=2)
        print("  seed %-6d %-4s score %d  %.1f min" %
              (s, "WON" if r["won"] else "S%d" % (r["sector"] + 1),
               r["score"], r["minutes"]))

    print()
    print("=== edge cases ===")
    test_boss_entrance()
    test_maxed_trader()
    print("  fully-upgraded ship: trader and salvage both handled")

    print()
    print("solo win rate    : %d/%d" % (wins, len(seeds)))
    print("average run time : %.1f min of combat" % (sum(mins) / len(mins)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
