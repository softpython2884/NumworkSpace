"""A pilot for headless tests.

The first version was a repulsion field: sum up a vector away from every nearby
bullet and fly along it. That works against aimed fire and fails completely
against everything a bullet-hell pattern is made of. A wall with one gap pushes
it sideways along the wall rather than into the hole; a spiral surrounds it, so
the vectors cancel and it sits still and dies. Measuring boss difficulty with
that pilot meant measuring how unreadable a pattern was to a bad heuristic, and
the first thing it would have told me is to delete the good attacks.

So it dodges the way a person does: consider each direction the stick can
actually go, work out how close the nearest bullet would get if you went that
way, and take the best one. Closest approach is computed properly -- relative
position against relative velocity -- because a bullet that is close now but
moving away is not a threat, and one that is far but converging is.

It has perfect information and perfect reaction, and no memory at all: it never
learns that a pattern repeats. A good human is worse at the first and much
better at the second, which is roughly the right error to have when the numbers
are being used to set difficulty.
"""

import math

from nova import data

# Nine sticks: the eight directions plus standing still.
MOVES = ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1),
         (1, 1), (1, -1), (-1, 1), (-1, -1))

HORIZON = 0.5        # seconds of future to look at
CLEAR = 15.0         # a bullet passing closer than this is a problem
CONSIDER = 150.0     # ignore bullets further away than this
AIM = 0.25           # weight on lining up with the target


class Bot:
    def __init__(self, combat, index=0):
        self.c = combat
        self.i = index

    def me(self):
        for p in self.c.players:
            if p.index == self.i and p.alive:
                return p
        return None

    def threats(self, me):
        """Bullets and bodies worth thinking about, as (x, y, vx, vy, radius)."""
        out = []
        for s in self.c.shots:
            if abs(s.x - me.x) < CONSIDER and abs(s.y - me.y) < CONSIDER:
                out.append((s.x, s.y, s.vx, s.vy, s.r + 4.0))
        for e in self.c.enemies:
            # Enemies hold a station and weave; 40 px/s downward is close
            # enough for a half-second look-ahead, and being wrong about it
            # only makes the pilot keep its distance.
            if abs(e.x - me.x) < CONSIDER and abs(e.y - me.y) < CONSIDER:
                out.append((e.x, e.y, 0.0, 40.0, 12.0))
        boss = getattr(self.c, "boss", None)
        if boss is not None:
            for beam in boss.beams:
                # a beam is a column, not a point: model it as a very wide,
                # stationary threat sitting at the player's own height
                if beam.t > beam.CHARGE * 0.45:
                    out.append((beam.x, me.y, 0.0, 0.0, beam.width * 0.5 + 8.0))
        # Lancers carry the same attack on a killable ship. A pilot that cannot
        # see them would rate the enemy by how invisible it is to a heuristic,
        # which is exactly the mistake the repulsion field made.
        for e in self.c.enemies:
            b = e.beam
            if b is not None and b.t > b.CHARGE * 0.45 and b.y < me.y:
                out.append((b.x, me.y, 0.0, 0.0, b.WIDTH * 0.5 + 8.0))
        return out

    def cost(self, px, py, vx, vy, threats):
        """How dangerous is holding this stick for the next half second.

        `px, py` is where the ship is *now*, not where the move would put it:
        integrating the move first and then looking a further half second
        ahead skips over the interval the ship actually has to survive, which
        is exactly the interval a bullet arrives in.
        """
        worst = 0.0
        for (bx, by, bvx, bvy, r) in threats:
            rx, ry = bx - px, by - py
            dvx, dvy = bvx - vx, bvy - vy
            vv = dvx * dvx + dvy * dvy
            if vv < 1e-6:
                t = 0.0
            else:
                t = -(rx * dvx + ry * dvy) / vv
                t = max(0.0, min(HORIZON, t))
            cx, cy = rx + dvx * t, ry + dvy * t
            d = math.hypot(cx, cy) - r
            if d < CLEAR:
                # nearer misses hurt disproportionately, and sooner is worse
                gap = CLEAR - d
                worst += gap * gap * (1.0 + (HORIZON - t))
        return worst

    def inputs(self):
        c = self.c
        me = self.me()
        if me is None:
            return (0, 0), False

        threats = self.threats(me)
        speed = me.SPEED * (1.0 + 0.18 * c.run.upgrades[data.U_SPEED])

        # Where we would rather be, all else equal: under a pickup, else under
        # whatever we are shooting at. A live pod first -- the core is armoured
        # until they are gone.
        want_x, pull = me.x, 0.0
        boss = getattr(c, "boss", None)
        if boss is not None:
            want_x = boss.x
            pods = [p for p in getattr(boss, "pods", []) if p.alive]
            if pods:
                want_x = min(pods, key=lambda p: abs(p.x - me.x)).x
            pull = 1.0
        best = None
        for pk in c.pickups:
            d = math.hypot(pk.x - me.x, pk.y - me.y)
            if best is None or d < best[0]:
                best = (d, pk)
        if best is not None and best[0] < 140:
            want_x, pull = best[1].x, 1.4
        elif boss is None and c.enemies:
            near = min(c.enemies, key=lambda e: abs(e.x - me.x))
            want_x, pull = near.x, 1.0

        lo_x, hi_x = data.PLAY_L + 8, data.PLAY_R - 8
        lo_y = data.TOP + (data.BOT - data.TOP) * 0.4
        hi_y = data.BOT - 12
        best_move, best_score = (0, 0), None
        for (mx, my) in MOVES:
            k = 0.7071 if (mx and my) else 1.0
            vx, vy = mx * speed * k, my * speed * k
            # where the move would actually end up, walls included
            ex = max(lo_x, min(hi_x, me.x + vx * HORIZON))
            ey = max(lo_y, min(hi_y, me.y + vy * HORIZON))
            score = self.cost(me.x, me.y, vx, vy, threats)
            # A move into a wall does not move: charge it the distance it
            # promised and did not deliver, or the pilot will happily "escape"
            # into the edge of the arena and stand there.
            blocked = (abs(me.x + vx * HORIZON - ex)
                       + abs(me.y + vy * HORIZON - ey))
            score += blocked * 1.5
            # tie-breakers: line up on the target, and prefer the lower half of
            # the arena, where there is room to react
            score += abs(ex - want_x) * AIM * pull
            score += max(0.0, (hi_y - 30) - ey) * 0.02
            if best_score is None or score < best_score:
                best_move, best_score = (mx, my), score

        # The bomb is the panic button, and a scripted pilot should use it the
        # way a player does: when the screen is genuinely unsurvivable.
        bomb = (best_score is not None and best_score > 900.0) or \
            len(c.shots) + len(c.enemies) > 26
        return best_move, bomb


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
