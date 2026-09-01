"""Run the PC test suite."""

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE = [("full runs", "test_run.py"),
         ("sound catalogue", "test_audio.py"),
         ("gamepad mapping", "test_gamepad.py"),
         ("frame budget", "test_perf.py")]


def main():
    env = dict(os.environ)
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    env.setdefault("SDL_AUDIODRIVER", "dummy")
    ok = True
    for name, script in SUITE:
        t0 = time.time()
        p = subprocess.run([sys.executable, os.path.join(HERE, script)],
                           capture_output=True, text=True, env=env)
        good = p.returncode == 0
        ok &= good
        print("  %-14s %-5s %6.1fs" % (name, "PASS" if good else "FAIL",
                                       time.time() - t0))
        if not good:
            print(p.stdout[-2500:])
            print(p.stderr[-1500:])
    print("ALL PASS" if ok else "FAILURES ABOVE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
