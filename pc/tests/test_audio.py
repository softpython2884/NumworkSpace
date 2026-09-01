"""Check the sound catalogue against what the game actually asks for.

A misspelled effect name is silent, not an error -- `play("expode")` simply
does nothing, forever, and nobody notices. So: play a whole run, record every
name requested, and require the two sets to match in both directions. Unused
entries matter too: they are sounds somebody wrote and forgot to trigger.

Gun names are aliases -- `play("shoot")` reaches one of three pitch variants --
so a request is expanded through `audio.gun_variants` before the sets are
compared, and the mute modes are exercised directly at the end.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import pygame

import test_run
from nova import audio as audio_mod

def rare_paths(audio):
    """Drive every effect a scripted run only meets by luck.

    Hull drops are a 9% roll, the deflector is one upgrade of twelve, a refusal
    needs an unaffordable item, and `game_over` needs the run to be lost. Left
    to chance the test passes or fails depending on the seed, which is worse
    than no test. Each of these is set up directly instead.
    """
    import pygame
    from nova import data, entities as ent
    from nova.art import Art
    from nova.combat import Combat
    from nova.run import Run

    art = Art()
    art.load_fonts()
    run = Run(1, 1, seed=5)
    run.upgrades[data.U_SHIELD] = 1      # deflector: shield_up, shield_break
    run.upgrades[data.U_SPREAD] = 3      # four barrels: shoot_big
    combat = Combat(run, data.N_FIGHT, art, audio)
    p = combat.players[0]

    # deflector charges, then eats a hit
    p.shield = False
    p.shield_t = 0.0
    combat.update(1 / 60.0, {"move0": (0, 0), "bomb": False})
    p.shield = True
    p.invuln = 0.0
    combat.hurt_player(p)

    # a hull pickup, collected
    pk = ent.Pickup(p.x, p.y, kind=1)
    pk.vx = pk.vy = 0.0
    combat.pickups.append(pk)
    run.hull = max(1, run.max_hull - 3)
    for _ in range(6):
        combat.update(1 / 60.0, {"move0": (0, 0), "bomb": False})

    # a boss, so its warning stinger fires
    Combat(run, data.N_BOSS, art, audio)

    # menu refusal, sector clear and the losing run: state transitions a
    # scripted winner never reaches
    from nova.game import Game
    from nova import ui
    g = Game.__new__(Game)
    g.audio = audio
    g.menu = ui.Menu(["nope"], [""], [data.WHITE], [False])
    g._menu_feedback(0, 0)
    g.run = run
    g.map = type("M", (), {"finished": staticmethod(lambda: True)})()
    g.advance()
    g.after_combat(False)


EXPECT_UNPLAYED = set()


class Tapped(dict):
    """A catalogue that remembers every lookup, so a test can see which sample
    `play` actually reached for rather than which name it was handed."""

    def __init__(self, src):
        dict.__init__(self, src)
        self.hits = []

    def get(self, key, default=None):
        self.hits.append(key)
        return dict.get(self, key, default)


def mute_modes(a):
    """M has to mute the guns *only*, then everything. Check all three states
    through `play` itself, since that is where the early returns live.

    Returns a list of failure messages.
    """
    bad = []
    real, a.effects = a.effects, Tapped(a.effects)
    try:
        a.mode = a.ALL
        a._gun_turn = 0
        for _ in range(audio_mod.GUN_VARIANTS * 2):
            a.play("shoot")
        a.play("explode")
        seen = set(a.effects.hits)
        want = set(audio_mod.gun_variants("shoot"))
        if not want <= seen:
            bad.append("rotation never reaches %s" % ", ".join(sorted(want - seen)))
        if "explode" not in seen:
            bad.append("sound on: explode did not play")

        a.effects.hits = []
        a.mode = a.NO_GUNS
        for name in audio_mod.GUN_SOUNDS:
            a.play(name)
        if a.effects.hits:
            bad.append("guns muted: %s still played"
                       % ", ".join(sorted(set(a.effects.hits))))
        for name in ("explode", "enemy_shoot", "hit", "pickup"):
            a.play(name)
        missed = [n for n in ("explode", "enemy_shoot", "hit")
                  if n not in a.effects.hits]
        if missed:
            bad.append("guns muted: it silenced %s too" % ", ".join(missed))

        a.effects.hits = []
        a.mode = a.OFF
        for name in ("shoot", "explode", "enemy_shoot"):
            a.play(name)
        if a.effects.hits:
            bad.append("sound off: %s still played"
                       % ", ".join(sorted(set(a.effects.hits))))
    finally:
        a.effects = real
        a.mode = a.ALL
        a._gun_turn = 0

    # two players firing on the same frame must collapse to one sound: the
    # throttle has to key on the requested name, not on the variant chosen
    real, a.effects = a.effects, Tapped(a.effects)
    try:
        a.play("shoot", throttle=0.5)
        a.play("shoot", throttle=0.5)
        if len(a.effects.hits) != 1:
            bad.append("throttle let %d gun sounds through instead of 1 (%s)"
                       % (len(a.effects.hits), ", ".join(a.effects.hits)))
    finally:
        a.effects = real
        a._last.clear()

    # and the key itself walks the three states in order and comes back round
    labels = [a.cycle_mute() for _ in range(4)]
    if labels != list(a.MODE_NAMES[1:]) + [a.MODE_NAMES[0], a.MODE_NAMES[1]]:
        bad.append("M does not cycle on -> guns -> off -> on: %s" % labels)
    a.mode = a.ALL
    return bad


def main():
    pygame.init()
    a = audio_mod.Audio(True)
    if not a.ok:
        print("FAIL: audio engine did not start")
        return 1

    rate = pygame.mixer.get_init()[0]
    print("mixer rate      : %d Hz (synthesised at %d)" % (rate, audio_mod.RATE))
    print("effects built   : %d" % len(a.effects))
    if rate != audio_mod.RATE:
        print("FAIL: mixer rate differs from the synthesis rate -- every sound")
        print("      would play at the wrong speed and pitch")
        return 1

    asked = set()
    real_play = audio_mod.Audio.play

    def spy(self, name, volume=1.0, throttle=0.0):
        asked.add(name)
        return real_play(self, name, volume, throttle)

    audio_mod.Audio.play = spy
    try:
        for seed in (7, 42, 101):
            test_run.run_once(seed)
        rare_paths(a)
    finally:
        audio_mod.Audio.play = real_play

    have = set(a.effects)
    # a request for "shoot" can land on any of its variants, so every variant
    # counts as reached -- and all of them must exist
    reachable = set()
    for name in asked:
        reachable.update(audio_mod.gun_variants(name))
    missing = reachable - have
    unused = have - reachable - EXPECT_UNPLAYED
    absent = EXPECT_UNPLAYED - have

    print("effects requested during play : %d" % len(asked))
    ok = True
    if missing:
        print("FAIL: the game asks for sounds that do not exist: %s"
              % ", ".join(sorted(missing)))
        ok = False
    if unused:
        print("FAIL: sounds built but never triggered: %s"
              % ", ".join(sorted(unused)))
        ok = False
    if absent:
        print("FAIL: expected-but-unplayed sounds are missing: %s"
              % ", ".join(sorted(absent)))
        ok = False

    for problem in mute_modes(a):
        print("FAIL: %s" % problem)
        ok = False
    print("mute modes      : %s" % " -> ".join(a.MODE_NAMES))

    # music: one track per sector, and they must differ
    lengths = []
    for sector in range(5):
        track = audio_mod.build_track(sector, 3)
        lengths.append(round(track.get_length(), 2))
    print("sector tracks   : %s seconds" % lengths)
    if len(set(lengths)) < 2:
        print("FAIL: every sector track is the same length -- likely identical")
        ok = False

    # the game must survive with no audio device at all
    silent = audio_mod.Audio(False)
    silent.play("shoot")
    silent.music(0)
    silent.stop_music()
    print("muted engine    : no-ops cleanly")

    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
