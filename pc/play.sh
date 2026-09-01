#!/usr/bin/env sh
# NOVA - install what is needed, then play. Linux and macOS.
#
#   ./play.sh                 first run installs, later runs just launch
#   ./play.sh --fullscreen    any option is passed straight to the game
#
# Everything lands in pc/.venv; delete that folder to start over.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
VENV="$HERE/.venv"
cd "$HERE"

find_python() {
    for c in python3 python python3.13 python3.12 python3.11; do
        if command -v "$c" >/dev/null 2>&1; then
            if "$c" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,8) else 1)' 2>/dev/null; then
                echo "$c"
                return 0
            fi
        fi
    done
    return 1
}

PY=$(find_python) || {
    echo "NOVA needs Python 3.8 or newer."
    echo "Install it from https://www.python.org/downloads/ and run this again."
    exit 1
}
echo "Using $($PY --version 2>&1)"

if [ ! -d "$VENV" ]; then
    echo "Creating a virtual environment in pc/.venv ..."
    "$PY" -m venv "$VENV" || {
        echo
        echo "Could not create the virtual environment."
        echo "On Debian or Ubuntu you may need:  sudo apt install python3-venv"
        exit 1
    }
fi

VPY="$VENV/bin/python"
"$VPY" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true

if ! "$VPY" -c "import pygame" >/dev/null 2>&1; then
    # pygame-ce first: it is the community fork, and it ships wheels for new
    # Python releases months before upstream pygame does. Same `import pygame`.
    echo "Installing pygame-ce and numpy ..."
    if ! "$VPY" -m pip install --quiet pygame-ce numpy; then
        echo "pygame-ce did not install; falling back to pygame ..."
        "$VPY" -m pip install --quiet pygame numpy || {
            echo
            echo "Could not install the dependencies."
            echo "Try by hand:  $VPY -m pip install pygame-ce numpy"
            exit 1
        }
    fi
fi

echo "Launching NOVA ..."
exec "$VPY" "$HERE/nova.py" "$@"
