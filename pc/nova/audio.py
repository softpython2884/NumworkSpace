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


# The player's own weapon. Enemy fire and impacts are information -- they tell
# you what is about to hurt you -- so they are never part of the gun mute.
GUN_SOUNDS = ("shoot", "shoot_big")
GUN_VARIANTS = 3


def gun_variants(name):
    """The concrete effect names a requested name can resolve to.

    `play("shoot")` never plays a sample called `shoot`: guns rotate through
    pitch variants, so the name is an alias for three of them. Everything else
    is its own single name. The catalogue test uses this to know that a
    request and a built sound line up.
    """
    if name in GUN_SOUNDS:
        return tuple("%s%d" % (name, i) for i in range(GUN_VARIANTS))
    return (name,)


def build_effects():
    """The whole sound catalogue. Each entry is a couple of lines of synthesis;
    that legibility is the point of generating them rather than shipping WAVs."""
    S = Synth
    fx = {}

    # --- guns ------------------------------------------------------------
    # Fire is automatic, so this plays five to ten times a second for as long
    # as the game is on. It has to be quiet, short, and never twice the same:
    # a repeated identical blip is what turns a shooter into a headache. Three
    # pitch variants are cycled, and the whole thing is well below the volume
    # of anything that only happens occasionally.
    small = ((760, 380), (820, 410), (700, 350))
    big = ((470, 200), (510, 215), (440, 185))
    assert len(small) == len(big) == GUN_VARIANTS, \
        "the rotation in Audio.resolve would never reach the extra variants"
    for i, (f0, f1) in enumerate(small):
        fx["shoot%d" % i] = _to_sound(
            S.env(S.lowpass(S.sweep(f0, f1, 0.045, duty=0.22), 0.55),
                  attack=0.001, curve=3.2), 0.085)
    for i, (f0, f1) in enumerate(big):
        fx["shoot_big%d" % i] = _to_sound(
            S.env(S.lowpass(S.sweep(f0, f1, 0.065, duty=0.3), 0.5),
                  attack=0.001, curve=2.6), 0.10)
    fx["enemy_shoot"] = _to_sound(S.env(S.sweep(300, 170, 0.10, duty=0.5),
                                        attack=0.002, curve=2.0), 0.17)

    # --- impacts ---------------------------------------------------------
    # also frequent, so also quiet
    fx["hit"] = _to_sound(S.env(S.mix(S.noise(0.045, 1) * 0.6,
                                      S.square(1400, 0.045, 0.15) * 0.4),
                                attack=0.001, curve=4.0), 0.13)
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


# --- music ---------------------------------------------------------------
#
# The old bed was eight bars of eighth notes: a triangle bass on every fourth
# step and, on the rest, a *random* note from a four-note scale. Random notes
# are not a melody -- there is nothing to remember and nothing to come back to
# -- and eight bars is fifteen seconds, so the whole idea went past four times
# a minute. It clicked on the repeat, too: measured, three of the five loops
# ended on a waveform step 34 to 59 times a normal sample-to-sample jump, which
# is a tick you can hear every time round.
#
# This is a song instead: a chord progression and one motif that gets answered,
# transposed and ornamented across four sections -- about seventy seconds
# before it comes round, and no seam when it does.
#
# The instruments stay exactly what they were. A first pass added drums and
# syncopated stabs and it stopped sounding like the game: three voices is what
# an NES gives you for music -- one triangle, two pulses -- and that limit is
# the sound, not an obstacle to it. Structure is what the old bed was missing,
# not instrumentation.

_MINOR = (0, 2, 3, 5, 7, 8, 10)
_DORIAN = (0, 2, 3, 5, 7, 9, 10)


def _hz(semitone):
    """Frequency of a semitone offset from C4."""
    return 440.0 * (2.0 ** ((semitone - 9) / 12.0))


def _degree(scale, d):
    """Scale degree to semitones, wrapping into octaves above and below."""
    return scale[d % 7] + 12 * (d // 7)


def _triad(scale, d):
    return tuple(_degree(scale, d + i) for i in (0, 2, 4))


# root (semitones from C), scale, progression as scale degrees, bpm
#
# Minor keys throughout: a run lasts a quarter of an hour and relentless
# cheerfulness does not survive that. Straight eighths, no swing -- the old bed
# was straight and that squareness is part of the era.
SECTOR_TRACKS = (
    (0,  _MINOR,  (0, 5, 2, 6), 104),   # C  minor   i VI III VII
    (2,  _DORIAN, (0, 3, 0, 6), 116),   # D  dorian  i IV  i   VII
    (-3, _MINOR,  (0, 4, 5, 6), 96),    # A  minor   i v   VI  VII
    (5,  _MINOR,  (0, 6, 5, 4), 128),   # F  minor   i VII VI  v
    (4,  _MINOR,  (0, 2, 6, 3), 138),   # E  minor   i III VII IV
    (1,  _DORIAN, (0, 6, 4, 5), 112),   # the Void, unhurried
)

BARS_PER_SECTION = 8
SECTIONS = 4


def track_for(sector):
    """Which track a sector plays.

    Everything past the campaign is the Void, and it gets its own rather than
    starting the first sector's music over -- the endless part of the game
    should not sound like the beginning of it.
    """
    return min(sector, len(SECTOR_TRACKS) - 1)


class _Canvas:
    """A song rendered by placing notes at times, not by concatenating slots.

    The old builder glued one array per eighth note end to end, which forces
    every voice onto the same rigid grid: nothing can ring past its slot,
    nothing can overlap, and nothing can sit a little late. Writing into one
    buffer allows all three -- and it is what makes the loop seamless, because
    a note still sounding at the end can be folded back onto the beginning.
    """

    def __init__(self, seconds, tail=2.5):
        self.n = int(seconds * RATE)
        self.buf = _np.zeros(self.n + int(tail * RATE), dtype=_np.float32)

    def add(self, t, wave, gain=1.0):
        i = int(t * RATE)
        if i < 0 or i >= len(self.buf):
            return
        j = min(len(self.buf), i + len(wave))
        self.buf[i:j] += wave[:j - i] * gain

    def loop(self):
        """Fold the tail back onto the head.

        A note still ringing when the loop ends carries into the start of the
        next pass, exactly as it would if the song simply kept playing. Cutting
        it instead is what left the step in the waveform.
        """
        out = self.buf[:self.n].copy()
        tail = self.buf[self.n:]
        m = min(len(tail), self.n)
        out[:m] += tail[:m]
        return out


def _motif(rng):
    """A phrase, chosen once and then used all the way through.

    This is the whole difference between the old bed and a tune. The notes
    still come out of a generator, but they are drawn once and then answered,
    transposed and ornamented rather than re-rolled every bar. A phrase you
    hear four times is a melody; four different phrases are noise with better
    manners.

    Returns [(scale degree, length in beats)] totalling eight beats.
    """
    shapes = ((1.0, 0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 1.0, 2.0),
              (1.5, 0.5, 1.0, 1.0, 0.5, 0.5, 1.0, 2.0),
              (0.5, 0.5, 1.0, 2.0, 0.5, 0.5, 1.0, 2.0),
              (2.0, 1.0, 1.0, 0.5, 0.5, 1.0, 2.0))
    rhythm = list(rng.choice(shapes))
    d = rng.choice((0, 2, 4))
    out = []
    for i, length in enumerate(rhythm):
        out.append((d, length))
        # Mostly steps, occasionally a leap, and pulled back if it wanders:
        # a motif that walks off never sounds like it came back.
        step = rng.choice((-2, -1, -1, 1, 1, 2, 3, -3))
        d += step
        if d > 9:
            d -= 7
        elif d < -3:
            d += 7
    return out


def _answer(motif, rng):
    """The second half of the phrase: same rhythm, resolving to the tonic."""
    out = []
    n = len(motif)
    for i, (d, length) in enumerate(motif):
        if i >= n - 2:
            d = 0 if i == n - 1 else rng.choice((1, 2, -1))
        else:
            d = d - rng.choice((0, 1, 2))
        out.append((d, length))
    return out


def _lead_note(freq, seconds):
    """Pulse one: the melody."""
    return Synth.env(Synth.square(freq, seconds * 0.96, 0.5),
                     attack=0.008, hold=seconds * 0.5, curve=2.2)


def _arp_note(freq, seconds):
    """Pulse two: the arpeggio, thinner so it sits under the tune."""
    return Synth.env(Synth.square(freq, seconds * 0.9, 0.25),
                     attack=0.002, curve=3.0)


def _bass_note(freq, seconds):
    """The triangle channel."""
    return Synth.env(Synth.triangle(freq, seconds * 0.92),
                     attack=0.006, hold=seconds * 0.55, curve=1.8)


# Per section: the arpeggio figure, the bass figure, and whether the arpeggio
# takes the last bar off.
#
# The first version of this song ran one arpeggio shape and one bass walk for
# all thirty-two bars and changed only the octave of the tune. That is four
# sections on paper and one section in the ear -- the accompaniment has to move
# too, or the melody is decorating a loop rather than sitting on an arrangement.
ARPS = (
    (0, 1, 2, 1, 2, 1, 0, 1),      # A  up and back, steady
    (0, 2, 1, 2, 0, 2, 1, 2),      # B  wider, pivots on the fifth
    (2, 1, 0, 1, 2, 1, 0, 1),      # A' mirrored, starts high
    (0, -1, 1, -1, 0, -1, 1, -1),  # C  narrow, sits under everything
)
BASS_FIGURES = (
    ((0.0, 0, 1.0), (1.5, 4, 0.5), (2.0, 0, 1.0), (3.5, -1, 0.5)),
    ((0.0, 0, 0.5), (0.5, 0, 0.5), (1.5, 4, 0.5), (2.0, 0, 1.0),
     (3.0, 4, 1.0)),
    ((0.0, 0, 1.0), (1.0, 7, 0.5), (2.0, 0, 0.5), (2.5, 4, 0.5),
     (3.5, -1, 0.5)),
    ((0.0, 0, 2.0), (2.0, 4, 2.0)),
)


def build_track(index, seed=0):
    """Four sections of eight bars: A, B, A' an octave up, then a sparse C.

    Three voices, the same three the old bed had -- one triangle, two pulses.
    What is new is that they are playing something: a chord progression, a
    melody that comes back, and an accompaniment that changes with the section
    instead of running the same bar thirty-two times.
    """
    root, scale, prog, bpm = SECTOR_TRACKS[index % len(SECTOR_TRACKS)]
    rng = random.Random(seed * 977 + index * 31 + 7)

    beat = 60.0 / bpm
    bar = beat * 4.0
    bars = BARS_PER_SECTION * SECTIONS
    song = _Canvas(bars * bar)

    motif = _motif(rng)
    answer = _answer(motif, rng)

    for section in range(SECTIONS):
        base = section * BARS_PER_SECTION
        octave_up = 12 if section == 2 else 0
        sparse = section == 3
        transpose = 2 if section == 1 else 0
        arp_shape = ARPS[section]
        bass_figure = BASS_FIGURES[section]
        # B walks the same four chords starting from the second, so the
        # harmony moves somewhere new without a new progression to learn.
        rotate = 1 if section == 1 else 0

        for b in range(BARS_PER_SECTION):
            bar_i = base + b
            t0 = bar_i * bar
            chord = _triad(scale, prog[(b + rotate) % len(prog)])
            chord_root = root + chord[0]
            nxt = _triad(scale, prog[(b + rotate + 1) % len(prog)])[0] + root
            # The last bar of every section drops the arpeggio. A hole is the
            # cheapest variety there is and the ear uses it to hear the seam
            # between sections.
            breather = (b == BARS_PER_SECTION - 1)

            # --- triangle: bass ------------------------------------------
            for pos, step, length in bass_figure:
                semi = (nxt - 13) if step < 0 else (chord_root - 12 + step)
                song.add(t0 + pos * beat,
                         _bass_note(_hz(semi), length * beat), 0.62)

            # --- pulse two: arpeggio -------------------------------------
            if not breather:
                for e in range(8):
                    if sparse and e % 2:
                        continue
                    d = arp_shape[e]
                    semi = root + _degree(scale, prog[(b + rotate) % len(prog)]
                                          + d * 2) + (12 if e >= 4 else 0)
                    song.add(t0 + e * 0.5 * beat,
                             _arp_note(_hz(semi), beat * 0.5),
                             0.13 if sparse else 0.17)

            # --- pulse one: the tune -------------------------------------
            # Over four bars, not two: motif, motif answered, so a phrase is
            # eight bars long and does not come back every three seconds.
            phrase = motif if (b % 4) < 2 else answer
            if b % 2 == 0:
                t = 0.0
                for i, (d, length) in enumerate(phrase):
                    if t >= 8.0:
                        break
                    semi = root + _degree(scale, d + transpose) + 12 + octave_up
                    dur = length * beat * (2.0 if sparse else 1.0)
                    song.add(t0 + t * beat, _lead_note(_hz(semi), dur), 0.34)
                    t += length
                    if sparse and t >= 4.0:
                        break

    return _to_sound(song.loop(), 0.62)


class Audio:
    """Owns the mixer, the catalogue and the music channel.

    Every entry point is a no-op when sound is off, so callers never have to
    guard their calls.

    Mute has three settings rather than two. Automatic fire means the gun plays
    for as long as the game is running, and wanting that gone is not the same
    as wanting silence -- so M steps through everything, guns off, all off.
    """

    ALL, NO_GUNS, OFF = range(3)
    MODE_NAMES = ("SOUND ON", "GUNS MUTED", "SOUND OFF")

    def __init__(self, enabled=True):
        self.ok = False
        self.mode = self.ALL if enabled else self.OFF
        self._gun_turn = 0
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

    @property
    def muted(self):
        return self.mode == self.OFF

    def resolve(self, name):
        """Which sample a requested name actually plays, or None if muted.

        Guns step to the next pitch variant every time, so holding fire never
        repeats one sample; that repetition, more than the volume, is what
        makes an automatic weapon tiring to listen to.
        """
        if name in GUN_SOUNDS:
            if self.mode == self.NO_GUNS:
                return None
            self._gun_turn = (self._gun_turn + 1) % GUN_VARIANTS
            return "%s%d" % (name, self._gun_turn)
        return name

    def play(self, name, volume=1.0, throttle=0.0):
        """Fire one effect. `throttle` suppresses repeats within N seconds,
        which keeps a wall of simultaneous explosions from turning to mush."""
        if not self.ok or self.mode == self.OFF:
            return
        # Throttle on the name asked for, not the variant it resolves to: two
        # players firing on the same frame must still collapse to one sound,
        # and they would land on different variants.
        if throttle:
            now = pygame.time.get_ticks() / 1000.0
            if now - self._last.get(name, -99.0) < throttle:
                return
            self._last[name] = now
        sample = self.resolve(name)
        if sample is None:
            return
        snd = self.effects.get(sample)
        if snd is None:
            return
        ch = pygame.mixer.find_channel(True)
        if ch is not None and ch is not self.music_channel:
            ch.set_volume(volume)
            ch.play(snd)

    def music(self, sector, seed=0):
        if not self.ok or self.mode == self.OFF:
            return
        key = (track_for(sector), seed)
        if self.current_track == key and self.music_channel.get_busy():
            return
        track = self.tracks.get(key)
        if track is None:
            # Only the one playing is kept. A seventy-second track is around
            # six megabytes of samples, and there is never a reason to hold
            # five of them when you can hear one -- rebuilding costs a fifth
            # of a second, once, on a screen where nothing is moving.
            self.tracks.clear()
            track = build_track(key[0], seed)
            self.tracks[key] = track
        self.current_track = key
        self.music_channel.play(track, loops=-1)
        self.music_channel.set_volume(0.45)

    def stop_music(self):
        if self.ok and self.music_channel is not None:
            self.music_channel.stop()
            self.current_track = None

    def cycle_mute(self):
        """Step: everything -> guns off -> all off. Returns the new label."""
        self.mode = (self.mode + 1) % 3
        if self.mode == self.OFF:
            self.stop_music()
        return self.MODE_NAMES[self.mode]

    @property
    def mode_name(self):
        return self.MODE_NAMES[self.mode]
