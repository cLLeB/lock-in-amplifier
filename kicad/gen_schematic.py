"""Generate lockin.kicad_sch for the lock-in amplifier and the netlist it is expected to produce.

Run with KiCad's bundled Python:  python gen_schematic.py
Coordinates below are in grid units of 2.54 mm. Regenerating overwrites lockin.kicad_sch,
so hand edits made in KiCad are lost; edit this file instead, or stop using it once the
schematic is taken over by hand.
"""
import json
import os
import uuid

from kisym import Q, child, dump, load_symbol, pins

G = 2.54
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = "lockin"
ROOT = str(uuid.uuid4())

FP_R = "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder"
FP_C = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
FP_FILM = "Capacitor_THT:C_Rect_L7.2mm_W4.5mm_P5.00mm_FKS2_FKP2_MKS2_MKP2"
FP_ELEC = "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm"
FP_SO8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
FP_SO16 = "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm"
FP_TO92 = "Package_TO_SOT_THT:TO-92_Inline_Wide"
FP_PD = "OptoDevice:Osram_DIL2_4.3x4.65mm_P5.08mm"
FP_XTAL = "Crystal:Crystal_C26-LF_D2.1mm_L6.5mm_Vertical"
FP_H2 = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
FP_H3 = "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
FP_DIODE = "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal"


def uid():
    return str(uuid.uuid4())


def num(v):
    s = "%.4f" % v
    s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def transform(x, y, rot, mirror):
    """Library coordinates (y up) to an on-sheet offset (y down)."""
    sx, sy = x, -y
    if mirror == "x":
        sy = -sy
    if rot == 90:
        sx, sy = sy, -sx
    elif rot == 180:
        sx, sy = -sx, -sy
    elif rot == 270:
        sx, sy = -sy, sx
    return sx, sy


class Sheet:
    def __init__(self):
        self.libs = {}
        self.out = []
        self.pin_at = {}      # (ref, pin number) -> (x, y) in mm
        self.segs = []        # wire segments in mm
        self.power_count = 0
        self.flag_count = 0

    def lib(self, lib_id):
        if lib_id not in self.libs:
            lib, name = lib_id.split(":")
            self.libs[lib_id] = load_symbol(lib, name)
        return self.libs[lib_id]

    def place(self, ref, lib_id, x, y, rot=0, mirror=None, unit=1, value=None, fp=None,
              ref_at=None, val_at=None):
        sym = self.lib(lib_id)
        X, Y = x * G, y * G
        lines = ["\t(symbol", '\t\t(lib_id "%s")' % lib_id,
                 "\t\t(at %s %s %d)" % (num(X), num(Y), rot)]
        if mirror:
            lines.append("\t\t(mirror %s)" % mirror)
        lines += ["\t\t(unit %d)" % unit, "\t\t(exclude_from_sim no)", "\t\t(in_bom yes)",
                  "\t\t(on_board yes)", "\t\t(dnp no)", '\t\t(uuid "%s")' % uid()]
        for e in sym:
            if not (isinstance(e, list) and e[0] == "property"):
                continue
            key = str(e[1])
            if key.startswith("ki_"):
                continue
            text = str(e[2])
            at = child(e, "at")
            px, py = transform(float(at[1]), float(at[2]), rot, mirror)
            ang = int(float(at[3])) if len(at) > 3 else 0
            pos = (X + px, Y + py)
            eff = child(e, "effects")
            # A field's stored angle is relative to the symbol, so a sideways symbol needs 90 to read level.
            level = 90 if rot in (90, 270) else 0
            if key == "Reference":
                text = ref
                if ref_at:
                    pos, ang, eff = (ref_at[0] * G, ref_at[1] * G), level, None
            elif key == "Value":
                if value is not None:
                    text = value
                if val_at:
                    pos, ang, eff = (val_at[0] * G, val_at[1] * G), level, None
            elif key == "Footprint" and fp is not None:
                text = fp
            hide = "\n\t\t\t(hide yes)" if child(e, "hide") is not None else ""
            eff_txt = dump(eff, 3) if eff else "(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)"
            lines.append('\t\t(property "%s" "%s"\n\t\t\t(at %s %s %d)%s\n\t\t\t%s\n\t\t)'
                         % (key, text, num(pos[0]), num(pos[1]), ang, hide, eff_txt))
        table = pins(sym)
        for p in table.get(unit, []) + table.get(0, []):
            dx, dy = transform(p["x"], p["y"], rot, mirror)
            self.pin_at[(ref, p["num"])] = (round(X + dx, 4), round(Y + dy, 4))
            lines.append('\t\t(pin "%s"\n\t\t\t(uuid "%s")\n\t\t)' % (p["num"], uid()))
        lines.append('\t\t(instances\n\t\t\t(project "%s"\n\t\t\t\t(path "/%s"\n\t\t\t\t\t(reference "%s")\n'
                     '\t\t\t\t\t(unit %d)\n\t\t\t\t)\n\t\t\t)\n\t\t)' % (PROJECT, ROOT, ref, unit))
        lines.append("\t)")
        self.out.append("\n".join(lines))

    def pt(self, p):
        """A point is (x, y) in grid units or 'REF.pin'."""
        if isinstance(p, str):
            ref, pin = p.split(".")
            return self.pin_at[(ref, pin)]
        return (round(p[0] * G, 4), round(p[1] * G, 4))

    def wire(self, *points):
        pts = [self.pt(p) for p in points]
        for a, b in zip(pts, pts[1:]):
            if a == b:
                continue
            if a[0] != b[0] and a[1] != b[1]:
                raise ValueError("diagonal wire %s -> %s" % (a, b))
            self.segs.append((a, b))
            self.out.append('\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n'
                            '\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)'
                            % (num(a[0]), num(a[1]), num(b[0]), num(b[1]), uid()))

    def label(self, name, p, rot=0):
        x, y = self.pt(p)
        just = {0: "left bottom", 180: "right bottom", 90: "left bottom", 270: "right bottom"}[rot]
        self.out.append('\t(label "%s"\n\t\t(at %s %s %d)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n'
                        '\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n\t)'
                        % (name, num(x), num(y), rot, just, uid()))

    def power(self, kind, p):
        self.power_count += 1
        ref = "#PWR%02d" % self.power_count
        x, y = self.pt(p)
        self.place(ref, "power:" + kind, x / G, y / G)

    def flag(self, p):
        self.flag_count += 1
        x, y = self.pt(p)
        self.place("#FLG%02d" % self.flag_count, "power:PWR_FLAG", x / G, y / G)

    def nc(self, p):
        x, y = self.pt(p)
        self.out.append('\t(no_connect\n\t\t(at %s %s)\n\t\t(uuid "%s")\n\t)' % (num(x), num(y), uid()))

    def text(self, s, x, y, size=2.0):
        self.out.append('\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at %s %s 0)\n\t\t(effects\n\t\t\t(font\n'
                        '\t\t\t\t(size %s %s)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)'
                        % (s, num(x * G), num(y * G), num(size), num(size), uid()))

    def junctions(self):
        ends = {}
        for a, b in self.segs:
            ends[a] = ends.get(a, 0) + 1
            ends[b] = ends.get(b, 0) + 1
        for p, n in ends.items():
            inside = 0
            for a, b in self.segs:
                if p in (a, b):
                    continue
                if a[0] == b[0] == p[0] and min(a[1], b[1]) < p[1] < max(a[1], b[1]):
                    inside += 1
                elif a[1] == b[1] == p[1] and min(a[0], b[0]) < p[0] < max(a[0], b[0]):
                    inside += 1
            if n >= 3 or inside:
                self.out.append('\t(junction\n\t\t(at %s %s)\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n'
                                '\t\t(uuid "%s")\n\t)' % (num(p[0]), num(p[1]), uid()))

    def write(self, path, title):
        self.junctions()
        libs = []
        for lib_id, sym in self.libs.items():
            node = list(sym)
            node[1] = Q(lib_id)
            libs.append("\t\t" + dump(node, 2))
        body = ['(kicad_sch', '\t(version 20250114)', '\t(generator "eeschema")', '\t(generator_version "9.0")',
                '\t(uuid "%s")' % ROOT, '\t(paper "A3")',
                '\t(title_block\n\t\t(title "%s")\n\t\t(rev "0.1")\n\t)' % title,
                "\t(lib_symbols\n%s\n\t)" % "\n".join(libs)]
        body += self.out
        body += ['\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)', "\t(embedded_fonts no)", ")"]
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(body) + "\n")


def R(s, ref, value, x, y, horiz=False, side=1):
    if horiz:
        s.place(ref, "Device:R", x, y, rot=90, value=value, fp=FP_R, ref_at=(x, y - 1), val_at=(x, y + 1.25))
    else:
        s.place(ref, "Device:R", x, y, value=value, fp=FP_R, ref_at=(x + 2 * side, y - 0.5), val_at=(x + 2 * side, y + 0.5))


def C(s, ref, value, x, y, horiz=False, fp=FP_C, polar=False, side=1):
    lib = "Device:C_Polarized" if polar else "Device:C"
    if horiz:
        s.place(ref, lib, x, y, rot=90, value=value, fp=fp, ref_at=(x, y - 1.5), val_at=(x, y + 1.75))
    else:
        s.place(ref, lib, x, y, value=value, fp=fp, ref_at=(x + 2.2 * side, y - 0.5), val_at=(x + 2.2 * side, y + 0.5))


def build():
    s = Sheet()
    OPA = "Amplifier_Operational:MCP6022"

    # ---- 1. Transimpedance amplifier -------------------------------------------------
    s.text("1  Transimpedance amplifier", 16, 15)
    s.place("U1", OPA, 30, 30, mirror="x", unit=1, value="MCP6022", fp=FP_SO8, ref_at=(31, 33), val_at=(31, 34))
    s.place("D1", "Sensor_Optical:BPW34", 21, 29, rot=180, value="BPW34", fp=FP_PD, ref_at=(21, 26.5), val_at=(21, 27.5))
    R(s, "R1", "100k", 30, 24, horiz=True)
    C(s, "C1", "100p", 30, 19, horiz=True)
    s.wire("D1.1", (25, 29), "U1.2")
    s.wire("D1.2", (18, 29), (18, 31))
    s.power("GND", (18, 31))
    s.wire((25, 29), (25, 24), "R1.1")
    s.wire((25, 24), (25, 19), "C1.1")
    s.wire("R1.2", (35, 24), (35, 30))
    s.wire("C1.2", (35, 19), (35, 24))
    s.wire("U1.1", (35, 30))
    s.wire("U1.3", (25, 31))
    s.label("VREF", (25, 31), 180)

    # ---- 2. High-pass filter and gain ------------------------------------------------
    s.text("2  High-pass 159 Hz, gain 11", 38, 15)
    C(s, "C2", "10n", 40, 30, horiz=True)
    R(s, "R2", "100k", 45, 34, side=-1)
    s.place("U1", OPA, 52, 31, unit=2, value="MCP6022", fp=FP_SO8, ref_at=(53, 28), val_at=(53, 29))
    R(s, "R3", "10k", 52, 37, horiz=True)
    R(s, "R4", "1k", 47, 41)
    s.wire((35, 30), "C2.1")
    s.wire("C2.2", (45, 30), "U1.5")
    s.wire((45, 30), "R2.1")
    s.wire("R2.2", (45, 37))
    s.label("VREF", (45, 37), 270)
    s.wire("U1.6", (47, 32), (47, 37), "R3.1")
    s.wire("R3.2", (57, 37), (57, 31))
    s.wire("U1.7", (57, 31), (60, 31))
    s.label("AC", (60, 31))
    s.wire((47, 37), "R4.1")
    s.wire("R4.2", (47, 44))
    s.label("VREF", (47, 44), 270)

    # ---- 3. Synchronous demodulator --------------------------------------------------
    s.text("3  Synchronous demodulator", 62, 15)
    s.label("AC", (64, 30), 180)
    R(s, "R5", "10k", 68, 30, horiz=True)
    s.place("U2", OPA, 78, 31, mirror="x", unit=1, value="MCP6022", fp=FP_SO8, ref_at=(79, 34), val_at=(79, 35))
    R(s, "R6", "10k", 78, 25, horiz=True)
    s.wire((64, 30), "R5.1")
    s.wire("R5.2", (73, 30), "U2.2")
    s.wire((73, 30), (73, 25), "R6.1")
    s.wire("R6.2", (83, 25), (83, 31))
    s.wire("U2.1", (83, 31))
    s.wire("U2.3", (72, 32))
    s.label("DP", (72, 32), 180)

    s.place("U5", "4xxx:4053", 70, 50, value="74HC4053", fp=FP_SO16, ref_at=(66, 41.5), val_at=(66, 42.5))
    s.wire("U5.12", (62, 44))
    s.label("VSW", (62, 44), 180)
    s.wire("U5.13", (62, 45))
    s.label("AC", (62, 45), 180)
    s.wire("U5.14", (78, 44))
    s.label("DP", (78, 44))
    s.wire("U5.11", (59, 54))
    s.label("REF", (59, 54), 180)
    for pin in ("2", "1", "5", "3", "6", "10", "9"):
        x, y = s.pin_at[("U5", pin)]
        s.wire("U5." + pin, (63, y / G))
    s.wire((63, 47), (63, 58))
    s.power("GND", (63, 58))
    s.nc("U5.15")
    s.nc("U5.4")
    s.power("+5V", "U5.16")
    s.wire("U5.8", (70, 60))
    s.wire("U5.7", (71, 60), (70, 60))
    s.power("GND", (70, 60))

    # ---- 4. Low-pass filter and output buffer ----------------------------------------
    s.text("4  Low-pass 1.6 Hz x2, buffer", 86, 15)
    R(s, "R7", "100k", 88, 31, horiz=True)
    C(s, "C3", "1u film", 92, 35, fp=FP_FILM, side=-1)
    R(s, "R8", "100k", 95, 31, horiz=True)
    C(s, "C4", "1u film", 99, 35, fp=FP_FILM, side=-1)
    s.place("U2", OPA, 106, 32, unit=2, value="MCP6022", fp=FP_SO8, ref_at=(107, 29), val_at=(107, 30))
    R(s, "R9", "100", 115, 32, horiz=True)
    s.place("J2", "Connector_Generic:Conn_01x03", 125, 33, value="OUT / VREF / GND", fp=FP_H3,
            ref_at=(124, 29), val_at=(124, 30))
    s.wire((83, 31), "R7.1")
    s.wire("R7.2", "R8.1")
    s.wire((92, 31), "C3.1")
    s.wire("C3.2", (92, 38))
    s.label("VREF", (92, 38), 270)
    s.wire("R8.2", "U2.5")
    s.wire((99, 31), "C4.1")
    s.wire("C4.2", (99, 38))
    s.label("VREF", (99, 38), 270)
    s.wire("U2.6", (102, 33), (102, 42), (111, 42), (111, 32))
    s.wire("U2.7", (111, 32), "R9.1")
    s.wire("R9.2", "J2.1")
    R(s, "R17", "100", 120, 41)
    s.wire("J2.2", (120, 33), "R17.1")
    s.wire("R17.2", (120, 44))
    s.label("VREF", (120, 44), 270)
    s.wire("J2.3", (122, 34), (122, 36))
    s.power("GND", (122, 36))

    # ---- Power input and 5 V regulator -----------------------------------------------
    s.text("Battery input and 5 V regulator", 16, 70)
    s.place("J1", "Connector_Generic:Conn_01x02", 30, 80, value="9 V battery", fp=FP_H2,
            ref_at=(30, 77), val_at=(30, 78))
    s.place("D2", "Diode:1N4148", 22, 80, value="1N4148", fp=FP_DIODE, ref_at=(22, 77.5), val_at=(22, 78.5))
    s.wire("J1.1", "D2.2")
    s.wire("D2.1", (18, 80))
    s.power("+9V", (18, 80))
    s.wire("J1.2", (26, 81), (26, 83))
    s.power("GND", (26, 83))

    s.place("U4", "Regulator_Linear:LP2950-5.0_TO92", 45, 80, value="LP2950-5.0", fp=FP_TO92)
    C(s, "C5", "1u", 40, 84)
    C(s, "C6", "10u", 51, 84, fp=FP_ELEC, polar=True)
    s.power("+9V", (38, 80))
    s.wire((38, 80), "U4.3")
    s.wire((40, 80), "C5.1")
    s.wire("U4.1", (55, 80))
    s.power("+5V", (55, 80))
    s.wire((51, 80), "C6.1")
    s.wire("C5.2", (40, 87), (51, 87), "C6.2")
    s.wire("U4.2", (45, 87), (45, 88))
    s.power("GND", (45, 88))

    # ---- Virtual ground --------------------------------------------------------------
    s.text("2.5 V virtual ground (VREF)", 62, 70)
    R(s, "R10", "10k", 65, 78)
    R(s, "R11", "10k", 65, 84.5)
    C(s, "C7", "10u", 69, 84.5, fp=FP_ELEC, polar=True)
    s.place("U3", OPA, 79, 82, unit=1, value="MCP6022", fp=FP_SO8, ref_at=(80, 79), val_at=(80, 80))
    s.wire("R10.1", (65, 75))
    s.power("+5V", (65, 75))
    s.wire("R10.2", "R11.1")
    s.wire((65, 81), (69, 81), "U3.3")
    s.wire((69, 81), "C7.1")
    s.wire("R11.2", (65, 88))
    s.wire("C7.2", (69, 88), (65, 88))
    s.wire((65, 88), (65, 89))
    s.power("GND", (65, 89))
    s.wire("U3.2", (75, 83), (75, 87), (84, 87), (84, 82))
    s.wire("U3.1", (84, 82), (87, 82))
    s.label("VREF", (87, 82))

    s.place("U3", OPA, 79, 96, unit=2, value="MCP6022", fp=FP_SO8, ref_at=(80, 93), val_at=(80, 94))
    s.text("2.5 V buffer for the switch (VSW)", 72, 90, size=1.27)
    s.wire("U3.5", (74, 95))
    s.label("VREF", (74, 95), 180)
    s.wire("U3.6", (75, 97), (75, 101), (84, 101), (84, 96), "U3.7")
    s.wire((84, 96), (87, 96))
    s.label("VSW", (87, 96))

    # ---- Reference clock -------------------------------------------------------------
    s.text("1024 Hz reference: 32.768 kHz / 32", 90, 70)
    s.place("U6", "74xx:74HC4060", 110, 85, value="74HC4060", fp=FP_SO16, ref_at=(114, 76), val_at=(114, 77))
    R(s, "R12", "330k", 96, 81, horiz=True)
    R(s, "R13", "10M", 100, 85, side=-1)
    s.place("Y1", "Device:Crystal", 97, 90, value="32.768k", fp=FP_XTAL, ref_at=(97, 87.5), val_at=(97, 92.25))
    C(s, "C8", "22p", 92, 93.5)
    C(s, "C9", "22p", 102, 93.5)
    s.wire("U6.10", "R12.2")
    s.wire((100, 81), "R13.1")
    s.wire("R13.2", (100, 88), (102, 88))
    s.wire("U6.11", (102, 82), (102, 90), "C9.1")
    s.wire("Y1.2", (102, 90))
    s.wire("R12.1", (92, 81), (92, 90), "C8.1")
    s.wire((92, 90), "Y1.1")
    s.wire("C8.2", (92, 97), (102, 97), "C9.2")
    s.wire((97, 97), (97, 98))
    s.power("GND", (97, 98))
    s.wire("U6.12", (104, 84), (104, 87))
    s.power("GND", (104, 87))
    s.nc("U6.9")
    for pin in ("7", "4", "6", "14", "13", "15", "1", "2", "3"):
        s.nc("U6." + pin)
    s.wire("U6.5", (119, 81))
    s.label("REF", (119, 81))
    s.power("+5V", "U6.16")
    s.power("GND", "U6.8")

    # ---- LED driver ------------------------------------------------------------------
    s.text("LED driver (LED on a lead, powered from 9 V)", 124, 70)
    s.place("Q1", "Transistor_FET:2N7000", 135, 85, value="2N7000", fp=FP_TO92, ref_at=(138, 84.5), val_at=(138, 85.5))
    R(s, "R14", "100", 129, 85, horiz=True)
    R(s, "R15", "100k", 132, 88.5)
    R(s, "R16", "680", 139, 76, horiz=True)
    s.place("J3", "Connector_Generic:Conn_01x02", 146, 76, value="LED anode / cathode", fp=FP_H2,
            ref_at=(146, 73), val_at=(146, 74))
    s.label("REF", (125, 85), 180)
    s.wire((125, 85), "R14.1")
    s.wire("R14.2", "Q1.2")
    s.wire((132, 85), "R15.1")
    s.wire("R15.2", (132, 91), (136, 91))
    s.wire("Q1.1", (136, 92))
    s.power("GND", (136, 92))
    s.wire("Q1.3", (136, 77), "J3.2")
    s.power("+9V", (134, 76))
    s.wire((134, 76), "R16.1")
    s.wire("R16.2", "J3.1")

    # ---- Op amp supply pins and decoupling --------------------------------------------
    s.text("Supply pins and decoupling (one 100 nF at each IC)", 16, 100)
    for i, (ref, cap) in enumerate((("U1", "C10"), ("U2", "C11"), ("U3", "C12"))):
        x = 22 + 16 * i
        s.place(ref, OPA, x, 110, unit=3, value="MCP6022", fp=FP_SO8, ref_at=(x - 5, 109.5), val_at=(x - 5, 110.5))
        C(s, cap, "100n", x + 3, 110)
        px = s.pin_at[(ref, "8")][0] / G
        s.power("+5V", ref + ".8")
        s.power("GND", ref + ".4")
        s.wire(ref + ".8", (x + 3, 107), cap + ".1")
        s.wire(ref + ".4", (x + 3, 113), cap + ".2")
    for i, cap in enumerate(("C13", "C14")):
        x = 70 + 8 * i
        C(s, cap, "100n", x, 110)
        s.wire(cap + ".1", (x, 107))
        s.power("+5V", (x, 107))
        s.wire(cap + ".2", (x, 113))
        s.power("GND", (x, 113))
    # Test points on the nodes to probe in the lab.
    FP_TP = "TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm"
    for ref, name, x, y in (("TP1", "TIA", 37, 30), ("TP2", "AC", 59, 31), ("TP3", "DEM", 85, 31),
                            ("TP4", "REF", 117, 81), ("TP5", "VREF", 86, 82)):
        # A pin resting on the middle of a wire is not connected; a stub ending on the wire is.
        s.place(ref, "Connector:TestPoint", x, y - 1, value=name, fp=FP_TP)
        s.wire((x, y), (x, y - 1))
    s.place("TP6", "Connector:TestPoint", 116, 110, value="GND", fp=FP_TP)
    s.wire((116, 110), (116, 112))
    s.power("GND", (116, 112))
    # Tell the rule checker that the battery drives +9V and GND.
    s.text("Power flags for the rule checker", 92, 106, size=1.27)
    s.flag((94, 110))
    s.wire((94, 110), (100, 110))
    s.power("+9V", (100, 110))
    s.flag((108, 110))
    s.wire((108, 110), (108, 112))
    s.power("GND", (108, 112))
    return s


# The netlist the drawing must produce: net name -> pins. Checked by check_netlist.py.
EXPECTED = {
    "GND": ["D1.2", "U5.1", "U5.2", "U5.3", "U5.5", "U5.6", "U5.7", "U5.8", "U5.9", "U5.10", "J2.3", "J1.2",
            "U4.2", "C5.2", "C6.2", "R11.2", "C7.2", "C8.2", "C9.2", "U6.12", "U6.8", "Q1.1", "R15.2",
            "U1.4", "U2.4", "U3.4", "C10.2", "C11.2", "C12.2", "C13.2", "C14.2", "TP6.1"],
    "+9V": ["D2.1", "U4.3", "C5.1", "R16.1"],
    "VBAT": ["J1.1", "D2.2"],
    "+5V": ["U4.1", "C6.1", "R10.1", "U5.16", "U6.16", "U1.8", "U2.8", "U3.8",
            "C10.1", "C11.1", "C12.1", "C13.1", "C14.1"],
    "VREF": ["U1.3", "R2.2", "R4.2", "C3.2", "C4.2", "R17.2", "U3.1", "U3.2", "U3.5", "TP5.1"],
    "VREFJ": ["R17.1", "J2.2"],
    "VMID": ["R10.2", "R11.1", "C7.1", "U3.3"],
    "PD": ["D1.1", "U1.2", "R1.1", "C1.1"],
    "TIA": ["U1.1", "R1.2", "C1.2", "C2.1", "TP1.1"],
    "HP": ["C2.2", "R2.1", "U1.5"],
    "GN": ["U1.6", "R3.1", "R4.1"],
    "AC": ["U1.7", "R3.2", "R5.1", "U5.13", "TP2.1"],
    "DN": ["R5.2", "U2.2", "R6.1"],
    "DEM": ["R6.2", "U2.1", "R7.1", "TP3.1"],
    "DP": ["U2.3", "U5.14"],
    "F1": ["R7.2", "R8.1", "C3.1"],
    "F2": ["R8.2", "C4.1", "U2.5"],
    "OUT": ["U2.6", "U2.7", "R9.1"],
    "OUTJ": ["R9.2", "J2.1"],
    "VSW": ["U3.6", "U3.7", "U5.12"],
    "REF": ["U6.5", "U5.11", "R14.1", "TP4.1"],
    "XR": ["U6.10", "R12.2", "R13.1"],
    "X1": ["U6.11", "R13.2", "Y1.2", "C9.1"],
    "X2": ["R12.1", "Y1.1", "C8.1"],
    "GATE": ["R14.2", "Q1.2", "R15.1"],
    "DRAIN": ["Q1.3", "J3.2"],
    "LEDA": ["R16.2", "J3.1"],
}

if __name__ == "__main__":
    sheet = build()
    sheet.write(os.path.join(HERE, PROJECT + ".kicad_sch"), "Lock-in amplifier for an optical sensor")
    pro = os.path.join(HERE, PROJECT + ".kicad_pro")
    if not os.path.exists(pro):
        with open(pro, "w", encoding="utf-8") as f:
            json.dump({"meta": {"filename": PROJECT + ".kicad_pro", "version": 3}}, f)
    with open(os.path.join(HERE, "expected_nets.json"), "w", encoding="utf-8") as f:
        json.dump(EXPECTED, f, indent=1)
    print("wrote", PROJECT + ".kicad_sch", "with", len(sheet.pin_at), "pins placed")
