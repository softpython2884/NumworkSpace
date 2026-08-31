"""Rewrite `from X import *` into an explicit import list.

A star-import copies every public name of the source module into the importing
module's globals dict. Across five modules that is several hundred redundant
dict entries -- measured at several kilobytes of a 32 KB heap, for names most
modules never touch.

This computes, per module, exactly which upstream names it actually uses, and
writes that list into the import statement.
"""

import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAIN = ["novad.py", "novae.py", "novaf.py", "novag.py", "nova.py"]
BUILTINS = set(dir(__import__("builtins")))


def defined(tree, own_modules=()):
    """Names a module binds at top level.

    `own_modules` names our own modules: imports from those are pass-throughs,
    not definitions, so they must not hide a name the module still needs.
    """
    out = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                for nm in ast.walk(t):
                    if isinstance(nm, ast.Name):
                        out.add(nm.id)
        elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
            out.add(n.target.id)
        elif isinstance(n, ast.Import):
            for a in n.names:
                out.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, ast.ImportFrom):
            if n.module in own_modules:
                continue
            for a in n.names:
                if a.name != "*":
                    out.add(a.asname or a.name)
    return out


def _bound(fn):
    """Names bound inside one function: parameters, assignments, loop targets,
    comprehension targets, nested defs."""
    out = set()
    a = fn.args
    for arg in list(a.args) + list(a.kwonlyargs) + list(getattr(a, "posonlyargs", [])):
        out.add(arg.arg)
    if a.vararg:
        out.add(a.vararg.arg)
    if a.kwarg:
        out.add(a.kwarg.arg)
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                for nm in ast.walk(t):
                    if isinstance(nm, ast.Name) and isinstance(nm.ctx, ast.Store):
                        out.add(nm.id)
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign, ast.For)):
            for nm in ast.walk(node.target):
                if isinstance(nm, ast.Name) and isinstance(nm.ctx, ast.Store):
                    out.add(nm.id)
        elif isinstance(node, ast.comprehension):
            for nm in ast.walk(node.target):
                if isinstance(nm, ast.Name) and isinstance(nm.ctx, ast.Store):
                    out.add(nm.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node is not fn:
            out.add(node.name)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            out.add(node.name)
    return out


def used(tree):
    """Names the module needs from outside itself.

    Locals must not count: a loop variable named `i` is not a missing import,
    and treating it as one would drown the real forward references in noise.
    """
    free = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            bound = _bound(node)
            for nm in ast.walk(node):
                if isinstance(nm, ast.Name) and nm.id not in bound:
                    free.add(nm.id)
        else:
            for nm in ast.walk(node):
                if isinstance(nm, ast.Name):
                    free.add(nm.id)
    return free


def wrap(module, names):
    """One import statement, wrapped to a sane line length."""
    head = "from %s import " % module
    if len(head + ", ".join(names)) <= 78:
        return head + ", ".join(names)
    out = []
    line = head + "("
    for j, nm in enumerate(names):
        piece = nm + ("," if j < len(names) - 1 else ")")
        if len(line) + len(piece) + 1 > 78:
            out.append(line)
            line = "    " + piece
        else:
            line = line + ("" if line.endswith("(") else " ") + piece
    out.append(line)
    return "\n".join(out)


def main():
    src_dir = os.path.join(ROOT, "src")
    owner = {}             # name -> the module that defines it
    changed = []
    for i, mod in enumerate(CHAIN):
        path = os.path.join(src_dir, mod)
        with open(path) as fh:
            text = fh.read()
        tree = ast.parse(text)
        local = defined(tree, {m[:-3] for m in CHAIN})

        if i > 0:
            # Import each name straight from the module that defines it, never
            # from the one loaded just before: otherwise a middle module has to
            # re-import names it never uses purely to pass them along.
            need = sorted(used(tree) - local - BUILTINS)
            groups = {}
            for nm in need:
                src = owner.get(nm)
                if src:
                    groups.setdefault(src, []).append(nm)
            block = "\n".join(
                wrap(m, sorted(ns)) for m, ns in
                sorted(groups.items(), key=lambda kv: CHAIN.index(kv[0] + ".py")))

            lines = text.split("\n")
            keep = []
            replaced = False
            skip_to = -1
            for k, line in enumerate(lines):
                if k <= skip_to:
                    continue
                if line.startswith("from nova") and " import" in line:
                    if "(" in line and ")" not in line:
                        j = k
                        while ")" not in lines[j]:
                            j += 1
                        skip_to = j
                    if not replaced:
                        keep.append(block)
                        replaced = True
                    continue
                keep.append(line)
            text = "\n".join(keep)
            with open(path, "w") as fh:
                fh.write(text)
            missing = sorted(n for n in need
                             if n not in owner and n not in BUILTINS)
            if missing:
                # A name defined in a module loaded *later* cannot be imported;
                # Python only fails when that line finally runs, which may be
                # deep into a game. Fail here instead.
                print("ERROR: %s uses names defined later in the chain: %s"
                      % (mod, ", ".join(missing)))
                print("       move those definitions into an earlier module.")
                return 1
            changed.append((mod, sum(len(v) for v in groups.values()), len(groups)))
            local |= {nm for v in groups.values() for nm in v}

        for nm in local:
            owner.setdefault(nm, mod[:-3])

    for mod, n, g in changed:
        print("  %-12s %d names from %d module(s)" % (mod, n, g))
    return 0


if __name__ == "__main__":
    sys.exit(main())
