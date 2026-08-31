#!/bin/sh
# Build the MicroPython 1.17 unix port -- the same interpreter version Epsilon
# ships -- so tools/memcheck.py can measure real heap use instead of guessing
# from file size. Needs gcc, make and git. Takes a couple of minutes, once.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
SRC="$HERE/micropython-src"

[ -d "$SRC" ] || git clone --depth 1 --branch v1.17 \
    https://github.com/micropython/micropython.git "$SRC"

# MicroPython 1.17 predates gcc 13, whose newer warnings trip its -Werror.
make -C "$SRC/ports/unix" -j4 \
    CFLAGS_EXTRA="-Wno-error -Wno-dangling-pointer -Wno-array-bounds -Wno-stringop-overflow -Wno-use-after-free"

cp "$SRC/ports/unix/micropython" "$HERE/micropython"
echo "built: $HERE/micropython"
