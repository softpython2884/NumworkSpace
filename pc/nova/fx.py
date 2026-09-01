"""Screen feel: particles, shake, hit-stop, and the CRT overlay.

None of this changes what the game does. All of it changes how it lands. The
calculator build could not afford a single particle; here we can throw a few
hundred a frame and never notice.
"""

import math
import random

import pygame

from . import data


class Particles:
    """A fixed pool of dots. Compacted like the calculator's entity pools --
    live particles fill the front of the list -- so the update loop never tests
    a dead slot and nothing is allocated while the game runs."""

    __slots__ = ("x", "y", "vx", "vy", "life", "full", "col", "size", "drag",
                 "gravity", "n", "cap")

    def __init__(self, cap=900):
        self.cap = cap
        self.x = [0.0] * cap
        self.y = [0.0] * cap
        self.vx = [0.0] * cap
        self.vy = [0.0] * cap
        self.life = [0.0] * cap
        self.full = [0.0] * cap
        self.col = [data.WHITE] * cap
        self.size = [1] * cap
        self.drag = [0.0] * cap
        self.gravity = [0.0] * cap
        self.n = 0

    def clear(self):
        self.n = 0

    def emit(self, x, y, vx, vy, life, colour, size=1, drag=2.2, gravity=0.0):
        i = self.n
        if i >= self.cap:
            return
        self.x[i] = x
        self.y[i] = y
        self.vx[i] = vx
        self.vy[i] = vy
        self.life[i] = life
        self.full[i] = life
        self.col[i] = colour
        self.size[i] = size
        self.drag[i] = drag
        self.gravity[i] = gravity
        self.n = i + 1

    def burst(self, x, y, count, speed, colours, life=0.5, size=1, spread=math.tau,
              angle=0.0, drag=2.2, gravity=0.0):
        for _ in range(count):
            a = angle + random.uniform(-spread / 2, spread / 2)
            s = speed * random.uniform(0.35, 1.0)
            self.emit(x, y, math.cos(a) * s, math.sin(a) * s,
                      life * random.uniform(0.6, 1.15),
                      random.choice(colours), size, drag, gravity)

    def update(self, dt):
        i = self.n - 1
        while i >= 0:
            self.life[i] -= dt
            if self.life[i] <= 0:
                self.n -= 1
                j = self.n
                if i != j:
                    self.x[i] = self.x[j]; self.y[i] = self.y[j]
                    self.vx[i] = self.vx[j]; self.vy[i] = self.vy[j]
                    self.life[i] = self.life[j]; self.full[i] = self.full[j]
                    self.col[i] = self.col[j]; self.size[i] = self.size[j]
                    self.drag[i] = self.drag[j]; self.gravity[i] = self.gravity[j]
            else:
                d = 1.0 - self.drag[i] * dt
                if d < 0.0:
                    d = 0.0
                self.vx[i] *= d
                self.vy[i] = self.vy[i] * d + self.gravity[i] * dt
                self.x[i] += self.vx[i] * dt
                self.y[i] += self.vy[i] * dt
            i -= 1

    def draw(self, surf):
        fill = surf.fill
        for i in range(self.n):
            t = self.life[i] / self.full[i]
            s = self.size[i]
            # Fade by shrinking rather than by alpha: no per-particle surface,
            # and it reads as more "pixel" than a soft fade would.
            if t < 0.35 and s > 1:
                s -= 1
            fill(self.col[i], (int(self.x[i]), int(self.y[i]), s, s))


class Shake:
    """Screen shake with a decaying amplitude, sampled on two sine waves so it
    reads as a jolt rather than as noise."""

    def __init__(self):
        self.amount = 0.0
        self.t = 0.0

    def kick(self, amount):
        self.amount = max(self.amount, amount)

    def update(self, dt):
        self.t += dt
        self.amount *= max(0.0, 1.0 - 7.0 * dt)
        if self.amount < 0.05:
            self.amount = 0.0

    def offset(self):
        if self.amount <= 0.0:
            return 0, 0
        return (int(math.sin(self.t * 47.0) * self.amount),
                int(math.sin(self.t * 61.0 + 1.7) * self.amount * 0.7))


class Flash:
    """A full-screen colour wash, used for bombs and hull hits."""

    def __init__(self):
        self.colour = data.WHITE
        self.amount = 0.0
        self.decay = 6.0

    def pop(self, colour, amount=0.7, decay=6.0):
        self.colour = colour
        self.amount = max(self.amount, amount)
        self.decay = decay

    def update(self, dt):
        self.amount *= max(0.0, 1.0 - self.decay * dt)
        if self.amount < 0.01:
            self.amount = 0.0

    def draw(self, surf):
        if self.amount <= 0.0:
            return
        layer = pygame.Surface(surf.get_size())
        layer.fill(self.colour)
        layer.set_alpha(int(255 * min(1.0, self.amount)))
        surf.blit(layer, (0, 0))


class Starfield:
    """Three parallax layers, back on PC. Stars are stored as floats so the slow
    layers drift smoothly instead of stepping a pixel at a time."""

    def __init__(self, count=110):
        self.stars = []
        for _ in range(count):
            layer = random.randrange(3)
            self.stars.append([random.uniform(0, data.W),
                               random.uniform(data.TOP, data.BOT), layer])

    def update(self, dt, speed=1.0):
        for s in self.stars:
            r, g, b, v = data.STAR_LAYERS[s[2]]
            s[1] += v * 46.0 * speed * dt
            if s[1] >= data.BOT:
                s[1] -= data.BOT - data.TOP
                s[0] = random.uniform(0, data.W)

    def draw(self, surf):
        fill = surf.fill
        for s in self.stars:
            r, g, b, _ = data.STAR_LAYERS[s[2]]
            fill((r, g, b), (int(s[0]), int(s[1]), 1, 1))


def make_crt(size):
    """Scanlines plus a soft vignette, baked once into one alpha surface.

    Drawn at window resolution, not game resolution: the point is that the
    lines fall between the fat game pixels rather than on top of them.
    """
    w, h = size
    layer = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(0, h, 3):
        pygame.draw.line(layer, (0, 0, 0, 46), (0, y), (w, y))
    corner = pygame.Surface(size, pygame.SRCALPHA)
    cx, cy = w / 2.0, h / 2.0
    step = 4
    maxd = math.hypot(cx, cy)
    for y in range(0, h, step):
        for x in range(0, w, step):
            d = math.hypot(x - cx, y - cy) / maxd
            a = int(max(0.0, (d - 0.55)) * 250)
            if a:
                corner.fill((0, 0, 0, min(a, 130)), (x, y, step, step))
    layer.blit(corner, (0, 0))
    return layer
