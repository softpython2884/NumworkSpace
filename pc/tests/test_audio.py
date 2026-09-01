"""Check the sound catalogue against what the game actually asks for.

A misspelled effect name is silent, not an error -- `play("expode")` simply
does nothing, forever, and nobody notices. So: play a whole run, record every
name requested, and require the two sets to match in both directions. Unused
entries matter too: they are sounds somebody wrote and forgot to trigger.
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
    missing = asked - have
    unused = have - asked - EXPECT_UNPLAYED
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
