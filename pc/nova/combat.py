"""The fight itself.

The rules are the ones the calculator build settled on, retuned for real time
and given room to breathe: particles on every impact, a boss with three phases,
crystals you actually chase, and a deflector that can eat a hit.
"""

import math
import random

import pygame

from . import boss as boss_mod
from . import data
from .ui import text as _text
from . import entities as ent
from .fx import Flash, Particles, Shake, Starfield


class _Silent:
    """Stand-in so callers never have to check whether sound exists."""

    def play(self, *a, **k):
        pass

    def music(self, *a, **k):
        pass

    def stop_music(self):
        pass


class Combat:
    """One combat node. `result` becomes True (cleared) or False (ship lost)."""

    def __init__(self, run, kind, art, audio=None):
        self.run = run
        self.kind = kind
        self.art = art
        self.audio = audio or _Silent()
        self.result = None
        self.rng = run.rng

        mid = (data.PLAY_L + data.PLAY_R) * 0.5
        self.players = [ent.Player(0, mid - (34 if run.players > 1 else 0))]
        if run.players > 1:
            self.players.append(ent.Player(1, mid + 34))

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
        self.intro_t = 0.0
        self.tag = ""
        self.time = 0.0
        self.ended_t = 0.0
        self.prev_bomb = True

        sector = run.sector
        self.is_boss = kind == data.N_BOSS
        budget = (16 + sector * 10 + run.node * 3) * run.budget_mult
        # Capped: past this an uncapped budget makes waves longer, not harder.
        self.budget = min(budget, 104)
        if kind == data.N_ELITE:
            self.budget *= 1.5
        self.pool = min(2 + sector, 5)

        if self.is_boss:
            self.budget = 0
            # One boss per sector, cycling once the campaign is behind you.
            self.boss = boss_mod.Boss(sector, sector, self.boss_hp(),
                                      (data.PLAY_L + data.PLAY_R) / 2,
                                      data.TOP - 20, run.fire_bonus, self.rng)
            self.tag = self.boss.name
            self.intro_t = 2.6
            self.audio.play("boss_warn")
        else:
            self.tag = "S%d-%d" % (sector + 1, run.node + 1)

    def boss_hp(self):
        """Scaled to the guns the player actually brought: a flat pool is a few
        seconds against a maxed build and several minutes against a stock one."""
        up = self.run.upgrades
        rate = 0.16 * (0.85 ** up[data.U_RATE])
        barrels = len(ent.SPREADS[min(up[data.U_SPREAD], 3)])
        dps = (1 + up[data.U_DMG]) * barrels / rate
        # Deliberately shorter than it was. The patterns take far more dodging
        # than they used to, so the same pool of hit points bought an 80-second
        # fight instead of a 30-second one -- and a dense pattern held for 80
        # seconds stops being a fight you read and becomes one you survive by
        # arithmetic.
        return int(40 + self.run.sector * 16 + dps * 2.6)

    # -- helpers ----------------------------------------------------------
    def live_players(self):
        return [p for p in self.players if p.alive]

    def nearest_player_pos(self, x):
        live = self.live_players()
        if not live:
            return (data.PLAY_L + data.PLAY_R) / 2, data.BOT
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
        x = self.rng.uniform(data.PLAY_L + 24, data.PLAY_R - 24)
        e = ent.Enemy(kind, x, data.TOP - 14, hp, self.run.sector, self.rng)
        self.enemies.append(e)
        gap = max(0.28, 0.85 - self.run.sector * 0.06) * self.rng.uniform(0.6, 1.4)
        self.spawn_t = gap

    def spawn_escort(self, kind, x, y):
        """A boss launching an escort. Weaker than a spawned wave enemy: they
        arrive in numbers and the boss is the real fight."""
        hp = max(1, data.ENEMY_HP[kind] + self.run.sector - 1)
        e = ent.Enemy(kind, max(data.PLAY_L + 12, min(data.PLAY_R - 12, x)),
                      y, hp, self.run.sector, self.rng)
        e.score = data.ENEMY_SCORE[kind] // 2
        self.enemies.append(e)
        self.particles.burst(x, y, 10, 90, (data.WHITE, data.ORANGE), 0.3)

    def kill_enemy(self, e):
        """Score, salvage and a proper explosion."""
        self.run.score += e.score
        big = e.kind == data.BOSS_ID
        # throttled: a bomb kills a dozen ships in one frame, and a dozen
        # explosion samples on top of each other is just noise
        self.audio.play("explode_big" if big else "explode",
                        1.0 if big else 0.8, throttle=0.0 if big else 0.045)
        colours = (data.WHITE, data.YELLOW, data.ORANGE, data.RED)
        self.particles.burst(e.x, e.y, 46 if big else 16, 260 if big else 140,
                             colours, 0.85 if big else 0.5, 2 if big else 1)
        self.particles.burst(e.x, e.y, 22 if big else 8, 120,
                             (data.GREY, data.DARK), 1.1, 1, drag=1.2, gravity=40)
        self.shake.kick(9.0 if big else 2.4)
        if big:
            self.flash.pop(data.WHITE, 0.55)
            for _ in range(14):
                self.pickups.append(ent.Pickup(
                    e.x + self.rng.uniform(-24, 24),
                    e.y + self.rng.uniform(-10, 10), rng=self.rng))
        else:
            n = 1 + (self.rng.random() < 0.45)
            for _ in range(n):
                self.pickups.append(ent.Pickup(e.x, e.y, rng=self.rng))
            # A hull patch every eleventh kill sounds modest until you count
            # the kills: at eighteen a fight it healed more than the fight
            # cost, so a sector's worth of patrols left the ship *fuller* than
            # it started and nothing that happened on the way to the boss
            # could matter. Measured at 0.09: -0.13 hull per patrol.
            if self.rng.random() < 0.03:
                self.pickups.append(ent.Pickup(e.x, e.y, kind=1,
                                               rng=self.rng))

    def hurt_player(self, p):
        if p.invuln > 0:
            return
        if p.take_hit():
            self.run.hull -= 1
            self.audio.play("hurt")
            self.flash.pop(data.RED, 0.5)
            self.shake.kick(7.0)
            self.particles.burst(p.x, p.y, 24, 170,
                                 (data.RED, data.ORANGE, data.WHITE), 0.55, 2)
            self.hitstop = 0.09
        else:
            self.audio.play("shield_break")
            self.flash.pop(data.BLUE, 0.35)
            self.shake.kick(3.5)
            self.particles.burst(p.x, p.y, 20, 150, (data.BLUE, data.WHITE), 0.4, 1)

    def use_bomb(self):
        if self.run.bombs <= 0:
            return
        self.run.bombs -= 1
        self.audio.play("bomb")
        self.flash.pop(data.WHITE, 1.0, decay=3.2)
        self.shake.kick(12.0)
        self.shots.clear()
        for _ in range(90):
            self.particles.burst(self.rng.uniform(data.PLAY_L, data.PLAY_R),
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
                shots = p.fire(up)
                self.bullets.extend(shots)
                self.audio.play("shoot_big" if len(shots) > 2 else "shoot",
                                0.8, throttle=0.035)
            if p.shield and not p.was_shielded:
                self.audio.play("shield_up", 0.7)
            p.was_shielded = p.shield

        for b in self.bullets:
            b.update(dt)
        for s in self.shots:
            s.update(dt)
        for e in self.enemies:
            tx, ty = self.nearest_player_pos(e.x)
            e.update(dt, tx)
            if e.y > data.TOP - 4 and e.wants_to_fire(
                    dt, 1.0 + self.run.fire_bonus):
                self.shots.extend(e.volley(tx, ty, self.run.difficulty
                                           + self.run.fire_bonus))
                self.audio.play("enemy_shoot", 0.55, throttle=0.06)

        if self.boss is not None:
            if self.intro_t > 0:
                # hold fire while the name card is up
                self.intro_t -= dt
                self.boss.move(dt, self)
                self.boss.t = 0.0
            else:
                self.boss.update(dt, self)

        targets = self.live_players()
        for pk in self.pickups:
            pk.update(dt, up[data.U_MAGNET], targets)

        self.collide()
        self.collide_boss()
        self.spawn_wave(dt)

        self.bullets = [b for b in self.bullets if b.alive]
        self.shots = [s for s in self.shots if s.alive]
        self.pickups = [p for p in self.pickups if p.alive]
        self.enemies = [e for e in self.enemies if e.alive]

        if self.run.hull <= 0:
            self.result = False
            return

        cleared = (self.boss is None) if self.is_boss else (
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

    def collide_boss(self):
        """Player shots against the boss and its pods, and its beams against
        the player. Pods are hit-tested first: they are in front, and hitting
        the armoured core when you meant to hit a pod feels like a cheat."""
        b = self.boss
        if b is None:
            return
        for shot in self.bullets:
            if shot.y < data.TOP - 10:
                continue
            box = (shot.x - 1, shot.y - 3, shot.w, shot.h)
            hit = None
            # Pods and wall guns first: they are in front of the core, and
            # hitting the armoured core when you meant to hit one of them
            # feels like the game cheated.
            for pod in b.live_pods():
                if ent.overlaps(box, pod.rect()):
                    hit = pod
                    break
            if hit is None:
                for turret in b.live_turrets():
                    if ent.overlaps(box, turret.rect()):
                        hit = turret
                        break
            if hit is not None:
                hit.hp -= shot.dmg
                hit.flash = 0.08
                self.audio.play("hit", 0.5, throttle=0.03)
                self.particles.burst(shot.x, shot.y, 4, 90,
                                     (data.WHITE, data.YELLOW), 0.2, 1)
                if hit.hp <= 0:
                    self.audio.play("explode", 0.9)
                    self.particles.burst(hit.x, hit.y, 26, 170,
                                         (data.WHITE, data.ORANGE, data.RED),
                                         0.7, 2)
                    self.shake.kick(6.0)
                if not shot.pierce:
                    shot.y = -999
                continue
            if id(b) in shot.hit:
                continue
            if ent.overlaps(box, b.rect()):
                dealt = b.take_hit(shot.dmg)
                self.audio.play("hit", 0.5 if dealt > 1 else 0.3, throttle=0.03)
                self.particles.burst(
                    shot.x, shot.y, 4 if dealt > 1 else 2, 90,
                    (data.WHITE, data.YELLOW) if dealt > 1 else (data.BLUE,),
                    0.2, 1)
                if b.hp <= 0:
                    self.kill_boss()
                    return
                if shot.pierce:
                    shot.hit.add(id(b))
                else:
                    shot.y = -999

        for p in self.live_players():
            pr = p.rect()
            if ent.overlaps(pr, b.rect()):
                self.hurt_player(p)
            for beam in b.beams:
                if beam.firing and ent.overlaps(pr, beam.rect(data.TOP)):
                    self.hurt_player(p)

    def kill_boss(self):
        b = self.boss
        self.run.score += b.score
        self.audio.play("explode_big")
        self.flash.pop(data.WHITE, 0.75)
        self.shake.kick(12.0)
        colours = (data.WHITE, data.YELLOW, data.ORANGE, data.RED)
        self.particles.burst(b.x, b.y, 70, 300, colours, 1.0, 2)
        self.particles.burst(b.x, b.y, 30, 140, (data.GREY, data.DARK), 1.3, 1,
                             drag=1.2, gravity=40)
        for _ in range(16):
            self.pickups.append(ent.Pickup(b.x + self.rng.uniform(-30, 30),
                                           b.y + self.rng.uniform(-10, 10),
                                           rng=self.rng))
        # escorts do not outlive their carrier
        for e in list(self.enemies):
            self.kill_enemy(e)
        self.enemies.clear()
        self.shots.clear()
        self.boss = None

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
                    self.audio.play("hit", 0.5, throttle=0.03)
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
                        self.audio.play("repair", 0.8)
                        self.particles.burst(pk.x, pk.y, 8, 70, (data.GREEN,), 0.35)
                    else:
                        run.crystals += run.crystal_value()
                        run.score += 5
                        self.audio.play("crystal", 0.5, throttle=0.04)
                        self.particles.burst(pk.x, pk.y, 6, 70, (data.CYAN,), 0.3)
                    pk.life = -1
        self.enemies = [e for e in self.enemies if e.hp > 0]

    # -- drawing ----------------------------------------------------------
    def draw(self, surf):
        surf.fill(data.VOID)
        self.stars.draw(surf)
        a = self.art
        sector = self.run.sector
        self.draw_frame(surf)

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

        if self.boss is not None:
            self.boss.draw(surf, a)

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

        self.mask_margins(surf)
        self.draw_side_panel(surf)
        if self.intro_t > 0 and self.boss is not None:
            self.draw_intro(surf)
        self.flash.draw(surf)

    def draw_intro(self, surf):
        """Name the boss and say what it does. A fight you have never seen
        should not open with a surprise you could not have read."""
        b = self.boss
        y = data.TOP + (data.BOT - data.TOP) // 2
        fade = min(1.0, self.intro_t / 0.5)
        band = pygame.Surface((data.PLAY_R - data.PLAY_L, 44), pygame.SRCALPHA)
        band.fill((0, 0, 0, int(190 * fade)))
        surf.blit(band, (data.PLAY_L, y - 22))
        pygame.draw.line(surf, data.RED, (data.PLAY_L, y - 22),
                         (data.PLAY_R, y - 22))
        pygame.draw.line(surf, data.RED, (data.PLAY_L, y + 21),
                         (data.PLAY_R, y + 21))
        _text(surf, self.art, b.name, (data.PLAY_L + data.PLAY_R) // 2, y - 16,
              data.RED, centre=True, big=True)
        _text(surf, self.art, b.tell, (data.PLAY_L + data.PLAY_R) // 2, y + 4,
              data.GREY, centre=True)

    def draw_frame(self, surf):
        """Rails either side of the arena, so the playable width reads as
        deliberate rather than as a window that failed to stretch."""
        if data.PLAY_L <= 0:
            return
        for x in (data.PLAY_L - 2, data.PLAY_R + 1):
            pygame.draw.line(surf, data.DARK, (x, data.TOP), (x, data.BOT))
            pygame.draw.line(surf, data.GREY, (x, data.TOP), (x, data.TOP + 8))
            pygame.draw.line(surf, data.GREY, (x, data.BOT - 8), (x, data.BOT))

    def draw_side_panel(self, surf):
        """On a wide monitor the margins get the ship's loadout.

        It is information the HUD has no room for at 16:9, and it stops the
        scenery from looking like wasted screen.
        """
        margin = data.PLAY_L
        if margin < 76:
            return
        a = self.art
        up = self.run.upgrades
        x = 8
        y = data.TOP + 6
        _text(surf, a, "LOADOUT", x, y, data.DARK)
        y += 16
        shown = 0
        # Names vary in length and the margin varies with the monitor, so the
        # label is trimmed to whatever is actually left once the level pips
        # have their space. A fixed column ran straight through the long ones.
        char_w = max(1, a.font.size("M")[0])
        pip_x = margin - 20
        for name, index, _price, _blurb in data.SHOP:
            level = up[index]
            if not level:
                continue
            room = max(3, (pip_x - x - 4) // char_w)
            _text(surf, a, name[:room], x, y, data.GREY)
            for i in range(level):
                surf.fill(data.CYAN, (pip_x + i * 5, y + 4, 3, 5))
            y += 13
            shown += 1
        if not shown:
            _text(surf, a, "stock ship", x, y, data.DARK)

        rx = data.PLAY_R + 10
        ry = data.TOP + 6
        _text(surf, a, "SECTOR", rx, ry, data.DARK)
        label = ("VOID %d" % (self.run.sector - 4)) if self.run.sector > 4 \
            else str(self.run.sector + 1)
        _text(surf, a, label, rx, ry + 16, data.SEC_ACCENT(self.run.sector))
        _text(surf, a, "NODE %d" % (self.run.node + 1), rx, ry + 32, data.GREY)
        if self.is_boss and self.boss is not None:
            _text(surf, a, "WARLORD", rx, ry + 54, data.RED)

    def mask_margins(self, surf):
        """Clip anything that leaked outside the arena.

        Explosions and engine trails are free to spray past the rails; without
        this they would scatter across the scenery and give away that the
        margins are just more canvas.
        """
        if data.PLAY_L > 0:
            left = pygame.Surface((data.PLAY_L - 1, data.BOT - data.TOP),
                                  pygame.SRCALPHA)
            left.fill((*data.VOID, 232))
            surf.blit(left, (0, data.TOP))
            right_w = data.W - data.PLAY_R - 2
            if right_w > 0:
                right = pygame.Surface((right_w, data.BOT - data.TOP),
                                       pygame.SRCALPHA)
                right.fill((*data.VOID, 232))
                surf.blit(right, (data.PLAY_R + 2, data.TOP))
        if data.TOP > data.HUD_H:
            top = pygame.Surface((data.W, data.TOP - data.HUD_H), pygame.SRCALPHA)
            top.fill((*data.VOID, 232))
            surf.blit(top, (0, data.HUD_H))
        if data.BOT < data.H:
            bot = pygame.Surface((data.W, data.H - data.BOT), pygame.SRCALPHA)
            bot.fill((*data.VOID, 232))
            surf.blit(bot, (0, data.BOT))
