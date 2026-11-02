"""Minimal reader for KiCad symbol libraries: s-expression parse, symbol lookup, pin positions."""
import os
import re

KICAD = os.path.join(os.environ["LOCALAPPDATA"], "Programs", "KiCad", "10.0")
SYMDIR = os.path.join(KICAD, "share", "kicad", "symbols")


class Q(str):
    """A string that was quoted in the source and must be quoted on output."""


def parse(text):
    i, n, stack = 0, len(text), [[]]
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c == "(":
            stack.append([])
            i += 1
        elif c == ")":
            done = stack.pop()
            stack[-1].append(done)
            i += 1
        elif c == '"':
            j, buf = i + 1, []
            while text[j] != '"':
                if text[j] == "\\":
                    buf.append(text[j:j + 2])
                    j += 2
                else:
                    buf.append(text[j])
                    j += 1
            stack[-1].append(Q("".join(buf)))
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in " \t\r\n()":
                j += 1
            stack[-1].append(text[i:j])
            i = j
    return stack[0]


def dump(x, ind=0):
    if isinstance(x, Q):
        return '"%s"' % x
    if isinstance(x, str):
        return x
    if all(not isinstance(e, list) for e in x):
        return "(" + " ".join(dump(e) for e in x) + ")"
    out = "(" + dump(x[0])
    for e in x[1:]:
        if isinstance(e, list):
            out += "\n" + "\t" * (ind + 1) + dump(e, ind + 1)
        else:
            out += " " + dump(e)
    return out + "\n" + "\t" * ind + ")"


_lib_text = {}


def _block(lib, name):
    if lib not in _lib_text:
        with open(os.path.join(SYMDIR, lib + ".kicad_sym"), encoding="utf-8") as f:
            _lib_text[lib] = f.read()
    text = _lib_text[lib]
    start = text.find('\n\t(symbol "%s"' % name)
    if start < 0:
        raise KeyError("%s:%s not found" % (lib, name))
    start += 1
    depth, i, instr = 0, start, False
    while True:
        c = text[i]
        if instr:
            if c == "\\":
                i += 1
            elif c == '"':
                instr = False
        elif c == '"':
            instr = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                break
        i += 1
    return parse(text[start:i + 1])[0]


def child(node, key):
    for e in node:
        if isinstance(e, list) and e and e[0] == key:
            return e
    return None


def load_symbol(lib, name):
    """Return the symbol node with any 'extends' parent merged in. Name is left unprefixed."""
    sym = _block(lib, name)
    ext = child(sym, "extends")
    if ext is None:
        return sym
    base = load_symbol(lib, str(ext[1]))
    base_name = str(base[1])
    own = {str(e[1]): e for e in sym if isinstance(e, list) and e[0] == "property"}
    merged = ["symbol", Q(name)]
    for e in base[2:]:
        if isinstance(e, list) and e[0] == "property":
            merged.append(own.pop(str(e[1]), e))
        elif isinstance(e, list) and e[0] == "symbol":
            sub = list(e)
            sub[1] = Q(name + str(e[1])[len(base_name):])
            merged.append(sub)
        else:
            merged.append(e)
    return merged


def pins(sym):
    """Map unit number -> list of pins (unit 0 is shared by all units)."""
    res = {}
    for e in sym:
        if not (isinstance(e, list) and e[0] == "symbol"):
            continue
        m = re.match(r".*_(\d+)_(\d+)$", str(e[1]))
        unit, style = int(m.group(1)), int(m.group(2))
        if style > 1:
            continue
        for p in e:
            if isinstance(p, list) and p[0] == "pin":
                at = child(p, "at")
                res.setdefault(unit, []).append({
                    "num": str(child(p, "number")[1]),
                    "name": str(child(p, "name")[1]),
                    "x": float(at[1]), "y": float(at[2]), "a": int(float(at[3])),
                    "type": p[1],
                })
    return res


def prop(sym, key):
    for e in sym:
        if isinstance(e, list) and e[0] == "property" and str(e[1]) == key:
            return str(e[2])
    return ""


if __name__ == "__main__":
    import sys
    for spec in sys.argv[1:]:
        lib, name = spec.split(":")
        s = load_symbol(lib, name)
        print("==", spec, "| footprint:", prop(s, "Footprint"))
        for unit, plist in sorted(pins(s).items()):
            for p in plist:
                print("  u%d pin %-3s %-12s at (%6.2f,%6.2f) a=%3d %s" % (unit, p["num"], p["name"], p["x"], p["y"], p["a"], p["type"]))
