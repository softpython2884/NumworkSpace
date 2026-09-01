"""Five bosses, five ideas, and a shared vocabulary of attacks.

    SENTINEL     fans, then walls with one gap, then a spiral
    HIVE MOTHER  escorts out of the bays, rain from above, wall guns
    LANCE        beams -- one, then two, then a comb that sweeps the arena
    BULWARK      pods armour the core and fire bursts; break them and it opens
    WARDEN       all of it, staged over three phases

They share a body: drift, hit points, phases by remaining hull. What differs is
`act`, dispatched once per frame, and that is the only place a boss's
personality lives.

The patterns are dense on purpose and none of them is random. A spiral is the
same spiral every second; a wall always has exactly one gap; a beam is fixed
where it was aimed when charging began. That is the difference between hard
and unfair: you are meant to learn the shape and move through it, not to be
surprised by it. The player's hitbox is 6x9 inside a 13x17 ship, a hull hit
buys 1.4 seconds of invulnerability, and a bomb wipes the screen -- all three
exist so that a full screen of bullets is a puzzle rather than a coin flip.
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
    `delay` holds one back, which is how a comb of them sweeps the arena.
    """

    CHARGE = 1.15
    FIRE = 1.35
    FADE = 0.3

    def __init__(self, x, width=26, delay=0.0):
        self.x = x
        self.width = width
        self.t = -delay

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
        if self.t < 0:
            return                      # still queued, nothing to show yet
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


class Turret:
    """A gun bolted to the arena wall, firing across it.

    The boss owns the middle of the screen. Without these, the edges are where
    you go to be safe, and a fight with a safe corner is a fight you win by
    standing in it. They are destructible, so clearing a side is a real choice
    to make with the seconds you are not shooting the boss -- and they arm
    visibly for a second first, because a shot from off-screen is an ambush,
    not a pattern.
    """

    ARM = 1.05

    def __init__(self, side, y, hp):
        self.side = side                # -1 left wall, +1 right wall
        self.y = y
        self.hp = hp
        self.max_hp = hp
        self.flash = 0.0
        self.t = 0.0
        self.fire_t = self.ARM + random.uniform(0.15, 0.8)
        self.w = 9
        self.h = 11

    @property
    def alive(self):
        return self.hp > 0

    @property
    def armed(self):
        return self.t >= self.ARM

    @property
    def x(self):
        # Read off the viewport every time: the arena is re-centred on a
        # resize and a turret welded to a stale edge would hang in mid-air.
        return (data.PLAY_L + 6) if self.side < 0 else (data.PLAY_R - 6)

    def rect(self):
        return (self.x - self.w / 2, self.y - self.h / 2, self.w, self.h)

    def update(self, dt, combat, rate, hot=True):
        self.t += dt
        if self.flash > 0:
            self.flash -= dt
        if not hot:
            return          # the boss's window has to be a window everywhere
        self.fire_t -= dt
        if self.fire_t > 0 or not self.armed:
            return
        self.fire_t = rate
        tx, ty = combat.nearest_player_pos(self.x)
        ang = math.atan2(ty - self.y, tx - self.x)
        if self.side > 0:
            ang = math.pi - _clamp(math.pi - ang, -0.55, 0.55)
        else:
            ang = _clamp(ang, -0.55, 0.55)
        speed = 132.0
        combat.shots.append(ent.EnemyBullet(
            self.x + self.side * -4, self.y,
            math.cos(ang) * speed, math.sin(ang) * speed, 3))
        combat.audio.play("enemy_shoot", 0.5, throttle=0.06)

    def draw(self, surf):
        x, y = int(self.x), int(self.y)
        if not self.armed:
            # arming: a blinking outline, so the first shot is never a shock
            if int(self.t * 12) % 2:
                pygame.draw.rect(surf, data.RED,
                                 (x - 5, y - 6, 10, 12), 1)
            return
        body = data.RED_D if self.flash <= 0 else data.WHITE
        surf.fill(body, (x - 4, y - 5, 8, 10))
        surf.fill(data.GREY, (x - 4, y - 5, 8, 2))
        # barrel, pointing into the arena
        bx = x - 7 if self.side > 0 else x + 3
        surf.fill(data.RED, (bx, y - 1, 4, 3))


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


class Boss:
    def __init__(self, index, sector, hp, x, y, fire_bonus=0.0):
        self.index = index % BOSS_COUNT
        self.sector = sector
        self.fire_bonus = fire_bonus
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
        self.turrets = []
        self.deployed = -1          # last phase whose wall guns are out
        self.spawn_t = 3.0
        self.state_t = 0.0
        self.enraged = False
        self.cycle = 0              # alternates attacks within a phase
        self.storming = True
        self.burst_t = self.STORM[0][0]
        self.spin = random.uniform(0.0, math.tau)
        self.stream_t = 0.0
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

    def live_turrets(self):
        return [t for t in self.turrets if t.alive]

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
            self.cycle = 0
            combat.audio.play("boss_warn", 0.6)

        self.move(dt, combat)
        for p in self.pods:
            p.x = self.x + p.ox
            p.y = self.y + p.oy
            if p.flash > 0:
                p.flash -= dt
        hot = self.breathe(dt, combat)
        turret_rate = self.fire_rate() * 1.45
        for t in self.live_turrets():
            t.update(dt, combat, turret_rate, hot)
        if hot:
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

    # Storm and lull, in seconds, per phase.
    #
    # The first cut of these bosses simply never stopped firing, and that was
    # the mistake: with no window to shoot back, a fight stops being something
    # you read and becomes arithmetic -- 60 seconds of dodging, chipping the
    # boss down between near misses. A pattern needs a rest in it for the same
    # reason a drum beat does. The storm can then be far nastier than it would
    # otherwise dare to be.
    STORM = ((3.0, 1.7), (3.6, 1.4), (4.4, 1.1))

    def breathe(self, dt, combat):
        """True while the guns are hot; False through the window between."""
        self.burst_t -= dt
        if self.burst_t <= 0:
            self.storming = not self.storming
            storm, lull = self.STORM[self.phase]
            self.burst_t = storm if self.storming else lull
            if self.storming:
                combat.audio.play("boss_warn", 0.35)
        return self.storming

    def fire_rate(self):
        base = (0.95, 0.72, 0.54)[self.phase]
        # The campaign ramp is deliberately shallow now. It used to hand the
        # first boss a third off its rate of fire, which made sector 1 a
        # formality -- and a formality teaches none of the patterns that
        # sector 2 then expects you to already know.
        base *= 1.15 - min(self.sector, 4) * 0.0375
        base /= 1.0 + self.fire_bonus
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

    # -- the attack vocabulary --------------------------------------------
    def aim(self, combat):
        tx, ty = combat.nearest_player_pos(self.x)
        return math.atan2(ty - self.y, tx - self.x)

    def spray(self, combat, count, spread, speed=118, y_off=10):
        """An aimed fan. Punishes standing still; the gaps widen with range."""
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
        """Everything at once, evenly. Move outward through a gap early: the
        ring only gets harder to cross as it spreads."""
        spin = self.t * 1.9
        for i in range(count):
            a = spin + i * (math.tau / count)
            combat.shots.append(ent.EnemyBullet(
                self.x, self.y + 6, math.cos(a) * speed, math.sin(a) * speed, 2))
        combat.audio.play("enemy_shoot", 0.6, throttle=0.05)

    def spiral(self, dt, combat, arms=2, rate=2.2, speed=100):
        """A rotating stream, emitted continuously.

        The densest thing in the game and the fairest: the arms turn at a fixed
        rate, so the safe path is a curve that is there every single rotation.
        Called every frame -- it keeps its own emission timer.
        """
        self.spin += dt * rate
        self.stream_t -= dt
        if self.stream_t > 0:
            return
        self.stream_t = 0.09
        for i in range(arms):
            a = self.spin + i * (math.tau / arms)
            combat.shots.append(ent.EnemyBullet(
                self.x, self.y + 6, math.cos(a) * speed, math.sin(a) * speed, 2))
        combat.audio.play("enemy_shoot", 0.4, throttle=0.1)

    def wall(self, combat, gap=56, speed=90, step=15):
        """A row across the whole arena with exactly one hole in it.

        The oldest attack there is. It asks one question -- are you willing to
        stop shooting and go somewhere -- and it asks it in a way nobody can
        misread.
        """
        hole = random.uniform(data.PLAY_L + gap, data.PLAY_R - gap)
        x = data.PLAY_L + 6
        while x < data.PLAY_R - 6:
            if abs(x - hole) > gap / 2:
                combat.shots.append(ent.EnemyBullet(x, self.y + 10, 0.0,
                                                    speed, 2))
            x += step
        combat.audio.play("enemy_shoot", 0.65, throttle=0.05)

    def rain(self, combat, count, speed=122):
        """Straight down from the top edge, spread wide and unaimed.

        Pressure rather than a threat: it takes space away without ever
        chasing anyone, which is what makes the aimed attacks land."""
        for _ in range(count):
            x = random.uniform(data.PLAY_L + 8, data.PLAY_R - 8)
            combat.shots.append(ent.EnemyBullet(
                x, data.TOP + 2, random.uniform(-16, 16), speed, 2))
        combat.audio.play("enemy_shoot", 0.5, throttle=0.08)

    def deploy_turrets(self, combat, phase, hp=None):
        """Bolt a pair of guns to the walls, one high, one low."""
        if self.deployed >= phase:
            return
        self.deployed = phase
        arena = data.BOT - data.TOP
        hp = hp or max(6, self.max_hp // 11)
        side = random.choice((-1, 1))
        for f, s in ((0.34, side), (0.60, -side)):
            self.turrets.append(Turret(s, data.TOP + arena * f, hp))
        combat.audio.play("boss_warn", 0.45)

    def cast_beams(self, combat, comb=False):
        """One beam where you are, or a comb that walks across the arena."""
        tx, _ = combat.nearest_player_pos(self.x)
        width = 20 + 4 * self.phase
        if comb:
            span = data.PLAY_R - data.PLAY_L
            n = 4
            start = data.PLAY_L + span * 0.13
            step = (span * 0.74) / (n - 1)
            order = list(range(n))
            if random.random() < 0.5:
                order.reverse()
            for i, slot in enumerate(order):
                self.beams.append(Beam(start + slot * step, width,
                                       delay=i * 0.32))
        elif self.phase >= 1:
            self.beams.append(Beam(tx, width))
            self.beams.append(Beam(tx + random.choice((-78, 78)), width))
        else:
            self.beams.append(Beam(tx, width))
        combat.audio.play("boss_warn", 0.5)

    def pod_burst(self, combat, pod, count=3, spread=0.16, speed=128):
        tx, ty = combat.nearest_player_pos(pod.x)
        ang = math.atan2(ty - pod.y, tx - pod.x)
        for i in range(count):
            a = ang + (i - (count - 1) / 2.0) * spread
            combat.shots.append(ent.EnemyBullet(
                pod.x, pod.y + 4, math.cos(a) * speed, math.sin(a) * speed, 3))
        combat.audio.play("enemy_shoot", 0.5, throttle=0.06)

    # -- behaviours -------------------------------------------------------
    def act_sentinel(self, dt, combat):
        """Fans, walls, and finally a spiral over the top.

        This is the first boss anyone meets, so it is the one that teaches the
        vocabulary: every attack it has is symmetrical, and every one of them
        comes back later on something meaner.
        """
        if self.phase == 2:
            self.spiral(dt, combat, arms=2, rate=2.0, speed=94)
        self.fire_t -= dt
        if self.fire_t > 0:
            return
        self.fire_t = self.fire_rate()
        self.cycle += 1
        if self.phase == 0:
            self.spray(combat, self.scaled(4, 6), 0.22)
            if self.cycle % 3 == 0:
                self.wall(combat, gap=66)
        elif self.phase == 1:
            self.spray(combat, self.scaled(6, 9), 0.20)
            if self.cycle % 2 == 0:
                self.wall(combat, gap=58, speed=98)
        else:
            self.ring(combat, self.scaled(10, 15))
            if self.cycle % 2 == 0:
                self.spray(combat, self.scaled(5, 7), 0.17, 134)

    def act_hive(self, dt, combat):
        """The bays are the threat, and from phase 1 the walls are too."""
        self.spawn_t -= dt
        if self.spawn_t <= 0:
            self.spawn_t = (3.4, 2.6, 1.9)[self.phase]
            wave = (3, 4, 5)[self.phase]
            for i in range(wave):
                kind = data.RUSHER_ID if (i % 2 and self.phase) else data.GRUNT_ID
                combat.spawn_escort(kind,
                                    self.x + (i - (wave - 1) / 2.0) * 18,
                                    self.y + 12)
            combat.audio.play("jump", 0.5)
        if self.phase >= 1:
            self.deploy_turrets(combat, 1)
        self.fire_t -= dt
        if self.fire_t <= 0:
            self.fire_t = self.fire_rate() * 1.2
            self.cycle += 1
            if self.cycle % 2:
                self.rain(combat, self.scaled(4, 7))
            else:
                self.spray(combat, self.scaled(3, 5), 0.28, 108)

    def act_lance(self, dt, combat):
        """Charge, telegraph, fire -- one beam, then two, then a comb that
        walks the arena end to end. Standing in a safe column stops working
        at exactly the moment you have learned to rely on it."""
        if not self.beams:
            gap = (2.6, 2.1, 1.6)[self.phase]
            if self.state_t > gap:
                self.state_t = 0.0
                self.cast_beams(combat, comb=(self.phase == 2))
        self.fire_t -= dt
        if self.fire_t <= 0:
            self.fire_t = self.fire_rate() * 1.15
            self.spray(combat, self.scaled(3, 5), 0.32, 112)
        if self.phase == 2:
            self.spiral(dt, combat, arms=3, rate=-1.7, speed=86)

    def act_bulwark(self, dt, combat):
        """The core is armoured until both pods are gone; the pods do the
        shooting, so breaking them quiets the fight as well as opening it --
        and then the core stops holding back."""
        rate = self.fire_rate()
        for p in self.live_pods():
            p.fire_t -= dt
            if p.fire_t <= 0:
                p.fire_t = rate * 1.05
                self.pod_burst(combat, p, count=self.scaled(2, 4))
        if not self.shielded:
            if not self.enraged:
                self.enraged = True
                combat.audio.play("boss_warn", 0.7)
                combat.shake.kick(8.0)
            self.spiral(dt, combat, arms=self.scaled(2, 4), rate=2.5, speed=102)
            self.fire_t -= dt
            if self.fire_t <= 0:
                self.fire_t = self.fire_rate()
                self.ring(combat, self.scaled(9, 14) + self.phase * 2)
        else:
            self.fire_t -= dt
            if self.fire_t <= 0:
                self.fire_t = self.fire_rate() * 1.1
                self.cycle += 1
                if self.cycle % 2:
                    self.wall(combat, gap=60, speed=96)
                else:
                    self.spray(combat, self.scaled(4, 6), 0.24, 110)

    def act_warden(self, dt, combat):
        """Everything, staged. Wall guns from the start, beams from phase 1,
        the bays open in phase 2 -- and the pods are still in the way."""
        self.deploy_turrets(combat, 0)
        self.act_bulwark(dt, combat)
        if self.phase >= 1:
            self.deploy_turrets(combat, 1)
            if not self.beams and self.state_t > 2.4:
                self.state_t = 0.0
                self.cast_beams(combat)
        if self.phase >= 2:
            self.spawn_t -= dt
            if self.spawn_t <= 0:
                self.spawn_t = 3.0
                for i in (-1, 1):
                    combat.spawn_escort(data.RUSHER_ID, self.x + i * 24,
                                        self.y + 12)
                combat.audio.play("jump", 0.5)

    # -- drawing ----------------------------------------------------------
    def draw(self, surf, art):
        top = data.TOP
        for b in self.beams:
            b.draw(surf, top)
        for t in self.live_turrets():
            t.draw(surf)
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
        if not self.storming:
            # Venting between volleys: the window to stop dodging and shoot.
            # Corner ticks rather than a box, because a box round the boss
            # already means "armoured" on BULWARK and WARDEN, and two states
            # that matter cannot share one shape.
            r = self.rect()
            x0, y0 = int(r[0]) - 5, int(r[1]) - 5
            x1, y1 = x0 + int(r[2]) + 10, y0 + int(r[3]) + 10
            for (cx, sx) in ((x0, 1), (x1, -1)):
                for (cy, sy) in ((y0, 1), (y1, -1)):
                    surf.fill(data.CYAN, (min(cx, cx + sx * 5), cy, 5, 1))
                    surf.fill(data.CYAN, (cx, min(cy, cy + sy * 5), 1, 5))
        if self.shielded:
            # a thin bracket, so "armoured" is visible rather than just felt
            r = self.rect()
            pygame.draw.rect(surf, data.BLUE,
                             (int(r[0]) - 2, int(r[1]) - 2,
                              int(r[2]) + 4, int(r[3]) + 4), 1)
