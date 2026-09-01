"""Export a WAV of the sound catalogue, so it can be heard without running the
game (and reviewed in a pull request like any other artefact)."""

import os
import sys
import wave

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
PC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PC)

import numpy as np
import pygame

pygame.init()
pygame.display.set_mode((64, 64))

from nova import audio as A

# Repeat counts are chosen so the guns run through a full rotation of their
# pitch variants -- hearing them in isolation is the point of the file.
ORDER = [
    ("shoot", 6), ("shoot_big", 3), ("enemy_shoot", 3), ("hit", 4),
    ("crystal", 3), ("repair", 1), ("explode", 2), ("explode_big", 1),
    ("shield_up", 1), ("shield_break", 1), ("hurt", 1), ("bomb", 1),
    ("menu_move", 3), ("menu_ok", 1), ("menu_no", 1), ("buy", 1),
    ("jump", 1), ("boss_warn", 1), ("sector_clear", 1), ("game_over", 1),
]


def main():
    engine = A.Audio(True)
    if not engine.ok:
        print("audio engine unavailable")
        return 1

    gap = np.zeros(int(A.RATE * 0.16), dtype=np.int16)
    chunks = []
    for name, times in ORDER:
        # gun names are aliases for a set of variants; play them in turn, the
        # way the engine does
        variants = A.gun_variants(name)
        for i in range(times):
            arr = pygame.sndarray.array(engine.effects[variants[i % len(variants)]])
            chunks.append(arr[:, 0].astype(np.int16))
            chunks.append(gap[:int(A.RATE * 0.07)])
        chunks.append(gap)

    chunks.append(np.zeros(int(A.RATE * 0.4), dtype=np.int16))
    track = pygame.sndarray.array(A.build_track(0, 1))[:, 0].astype(np.int16)
    chunks.append(track[:int(A.RATE * 12)])

    out = np.concatenate(chunks)
    path = os.path.normpath(os.path.join(PC, "..", "docs", "nova-sound-demo.wav"))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(A.RATE)
        w.writeframes(out.tobytes())
    print("wrote %s  (%.1f s, %d KB)" %
          (os.path.relpath(path, os.path.dirname(PC)),
           len(out) / A.RATE, os.path.getsize(path) // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
