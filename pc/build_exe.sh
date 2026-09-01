#!/usr/bin/env sh
# Build a single-file NOVA executable for the machine you run this on.
# Windows users: run build_exe.cmd instead. There is no cross-compiling --
# a Windows .exe has to be built on Windows.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"

VENV="$HERE/.venv"
if [ ! -d "$VENV" ]; then
    echo "Setting up first (this also installs the game's dependencies) ..."
    ./play.sh --help >/dev/null 2>&1 || true
fi
VPY="$VENV/bin/python"
[ -x "$VPY" ] || VPY=$(command -v python3)

"$VPY" -m pip install --quiet --upgrade pyinstaller || {
    echo "Could not install PyInstaller."
    exit 1
}
"$VPY" tools/make_icon.py
"$VPY" -m PyInstaller --noconfirm --clean nova.spec

echo
echo "Built: $HERE/dist/NOVA"
