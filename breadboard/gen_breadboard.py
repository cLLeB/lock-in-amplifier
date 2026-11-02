"""Breadboard layout for the lock-in amplifier.

One table (PARTS, WIRES) describes where every leg and wire goes on an 830-hole breadboard.
The script checks that this wiring gives exactly the nets of the KiCad schematic
(../kicad/expected_nets.json), then writes the picture (breadboard-layout.svg) and the
step-by-step guide (../BREADBOARD-GUIDE.md).

Holes: column letter a-j and row number 1-63, for example "e12". Columns a-e of a row are joined,
and columns f-j of a row are joined. Rails: "L+", "L-", "R+", "R-".
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = 63

RAILS = {"L+": "VREF (2.5 V)", "L-": "GND", "R+": "+5V", "R-": "GND"}


def dip(ref, pins, top):
    """Legs of a chip across the centre gap, pin 1 at column e of row `top`."""
    half = pins // 2
    legs = {}
    for p in range(1, half + 1):
        legs["%s.%d" % (ref, p)] = "e%d" % (top + p - 1)
    for p in range(half + 1, pins + 1):
        legs["%s.%d" % (ref, p)] = "f%d" % (top + pins - p)
    return legs


# stage, reference, value, what it is, {pin: hole}, note
PARTS = [
    (1, "U4", "LP2950-5.0", "5 V regulator", {"U4.1": "h3", "U4.2": "h4", "U4.3": "h5"},
     "flat face toward the centre gap"),
    (1, "C6", "10 uF", "electrolytic", {"C6.1": "g3", "C6.2": "g4"}, "long leg (+) in g3"),
    (1, "C5", "10 uF", "electrolytic", {"C5.1": "i5", "C5.2": "i4"}, "long leg (+) in i5"),
    (1, "D2", "1N4148", "diode", {"D2.1": "f5", "D2.2": "f8"}, "black band end in f5"),
    (2, "U3", "MCP6022", "op amp", dip("U3", 8, 23), "notch toward row 1"),
    (2, "R10", "10 k", "resistor", {"R10.1": "R+", "R10.2": "j27"}, ""),
    (2, "R11", "10 k", "resistor", {"R11.1": "a25", "R11.2": "L-"}, ""),
    (2, "C7", "10 uF", "electrolytic", {"C7.1": "c25", "C7.2": "c26"}, "long leg (+) in c25"),
    (2, "C12", "100 nF", "capacitor", {"C12.1": "R+", "C12.2": "R-"}, "plugs into the two right-hand rails"),
    (3, "U6", "74HC4060", "counter", dip("U6", 16, 10), "notch toward row 1"),
    (3, "C14", "100 nF", "capacitor", {"C14.1": "R+", "C14.2": "R-"}, "plugs into the two right-hand rails"),
    (3, "R13", "10 M", "resistor", {"R13.1": "g16", "R13.2": "g20"}, ""),
    (3, "R12", "330 k", "resistor", {"R12.1": "h21", "R12.2": "h16"}, ""),
    (3, "Y1", "32.768 kHz", "crystal", {"Y1.1": "f21", "Y1.2": "f20"}, "either way round; spread the two legs"),
    (3, "C9", "22 pF", "capacitor", {"C9.1": "i20", "C9.2": "i22"}, "spread the legs to span two rows"),
    (3, "C8", "22 pF", "capacitor", {"C8.1": "j21", "C8.2": "j22"}, ""),
    (4, "R16", "680", "resistor", {"R16.1": "g5", "R16.2": "d5"}, "crosses the centre gap"),
    (4, "LED", "red LED", "LED", {"J3.1": "c5", "J3.2": "c6"}, "long leg in c5"),
    (4, "Q1", "2N7000", "MOSFET", {"Q1.3": "b6", "Q1.2": "b7", "Q1.1": "b8"},
     "flat face toward the centre gap"),
    (4, "R15", "100 k", "resistor", {"R15.1": "a7", "R15.2": "L-"}, ""),
    (4, "R14", "100", "resistor", {"R14.1": "c14", "R14.2": "c7"}, "lies over rows 8 to 13"),
    (5, "U1", "MCP6022", "op amp", dip("U1", 8, 30), "notch toward row 1"),
    (5, "C10", "100 nF", "capacitor", {"C10.1": "R+", "C10.2": "R-"}, "plugs into the two right-hand rails"),
    (5, "R1", "100 k", "resistor", {"R1.1": "d31", "R1.2": "d30"}, "stand it on end (rows next to each other)"),
    (5, "C1", "100 pF", "capacitor", {"C1.1": "c31", "C1.2": "c30"}, ""),
    (5, "C2", "10 nF", "capacitor", {"C2.1": "b30", "C2.2": "b29"}, ""),
    (5, "R2", "100 k", "resistor", {"R2.1": "a29", "R2.2": "L+"}, ""),
    (5, "R3", "10 k", "resistor", {"R3.1": "g32", "R3.2": "g31"}, "stand it on end"),
    (5, "R4", "1 k", "resistor", {"R4.1": "h32", "R4.2": "h36"}, ""),
    (5, "D1", "BPW34", "photodiode", {"D1.1": "b31", "D1.2": "b33"}, "leg with the small tab (cathode) in b31"),
    (6, "U5", "74HC4053", "analog switch", dip("U5", 16, 37), "notch toward row 1"),
    (6, "C13", "100 nF", "capacitor", {"C13.1": "R+", "C13.2": "R-"}, "plugs into the two right-hand rails"),
    (6, "U2", "MCP6022", "op amp", dip("U2", 8, 48), "notch toward row 1"),
    (6, "C11", "100 nF", "capacitor", {"C11.1": "R+", "C11.2": "R-"}, "plugs into the two right-hand rails"),
    (6, "R5", "10 k", "resistor", {"R5.1": "d45", "R5.2": "d49"}, ""),
    (6, "R6", "10 k", "resistor", {"R6.1": "c49", "R6.2": "c48"}, "stand it on end"),
    (7, "R7", "100 k", "resistor", {"R7.1": "b48", "R7.2": "b54"}, ""),
    (7, "C3", "1 uF film", "capacitor", {"C3.1": "c54", "C3.2": "c56"}, ""),
    (7, "R8", "100 k", "resistor", {"R8.1": "d54", "R8.2": "g51"}, "crosses the centre gap"),
    (7, "C4", "1 uF film", "capacitor", {"C4.1": "h51", "C4.2": "h53"}, ""),
    (7, "R9", "100", "resistor", {"R9.1": "j50", "R9.2": "j56"}, ""),
    (7, "R17", "100", "resistor", {"R17.1": "g58", "R17.2": "g53"}, ""),
]

# stage, from, to, colour hint, what it carries
WIRES = [
    (1, "L-", "R-", "black", "joins the two ground rails (at row 62)"),
    (1, "j3", "R+", "red", "+5V to the right rail"),
    (1, "j4", "R-", "black", "regulator ground"),
    (2, "j23", "R+", "red", "U3 supply"),
    (2, "a26", "L-", "black", "U3 ground"),
    (2, "b23", "b24", "any", "U3 pin 1 to pin 2 (short link)"),
    (2, "a23", "L+", "yellow", "VREF to the left rail"),
    (2, "L+", "g26", "yellow", "VREF to U3 pin 5. Go round the bottom end of U3"),
    (2, "g27", "b25", "any", "R10 to U3 pin 3. Go round the bottom end of U3"),
    (2, "h24", "h25", "any", "U3 pin 7 to pin 6 (short link)"),
    (3, "j10", "R+", "red", "U6 supply"),
    (3, "a17", "L-", "black", "U6 ground"),
    (3, "j14", "R-", "black", "U6 reset held low"),
    (3, "i15", "j20", "any", "U6 pin 11 to the crystal"),
    (3, "g22", "R-", "black", "ground for C8 and C9"),
    (4, "a8", "L-", "black", "MOSFET source to ground"),
    (5, "j30", "R+", "red", "U1 supply"),
    (5, "a33", "L-", "black", "U1 ground"),
    (5, "a32", "L+", "yellow", "VREF to U1 pin 3"),
    (5, "d29", "g33", "any", "high-pass output to U1 pin 5. Go round the top end of U1"),
    (5, "g36", "L+", "yellow", "VREF to R4. Go round the bottom end of U1"),
    (6, "j37", "R+", "red", "U5 supply"),
    (6, "a42", "L-", "black", "U5 pin 6 to ground"),
    (6, "a43", "L-", "black", "U5 pin 7 to ground"),
    (6, "a44", "L-", "black", "U5 pin 8 to ground"),
    (6, "j43", "R-", "black", "U5 pin 10 to ground"),
    (6, "j44", "R-", "black", "U5 pin 9 to ground"),
    (6, "h31", "h40", "any", "AC signal to U5 pin 13"),
    (6, "i25", "i41", "any", "VSW to U5 pin 12"),
    (6, "b14", "j42", "any", "1024 Hz clock to U5 pin 11. Lay it along the right-hand edge"),
    (6, "j48", "R+", "red", "U2 supply"),
    (6, "a51", "L-", "black", "U2 ground"),
    (6, "g40", "c45", "any", "AC signal to R5"),
    (6, "h39", "c50", "any", "U5 pin 14 to U2 pin 3"),
    (7, "h49", "h50", "any", "U2 pin 7 to pin 6 (short link)"),
    (7, "a56", "L+", "yellow", "VREF to C3"),
    (7, "b56", "i53", "yellow", "VREF to C4 and R17"),
]

RAIL_ROW = {"C14": 10, "C12": 23, "C10": 30, "C13": 37, "C11": 48}

# Things that are not parts on the breadboard: where the battery and the meter connect.
EXTERNAL = {"J1.1": "g8", "J1.2": "R-", "J2.1": "i56", "J2.2": "i58"}

# Schematic pins that are deliberately not wired on the breadboard.
LEFT_OPEN = {
    "U5.1", "U5.2", "U5.3", "U5.5",   # ends of the two unused switches: harmless when open
    "J2.3",                           # ground pin of the output connector
    "TP1.1", "TP2.1", "TP3.1", "TP4.1", "TP5.1", "TP6.1",
}


def node_of(hole):
    if hole in RAILS:
        return hole
    col, row = hole[0], int(hole[1:])
    if col not in "abcdefghij" or not 1 <= row <= ROWS:
        raise SystemExit("bad hole " + hole)
    return ("L" if col in "abcde" else "R") + str(row)


def build():
    used = {}
    pin_hole = {}
    for stage, ref, value, kind, legs, note in PARTS:
        for pin, hole in legs.items():
            pin_hole[pin] = hole
    pin_hole.update(EXTERNAL)
    entries = [(p, h) for p, h in pin_hole.items()]
    for i, (stage, a, b, colour, what) in enumerate(WIRES):
        entries += [("wire%d" % i, a), ("wire%d'" % i, b)]
    for who, hole in entries:
        if hole in RAILS:
            continue
        node_of(hole)
        if hole in used:
            raise SystemExit("hole %s used by %s and %s" % (hole, used[hole], who))
        used[hole] = who

    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for stage, a, b, colour, what in WIRES:
        parent[find(node_of(a))] = find(node_of(b))
    groups = {}
    for pin, hole in pin_hole.items():
        groups.setdefault(find(node_of(hole)), set()).add(pin)
    return pin_hole, groups, used


def check(groups):
    want = json.load(open(os.path.join(HERE, "..", "kicad", "expected_nets.json")))
    # The board has resistors R9 and R17 feeding connector J2 and a connector J3 for the LED:
    # same names here. Dropped pins are removed from the comparison.
    want_sets = {}
    for net, pins in want.items():
        s = set(pins) - LEFT_OPEN
        if s:
            want_sets[net] = s
    have = [g for g in groups.values()]
    errors = []
    for net, s in sorted(want_sets.items()):
        match = [g for g in have if g & s]
        if len(match) != 1 or match[0] != s:
            got = sorted(set().union(*match)) if match else []
            errors.append("%s: want %s, breadboard gives %s" % (net, sorted(s), got))
    wanted_pins = set().union(*want_sets.values())
    # Chip pins with no connection in the schematic (or left open on purpose) must touch nothing.
    for g in have:
        loose = g - wanted_pins
        if loose and len(g) != 1:
            errors.append("unused pin joined to something: %s" % sorted(g))
    missing = wanted_pins - set().union(*have)
    if missing:
        errors.append("schematic pins not placed: %s" % sorted(missing))
    return want_sets, errors


# ---------------------------------------------------------------- picture

P = 12.0          # pixels per hole pitch
X0, Y0 = 150.0, 60.0
COLX = {}
for i, c in enumerate("abcde"):
    COLX[c] = X0 + i * P
for i, c in enumerate("fghij"):
    COLX[c] = X0 + (7 + i) * P
RAILX = {"L+": X0 - 4 * P, "L-": X0 - 3 * P, "R-": X0 + 14 * P, "R+": X0 + 15 * P}
WIRE_COL = {"red": "#d22", "black": "#222", "yellow": "#c90", "any": "#27c"}


def xy(hole, near_row=None):
    if hole in RAILS:
        return RAILX[hole], Y0 + ((near_row or 1) - 1) * P
    return COLX[hole[0]], Y0 + (int(hole[1:]) - 1) * P


def row_of(hole):
    return None if hole in RAILS else int(hole[1:])


def svg(pin_hole):
    out = []
    w, h = X0 + 15 * P + 330, Y0 + ROWS * P + 40
    out.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" font-family="Arial" font-size="9">' % (w, h))
    out.append('<rect width="100%" height="100%" fill="#fff"/>')
    out.append('<rect x="%g" y="%g" width="%g" height="%g" rx="6" fill="#f4f1e6" stroke="#999"/>'
               % (X0 - 5.2 * P, Y0 - 1.5 * P, 21.4 * P, (ROWS + 2) * P))
    out.append('<text x="%g" y="20" font-size="14" font-weight="bold">Lock-in amplifier on a breadboard (top view, row 1 at the top)</text>' % 10)
    out.append('<text x="%g" y="%g" font-size="10" fill="#555">Wires are drawn straight to show where they start and end. Lay the real wires round the chips, not over them.</text>' % (10, Y0 + (ROWS + 2.2) * P))
    for rail, x in RAILX.items():
        col = {"L+": "#c90", "L-": "#222", "R-": "#222", "R+": "#d22"}[rail]
        out.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="2" opacity="0.5"/>'
                   % (x, Y0 - P / 2, x, Y0 + (ROWS - 1) * P + P / 2, col))
        out.append('<text x="%g" y="%g" text-anchor="middle" font-weight="bold" fill="%s">%s</text>' % (x, Y0 - 2.2 * P, col, rail))
        out.append('<text x="%g" y="%g" text-anchor="middle" font-size="7" fill="%s">%s</text>'
                   % (x, Y0 - 1.6 * P + 2, col, RAILS[rail].split(" ")[0]))
    for c, x in COLX.items():
        out.append('<text x="%g" y="%g" text-anchor="middle" fill="#666">%s</text>' % (x, Y0 - P, c))
    for r in range(1, ROWS + 1):
        y = Y0 + (r - 1) * P
        if r == 1 or r % 5 == 0:
            out.append('<text x="%g" y="%g" text-anchor="end" fill="#666">%d</text>' % (X0 - 1.0 * P, y + 3, r))
            out.append('<text x="%g" y="%g" fill="#666">%d</text>' % (X0 + 12.0 * P, y + 3, r))
        for c, x in COLX.items():
            out.append('<circle cx="%g" cy="%g" r="1.6" fill="#bbb"/>' % (x, y))
    # chips
    for stage, ref, value, kind, legs, note in PARTS:
        rows = [row_of(hh) for hh in legs.values() if hh not in RAILS]
        if ref.startswith("U") and len(legs) >= 8:
            y1, y2 = Y0 + (min(rows) - 1) * P - P / 2 + 1, Y0 + (max(rows) - 1) * P + P / 2 - 1
            out.append('<rect x="%g" y="%g" width="%g" height="%g" rx="3" fill="#333"/>' % (COLX["e"] + 3, y1, 3 * P - 6, y2 - y1))
            out.append('<circle cx="%g" cy="%g" r="2.5" fill="#f4f1e6"/>' % (COLX["e"] + 1.5 * P, y1 + 1))
            out.append('<text x="%g" y="%g" text-anchor="middle" fill="#fff" font-weight="bold">%s</text>' % (COLX["e"] + 1.5 * P, (y1 + y2) / 2 + 3, ref))
            for pin, hh in legs.items():
                x, y = xy(hh)
                out.append('<rect x="%g" y="%g" width="5" height="5" fill="#333"/>' % (x - 2.5, y - 2.5))
            continue
        holes = list(legs.values())
        colour = {"resistor": "#b5651d", "capacitor": "#2a8", "electrolytic": "#55a", "diode": "#e70",
                  "LED": "#e00", "MOSFET": "#555", "5 V regulator": "#555", "crystal": "#888",
                  "photodiode": "#a0a"}.get(kind, "#555")
        pts = []
        base = ([r for r in rows if r is not None] or [RAIL_ROW.get(ref, 1)])[0]
        for hh in holes:
            pts.append(xy(hh, near_row=base))
        for i in range(len(pts) - 1):
            out.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="4" stroke-linecap="round" opacity="0.85"/>'
                       % (pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], colour))
        for x, y in pts:
            out.append('<circle cx="%g" cy="%g" r="2.6" fill="%s"/>' % (x, y, colour))
        mx = sum(p[0] for p in pts) / len(pts)
        my = sum(p[1] for p in pts) / len(pts)
        out.append('<text x="%g" y="%g" text-anchor="middle" font-size="8" font-weight="bold" stroke="#fff" stroke-width="2.5" paint-order="stroke">%s</text>'
                   % (mx, my - 4, ref))
    # wires
    for stage, a, b, colour, what in WIRES:
        ra, rb = row_of(a), row_of(b)
        near = ra or rb or 62
        if a in RAILS and b in RAILS:
            near = 62
        x1, y1 = xy(a, near)
        x2, y2 = xy(b, near)
        col = WIRE_COL[colour]
        if abs(y2 - y1) > 6 * P and "edge" in what:
            ex = X0 + 16.5 * P
            d = "M%g,%g L%g,%g L%g,%g L%g,%g" % (x1, y1, x1, y1 - P * 0.5, ex, y1 - P * 0.5, ex, y2)
            out.append('<path d="%s L%g,%g" fill="none" stroke="%s" stroke-width="1.6"/>' % (d, x2, y2, col))
        else:
            bend = 0.18 * (y2 - y1) if abs(x2 - x1) < 1 else 0
            out.append('<path d="M%g,%g Q%g,%g %g,%g" fill="none" stroke="%s" stroke-width="1.6"/>'
                       % (x1, y1, (x1 + x2) / 2 + bend + (6 if abs(x2 - x1) < 1 else 0), (y1 + y2) / 2, x2, y2, col))
        for x, y in ((x1, y1), (x2, y2)):
            out.append('<circle cx="%g" cy="%g" r="2.2" fill="%s"/>' % (x, y, col))
    for name, hole, label in (("J1.1", "g8", "battery + (red)"), ("J2.1", "i56", "meter + (OUT)"), ("J2.2", "i58", "meter - (VREF)")):
        x, y = xy(hole)
        out.append('<circle cx="%g" cy="%g" r="3.2" fill="none" stroke="#090" stroke-width="1.5"/>' % (x, y))
        out.append('<text x="%g" y="%g" fill="#090" font-weight="bold">%s</text>' % (X0 + 17.2 * P, y + 3, label))
    out.append('<text x="%g" y="%g" fill="#090" font-weight="bold">battery - (black): any hole of R-</text>' % (X0 + 17.2 * P, Y0 + 9 * P + 3))
    # legend
    lx, ly = X0 + 17.2 * P, Y0 + 14 * P
    sections = [(1, "Rows 3 to 8, right: 5 V supply"), (4, "Rows 5 to 14, left: LED driver"), (3, "Rows 10 to 22: 1024 Hz clock (U6)"),
                (2, "Rows 23 to 27: 2.5 V reference (U3)"), (5, "Rows 29 to 36: photodiode amplifier (U1)"),
                (6, "Rows 37 to 51: demodulator (U5, U2)"), (7, "Rows 51 to 58: filter and output")]
    out.append('<text x="%g" y="%g" font-size="11" font-weight="bold">Where things are</text>' % (lx, ly))
    for i, (stage, text) in enumerate(sections):
        out.append('<text x="%g" y="%g" font-size="10">Stage %d. %s</text>' % (lx, ly + 16 + i * 14, stage, text))
    ly2 = ly + 16 + len(sections) * 14 + 14
    out.append('<text x="%g" y="%g" font-size="11" font-weight="bold">Colours</text>' % (lx, ly2))
    for i, (col, text) in enumerate((("#d22", "wire: +5V"), ("#222", "wire: ground"), ("#c90", "wire: VREF 2.5 V"), ("#27c", "wire: signal"),
                                     ("#b5651d", "resistor"), ("#2a8", "small capacitor"), ("#55a", "10 uF electrolytic"),
                                     ("#e70", "diode"), ("#a0a", "photodiode"), ("#e00", "LED"), ("#888", "crystal"))):
        y = ly2 + 14 + i * 13
        out.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="4"/>' % (lx, y - 3, lx + 18, y - 3, col))
        out.append('<text x="%g" y="%g" font-size="10">%s</text>' % (lx + 24, y, text))
    out.append("</svg>")
    return "\n".join(out)


INTRO = """# Breadboard guide: lock-in amplifier

Written by `breadboard/gen_breadboard.py`, which also checks that the wiring below gives exactly the
connections of the schematic (27 nets). Do not edit the tables by hand: change the script and run it again.

Nothing has been built yet. Every expected value comes from calculation or simulation.

Picture of the finished breadboard: `breadboard/breadboard-layout.png`. Keep it open while building.

## How to read a hole name

- Hold the breadboard upright, row 1 at the top. Columns are lettered a to j, left to right.
- A hole is a column letter and a row number: `e12` is column e, row 12.
- In one row, holes a to e are joined together, and holes f to j are joined together. The two halves
  are not joined across the centre gap.
- The four long rails at the sides are used like this:

| Rail | Position | Carries |
|---|---|---|
| L+ | left, outer | VREF (2.5 V) |
| L- | left, inner | ground |
| R- | right, inner | ground |
| R+ | right, outer | +5 V |

Your breadboard's rails may be printed in a different left-to-right order. What matters is that the two
rails on each side are the two listed, and that you always use the same one for the same purpose.

## Before you start

1. **Check the rails.** On many breadboards each rail is cut in the middle. With the multimeter on
   continuity, test from the top hole to the bottom hole of each of the four rails. If one does not beep,
   join its two halves with a short wire across the break.
2. **Prepare the battery clip.** Its wires are soft and will not push into the holes. At the lab, solder
   each wire to one pin snapped off your pin header strip. Do not connect the battery yet.
3. **Chips.** Each chip sits across the centre gap with its notch (or dot) toward row 1. Pin 1 is then at
   the top left. Straighten the legs gently against the table first so they drop into the holes.
4. **Three-leg parts** (U4 and Q1): spread the three legs slightly so each goes in its own row.
5. **Short links.** Three wires join two neighbouring rows. A bent offcut of resistor leg does the same
   job and saves your jumper wires.
6. **Measuring.** The black lead of the multimeter and the ground clip of the scope probe go on the
   L- rail: push a wire into the rail and clip onto it. To measure a row, push a wire into any free
   hole of that half-row and touch or clip onto the wire.

Rules: disconnect the battery before adding parts. Do not go on until the check of the stage passes.
If a check fails, stop and send a photo and the reading.
"""

STAGE_TEXT = {
    1: ("5 V supply",
        "Turns the 9 V battery into a steady 5 V on the R+ rail.",
        """Check:

- With the multimeter on continuity, R+ to R- must not beep.
- Battery: red wire into **g8**, black wire into the **R-** rail. If the battery is the wrong way round,
  the diode blocks it and nothing happens.
- R+ rail reads 4.95 to 5.05 V. L- and R- read 0 V between them.
- Scope on the R+ rail, AC coupling, 10 mV per division: flat. A steady sine wave means the regulator is
  oscillating: send a screenshot."""),
    2: ("2.5 V reference",
        "Makes VREF, the 2.5 V that every amplifier stage uses as its zero, and puts it on the L+ rail.",
        """Check:

- L+ rail reads 2.45 to 2.55 V.
- Row 24, right half (U3 pin 7): the same as L+ to within a few millivolts. This is VSW, the separate
  copy for the switch."""),
    3: ("1024 Hz clock",
        "The crystal and U6 make the 1024 Hz square wave that drives both the LED and the switch.",
        """The crystal's legs are very thin. Push them straight down and check the crystal does not wobble.

Check: scope on row 14, left half (U6 pin 5): square wave, 0 to 5 V, 1024 Hz, half the time high.

If there is no square wave:

1. Press the crystal, R12, R13, C8 and C9 down and look again.
2. If it still does not start, pull the crystal out. Set the signal generator to a square wave, 0 to 5 V,
   32.768 kHz, and connect it to row 15, right half (U6 pin 11), generator ground to L-. Row 14 then shows
   1024 Hz. Carry on; the rest of the circuit does not care where the clock comes from."""),
    4: ("LED driver",
        "The MOSFET switches the LED on and off 1024 times a second.",
        """Check:

- The LED looks steadily lit (it blinks too fast to see).
- Scope on row 6, left half: a square wave at 1024 Hz.
- If the LED is dark, it is probably the wrong way round: swap its two legs."""),
    5: ("Photodiode amplifier and gain",
        "U1 turns the photodiode's current into a voltage, removes the steady part and amplifies the rest 11 times.",
        """The photodiode faces up. Start with the LED pointing up as well and hold a sheet of white paper about
10 cm above the board, so the photodiode sees the LED by reflection. Pointing the LED straight at the
photodiode from a few centimetres is too strong and overloads the amplifier.

Check:

- Row 30, left half (TIA) with the photodiode covered: equal to L+ (2.5 V).
- Same row in room light: above 2.5 V, by 0.1 V for each microamp of light. If it sits near 5 V the light
  is too bright: shade the photodiode. If it goes below 2.5 V, the photodiode is the wrong way round.
- With the paper in place: a small 1024 Hz square wave on row 30, left half, and the same wave 11 times
  larger on row 31, right half (AC), centred on 2.5 V. The 100 Hz ripple from the room lights is also
  visible there; that is expected."""),
    6: ("Demodulator",
        "The switch U5 and the op amp U2 flip the signal in step with the clock, so the LED's light becomes a steady level.",
        """The clock wire (b14 to j42) is the one wire to keep away from the photodiode end of U1: lay it out
past the right-hand edge of the board.

Check: with the paper in place, row 48, left half (DEM) shows the square wave folded to one side of 2.5 V
(always above it), with short spikes at each switching edge. If it is always below 2.5 V, U5 is not
switching: check row 42, right half (U5 pin 11) for the 1024 Hz clock."""),
    7: ("Filter and output",
        "Two slow filters keep only the steady level. The meter reads it between OUT and VREF.",
        """Multimeter on DC volts: red lead on a wire in **i56** (OUT), black lead on a wire in **i58** (VREF).

Check:

- LED pulled out or covered: within about 2 mV of zero. Write this number down: it is the offset to
  subtract from every later reading.
- LED back, paper in place: a steady positive voltage, 0.52 mV for each nanoamp of signal. It settles
  in about a second. Move the paper closer and the reading rises.
- Room lights on and off: the reading should not change. This is the result the project exists to show.

Send me the three readings and scope screenshots of rows 30 (left), 31 (right), 48 (left) and 14 (left)."""),
}

OUTRO = """## What is different from the circuit board

| On the breadboard | On the board | Why |
|---|---|---|
| C5 is a 10 uF electrolytic | 1 uF ceramic | Saves buying one more type with legs |
| The five 100 nF capacitors sit across the right-hand rails | One at each chip's supply pins | Their legs are too short to reach from a chip to a rail |
| U5 pins 1, 2, 3 and 5 are left open | Tied to ground | They are the ends of unused switches; open is harmless and saves four wires |
| C2 (10 nF) is a less precise type | Precise type | The precise one with legs was out of stock; the reading may be a few percent off |
| No test points | TP1 to TP6 | Any free hole of a row does the job |

A breadboard adds stray capacitance and picks up more hum than a board. Expect the same behaviour and
roughly the same numbers, not identical ones.

## Not checked

- Nothing here has been built.
- The pin numbers of the plug-in 74HC4053 are taken to be the same as the flat version (they are the
  same chip in another package); only the 74HC4060's were read from the plug-in datasheet.
- Whether the breadboard you receive has its rails cut in the middle (step 1 above finds out).
"""


def guide():
    out = [INTRO]
    counts = "The whole build uses %d parts and %d wires." % (len(PARTS), len(WIRES))
    out.append(counts + "\n")
    for stage in range(1, 8):
        title, what, check = STAGE_TEXT[stage]
        out.append("## Stage %d: %s\n" % (stage, title))
        out.append(what + "\n")
        out.append("| Part | Value | Goes in | Note |")
        out.append("|---|---|---|---|")
        for st, ref, value, kind, legs, note in PARTS:
            if st != stage:
                continue
            if len(legs) >= 8:
                first, last = "%s.1" % ref, "%s.%d" % (ref, len(legs) // 2)
                holes = "rows %s to %s, across the centre gap, pin 1 in %s" % (legs[first][1:], legs[last][1:], legs[first])
            else:
                holes = " and ".join(("the %s rail" % h) if h in RAILS else h for h in legs.values())
                if ref in RAIL_ROW:
                    holes += ", level with row %d" % RAIL_ROW[ref]
            out.append("| %s | %s | %s | %s |" % (ref, value, holes, note))
        out.append("")
        out.append("| Wire from | To | What it does |")
        out.append("|---|---|---|")
        for st, a, b, colour, what_w in WIRES:
            if st == stage:
                out.append("| %s | %s | %s |" % (a, b, what_w))
        out.append("")
        out.append(check + "\n")
    out.append(OUTRO)
    return "\n".join(out)


def main():
    pin_hole, groups, used = build()
    want, errors = check(groups)
    if errors:
        print("WIRING DOES NOT MATCH THE SCHEMATIC")
        for e in errors:
            print("  " + e)
        sys.exit(1)
    print("WIRING OK: %d nets match the schematic" % len(want))
    print("parts: %d, wires: %d, holes used: %d" % (len(PARTS), len(WIRES), len(used)))
    per_strip = {}
    for hole in used:
        per_strip.setdefault(node_of(hole), []).append(hole)
    worst = max(len(v) for v in per_strip.values())
    print("most holes used in one strip of 5: %d" % worst)
    open(os.path.join(HERE, "breadboard-layout.svg"), "w", encoding="utf-8").write(svg(pin_hole))
    open(os.path.join(HERE, "..", "BREADBOARD-GUIDE.md"), "w", encoding="utf-8", newline="\n").write(guide())
    print("wrote breadboard-layout.svg and ../BREADBOARD-GUIDE.md")


if __name__ == "__main__":
    main()
