"""Measure how much MicroPython heap the game actually needs to load.

The NumWorks gives Python 32 KB of heap, and that heap has to hold the compiled
bytecode, every runtime object, *and* the parse tree while a module is being
compiled. The parse tree is the killer: it is several times the size of the
source file and it exists all at once.

Counting bytes in the .py file does not measure any of that. This does: it runs
the real MicroPython 1.17 interpreter (the version Epsilon ships) and bisects for
the smallest heap that can import the game.

Build the interpreter once:

    tools/mp/build.sh

The interpreter here is a 64-bit build, so its pointers are twice the width of
the calculator's 32-bit ARM. Object-heavy structures -- the parse tree above all
-- therefore cost roughly twice as much here. We budget against 2x the device's
32 KB and keep headroom on top, which is the conservative direction.
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MP = os.path.join(ROOT, "tools", "mp", "micropython")
STUBS = os.path.join(ROOT, "tools", "mp", "stubs")

DEVICE_HEAP = 32 * 1024
# 64-bit pointers double the parse tree, so this build's budget is 2x the
# device's, minus headroom for what the game allocates once it is running.
BUDGET_K = 48


def probe(heap_k, entry, workdir):
    src = ("import kandinsky, ion, time, gc, sys\n"
           "sys.path.insert(0, %r)\n"
           "gc.collect()\n"
           "b = gc.mem_free()\n"
           "import %s\n"
           "gc.collect()\n"
           "print('OK', b - gc.mem_free(), gc.mem_free())\n" % (workdir, entry))
    path = os.path.join(STUBS, "_probe.py")
    with open(path, "w") as fh:
        fh.write(src)
    try:
        r = subprocess.run([MP, "-X", "heapsize=%dk" % heap_k, "_probe.py"],
                           capture_output=True, text=True, cwd=STUBS, timeout=90)
    except subprocess.TimeoutExpired:
        return None
    if r.stdout.startswith("OK"):
        parts = r.stdout.split()
        return int(parts[1]), int(parts[2])
    return None


def min_heap(entry, workdir):
    """Smallest heap (KB) that can import `entry`, by bisection."""
    lo, hi = 8, 512
    if probe(hi, entry, workdir) is None:
        return None, None, None
    best = None
    while lo < hi:
        mid = (lo + hi) // 2
        got = probe(mid, entry, workdir)
        if got:
            hi = mid
            best = got
        else:
            lo = mid + 1
    got = probe(lo, entry, workdir) or best
    return lo, got[0], got[1]


def prepare(path, workdir):
    """Copy the game next to the stubs with its entry-point call removed."""
    import re
    with open(path) as fh:
        lines = fh.read().rstrip("\n").split("\n")
    if re.match(r"^[A-Za-z_]\w*\(\)$", lines[-1]):
        lines = lines[:-1]
    name = os.path.basename(path)
    with open(os.path.join(workdir, name), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return name[:-3]


def main(argv):
    if not os.path.exists(MP):
        print("MicroPython interpreter not built.")
        print("Run:  tools/mp/build.sh")
        return 2

    targets = argv[1:] or [os.path.join(ROOT, "dist", "nova.py")]
    workdir = os.path.join(ROOT, "tools", "mp", "work")
    os.makedirs(workdir, exist_ok=True)

    # Every dist/*.py module must be importable, so stage them all.
    dist = os.path.join(ROOT, "dist")
    for f in sorted(os.listdir(dist)):
        if f.endswith(".py"):
            prepare(os.path.join(dist, f), workdir)

    print("%-22s %8s %10s %10s %8s" %
          ("module", "bytes", "min heap", "resident", "verdict"))
    print("-" * 64)
    worst = 0
    ok = True
    for t in targets:
        entry = prepare(t, workdir)
        size = os.path.getsize(t)
        heap_k, resident, free = min_heap(entry, workdir)
        if heap_k is None:
            print("%-22s %8d %10s %10s %8s" %
                  (os.path.basename(t), size, "FAIL", "-", "FAIL"))
            ok = False
            continue
        worst = max(worst, heap_k)
        good = heap_k <= BUDGET_K
        ok &= good
        print("%-22s %8d %9dK %10d %8s" %
              (os.path.basename(t), size, heap_k, resident,
               "ok" if good else "TOO BIG"))

    print("-" * 64)
    print("budget on this 64-bit build : %dK" % BUDGET_K)
    print("device heap (NumWorks)      : %dK" % (DEVICE_HEAP // 1024))
    print("worst module measured       : %dK" % worst)
    print()
    print("PASS" if ok else
          "FAIL: needs more heap than a NumWorks has -- it will MemoryError")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
