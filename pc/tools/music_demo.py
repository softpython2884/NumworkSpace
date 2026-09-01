"""Export the music to a WAV, including a proof that the loop has no seam.

Three parts:

  1. a sector track from the top, long enough to hear the four sections
  2. the loop point itself -- the last seconds of the track followed by its
     first seconds, which is exactly what your ears get when it repeats
  3. the Void's own track, so it is obvious the six are not one tune tinted
     six ways

Part 2 is the one worth listening for. If the loop had a seam you would hear a
tick at the join, and the old tracks did: measured, three of the five ended on
a waveform step five to sixteen times their own 99th-percentile sample step.
"""

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


def samples(sound):
    return pygame.sndarray.array(sound)[:, 0].astype(np.int16)


def seconds(n):
    return np.zeros(int(A.RATE * n), dtype=np.int16)


def main():
    pygame.mixer.quit()
    pygame.mixer.init(frequency=A.RATE, size=-16, channels=2, buffer=512)

    first = samples(A.build_track(0, 1))
    void = samples(A.build_track(len(A.SECTOR_TRACKS) - 1, 1))
    rate = A.RATE

    parts = []
    # 1. sector one, from the top: two sections, so the melody is stated and
    #    then answered an octave up
    parts.append(first[:int(rate * 42)])
    parts.append(seconds(1.2))

    # 2. the seam. Six seconds either side of the wrap, played straight
    #    through -- there is no edit here, it is the file's own end and start.
    parts.append(first[-int(rate * 6):])
    parts.append(first[:int(rate * 6)])
    parts.append(seconds(1.2))

    # 3. the Void
    parts.append(void[:int(rate * 24)])

    out = np.concatenate(parts)
    path = os.path.normpath(os.path.join(PC, "..", "docs",
                                         "nova-music-demo.wav"))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(out.tobytes())

    print("track lengths: %s seconds"
          % [round(len(samples(A.build_track(i, 1))) / rate, 1)
             for i in range(len(A.SECTOR_TRACKS))])
    print("wrote %s  (%.1f s, %d KB)"
          % (os.path.relpath(path, os.path.dirname(PC)),
             len(out) / rate, os.path.getsize(path) // 1024))
    print("  0:00  sector one, from the top")
    print("  0:42  the loop point: six seconds either side of the wrap")
    print("  0:55  the Void")
    return 0


if __name__ == "__main__":
    sys.exit(main())
