#!/usr/bin/env python3
"""NOVA -- a space rogue-lite. PC edition.

    python3 nova.py [--scale N] [--fullscreen] [--no-crt]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser(description="NOVA - space rogue-lite")
    ap.add_argument("--scale", type=int, default=3,
                    help="window scale, 1-6 (default 3 -> 1440x810)")
    ap.add_argument("--fullscreen", action="store_true")
    ap.add_argument("--no-crt", action="store_true",
                    help="disable the scanline overlay")
    args = ap.parse_args()

    from nova.game import Game
    Game(scale=args.scale, fullscreen=args.fullscreen,
         crt=not args.no_crt).loop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
