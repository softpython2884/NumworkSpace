"""A seed must reproduce a fight, exactly.

This test exists because it did not. Boss patterns and enemy behaviour drew
from the module-level `random` rather than from the run's own generator, so the
same seed won a run once and lost it the next two times. Nothing crashed and no
test failed -- the game was simply not reproducible, which meant the balance
bench had been reporting run-to-run noise as if it were the effect of a change,
and a seed in a bug report reproduced nothing.

So: drive the same fight twice from the same seed with the same inputs, hash
what happens, and require the hashes to match. Then drive it from a different
seed and require them *not* to match, because a test that passes on a constant
is not a test.

Particles, screen shake and the starfield are deliberately left on the global
generator: they cannot change the outcome of anything, and threading a seeded
generator through the particle pool would be churn for no property gained.
Nothing in the trace below looks at them.
"""

import hashlib
import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import pygame

from nova import data
from nova.art import Art
from nova.combat import Combat
from nova.run import Run

DT = 1 / 60.0
FRAMES = 900          # fifteen seconds, well past a boss's first phase change


def trace(kind, seed, sector, frames=FRAMES):
    """Fingerprint a fight: everything that decides how it goes, nothing else.

    The inputs are a fixed scripted weave rather than the test pilot, so the
    fingerprint depends on the game and not on the pilot's own arithmetic.
    """
    art = Art()
    art.load_fonts()
    run = Run(1, 1, seed=seed)
    run.sector = sector
    run.node = 6
    combat = Combat(run, kind, art)
    combat.intro_t = 0.0

    h = hashlib.sha256()
    for f in range(frames):
        # a repeatable weave across the arena
        dx = (1, 1, 0, -1, -1, 0)[(f // 37) % 6]
        dy = (0, -1, 0, 1)[(f // 53) % 4]
        combat.update(DT, {"move0": (dx, dy), "bomb": f % 611 == 610})
        if f % 5:
            continue
        parts = [len(combat.shots), len(combat.enemies), len(combat.bullets),
                 len(combat.pickups), run.hull, run.crystals, run.score]
        for s in combat.shots[:24]:
            parts += [int(s.x), int(s.y), int(s.vx), int(s.vy)]
        for e in combat.enemies[:12]:
            parts += [int(e.x), int(e.y), e.hp]
        b = combat.boss
        if b is not None:
            parts += [int(b.x), int(b.y), b.hp, b.phase, int(b.storming),
                      len(b.beams), len(b.turrets)]
        h.update(",".join(str(p) for p in parts).encode())
        if combat.result is not None:
            break
    return h.hexdigest()[:16]


def main():
    pygame.init()
    pygame.display.set_mode((data.W, data.H))
    ok = True

    # Every boss, not just one. The first version of this test traced only the
    # sector-2 boss and passed happily with a deliberately reintroduced bug --
    # HIVE MOTHER has no walls, so a wall's roll leaking onto the global
    # generator changed nothing it could see. A pattern that is not exercised
    # is not covered.
    cases = [("patrol", data.N_FIGHT, 1)]
    cases += [(data.BOSS_NAME[i].lower(), data.N_BOSS, i)
              for i in range(len(data.BOSS_NAME))]

    for label, kind, sector in cases:
        # The global generator is deliberately disturbed between the two runs.
        # Left undisturbed, a roll that leaks onto it would still line up and
        # the test would pass on the very bug it exists to catch.
        a = trace(kind, 4242, sector)
        for _ in range(98):
            random.random()
        b = trace(kind, 4242, sector)
        same = a == b
        print("  %-12s seed 4242 twice : %s %s  %s" %
              (label, a, b, "same" if same else "DIFFER"))
        if not same:
            print("     FAIL: the same seed did not reproduce the fight")
            ok = False

        # Sanity: the fingerprint must actually be sensitive to the seed.
        # Several alternates rather than one, because how much randomness a
        # fight consumes varies a lot by boss -- LANCE's opening rolls exactly
        # one die, its drift direction, so four seeds in a row can legitimately
        # produce the same fight. Requiring one specific seed to differ tests
        # the seed, not the game.
        others = [trace(kind, seed, sector) for seed in (99, 55, 7, 1234)]
        if all(o == a for o in others):
            print("     FAIL: no seed changed the trace -- the fingerprint is"
                  " not looking at anything")
            ok = False

    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
