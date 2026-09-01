"""A pilot for headless tests: dodges what is close, lines up on what is not."""

import math


class Bot:
    def __init__(self, combat, index=0):
        self.c = combat
        self.i = index

    def inputs(self):
        c = self.c
        me = None
        for p in c.players:
            if p.index == self.i and p.alive:
                me = p
        if me is None:
            return (0, 0), False

        # threat field: enemy shots and bodies, weighted by closeness
        dx = dy = 0.0
        danger = 0.0
        for s in c.shots:
            d = math.hypot(s.x - me.x, s.y - me.y)
            if d < 78 and s.y < me.y + 30:
                w = (78 - d) / 78
                danger += w
                dx -= (s.x - me.x) / max(d, 1) * w
                dy -= (s.y - me.y) / max(d, 1) * w
        for e in c.enemies:
            d = math.hypot(e.x - me.x, e.y - me.y)
            if d < 70:
                w = (70 - d) / 70
                danger += w
                dx -= (e.x - me.x) / max(d, 1) * w
                dy -= (e.y - me.y) / max(d, 1) * w

        # A boss is too big to ever be "safe"; drift under it anyway, or the
        # bot dodges forever and never fires on it. Aim at a live pod first --
        # the core is armoured until they are gone.
        boss = getattr(c, "boss", None)
        if boss is not None:
            target_x = boss.x
            pods = [p for p in getattr(boss, "pods", []) if p.alive]
            if pods:
                target_x = min(pods, key=lambda p: abs(p.x - me.x)).x
            dx += (target_x - me.x) / 60.0
            dy += 0.25
            # step out of a charging or firing beam
            for beam in getattr(boss, "beams", []):
                if abs(beam.x - me.x) < beam.width:
                    dx += 2.5 if me.x > beam.x else -2.5

        if danger < 0.25:
            # nothing pressing: grab loot, else get under a target
            target = None
            best = 1e9
            for pk in c.pickups:
                d = math.hypot(pk.x - me.x, pk.y - me.y)
                if d < best:
                    best, target = d, pk
            if target is None or best > 150:
                for e in c.enemies:
                    d = abs(e.x - me.x)
                    if d < best:
                        best, target = d, e
            if target is not None:
                dx = target.x - me.x
                dy = (target.y - me.y) * 0.25 if hasattr(target, "kind") else \
                     (target.y - me.y)
                # never chase an enemy upward into it
                if hasattr(target, "kind"):
                    dy = 0.35 if me.y < c.players[0].y else 0.0
                    dy = 0.0

        n = math.hypot(dx, dy)
        if n > 0.05:
            dx, dy = dx / n, dy / n
        else:
            dx = dy = 0.0
        step = lambda v: 1 if v > 0.35 else (-1 if v < -0.35 else 0)
        bomb = len(c.shots) + len(c.enemies) > 22
        return (step(dx), step(dy)), bomb


def drive(combat, players=1, max_seconds=180.0, dt=1 / 60):
    bots = [Bot(combat, i) for i in range(players)]
    t = 0.0
    while combat.result is None and t < max_seconds:
        inp = {}
        bomb = False
        for b in bots:
            mv, bb = b.inputs()
            inp["move%d" % b.i] = mv
            bomb = bomb or bb
        inp["bomb"] = bomb
        combat.update(dt, inp)
        t += dt
    return t
