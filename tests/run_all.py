"""Run the suite against src/ and again against the shipped dist/ build."""

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SUITE = [("controls", "test_controls.py"),
         ("termination", "test_termination.py"),
         ("endless", "test_endless.py"),
         ("performance", "test_combat.py")]


def run(name, script, src):
    env = dict(os.environ)
    if src:
        env["NOVA_SRC"] = src
    t0 = time.time()
    p = subprocess.run([sys.executable, os.path.join(HERE, script)],
                       capture_output=True, text=True, env=env, cwd=ROOT)
    ok = p.returncode == 0
    print("  %-13s %-5s  %5.1fs" % (name, "PASS" if ok else "FAIL", time.time() - t0))
    if not ok:
        print(p.stdout[-2000:])
        print(p.stderr[-1500:])
    return ok


def main():
    targets = [("src/", None)]
    dist = os.path.join(ROOT, "dist")
    if os.path.exists(os.path.join(dist, "nova.py")):
        targets.append(("dist/ (shipped build)", dist))
    ok = True
    for label, src in targets:
        print("== %s ==" % label)
        for name, script in SUITE:
            ok &= run(name, script, src)
        print()
    print("ALL PASS" if ok else "FAILURES ABOVE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
