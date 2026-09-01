"""Gamepad support, kept separate so the rest of the game never asks where a
direction came from.

Pads are matched to players by connection order: the first pad drives player 1,
the second player 2. Both keyboard and pad stay live at all times -- in co-op
one player can hold a controller while the other uses the keys, which is how
these things actually get played on a sofa.

Hot-plugging is handled: pads found at startup and pads plugged in later go
through the same path.
"""

import pygame

DEADZONE = 0.35

# SDL's standard layout: 0 south, 1 east, 2 west, 3 north. The sets below must
# not overlap -- an earlier version had button 1 in both CONFIRM and BACK, so
# one press emitted both and menus took a choice and cancelled it in the same
# frame.
CONFIRM = (0, 2, 3)         # south / west / north confirm
BACK = (1,)                 # east cancels, as every console has taught people
START = (6, 7, 9, 11)       # start, in its various numberings
BOMB = (0, 2, 4, 5)         # south, west, or either shoulder


class Pads:
    def __init__(self):
        self.pads = []
        self.prev = {}
        try:
            pygame.joystick.init()
        except Exception:
            return
        for i in range(pygame.joystick.get_count()):
            self._add(i)

    # -- plumbing ---------------------------------------------------------
    def _add(self, index):
        try:
            js = pygame.joystick.Joystick(index)
            js.init()
        except Exception:
            return
        if any(p.get_instance_id() == js.get_instance_id() for p in self.pads):
            return
        self.pads.append(js)

    def handle_event(self, e):
        """Returns True if the event was a pad hot-plug."""
        if e.type == pygame.JOYDEVICEADDED:
            self._add(e.device_index)
            return True
        if e.type == pygame.JOYDEVICEREMOVED:
            self.pads = [p for p in self.pads
                         if p.get_instance_id() != e.instance_id]
            return True
        return False

    @property
    def count(self):
        return len(self.pads)

    def pad_for(self, player):
        return self.pads[player] if player < len(self.pads) else None

    # -- reading ----------------------------------------------------------
    def direction(self, player):
        """(dx, dy) in -1..1 from stick or d-pad, or (0, 0)."""
        js = self.pad_for(player)
        if js is None:
            return 0, 0
        dx = dy = 0
        try:
            if js.get_numaxes() >= 2:
                ax, ay = js.get_axis(0), js.get_axis(1)
                if abs(ax) > DEADZONE:
                    dx = 1 if ax > 0 else -1
                if abs(ay) > DEADZONE:
                    dy = 1 if ay > 0 else -1
            if js.get_numhats() >= 1 and (dx == 0 and dy == 0):
                hx, hy = js.get_hat(0)
                dx = hx
                dy = -hy                    # SDL hats are y-up, the game is y-down
        except Exception:
            return 0, 0
        return dx, dy

    def held(self, player, buttons):
        js = self.pad_for(player)
        if js is None:
            return False
        try:
            n = js.get_numbuttons()
            return any(b < n and js.get_button(b) for b in buttons)
        except Exception:
            return False

    def bomb(self, player):
        return self.held(player, BOMB)

    # -- menu edges -------------------------------------------------------
    def menu_edges(self):
        """Menu navigation as discrete presses.

        A held stick would otherwise scroll a menu at sixty steps a second, so
        this reports only transitions, and only from pad 0.
        """
        out = []
        js = self.pad_for(0)
        if js is None:
            return out
        dx, dy = self.direction(0)
        confirm = self.held(0, CONFIRM)
        back = self.held(0, BACK)
        start = self.held(0, START)
        prev = self.prev.get(0, (0, 0, False, False, False))
        if dy != prev[1]:
            if dy < 0:
                out.append("up")
            elif dy > 0:
                out.append("down")
        if confirm and not prev[2]:
            out.append("confirm")
        elif back and not prev[3]:
            out.append("back")
        if start and not prev[4]:
            # Start is its own edge now rather than another confirm: it opens
            # and closes the pause menu, which is what start does everywhere
            # else, and the game decides what that means on the title screen.
            out.append("start")
        self.prev[0] = (dx, dy, confirm, back, start)
        return out

    def name(self, player=0):
        js = self.pad_for(player)
        if js is None:
            return None
        try:
            return js.get_name()
        except Exception:
            return "gamepad"
