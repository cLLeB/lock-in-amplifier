"""Compare the netlist KiCad exports from lockin.kicad_sch with expected_nets.json.

Usage (KiCad's Python):  python check_netlist.py lockin.net
Net names are ignored; only which pins are joined together is compared.
"""
import json
import os
import sys

from kisym import child, parse

HERE = os.path.dirname(os.path.abspath(__file__))


def exported(path):
    with open(path, encoding="utf-8") as f:
        root = parse(f.read())[0]
    nets = {}
    for net in child(root, "nets")[1:]:
        name = str(child(net, "name")[1])
        nodes = set()
        for n in net:
            if isinstance(n, list) and n[0] == "node":
                nodes.add("%s.%s" % (child(n, "ref")[1], child(n, "pin")[1]))
        nets[name] = nodes
    return nets


def main():
    got = exported(sys.argv[1])
    with open(os.path.join(HERE, "expected_nets.json"), encoding="utf-8") as f:
        want = {k: set(v) for k, v in json.load(f).items()}
    got_groups = {frozenset(v): k for k, v in got.items() if len(v) > 1}
    ok = True
    for name, pins in sorted(want.items()):
        if frozenset(pins) in got_groups:
            continue
        ok = False
        print("MISMATCH", name)
        for gname, gpins in got.items():
            if gpins & pins:
                print("   KiCad net %-28s missing: %s  extra: %s"
                      % (gname, sorted(pins - gpins), sorted(gpins - pins)))
    want_groups = {frozenset(v) for v in want.values()}
    for group, gname in got_groups.items():
        if group not in want_groups and not any(group & w for w in want_groups):
            ok = False
            print("UNEXPECTED net", gname, sorted(group))
    wanted_pins = set().union(*want.values())
    stray = sorted(p for v in got.values() for p in v if p not in wanted_pins and len(v) > 1)
    if stray:
        ok = False
        print("pins joined to something but not in the expected list:", stray)
    print("NETLIST OK: %d nets match" % len(want) if ok else "NETLIST DIFFERS")


if __name__ == "__main__":
    main()
