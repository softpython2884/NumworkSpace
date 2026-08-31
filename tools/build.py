"""Compile src/nova.py down to dist/nova.py, the file you paste into a NumWorks.

The calculator gives Python 32 KB of storage for *all* scripts and 32 KB of heap
for the bytecode plus every runtime object, so the readable source cannot ship
as-is. Three passes, each safe by construction:

  1. strip  -- drop comments and docstrings via `tokenize` (never regexes: a
               regex cannot tell a comment from a '#' inside a string)
  2. rename -- shorten identifiers. Names are renamed *by spelling*, one symbol
               per name across the whole file, which is only sound because
               tools/lint_globals.py proves no local or parameter shadows a
               module-level name. Attributes, keyword arguments, builtins and
               imported names are never touched.
  3. indent -- re-emit with one space per level instead of four

The result is verified: it must parse, and tests/run_all.py runs the entire
suite against dist/nova.py as well as src/nova.py.
"""

import ast
import io
import keyword
import os
import sys
import tokenize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Names that must survive verbatim: the calculator's own API, plus anything the
# language resolves by spelling.
PROTECTED = {
    "kandinsky", "ion", "time",
    "fill_rect", "draw_string", "set_pixel", "get_pixel", "color",
    "keydown", "monotonic", "sleep",
}
PROTECTED |= {k for k in dir(__builtins__)} if isinstance(__builtins__, dict) is False else set(__builtins__)
PROTECTED |= set(dir(__import__("builtins")))
PROTECTED |= set(keyword.kwlist)
PROTECTED |= {"self", "__name__", "__init__"}


def _docstring_spans(src):
    """Positions of docstrings safe to delete (never the sole statement)."""
    tree = ast.parse(src)
    spans = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = node.body
        if (len(body) > 1 and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            e = body[0]
            spans.append(((e.lineno, e.col_offset),
                          (e.end_lineno, e.end_col_offset)))
    return spans


def _comment_spans(src):
    spans = []
    readline = io.StringIO(src).readline
    for ttype, _, start, end, _ in tokenize.generate_tokens(readline):
        if ttype == tokenize.COMMENT:
            spans.append((start, end))
    return spans


def strip_comments(src):
    """Delete comments and docstrings by text span.

    Working on spans rather than re-emitting the token stream keeps the original
    indentation byte-for-byte, which matters because Python's grammar is the
    indentation.
    """
    lines = src.split("\n")
    spans = _comment_spans(src) + _docstring_spans(src)
    # Apply bottom-up so earlier positions stay valid.
    for (r0, c0), (r1, c1) in sorted(spans, reverse=True):
        i0, i1 = r0 - 1, r1 - 1
        if i0 == i1:
            lines[i0] = lines[i0][:c0] + lines[i0][c1:]
        else:
            head = lines[i0][:c0]
            tail = lines[i1][c1:]
            lines[i0:i1 + 1] = [head + tail]
    return "\n".join(l for l in lines if l.strip())


def short_names():
    """Yield a, b, ... z, A, ... Z, aa, ab, ... skipping anything reserved."""
    alpha = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    n = 1
    while True:
        idx = [0] * n
        while True:
            name = "".join(alpha[i] for i in idx)
            if name not in PROTECTED and not keyword.iskeyword(name):
                yield name
            k = n - 1
            while k >= 0:
                idx[k] += 1
                if idx[k] < len(alpha):
                    break
                idx[k] = 0
                k -= 1
            if k < 0:
                break
        n += 1


def collect(src):
    """Every identifier we are allowed to rename, with its use count."""
    tree = ast.parse(src)
    counts = {}
    imported = set()
    kwargs_used = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            # `ion.KEY_LEFT` -> KEY_LEFT is an attribute of a foreign module
            kwargs_used.add(node.attr)
        elif isinstance(node, ast.keyword) and node.arg:
            kwargs_used.add(node.arg)
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                imported.add(a.asname or a.name)
        elif isinstance(node, ast.Import):
            for a in node.names:
                imported.add((a.asname or a.name).split(".")[0])
        elif isinstance(node, ast.Name):
            counts[node.id] = counts.get(node.id, 0) + 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            counts[node.name] = counts.get(node.name, 0) + 1
            for a in node.args.args + node.args.kwonlyargs:
                counts[a.arg] = counts.get(a.arg, 0) + 1
            if node.args.vararg:
                counts[node.args.vararg.arg] = counts.get(node.args.vararg.arg, 0) + 1
            if node.args.kwarg:
                counts[node.args.kwarg.arg] = counts.get(node.args.kwarg.arg, 0) + 1

    banned = PROTECTED | imported | kwargs_used
    return {n: c for n, c in counts.items() if n not in banned}, banned


def build_map(counts, banned):
    """Shortest names to the most-used identifiers.

    Every renameable identifier is renamed, including the one-character ones.
    Leaving those alone looks like a free win but it is a trap: the generator
    would happily hand `g` to some other symbol while a local `g` still exists,
    and the two silently become one variable. The AST shape is unchanged by
    that, so a structural check cannot see it -- only running the build can,
    which is why tests/run_all.py exercises dist/nova.py too.
    """
    order = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    gen = (n for n in short_names() if n not in banned)
    mapping = {}
    for name, _ in order:
        mapping[name] = next(gen)

    # The rename must be injective, and must not collide with any name we kept.
    new = list(mapping.values())
    assert len(new) == len(set(new)), "minifier produced duplicate names"
    kept = banned | {n for n in counts if n not in mapping}
    clash = set(new) & kept
    assert not clash, "minified names collide with kept names: %s" % sorted(clash)
    return mapping


def rename(src, mapping):
    """Apply the map over the token stream, skipping attribute positions."""
    out = []
    prev_op = None
    readline = io.StringIO(src).readline
    for ttype, tstr, _, _, _ in tokenize.generate_tokens(readline):
        if ttype == tokenize.NAME and prev_op != "." and tstr in mapping:
            tstr = mapping[tstr]
        if ttype == tokenize.OP:
            prev_op = tstr
        elif ttype not in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
                           tokenize.DEDENT, tokenize.COMMENT):
            prev_op = None
        out.append((ttype, tstr))
    return tokenize.untokenize(out)


def reindent(src):
    """Four spaces per level is 3 wasted bytes per level per line."""
    out = []
    for line in src.split("\n"):
        stripped = line.lstrip(" ")
        if not stripped:
            continue
        depth = (len(line) - len(stripped)) // 4
        out.append(" " * depth + stripped)
    return "\n".join(out) + "\n"


def squeeze(src):
    """Trim the spaces `untokenize` leaves around operators and separators."""
    out = []
    for line in src.split("\n"):
        # Only touch code outside string literals.
        res = []
        i = 0
        quote = None
        while i < len(line):
            ch = line[i]
            if quote:
                res.append(ch)
                if ch == "\\" and i + 1 < len(line):
                    res.append(line[i + 1])
                    i += 2
                    continue
                if ch == quote:
                    quote = None
            elif ch in "\"'":
                quote = ch
                res.append(ch)
            elif ch == " ":
                prev = res[-1] if res else ""
                nxt = line[i + 1] if i + 1 < len(line) else ""
                # keep the space only when removing it would fuse two tokens
                if (prev.isalnum() or prev == "_") and (nxt.isalnum() or nxt == "_"):
                    res.append(ch)
                elif prev == "" and res == []:
                    res.append(ch)
                else:
                    pass
            else:
                res.append(ch)
            i += 1
        # restore leading indentation, which the loop above would have eaten
        lead = len(line) - len(line.lstrip(" "))
        out.append(" " * lead + "".join(res).lstrip(" "))
    return "\n".join(out)


def structural_signature(src):
    """A fingerprint of what the code *does*, ignoring what things are called."""
    tree = ast.parse(src)
    sig = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            sig.append(("const", repr(node.value)))
        else:
            sig.append((type(node).__name__,))
    sig.sort()
    return sig


def main(argv):
    src_path = os.path.join(ROOT, "src", "nova.py")
    out_path = os.path.join(ROOT, "dist", "nova.py")
    if len(argv) > 1:
        src_path = argv[1]
    if len(argv) > 2:
        out_path = argv[2]

    with open(src_path) as fh:
        original = fh.read()

    step1 = strip_comments(original)
    # Compare against the stripped source, not the original: removing docstrings
    # legitimately removes string constants, and that must not read as damage.
    before = structural_signature(step1)
    counts, banned = collect(step1)
    mapping = build_map(counts, banned)
    step2 = rename(step1, mapping)
    step3 = reindent(step2)
    step4 = squeeze(step3)

    # Verification: it must parse, and rename/indent/squeeze must not have
    # changed what the code does. Identifier spellings may differ; node shapes
    # and every constant must match exactly.
    ast.parse(step4)
    after = structural_signature(step4)
    bshapes = [x for x in before if x[0] != "Name"]
    ashapes = [x for x in after if x[0] != "Name"]
    if bshapes != ashapes:
        print("FAIL: minified code is not structurally identical")
        from collections import Counter
        lost = Counter(bshapes) - Counter(ashapes)
        gained = Counter(ashapes) - Counter(bshapes)
        for k, v in list(lost.items())[:8]:
            print("   lost   x%-3d %s" % (v, k))
        for k, v in list(gained.items())[:8]:
            print("   gained x%-3d %s" % (v, k))
        return 1

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # Ship the rename table beside the build so the test suite can drive the
    # minified file through the exact same tests as the source.
    import json
    with open(out_path.replace(".py", ".map.json"), "w") as fh:
        json.dump(mapping, fh, indent=0, sort_keys=True)
    header = ("# NOVA - space rogue-lite for NumWorks. MIT licence.\n"
              "# Generated from src/nova.py by tools/build.py -- do not edit.\n"
              "# https://github.com/softpython2884/NumworkSpace\n")
    with open(out_path, "w") as fh:
        fh.write(header + step4)

    a, b = len(original), len(header + step4)
    print("source    : %6d bytes  %s" % (a, os.path.relpath(src_path, ROOT)))
    print("minified  : %6d bytes  %s" % (b, os.path.relpath(out_path, ROOT)))
    print("saved     : %6d bytes  (%.0f%%)" % (a - b, 100.0 * (a - b) / a))
    print("identifiers renamed: %d" % len(mapping))
    print()
    budget = 32 * 1024
    print("NumWorks script storage: %d bytes total for all scripts" % budget)
    print("this script uses %.1f%% of it, %d bytes to spare" % (100.0 * b / budget, budget - b))
    return 0 if b < budget else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
