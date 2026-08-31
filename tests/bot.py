"""A pilot that dodges, so tests exercise the game the way a person plays it.

It scores the danger to its left and right and moves away from the worse side;
with nothing incoming it lines up on the nearest enemy. Perfect information and
perfect reflexes, but a naive strategy -- a human on a calculator keypad will do
worse, which is the right direction for a difficulty check to err in.
"""


class Dodger:
    def __init__(self, g):
        self.g = g
        self.want = [0, 0]
        self.tick = 0

    def _decide(self, pi):
        g = self.g
        S, E, F = g["S"], g["E"], g["F"]
        NE, NF, PY = g["NE"], g["NF"], g["PY"]
        me = g["PX"][pi] + 7
        left = right = 0
        for o in range(0, S[NF] * 4, 4):
            dy = PY - F[o + 1]
            if 0 < dy < 90:
                dx = F[o] - me
                w = 90 - dy
                if -26 < dx < 0:
                    left += w
                elif 0 <= dx < 26:
                    right += w
        for o in range(0, S[NE] * 6, 6):
            dy = PY - E[o + 1]
            if 0 < dy < 110:
                dx = E[o] - me
                w = 60 - (dy >> 1)
                # widen the no-go zone as it closes: lining up under a ship
                # about to land on you is a collision, not aiming
                near = 42 if dy < 64 else 30
                if -near < dx < 0:
                    left += w
                elif 0 <= dx < near:
                    right += w
        if left or right:
            return 1 if left > right else (-1 if right > left else 0)
        tgt = None
        for o in range(0, S[NE] * 6, 6):
            d = E[o] + (g["EW"][E[o + 2]] >> 1) - me
            if tgt is None or abs(d) < abs(tgt):
                tgt = d
        if tgt is not None and abs(tgt) > 4:
            return 1 if tgt > 0 else -1
        return 0

    def keydown(self, k):
        g = self.g
        self.tick += 1
        if self.tick % 2 == 1:
            self.want[0] = self._decide(0)
            if g["PON"][1]:
                self.want[1] = self._decide(1)
        if k == g["KL"]:
            return self.want[0] < 0
        if k == g["KR"]:
            return self.want[0] > 0
        if k == g["K4"]:
            return self.want[1] < 0
        if k == g["K6"]:
            return self.want[1] > 0
        if k == g["KE"]:
            S = g["S"]
            return S[g["NF"]] + S[g["NE"]] > 12 and self.tick % 7 == 0
        return False
