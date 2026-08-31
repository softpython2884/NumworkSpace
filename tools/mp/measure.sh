#!/bin/sh
# Bisect for the smallest heap that can import the game, on the real MicroPython
# 1.17 interpreter Epsilon ships. Prints the minimum in KB.
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
MP="$ROOT/tools/mp/micropython"
WORK="$ROOT/tools/mp/work"
mkdir -p "$WORK"
rm -f "$WORK"/*.py
python3 - "$ROOT" <<'PY'
import re, os, sys
root = sys.argv[1]
for f in sorted(os.listdir(os.path.join(root, "dist"))):
    if not f.endswith(".py"):
        continue
    lines = open(os.path.join(root, "dist", f)).read().rstrip("\n").split("\n")
    if re.match(r"^[A-Za-z_]\w*\(\)$", lines[-1]):
        lines = lines[:-1]          # do not start the game on import
    open(os.path.join(root, "tools/mp/work", f), "w").write("\n".join(lines) + "\n")
PY
lo=16; hi=200
while [ $lo -lt $hi ]; do
  mid=$(( (lo + hi) / 2 ))
  if timeout 60 "$MP" -X heapsize=${mid}k -c "
import sys; sys.path.insert(0,'$ROOT/tools/mp/stubs'); sys.path.insert(0,'$WORK')
import nova
print('OK')" 2>/dev/null | grep -q OK; then hi=$mid; else lo=$(( mid + 1 )); fi
done
echo "$lo"
