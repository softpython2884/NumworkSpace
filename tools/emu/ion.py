"""Headless re-implementation of the NumWorks `ion` module.

`keydown(k)` on Epsilon polls the keyboard matrix and returns True while the key
is held. There is no event queue and no auto-repeat: the game is responsible for
edge detection. This stub reproduces that exactly, and lets a test drive the game
by pushing key states in (see `_press` / `_set_state`).

Key codes follow Epsilon's 9x6 matrix layout; the gaps (8-11, 35, 41, 47, 53)
are unpopulated positions in that matrix.
"""

KEY_LEFT = 0
KEY_UP = 1
KEY_DOWN = 2
KEY_RIGHT = 3
KEY_OK = 4
KEY_BACK = 5
KEY_HOME = 6
KEY_ONOFF = 7
KEY_SHIFT = 12
KEY_ALPHA = 13
KEY_XNT = 14
KEY_VAR = 15
KEY_TOOLBOX = 16
KEY_BACKSPACE = 17
KEY_EXP = 18
KEY_LN = 19
KEY_LOG = 20
KEY_IMAGINARY = 21
KEY_COMMA = 22
KEY_POWER = 23
KEY_SINE = 24
KEY_COSINE = 25
KEY_TANGENT = 26
KEY_PI = 27
KEY_SQRT = 28
KEY_SQUARE = 29
KEY_SEVEN = 30
KEY_EIGHT = 31
KEY_NINE = 32
KEY_LEFTPARENTHESIS = 33
KEY_RIGHTPARENTHESIS = 34
KEY_FOUR = 36
KEY_FIVE = 37
KEY_SIX = 38
KEY_MULTIPLICATION = 39
KEY_DIVISION = 40
KEY_ONE = 42
KEY_TWO = 43
KEY_THREE = 44
KEY_PLUS = 45
KEY_MINUS = 46
KEY_ZERO = 48
KEY_DOT = 49
KEY_EE = 50
KEY_ANS = 51
KEY_EXE = 52

_state = set()
_poll_count = 0


def keydown(k):
    global _poll_count
    _poll_count += 1
    return k in _state


# --- test helpers (not part of the calculator API) --------------------------

def _set_state(keys):
    """Replace the held-key set. `keys` is any iterable of key codes."""
    global _state
    _state = set(keys)


def _press(*keys):
    _state.update(keys)


def _release(*keys):
    _state.difference_update(keys)


def _reset():
    global _state, _poll_count
    _state = set()
    _poll_count = 0


def _polls():
    return _poll_count


# --- matrix helper, used to justify the 2-player key mapping ----------------

def matrix_position(k):
    """Return (row, col) of a key in Epsilon's 9x6 scan matrix."""
    return (k // 6, k % 6)


def ghosts(keys):
    """True if this key combination can ghost on a diode-less matrix.

    Ghosting needs three keys where two share a row and two share a column:
    the scan then reports a fourth, un-pressed key at the rectangle's corner.
    Any two keys are always safe, whatever their position.
    """
    pos = [matrix_position(k) for k in keys]
    for i in range(len(pos)):
        for j in range(len(pos)):
            for m in range(len(pos)):
                if i == j or i == m or j == m:
                    continue
                # pos[i] shares a row with pos[j] and a column with pos[m]
                if pos[i][0] == pos[j][0] and pos[i][1] == pos[m][1]:
                    return True
    return False
