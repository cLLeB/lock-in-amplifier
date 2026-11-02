# Builds the STL files for the lock-in amplifier case without OpenSCAD.
# Same geometry and the same numbers as lockin-case.scad (keep the two in step).
#
# Needs: numpy, trimesh, manifold3d, matplotlib (for the label font and the render).
#   python -m venv venv
#   venv/Scripts/python -m pip install numpy trimesh manifold3d matplotlib
#   venv/Scripts/python make_case_stl.py
#
# Writes, next to this file:
#   lockin-base.stl        floor down
#   lockin-lid.stl         outer face down (already turned over for printing)
#   lockin-led-holder.stl  flange down
#   lockin-case-render.png assembled view, exploded view and the print layout
# Each part is checked for being watertight, and its size is printed.

import os
import numpy as np
import trimesh
from manifold3d import Manifold, CrossSection, FillRule
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

HERE = os.path.dirname(os.path.abspath(__file__))
FN = 48

# ---- from the board file ----
board_l, board_w, board_t = 90.0, 60.0, 1.6
holes = [(4, 4), (86, 4), (4, 56), (86, 56)]
d1_x, d1_y = 8.0, 13.51
j2_x = 86.0
j2_y = [12.05, 14.59, 17.13]
j2_name = ["OUT", "VREF", "GND"]
j1_y = 48.32

# ---- estimates: measure on the assembled board ----
top_h = 15.0   # measured 2026-10-28: tallest part 13 mm, plus 2 mm room
under_h = 5.0
d1_h = 1.5
led_gap = 3.0
led_d = 5.0
led_rim = 5.8
led_len = 7.6
bat = (26.5, 48.5, 17.5)
pin_top = 8.5   # J2 header pin tips above the board (2.5 mm plastic + 6 mm pin)

# ---- printing choices ----
wall = 2.0
lid_t = 2.0
gap = 0.4
lip = 3.0
lip_w = 1.2
fit = 0.15
div_t = 1.6
div_h = 10.0
bay_l = bat[0] + 1
pin_d = 2.9
pin_up = 2.5
so_d = 6.5
tube_d = 6.0
tube_bore = 3.4
win = 8.0
wire_hole = 6.2
wire_x = 18.2
j2_win = (6.0, 9.0)   # window over J2 (x, y): no posts, no soldering
txt_h = 2.2
txt_d = 0.6
flange_d = 13.0
flange_t = 1.6
holder_d = 7.6
rim_bore = 6.1
led_bore = 5.2

in_l = gap + board_l + gap + div_t + bay_l
in_w = gap + board_w + gap
in_h = under_h + board_t + top_h
out_l = in_l + 2 * wall
out_w = in_w + 2 * wall
out_h = wall + in_h


def cx(x): return wall + gap + x
def cy(y): return wall + gap + (board_w - y)


board_top = wall + under_h + board_t
div_x = wall + gap + board_l + gap


# ---- small OpenSCAD-like helpers ----
def cube(size, at=(0, 0, 0)):
    return Manifold.cube(tuple(float(s) for s in size)).translate(tuple(float(a) for a in at))


def cyl(d, h, at=(0, 0, 0), fn=FN):
    return Manifold.cylinder(float(h), d / 2.0, d / 2.0, fn).translate(tuple(float(a) for a in at))


def _fold(parts, op):
    out = parts[0]
    for p in parts[1:]:
        out = op(out, p)
    return out


def text_solid(s, size, depth, right_x, centre_y, z0):
    """Bold text, right-aligned at right_x and centred on centre_y (like halign=right, valign=center)."""
    fp = FontProperties(family="DejaVu Sans", weight="bold")
    # Both matplotlib and OpenSCAD give capitals about 0.72 x size tall, so the size is used as is.
    tp = TextPath((0, 0), s, size=size, prop=fp)
    polys = [np.asarray(p, dtype=float) for p in tp.to_polygons(closed_only=True) if len(p) >= 3]
    cs = CrossSection(polys, FillRule.EvenOdd)
    x0, y0, x1, y1 = cs.bounds()
    cs = cs.translate((right_x - x1, centre_y - (y0 + y1) / 2))
    return cs.extrude(depth).translate((0, 0, z0))


# ---- parts ----
def base():
    shell = cube((out_l, out_w, out_h)) - cube((in_l, in_w, out_h), (wall, wall, wall))
    parts = [shell]
    for hx, hy in holes:
        parts.append(cyl(so_d, under_h + 0.01, (cx(hx), cy(hy), wall - 0.01)))
        parts.append(cyl(pin_d, under_h + board_t + pin_up, (cx(hx), cy(hy), wall - 0.01), fn=32))
    parts.append(cube((div_t, in_w + 0.02, div_h), (div_x, wall - 0.01, wall - 0.01)))
    b = _fold(parts, lambda a, c: a + c)
    b = b - cube((div_t + 2, 6, div_h), (div_x - 1, cy(j1_y) - 3, wall + under_h + 2))
    b = b - cube((12, wall + 2, 2), (out_l / 2 - 6, -1, out_h - 1.5))
    return b


def lid():
    """As it sits on the base, underside at z = 0."""
    parts = [cube((out_l, out_w, lid_t))]
    ring = cube((in_l - 2 * fit, in_w - 2 * fit, lip + 0.01)) - cube(
        (in_l - 2 * fit - 2 * lip_w, in_w - 2 * fit - 2 * lip_w, lip + 2), (lip_w, lip_w, -1))
    parts.append(ring.translate((wall + fit, wall + fit, -lip)))
    for hx, hy in holes:
        parts.append(cyl(tube_d, top_h + 0.01, (cx(hx), cy(hy), -top_h)))
    rib_h = in_h - bat[2] - 0.5
    for dx in (bay_l / 3, 2 * bay_l / 3):
        parts.append(cube((1.2, 30, rib_h + 0.01), (div_x + div_t + dx - 0.6, out_w / 2 - 15, -rib_h)))
    L = _fold(parts, lambda a, c: a + c)
    cuts = []
    for hx, hy in holes:
        cuts.append(cyl(tube_bore, pin_up + 1.5, (cx(hx), cy(hy), -top_h - 1), fn=32))
    cuts.append(cube((win, win, lid_t + 2), (cx(d1_x) - win / 2, cy(d1_y) - win / 2, -1)))
    cuts.append(cyl(wire_hole, lid_t + 2, (cx(wire_x), cy(d1_y), -1)))
    # one window over J2's three header pins: the meter probes go in and touch the pin tips
    cuts.append(cube((j2_win[0], j2_win[1], lid_t + 2),
                     (cx(j2_x) - j2_win[0] / 2, cy(j2_y[1]) - j2_win[1] / 2, -1)))
    for y, name in zip(j2_y, j2_name):
        cuts.append(text_solid(name, txt_h, txt_d + 1, cx(j2_x) - j2_win[0] / 2 - 1.0, cy(y), lid_t - txt_d))
    for c in cuts:
        L = L - c
    return L


def led_holder():
    """As it sits in the lid, flange underside at z = 0."""
    tip = board_top + d1_h + led_gap
    lidz = out_h + lid_t
    down = lidz - tip
    step = led_len - down
    h = cyl(flange_d, flange_t) + cyl(holder_d, down + 0.01, (0, 0, -down))
    h = h - cyl(led_bore, led_len + 1.01, (0, 0, -down - 1))
    h = h - cyl(rim_bore, flange_t - step + 1, (0, 0, step))
    return h, tip, down


def flip_x(m):
    """rotate([180, 0, 0]): y -> -y, z -> -z."""
    return m.rotate((180.0, 0.0, 0.0))


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3],
                           faces=np.asarray(mesh.tri_verts), process=True)


def main():
    b = base()
    l_asm = lid()
    h_asm, tip, down = led_holder()

    # print orientations, each sitting on z = 0
    l_print = flip_x(l_asm).translate((0, out_w, lid_t))
    h_print = flip_x(h_asm).translate((0, 0, flange_t))

    results = {}
    for name, m in (("lockin-base.stl", b), ("lockin-lid.stl", l_print), ("lockin-led-holder.stl", h_print)):
        t = to_trimesh(m)
        t.export(os.path.join(HERE, name))
        ext = t.bounds[1] - t.bounds[0]
        results[name] = t
        print(f"{name:24s} watertight={t.is_watertight}  volume={t.volume / 1000:.1f} cm3  "
              f"size={ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm  zmin={t.bounds[0][2]:.2f}  tris={len(t.faces)}")

    print(f"case outside {out_l:.1f} x {out_w:.1f} x {out_h + lid_t:.1f} mm (base {out_h:.1f} + lid {lid_t:.1f})")
    print(f"LED tip at {tip - board_top:.2f} mm above the board, {led_gap:.1f} mm above D1; holder tube {down:.1f} mm below the lid top")
    print(f"J2 pin tips {top_h + lid_t - pin_top:.1f} mm below the lid top: probes reach them through the window")

    # sanity checks between parts (assembled)
    l_on = l_asm.translate((0, 0, out_h))
    h_on = h_asm.translate((cx(d1_x), cy(d1_y), out_h + lid_t))
    print("overlap base/lid  (mm3):", round((b ^ l_on).volume(), 3))
    print("overlap lid/holder(mm3):", round((l_on ^ h_on).volume(), 3))
    print("overlap base/holder(mm3):", round((b ^ h_on).volume(), 3))

    render(b, l_on, h_on, results)


def render(b, l_on, h_on, results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    # dummies for context (not printed): board and battery
    board = cube((board_l, board_w, board_t), (cx(0), cy(board_w), wall + under_h))
    for hx, hy in holes:
        board = board - cyl(3.2, 5, (cx(hx), cy(hy), wall + under_h - 1))
    battery = cube(bat, (div_x + div_t + 0.5, wall + 1, wall))

    def draw(ax, items, title, elev=28, azim=-60):
        allv = []
        for m, col, alpha in items:
            t = to_trimesh(m)
            # split long thin triangles so matplotlib's per-face depth sorting draws them in order
            v_, f_ = trimesh.remesh.subdivide_to_size(t.vertices, t.faces, max_edge=4.0)
            t = trimesh.Trimesh(v_, f_, process=False)
            tris = t.vertices[t.faces]
            n = t.face_normals
            shade = 0.45 + 0.55 * np.clip(n @ np.array([0.3, -0.5, 0.8]) / np.linalg.norm([0.3, -0.5, 0.8]), 0, 1)
            rgb = np.array(matplotlib.colors.to_rgb(col))
            fc = np.clip(rgb[None, :] * shade[:, None], 0, 1)
            pc = Poly3DCollection(tris, facecolors=np.c_[fc, np.full(len(fc), alpha)], edgecolors="none")
            ax.add_collection3d(pc)
            allv.append(t.vertices)
        v = np.vstack(allv)
        lo, hi = v.min(0), v.max(0)
        c = (lo + hi) / 2
        r = (hi - lo).max() / 2
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        ax.set_title(title, fontsize=11)

    fig = plt.figure(figsize=(16, 11))
    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    draw(ax1, [(b, "#4a78b5", 1), (l_on, "#d9d9d9", 0.35), (h_on, "#e07b39", 1)],
         "Assembled (lid see-through)")
    ax2 = fig.add_subplot(2, 2, 2, projection="3d")
    lift = 30
    draw(ax2, [(b, "#4a78b5", 1), (board.translate((0, 0, lift)), "#2e8b57", 1),
               (battery.translate((0, 0, lift)), "#555555", 1),
               (l_on.translate((0, 0, 2 * lift)), "#d9d9d9", 1), (h_on.translate((0, 0, 3 * lift)), "#e07b39", 1)],
         "Exploded: base, board + battery (dummies), lid, LED holder")
    # lid top as a 2D section just inside the engraving: shows the window, holes and labels
    ax3 = fig.add_subplot(2, 2, 3)
    sec = lid().slice(lid_t - txt_d / 2)
    for poly in sec.to_polygons():
        q = np.vstack([poly, poly[:1]])
        ax3.fill(q[:, 0], q[:, 1], color="#d9d9d9", edgecolor="#333333", linewidth=0.6)
    hx, hy = cx(d1_x), cy(d1_y)
    ax3.add_patch(matplotlib.patches.Circle((hx, hy), flange_d / 2, fill=False, ls="--", color="#e07b39"))
    ax3.text(hx, hy + flange_d / 2 + 1.5, "LED holder flange", ha="center", fontsize=8, color="#e07b39")
    ax3.set_aspect("equal"); ax3.set_axis_off()
    ax3.set_title("Lid seen from above (section 0.3 mm below the top): window, wire hole, J2 window and labels",
                  fontsize=10)
    ax4 = fig.add_subplot(2, 2, 4, projection="3d")
    lay = [(b, "#4a78b5", 1),
           (flip_x(lid()).translate((0, 2 * out_w + 8, lid_t)), "#d9d9d9", 1),
           (flip_x(led_holder()[0]).translate((out_l + 15, out_w / 2, flange_t)), "#e07b39", 1)]
    draw(ax4, lay, "Print layout (as in the .scad): base, lid face down, holder flange down", elev=35, azim=-70)
    fig.tight_layout()
    out = os.path.join(HERE, "lockin-case-render.png")
    fig.savefig(out, dpi=110)
    print("render:", out)


if __name__ == "__main__":
    main()
