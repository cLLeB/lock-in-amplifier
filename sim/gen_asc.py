"""Write lockin_tran.asc, a drawn LTspice schematic of the circuit in lockin_tran.cir.

Rerunning overwrites it, so stop using this script once the schematic is edited by hand
in LTspice. Pass a file name to also write a rough SVG picture of the drawing.

Run with KiCad's Python:  python.exe gen_asc.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SYM = os.path.join(os.environ["LOCALAPPDATA"], "LTspice", "lib", "sym")

OPAMP = "OpAmps\\UniversalOpAmp2"
lines = ["Version 4", "SHEET 1 3800 1500"]
svg = []


def wire(*pts):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        lines.append("WIRE %d %d %d %d" % (x1, y1, x2, y2))
        svg.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#00c" stroke-width="2"/>' % (x1, y1, x2, y2))


def flag(x, y, name):
    lines.append("FLAG %d %d %s" % (x, y, name))
    if name == "0":
        svg.append('<path d="M%d %d l-16 0 l16 16 l16 -16 z" fill="none" stroke="#00c" stroke-width="2"/>' % (x, y))
    else:
        svg.append('<text x="%d" y="%d" font-size="22" fill="#a00" text-anchor="middle">%s</text>' % (x, y - 6, name))


def symbol(kind, x, y, rot, name, value=None, extra=(), windows=()):
    lines.append("SYMBOL %s %d %d %s" % (kind, x, y, rot))
    for w in windows:
        lines.append("WINDOW " + w)
    lines.append("SYMATTR InstName " + name)
    if value is not None:
        lines.append("SYMATTR Value " + value)
    for key, val in extra:
        lines.append("SYMATTR %s %s" % (key, val))

    def tr(px, py):
        return (x - py, y + px) if rot == "R90" else (x + px, y + py)
    with open(os.path.join(SYM, kind + ".asy")) as f:
        for ln in f:
            p = ln.split()
            if p[:1] == ["LINE"]:
                (a, b), (c, d) = tr(int(p[2]), int(p[3])), tr(int(p[4]), int(p[5]))
                svg.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#000" stroke-width="2"/>' % (a, b, c, d))
            elif p[:1] == ["CIRCLE"]:
                (a, b), (c, d) = tr(int(p[2]), int(p[3])), tr(int(p[4]), int(p[5]))
                svg.append('<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="none" stroke="#000" stroke-width="2"/>'
                           % ((a + c) / 2, (b + d) / 2, abs(c - a) / 2, abs(d - b) / 2))
    label = name + ("  " + value if value else "")
    tx, ty = (x - 48, y - 8) if rot == "R90" else (x + 40, y + 40)
    if kind == OPAMP:
        tx, ty = x + 16, y - 36
    svg.append('<text x="%d" y="%d" font-size="20" fill="#060">%s</text>' % (tx, ty, label))


def text(x, y, s, directive=False, size=2):
    lines.append("TEXT %d %d Left %d %s%s" % (x, y, size, "!" if directive else ";", s))
    for k, part in enumerate(s.split("\\n")):
        svg.append('<text x="%d" y="%d" font-size="%d" fill="%s">%s</text>'
                   % (x, y + 8 + 28 * k, 22 if size == 2 else 30, "#000" if directive else "#06c",
                      part.replace("&", "&amp;").replace("<", "&lt;")))


# Two-pin parts by the position of their pins
def hres(name, value, xl, y):       # pins at (xl, y) and (xl + 80, y)
    symbol("res", xl + 96, y - 16, "R90", name, value, windows=("0 0 56 VBottom 2", "3 32 56 VTop 2"))


def vres(name, value, x, yt):       # pins at (x, yt) and (x, yt + 80)
    symbol("res", x - 16, yt - 16, "R0", name, value)


def hcap(name, value, xl, y):       # pins at (xl, y) and (xl + 64, y)
    symbol("cap", xl + 64, y - 16, "R90", name, value, windows=("0 0 32 VBottom 2", "3 32 32 VTop 2"))


def vcap(name, value, x, yt):       # pins at (x, yt) and (x, yt + 64)
    symbol("cap", x - 16, yt, "R0", name, value)


def opamp(name, x, y):
    """Pins: in- (x-32, y-16), in+ (x-32, y+16), out (x+32, y). Supplies are labelled."""
    symbol(OPAMP, x, y, "R0", name,
           extra=(("Value2", "Avol=1Meg GBW=10Meg Slew=7Meg"), ("SpiceLine", "Ilimit=20m Rail=0.02 Vos=0")))
    wire((x, y - 32), (x, y - 48))
    flag(x, y - 48, "vcc")
    wire((x, y + 32), (x, y + 48))
    flag(x, y + 48, "0")


def source(kind, name, value, x, y, top, top_net):
    """Vertical source with its lower pin grounded. `top` is the y of the upper pin."""
    oy = top - (0 if kind == "current" else 16)
    symbol(kind, x, oy, "R0", name, value)
    bottom = oy + (80 if kind == "current" else 96)
    flag(x, bottom, "0")
    if top_net:
        wire((x, top), (x, top - 32))
        flag(x, top - 32, top_net)


text(-800, 40, "Lock-in amplifier", size=3)
# ---- 1 Photodiode and transimpedance amplifier ----
text(-800, 176, "1  Photodiode and transimpedance amplifier")
X, Y = 400, 400
RAIL = Y - 16
source("current", "Isig", "PULSE(0 {Ipk} 0 1u 1u {T/2} {T})", -800, 0, RAIL, None)
source("current", "Iflick", "SINE(0 1u 100)", -352, 0, RAIL, None)
source("current", "Iamb", "5u", -96, 0, RAIL, None)
vcap("Cpd", "70p", 96, RAIL + 32)
flag(96, RAIL + 96, "0")
wire((96, RAIL), (96, RAIL + 32))
wire((-800, RAIL), (-352, RAIL), (-96, RAIL), (96, RAIL), (320, RAIL), (X - 32, RAIL))
flag(208, RAIL, "inn")
opamp("U1", X, Y)
wire((X - 32, Y + 16), (X - 80, Y + 16))
flag(X - 80, Y + 16, "vref")
hres("Rf", "100k", 320, Y - 128)
hcap("Cf", "100p", 336, Y - 208)
wire((320, RAIL), (320, Y - 128), (320, Y - 208), (336, Y - 208))
wire((400, Y - 128), (464, Y - 128), (464, Y))
wire((400, Y - 208), (464, Y - 208), (464, Y - 128))
wire((X + 32, Y), (464, Y), (528, Y))
flag(528, Y, "tia")

# ---- 2 High-pass and gain of 11 ----
text(800, 176, "2  High-pass and gain 11")
X = 1104
wire((X - 240, Y + 16), (X - 208, Y + 16))
flag(X - 240, Y + 16, "tia")
hcap("Chp", "10n", X - 208, Y + 16)
wire((X - 144, Y + 16), (X - 96, Y + 16), (X - 32, Y + 16))
vres("Rhp", "100k", X - 96, Y + 48)
wire((X - 96, Y + 16), (X - 96, Y + 48))
wire((X - 96, Y + 128), (X - 96, Y + 160))
flag(X - 96, Y + 160, "vref")
opamp("U2", X, Y)
wire((X - 32, Y - 16), (X - 64, Y - 16), (X - 64, Y - 128))
hres("Rg2", "10k", X - 64, Y - 128)
wire((X + 16, Y - 128), (X + 64, Y - 128), (X + 64, Y))
wire((X + 32, Y), (X + 64, Y), (X + 128, Y))
flag(X + 128, Y, "ac")
hres("Rg1", "1k", X - 192, Y - 128)
wire((X - 112, Y - 128), (X - 64, Y - 128))
wire((X - 192, Y - 128), (X - 240, Y - 128))
flag(X - 240, Y - 128, "vref")

# ---- 3 Synchronous demodulator ----
text(1440, 176, "3  Demodulator")
X = 1744
wire((X - 240, Y - 16), (X - 192, Y - 16))
flag(X - 240, Y - 16, "ac")
hres("Ra", "10k", X - 192, Y - 16)
wire((X - 112, Y - 16), (X - 64, Y - 16), (X - 32, Y - 16))
wire((X - 64, Y - 16), (X - 64, Y - 128))
hres("Rb", "10k", X - 64, Y - 128)
wire((X + 16, Y - 128), (X + 64, Y - 128), (X + 64, Y))
opamp("U3", X, Y)
wire((X + 32, Y), (X + 64, Y), (X + 128, Y))
flag(X + 128, Y, "dem")
wire((X - 32, Y + 16), (X - 64, Y + 16), (X - 64, Y + 64), (X - 112, Y + 64))
flag(X - 112, Y + 64, "dp")

# ---- 4 Low-pass and buffer ----
text(2240, 176, "4  Low-pass and buffer")
X = 2784
wire((X - 464, Y + 16), (X - 416, Y + 16))
flag(X - 464, Y + 16, "dem")
hres("Rl1", "100k", X - 416, Y + 16)
wire((X - 336, Y + 16), (X - 288, Y + 16), (X - 240, Y + 16))
vcap("Cl1", "1u", X - 288, Y + 48)
wire((X - 288, Y + 16), (X - 288, Y + 48))
wire((X - 288, Y + 112), (X - 288, Y + 144))
flag(X - 288, Y + 144, "vref")
hres("Rl2", "100k", X - 240, Y + 16)
wire((X - 160, Y + 16), (X - 96, Y + 16), (X - 32, Y + 16))
vcap("Cl2", "1u", X - 96, Y + 48)
wire((X - 96, Y + 16), (X - 96, Y + 48))
wire((X - 96, Y + 112), (X - 96, Y + 144))
flag(X - 96, Y + 144, "vref")
opamp("U4", X, Y)
wire((X - 32, Y - 16), (X - 64, Y - 16), (X - 64, Y - 112), (X + 64, Y - 112), (X + 64, Y))
wire((X + 32, Y), (X + 64, Y), (X + 128, Y))
flag(X + 128, Y, "out")

# ---- Supply, virtual ground, clock, switches ----
Y2 = 864
text(-800, 688, "Supply")
source("voltage", "Vcc", "5", -752, 0, Y2, "vcc")

text(-560, 688, "2.5 V virtual ground")
GX = -480
wire((GX, Y2 - 80), (GX, Y2 - 112))
flag(GX, Y2 - 112, "vcc")
vres("Rv1", "10k", GX, Y2 - 80)
wire((GX, Y2), (GX, Y2 + 16), (GX, Y2 + 32))
vres("Rv2", "10k", GX, Y2 + 32)
flag(GX, Y2 + 112, "0")
OX, OYY = GX + 320, Y2
wire((GX, Y2 + 16), (GX + 128, Y2 + 16), (OX - 32, Y2 + 16))
vcap("Cv", "10u", GX + 128, Y2 + 48)
wire((GX + 128, Y2 + 16), (GX + 128, Y2 + 48))
flag(GX + 128, Y2 + 112, "0")
opamp("U5", OX, OYY)
wire((OX - 32, OYY - 16), (OX - 64, OYY - 16), (OX - 64, OYY - 112), (OX + 64, OYY - 112), (OX + 64, OYY))
wire((OX + 32, OYY), (OX + 64, OYY), (OX + 128, OYY))
flag(OX + 128, OYY, "vref")

# Second buffer: feeds only the analog switch, so switching spikes stay off vref
text(32, 688, "Switch buffer")
BX = OX + 352
wire((OX + 128, OYY), (BX - 128, OYY), (BX - 128, OYY + 16), (BX - 32, OYY + 16))
opamp("U6", BX, OYY)
wire((BX - 32, OYY - 16), (BX - 64, OYY - 16), (BX - 64, OYY - 112), (BX + 64, OYY - 112), (BX + 64, OYY))
wire((BX + 32, OYY), (BX + 64, OYY), (BX + 128, OYY))
flag(BX + 128, OYY, "vsw")

text(608, 688, "1024 Hz clock")
source("voltage", "Vclk", "PULSE(0 5 0 1u 1u {T/2} {T})", 688, 0, Y2, "ref")
source("bv", "Bnb", "V=5-V(ref)", 1200, 0, Y2, "refb")

text(1648, 688, "Analog switch")
for name, sx, a_net, ctrl in (("S1", 1792, "ac", "ref"), ("S2", 2128, "vsw", "refb")):
    sy = Y2 - 16
    symbol("sw", sx, sy, "R0", name, "SW4053")
    wire((sx, sy + 16), (sx, sy - 16))
    flag(sx, sy - 16, a_net)
    wire((sx, sy + 96), (sx, sy + 128), (sx + 64, sy + 128))
    flag(sx + 64, sy + 128, "dp")
    wire((sx - 48, sy + 80), (sx - 112, sy + 80))
    flag(sx - 112, sy + 80, ctrl)
    wire((sx - 48, sy + 32), (sx - 112, sy + 32))
    flag(sx - 112, sy + 32, "0")

# ---- Simulation commands ----
text(-800, 1120, ".param fref=1024 T={1/fref} Ipk=10n\\n.step param Ipk list 0 10n 100n\\n.tran 0 3 0 20u\\n"
                 ".model SW4053 SW(Ron=100 Roff=100Meg Vt=2.5 Vh=0.5)\\n"
                 ".meas TRAN vout_dc AVG V(out,vref) FROM 2.5 TO 3", directive=True)


with open(os.path.join(HERE, "lockin_tran.asc"), "w", newline="\r\n") as f:
    f.write("\n".join(lines) + "\n")
if len(sys.argv) > 1:
    with open(sys.argv[1], "w") as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-900 0 4000 1400" font-family="sans-serif">'
                '<rect x="-900" y="0" width="4000" height="1400" fill="#fff"/>' + "".join(svg) + "</svg>")
print("wrote lockin_tran.asc,", len(lines), "lines")
