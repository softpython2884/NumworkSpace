"""The fight itself.

The rules are the ones the calculator build settled on, retuned for real time
and given room to breathe: particles on every impact, a boss with three phases,
crystals you actually chase, and a deflector that can eat a hit.
"""

import math
import random

import pygame

from . import art as art_mod
from . import data
from . import entities as ent
from .fx import Flash, Particles, Shake, Starfield


class Combat:
    """One combat node. `result` becomes True (cleared) or False (ship lost)."""

    def __init__(self, run, kind, art):
        self.run = run
        self.kind = kind
        self.art = art
        self.result = None
        self.rng = run.rng

        self.players = [ent.Player(0, data.W * 0.5 - (34 if run.players > 1 else 0))]
        if run.players > 1:
            self.players.append(ent.Player(1, data.W * 0.5 + 34))

        self.bullets = []
        self.enemies = []
        self.shots = []
        self.pickups = []
        self.particles = Particles()
        self.shake = Shake()
        self.flash = Flash()
        self.stars = Starfield()

        self.hitstop = 0.0
        self.spawn_t = 1.1
        self.boss = None
        self.tag = ""
        self.time = 0.0
        self.ended_t = 0.0
        self.prev_bomb = True

        sector = run.sector
        self.is_boss = kind == data.N_BOSS
        budget = (14 + sector * 9 + run.node * 3) * run.budget_mult
        # Capped: past this an uncapped budget makes waves longer, not harder.
        self.budget = min(budget, 96)
        if kind == data.N_ELITE:
            self.budget *= 1.4
        self.pool = min(2 + sector, 5)

        if self.is_boss:
            self.budget = 0
            hp = self.boss_hp()
            self.boss = ent.Enemy(data.BOSS_ID, data.W / 2, data.TOP - 20, hp, sector)
            self.enemies.append(self.boss)
            self.tag = "WARLORD"
        else:
            self.tag = "S%d-%d" % (sector + 1, run.node + 1)

    def boss_hp(self):
        """Scaled to the guns the player actually brought: a flat pool is a few
        seconds against a maxed build and several minutes against a stock one."""
        up = self.run.upgrades
        rate = 0.16 * (0.85 ** up[data.U_RATE])
        barrels = len(ent.SPREADS[min(up[data.U_SPREAD], 3)])
        dps = (1 + up[data.U_DMG]) * barrels / rate
        return int(55 + self.run.sector * 20 + dps * 4.0)

    # -- helpers ----------------------------------------------------------
    def live_players(self):
        return [p for p in self.players if p.alive]

    def nearest_player_pos(self, x):
        live = self.live_players()
        if not live:
            return data.W / 2, data.BOT
        best = min(live, key=lambda p: abs(p.x - x))
        return best.x, best.y

    def spawn_wave(self, dt):
        if self.budget <= 0 or len(self.enemies) > 14:
            return
        self.spawn_t -= dt
        if self.spawn_t > 0:
            return
        kind = self.rng.randrange(self.pool)
        self.budget -= data.ENEMY_COST[kind]
        hp = data.ENEMY_HP[kind] + self.run.sector
        x = self.rng.uniform(24, data.W - 24)
        e = ent.Enemy(kind, x, data.TOP - 14, hp, self.run.sector)
        self.enemies.append(e)
        gap = max(0.28, 0.85 - self.run.sector * 0.06) * self.rng.uniform(0.6, 1.4)
        self.spawn_t = gap

    def kill_enemy(self, e):
        """Score, salvage and a proper explosion."""
        self.run.score += e.score
        big = e.kind == data.BOSS_ID
        colours = (data.WHITE, data.YELLOW, data.ORANGE, data.RED)
        self.particles.burst(e.x, e.y, 46 if big else 16, 260 if big else 140,
                             colours, 0.85 if big else 0.5, 2 if big else 1)
        self.particles.burst(e.x, e.y, 22 if big else 8, 120,
                             (data.GREY, data.DARK), 1.1, 1, drag=1.2, gravity=40)
        self.shake.kick(9.0 if big else 2.4)
        if big:
            self.flash.pop(data.WHITE, 0.55)
            for _ in range(14):
                self.pickups.append(ent.Pickup(e.x + self.rng.uniform(-24, 24),
                                               e.y + self.rng.uniform(-10, 10)))
        else:
            n = 1 + (self.rng.random() < 0.45)
            for _ in range(n):
                self.pickups.append(ent.Pickup(e.x, e.y))
            if self.rng.random() < 0.09:
                self.pickups.append(ent.Pickup(e.x, e.y, kind=1))

    def hurt_player(self, p):
        if p.invuln > 0:
            return
        if p.take_hit():
            self.run.hull -= 1
            self.flash.pop(data.RED, 0.5)
            self.shake.kick(7.0)
            self.particles.burst(p.x, p.y, 24, 170,
                                 (data.RED, data.ORANGE, data.WHITE), 0.55, 2)
            self.hitstop = 0.09
        else:
            self.flash.pop(data.BLUE, 0.35)
            self.shake.kick(3.5)
            self.particles.burst(p.x, p.y, 20, 150, (data.BLUE, data.WHITE), 0.4, 1)

    def use_bomb(self):
        if self.run.bombs <= 0:
            return
        self.run.bombs -= 1
        self.flash.pop(data.WHITE, 1.0, decay=3.2)
        self.shake.kick(12.0)
        self.shots.clear()
        for _ in range(90):
            self.particles.burst(self.rng.uniform(0, data.W),
                                 self.rng.uniform(data.TOP, data.BOT),
                                 2, 130, (data.WHITE, data.CYAN), 0.5, 2)
        for e in list(self.enemies):
            e.hp -= 6
            e.flash = 0.12
            if e.hp <= 0:
                self.kill_enemy(e)
                self.enemies.remove(e)

    # -- main step --------------------------------------------------------
    def update(self, dt, inputs):
        if self.hitstop > 0:
            # A few frames of freeze on a hull hit: the cheapest way to make
            # damage feel like it landed.
            self.hitstop -= dt
            self.shake.update(dt)
            self.flash.update(dt)
            return
        self.time += dt
        self.stars.update(dt)
        self.particles.update(dt)
        self.shake.update(dt)
        self.flash.update(dt)

        up = self.run.upgrades
        bomb_held = inputs.get("bomb", False)
        if bomb_held and not self.prev_bomb:
            self.use_bomb()
        self.prev_bomb = bomb_held

        for p in self.live_players():
            dx, dy = inputs.get("move%d" % p.index, (0, 0))
            p.update(dt, dx, dy, up)
            if p.thrust > 0:
                self.particles.emit(p.x + self.rng.uniform(-2.5, 2.5), p.y + 8,
                                    self.rng.uniform(-16, 16),
                                    70 + 60 * p.thrust, 0.22,
                                    data.ORANGE if self.rng.random() < 0.6
                                    else data.YELLOW, 1, drag=3.0)
            if p.can_fire():
                self.bullets.extend(p.fire(up))

        for b in self.bullets:
            b.update(dt)
        for s in self.shots:
            s.update(dt)
        for e in self.enemies:
            tx, ty = self.nearest_player_pos(e.x)
            e.update(dt, tx)
            if e.y > data.TOP - 4 and e.wants_to_fire(dt):
                self.shots.extend(e.volley(tx, ty, self.run.difficulty
                                           + self.run.fire_bonus))

        targets = self.live_players()
        for pk in self.pickups:
            pk.update(dt, up[data.U_MAGNET], targets)

        self.collide()
        self.spawn_wave(dt)

        self.bullets = [b for b in self.bullets if b.alive]
        self.shots = [s for s in self.shots if s.alive]
        self.pickups = [p for p in self.pickups if p.alive]
        self.enemies = [e for e in self.enemies if e.alive]

        if self.run.hull <= 0:
            self.result = False
            return

        cleared = (not self.enemies) if self.is_boss else (
            self.budget <= 0 and not self.enemies and not self.shots)
        if cleared:
            # Hold the scene open for a moment so the salvage can be collected
            # and the last explosion finishes -- ending on the frame the boss
            # dies throws away everything it just dropped.
            self.ended_t += dt
            if self.ended_t > 2.6 or (not self.pickups and self.ended_t > 0.9):
                self.result = True
        else:
            self.ended_t = 0.0

    def collide(self):
        run = self.run
        for b in self.bullets:
            for e in self.enemies:
                # hp <= 0 means it died earlier this frame but has not been
                # filtered out yet -- without this guard a second bullet in the
                # same frame scores and explodes it all over again.
                if e.hp <= 0 or id(e) in b.hit:
                    continue
                if ent.overlaps((b.x - 1, b.y - 3, b.w, b.h), e.rect()):
                    e.hp -= b.dmg
                    e.flash = 0.08
                    self.particles.burst(b.x, b.y, 4, 90,
                                         (data.WHITE, data.YELLOW), 0.2, 1,
                                         spread=2.2, angle=-math.pi / 2)
                    if e.hp <= 0:
                        self.kill_enemy(e)
                    if b.pierce:
                        b.hit.add(id(e))
                    else:
                        b.y = -999
                    break
        self.enemies = [e for e in self.enemies if e.hp > 0]

        for p in self.live_players():
            pr = p.rect()
            for s in self.shots:
                if ent.overlaps(pr, (s.x - s.r, s.y - s.r, s.r * 2, s.r * 2)):
                    self.hurt_player(p)
                    s.y = 1e9
                    break
            for e in self.enemies:
                if e.hp > 0 and ent.overlaps(pr, e.rect()):
                    self.hurt_player(p)
                    if e.kind != data.BOSS_ID:
                        e.hp = 0
                        self.kill_enemy(e)
                    break
            for pk in self.pickups:
                if ent.overlaps((p.x - 9, p.y - 9, 18, 18),
                                (pk.x - 3, pk.y - 3, 6, 6)):
                    if pk.kind:
                        run.heal(1)
                        self.particles.burst(pk.x, pk.y, 8, 70, (data.GREEN,), 0.35)
                    else:
                        run.crystals += run.crystal_value()
                        run.score += 5
                        self.particles.burst(pk.x, pk.y, 6, 70, (data.CYAN,), 0.3)
                    pk.life = -1
        self.enemies = [e for e in self.enemies if e.hp > 0]

    # -- drawing ----------------------------------------------------------
    def draw(self, surf):
        surf.fill(data.VOID)
        self.stars.draw(surf)
        a = self.art
        sector = self.run.sector

        for pk in self.pickups:
            img = a.repair if pk.kind else a.crystal
            # blink out over the last second so it never vanishes unfairly
            if pk.life > 1.2 or int(pk.life * 12) % 2:
                surf.blit(img, (int(pk.x) - img.get_width() // 2,
                                int(pk.y) - img.get_height() // 2))

        for e in self.enemies:
            img = a.enemy_surface(sector, e.kind, e.flash > 0)
            surf.blit(img, (int(e.x) - img.get_width() // 2,
                            int(e.y) - img.get_height() // 2))

        self.particles.draw(surf)

        for b in self.bullets:
            surf.fill(data.YELLOW, (int(b.x) - 1, int(b.y) - 3, 2, 6))
            surf.fill(data.WHITE, (int(b.x) - 1, int(b.y) - 3, 2, 2))
        for s in self.shots:
            r = s.r
            surf.fill(data.ORANGE, (int(s.x) - r, int(s.y) - r, r * 2, r * 2))
            surf.fill(data.WHITE, (int(s.x) - r + 1, int(s.y) - r + 1,
                                   max(1, r * 2 - 2), max(1, r * 2 - 2)))

        for p in self.players:
            if not p.alive:
                continue
            if p.invuln > 0 and int(p.invuln * 20) % 2:
                continue
            img = a.players[p.index]
            px = int(p.x) - img.get_width() // 2
            py = int(p.y) - img.get_height() // 2
            surf.blit(img, (px, py))
            if p.shield:
                pygame.draw.circle(surf, data.BLUE, (int(p.x), int(p.y)), 13, 1)

        self.flash.draw(surf)
