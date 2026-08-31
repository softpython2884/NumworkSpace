"""Load nova.py against the headless calculator stubs.

The game calls main() at import time, because that is how Epsilon runs a script
(it imports it -- `__name__` is never "__main__" there, so the usual guard would
silently do nothing on the real device). The harness therefore loads the source
with that final call removed and hands back the module namespace.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMU = os.path.join(ROOT, "tools", "emu")
if EMU not in sys.path:
    sys.path.insert(0, EMU)


class FakeTime:
    """Virtual clock: monotonic() advances only when the game sleeps, so a
    25 fps loop runs as fast as the CPU allows and still sees sane timings."""

    def __init__(self):
        self.t = 0.0
        self.slept = 0.0

    def monotonic(self):
        self.t += 0.0005          # pretend the frame took half a millisecond
        return self.t

    def sleep(self, d):
        if d > 0:
            self.t += d
            self.slept += d


class Namespace(dict):
    """Module globals addressed by their *source* names.

    dist/nova.py has every identifier renamed, so the tests would not find
    `plx` or `fight` in it. The build writes its rename table next to the
    output; this proxy applies it on both reads and writes, which lets the
    identical test suite run against the shipped artifact.
    """

    def __init__(self, g, mapping):
        super().__init__()
        self._g = g
        self._m = mapping

    def _key(self, k):
        return self._m.get(k, k)

    def __getitem__(self, k):
        return self._g[self._key(k)]

    def __setitem__(self, k, v):
        self._g[self._key(k)] = v

    def __contains__(self, k):
        return self._key(k) in self._g

    def get(self, k, default=None):
        return self._g.get(self._key(k), default)

    def __len__(self):
        return len(self._g)


def load(path=None, clock=None):
    """Return (module_globals, kandinsky, ion, clock).

    Set NOVA_SRC to point the whole suite at a different build.
    """
    import kandinsky
    import ion

    clock = clock or FakeTime()
    sys.modules["time"] = clock
    src_path = path or os.environ.get("NOVA_SRC") or os.path.join(ROOT, "src", "nova.py")
    with open(src_path) as fh:
        src = fh.read()

    # Drop the trailing entry-point call. In dist/ the function has been
    # renamed, so match the shape of the line rather than its spelling.
    import re
    lines = src.rstrip("\n").split("\n")
    assert re.match(r"^[A-Za-z_][A-Za-z_0-9]*\(\)$", lines[-1]), (
        "expected a trailing entry-point call in " + src_path + ", got: " + lines[-1])
    stripped = "\n".join(lines[:-1]) + "\n"

    kandinsky._reset()
    ion._reset()
    g = {"__name__": "nova"}
    exec(compile(stripped, "nova", "exec"), g)
    g["_clock"] = clock

    mapping_path = src_path.replace(".py", ".map.json")
    if os.path.exists(mapping_path):
        import json
        with open(mapping_path) as fh:
            g = Namespace(g, json.load(fh))
    return g, kandinsky, ion, clock


def restore_time():
    import time as realtime
    sys.modules["time"] = realtime
