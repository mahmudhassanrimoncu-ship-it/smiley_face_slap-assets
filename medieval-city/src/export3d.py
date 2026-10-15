"""Writes the world as a ready-to-import 3D blockout (.glb, glTF 2.0).

glTF axes: +X = east, +Y = up, +Z = south. The model's origin is the map's
north-west corner at sea level, so a point at map (x, y) with elevation z sits
at glTF (x, z, y). Every building is its own node, pivot at the centre of its
floor, named "<ID> <name>", with all its catalogue data stored in `extras`
(Blender shows these as Custom Properties).
"""
import json
import math
import struct

import numpy as np

from geom import ellipse_pts, sample
from surface import LAYER_COLORS, LAYERS

MATERIALS = {
    # name: (rgb 0-255, alpha, roughness)
    "Stone wall": ((176, 170, 158), 1, 0.9), "Plaster & timber": ((226, 214, 186), 1, 0.9),
    "Wattle & daub": ((190, 168, 128), 1, 1.0), "Wood": ((110, 78, 50), 1, 0.85),
    "Roof thatch": ((196, 164, 92), 1, 1.0), "Roof slate": ((74, 80, 92), 1, 0.7),
    "Roof clay tile": ((160, 80, 56), 1, 0.8), "Roof shingle": ((96, 70, 50), 1, 0.9),
    "Door": ((70, 44, 26), 1, 0.8), "Water": ((52, 104, 136), 0.82, 0.08),
    "Bark": ((88, 66, 46), 1, 1.0), "Bark (birch)": ((220, 216, 204), 1, 1.0),
    "Leaves (broadleaf)": ((64, 104, 48), 1, 0.9), "Leaves (pine)": ((40, 72, 48), 1, 0.9),
    "Leaves (birch)": ((122, 150, 64), 1, 0.9), "Leaves (willow)": ((112, 140, 74), 1, 0.9),
    "Leaves (fruit tree)": ((88, 130, 56), 1, 0.9), "Cloth (red)": ((170, 48, 40), 1, 1.0),
    "Cloth (blue)": ((48, 72, 150), 1, 1.0), "Cloth (cream)": ((230, 220, 190), 1, 1.0),
    "Hay": ((210, 180, 96), 1, 1.0), "Hedge": ((58, 96, 52), 1, 1.0), "Sarsen stone": ((150, 146, 132), 1, 0.95),
    "Bronze": ((120, 96, 60), 1, 0.4), "Leaves (yew)": ((34, 62, 40), 1, 0.9), "Leaves (lime)": ((96, 136, 60), 1, 0.9),
    "Gilded": ((214, 176, 80), 1, 0.35), "Iron": ((60, 60, 64), 1, 0.5), "Fire": ((255, 140, 40), 1, 0.6),
}
for k in LAYERS:
    MATERIALS[f"Terrain {k}"] = (LAYER_COLORS[k], 1, 1.0)


# ================================================================ mesh builder
class MB:
    """Flat-shaded triangle soup grouped by material; faces auto-oriented outward."""

    def __init__(self):
        self.parts = {}

    def tri(self, mat, a, b, c, ref=None):
        a, b, c = np.asarray(a, float), np.asarray(b, float), np.asarray(c, float)
        n = np.cross(b - a, c - a)
        ln = np.linalg.norm(n)
        if ln < 1e-9:
            return
        n /= ln
        if ref is not None and np.dot(n, (a + b + c) / 3 - np.asarray(ref, float)) < 0:
            b, c, n = c, b, -n
        p = self.parts.setdefault(mat, ([], []))
        p[0].extend([a, b, c])
        p[1].extend([n, n, n])

    def quad(self, mat, a, b, c, d, ref=None):
        self.tri(mat, a, b, c, ref)
        self.tri(mat, a, c, d, ref)

    def poly_prism(self, mat, pts, y0, y1, cap_top=True, cap_bottom=False):
        """Vertical extrusion of a convex XZ polygon."""
        cx = sum(p[0] for p in pts) / len(pts)
        cz = sum(p[1] for p in pts) / len(pts)
        ref = (cx, (y0 + y1) / 2, cz)
        n = len(pts)
        for i in range(n):
            (x0, z0), (x1, z1) = pts[i], pts[(i + 1) % n]
            self.quad(mat, (x0, y0, z0), (x1, y0, z1), (x1, y1, z1), (x0, y1, z0), ref)
        for y, on in ((y1, cap_top), (y0, cap_bottom)):
            if on:
                for i in range(1, n - 1):
                    self.tri(mat, (pts[0][0], y, pts[0][1]), (pts[i][0], y, pts[i][1]),
                             (pts[i + 1][0], y, pts[i + 1][1]), (cx, (y0 + y1) / 2, cz))

    def box(self, mat, x0, x1, y0, y1, z0, z1, bottom=False):
        self.poly_prism(mat, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, True, bottom)

    def obox(self, mat, cx, cz, length, width, yaw, y0, y1):
        """Box centred at (cx, cz), `length` along direction yaw (radians from +X toward +Z)."""
        ux, uz = math.cos(yaw), math.sin(yaw)
        vx, vz = -uz, ux
        hl, hw = length / 2, width / 2
        pts = [(cx - ux * hl - vx * hw, cz - uz * hl - vz * hw), (cx + ux * hl - vx * hw, cz + uz * hl - vz * hw),
               (cx + ux * hl + vx * hw, cz + uz * hl + vz * hw), (cx - ux * hl + vx * hw, cz - uz * hl + vz * hw)]
        self.poly_prism(mat, pts, y0, y1)

    def cyl(self, mat, cx, cz, r, y0, y1, n=10, top=True):
        pts = [(cx + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
        self.poly_prism(mat, pts, y0, y1, top)

    def cone(self, mat, cx, cz, r, y0, y1, n=10):
        apex = (cx, y1, cz)
        ref = (cx, y0 + (y1 - y0) * 0.25, cz)
        for i in range(n):
            t0, t1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            self.tri(mat, (cx + r * math.cos(t0), y0, cz + r * math.sin(t0)),
                     (cx + r * math.cos(t1), y0, cz + r * math.sin(t1)), apex, ref)

    def merlons(self, mat, pts, y, t, closed=True):
        if LITE:                                    # web preview: skip battlements to save bytes
            return
        seq = pts + [pts[0]] if closed else pts
        for (x0, z0), (x1, z1) in zip(seq, seq[1:]):
            L = math.hypot(x1 - x0, z1 - z0)
            yaw = math.atan2(z1 - z0, x1 - x0)
            for k in range(int(L / 1.8)):
                s = (k + 0.5) / int(L / 1.8)
                self.obox(mat, x0 + (x1 - x0) * s, z0 + (z1 - z0) * s, 0.9, t, yaw, y, y + 1.0)

    def slab(self, mat, pts, width, thickness):
        """A walkway/deck following 3D points (x, y, z) with the given width."""
        for (x0, y0, z0), (x1, y1, z1) in zip(pts, pts[1:]):
            yaw = math.atan2(z1 - z0, x1 - x0)
            vx, vz = -math.sin(yaw) * width / 2, math.cos(yaw) * width / 2
            a, b = (x0 - vx, y0, z0 - vz), (x1 - vx, y1, z1 - vz)
            c, d = (x1 + vx, y1, z1 + vz), (x0 + vx, y0, z0 + vz)
            mid = ((x0 + x1) / 2, (y0 + y1) / 2 - thickness / 2, (z0 + z1) / 2)
            self.quad(mat, a, b, c, d, mid)
            lo = lambda p: (p[0], p[1] - thickness, p[2])
            self.quad(mat, lo(a), lo(b), lo(c), lo(d), mid)
            self.quad(mat, a, b, lo(b), lo(a), mid)
            self.quad(mat, d, c, lo(c), lo(d), mid)

    def primitives(self):
        out = []
        for mat, (pos, nrm) in self.parts.items():
            pos = np.asarray(pos, np.float32)
            out.append((mat, pos, np.asarray(nrm, np.float32), np.arange(len(pos), dtype=np.uint32), None))
        return out


# ================================================================ glTF writer
def _lin(c):
    """glTF colour factors are linear; our palette is written in sRGB."""
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


class GLB:
    def __init__(self):
        self.bin = bytearray()
        self.views, self.accessors, self.meshes, self.nodes = [], [], [], []
        self.materials, self.mat_index = [], {}

    def material(self, name):
        if name not in self.mat_index:
            rgb, alpha, rough = MATERIALS[name]
            m = dict(name=name, pbrMetallicRoughness=dict(
                baseColorFactor=[round(_lin(c), 4) for c in rgb] + [alpha], metallicFactor=0.0,
                roughnessFactor=rough))
            if alpha < 1:
                m["alphaMode"] = "BLEND"
                m["doubleSided"] = True
            self.mat_index[name] = len(self.materials)
            self.materials.append(m)
        return self.mat_index[name]

    def _view(self, data, target):
        while len(self.bin) % 4:
            self.bin.append(0)
        self.views.append(dict(buffer=0, byteOffset=len(self.bin), byteLength=len(data), target=target))
        self.bin.extend(data)
        return len(self.views) - 1

    def _acc(self, arr, kind, target, minmax=False):
        ctype = 5125 if arr.dtype == np.uint32 else 5126
        v = self._view(arr.tobytes(), target)
        a = dict(bufferView=v, componentType=ctype, count=int(arr.shape[0]), type=kind)
        if minmax:
            a["min"] = [float(x) for x in arr.min(axis=0)]
            a["max"] = [float(x) for x in arr.max(axis=0)]
        self.accessors.append(a)
        return len(self.accessors) - 1

    def mesh(self, name, prims):
        out = []
        for mat, pos, nrm, idx, uv in prims:
            if len(pos) == 0:
                continue
            attrs = dict(POSITION=self._acc(pos.astype(np.float32), "VEC3", 34962, True),
                         NORMAL=self._acc(nrm.astype(np.float32), "VEC3", 34962))
            if uv is not None:
                attrs["TEXCOORD_0"] = self._acc(uv.astype(np.float32), "VEC2", 34962)
            out.append(dict(attributes=attrs, indices=self._acc(idx.astype(np.uint32), "SCALAR", 34963),
                            material=self.material(mat)))
        if not out:
            return None
        self.meshes.append(dict(name=name, primitives=out))
        return len(self.meshes) - 1

    def node(self, name, mesh=None, t=None, yaw=None, children=None, extras=None):
        n = dict(name=name)
        if mesh is not None:
            n["mesh"] = mesh
        if t is not None:
            n["translation"] = [round(float(v), 3) for v in t]
        if yaw:
            n["rotation"] = [0.0, math.sin(yaw / 2), 0.0, math.cos(yaw / 2)]
        if children:
            n["children"] = children
        if extras:
            n["extras"] = extras
        self.nodes.append(n)
        return len(self.nodes) - 1

    def write(self, path, roots, asset_extras=None):
        gl = dict(asset=dict(version="2.0", generator="Ashford Vale world builder"),
                  scene=0, scenes=[dict(name="World", nodes=roots)], nodes=self.nodes, meshes=self.meshes,
                  materials=self.materials, accessors=self.accessors, bufferViews=self.views,
                  buffers=[dict(byteLength=len(self.bin))])
        if asset_extras:
            gl["asset"]["extras"] = asset_extras
        if str(path).endswith((".gltf", ".json")):           # single-file glTF with the buffer inlined
            import base64
            gl["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(bytes(self.bin)).decode()
            with open(path, "w") as f:
                json.dump(gl, f, separators=(",", ":"))
            return
        js = json.dumps(gl, separators=(",", ":")).encode()
        js += b" " * ((4 - len(js) % 4) % 4)
        bn = bytes(self.bin) + b"\0" * ((4 - len(self.bin) % 4) % 4)
        with open(path, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bn)))
            f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
            f.write(struct.pack("<II", len(bn), 0x004E4942) + bn)


# ================================================================ world parts
def wall_mat(m):
    return {"stone": "Stone wall", "timber": "Plaster & timber", "wattle": "Wattle & daub", "wood": "Wood",
            "hedge": "Hedge"}[m]


def roof_mat(b):
    if b.get("thatch"):
        return "Roof thatch"
    if b["material"] == "stone":
        return "Roof slate"
    return "Roof clay tile" if b["district"] == "T" else "Roof shingle"


def building_mesh(b):
    m = MB()
    wm, rm = wall_mat(b["material"]), roof_mat(b)
    w, d = b["w"], b["d"]
    top = (b["ground_max"] - b["z"]) + b["h"]
    roof = b["roof"]
    if b["shape"] == "round":
        r = w / 2
        m.cyl(wm, 0, 0, r, 0, top, n=12)
        if roof == "cone":
            m.cone(rm, 0, 0, r * 1.15, top, top + b["roof_h"], n=12)
        elif roof == "crenel":
            ring = [(r * 0.86 * math.cos(2 * math.pi * i / 12), r * 0.86 * math.sin(2 * math.pi * i / 12)) for i in range(12)]
            m.merlons(wm, ring, top, 0.6)
        return m
    if b["type"] == "gatehouse":
        pw, ph = b["passage_w"], (b["ground_max"] - b["z"]) + b["passage_h"]
        m.box(wm, -w / 2, -pw / 2, 0, top, -d / 2, d / 2)
        m.box(wm, pw / 2, w / 2, 0, top, -d / 2, d / 2)
        m.box(wm, -pw / 2, pw / 2, ph, top, -d / 2, d / 2)
    elif b.get("open_ground_floor"):
        for sx in (-1, 1):
            for sz in (-1, 1):
                m.box("Wood", sx * w / 2 - 0.3 * sx - 0.3, sx * w / 2 - 0.3 * sx + 0.3, 0, 3.2,
                      sz * d / 2 - 0.3 * sz - 0.3, sz * d / 2 - 0.3 * sz + 0.3)
        m.box(wm, -w / 2, w / 2, 3.2, top, -d / 2, d / 2, bottom=True)
    elif b["type"] == "sheepfold":
        t = 0.6
        m.box(wm, -w / 2, w / 2, 0, top, -d / 2, -d / 2 + t)
        m.box(wm, -w / 2, w / 2, 0, top, d / 2 - t, d / 2)
        m.box(wm, -w / 2, -w / 2 + t, 0, top, -d / 2, d / 2)
        m.box(wm, w / 2 - t, w / 2, 0, top, -d / 2, -1.5)
        m.box(wm, w / 2 - t, w / 2, 0, top, 1.5, d / 2)
        return m
    else:
        m.box(wm, -w / 2, w / 2, 0, top, -d / 2, d / 2)
        if b["type"] not in ("stand", "watchtower", "keep"):
            if not LITE:
                m.box("Door", -0.65, 0.65, (b["ground_max"] - b["z"]), (b["ground_max"] - b["z"]) + 2.2,
                      -d / 2 - 0.12, -d / 2 + 0.05)
    if roof == "crenel":
        inset = 0.45
        m.merlons(wm, [(-w / 2 + inset, -d / 2 + inset), (w / 2 - inset, -d / 2 + inset),
                       (w / 2 - inset, d / 2 - inset), (-w / 2 + inset, d / 2 - inset)], top, 0.7)
    elif roof in ("gable", "hip"):
        o = 0.5
        rh = b["roof_h"]
        along_x = w >= d
        L, S = (w / 2 + o, d / 2 + o) if along_x else (d / 2 + o, w / 2 + o)
        hip = (L - S) if roof == "hip" else L
        hip = max(hip, 0.0)

        def P(u, y, v):  # u along ridge, v across
            return (u, y, v) if along_x else (v, y, u)

        ref = (0, top + rh * 0.2, 0)
        y0, y1 = top, top + rh
        m.quad(rm, P(-L, y0, -S), P(L, y0, -S), P(hip, y1, 0), P(-hip, y1, 0), ref)
        m.quad(rm, P(-L, y0, S), P(L, y0, S), P(hip, y1, 0), P(-hip, y1, 0), ref)
        endmat = rm if roof == "hip" else wm
        m.tri(endmat, P(-L, y0, -S), P(-L, y0, S), P(-hip, y1, 0), ref)
        m.tri(endmat, P(L, y0, -S), P(L, y0, S), P(hip, y1, 0), ref)
    elif roof == "spire":
        a, h1 = w / 2 + 0.2, top + b["roof_h"]
        ref = (0, top + 0.5, 0)
        c = [(-a, -a), (a, -a), (a, a), (-a, a)]
        for i in range(4):
            m.tri(rm, (c[i][0], top, c[i][1]), (c[(i + 1) % 4][0], top, c[(i + 1) % 4][1]), (0, h1, 0), ref)
    if b["type"] == "windmill":
        hub_y = top - 1.5
        for k in range(4):
            ang = math.pi / 4 + k * math.pi / 2
            cx, cy = math.cos(ang) * b["sails"] / 2, hub_y + math.sin(ang) * b["sails"] / 2
            pts = []
            ux, uy = math.cos(ang), math.sin(ang)
            for s, t in ((0.6, -0.9), (b["sails"], -0.9), (b["sails"], 0.9), (0.6, 0.9)):
                pts.append((ux * s - uy * t, hub_y + uy * s + ux * t))
            z = -d / 2 - 0.6
            m.quad("Cloth (cream)", (pts[0][0], pts[0][1], z), (pts[1][0], pts[1][1], z),
                   (pts[2][0], pts[2][1], z), (pts[3][0], pts[3][1], z), (0, hub_y, 0))
    return m


def prop_mesh(p):
    m = MB()
    t = p["type"]
    if t == "well":
        m.cyl("Stone wall", 0, 0, 1.3, -0.3, 0.9, 10)
        m.box("Wood", -1.2, -1.0, 0, 2.6, -0.1, 0.1)
        m.box("Wood", 1.0, 1.2, 0, 2.6, -0.1, 0.1)
        m.box("Roof shingle", -1.6, 1.6, 2.6, 2.8, -1.0, 1.0)
    elif t == "market_stall":
        m.box("Wood", -p["w"] / 2, p["w"] / 2, 0, 0.9, -p["d"] / 2, p["d"] / 2)
        cloth = ["Cloth (red)", "Cloth (blue)", "Cloth (cream)"][int(p["x"] * 7) % 3]
        m.quad(cloth, (-p["w"] / 2 - 0.2, 2.6, -p["d"] / 2 - 0.4), (p["w"] / 2 + 0.2, 2.6, -p["d"] / 2 - 0.4),
               (p["w"] / 2 + 0.2, 2.1, p["d"] / 2 + 0.2), (-p["w"] / 2 - 0.2, 2.1, p["d"] / 2 + 0.2), (0, 0, 0))
        for sx in (-1, 1):
            m.box("Wood", sx * p["w"] / 2 - 0.08, sx * p["w"] / 2 + 0.08, 0, 2.6, -p["d"] / 2 - 0.08, -p["d"] / 2 + 0.08)
    elif t == "market_cross":
        m.box("Stone wall", -1.5, 1.5, -0.3, 0.6, -1.5, 1.5)
        m.box("Stone wall", -0.25, 0.25, 0.6, 6, -0.25, 0.25)
        m.box("Stone wall", -1, 1, 4.6, 5.1, -0.2, 0.2)
    elif t == "gravestone":
        m.box("Stone wall", -0.35, 0.35, 0, 1.0, -0.1, 0.1)
    elif t == "stocks":
        m.box("Wood", -1, 1, 0, 0.8, -0.2, 0.2)
    elif t == "training_dummy":
        m.box("Wood", -0.1, 0.1, 0, 1.9, -0.1, 0.1)
        m.box("Wood", -0.7, 0.7, 1.4, 1.55, -0.08, 0.08)
    elif t in ("cart", "stone_block"):
        m.box("Wood" if t == "cart" else "Stone wall", -1.0, 1.0, 0, 1.0, -0.7, 0.7)
    elif t == "drawbridge":
        m.box("Wood", -p["w"] / 2, p["w"] / 2, -0.3, 0.2, -p["length"] / 2, p["length"] / 2)
    elif t == "beacon":
        m.cyl("Iron", 0, 0, 0.7, 0, 1.6, 8)
        m.cone("Fire", 0, 0, 0.6, 1.6, 2.6, 6)
    elif t in ("standing_stone", "menhir"):
        w, d, h = p.get("w", 1.1), p.get("d", 0.6), p["h"]
        lean = math.radians(p.get("lean", 0))
        top_w = 0.7 if t == "standing_stone" else 0.45
        sh = math.sin(lean) * h                                   # weathered stones lean a little
        bot = [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]
        top = [(x * top_w + sh, z * top_w) for x, z in bot]
        ref = (sh / 2, h / 2, 0)
        for i in range(4):
            a0, a1 = bot[i], bot[(i + 1) % 4]
            b0, b1 = top[i], top[(i + 1) % 4]
            m.quad("Sarsen stone", (a0[0], -0.8, a0[1]), (a1[0], -0.8, a1[1]), (b1[0], h, b1[1]), (b0[0], h, b0[1]), ref)
        apex = (sh, h + (0.4 if t == "standing_stone" else 1.2), 0)
        for i in range(4):
            b0, b1 = top[i], top[(i + 1) % 4]
            m.tri("Sarsen stone", (b0[0], h, b0[1]), (b1[0], h, b1[1]), apex, ref)
    elif t == "altar_stone":
        w, d, h = p.get("w", 2.4), p.get("d", 1.2), p.get("h", 1.1)
        m.box("Sarsen stone", -w / 2, w / 2, -0.3, h, -d / 2, d / 2)
    elif t == "dolmen":
        w, d, h = p["w"], p["d"], p["h"]
        for x, z in ((-w / 2 + 0.6, -d / 2 + 0.5), (w / 2 - 0.6, -d / 2 + 0.5), (0, d / 2 - 0.5)):
            m.box("Sarsen stone", x - 0.5, x + 0.5, -0.5, h, z - 0.4, z + 0.4)
        m.box("Sarsen stone", -w / 2, w / 2, h, h + 0.9, -d / 2, d / 2)
    elif t == "column":
        m.box("Stone wall", -4, 4, -0.5, 2.5, -4, 4)
        m.cyl("Stone wall", 0, 0, p["r"], 2.5, p["h"], 14)
        m.box("Stone wall", -p["r"] - 0.6, p["r"] + 0.6, p["h"], p["h"] + 1.2, -p["r"] - 0.6, p["r"] + 0.6)
        m.cyl("Gilded", 0, 0, 0.7, p["h"] + 1.2, p["h"] + 4.6, 8)
        m.cone("Gilded", 0, 0, 0.8, p["h"] + 4.6, p["h"] + 5.6, 8)
    elif t == "statue":
        m.box("Stone wall", -1.6, 1.6, -0.3, 2.4, -1.6, 1.6)
        m.cyl("Bronze", 0, 0, 0.6, 2.4, 2.4 + p["h"] * 0.7, 8)
        m.cone("Bronze", 0, 0, 0.5, 2.4 + p["h"] * 0.7, 2.4 + p["h"], 8)
    elif t == "fountain":
        r = p["r"]
        ring = [(r * math.cos(2 * math.pi * i / 16), r * math.sin(2 * math.pi * i / 16)) for i in range(16)]
        for i in range(16):
            (x0, z0), (x1, z1) = ring[i], ring[(i + 1) % 16]
            m.obox("Stone wall", (x0 + x1) / 2, (z0 + z1) / 2, math.hypot(x1 - x0, z1 - z0) + 0.2, 0.5,
                   math.atan2(z1 - z0, x1 - x0), -0.3, 0.8)
        m.cyl("Water", 0, 0, r - 0.3, -0.3, 0.55, 16)
        m.cyl("Stone wall", 0, 0, 0.5, 0, 3.0, 8)
        m.cyl("Stone wall", 0, 0, 1.4, 3.0, 3.3, 10)
    elif t == "sundial":
        m.cyl("Stone wall", 0, 0, 0.5, 0, 1.1, 8)
        m.box("Bronze", -0.05, 0.05, 1.1, 1.5, -0.4, 0.4)
    elif t == "ship":
        L, w = p["length"], p["w"]
        top = p["top"] - p["z"] if "top" in p else 0
        m.poly_prism("Wood", [(-L / 2, 0), (-L / 2 + 2, -w / 2), (L / 2 - 4, -w / 2), (L / 2, 0), (L / 2 - 4, w / 2),
                              (-L / 2 + 2, w / 2)], top - 1.2, top + 1.8)
        m.box("Wood", -L / 2 + 0.5, -L / 2 + 5, top + 1.8, top + 4.2, -w / 2 + 0.5, w / 2 - 0.5)
        m.cyl("Wood", 1, 0, 0.3, top + 1.8, top + 18, 6)
        m.box("Cloth (cream)", 0.7, 1.0, top + 6, top + 16, -w * 0.9, w * 0.9)
    elif t == "pen":
        w, d = p["w"], p["d"]
        for x0, x1, z0, z1 in ((-w / 2, w / 2, -d / 2, -d / 2 + 0.15), (-w / 2, w / 2, d / 2 - 0.15, d / 2),
                               (-w / 2, -w / 2 + 0.15, -d / 2, d / 2), (w / 2 - 0.15, w / 2, -d / 2, d / 2 - 2)):
            m.box("Wood", x0, x1, 0, 1.1, z0, z1)
    elif t == "stepping_stones":
        for k in range(9):
            z = -p["length"] / 2 + k * p["length"] / 8
            m.cyl("Stone wall", 0.4 * (-1) ** k, z, 0.8, -2.5, p["top"] - p["z"] + 0.25, 7)
    elif t == "waterwheel":
        m.poly_prism("Wood", [(p["r"] * math.cos(2 * math.pi * i / 12), p["r"] * math.sin(2 * math.pi * i / 12))
                              for i in range(12)], -p["w"] / 2, p["w"] / 2)
    elif t == "vat":
        m.cyl("Wood", 0, 0, 1.0, 0, 1.0, 8)
    elif t == "crane":
        m.box("Wood", -0.2, 0.2, 0, 8, -0.2, 0.2)
        m.box("Wood", -0.15, 6, 7.4, 7.7, -0.15, 0.15)
    elif t == "charcoal_clamp":
        m.cone("Roof shingle", 0, 0, p["r"], -0.2, 2.2, 10)
    elif t == "pavilion":
        cl = "Cloth (red)" if p["x"] < 1300 else "Cloth (blue)"
        m.cyl(cl, 0, 0, p["r"], 0, 2.2, 10, top=False)
        m.cone(cl, 0, 0, p["r"] * 1.1, 2.2, 5.0, 10)
    elif t == "jetty":
        m.box("Wood", -p["w"] / 2, p["w"] / 2, p["top"] - p["z"] + 0.4, p["top"] - p["z"] + 0.7,
              -p["length"], 0)
    elif t == "boat":
        m.box("Wood", -0.7, 0.7, p["top"] - p["z"] - 0.2, p["top"] - p["z"] + 0.4, -2, 2)
    elif t == "haystack":
        m.cyl("Hay", 0, 0, 1.6, -0.2, 1.4, 8)
        m.cone("Hay", 0, 0, 1.7, 1.4, 3.0, 8)
    elif t == "maypole":
        m.cyl("Wood", 0, 0, 0.15, 0, 9, 6)
        m.cone("Cloth (red)", 0, 0, 0.6, 7.5, 9.2, 6)
    else:
        return None
    return m


TREE_SHAPES = {  # species: (bark material, leaves material, kind)
    "oak": ("Bark", "Leaves (broadleaf)", "round"), "beech": ("Bark", "Leaves (broadleaf)", "round"),
    "ash": ("Bark", "Leaves (broadleaf)", "round"), "hawthorn": ("Bark", "Leaves (broadleaf)", "round"),
    "alder": ("Bark", "Leaves (broadleaf)", "round"), "birch": ("Bark (birch)", "Leaves (birch)", "narrow"),
    "pine": ("Bark", "Leaves (pine)", "conifer"), "willow": ("Bark", "Leaves (willow)", "weeping"),
    "apple": ("Bark", "Leaves (fruit tree)", "round"), "pear": ("Bark", "Leaves (fruit tree)", "round"),
    "plum": ("Bark", "Leaves (fruit tree)", "round"), "yew": ("Bark", "Leaves (yew)", "weeping"),
    "lime": ("Bark", "Leaves (lime)", "narrow"),
}


def _tree_geometry(kind, h):
    """Indexed, smooth-shaded low-poly tree as {material: (verts, faces)} in local coords."""
    parts = {}
    tr = max(0.18, h * 0.025)

    def ring(r, y, n):
        return [(r * math.cos(2 * math.pi * i / n), y, r * math.sin(2 * math.pi * i / n)) for i in range(n)]

    trunk_top = h * (0.45 if kind != "conifer" else 0.25)
    v = ring(tr, -0.5, 5) + ring(tr * 0.7, trunk_top, 5)
    f = [(i, (i + 1) % 5, 5 + (i + 1) % 5) for i in range(5)] + [(i, 5 + (i + 1) % 5, 5 + i) for i in range(5)]
    parts["trunk"] = (v, f)
    if kind == "conifer":
        v, f = [], []
        for lvl, (y0, y1, r) in enumerate([(h * 0.22, h * 0.7, h * 0.24), (h * 0.5, h, h * 0.16)]):
            base = len(v)
            v += ring(r, y0, 7) + [(0, y1, 0)]
            f += [(base + i, base + 7, base + (i + 1) % 7) for i in range(7)]
            f += [(base + i, base + (i + 1) % 7, base + 7) for i in range(0)]
        parts["leaves"] = (v, f)
    else:
        r = {"round": 0.32, "narrow": 0.2, "weeping": 0.42}[kind] * h
        yc = h * (0.68 if kind != "weeping" else 0.58)
        ry = {"round": 0.34, "narrow": 0.4, "weeping": 0.3}[kind] * h
        v = [(0, yc + ry, 0)] + ring(r, yc + ry * 0.35, 7) + ring(r * 0.95, yc - ry * 0.45, 7) + [(0, yc - ry * 0.8, 0)]
        f = [(0, 1 + (i + 1) % 7, 1 + i) for i in range(7)]
        f += [(1 + i, 1 + (i + 1) % 7, 8 + (i + 1) % 7) for i in range(7)]
        f += [(1 + i, 8 + (i + 1) % 7, 8 + i) for i in range(7)]
        f += [(15, 8 + i, 8 + (i + 1) % 7) for i in range(7)]
        parts["leaves"] = (v, f)
    return parts


def trees_mesh(trees):
    """One merged, indexed mesh per material for thousands of trees."""
    acc = {}
    cache = {}
    for t in trees:
        bark, leaves, kind = TREE_SHAPES[t["species"]]
        key = (kind, round(t["height"]))
        if key not in cache:
            cache[key] = _tree_geometry(kind, round(t["height"]))
        rot = (hash((t["x"], t["y"])) % 628) / 100
        cr, sr = math.cos(rot), math.sin(rot)
        for part, (v, f) in cache[key].items():
            mat = bark if part == "trunk" else leaves
            v = np.asarray(v, np.float32)
            vv = np.stack([v[:, 0] * cr - v[:, 2] * sr + t["x"], v[:, 1] + t["z"], v[:, 0] * sr + v[:, 2] * cr + t["y"]], 1)
            a = acc.setdefault(mat, ([], [], [], 0))
            a[0].append(vv)
            a[1].append(np.asarray(f, np.uint32) + a[3])
            nn = v - np.array([0, float(v[:, 1].mean()), 0], np.float32)
            nn[:, 1] *= 0.6
            nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-6)
            nn = np.stack([nn[:, 0] * cr - nn[:, 2] * sr, nn[:, 1], nn[:, 0] * sr + nn[:, 2] * cr], 1)
            a[2].append(nn)
            acc[mat] = (a[0], a[1], a[2], a[3] + len(v))
    prims = []
    for mat, (vs, fs, ns, _) in acc.items():
        prims.append((mat, np.concatenate(vs), np.concatenate(ns), np.concatenate(fs).ravel(), None))
    return prims


def terrain_mesh(H, weights, step):
    res = H.shape[0]
    idx = np.arange(0, res, step)
    if idx[-1] != res - 1:
        idx = np.append(idx, res - 1)
    n = len(idx)
    scale = 2048.0 / (res - 1)
    X, Z = np.meshgrid(idx * scale, idx * scale)
    Y = H[np.ix_(idx, idx)]
    pos = np.stack([X, Y, Z], -1).reshape(-1, 3).astype(np.float32)
    gz, gx = np.gradient(Y, idx * scale, idx * scale)
    nrm = np.stack([-gx, np.ones_like(gx), -gz], -1).reshape(-1, 3)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    uv = np.stack([X / 8.0, Z / 8.0], -1).reshape(-1, 2).astype(np.float32)
    i, j = np.meshgrid(np.arange(n - 1), np.arange(n - 1), indexing="ij")
    a = (i * n + j).ravel()
    b, c, d = a + 1, a + n, a + n + 1
    # dominant ground layer at each quad's centre picks its material
    ci = ((idx[:-1] + idx[1:]) // 2)
    stack = np.stack([weights[k][np.ix_(ci, ci)] for k in LAYERS], 0)
    dom = stack.argmax(0).ravel()
    prims = []
    for li, k in enumerate(LAYERS):
        m = dom == li
        if not m.any():
            continue
        tris = np.concatenate([np.stack([a[m], c[m], b[m]], 1), np.stack([b[m], c[m], d[m]], 1)]).ravel()
        prims.append((f"Terrain {k}", pos, nrm.astype(np.float32), tris.astype(np.uint32), uv))
    return prims


def _compact(prims):
    """Give each terrain primitive only the vertices it uses."""
    out = []
    for mat, pos, nrm, idx, uv in prims:
        used, inv = np.unique(idx, return_inverse=True)
        out.append((mat, pos[used], nrm[used], inv.astype(np.uint32), None if uv is None else uv[used]))
    return out


def water_meshes(W):
    out = []
    for w in W.waters:
        m = MB()
        if w["kind"] in ("river", "stream"):
            line, lv = w["line"], w["levels"]
            half = w["width"] / 2 + (1.5 if w["kind"] == "river" else 0.6)
            for i in range(len(line) - 1):
                (x0, z0), (x1, z1) = line[i], line[i + 1]
                if not (0 <= x0 <= 2048 and 0 <= x1 <= 2048 and 0 <= z0 <= 2048 and 0 <= z1 <= 2048):
                    continue
                yaw = math.atan2(z1 - z0, x1 - x0)
                j = min(i + 2, len(line) - 1)
                yaw2 = math.atan2(line[j][1] - z0, line[j][0] - x0)
                v0 = (-math.sin(yaw) * half, math.cos(yaw) * half)
                v1 = (-math.sin(yaw2) * half, math.cos(yaw2) * half)
                y0, y1 = float(lv[i]), float(lv[i + 1])
                m.quad("Water", (x0 - v0[0], y0, z0 - v0[1]), (x1 - v1[0], y1, z1 - v1[1]),
                       (x1 + v1[0], y1, z1 + v1[1]), (x0 + v0[0], y0, z0 + v0[1]), ((x0 + x1) / 2, y0 - 5, (z0 + z1) / 2))
        elif w["kind"] == "moat":
            y = w["level"]
            pin = ellipse_pts(w["cx"], w["cy"], w["rx"] - 10, w["ry"] - 10, 72)
            pout = ellipse_pts(w["cx"], w["cy"], w["rx"] + 10, w["ry"] + 10, 72)
            for i in range(72):
                a, b = pin[i], pin[(i + 1) % 72]
                c, d = pout[(i + 1) % 72], pout[i]
                m.quad("Water", (a[0], y, a[1]), (b[0], y, b[1]), (c[0], y, c[1]), (d[0], y, d[1]),
                       (a[0], y - 5, a[1]))
        else:
            y = w["level"]
            rot = math.radians(w.get("heading", 0))
            pts = []
            for k in range(40):
                t = 2 * math.pi * k / 40
                ex, ez = w["rx"] * 1.12 * math.cos(t), w["ry"] * 1.12 * math.sin(t)
                pts.append((w["cx"] + ex * math.cos(rot) - ez * math.sin(rot), w["cy"] + ex * math.sin(rot) + ez * math.cos(rot)))
            for k in range(40):
                a, b = pts[k], pts[(k + 1) % 40]
                m.tri("Water", (w["cx"], y, w["cy"]), (a[0], y, a[1]), (b[0], y, b[1]), (w["cx"], y - 5, w["cy"]))
        out.append((w, m))
    return out


def bridge_mesh(br):
    m = MB()
    L, Wd, deck = br["length"], br["width"], br["deck_z"]
    mat = "Stone wall" if br["material"] == "stone" else "Wood"
    ramp = 9.0
    pts = [(-L / 2 - ramp, br["end_z"][0] + 0.05, 0), (-L / 2, deck, 0), (L / 2, deck, 0),
           (L / 2 + ramp, br["end_z"][1] + 0.05, 0)]
    m.slab(mat, pts, Wd, 0.8 if mat == "Wood" else 1.4)
    for side in (-1, 1):
        z = side * (Wd / 2 - 0.25)
        m.box(mat, -L / 2, L / 2, deck, deck + (1.0 if mat == "Stone wall" else 0.9), z - 0.25, z + 0.25)
    n = br["arches"]
    piers = [-L / 2 + L * k / n for k in range(1, n)] if n > 1 else ([-L / 6, L / 6] if n else [-L / 4, 0, L / 4])
    for px in piers:
        if br["arches"]:
            pw = min(2.4, L / max(n, 1) * 0.3)
            m.box(mat, px - pw / 2, px + pw / 2, br["water_z"] - 3, deck - 1.4, -Wd / 2, Wd / 2)
        else:
            for sz in (-1, 1):
                m.box(mat, px - 0.2, px + 0.2, br["water_z"] - 2.5, deck - 0.8, sz * Wd / 2 - 0.4 * sz - 0.2,
                      sz * Wd / 2 - 0.4 * sz + 0.2)
    return m


def wall_mesh(w):
    m = MB()
    mat = wall_mat(w["material"])
    t = w["thickness"]
    for (x0, z0, x1, z1), (lo, hi) in zip(w["segments"], w["z"]):
        L = math.hypot(x1 - x0, z1 - z0) + t * 0.6
        yaw = math.atan2(z1 - z0, x1 - x0)
        top = hi + w["height"]
        m.obox(mat, (x0 + x1) / 2, (z0 + z1) / 2, L, t, yaw, lo, top)
        if w["kind"] in ("curtain", "inner", "town", "barbican"):
            nx, nz = -math.sin(yaw) * (t / 2 - 0.25), math.cos(yaw) * (t / 2 - 0.25)
            for s in (-1, 1):
                m.merlons(mat, [(x0 + s * nx, z0 + s * nz), (x1 + s * nx, z1 + s * nz)], top, 0.5, closed=False)
    return m


DISTRICT_NAMES = {"C": "Crownhold Castle", "T": "City wall & gates", "H": "The Hallowstones", "M": "Market quarter",
                  "K": "Minster close", "N": "North Ward", "E": "East Ward", "W": "West Ward", "S": "Southbank",
                  "R": "River, bridges & quays", "G": "Gardens & King's Park", "U": "University",
                  "X": "Outside the walls"}
GENERIC = {"house", "shop", "workshop", "tenement", "stable", "storehouse"}


def _placed(prims, x, y, z, heading):
    """Bake a local mesh into world coordinates (same transform as a node's translation + yaw)."""
    th = -math.radians(heading)
    c, s = math.cos(th), math.sin(th)
    out = []
    for mat, pos, nrm, idx, uv in prims:
        p = np.stack([pos[:, 0] * c + pos[:, 2] * s + x, pos[:, 1] + z, -pos[:, 0] * s + pos[:, 2] * c + y], 1)
        n = np.stack([nrm[:, 0] * c + nrm[:, 2] * s, nrm[:, 1], -nrm[:, 0] * s + nrm[:, 2] * c], 1)
        out.append((mat, p.astype(np.float32), n.astype(np.float32), idx, uv))
    return out


def _merge(prim_lists):
    acc = {}
    for prims in prim_lists:
        for mat, pos, nrm, idx, uv in prims:
            a = acc.setdefault(mat, ([], [], [], 0))
            a[0].append(pos)
            a[1].append(nrm)
            a[2].append(idx + a[3])
            acc[mat] = (a[0], a[1], a[2], a[3] + len(pos))
    return [(mat, np.concatenate(p), np.concatenate(n), np.concatenate(i).astype(np.uint32), None)
            for mat, (p, n, i, _) in acc.items()]


LITE = False


def export_glb(W, H, path, terrain_step=4, tree_stride=1, with_props=True, merge_all=False, lite=False):
    global LITE
    LITE = lite
    g = GLB()
    roots = []
    roots.append(g.node("Terrain", g.mesh("Terrain", _compact(terrain_mesh(H, W.weights, terrain_step))),
                        extras=dict(note="Blockout terrain. For full detail use heightmap_2049.png (1 m per pixel).")))
    water_children = []
    for w, m in water_meshes(W):
        water_children.append(g.node(w["name"], g.mesh(w["name"], m.primitives())))
    roots.append(g.node("Water", children=water_children))
    wall_children = [g.node(f"{w['id']} {w['name']}", g.mesh(w["name"], wall_mesh(w).primitives()),
                            extras=dict(kind=w["kind"], height=w["height"], thickness=w["thickness"]))
                     for w in W.walls]
    roots.append(g.node("Walls", children=wall_children))
    br_children = []
    for br in W.bridges:
        mesh = g.mesh(br["name"], bridge_mesh(br).primitives())
        br_children.append(g.node(br["name"], mesh, t=(br["x"], 0, br["y"]), yaw=-math.radians(br["heading"]),
                                  extras={k: br[k] for k in ("road", "length", "width", "deck_z")}))
    roots.append(g.node("Bridges", children=br_children))
    groups = {}
    blocks = {}
    for b in W.buildings:
        if b["type"] in GENERIC or merge_all:
            key = (DISTRICT_NAMES[b["district"]], f"{chr(65 + int(b['x'] // 128))}{int(b['y'] // 128) + 1}")
            blocks.setdefault(key, []).append(_placed(building_mesh(b).primitives(), b["x"], b["y"], b["z"], b["heading"]))
            continue
        mesh = g.mesh(b["name"], building_mesh(b).primitives())
        extras = {k: v for k, v in b.items() if k not in ("x", "y", "z")}
        extras.update(map_x=b["x"], map_y=b["y"], floor_z=b["z"])
        node = g.node(f"{b['id']} {b['name']}", mesh, t=(b["x"], b["z"], b["y"]),
                      yaw=-math.radians(b["heading"]), extras=extras)
        groups.setdefault(DISTRICT_NAMES[b["district"]], []).append(node)
    for (dist, cell), lists in sorted(blocks.items()):
        node = g.node(f"{dist} - houses in square {cell}", g.mesh(f"Houses {cell}", _merge(lists)),
                      extras=dict(count=len(lists), note="Ordinary houses merged per 128 m grid square; "
                                  "each one is listed individually in data/buildings.csv"))
        groups.setdefault(dist, []).append(node)
    roots.append(g.node("Buildings", children=[g.node(k, children=v) for k, v in groups.items()]))
    if with_props:
        pc, merged = [], {}
        for p in W.props:
            m = prop_mesh(p)
            if m is None:
                continue
            if "name" in p and not merge_all:
                mesh = g.mesh(p["type"], m.primitives())
                pc.append(g.node(p["name"], mesh, t=(p["x"], p["z"], p["y"]), yaw=-math.radians(p["heading"])))
            else:
                key = p.get("group", p["type"].replace("_", " ").title())
                merged.setdefault(key, []).append(_placed(m.primitives(), p["x"], p["y"], p["z"], p["heading"]))
        for key, lists in merged.items():
            pc.append(g.node(f"{key} ({len(lists)})", g.mesh(key, _merge(lists))))
        roots.append(g.node("Props & monuments", children=pc))
    trees = W.trees[::tree_stride]
    by_group = {}
    for t in trees:
        by_group.setdefault(t["group"], []).append(t)
    tc = [g.node(f"Trees - {k}", g.mesh(f"Trees {k}", trees_mesh(v)), extras=dict(count=len(v)))
          for k, v in by_group.items()]
    roots.append(g.node("Trees", children=tc))
    mk = [g.node(f"Landmark {lm['n']:02d} - {lm['name']}", t=(lm["x"], float(sample(H, lm["x"], lm["y"])) + 2, lm["y"]),
                 extras=dict(number=lm["n"], label=lm["name"], description=lm["desc"])) for lm in W.landmarks]
    roots.append(g.node("Landmarks (empties)", children=mk))
    g.write(path, [g.node(W.realm, children=roots)],
            asset_extras=dict(units="metres", axes="+X east, +Y up, +Z south; origin = map north-west corner"))
