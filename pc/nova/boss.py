"""Five bosses, five ideas.

The first PC build had one boss reskinned per sector, which meant the fight
that should be a sector's punchline was the same fight every time. Each of
these owns a mechanic instead:

    SENTINEL     fans of fire; read the gaps
    HIVE MOTHER  opens its bays and sends escorts
    LANCE        charges a beam, telegraphs it, then fires
    BULWARK      two turret pods armour the core until you break them
    WARDEN       pods, beam and escorts together, over three phases

They share a body: drift, hit points, phases by remaining hull. What differs is
`act`, which is dispatched once per frame and is the only place a boss's
personality lives.
"""

import math
import random

import pygame

from . import data
from . import entities as ent

SENTINEL, HIVE, LANCE, BULWARK, WARDEN = range(5)
BOSS_COUNT = 5


class Beam:
    """A vertical column of death, with a warning first.

    The telegraph is the mechanic: the beam is fixed where it was aimed when
    charging began, so it is always dodgeable and never feels arbitrary.
    """

    CHARGE = 1.15
    FIRE = 1.35
    FADE = 0.3

    def __init__(self, x, width=26):
        self.x = x
        self.width = width
        self.t = 0.0

    def update(self, dt):
        self.t += dt

    @property
    def firing(self):
        return self.CHARGE <= self.t < self.CHARGE + self.FIRE

    @property
    def done(self):
        return self.t >= self.CHARGE + self.FIRE + self.FADE

    def rect(self, top):
        half = self.width / 2
        return (self.x - half, top, self.width, data.BOT - top)

    def draw(self, surf, top):
        if self.t < self.CHARGE:
            # charging: a thin line that pulses faster as it fills
            frac = self.t / self.CHARGE
            if int(self.t * (6 + 18 * frac)) % 2:
                w = max(1, int(2 + frac * 4))
                surf.fill(data.RED, (int(self.x - w / 2), top, w,
                                     data.BOT - top))
            return
        if self.firing:
            w = self.width
            surf.fill(data.RED_D, (int(self.x - w / 2), top, w, data.BOT - top))
            surf.fill(data.RED, (int(self.x - w / 2) + 3, top, w - 6,
                                 data.BOT - top))
            surf.fill(data.WHITE, (int(self.x - 3), top, 6, data.BOT - top))
            return
        # fading
        frac = 1.0 - (self.t - self.CHARGE - self.FIRE) / self.FADE
        w = max(1, int(self.width * frac * 0.5))
        surf.fill(data.RED, (int(self.x - w / 2), top, w, data.BOT - top))


class Pod:
    """A turret bolted to a boss. Armours the core while it lives."""

    def __init__(self, offset_x, offset_y, hp):
        self.ox = offset_x
        self.oy = offset_y
        self.hp = hp
        self.max_hp = hp
        self.flash = 0.0
        self.fire_t = random.uniform(0.5, 1.6)
        self.w = 11
        self.h = 7
        self.x = 0.0
        self.y = 0.0

    @property
    def alive(self):
        return self.hp > 0

    def rect(self):
        return (self.x - self.w / 2, self.y - self.h / 2, self.w, self.h)


class Boss:
    def __init__(self, index, sector, hp, x, y):
        self.index = index % BOSS_COUNT
        self.sector = sector
        self.hp = hp
        self.max_hp = hp
        self.x = x
        self.y = y
        self.t = 0.0
        self.fire_t = 1.2
        self.drift = random.choice((-1, 1)) * 34.0
        self.flash = 0.0
        self.phase = 0
        self.w = 37
        self.h = 17
        self.score = data.ENEMY_SCORE[data.BOSS_ID]
        self.beams = []
        self.pods = []
        self.spawn_t = 3.0
        self.state_t = 0.0
        self.enraged = False
        if self.index in (BULWARK, WARDEN):
            pod_hp = max(8, hp // 6)
            self.pods = [Pod(-34, 5, pod_hp), Pod(34, 5, pod_hp)]

    # -- helpers ----------------------------------------------------------
    @property
    def name(self):
        return data.BOSS_NAME[self.index]

    @property
    def tell(self):
        return data.BOSS_TELL[self.index]

    @property
    def shielded(self):
        """BULWARK and WARDEN take reduced damage while a pod stands."""
        return any(p.alive for p in self.pods)

    def rect(self):
        return (self.x - self.w / 2, self.y - self.h / 2, self.w, self.h)

    def live_pods(self):
        return [p for p in self.pods if p.alive]

    def take_hit(self, dmg):
        """Returns the damage actually dealt."""
        if self.shielded:
            dmg = max(1, dmg // 4)
        self.hp -= dmg
        self.flash = 0.08
        return dmg

    # -- per-frame --------------------------------------------------------
    def update(self, dt, combat):
        self.t += dt
        self.state_t += dt
        if self.flash > 0:
            self.flash -= dt

        was = self.phase
        frac = self.hp / self.max_hp
        self.phase = 0 if frac > 0.62 else (1 if frac > 0.28 else 2)
        if self.phase != was:
            self.state_t = 0.0
            combat.audio.play("boss_warn", 0.6)

        self.move(dt, combat)
        for p in self.pods:
            p.x = self.x + p.ox
            p.y = self.y + p.oy
            if p.flash > 0:
                p.flash -= dt
        self.act(dt, combat)

        for b in self.beams:
            b.update(dt)
        self.beams = [b for b in self.beams if not b.done]

    def move(self, dt, combat):
        self.x += self.drift * dt
        left = data.PLAY_L + self.w / 2 + 6
        right = data.PLAY_R - self.w / 2 - 6
        if self.x < left or self.x > right:
            self.drift = -self.drift
            self.x = max(left, min(right, self.x))
        target = data.TOP + 40
        if self.y < target:
            self.y = min(target, self.y + 30 * dt)

    def fire_rate(self):
        base = (1.5, 1.15, 0.85)[self.phase]
        # Sector 1 gets a slower version of the same fight. The first boss a
        # player meets is often met with a stock ship, and a fair pattern at
        # sector 5 speed is not a fair pattern at sector 1.
        base *= 1.34 - min(self.sector, 4) * 0.085
        if self.enraged:
            base *= 0.62
        # A stalled fight gets faster, not longer: either it dies or you do.
        if self.t > 45.0:
            base *= max(0.4, 1.0 - (self.t - 45.0) * 0.02)
        return base

    def scaled(self, low, high):
        """Interpolate a pattern's density across the campaign."""
        f = min(self.sector, 4) / 4.0
        return int(round(low + (high - low) * f))

    def act(self, dt, combat):
        """Dispatch to the boss's own behaviour."""
        if self.index == SENTINEL:
            self.act_sentinel(dt, combat)
        elif self.index == HIVE:
            self.act_hive(dt, combat)
        elif self.index == LANCE:
            self.act_lance(dt, combat)
        elif self.index == BULWARK:
            self.act_bulwark(dt, combat)
        else:
            self.act_warden(dt, combat)

    # -- behaviours -------------------------------------------------------
    def aim(self, combat):
        tx, ty = combat.nearest_player_pos(self.x)
        return math.atan2(ty - self.y, tx - self.x)

    def spray(self, combat, count, spread, speed=118, y_off=10):
        ang = self.aim(combat)
        out = []
        for i in range(count):
            a = ang + (i - (count - 1) / 2.0) * spread
            out.append(ent.EnemyBullet(self.x, self.y + y_off,
                                       math.cos(a) * speed,
                                       math.sin(a) * speed, 3))
        combat.shots.extend(out)
        combat.audio.play("enemy_shoot", 0.6, throttle=0.05)

    def ring(self, combat, count, speed=96):
        spin = self.t * 1.9
        for i in range(count):
            a = spin + i * (math.tau / count)
            combat.shots.append(ent.EnemyBullet(
                self.x, self.y + 6, math.cos(a) * speed, math.sin(a) * speed, 2))
        combat.audio.play("enemy_shoot", 0.6, throttle=0.05)

    def act_sentinel(self, dt, combat):
        self.fire_t -= dt
        if self.fire_t > 0:
            return
        self.fire_t = self.fire_rate()
        if self.phase == 0:
            self.spray(combat, self.scaled(2, 3), 0.26)
        elif self.phase == 1:
            self.spray(combat, self.scaled(4, 7), 0.24)
        else:
            self.ring(combat, self.scaled(6, 11))

    def act_hive(self, dt, combat):
        """Sends escorts. The bays are the threat; the gun is an afterthought."""
        self.spawn_t -= dt
        if self.spawn_t <= 0:
            self.spawn_t = (4.6, 3.6, 2.7)[self.phase]
            wave = (2, 3, 4)[self.phase]
            for i in range(wave):
                kind = data.RUSHER_ID if (i % 2 and self.phase) else data.GRUNT_ID
                combat.spawn_escort(kind,
                                    self.x + (i - (wave - 1) / 2.0) * 18,
                                    self.y + 12)
            combat.audio.play("jump", 0.5)
        self.fire_t -= dt
        if self.fire_t <= 0:
            self.fire_t = self.fire_rate() * 1.5
            self.spray(combat, 2 + self.phase, 0.3, 104)

    def act_lance(self, dt, combat):
        """Charge, telegraph, fire. Between beams it plinks at you so standing
        still in a safe column is not free either."""
        if not self.beams:
            gap = (3.4, 2.7, 2.0)[self.phase]
            if self.state_t > gap:
                self.state_t = 0.0
                tx, _ = combat.nearest_player_pos(self.x)
                width = 22 + 6 * self.phase
                self.beams.append(Beam(tx, width))
                if self.phase == 2:
                    # second beam, offset, so the safe lane is narrower
                    self.beams.append(Beam(tx + random.choice((-70, 70)), width))
                combat.audio.play("boss_warn", 0.5)
        self.fire_t -= dt
        if self.fire_t <= 0:
            self.fire_t = self.fire_rate() * 1.3
            self.spray(combat, 2, 0.5, 96)

    def act_bulwark(self, dt, combat):
        """The core is armoured until both pods are gone; the pods do the
        shooting, so breaking them quiets the fight as well as opening it."""
        for p in self.live_pods():
            p.fire_t -= dt
            if p.fire_t <= 0:
                p.fire_t = self.fire_rate() * 1.2
                ang = math.atan2(combat.nearest_player_pos(p.x)[1] - p.y,
                                 combat.nearest_player_pos(p.x)[0] - p.x)
                combat.shots.append(ent.EnemyBullet(
                    p.x, p.y + 4, math.cos(ang) * 126, math.sin(ang) * 126, 3))
                combat.audio.play("enemy_shoot", 0.5, throttle=0.06)
        if not self.shielded:
            if not self.enraged:
                self.enraged = True
                combat.audio.play("boss_warn", 0.7)
                combat.shake.kick(8.0)
            self.fire_t -= dt
            if self.fire_t <= 0:
                self.fire_t = self.fire_rate()
                self.ring(combat, self.scaled(6, 9) + self.phase)
        else:
            self.fire_t -= dt
            if self.fire_t <= 0:
                self.fire_t = self.fire_rate() * 1.6
                self.spray(combat, 3, 0.28, 106)

    def act_warden(self, dt, combat):
        """Everything, staged. Phase 0 pods and fans, phase 1 adds a beam,
        phase 2 opens the bays as well."""
        self.act_bulwark(dt, combat)
        if self.phase >= 1 and not self.beams:
            if self.state_t > 3.0:
                self.state_t = 0.0
                tx, _ = combat.nearest_player_pos(self.x)
                self.beams.append(Beam(tx, 24))
                combat.audio.play("boss_warn", 0.5)
        if self.phase >= 2:
            self.spawn_t -= dt
            if self.spawn_t <= 0:
                self.spawn_t = 3.4
                for i in (-1, 1):
                    combat.spawn_escort(data.RUSHER_ID, self.x + i * 24,
                                        self.y + 12)
                combat.audio.play("jump", 0.5)

    # -- drawing ----------------------------------------------------------
    def draw(self, surf, art):
        top = data.TOP
        for b in self.beams:
            b.draw(surf, top)
        for p in self.pods:
            if p.alive:
                img = art.pod_flash if p.flash > 0 else art.pod
            else:
                img = art.pod_dead
            surf.blit(img, (int(p.x) - img.get_width() // 2,
                            int(p.y) - img.get_height() // 2))
        img = art.boss_surface(self.index, self.flash > 0)
        surf.blit(img, (int(self.x) - img.get_width() // 2,
                        int(self.y) - img.get_height() // 2))
        if self.shielded:
            # a thin bracket, so "armoured" is visible rather than just felt
            r = self.rect()
            pygame.draw.rect(surf, data.BLUE,
                             (int(r[0]) - 2, int(r[1]) - 2,
                              int(r[2]) + 4, int(r[3]) + 4), 1)
