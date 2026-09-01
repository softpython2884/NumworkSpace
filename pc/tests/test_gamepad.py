"""Exercise the pad mapping with a stand-in device.

No controller can be plugged into CI, and a mapping that is only ever tested by
hand is a mapping that breaks quietly. This drives the real Pads logic with a
fake joystick: axes, d-pad, buttons, menu edges and hot-unplug.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import pygame

from nova.gamepad import Pads


class FakePad:
    def __init__(self, iid=1):
        self.axes = [0.0, 0.0]
        self.hat = (0, 0)
        self.buttons = [False] * 12
        self.iid = iid

    def get_instance_id(self):
        return self.iid

    def get_numaxes(self):
        return len(self.axes)

    def get_numhats(self):
        return 1

    def get_numbuttons(self):
        return len(self.buttons)

    def get_axis(self, i):
        return self.axes[i]

    def get_hat(self, i):
        return self.hat

    def get_button(self, i):
        return self.buttons[i]

    def get_name(self):
        return "fake pad"


def main():
    pygame.init()
    pads = Pads()
    pad = FakePad()
    pads.pads = [pad]
    ok = True

    def check(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print("  %-34s %-12s %s" % (label, str(got), "ok" if good else
                                    "FAIL, wanted %s" % (want,)))

    print("stick and d-pad")
    check("neutral", pads.direction(0), (0, 0))
    pad.axes = [0.9, 0.0]
    check("stick right", pads.direction(0), (1, 0))
    pad.axes = [-0.9, -0.8]
    check("stick up-left", pads.direction(0), (-1, -1))
    pad.axes = [0.2, 0.2]
    check("inside deadzone", pads.direction(0), (0, 0))
    pad.axes = [0.0, 0.0]
    pad.hat = (1, 1)
    # SDL reports hat y up-positive; the game's y grows downward
    check("d-pad up-right", pads.direction(0), (1, -1))
    pad.hat = (0, -1)
    check("d-pad down", pads.direction(0), (0, 1))
    pad.hat = (0, 0)

    print("\nbuttons")
    check("bomb released", pads.bomb(0), False)
    pad.buttons[0] = True
    check("south button bombs", pads.bomb(0), True)
    pad.buttons[0] = False

    print("\nmenu edges are transitions, not held state")
    pads.prev.clear()
    pad.hat = (0, -1)
    check("first frame down", pads.menu_edges(), ["down"])
    check("held, second frame", pads.menu_edges(), [])
    pad.hat = (0, 0)
    pads.menu_edges()
    pad.buttons[0] = True
    check("south confirms", pads.menu_edges(), ["confirm"])
    check("confirm held", pads.menu_edges(), [])
    pad.buttons[0] = False
    pads.menu_edges()
    pad.buttons[1] = True
    check("east cancels, only", pads.menu_edges(), ["back"])
    pad.buttons[1] = False
    pads.menu_edges()

    print("\nbutton sets must not overlap")
    from nova import gamepad as gp
    overlap = set(gp.CONFIRM) & set(gp.BACK)
    check("confirm vs back", sorted(overlap), [])
    overlap = set(gp.CONFIRM) & set(gp.START)
    check("confirm vs start", sorted(overlap), [])

    print("\nabsence and hot-unplug")
    pads.pads = []
    check("no pad: direction", pads.direction(0), (0, 0))
    check("no pad: bomb", pads.bomb(0), False)
    check("no pad: menu", pads.menu_edges(), [])
    check("no pad: name", pads.name(0), None)

    print()
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
