"""Run the whole suite against src/nova.py and again against dist/nova.py.

The minified build is what actually ships, so it is what actually has to work.
Testing only the readable source would leave the minifier unverified.
"""

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SUITE = [
    ("controls", "test_controls.py"),
    ("map", "test_map.py"),
    ("termination", "test_termination.py"),
    ("endless", "test_endless.py"),
    ("performance", "test_combat.py"),
]


def run(name, script, src):
    env = dict(os.environ)
    if src:
        env["NOVA_SRC"] = src
    t0 = time.time()
    p = subprocess.run([sys.executable, os.path.join(HERE, script)],
                       capture_output=True, text=True, env=env, cwd=ROOT)
    dt = time.time() - t0
    ok = p.returncode == 0
    print("  %-13s %-5s  %5.1fs" % (name, "PASS" if ok else "FAIL", dt))
    if not ok:
        print(p.stdout[-2500:])
        print(p.stderr[-2000:])
    return ok


def main():
    targets = [("src/nova.py", None)]
    dist = os.path.join(ROOT, "dist", "nova.py")
    if os.path.exists(dist):
        targets.append(("dist/nova.py (shipped build)", dist))

    all_ok = True
    for label, src in targets:
        print("== %s ==" % label)
        for name, script in SUITE:
            all_ok &= run(name, script, src)
        print()

    print("ALL PASS" if all_ok else "FAILURES ABOVE")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
