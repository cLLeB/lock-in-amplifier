# Builds 3d-view.html: both projects in 3D, each board (with every part, from KiCad) inside its printed case.
# Open the page in a browser: drag to turn, scroll to zoom, the slider lifts the lid off.
#
# Needs: numpy, trimesh, manifold3d, matplotlib, and KiCad 10 (kicad-cli) for the boards.
#   venv/Scripts/python make_3d_view.py
# The cases come from the two case generators (case/make_case_stl.py, smart-socket/case/make_case_stl.py),
# so the view always shows the case as it is printed.

import base64
import shutil
import importlib.util
import os
import subprocess
import tempfile

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KICAD = os.path.join(os.environ["LOCALAPPDATA"], "Programs", "KiCad", "10.0", "bin", "kicad-cli.exe")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def board_mesh(pcb, tmp, origin_case, board_w):
    """The board and its parts as one coloured mesh, in case millimetres (z up)."""
    glb = os.path.join(tmp, os.path.basename(pcb) + ".glb")
    subprocess.run([KICAD, "pcb", "export", "glb", "-f", "--user-origin", "100x80mm", "--include-pads",
                    "--include-silkscreen", "--include-soldermask", "--subst-models", "-o", glb, pcb],
                   check=True, capture_output=True)
    sc = trimesh.load(glb)
    x0, y0, z0 = origin_case
    # glTF: metres, x = board x, y = up from the board's underside, z = board y (down the drawing).
    # Case: x the same, y = board_w - board y (towards the back), z up.
    m = np.array([[1000, 0, 0, x0],
                  [0, 0, -1000, y0 + board_w],
                  [0, 1000, 0, z0],
                  [0, 0, 0, 1]], dtype=float)
    parts = []
    for node in sc.graph.nodes_geometry:
        tf, gname = sc.graph[node]
        g = sc.geometry[gname].copy()
        g.apply_transform(m @ tf)
        col = [120, 120, 120, 255]
        try:
            col = list(g.visual.material.main_color[:3]) + [255]   # KiCad gives each part its material colour
        except Exception:
            pass
        parts.append(vertex_coloured(g, col))
    return trimesh.util.concatenate(parts)


def vertex_coloured(t, color=None):
    """Colours per vertex (the glTF export would otherwise need scipy to convert face colours)."""
    if color is not None:
        t.visual = trimesh.visual.ColorVisuals(t, vertex_colors=np.tile(np.asarray(color, np.uint8), (len(t.vertices), 1)))
        return t
    if getattr(t.visual, "kind", None) == "face":
        fc = np.asarray(t.visual.face_colors)
        t = trimesh.Trimesh(t.vertices[t.faces].reshape(-1, 3), np.arange(len(t.faces) * 3).reshape(-1, 3), process=False)
        t.visual = trimesh.visual.ColorVisuals(t, vertex_colors=np.repeat(fc, 3, axis=0))
    elif getattr(t.visual, "kind", None) != "vertex":
        t = vertex_coloured(t, [120, 120, 120, 255])
    return t


def man(m, color):
    """manifold3d solid -> coloured trimesh."""
    mesh = m.to_mesh()
    t = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)
    return vertex_coloured(t, color)


def box(size, at, color):
    t = trimesh.creation.box(extents=size)
    t.apply_translation(np.asarray(at, float) + np.asarray(size, float) / 2)
    return vertex_coloured(t, color)


def cylz(d, h, at, color):
    t = trimesh.creation.cylinder(radius=d / 2, height=h, sections=40)
    t.apply_translation(np.asarray(at, float) + [0, 0, h / 2])
    return vertex_coloured(t, color)


def cylx(d, h, at, color):
    t = trimesh.creation.cylinder(radius=d / 2, height=h, sections=32)
    t.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    t.apply_translation(np.asarray(at, float) + [h / 2, 0, 0])
    return vertex_coloured(t, color)


CASE = [74, 110, 160, 255]
LID = [215, 220, 228, 255]
BLUE = [40, 70, 160, 255]
BLACK = [30, 30, 32, 255]
METAL = [180, 182, 188, 255]
WHITE = [242, 242, 242, 255]
RED = [220, 40, 40, 255]


def socket_scene(tmp):
    c = load_module(os.path.join(ROOT, "smart-socket", "case", "make_case_stl.py"), "socket_case")
    base, lid = man(c.base(), CASE), man(c.lid().translate((0, 0, c.out_h)), LID)
    board = board_mesh(os.path.join(ROOT, "smart-socket", "kicad", "smartsocket.kicad_pcb"), tmp,
                       (c.cx(0), c.wall + c.gap, c.cz(-c.board_t)), c.board_w)
    p = lambda x, y, z: (c.cx(x), c.cy(y), c.cz(z))   # board point (board y from the back edge) -> case
    extra = []
    # The two modules, which KiCad shows only as their header pins. (x, y ranges in board mm.)
    def module(x0, x1, y0, y1, z0, t, col):
        a, b = p(x0, y1, z0), p(x1, y0, z0)
        extra.append(box((b[0] - a[0], b[1] - a[1], t), a, col))
    module(0.0, 13.97, 1.84, 22.16, 2.4, 1.6, BLUE)                         # J1, USB-C socket board
    a = p(-0.6, 12 + 4.5, 4.0); extra.append(box((7.5, 9.0, 3.2), a, METAL))  # its socket
    module(14.52, 32.32, 0.75, 21.75, 2.5, 1.0, BLUE)                       # U1, XIAO ESP32-C3
    a = p(17.4, 13.0, 3.5); extra.append(box((12.0, 10.0, 2.4), a, METAL))  # its shield can
    a = p(23.42 - 4.5, 22.95, 3.5); extra.append(box((9.0, 7.3, 3.2), a, METAL))   # its USB-C port
    # the phone cable, leaving through the slot
    extra.append(cylx(c.cable_d, 30, (c.cx(c.board_l) + 1.5, c.cab_y, c.cab_z), WHITE))
    # the antenna, stuck under the lid
    a = (c.cx(6), c.cy(17), c.out_h - 0.25); extra.append(box((26, 10, 0.2), a, BLACK))
    return base, board, lid, trimesh.util.concatenate(extra)


def lockin_scene(tmp):
    c = load_module(os.path.join(ROOT, "case", "make_case_stl.py"), "lockin_case")
    base = man(c.base(), CASE)
    lid = man(c.lid().translate((0, 0, c.out_h)), LID)
    h, tip, down = c.led_holder()
    holder = man(h.translate((c.cx(c.d1_x), c.cy(c.d1_y), c.out_h + c.lid_t)), [224, 123, 57, 255])
    board = board_mesh(os.path.join(ROOT, "kicad", "lockin.kicad_pcb"), tmp,
                       (c.wall + c.gap, c.wall + c.gap, c.wall + c.under_h), c.board_w)
    lid = trimesh.util.concatenate([lid, holder])   # the holder sits in the lid and comes off with it
    extra = []
    # 9 V battery in its bay
    extra.append(box(c.bat, (c.div_x + c.div_t + 0.5, c.wall + 1, c.wall), [60, 60, 64, 255]))
    # the photodiode D1 (no KiCad model) and the LED in its holder, tip led_gap above it
    extra.append(box((4.3, 4.65, c.d1_h), (c.cx(c.d1_x) - 2.15, c.cy(c.d1_y) - 2.3, c.board_top), BLACK))
    extra.append(cylz(c.led_d, c.led_len - 1.0, (c.cx(c.d1_x), c.cy(c.d1_y), tip), RED))
    return base, board, lid, trimesh.util.concatenate(extra)


def glb_b64(base, board, lid, extra):
    s = trimesh.Scene()
    s.add_geometry(base, node_name="base", geom_name="base")
    s.add_geometry(board, node_name="board", geom_name="board")
    s.add_geometry(extra, node_name="extra", geom_name="extra")
    s.add_geometry(lid, node_name="lid", geom_name="lid")
    return base64.b64encode(s.export(file_type="glb")).decode()


def main():
    with tempfile.TemporaryDirectory() as tmp:
        sock = glb_b64(*socket_scene(tmp))
        lock = glb_b64(*lockin_scene(tmp))
    page = open(os.path.join(HERE, "viewer.template.html"), encoding="utf8").read()

    def write(path, socket_data, lockin_data, only):
        html = page.replace("%%SOCKET%%", socket_data).replace("%%LOCKIN%%", lockin_data).replace("%%ONLY%%", only)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf8").write(html)
        print("wrote", path, round(len(html) / 1e6, 1), "MB")

    write(os.path.join(HERE, "3d-view.html"), sock, lock, "")
    # The print folder: one subfolder per project with its STL files and its own 3D page.
    prints = os.path.join(ROOT, "3D-prints")
    sdir, ldir = os.path.join(prints, "Smart socket"), os.path.join(prints, "Lock-in amplifier")
    write(os.path.join(sdir, "Smart socket 3D view.html"), sock, "", "socket")
    write(os.path.join(ldir, "Lock-in amplifier 3D view.html"), "", lock, "lockin")
    for src, dst in ((os.path.join(ROOT, "smart-socket", "case"), sdir), (os.path.join(ROOT, "case"), ldir)):
        for f in sorted(os.listdir(src)):
            if f.endswith(".stl"):
                shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
                print("copied", f, "->", os.path.basename(dst))


if __name__ == "__main__":
    main()
