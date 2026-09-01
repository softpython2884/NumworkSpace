"""Ships, shots and pickups.

Everything moves in pixels per second and is stepped by delta time, so the game
runs at the same speed whatever the monitor does. (The calculator build capped
the frame rate instead and worked in whole pixels per frame -- it had no
floating point budget to spare.)
"""

import math
import random

from . import data


class Bullet:
    __slots__ = ("x", "y", "vx", "vy", "dmg", "pierce", "hit", "w", "h")

    def __init__(self, x, y, vx, vy, dmg, pierce):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.dmg = dmg
        self.pierce = pierce
        self.hit = set()      # enemies already pierced, so each is hit once
        self.w = 2
        self.h = 6

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

    @property
    def alive(self):
        return (data.TOP - 24 < self.y < data.BOT + 20
                and data.PLAY_L - 20 < self.x < data.PLAY_R + 20)


class EnemyBullet:
    __slots__ = ("x", "y", "vx", "vy", "r")

    def __init__(self, x, y, vx, vy, r=2):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.r = r

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

    @property
    def alive(self):
        return (data.TOP - 40 < self.y < data.BOT + 20
                and data.PLAY_L - 20 < self.x < data.PLAY_R + 20)


class EnemyBeam:
    """A lancer's beam: LANCE's mechanic, bolted to something you can kill.

    Same contract as the boss's -- it locks where it aimed when the charge
    began, so it is always dodgeable and never arbitrary -- but it hangs off a
    mortal ship. Kill the lancer mid-charge and the beam goes with it, which is
    the whole reason for putting a boss attack on a regular enemy: it turns
    into a target priority instead of a weather condition.
    """

    CHARGE = 0.85
    FIRE = 0.5
    FADE = 0.2
    WIDTH = 9

    __slots__ = ("x", "y", "t")

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.t = 0.0

    def update(self, dt):
        self.t += dt

    @property
    def firing(self):
        return self.CHARGE <= self.t < self.CHARGE + self.FIRE

    @property
    def done(self):
        return self.t >= self.CHARGE + self.FIRE + self.FADE

    def rect(self):
        half = self.WIDTH / 2
        return (self.x - half, self.y, self.WIDTH, data.BOT - self.y)

    def draw(self, surf):
        top = int(self.y)
        h = data.BOT - top
        if h <= 0:
            return
        if self.t < self.CHARGE:
            frac = self.t / self.CHARGE
            if int(self.t * (7 + 20 * frac)) % 2:
                w = max(1, int(1 + frac * 3))
                surf.fill(data.ORANGE, (int(self.x - w / 2), top, w, h))
            return
        if self.firing:
            w = self.WIDTH
            surf.fill(data.ORANGE, (int(self.x - w / 2), top, w, h))
            surf.fill(data.WHITE, (int(self.x - 2), top, 4, h))
            return
        frac = 1.0 - (self.t - self.CHARGE - self.FIRE) / self.FADE
        w = max(1, int(self.WIDTH * frac * 0.5))
        surf.fill(data.ORANGE, (int(self.x - w / 2), top, w, h))


class Pickup:
    """Crystals and hull patches, back from the calculator's cutting-room floor."""

    __slots__ = ("x", "y", "vx", "vy", "kind", "life")

    def __init__(self, x, y, kind=0, rng=None):
        self.x = x
        self.y = y
        rng = rng or random
        self.vx = rng.uniform(-24, 24)
        self.vy = rng.uniform(-40, -8)
        self.kind = kind          # 0 crystal, 1 hull
        self.life = 11.0

    def update(self, dt, magnet, targets):
        self.life -= dt
        if magnet:
            best = None
            bd = 1e9
            for t in targets:
                d = (t.x - self.x) ** 2 + (t.y - self.y) ** 2
                if d < bd:
                    bd, best = d, t
            if best is not None and bd < (110 + 70 * magnet) ** 2:
                a = math.atan2(best.y - self.y, best.x - self.x)
                pull = 300 + 150 * magnet
                self.vx += math.cos(a) * pull * dt
                self.vy += math.sin(a) * pull * dt
        self.vy += 62 * dt                      # drifts downward
        self.vx *= 1.0 - 0.9 * dt
        self.vy = min(self.vy, 150)
        self.x += self.vx * dt
        self.y += self.vy * dt

    @property
    def alive(self):
        return self.life > 0 and self.y < data.BOT + 16


class Player:
    __slots__ = ("x", "y", "index", "cooldown", "invuln", "shield", "shield_t",
                 "w", "h", "alive", "thrust", "was_shielded")

    SPEED = 165.0

    def __init__(self, index, x):
        self.index = index
        self.x = x
        self.y = data.BOT - 40
        self.cooldown = 0.0
        self.invuln = 0.0
        self.shield = False
        self.shield_t = 0.0
        self.w = 13
        self.h = 17
        self.alive = True
        self.thrust = 0.0
        self.was_shielded = False

    def rect(self):
        # A forgiving hitbox: narrower and shorter than the sprite, as any
        # decent shmup does.
        return (self.x - 3, self.y - 4, 6, 9)

    def update(self, dt, dx, dy, upgrades):
        speed = Player.SPEED * (1.0 + 0.18 * upgrades[data.U_SPEED])
        if dx and dy:
            k = 0.7071
            dx *= k
            dy *= k
        self.x += dx * speed * dt
        self.y += dy * speed * dt
        # Bounded by the arena, not the canvas: on an ultrawide the extra
        # canvas is scenery, and flying out into it would change the game.
        self.x = max(data.PLAY_L + 8, min(data.PLAY_R - 8, self.x))
        # Ships stay in the lower part of the arena: classic vertical shmup
        # framing, and it keeps the enemy approach readable.
        arena_h = data.BOT - data.TOP
        self.y = max(data.TOP + arena_h * 0.4, min(data.BOT - 12, self.y))
        self.thrust = 1.0 if dy < 0 else (0.35 if dy > 0 else 0.7)
        if self.invuln > 0:
            self.invuln -= dt
        if upgrades[data.U_SHIELD] and not self.shield:
            self.shield_t -= dt
            if self.shield_t <= 0:
                self.shield = True
        self.cooldown -= dt

    def can_fire(self):
        return self.cooldown <= 0

    def fire(self, upgrades):
        """Auto-fire, kept from the calculator version: it is the identity of
        the game, and it leaves both hands free for dodging."""
        rate = 0.16 * (0.85 ** upgrades[data.U_RATE])
        self.cooldown = rate
        dmg = 1 + upgrades[data.U_DMG]
        pierce = upgrades[data.U_PIERCE] > 0
        speed = -430.0 * (1.0 + 0.25 * upgrades[data.U_BULLET])
        barrels = min(upgrades[data.U_SPREAD], 3)
        out = []
        for ox, ang in SPREADS[barrels]:
            out.append(Bullet(self.x + ox, self.y - 8,
                              math.sin(ang) * -speed, math.cos(ang) * speed,
                              dmg, pierce))
        return out

    def take_hit(self):
        """True if this cost hull; False if the deflector ate it."""
        if self.shield:
            self.shield = False
            self.shield_t = 8.0
            self.invuln = 0.6
            return False
        self.invuln = 1.4
        return True


SPREADS = (
    ((0, 0.0),),
    ((-4, 0.0), (4, 0.0)),
    ((-6, -0.10), (0, 0.0), (6, 0.10)),
    ((-8, -0.16), (-3, -0.05), (3, 0.05), (8, 0.16)),
)


class Enemy:
    __slots__ = ("x", "y", "kind", "hp", "max_hp", "t", "fire_t", "anchor",
                 "drift", "w", "h", "flash", "phase", "score", "rng",
                 "beam", "dash_t", "dash_vx", "dash_vy")

    def __init__(self, kind, x, y, hp, sector, rng=None):
        self.kind = kind
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = hp
        self.rng = rng or random
        self.t = self.rng.uniform(0, 6.0)
        self.fire_t = self.rng.uniform(0.4, 1.8)
        self.anchor = data.TOP + 40 + self.rng.uniform(
            0, (data.BOT - data.TOP) * 0.28)
        self.drift = self.rng.choice((-1, 1)) * self.rng.uniform(30, 62)
        self.flash = 0.0
        self.phase = 0
        self.score = data.ENEMY_SCORE[kind]
        self.w, self.h = ENEMY_SIZE[kind]
        self.beam = None                 # lancers only
        self.dash_t = 0.0                # phantoms only
        self.dash_vx = 0.0
        self.dash_vy = 0.0

    def rect(self):
        return (self.x - self.w / 2, self.y - self.h / 2, self.w, self.h)

    def update(self, dt, target_x):
        self.t += dt
        if self.flash > 0:
            self.flash -= dt
        k = self.kind
        speed = data.ENEMY_SPEED[k]
        if k == data.WEAVER_ID:
            self.x += math.sin(self.t * 2.4) * 78 * dt
            self.y += speed * dt
        elif k == data.TURRET_ID:
            if self.y < self.anchor:
                self.y += speed * dt
            else:
                # The anchor sinks -- the fix that stopped turrets from camping
                # forever on the calculator. Same rule here: nothing can stall
                # a fight by being ignorable.
                self.anchor += 11 * dt
                self.y += 11 * dt
                self.x += math.sin(self.t * 1.1) * 26 * dt
        elif k == data.LANCER_ID:
            # Slides to its station, then works a charge-fire cycle. It never
            # descends past the anchor: a beam is only fair if you can see
            # where it will be, and one falling on top of you is not that.
            if self.y < self.anchor:
                self.y += speed * dt
            else:
                self.x += math.sin(self.t * 0.9) * 22 * dt
                self.anchor += 6 * dt
                self.y += 6 * dt
            if self.beam is not None:
                # The beam does not follow the ship: it stays where it aimed
                # when the charge began, which is the whole telegraph.
                self.beam.update(dt)
                if self.beam.done:
                    self.beam = None
                    self.fire_t = self.rng.uniform(1.3, 2.1)
            else:
                self.fire_t -= dt
                if self.fire_t <= 0 and self.y > data.TOP + 8:
                    self.beam = EnemyBeam(target_x, self.y + 6)
        elif k == data.SPINNER_ID:
            # Drifts in slowly and turns. Its rings are the one attack in the
            # roster that does not care where you are, which is what makes it
            # awkward next to everything that does.
            self.y += speed * dt
            self.x += math.sin(self.t * 1.6) * 34 * dt
        elif k == data.PHANTOM_ID:
            # The Void's answer to a maxed rate of fire: it will not stand
            # still to be hit. Lining up under it is the trigger, so parking
            # beneath one and holding the trigger -- which is what a stock
            # shmup rewards by then -- is exactly what does not work.
            if self.dash_t > 0:
                self.dash_t -= dt
                self.x += self.dash_vx * dt
                self.y += self.dash_vy * dt
            else:
                self.y += speed * dt
                lined_up = abs(self.x - target_x) < 26
                self.fire_t -= dt * (2.2 if lined_up else 1.0)
                if lined_up and self.t > 0.7:
                    self.t = 0.0
                    self.dash_t = 0.24
                    if self.rng.random() < 0.45:
                        # backwards, out of the firing lane entirely
                        self.dash_vy = -260.0
                        self.dash_vx = self.rng.choice((-1, 1)) * 90.0
                    else:
                        away = 1.0 if self.x > target_x else -1.0
                        self.dash_vx = away * 300.0
                        self.dash_vy = -40.0
        elif k == data.BOSS_ID:
            self.x += self.drift * dt
            if self.x < data.PLAY_L + 60 or self.x > data.PLAY_R - 60:
                self.drift = -self.drift
            # It holds the top of the screen and never descends. Dropping it
            # onto the player looked like good pressure and was the opposite:
            # once the boss sits below the ship, shots that only travel upward
            # can never reach it. The pressure comes from enrage instead.
            self.y = min(data.TOP + 46, self.y + 26 * dt)
            self.phase = 0 if self.hp > self.max_hp * 0.6 else (
                1 if self.hp > self.max_hp * 0.25 else 2)
        else:
            self.y += speed * dt
        self.x = max(data.PLAY_L + 6, min(data.PLAY_R - 6, self.x))
        if k == data.PHANTOM_ID:
            # A dash backwards must not park it off the top, where nothing can
            # reach it and it stops being a fight.
            self.y = max(data.TOP + 10, self.y)

    def wants_to_fire(self, dt, haste=1.0):
        """`haste` is the difficulty tier's contribution.

        It used to change only the muzzle velocity, which is barely a
        difficulty setting at all: ACE fielded more enemies than PILOT, and
        more enemies meant more salvage, so the hard tier bought the player a
        better ship and won more often than the easy one. Rate of fire is the
        knob that costs the player something without paying them back.
        """
        rate = data.ENEMY_FIRE[self.kind]
        if rate <= 0:
            return False
        rate /= haste
        if self.kind == data.BOSS_ID and self.t > 40.0:
            # Enrage: a stalled boss fight gets faster, not longer. This is what
            # bounds the fight -- either it dies or you do.
            rate *= max(0.32, 1.0 - (self.t - 40.0) * 0.022)
        self.fire_t -= dt
        if self.fire_t <= 0:
            self.fire_t = rate * self.rng.uniform(0.75, 1.3)
            return True
        return False

    def volley(self, tx, ty, difficulty):
        """Enemy shot patterns. The boss cycles through three as it loses hull,
        which is the sort of thing a 32 KB heap could never hold."""
        k = self.kind
        out = []
        base = 108 + 26 * difficulty
        ang = math.atan2(ty - self.y, tx - self.x)
        if k == data.BOSS_ID:
            if self.phase == 0:
                for i in (-1, 0, 1):
                    a = ang + i * 0.22
                    out.append(EnemyBullet(self.x, self.y + 10,
                                           math.cos(a) * base, math.sin(a) * base, 3))
            elif self.phase == 1:
                for i in range(7):
                    a = math.pi / 2 + (i - 3) * 0.26
                    out.append(EnemyBullet(self.x, self.y + 10,
                                           math.cos(a) * base, math.sin(a) * base, 2))
            else:
                spin = self.t * 2.1
                for i in range(9):
                    a = spin + i * (math.tau / 9)
                    out.append(EnemyBullet(self.x, self.y + 6,
                                           math.cos(a) * base * 0.8,
                                           math.sin(a) * base * 0.8, 2))
        elif k == data.SPINNER_ID:
            spin = self.t * 1.7
            for i in range(6):
                a = spin + i * (math.tau / 6)
                out.append(EnemyBullet(self.x, self.y,
                                       math.cos(a) * base * 0.66,
                                       math.sin(a) * base * 0.66, 2))
        elif k == data.PHANTOM_ID:
            for i in (-1, 1):
                a = ang + i * 0.1
                out.append(EnemyBullet(self.x, self.y + 4,
                                       math.cos(a) * base * 1.15,
                                       math.sin(a) * base * 1.15, 2))
        elif k == data.TANK_ID:
            for i in (-1, 1):
                a = ang + i * 0.16
                out.append(EnemyBullet(self.x + i * 6, self.y + 6,
                                       math.cos(a) * base, math.sin(a) * base, 3))
        else:
            out.append(EnemyBullet(self.x, self.y + 6,
                                   math.cos(ang) * base, math.sin(ang) * base, 2))
        return out

    @property
    def alive(self):
        if self.hp <= 0:
            return False
        # A boss is never removed for drifting off-screen: it has to be killed.
        return self.kind == data.BOSS_ID or self.y < data.BOT + 30


ENEMY_SIZE = ((11, 11), (11, 11), (11, 12), (11, 13), (17, 13), (37, 17),
              (11, 10), (11, 11), (11, 9))


def overlaps(a, b):
    return (a[0] < b[0] + b[2] and a[0] + a[2] > b[0] and
            a[1] < b[1] + b[3] and a[1] + a[3] > b[1])
