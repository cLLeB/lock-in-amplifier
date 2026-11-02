"""Create the board (lockin.kicad_pcb) from lockin.net: place, route, pour ground.

Loads every footprint, assigns nets, links each footprint to its schematic symbol,
places the parts in functional groups, routes the tracks with a grid router and fills
a ground plane on the bottom layer. Rerunning overwrites lockin.kicad_pcb, so stop
using this script once the board is edited by hand in KiCad.

Run with KiCad's Python:  python.exe gen_board.py
"""
import heapq
import os
import sys

import pcbnew

from kisym import parse

HERE = os.path.dirname(os.path.abspath(__file__))
FP_ROOT = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), "share", "kicad", "footprints")
OUT = os.path.join(HERE, "lockin.kicad_pcb")

# Board origin on the page and size, mm
OX, OY = 100.0, 80.0
W, H = 90.0, 60.0

TRACK = 0.3         # track width, mm
VIA_D, VIA_DRILL = 0.7, 0.3
G = 0.25            # routing grid, mm
PAD_INFL = 0.4      # clearance 0.2 + half track 0.15 + margin
EDGE = 0.75         # keep track centres this far from the board edge
BOTTOM_COST = 4     # tracks on the bottom cut the ground plane, so they cost more
VIA_COST = 30

# ref: (x, y, rotation) in mm from the board's top-left corner
PLACE = {
    # 1 Transimpedance amplifier: photodiode, R1, C1 tight around U1 pin 2
    "D1": (8, 16, 90), "U1": (22, 16, 0), "R1": (20, 7, 0), "C1": (20, 11, 0), "C10": (22, 22, 0),
    # 2 High-pass and gain
    "C2": (31, 10, 0), "R2": (31, 14, 0), "R3": (31, 18, 0), "R4": (31, 22, 0),
    # 3 Demodulator
    "R5": (43, 7, 180), "R6": (43, 12, 0), "U2": (44, 17, 0), "C11": (44, 23, 0),
    "U5": (57, 17, 0), "C13": (57, 26, 0),
    # 4 Low-pass, buffer, output
    "R7": (67, 7, 0), "R8": (67, 11, 0), "C3": (70, 17, 0), "C4": (70, 24, 0),
    "R9": (80, 9, 0), "R17": (79, 13, 0), "J2": (86, 12, 0),
    # Virtual ground, below the amplifiers
    "R10": (10, 36, 0), "R11": (10, 40, 0), "C7": (11, 46, 0), "U3": (20, 42, 0), "C12": (20, 48, 0),
    # Clock: bottom centre, away from the photodiode
    "Y1": (33, 38, 0), "C8": (33, 44, 0), "C9": (33, 48, 0), "U6": (42, 42, 0), "C14": (42, 51, 0),
    "R12": (50, 35, 0), "R13": (50, 39, 0),
    # Supply and LED driver share the bottom-right corner, so the LED current loop
    # (battery, R16, LED, Q1, battery) stays local and off the amplifiers' ground.
    "U4": (60, 42, 0), "C5": (60, 48, 0), "C6": (70, 44, 0),
    "R14": (76, 35, 0), "R15": (76, 39, 0), "Q1": (77, 45, 0), "R16": (82, 35, 0),
    "J3": (86, 38, 0), "J1": (86, 47, 0), "D2": (73, 52.5, 0),
    # Test points along the top edge
    "TP1": (28, 3.5, 0), "TP2": (36, 3.5, 0), "TP3": (52, 3.5, 0), "TP4": (62, 3.5, 0),
    "TP5": (72, 3.5, 0), "TP6": (80, 3.5, 0),
}
HOLES = [(4, 4), (86, 4), (4, 56), (86, 56)]

NX, NY = int(round(W / G)) + 1, int(round(H / G)) + 1
N = NX * NY
F, B = 0, 1
LAYER = {F: pcbnew.F_Cu, B: pcbnew.B_Cu}
DISC2 = [(dx, dy) for dx in range(-2, 3) for dy in range(-2, 3) if dx * dx + dy * dy <= 4]
DISC3 = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4) if dx * dx + dy * dy <= 8]
VIA_RING = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)] + [(2, 0), (-2, 0), (0, 2), (0, -2)]
MOVES = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
         (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]


def kids(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def kid(node, key):
    found = kids(node, key)
    return found[0] if found else None


def mm(v):
    return pcbnew.FromMM(float(v))


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


class Router:
    def __init__(self, board):
        self.board = board
        self.occ = [[0] * N, [0] * N]   # 0 free, n > 0 reserved for net n, -1 blocked
        self.novia = [False] * N
        self.failed = []
        self.segs = []
        self.via_at = []
        self.length = 0.0
        self.vias = 0
        for iy in range(NY):
            for ix in range(NX):
                x, y = ix * G, iy * G
                if x < EDGE or y < EDGE or x > W - EDGE or y > H - EDGE:
                    self.occ[F][iy * NX + ix] = self.occ[B][iy * NX + ix] = -1

    def claim(self, layer, ix, iy, nid):
        if 0 <= ix < NX and 0 <= iy < NY:
            i = iy * NX + ix
            cur = self.occ[layer][i]
            if cur == 0:
                self.occ[layer][i] = nid
            elif cur != nid:
                self.occ[layer][i] = -1

    def claim_rect(self, layers, x1, y1, x2, y2, nid):
        for iy in range(int(-(-y1 // G)), int(y2 // G) + 1):
            for ix in range(int(-(-x1 // G)), int(x2 // G) + 1):
                for layer in layers:
                    self.claim(layer, ix, iy, nid)

    def ok(self, layer, i, nid):
        cur = self.occ[layer][i]
        return cur == 0 or cur == nid

    def via_ok(self, ix, iy, nid):
        for dx, dy in VIA_RING:
            jx, jy = ix + dx, iy + dy
            if not (0 <= jx < NX and 0 <= jy < NY):
                return False
            j = jy * NX + jx
            if self.novia[j] or not self.ok(F, j, nid) or not self.ok(B, j, nid):
                return False
        return True

    def seed(self, pad, nid):
        """Grid cell inside the pad, usable by its net, nearest to the pad centre."""
        cx, cy = pad["x"], pad["y"]
        best = None
        for iy in range(int(-(-pad["y1"] // G)), int(pad["y2"] // G) + 1):
            for ix in range(int(-(-pad["x1"] // G)), int(pad["x2"] // G) + 1):
                if all(self.ok(l, iy * NX + ix, nid) for l in pad["layers"]):
                    d = (ix * G - cx) ** 2 + (iy * G - cy) ** 2
                    if best is None or d < best[0]:
                        best = (d, ix, iy)
        return None if best is None else (best[1], best[2])

    def search(self, sources, is_target, nid, tree, top_only=False):
        """Dijkstra over (layer, cell). Returns the list of states from a source to a target."""
        dist, prev, heap = {}, {}, []
        for s in sources:
            dist[s] = 0.0
            heap.append((0.0, s))
        heapq.heapify(heap)
        while heap:
            d, s = heapq.heappop(heap)
            if d > dist.get(s, 1e18):
                continue
            if is_target(s) and s not in sources:
                path = [s]
                while s in prev:
                    s = prev[s]
                    path.append(s)
                return path[::-1]
            layer, i = divmod(s, N)
            iy, ix = divmod(i, NX)
            w = BOTTOM_COST if layer == B else 1
            for dx, dy, c in MOVES:
                jx, jy = ix + dx, iy + dy
                if not (0 <= jx < NX and 0 <= jy < NY):
                    continue
                j = jy * NX + jx
                t = layer * N + j
                if not (self.ok(layer, j, nid) or t in tree):
                    continue
                if dx and dy and not (self.ok(layer, iy * NX + jx, nid) and self.ok(layer, jy * NX + ix, nid)):
                    continue
                nd = d + c * w
                if nd < dist.get(t, 1e18):
                    dist[t] = nd
                    prev[t] = s
                    heapq.heappush(heap, (nd, t))
            if not top_only and self.via_ok(ix, iy, nid):
                t = (1 - layer) * N + i
                nd = d + VIA_COST
                if nd < dist.get(t, 1e18):
                    dist[t] = nd
                    prev[t] = s
                    heapq.heappush(heap, (nd, t))
        return None

    def add_track(self, layer, a, b, net):
        if a != b:
            self.segs.append((layer, a, b, net))

    def emit_tracks(self):
        """Write the tracks, cut wherever another track of the same net joins mid-way,
        so every junction is at a track end."""
        def key(p):
            return (round(p[0] * 1000), round(p[1] * 1000))
        ends = {}
        for layer, a, b, net in self.segs:
            ends.setdefault((net.GetNetCode(), layer), set()).update((key(a), key(b)))
        for code, p in self.via_at:
            for layer in (F, B):
                ends.setdefault((code, layer), set()).add(key(p))
        for layer, a, b, net in self.segs:
            pts = [a]
            steps = int(round(max(abs(b[0] - a[0]), abs(b[1] - a[1])) / G))
            on_grid = all(abs(v / G - round(v / G)) < 1e-6 for v in a + b)
            if on_grid:
                for k in range(1, steps):
                    p = (a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps)
                    if key(p) in ends[(net.GetNetCode(), layer)]:
                        pts.append(p)
            pts.append(b)
            for p, q in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(self.board)
                t.SetStart(pt(*p))
                t.SetEnd(pt(*q))
                t.SetWidth(mm(TRACK))
                t.SetLayer(LAYER[layer])
                t.SetNet(net)
                self.board.Add(t)
                self.length += ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5

    def add_via(self, ix, iy, net, nid):
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(pt(ix * G, iy * G))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetDrill(mm(VIA_DRILL))
        try:
            v.SetWidth(pcbnew.F_Cu, mm(VIA_D))
        except TypeError:
            v.SetWidth(mm(VIA_D))
        v.SetNet(net)
        self.board.Add(v)
        self.vias += 1
        self.via_at.append((net.GetNetCode(), (ix * G, iy * G)))
        for dx, dy in DISC3:
            self.claim(F, ix + dx, iy + dy, nid)
            self.claim(B, ix + dx, iy + dy, nid)

    def lay(self, path, net, nid, tree):
        """Turn a path of states into tracks and vias, and reserve the space."""
        cells = [divmod(s, N) for s in path]
        k = 0
        while k < len(cells) - 1:
            (la, a), (lb, b) = cells[k], cells[k + 1]
            if la != lb:
                iy, ix = divmod(a, NX)
                self.add_via(ix, iy, net, nid)
                k += 1
                continue
            m = k + 1
            while m + 1 < len(cells) and cells[m + 1][0] == la and cells[m + 1][1] - cells[m][1] == b - a:
                m += 1
            self._seg(cells[k], cells[m], net)
            k = m
        for layer, i in cells:
            iy, ix = divmod(i, NX)
            for dx, dy in DISC2:
                self.claim(layer, ix + dx, iy + dy, nid)
        tree.update(path)

    def _seg(self, a, b, net):
        (layer, i), (_, j) = a, b
        ay, ax = divmod(i, NX)
        by, bx = divmod(j, NX)
        self.add_track(layer, (ax * G, ay * G), (bx * G, by * G), net)


def build(priority):
    """Place and route once. Nets named in `priority` are routed before the others."""
    with open(os.path.join(HERE, "lockin.net"), encoding="utf-8") as f:
        net = parse(f.read())[0]

    board = pcbnew.NewBoard(OUT)

    pin_net, net_id, net_item = {}, {}, {}
    for n in kids(kid(net, "nets"), "net"):
        name = str(kid(n, "name")[1])
        item = pcbnew.NETINFO_ITEM(board, name)
        board.Add(item)
        net_id[name] = len(net_id) + 1
        net_item[name] = item
        for node in kids(n, "node"):
            pin_net[(str(kid(node, "ref")[1]), str(kid(node, "pin")[1]))] = name

    missing = []
    for comp in kids(kid(net, "components"), "comp"):
        ref = str(kid(comp, "ref")[1])
        lib, name = str(kid(comp, "footprint")[1]).split(":")
        fp = pcbnew.FootprintLoad(os.path.join(FP_ROOT, lib + ".pretty"), name)
        if fp is None:
            raise SystemExit("footprint not found: %s:%s" % (lib, name))
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(str(kid(comp, "value")[1]))
        # Link to the schematic symbol so "Update PCB from Schematic" recognises the part
        fp.SetPath(pcbnew.KIID_PATH("/" + str(kid(comp, "tstamps")[1])))
        for key, kind in (("description", pcbnew.FIELD_T_DESCRIPTION), ("datasheet", pcbnew.FIELD_T_DATASHEET)):
            node = kid(comp, key)
            field = fp.GetField(kind)
            if node is not None and field is not None:
                field.SetText(str(node[1]))
        # Copy the symbol's simulation fields (hidden), or the board-against-schematic check reports them missing
        for fld in kids(kid(comp, "fields") or [], "field"):
            fname = str(kid(fld, "name")[1])
            if fname.startswith("Sim."):
                fp.SetField(fname, str(fld[-1]))
                for f in fp.GetFields():
                    if f.GetName() == fname:
                        f.SetVisible(False)
                        f.SetLayer(pcbnew.F_Fab)
        board.Add(fp)
        if ref not in PLACE:
            missing.append(ref)
            continue
        x, y, rot = PLACE[ref]
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            if ref == "D1":
                # Vishay BPW34 leads are flat, 0.7 to 0.8 mm wide by 0.3 mm: too wide for the library's 0.7 mm hole
                pad.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.0), pcbnew.FromMM(1.0)))
                pad.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.8), pcbnew.FromMM(1.8)))
            name = pin_net.get((ref, pad.GetNumber()))
            if name is not None:
                pad.SetNet(net_item[name])
    if missing:
        raise SystemExit("no position for: " + ", ".join(missing))

    for k, (x, y) in enumerate(HOLES):
        fp = pcbnew.FootprintLoad(os.path.join(FP_ROOT, "MountingHole.pretty"), "MountingHole_3.2mm_M3")
        fp.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_3.2mm_M3"))
        fp.SetReference("H%d" % (k + 1))
        fp.SetAttributes(pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        board.Add(fp)
        fp.SetPosition(pt(x, y))

    corners = [(0, 0), (W, 0), (W, H), (0, H)]
    for (x1, y1), (x2, y2) in zip(corners, corners[1:] + corners[:1]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetStart(pt(x1, y1))
        seg.SetEnd(pt(x2, y2))
        seg.SetWidth(mm(0.1))
        board.Add(seg)

    label = pcbnew.PCB_TEXT(board)
    label.SetText("Lock-in amplifier  rev 0.1  2026-10")
    label.SetLayer(pcbnew.F_SilkS)
    label.SetPosition(pt(45, 57))
    label.SetTextSize(pcbnew.VECTOR2I(mm(1.2), mm(1.2)))
    label.SetTextThickness(mm(0.18))
    board.Add(label)

    # Pin names beside the connectors and the photodiode cathode, right-aligned
    for text, x, y in (("+9V", 84.3, 47), ("GND", 84.3, 49.54), ("A", 84.3, 38), ("K", 84.3, 40.54),
                       ("OUT", 84.3, 12), ("VREF", 84.3, 14.54), ("GND", 84.3, 17.08), ("K", 8.9, 18.4)):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetPosition(pt(x, y))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT)
        t.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        t.SetTextThickness(mm(0.13))
        board.Add(t)

    # ---- routing ----
    r = Router(board)
    pads_by_net = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            x1 = pcbnew.ToMM(bb.GetX()) - OX
            y1 = pcbnew.ToMM(bb.GetY()) - OY
            x2, y2 = x1 + pcbnew.ToMM(bb.GetWidth()), y1 + pcbnew.ToMM(bb.GetHeight())
            pos = pad.GetPosition()
            through = pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            name = pad.GetNetname()
            nid = net_id.get(name, -1)
            p = {"x": pcbnew.ToMM(pos.x) - OX, "y": pcbnew.ToMM(pos.y) - OY, "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                 "layers": (F, B) if through else (F,), "ref": fp.GetReference() + "." + pad.GetNumber()}
            infl = PAD_INFL + (0.3 if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else 0)
            r.claim_rect(p["layers"], x1 - infl, y1 - infl, x2 + infl, y2 + infl, nid)
            if True:    # no vias on or right beside any pad
                for iy in range(int(-(-(y1 - 0.45) // G)), int((y2 + 0.45) // G) + 1):
                    for ix in range(int(-(-(x1 - 0.45) // G)), int((x2 + 0.45) // G) + 1):
                        if 0 <= ix < NX and 0 <= iy < NY:
                            r.novia[iy * NX + ix] = True
            if nid > 0:
                pads_by_net.setdefault(name, []).append(p)

    def states(pad, cell):
        return [l * N + cell[1] * NX + cell[0] for l in pad["layers"]]

    def stub(pad, cell, layer, item):
        r.add_track(layer, (pad["x"], pad["y"]), (cell[0] * G, cell[1] * G), item)

    def connect_ends(path, seeds, item):
        for s in (path[0], path[-1]):
            if s in seeds:
                pad, cell = seeds[s]
                stub(pad, cell, s // N, item)

    # Ground: through-hole pads reach the plane directly; each surface-mount pad gets a via.
    gnd = "GND"
    nid, item = net_id[gnd], net_item[gnd]
    tree, seeds = set(), {}
    smd = []
    for p in pads_by_net.pop(gnd):
        cell = r.seed(p, nid)
        for s in states(p, cell):
            seeds[s] = (p, cell)
        if len(p["layers"]) == 2:
            tree.update(states(p, cell))
        else:
            smd.append((p, cell))
    for p, cell in smd:
        src = set(states(p, cell))

        def hit(s, nid=nid, tree=tree):
            if s in tree:
                return True
            iy, ix = divmod(s % N, NX)
            return s < N and r.via_ok(ix, iy, nid)
        path = r.search(src, hit, nid, tree, top_only=True)
        if path is None:
            r.failed.append("GND " + p["ref"])
            continue
        end = path[-1]
        new_via = end not in tree
        r.lay(path, item, nid, tree)
        connect_ends(path, seeds, item)
        if new_via:
            iy, ix = divmod(end % N, NX)
            r.add_via(ix, iy, item, nid)
            tree.add(N + end % N)

    # Signals and supplies: shortest nets first; within a net, grow a tree pad by pad.
    def span(name):
        ps = pads_by_net[name]
        return (max(p["x"] for p in ps) - min(p["x"] for p in ps)) + (max(p["y"] for p in ps) - min(p["y"] for p in ps))

    order = sorted((n for n in pads_by_net if len(pads_by_net[n]) > 1),
                   key=lambda n: (priority.index(n) if n in priority else len(priority), span(n)))
    failed_nets = []
    for name in order:
        nid, item = net_id[name], net_item[name]
        seeds, todo = {}, {}
        for p in pads_by_net[name]:
            cell = r.seed(p, nid)
            if cell is None:
                r.failed.append("%s %s (pad boxed in)" % (name, p["ref"]))
                continue
            for s in states(p, cell):
                seeds[s] = (p, cell)
                todo[s] = p["ref"]
        first = next(iter(todo.values()))
        tree = {s for s, ref in todo.items() if ref == first}
        todo = {s: ref for s, ref in todo.items() if ref != first}
        while todo:
            path = r.search(set(tree), lambda s: s in todo, nid, tree)
            if path is None:
                r.failed.append("%s: %s" % (name, ", ".join(sorted(set(todo.values())))))
                failed_nets.append(name)
                break
            ref = todo[path[-1]]
            r.lay(path, item, nid, tree)
            connect_ends(path, seeds, item)
            for s in [s for s, v in todo.items() if v == ref]:
                tree.add(s)
                del todo[s]

    r.emit_tracks()

    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.B_Cu)
    zone.SetNet(net_item[gnd])
    outline = zone.Outline()
    outline.NewOutline()
    for x, y in corners:
        outline.Append(mm(OX + x), mm(OY + y))
    board.Add(zone)
    # The zone is filled afterwards by: kicad-cli pcb drc --refill-zones --save-board

    pcbnew.SaveBoard(OUT, board)
    print("wrote", OUT)
    print("footprints %d, track %.0f mm, vias %d" % (len(board.GetFootprints()), r.length, r.vias))
    print("not routed:", r.failed if r.failed else "none")
    return failed_nets, bool(r.failed)


def main():
    # A net that gets boxed in is routed first on the next attempt.
    priority = []
    for attempt in range(8):
        failed_nets, any_failed = build(priority)
        if not failed_nets:
            break
        priority = failed_nets + [n for n in priority if n not in failed_nets]
        print("retrying with first:", priority)
    if any_failed:
        raise SystemExit("routing incomplete")


if __name__ == "__main__":
    main()
