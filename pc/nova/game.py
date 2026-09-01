"""The state machine and the main loop.

Everything is drawn onto a 480x270 surface and blown up by a whole number to
fill the window, so a game pixel stays a hard square whatever the monitor is.
"""

import math
import random

import pygame

from . import data, sector, ui
from .art import Art
from .combat import Combat
from .fx import Flash, Particles, Starfield, make_crt
from .run import Run

TITLE, MAP, COMBAT, TRADER, EVENT, REST, INTERLUDE, GAMEOVER = range(8)


class Game:
    def __init__(self, scale=3, fullscreen=False, crt=True):
        pygame.init()
        pygame.display.set_caption("NOVA")
        self.scale = scale
        self.fullscreen = fullscreen
        self.crt_on = crt
        self.screen = None
        self.crt = None
        self._open_window()

        self.canvas = pygame.Surface((data.W, data.H))
        self.art = Art()
        self.art.load_fonts()
        self.clock = pygame.time.Clock()
        self.t = 0.0
        self.running = True

        self.run = None
        self.map = None
        self.combat = None
        self.menu = None
        self.state = TITLE
        self.pending = None
        self.message = None
        self.stars = Starfield(140)
        self.title_particles = Particles(300)
        self.flash = Flash()
        self.difficulty = 1
        self.players = 1
        self.enter_title()

    # -- window -----------------------------------------------------------
    def _open_window(self):
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN |
                                                  pygame.SCALED)
            size = self.screen.get_size()
            self.scale = max(1, min(size[0] // data.W, size[1] // data.H))
        else:
            self.screen = pygame.display.set_mode((data.W * self.scale,
                                                   data.H * self.scale))
        self.crt = make_crt(self.screen.get_size())

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self._open_window()

    def set_scale(self, scale):
        if self.fullscreen:
            return
        self.scale = max(1, min(6, scale))
        self._open_window()

    # -- state entry ------------------------------------------------------
    def enter_title(self):
        self.state = TITLE
        name = data.DIFFICULTIES[self.difficulty][0]
        self.menu = ui.Menu(
            ["SOLO", "CO-OP  2 PLAYERS", "DIFFICULTY   " + name, "QUIT"],
            ["Arrows or WASD. Fire is automatic.",
             "P1 arrows, P2 WASD. One hull, one score.",
             data.DIFFICULTIES[self.difficulty][4],
             "Leave the void alone."],
            [data.CYAN, data.VIOLET, data.ORANGE, data.GREY])

    def start_run(self, players):
        self.players = players
        self.run = Run(players, self.difficulty)
        self.new_sector()

    def new_sector(self):
        self.map = sector.SectorMap(self.run.rng, self.run.sector)
        self.enter_map()

    def enter_map(self):
        self.state = MAP
        opts = self.map.options()
        self.selected = opts[0] if opts else None
        self.sel_index = 0

    def enter_node(self, kind):
        self.run.node = self.map.col
        self.run.enter_node()
        if kind == data.N_SHOP:
            self.enter_trader(free=False)
        elif kind == data.N_REST:
            self.state = REST
            healed = min(5, self.run.max_hull - self.run.hull)
            self.run.heal(5)
            self.message = ("REPAIR BAY", data.GREEN,
                            "Hull patched: +%d" % healed if healed else
                            "Hull already full")
        elif kind == data.N_EVENT:
            self.enter_event()
        else:
            self.state = COMBAT
            self.combat = Combat(self.run, kind, self.art)
            self.pending = kind

    def enter_trader(self, free):
        self.state = TRADER
        self.free_pick = free
        self.offers = self.run.offers(3)
        self.build_trader_menu()

    def build_trader_menu(self):
        items, hints, colours, enabled = [], [], [], []
        for i in self.offers:
            name, upgrade, _price, blurb = data.SHOP[i]
            level = self.run.upgrades[upgrade]
            price = self.run.price(i)
            stars = "*" * level
            if self.free_pick:
                items.append("%-17s %s" % (name, stars))
                hints.append(blurb)
                colours.append(data.CYAN)
                enabled.append(True)
            else:
                ok = self.run.can_buy(i)
                items.append("%-17s %3d  %s" % (name, price, stars))
                hints.append(blurb if ok else
                             ("Maxed out" if level >= 3 else
                              "Need %d more crystals" % (price - self.run.crystals)))
                colours.append(data.YELLOW)
                enabled.append(ok)
        if not self.free_pick:
            items.append("LEAVE")
            hints.append("Back to the map")
            colours.append(data.WHITE)
            enabled.append(True)
        self.menu = ui.Menu(items, hints, colours, enabled)

    def enter_event(self):
        self.state = EVENT
        self.event = self.run.rng.choice(data.EVENTS)
        title, line, a, b = self.event
        self.menu = ui.Menu([a[0], b[0]],
                            ["", ""], [data.VIOLET, data.VIOLET])

    def resolve_event(self, choice):
        _title, _line, a, b = self.event
        label, effect, value = (a if choice == 0 else b)
        run = self.run
        if effect == "crystals":
            run.crystals += value
            self.message = ("SALVAGE", data.CYAN, "+%d crystals" % value)
        elif effect == "risky":
            if run.rng.random() < 0.6:
                run.crystals += value
                self.message = ("SALVAGE", data.CYAN, "+%d crystals" % value)
            else:
                run.hull -= 2
                self.message = ("HULL BREACH", data.RED, "-2 hull")
        elif effect == "repair":
            run.heal(value)
            self.message = ("REPAIRS", data.GREEN, "+%d hull" % value)
        elif effect == "freeupgrade":
            self.enter_trader(free=True)
            return
        elif effect == "maxhull":
            if run.crystals >= value:
                run.crystals -= value
                run.max_hull += 2
                run.heal(2)
                self.message = ("THE SHRINE ANSWERS", data.GREEN, "+2 max hull")
            else:
                self.message = ("NOTHING HAPPENS", data.GREY, "Not enough crystals")
        elif effect == "ambush":
            self.state = COMBAT
            self.combat = Combat(run, data.N_ELITE, self.art)
            self.pending = data.N_ELITE
            return
        else:
            self.message = ("YOU MOVE ON", data.GREY, "Nothing out here")
        self.state = REST

    def after_combat(self, won):
        if not won:
            self.state = GAMEOVER
            return
        if self.pending in (data.N_ELITE, data.N_BOSS):
            self.enter_trader(free=True)
        else:
            self.run.crystals += 6 + self.run.upgrades[data.U_GREED] * 3
            self.advance()

    def advance(self):
        """Leave the node we just resolved, and move the run forward."""
        if self.map.finished():
            self.run.sector += 1
            if self.run.sector == 5:
                self.run.cleared = True
            self.state = INTERLUDE
            self.message = None
        else:
            self.enter_map()

    # -- input ------------------------------------------------------------
    def movement(self, keys, index):
        if index == 0:
            dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - \
                 (keys[pygame.K_LEFT] or keys[pygame.K_a])
            dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - \
                 (keys[pygame.K_UP] or keys[pygame.K_w])
        else:
            dx = keys[pygame.K_d] - keys[pygame.K_a]
            dy = keys[pygame.K_s] - keys[pygame.K_w]
        return dx, dy

    def combat_inputs(self):
        keys = pygame.key.get_pressed()
        inp = {"bomb": keys[pygame.K_SPACE] or keys[pygame.K_LSHIFT]}
        if self.players > 1:
            # split the keyboard: P1 on the arrows, P2 on WASD
            inp["move0"] = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT],
                            keys[pygame.K_DOWN] - keys[pygame.K_UP])
            inp["move1"] = (keys[pygame.K_d] - keys[pygame.K_a],
                            keys[pygame.K_s] - keys[pygame.K_w])
        else:
            inp["move0"] = self.movement(keys, 0)
        return inp

    def handle_event(self, e):
        if e.type == pygame.QUIT:
            self.running = False
            return
        if e.type != pygame.KEYDOWN:
            return
        if e.key == pygame.K_F11 or (e.key == pygame.K_RETURN and
                                     (e.mod & pygame.KMOD_ALT)):
            self.toggle_fullscreen()
            return
        if e.key == pygame.K_F1:
            self.crt_on = not self.crt_on
            return
        if e.key in (pygame.K_KP_PLUS, pygame.K_EQUALS):
            self.set_scale(self.scale + 1)
            return
        if e.key in (pygame.K_KP_MINUS, pygame.K_MINUS):
            self.set_scale(self.scale - 1)
            return

        if self.state == TITLE:
            choice = self.menu.key(e)
            if choice == 0:
                self.start_run(1)
            elif choice == 1:
                self.start_run(2)
            elif choice == 2:
                self.difficulty = (self.difficulty + 1) % len(data.DIFFICULTIES)
                self.enter_title()
            elif choice == 3:
                self.running = False
        elif self.state == MAP:
            opts = self.map.options()
            if not opts:
                return
            if e.key in (pygame.K_UP, pygame.K_w):
                self.sel_index = (self.sel_index - 1) % len(opts)
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.sel_index = (self.sel_index + 1) % len(opts)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                node = opts[self.sel_index]
                kind = self.map.advance(node)
                self.enter_node(kind)
            self.selected = opts[min(self.sel_index, len(opts) - 1)]
        elif self.state == TRADER:
            choice = self.menu.key(e)
            if choice is None:
                return
            if self.free_pick:
                self.run.grant(data.SHOP[self.offers[choice]][1])
                self.advance()
            elif choice == len(self.menu.items) - 1:
                self.advance()
            else:
                i = self.offers[choice]
                if self.run.can_buy(i):
                    self.run.crystals -= self.run.price(i)
                    self.run.grant(data.SHOP[i][1])
                    self.build_trader_menu()
        elif self.state == EVENT:
            choice = self.menu.key(e)
            if choice is not None:
                self.resolve_event(choice)
        elif self.state == REST:
            if e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self.advance()
        elif self.state == INTERLUDE:
            if e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self.new_sector()
        elif self.state == GAMEOVER:
            if e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self.enter_title()

    # -- update / draw ----------------------------------------------------
    def update(self, dt):
        self.t += dt
        self.flash.update(dt)
        if self.state == COMBAT:
            self.combat.update(dt, self.combat_inputs())
            if self.combat.result is not None:
                self.after_combat(self.combat.result)
        else:
            self.stars.update(dt, 0.35)
            self.title_particles.update(dt)

    def draw(self):
        c = self.canvas
        if self.state == COMBAT:
            self.combat.draw(c)
            boss = self.combat.boss if self.combat.is_boss else None
            ui.draw_hud(c, self.art, self.run, self.combat.tag, boss)
            ox, oy = self.combat.shake.offset()
        else:
            ox = oy = 0
            if self.state == TITLE:
                self.draw_title(c)
            elif self.state == MAP:
                sector.draw_map(c, self.art, self.map, self.run,
                                self.selected, self.t)
            elif self.state == TRADER:
                self.draw_trader(c)
            elif self.state == EVENT:
                self.draw_event(c)
            elif self.state == REST:
                self.draw_message(c)
            elif self.state == INTERLUDE:
                self.draw_interlude(c)
            elif self.state == GAMEOVER:
                self.draw_gameover(c)

        frame = pygame.transform.scale(c, self.screen.get_size())
        self.screen.fill((0, 0, 0))
        self.screen.blit(frame, (ox * self.scale, oy * self.scale))
        if self.crt_on:
            self.screen.blit(self.crt, (0, 0))
        pygame.display.flip()

    def draw_title(self, c):
        c.fill(data.VOID)
        self.stars.draw(c)
        pygame.draw.rect(c, data.CYAN, (0, 56, data.W, 2))
        pygame.draw.rect(c, data.CYAN, (0, 104, data.W, 2))
        ui.text(c, self.art, "N O V A", data.W // 2, 66, data.WHITE,
                centre=True, big=True)
        ui.text(c, self.art, "a space rogue-lite", data.W // 2, 110,
                data.GREY, centre=True)
        # 138 keeps the menu's own hint line clear of the shortcut line below
        self.menu.draw(c, self.art, 138, self.t)
        ui.text(c, self.art, "F11 fullscreen    F1 CRT filter    +/- window size",
                data.W // 2, 256, data.DARK, centre=True)

    def draw_trader(self, c):
        if self.free_pick:
            ui.panel(c, self.art, "SALVAGE", data.CYAN, "Take one")
        else:
            ui.panel(c, self.art, "TRADER", data.YELLOW)
            ui.text(c, self.art, "%d crystals" % self.run.crystals, 16, 54,
                    data.CYAN)
            ui.text(c, self.art, "hull %d/%d" % (self.run.hull, self.run.max_hull),
                    data.W - 16, 54, data.GREEN, right=True)
        self.menu.draw(c, self.art, 96, self.t)

    def draw_event(self, c):
        title, line, _a, _b = self.event
        ui.panel(c, self.art, title, data.VIOLET, line)
        self.menu.draw(c, self.art, 120, self.t)

    def draw_message(self, c):
        title, colour, line = self.message
        ui.panel(c, self.art, title, colour)
        ui.text(c, self.art, line, data.W // 2, 120, data.WHITE, centre=True)
        ui.text(c, self.art, "hull %d/%d" % (self.run.hull, self.run.max_hull),
                data.W // 2, 146, data.GREY, centre=True)
        ui.text(c, self.art, "ENTER", data.W // 2, 226, data.DARK, centre=True)

    def draw_interlude(self, c):
        s = self.run.sector
        cleared = s == 5
        ui.panel(c, self.art, "VICTORY" if cleared else "SECTOR CLEARED",
                 data.GREEN if cleared else data.SECTOR_COLOURS[(s - 1) % 5])
        if s >= 5:
            ui.text(c, self.art, "The void has no edge.", data.W // 2, 110,
                    data.VIOLET, centre=True)
            ui.text(c, self.art, "Void depth %d" % (s - 4), data.W // 2, 132,
                    data.WHITE, centre=True)
        else:
            ui.text(c, self.art, "Entering sector %d" % (s + 1), data.W // 2,
                    118, data.WHITE, centre=True)
        ui.text(c, self.art, "score %07d" % self.run.score, data.W // 2, 160,
                data.YELLOW, centre=True)
        ui.text(c, self.art, "ENTER", data.W // 2, 226, data.DARK, centre=True)

    def draw_gameover(self, c):
        run = self.run
        ui.panel(c, self.art, "SHIP LOST", data.RED)
        if run.sector > 4:
            ui.text(c, self.art, "Void depth %d" % (run.sector - 4), data.W // 2,
                    104, data.VIOLET, centre=True)
        else:
            ui.text(c, self.art, "Sector %d" % (run.sector + 1), data.W // 2,
                    104, data.WHITE, centre=True)
        ui.text(c, self.art, "score %07d" % run.score, data.W // 2, 128,
                data.YELLOW, centre=True)
        ui.text(c, self.art, "%s   seed %05d" % (run.diff_name, run.seed),
                data.W // 2, 152, data.GREY, centre=True)
        if run.cleared:
            ui.text(c, self.art, "campaign cleared", data.W // 2, 176,
                    data.GREEN, centre=True)
        ui.text(c, self.art, "ENTER to return to the title", data.W // 2, 226,
                data.DARK, centre=True)

    # -- loop -------------------------------------------------------------
    def loop(self):
        while self.running:
            dt = min(self.clock.tick(60) / 1000.0, 1 / 20.0)
            for e in pygame.event.get():
                self.handle_event(e)
            self.update(dt)
            self.draw()
        pygame.quit()
