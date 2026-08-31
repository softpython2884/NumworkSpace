"""Load NOVA against the headless calculator stubs.

The game ships as five modules because the calculator compiles a module's whole
parse tree in RAM at once, so the peak is set by the largest single module. That
makes a test's life harder: a name lives in exactly one module, but a test wants
to reach all of them. This loads the chain and hands back one namespace that
reads from, and writes through to, every module that holds the name.

Writing through matters: `from x import f` copies the reference, so replacing
`keydown` for a test has to replace it in each module that imported it.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMU = os.path.join(ROOT, "tools", "emu")
CHAIN = ["novad", "novae", "novaf", "novag", "nova"]


class FakeTime:
    """Virtual clock: monotonic() only advances when the game sleeps, so a
    25 fps loop runs as fast as the CPU allows and still sees sane timings."""

    def __init__(self):
        self.t = 0.0

    def monotonic(self):
        self.t += 0.0005
        return self.t

    def sleep(self, d):
        if d > 0:
            self.t += d


class Namespace:
    """One view over the module chain, addressed by source names."""

    def __init__(self, mods, mapping):
        self._mods = mods           # ordered dicts of module globals
        self._m = mapping or {}

    def _key(self, k):
        return self._m.get(k, k)

    def __getitem__(self, k):
        kk = self._key(k)
        for g in reversed(self._mods):
            if kk in g:
                return g[kk]
        raise KeyError(k)

    def __setitem__(self, k, v):
        kk = self._key(k)
        hit = False
        for g in self._mods:
            if kk in g:
                g[kk] = v
                hit = True
        if not hit:
            self._mods[-1][kk] = v

    def __contains__(self, k):
        kk = self._key(k)
        return any(kk in g for g in self._mods)

    def get(self, k, default=None):
        try:
            return self[k]
        except KeyError:
            return default


def load(src_dir=None, clock=None):
    """Return (namespace, kandinsky, ion, clock)."""
    if EMU not in sys.path:
        sys.path.insert(0, EMU)
    import kandinsky
    import ion

    clock = clock or FakeTime()
    sys.modules["time"] = clock
    src_dir = src_dir or os.environ.get("NOVA_SRC") or os.path.join(ROOT, "src")

    kandinsky._reset()
    ion._reset()

    mapping = {}
    mpath = os.path.join(src_dir, "nova.map.json")
    if os.path.exists(mpath):
        import json
        with open(mpath) as fh:
            mapping = json.load(fh)

    mods = []
    ns = {}
    for name in CHAIN:
        with open(os.path.join(src_dir, name + ".py")) as fh:
            text = fh.read()
        if name == "nova":
            # strip the entry-point call so importing does not start the game
            import re
            lines = text.rstrip("\n").split("\n")
            assert re.match(r"^[A-Za-z_]\w*\(\)$", lines[-1]), lines[-1]
            text = "\n".join(lines[:-1]) + "\n"
        g = {"__name__": name}
        # star-imports resolve against what earlier modules produced
        sys.modules[name] = _Mod(g)
        exec(compile(text, name, "exec"), g)
        mods.append(g)
        ns = g
    return Namespace(mods, mapping), kandinsky, ion, clock


class _Mod:
    """Minimal module object so `from novad import X` finds the exec'd globals."""

    def __init__(self, g):
        self.__dict__ = g
