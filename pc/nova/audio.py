"""Chiptune sound, synthesised at startup. No audio files anywhere.

Every effect is built from square, triangle and noise waves with a hard
envelope -- the same four ingredients an NES had. That keeps the repository
free of binary assets, makes each sound a couple of readable lines instead of
a WAV nobody can edit, and means the whole soundtrack costs about a megabyte
of RAM and a fraction of a second to build.

If numpy or the mixer is unavailable the game runs silently rather than
failing: sound is a garnish, not a dependency.
"""

import math
import random

try:
    import numpy as _np
except ImportError:                                   # pragma: no cover
    _np = None

import pygame

RATE = 22050          # deliberately low: it is part of the sound
MASTER = 0.55

# Note names to frequency, A4 = 440. Two octaves is plenty for chiptune.
_NOTES = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3,
          "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}


def note(name, octave=4):
    return 440.0 * (2.0 ** ((_NOTES[name] + (octave - 4) * 12) / 12.0))


class Synth:
    """Waveform generators. Each returns a float array in [-1, 1]."""

    @staticmethod
    def _t(duration):
        n = max(1, int(RATE * duration))
        return _np.arange(n, dtype=_np.float32) / RATE

    @staticmethod
    def square(freq, duration, duty=0.5):
        t = Synth._t(duration)
        phase = (t * freq) % 1.0
        return _np.where(phase < duty, 1.0, -1.0).astype(_np.float32)

    @staticmethod
    def triangle(freq, duration):
        t = Synth._t(duration)
        phase = (t * freq) % 1.0
        return (4.0 * _np.abs(phase - 0.5) - 1.0).astype(_np.float32)

    @staticmethod
    def saw(freq, duration):
        t = Synth._t(duration)
        return (2.0 * ((t * freq) % 1.0) - 1.0).astype(_np.float32)

    @staticmethod
    def noise(duration, seed=None):
        n = max(1, int(RATE * duration))
        rng = _np.random.default_rng(seed)
        return rng.uniform(-1.0, 1.0, n).astype(_np.float32)

    @staticmethod
    def sweep(f0, f1, duration, kind="square", duty=0.5):
        """A glide from f0 to f1. Phase is integrated so the pitch actually
        slides instead of jumping every sample."""
        t = Synth._t(duration)
        n = len(t)
        freq = _np.linspace(f0, f1, n, dtype=_np.float32)
        phase = _np.cumsum(freq) / RATE
        if kind == "square":
            return _np.where((phase % 1.0) < duty, 1.0, -1.0).astype(_np.float32)
        if kind == "saw":
            return (2.0 * (phase % 1.0) - 1.0).astype(_np.float32)
        return (4.0 * _np.abs((phase % 1.0) - 0.5) - 1.0).astype(_np.float32)

    @staticmethod
    def env(wave, attack=0.005, decay=None, hold=0.0, curve=3.0):
        """Attack, optional hold, then an exponential fall to silence."""
        n = len(wave)
        out = _np.ones(n, dtype=_np.float32)
        a = min(n, int(attack * RATE))
        if a > 0:
            out[:a] = _np.linspace(0.0, 1.0, a)
        start = a + int(hold * RATE)
        if start < n:
            fall = _np.linspace(0.0, 1.0, n - start)
            out[start:] = (1.0 - fall) ** curve
        return wave * out

    @staticmethod
    def lowpass(wave, amount=0.35):
        """One-pole filter. Rounds off the harshest edges of the square waves
        without losing the character."""
        out = _np.empty_like(wave)
        acc = 0.0
        k = amount
        for i in range(len(wave)):
            acc += (wave[i] - acc) * k
            out[i] = acc
        return out

    @staticmethod
    def mix(*waves):
        n = max(len(w) for w in waves)
        out = _np.zeros(n, dtype=_np.float32)
        for w in waves:
            out[:len(w)] += w
        return out

    @staticmethod
    def cat(*waves):
        return _np.concatenate(waves)

    @staticmethod
    def silence(duration):
        return _np.zeros(max(1, int(RATE * duration)), dtype=_np.float32)


def _to_sound(wave, volume=1.0):
    peak = float(_np.max(_np.abs(wave))) or 1.0
    scaled = (wave / peak) * (32767 * MASTER * volume)
    mono = scaled.astype(_np.int16)
    stereo = _np.column_stack([mono, mono])
    return pygame.sndarray.make_sound(_np.ascontiguousarray(stereo))


def build_effects():
    """The whole sound catalogue. Each entry is a couple of lines of synthesis;
    that legibility is the point of generating them rather than shipping WAVs."""
    S = Synth
    fx = {}

    # --- guns ------------------------------------------------------------
    fx["shoot"] = _to_sound(S.env(S.sweep(880, 420, 0.07, duty=0.25),
                                  attack=0.001, curve=2.5), 0.30)
    fx["shoot_big"] = _to_sound(S.env(S.sweep(520, 200, 0.11, duty=0.35),
                                      attack=0.001, curve=2.0), 0.34)
    fx["enemy_shoot"] = _to_sound(S.env(S.sweep(300, 170, 0.10, duty=0.5),
                                        attack=0.002, curve=2.0), 0.20)

    # --- impacts ---------------------------------------------------------
    fx["hit"] = _to_sound(S.env(S.mix(S.noise(0.045, 1) * 0.6,
                                      S.square(1400, 0.045, 0.15) * 0.4),
                                attack=0.001, curve=4.0), 0.22)
    fx["explode"] = _to_sound(
        S.env(S.mix(S.lowpass(S.noise(0.34, 2), 0.30),
                    S.sweep(320, 60, 0.34, kind="saw") * 0.5),
              attack=0.002, curve=2.2), 0.42)
    fx["explode_big"] = _to_sound(
        S.env(S.mix(S.lowpass(S.noise(0.95, 3), 0.16),
                    S.sweep(220, 34, 0.95, kind="saw") * 0.7,
                    S.sweep(90, 28, 0.95, kind="triangle") * 0.6),
              attack=0.003, hold=0.06, curve=1.8), 0.62)

    # --- the ship --------------------------------------------------------
    fx["hurt"] = _to_sound(
        S.env(S.mix(S.sweep(440, 70, 0.42, duty=0.35),
                    S.noise(0.42, 4) * 0.35),
              attack=0.001, curve=1.6), 0.55)
    fx["shield_break"] = _to_sound(
        S.env(S.mix(S.sweep(900, 300, 0.28, kind="triangle"),
                    S.square(1320, 0.28, 0.2) * 0.3),
              attack=0.001, curve=2.2), 0.42)
    fx["shield_up"] = _to_sound(S.env(S.sweep(300, 900, 0.26, kind="triangle"),
                                      attack=0.01, curve=2.0), 0.34)
    fx["bomb"] = _to_sound(
        S.cat(S.env(S.sweep(1600, 200, 0.22, kind="saw"), attack=0.01, curve=1.2),
              S.env(S.mix(S.lowpass(S.noise(0.85, 5), 0.12),
                          S.sweep(160, 25, 0.85, kind="triangle")),
                    attack=0.002, hold=0.1, curve=1.5)), 0.70)

    # --- pickups ---------------------------------------------------------
    fx["crystal"] = _to_sound(
        S.cat(S.env(S.square(note("E", 6), 0.045, 0.5), attack=0.001, curve=3),
              S.env(S.square(note("B", 6), 0.06, 0.5), attack=0.001, curve=3)),
        0.22)
    fx["repair"] = _to_sound(
        S.cat(*[S.env(S.triangle(note(n, o), 0.075), attack=0.004, curve=2.5)
                for n, o in (("C", 5), ("E", 5), ("G", 5), ("C", 6))]), 0.30)

    # --- interface -------------------------------------------------------
    fx["menu_move"] = _to_sound(S.env(S.square(660, 0.035, 0.5),
                                      attack=0.001, curve=4.0), 0.20)
    fx["menu_ok"] = _to_sound(
        S.cat(S.env(S.square(note("G", 5), 0.05, 0.5), attack=0.001, curve=3),
              S.env(S.square(note("C", 6), 0.10, 0.5), attack=0.001, curve=2.5)),
        0.28)
    fx["menu_no"] = _to_sound(S.env(S.square(120, 0.14, 0.5),
                                    attack=0.001, curve=2.0), 0.26)
    fx["buy"] = _to_sound(
        S.cat(S.env(S.square(note("C", 6), 0.05, 0.25), attack=0.001, curve=3),
              S.env(S.square(note("E", 6), 0.05, 0.25), attack=0.001, curve=3),
              S.env(S.square(note("G", 6), 0.14, 0.25), attack=0.001, curve=2.2)),
        0.32)
    fx["jump"] = _to_sound(S.env(S.sweep(180, 720, 0.34, kind="triangle"),
                                 attack=0.01, curve=1.6), 0.30)

    # --- stingers --------------------------------------------------------
    fx["boss_warn"] = _to_sound(
        S.cat(*[S.env(S.square(f, 0.16, 0.5), attack=0.005, hold=0.06, curve=2.0)
                for f in (330, 247, 330, 247)]), 0.42)
    fx["sector_clear"] = _to_sound(
        S.cat(*[S.env(S.square(note(n, o), d, 0.5), attack=0.004, curve=2.0)
                for n, o, d in (("C", 5, 0.11), ("E", 5, 0.11), ("G", 5, 0.11),
                                ("C", 6, 0.30))]), 0.40)
    fx["game_over"] = _to_sound(
        S.cat(*[S.env(S.triangle(note(n, o), d), attack=0.008, curve=1.6)
                for n, o, d in (("G", 4, 0.20), ("F", 4, 0.20), ("D#", 4, 0.22),
                                ("C", 4, 0.60))]), 0.44)
    return fx


# One scale and tempo per sector, so the five of them do not sound alike.
SECTOR_TRACKS = (
    (("C", "D#", "G", "A#"), 3, 120),
    (("D", "F", "A", "C"), 3, 132),
    (("A", "C", "E", "G"), 2, 108),
    (("F", "G#", "C", "D#"), 3, 144),
    (("E", "G", "A#", "D"), 2, 152),
)


def build_track(index, seed=0):
    """A looping bass-and-arpeggio bed, generated per sector.

    Two voices: a triangle bass on the root, and a square arpeggio walking the
    scale. Structure comes from the seed, so every sector's loop is its own
    without anybody having to compose one.
    """
    S = Synth
    scale, octave, bpm = SECTOR_TRACKS[index % len(SECTOR_TRACKS)]
    rng = random.Random(seed * 31 + index)
    beat = 60.0 / bpm / 2.0            # eighth notes
    bars = 8
    steps = bars * 8

    bass = []
    lead = []
    for i in range(steps):
        root = scale[(i // 8) % len(scale)]
        # bass: root on the beat, rest between
        if i % 4 == 0:
            b = S.env(S.triangle(note(root, octave - 1), beat * 0.95),
                      attack=0.004, hold=beat * 0.4, curve=2.0) * 0.9
        else:
            b = S.silence(beat)
        bass.append(b)

        if rng.random() < 0.78:
            n = scale[rng.randrange(len(scale))]
            o = octave + (1 if rng.random() < 0.45 else 0)
            l = S.env(S.square(note(n, o), beat * 0.9, 0.25),
                      attack=0.002, curve=3.0) * 0.32
            l = _np.concatenate([l, S.silence(beat * 0.1)])
        else:
            l = S.silence(beat)
        lead.append(l)

    b = S.cat(*bass)
    l = S.cat(*lead)
    n = min(len(b), len(l))
    return _to_sound(S.mix(b[:n], l[:n]), 0.55)


class Audio:
    """Owns the mixer, the catalogue and the music channel.

    Every entry point is a no-op when sound is off, so callers never have to
    guard their calls.
    """

    def __init__(self, enabled=True):
        self.ok = False
        self.muted = not enabled
        self.effects = {}
        self.tracks = {}
        self.music_channel = None
        self.current_track = None
        self._last = {}
        if not enabled or _np is None:
            return
        try:
            # pygame.init() may have already opened the mixer at 44100. Our
            # waves are synthesised at RATE, and a mismatch plays every sound
            # at double speed and an octave up -- so close it and reopen at the
            # rate we actually generate.
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            pygame.mixer.init(RATE, -16, 2, 512)
            got = pygame.mixer.get_init()
            if got and got[0] != RATE:
                raise RuntimeError("mixer refused %d Hz" % RATE)
            pygame.mixer.set_num_channels(24)
            self.effects = build_effects()
            self.music_channel = pygame.mixer.Channel(0)
            self.ok = True
        except Exception:
            # A machine with no audio device should still play the game.
            self.ok = False

    def play(self, name, volume=1.0, throttle=0.0):
        """Fire one effect. `throttle` suppresses repeats within N seconds,
        which keeps a wall of simultaneous explosions from turning to mush."""
        if not self.ok or self.muted:
            return
        snd = self.effects.get(name)
        if snd is None:
            return
        if throttle:
            now = pygame.time.get_ticks() / 1000.0
            if now - self._last.get(name, -99.0) < throttle:
                return
            self._last[name] = now
        ch = pygame.mixer.find_channel(True)
        if ch is not None and ch is not self.music_channel:
            ch.set_volume(volume)
            ch.play(snd)

    def music(self, sector, seed=0):
        if not self.ok or self.muted:
            return
        key = (sector % len(SECTOR_TRACKS), seed)
        if self.current_track == key and self.music_channel.get_busy():
            return
        track = self.tracks.get(key)
        if track is None:
            track = build_track(key[0], seed)
            self.tracks[key] = track
        self.current_track = key
        self.music_channel.play(track, loops=-1)
        self.music_channel.set_volume(0.45)

    def stop_music(self):
        if self.ok and self.music_channel is not None:
            self.music_channel.stop()
            self.current_track = None

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self.stop_music()
        return self.muted
