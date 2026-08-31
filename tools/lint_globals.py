"""Catch the mistake MicroPython only reports at runtime, deep into a run:
a function that assigns to a module-level name without declaring it global.

CPython and MicroPython both turn such a name into a local, so the function
raises UnboundLocalError the first time it runs -- possibly an hour into a
game. Static detection is the only cheap way to be sure.
"""

import ast
import sys


def module_globals(tree):
    names = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.For):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
    return names


def check(path):
    with open(path) as fh:
        src = fh.read()
    tree = ast.parse(src)
    gnames = module_globals(tree)
    problems = []

    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        declared = set()
        assigned = {}
        params = {a.arg for a in fn.args.args}
        params |= {a.arg for a in fn.args.kwonlyargs}
        if fn.args.vararg:
            params.add(fn.args.vararg.arg)
        if fn.args.kwarg:
            params.add(fn.args.kwarg.arg)

        for node in ast.walk(fn):
            if isinstance(node, ast.Global):
                declared.update(node.names)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    for nm in ast.walk(t):
                        if isinstance(nm, ast.Name) and isinstance(nm.ctx, ast.Store):
                            assigned.setdefault(nm.id, nm.lineno)
            elif isinstance(node, ast.AugAssign):
                if isinstance(node.target, ast.Name):
                    assigned.setdefault(node.target.id, node.lineno)
            elif isinstance(node, ast.For):
                for nm in ast.walk(node.target):
                    if isinstance(nm, ast.Name):
                        assigned.setdefault(nm.id, nm.lineno)

        for name, line in sorted(assigned.items(), key=lambda kv: kv[1]):
            if name in gnames and name not in declared and name not in params:
                problems.append((line, fn.name, name, "assigns"))

        # A parameter that reuses a module-level name is legal Python, but it
        # makes one identifier mean two things -- which the minifier renames as
        # a single symbol. Flag it so the two stay in agreement.
        for name in sorted(params & gnames):
            problems.append((fn.lineno, fn.name, name, "parameter shadows"))

    return problems


def main(argv):
    rc = 0
    for path in argv[1:] or ["src/nova.py"]:
        problems = check(path)
        if problems:
            rc = 1
            for line, fn, name, kind in problems:
                if kind == "assigns":
                    print("%s:%d: %s() assigns global '%s' without 'global %s'"
                          % (path, line, fn, name, name))
                else:
                    print("%s:%d: %s() parameter '%s' shadows a module-level name"
                          % (path, line, fn, name))
        else:
            print("%s: no shadowed globals" % path)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
