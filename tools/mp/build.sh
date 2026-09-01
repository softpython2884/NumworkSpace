#!/bin/sh
# Build the MicroPython 1.17 unix port -- the same interpreter version Epsilon
# ships -- so tools/memcheck.py can measure real heap use instead of guessing
# from file size. Needs gcc, make and git; builds in about fifteen seconds.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
SRC="$HERE/micropython-src"

[ -d "$SRC" ] || git clone --depth 1 --branch v1.17 \
    https://github.com/micropython/micropython.git "$SRC"

# The unix port's default build wants two git submodules -- axtls for ussl and
# berkeley-db for btree -- which a shallow clone does not bring, and which have
# nothing to do with what we measure. Epsilon ships neither. Turning both off
# builds the interpreter we care about out of the tree we actually have.
#
# MicroPython 1.17 also predates gcc 13, whose newer warnings trip its -Werror.
make -C "$SRC/ports/unix" -j4 \
    MICROPY_PY_USSL=0 MICROPY_SSL_AXTLS=0 MICROPY_PY_BTREE=0 \
    CFLAGS_EXTRA="-Wno-error -Wno-dangling-pointer -Wno-array-bounds -Wno-stringop-overflow -Wno-use-after-free"

cp "$SRC/ports/unix/micropython" "$HERE/micropython"
echo "built: $HERE/micropython"
