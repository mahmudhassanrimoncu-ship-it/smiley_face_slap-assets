"""Blueprint-style SVG sheets drawn straight from the world data.

Sheets:
  main   - the whole vale, contours every 5 m, numbered landmarks, legend & key
  castle - Ashford Castle at large scale with every building ID and size
  town   - the walled town with every building ID
"""
import base64
import html
import io
import math

import numpy as np
from PIL import Image

from config import NAMES, REALM, REALM_TAGLINE, WORLD_SIZE, YOU, YOUR_HOUSE
from geom import rect_corners, sample

BG = "#173b6c"
INK = "#e9f2ff"
WATER = "#2a5a96"
SANS = "'Courier New', Courier, monospace"
SERIF = "Georgia, 'Times New Roman', serif"


def esc(s):
    return html.escape(str(s), quote=True)


class View:
    def __init__(self, x0, y0, x1, y1, px, py, scale):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.px, self.py, self.s = px, py, scale
        self.w, self.h = (x1 - x0) * scale, (y1 - y0) * scale

    def X(self, x):
        return self.px + (x - self.x0) * self.s

    def Y(self, y):
        return self.py + (y - self.y0) * self.s

    def P(self, pts):
        return " ".join(f"{self.X(x):.1f},{self.Y(y):.1f}" for x, y in pts)

    def visible(self, x, y, pad=0):
        return self.x0 - pad <= x <= self.x1 + pad and self.y0 - pad <= y <= self.y1 + pad


# ---------------------------------------------------------------- contours
_CASES = {1: [(3, 2)], 2: [(2, 1)], 3: [(3, 1)], 4: [(0, 1)], 5: [(3, 0), (2, 1)], 6: [(0, 2)], 7: [(3, 0)],
          8: [(0, 3)], 9: [(0, 2)], 10: [(0, 1), (3, 2)], 11: [(0, 1)], 12: [(3, 1)], 13: [(2, 1)], 14: [(3, 2)]}


def contour_lines(Z, level, x0, y0, cell):
    a = Z >= level
    case = a[:-1, :-1] * 8 + a[:-1, 1:] * 4 + a[1:, 1:] * 2 + a[1:, :-1] * 1
    nc = Z.shape[1]
    keys1, keys2, pts = [], [], {}

    def edge(e, i, j):
        if e == 0:
            z0, z1 = Z[i, j], Z[i, j + 1]
            t = (level - z0) / np.where(z1 == z0, 1e-6, z1 - z0)
            return (i * nc + j) * 2, j + t, i.astype(float)
        if e == 2:
            z0, z1 = Z[i + 1, j], Z[i + 1, j + 1]
            t = (level - z0) / np.where(z1 == z0, 1e-6, z1 - z0)
            return ((i + 1) * nc + j) * 2, j + t, (i + 1).astype(float)
        if e == 3:
            z0, z1 = Z[i, j], Z[i + 1, j]
            t = (level - z0) / np.where(z1 == z0, 1e-6, z1 - z0)
            return (i * nc + j) * 2 + 1, j.astype(float), i + t
        z0, z1 = Z[i, j + 1], Z[i + 1, j + 1]
        t = (level - z0) / np.where(z1 == z0, 1e-6, z1 - z0)
        return (i * nc + j + 1) * 2 + 1, (j + 1).astype(float), i + t

    for c, segs in _CASES.items():
        i, j = np.nonzero(case == c)
        if len(i) == 0:
            continue
        for e1, e2 in segs:
            k1, xa, ya = edge(e1, i, j)
            k2, xb, yb = edge(e2, i, j)
            for k, x, y in zip(k1.tolist(), xa.tolist(), ya.tolist()):
                pts[k] = (x0 + x * cell, y0 + y * cell)
            for k, x, y in zip(k2.tolist(), xb.tolist(), yb.tolist()):
                pts[k] = (x0 + x * cell, y0 + y * cell)
            keys1 += k1.tolist()
            keys2 += k2.tolist()
    adj = {}
    for s, (k1, k2) in enumerate(zip(keys1, keys2)):
        adj.setdefault(k1, []).append(s)
        adj.setdefault(k2, []).append(s)
    used = bytearray(len(keys1))
    lines = []
    for s in range(len(keys1)):
        if used[s]:
            continue
        used[s] = 1
        chain = [keys1[s], keys2[s]]
        for direction in (1, 0):
            while True:
                end = chain[-1] if direction else chain[0]
                nxt = None
                for t in adj.get(end, ()):
                    if not used[t]:
                        nxt = t
                        break
                if nxt is None:
                    break
                used[nxt] = 1
                other = keys2[nxt] if keys1[nxt] == end else keys1[nxt]
                if direction:
                    chain.append(other)
                else:
                    chain.insert(0, other)
        lines.append([pts[k] for k in chain])
    return lines


def hillshade_png(H, res, region=None):
    if region:
        x0, y0, x1, y1 = region
        k = (H.shape[0] - 1) / WORLD_SIZE
        H = H[int(y0 * k):int(y1 * k) + 1, int(x0 * k):int(x1 * k) + 1]
    img = Image.fromarray(H.astype(np.float32), mode="F").resize((res, int(res * H.shape[0] / H.shape[1])), Image.BILINEAR)
    Z = np.asarray(img)
    cell = (region[2] - region[0] if region else WORLD_SIZE) / res
    gy, gx = np.gradient(Z, cell)
    az, alt = math.radians(315), math.radians(40)
    slope = np.arctan(np.hypot(gx, gy) * 1.6)
    aspect = np.arctan2(-gy, gx)
    shade = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    v = np.clip((shade - np.sin(alt)) * 1.8, -1, 1)          # 0 on flat ground, +lit, -shadow
    rgba = np.zeros(v.shape + (4,), np.uint8)
    lit = v > 0
    rgba[lit, :3] = (233, 242, 255)
    rgba[~lit, :3] = (4, 14, 34)
    rgba[..., 3] = (np.abs(v) * np.where(lit, 150, 200)).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------- svg helpers
class SVG:
    def __init__(self, w, h, title):
        self.w, self.h = w, h
        self.o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
                  f"<title>{esc(title)}</title>", DEFS]

    def a(self, s):
        self.o.append(s)

    def text(self, x, y, s, size=13, anchor="middle", weight="normal", italic=False, spacing=0, font=SANS,
             halo=True, opacity=1, rotate=0, fill=INK):
        halo_attr = (f' stroke="{BG}" stroke-width="{max(3, size * 0.3):.1f}" paint-order="stroke" '
                     f'stroke-linejoin="round"' if halo else "")
        rot = f' transform="rotate({rotate:.1f} {x:.1f} {y:.1f})"' if rotate else ""
        self.a(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size}" text-anchor="{anchor}" '
               f'font-weight="{weight}" font-style="{"italic" if italic else "normal"}" letter-spacing="{spacing}" '
               f'fill="{fill}" opacity="{opacity}"{halo_attr}{rot}>{esc(s)}</text>')

    def done(self):
        self.o.append(f'<rect width="{self.w}" height="{self.h}" fill="url(#vignette)" pointer-events="none"/>')
        return "\n".join(self.o + ["</svg>"])


DEFS = f'''<defs>
<pattern id="g20" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20 0H0V20" fill="none" stroke="{INK}" stroke-width="0.5" opacity="0.09"/></pattern>
<pattern id="g100" width="100" height="100" patternUnits="userSpaceOnUse"><rect width="100" height="100" fill="url(#g20)"/><path d="M100 0H0V100" fill="none" stroke="{INK}" stroke-width="0.8" opacity="0.13"/></pattern>
<pattern id="p-wheat" width="5" height="5" patternUnits="userSpaceOnUse"><line x1="2.5" y1="0" x2="2.5" y2="5" stroke="{INK}" stroke-width="0.7" opacity="0.6"/></pattern>
<pattern id="p-rye" width="3.5" height="3.5" patternUnits="userSpaceOnUse"><line x1="1.7" y1="0" x2="1.7" y2="3.5" stroke="{INK}" stroke-width="0.6" opacity="0.6"/></pattern>
<pattern id="p-barley" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="3" y1="0" x2="3" y2="6" stroke="{INK}" stroke-width="0.7" opacity="0.6"/></pattern>
<pattern id="p-oats" width="6" height="6" patternUnits="userSpaceOnUse"><circle cx="3" cy="3" r="0.9" fill="{INK}" opacity="0.7"/></pattern>
<pattern id="p-beans" width="8" height="8" patternUnits="userSpaceOnUse"><path d="M2 4h4M4 2v4" stroke="{INK}" stroke-width="0.7" opacity="0.65"/></pattern>
<pattern id="p-peas" width="8" height="8" patternUnits="userSpaceOnUse"><circle cx="4" cy="4" r="1.6" fill="none" stroke="{INK}" stroke-width="0.6" opacity="0.65"/></pattern>
<pattern id="p-fallow" width="10" height="10" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="0.7" fill="{INK}" opacity="0.5"/><circle cx="7" cy="7" r="0.7" fill="{INK}" opacity="0.5"/></pattern>
<pattern id="p-grazing" width="22" height="16" patternUnits="userSpaceOnUse"><path d="M4 7l1.5 3 1.5-3M14 14l1.5-3 1.5 3" fill="none" stroke="{INK}" stroke-width="0.7" opacity="0.6"/></pattern>
<pattern id="p-herbs" width="6" height="6" patternUnits="userSpaceOnUse"><path d="M0 0L6 6M6 0L0 6" stroke="{INK}" stroke-width="0.5" opacity="0.6"/></pattern>
<pattern id="p-croft" width="7" height="7" patternUnits="userSpaceOnUse"><circle cx="3.5" cy="3.5" r="0.6" fill="{INK}" opacity="0.4"/></pattern>
<pattern id="hatch" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="4" height="4" fill="{BG}"/><line x1="0" y1="0" x2="0" y2="4" stroke="{INK}" stroke-width="0.8" opacity="0.85"/></pattern>
<pattern id="waves" width="16" height="8" patternUnits="userSpaceOnUse"><rect width="16" height="8" fill="{WATER}"/><path d="M1 5q2-3 4 0t4 0" fill="none" stroke="{INK}" stroke-width="0.6" opacity="0.5"/></pattern>
<pattern id="cobble" width="6" height="6" patternUnits="userSpaceOnUse"><circle cx="3" cy="3" r="0.6" fill="{INK}" opacity="0.35"/></pattern>
<radialGradient id="vignette" cx="50%" cy="50%" r="75%"><stop offset="65%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#000" stop-opacity="0.3"/></radialGradient>
</defs>'''


# ---------------------------------------------------------------- map layers
def draw_map(svg, W, H, v, contour_step=5, index_step=25, detail=False, label_ids=False, shade_res=1024):
    region = (v.x0, v.y0, v.x1, v.y1)
    clip = f"clip{int(v.px)}{int(v.py)}"
    svg.a(f'<clipPath id="{clip}"><rect x="{v.px}" y="{v.py}" width="{v.w:.1f}" height="{v.h:.1f}"/></clipPath>')
    svg.a(f'<g clip-path="url(#{clip})">')
    png = hillshade_png(H, shade_res, region)
    svg.a(f'<image x="{v.px}" y="{v.py}" width="{v.w:.1f}" height="{v.h:.1f}" preserveAspectRatio="none" '
          f'opacity="0.9" href="data:image/png;base64,{png}"/>')

    # contours
    k = (H.shape[0] - 1) / WORLD_SIZE
    cell = 4.0 if not detail else 1.0
    stride = int(cell * k)
    i0, i1 = int(v.y0 * k), int(v.y1 * k) + 1
    j0, j1 = int(v.x0 * k), int(v.x1 * k) + 1
    Z = H[i0:i1:stride, j0:j1:stride]
    lo, hi = math.ceil(Z.min() / contour_step) * contour_step, Z.max()
    for level in np.arange(lo, hi, contour_step):
        major = abs(level % index_step) < 1e-6
        lines = contour_lines(Z, level, j0 / k, i0 / k, cell)
        if not lines:
            continue
        d = " ".join("M" + " L".join(f"{v.X(x):.1f},{v.Y(y):.1f}" for x, y in ln[::1 if detail else 2] + [ln[-1]])
                     for ln in lines if len(ln) > 3)
        svg.a(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{1.1 if major else 0.55}" '
              f'opacity="{0.6 if major else 0.32}"/>')
        if major:
            for ln in lines:
                if len(ln) > 120:
                    x, y = ln[len(ln) // 2]
                    if v.visible(x, y, -20):
                        svg.text(v.X(x), v.Y(y) + 3, f"{int(level)}", size=9, opacity=0.8)

    # fields, crofts, pastures
    for f in W.fields:
        if f["crop"] == "outline":
            svg.a(f'<polygon points="{v.P(f["poly"])}" fill="none" stroke="{INK}" stroke-width="1.6"/>')
        else:
            svg.a(f'<polygon points="{v.P(f["poly"])}" fill="url(#p-{f["crop"]})" stroke="{INK}" '
                  f'stroke-width="0.6" opacity="0.95"/>')
    for p in W.pastures:
        svg.a(f'<polygon points="{v.P(p["poly"])}" fill="url(#p-grazing)" stroke="{INK}" stroke-width="1" '
              f'stroke-dasharray="6 4"/>')
    for c in W.crofts:
        svg.a(f'<polygon points="{v.P(c["poly"])}" fill="url(#p-croft)" stroke="{INK}" stroke-width="0.6" '
              f'stroke-dasharray="3 3" opacity="0.8"/>')
    if hasattr(W, "churchyard"):
        x0, y0, x1, y1 = W.churchyard
        svg.a(f'<polygon points="{v.P([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])}" fill="none" stroke="{INK}" '
              f'stroke-width="0.8" stroke-dasharray="4 3"/>')

    # trees
    tree_out = []
    for t in W.trees:
        if not v.visible(t["x"], t["y"], 10):
            continue
        r = max(1.5, t["height"] * 0.2 * v.s)
        if t["species"] in ("apple", "pear", "plum"):
            r = max(1.6, 2.2 * v.s)
        tree_out.append(f'<circle cx="{v.X(t["x"]):.1f}" cy="{v.Y(t["y"]):.1f}" r="{r:.1f}"/>')
    svg.a(f'<g fill="{BG}" stroke="{INK}" stroke-width="{0.7 if not detail else 1}" opacity="0.9">{"".join(tree_out)}</g>')

    # water
    for w in W.waters:
        if w["kind"] in ("river", "stream"):
            d = "M" + " L".join(f"{v.X(x):.1f},{v.Y(y):.1f}" for x, y in w["line"])
            ww = w["width"] * v.s
            svg.a(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{ww + 3:.1f}" stroke-linejoin="round"/>')
            svg.a(f'<path d="{d}" fill="none" stroke="{WATER}" stroke-width="{ww:.1f}" stroke-linejoin="round"/>')
            svg.a(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="0.7" stroke-dasharray="10 9" opacity="0.5"/>')
        elif w["kind"] == "moat":
            from geom import ellipse_pts
            outer = ellipse_pts(w["cx"], w["cy"], w["rx"] + w["width"] / 2, w["ry"] + w["width"] / 2, 72)
            inner = ellipse_pts(w["cx"], w["cy"], w["rx"] - w["width"] / 2, w["ry"] - w["width"] / 2, 72)
            svg.a(f'<path d="M{v.P(outer)}Z M{v.P(inner[::-1])}Z" fill="url(#waves)" fill-rule="evenodd" '
                  f'stroke="{INK}" stroke-width="1.5"/>')
        else:
            pts = w["line"]
            if w.get("heading"):
                rot = math.radians(w["heading"])
                pts = [(w["cx"] + (x - w["cx"]) * math.cos(rot) - (y - w["cy"]) * math.sin(rot),
                        w["cy"] + (x - w["cx"]) * math.sin(rot) + (y - w["cy"]) * math.cos(rot)) for x, y in pts]
            svg.a(f'<polygon points="{v.P(pts)}" fill="url(#waves)" stroke="{INK}" stroke-width="1.4"/>')

    # roads
    style = {"road": (1.0, None), "lane": (1.0, None), "street": (1.0, None), "track": (0.9, "6 4"),
             "path": (0.9, "2 4")}
    for kind in ("path", "track", "lane", "road", "street"):
        for r in W.roads:
            if r["kind"] != kind:
                continue
            d = "M" + " L".join(f"{v.X(x):.1f},{v.Y(y):.1f}" for x, y in r["line"][::2]) + \
                (f" L{v.X(r['line'][-1][0]):.1f},{v.Y(r['line'][-1][1]):.1f}")
            ww = max(r["width"] * v.s, 2.5)
            if kind == "path":
                svg.a(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="1.2" stroke-dasharray="2 4" opacity="0.9"/>')
                continue
            svg.a(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{ww + 2.4:.1f}" stroke-linejoin="round" '
                  f'stroke-linecap="round"' + (f' stroke-dasharray="{style[kind][1]}"' if kind == "track" else "") + "/>")
            svg.a(f'<path d="{d}" fill="none" stroke="{BG}" stroke-width="{ww:.1f}" stroke-linejoin="round" stroke-linecap="round"/>')
            if r["surface"] == "cobble":
                svg.a(f'<path d="{d}" fill="none" stroke="url(#cobble)" stroke-width="{ww:.1f}" stroke-linejoin="round"/>')
    if hasattr(W, "square"):
        x0, y0, x1, y1 = W.square
        svg.a(f'<rect x="{v.X(x0):.1f}" y="{v.Y(y0):.1f}" width="{(x1 - x0) * v.s:.1f}" height="{(y1 - y0) * v.s:.1f}" '
              f'fill="{BG}" stroke="{INK}" stroke-width="1.2"/>')
        svg.a(f'<rect x="{v.X(x0):.1f}" y="{v.Y(y0):.1f}" width="{(x1 - x0) * v.s:.1f}" height="{(y1 - y0) * v.s:.1f}" '
              f'fill="url(#cobble)"/>')

    # bridges
    for br in W.bridges:
        c = rect_corners(br["x"], br["y"], br["length"], br["width"], br["heading"])
        svg.a(f'<polygon points="{v.P(c)}" fill="{BG}" stroke="{INK}" stroke-width="1.6"/>')

    # walls
    for w in W.walls:
        tw = max(w["thickness"] * v.s, 1.6)
        d = " ".join(f"M{v.X(s[0]):.1f},{v.Y(s[1]):.1f} L{v.X(s[2]):.1f},{v.Y(s[3]):.1f}" for s in w["segments"])
        if w["kind"] == "fence":
            svg.a(f'<path d="{d}" stroke="{INK}" stroke-width="1.5"/>')
            continue
        svg.a(f'<path d="{d}" stroke="{INK}" stroke-width="{tw + 2.2:.1f}" stroke-linecap="square"/>')
        svg.a(f'<path d="{d}" stroke="{BG}" stroke-width="{max(tw - 0.6, 0.8):.1f}" stroke-linecap="square"/>')

    # buildings
    important = {"keep", "hall", "church", "chapel", "guildhall", "inn", "manor_house", "gatehouse", "market_hall",
                 "watermill", "windmill", "watchtower", "lodge", "cloister"}
    for b in W.buildings:
        if not v.visible(b["x"], b["y"], 20):
            continue
        fill = "url(#hatch)" if b["type"] in important or b["type"] == "shop" else BG
        sw = 1.4 if b["type"] in important else 1.0
        if b["shape"] == "round":
            svg.a(f'<circle cx="{v.X(b["x"]):.1f}" cy="{v.Y(b["y"]):.1f}" r="{b["w"] / 2 * v.s:.1f}" fill="{BG}" '
                  f'stroke="{INK}" stroke-width="{sw + 0.4}"/>')
            if v.s > 2:
                svg.a(f'<circle cx="{v.X(b["x"]):.1f}" cy="{v.Y(b["y"]):.1f}" r="{b["w"] / 2 * v.s * 0.62:.1f}" '
                      f'fill="none" stroke="{INK}" stroke-width="0.6"/>')
        else:
            c = rect_corners(b["x"], b["y"], b["w"], b["d"], b["heading"])
            svg.a(f'<polygon points="{v.P(c)}" fill="{fill}" stroke="{INK}" stroke-width="{sw}"/>')
            if b["roof"] in ("gable", "hip") and v.s > 1.5:
                along_x = b["w"] >= b["d"]
                a = math.radians(b["heading"] + (0 if along_x else 90))
                L = (abs(b["w"] - b["d"]) / 2 if b["roof"] == "hip" else max(b["w"], b["d"]) / 2 - 0.5)
                x0, y0 = b["x"] - L * math.cos(a), b["y"] - L * math.sin(a)
                x1, y1 = b["x"] + L * math.cos(a), b["y"] + L * math.sin(a)
                svg.a(f'<line x1="{v.X(x0):.1f}" y1="{v.Y(y0):.1f}" x2="{v.X(x1):.1f}" y2="{v.Y(y1):.1f}" '
                      f'stroke="{INK}" stroke-width="0.6" opacity="0.8"/>')
            if v.s > 2.5 and b["type"] not in ("gatehouse",):           # door tick on the front
                f = math.radians(b["heading"])
                fx, fy = b["x"] + math.sin(f) * b["d"] / 2, b["y"] - math.cos(f) * b["d"] / 2
                svg.a(f'<circle cx="{v.X(fx):.1f}" cy="{v.Y(fy):.1f}" r="{max(1.2, 0.6 * v.s):.1f}" fill="{INK}"/>')
        if label_ids:
            fs = max(6.5, min(11, min(b["w"], b["d"]) * v.s / 2.6))
            if b["type"] in ("tower",) and b["name"] in ("Keep turret",):
                continue
            svg.text(v.X(b["x"]), v.Y(b["y"]) + fs * 0.35, b["id"].split("-")[1], size=round(fs, 1), halo=True,
                     weight="bold")

    # props worth seeing
    for p in W.props:
        if not v.visible(p["x"], p["y"]):
            continue
        X, Y = v.X(p["x"]), v.Y(p["y"])
        t = p["type"]
        if t in ("standing_stone", "altar_stone", "gravestone"):
            svg.a(f'<rect x="{X - 1.6:.1f}" y="{Y - 1.6:.1f}" width="3.2" height="3.2" fill="{INK}"/>')
        elif t == "well":
            svg.a(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="{max(2.5, 1.3 * v.s):.1f}" fill="url(#waves)" stroke="{INK}"/>')
        elif t == "beacon":
            svg.a(f'<path d="M{X:.1f},{Y - 5:.1f} l4,8 h-8z" fill="{INK}"/>')
        elif t == "market_cross":
            svg.a(f'<path d="M{X:.1f},{Y - 5:.1f}v10M{X - 4:.1f},{Y - 1:.1f}h8" stroke="{INK}" stroke-width="1.6"/>')
        elif t in ("market_stall",) and v.s > 2:
            c = rect_corners(p["x"], p["y"], p["w"], p["d"], p["heading"])
            svg.a(f'<polygon points="{v.P(c)}" fill="{BG}" stroke="{INK}" stroke-width="0.8"/>')
        elif t == "stepping_stones":
            for kk in range(7):
                a = math.radians(p["heading"])
                s = -p["length"] / 2 + kk * p["length"] / 6
                svg.a(f'<circle cx="{v.X(p["x"] + s * math.cos(a)):.1f}" cy="{v.Y(p["y"] + s * math.sin(a)):.1f}" '
                      f'r="2" fill="{INK}"/>')
        elif t == "drawbridge" and v.s > 1:
            c = rect_corners(p["x"], p["y"], p["w"], p["length"], p["heading"])
            svg.a(f'<polygon points="{v.P(c)}" fill="url(#hatch)" stroke="{INK}" stroke-width="1"/>')
    svg.a("</g>")


def frame_and_grid(svg, v, step=128, labels=True):
    svg.a(f'<rect x="{v.px}" y="{v.py}" width="{v.w:.1f}" height="{v.h:.1f}" fill="none" stroke="{INK}" stroke-width="3"/>')
    svg.a(f'<rect x="{v.px - 9}" y="{v.py - 9}" width="{v.w + 18:.1f}" height="{v.h + 18:.1f}" fill="none" '
          f'stroke="{INK}" stroke-width="1"/>')
    first_x = math.ceil(v.x0 / step) * step
    first_y = math.ceil(v.y0 / step) * step
    for gx in np.arange(first_x, v.x1 + 0.1, step):
        X = v.X(gx)
        svg.a(f'<line x1="{X:.1f}" y1="{v.py}" x2="{X:.1f}" y2="{v.py + v.h:.1f}" stroke="{INK}" stroke-width="0.6" '
              f'stroke-dasharray="1 7" opacity="0.55"/>')
        svg.a(f'<line x1="{X:.1f}" y1="{v.py - 9}" x2="{X:.1f}" y2="{v.py}" stroke="{INK}"/>')
        svg.a(f'<line x1="{X:.1f}" y1="{v.py + v.h:.1f}" x2="{X:.1f}" y2="{v.py + v.h + 9:.1f}" stroke="{INK}"/>')
        if labels and gx + step <= v.x1 + 0.1 and step == 128:
            col = chr(65 + int(gx // 128))
            svg.text(X + step * v.s / 2, v.py - 16, col, size=13, weight="bold", halo=False)
            svg.text(X + step * v.s / 2, v.py + v.h + 28, col, size=13, weight="bold", halo=False)
        svg.text(X, v.py + v.h + 44 if step == 128 else v.py + v.h + 26, f"{int(gx)} m", size=9, halo=False, opacity=0.7)
    for gy in np.arange(first_y, v.y1 + 0.1, step):
        Y = v.Y(gy)
        svg.a(f'<line x1="{v.px}" y1="{Y:.1f}" x2="{v.px + v.w:.1f}" y2="{Y:.1f}" stroke="{INK}" stroke-width="0.6" '
              f'stroke-dasharray="1 7" opacity="0.55"/>')
        svg.a(f'<line x1="{v.px - 9}" y1="{Y:.1f}" x2="{v.px}" y2="{Y:.1f}" stroke="{INK}"/>')
        if labels and gy + step <= v.y1 + 0.1 and step == 128:
            svg.text(v.px - 24, Y + step * v.s / 2 + 5, str(int(gy // 128) + 1), size=13, weight="bold", halo=False)
        svg.text(v.px - 14, Y + 3, f"{int(gy)}", size=9, anchor="end", halo=False, opacity=0.7)


def compass(svg, cx, cy, r=70):
    svg.a(f'<g transform="translate({cx} {cy})" stroke="{INK}">'
          f'<circle r="{r}" fill="none" stroke-width="1"/><circle r="{r - 8}" fill="none" stroke-width="0.6" stroke-dasharray="2 3"/>'
          + "".join(f'<line x1="0" y1="{-r + 8}" x2="0" y2="{-r + 1}" transform="rotate({d})" stroke-width="1"/>'
                    for d in range(0, 360, 15))
          + f'<path d="M0,{-r + 6} L9,-9 L0,0Z" fill="{INK}"/><path d="M0,{-r + 6} L-9,-9 L0,0Z" fill="none" stroke-width="1.2"/>'
          f'<path d="M0,{r - 6} L9,9 L0,0Z" fill="none" stroke-width="1.2"/><path d="M0,{r - 6} L-9,9 L0,0Z" fill="{INK}"/>'
          f'<path d="M{r - 6},0 L9,-9 L0,0Z" fill="{INK}"/><path d="M{r - 6},0 L9,9 L0,0Z" fill="none" stroke-width="1.2"/>'
          f'<path d="M{-r + 6},0 L-9,9 L0,0Z" fill="{INK}"/><path d="M{-r + 6},0 L-9,-9 L0,0Z" fill="none" stroke-width="1.2"/>'
          f'<circle r="4" fill="{BG}" stroke-width="1.4"/></g>')
    for lbl, dx, dy in [("N", 0, -r - 10), ("S", 0, r + 22), ("E", r + 16, 6), ("W", -r - 16, 6)]:
        svg.text(cx + dx, cy + dy, lbl, size=17, weight="bold", font=SERIF, halo=False)


def scale_bar(svg, x, y, v, metres, ticks):
    svg.text(x, y, f"SCALE  1 : {int(round(1000 / (v.s * 0.2646) / 50) * 50):,}  (on a 96-dpi print)".replace(",", " "),
             size=11, anchor="start", halo=False)
    seg = metres / ticks
    for k in range(ticks):
        svg.a(f'<rect x="{x + k * seg * v.s:.1f}" y="{y + 10}" width="{seg * v.s:.1f}" height="9" '
              f'fill="{INK if k % 2 == 0 else BG}" stroke="{INK}"/>')
    for k in range(ticks + 1):
        svg.text(x + k * seg * v.s, y + 36, f"{int(k * seg)}" + (" m" if k == ticks else ""), size=10, halo=False)


def title_block(svg, x0, y0, x1, y1, rows):
    rh = (y1 - y0) / len(rows)
    svg.a(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="none" stroke="{INK}" stroke-width="1.4"/>')
    svg.a(f'<line x1="{x0 + 110}" y1="{y0}" x2="{x0 + 110}" y2="{y1}" stroke="{INK}" stroke-width="0.8"/>')
    for i, (k, val) in enumerate(rows):
        y = y0 + i * rh
        if i:
            svg.a(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{INK}" stroke-width="0.8"/>')
        svg.text(x0 + 12, y + rh / 2 + 4, k, size=10, anchor="start", spacing=2, halo=False, opacity=0.8)
        svg.text(x0 + 122, y + rh / 2 + 4, val, size=12, anchor="start", halo=False)


def legend(svg, x, y, width):
    svg.text(x, y, "LEGEND", size=16, anchor="start", weight="bold", spacing=4, halo=False)
    svg.a(f'<line x1="{x}" y1="{y + 8}" x2="{x + width}" y2="{y + 8}" stroke="{INK}"/>')
    items = [
        ("contour", "Contour, every 5 m (bold every 25 m)"), ("wall", "Castle / town wall"),
        ("tower", "Tower (round)"), ("bld", "Building, dot = front door"), ("bldh", "Hall, church, inn, shop"),
        ("road", "Road / street (cobbled dotted)"), ("track", "Field track"), ("path", "Footpath"),
        ("water", "River, moat, pond"), ("bridge", "Bridge"), ("croft", "Croft (cottage garden)"),
        ("wheat", "Wheat / rye strips"), ("barley", "Barley, oats, beans, peas"), ("fallow", "Fallow strips"),
        ("pasture", "Pasture & greens"), ("tree", "Tree (size = crown)"), ("lm", "Numbered landmark (see key)"),
    ]
    for i, (k, label) in enumerate(items):
        col, row = divmod(i, 9)
        sx = x + col * (width / 2)
        sy = y + 36 + row * 28
        if k == "contour":
            svg.a(f'<path d="M{sx},{sy} q14,-12 28,-3 t28,0" fill="none" stroke="{INK}" stroke-width="1.1"/>')
        elif k == "wall":
            svg.a(f'<path d="M{sx},{sy - 4} h56" stroke="{INK}" stroke-width="6"/><path d="M{sx},{sy - 4} h56" stroke="{BG}" stroke-width="3"/>')
        elif k == "tower":
            svg.a(f'<circle cx="{sx + 28}" cy="{sy - 4}" r="8" fill="{BG}" stroke="{INK}" stroke-width="1.6"/>')
        elif k in ("bld", "bldh"):
            svg.a(f'<rect x="{sx + 14}" y="{sy - 12}" width="28" height="16" fill="{"url(#hatch)" if k == "bldh" else BG}" stroke="{INK}"/>'
                  f'<circle cx="{sx + 28}" cy="{sy - 12}" r="1.6" fill="{INK}"/>')
        elif k == "road":
            svg.a(f'<path d="M{sx},{sy - 4} h56" stroke="{INK}" stroke-width="10"/><path d="M{sx},{sy - 4} h56" stroke="{BG}" stroke-width="7.6"/>')
        elif k == "track":
            svg.a(f'<path d="M{sx},{sy - 4} h56" stroke="{INK}" stroke-width="6" stroke-dasharray="6 4"/><path d="M{sx},{sy - 4} h56" stroke="{BG}" stroke-width="3.6"/>')
        elif k == "path":
            svg.a(f'<path d="M{sx},{sy - 4} h56" stroke="{INK}" stroke-width="1.2" stroke-dasharray="2 4"/>')
        elif k == "water":
            svg.a(f'<rect x="{sx}" y="{sy - 12}" width="56" height="15" fill="url(#waves)" stroke="{INK}"/>')
        elif k == "bridge":
            svg.a(f'<rect x="{sx}" y="{sy - 12}" width="56" height="15" fill="url(#waves)"/><rect x="{sx + 18}" y="{sy - 15}" width="20" height="21" fill="{BG}" stroke="{INK}" stroke-width="1.4"/>')
        elif k == "croft":
            svg.a(f'<rect x="{sx + 6}" y="{sy - 13}" width="44" height="17" fill="url(#p-croft)" stroke="{INK}" stroke-dasharray="3 3"/>')
        elif k in ("wheat", "barley", "fallow"):
            svg.a(f'<rect x="{sx}" y="{sy - 13}" width="56" height="17" fill="url(#p-{k})" stroke="{INK}"/>')
        elif k == "pasture":
            svg.a(f'<rect x="{sx}" y="{sy - 13}" width="56" height="17" fill="url(#p-grazing)" stroke="{INK}" stroke-dasharray="6 4"/>')
        elif k == "tree":
            for j in range(3):
                svg.a(f'<circle cx="{sx + 10 + j * 18}" cy="{sy - 4}" r="{4 + j * 1.5}" fill="{BG}" stroke="{INK}"/>')
        elif k == "lm":
            svg.a(f'<circle cx="{sx + 28}" cy="{sy - 4}" r="11" fill="{BG}" stroke="{INK}" stroke-width="1.4"/>')
            svg.text(sx + 28, sy, "7", size=11, weight="bold", halo=False)
        svg.text(sx + 66, sy, label, size=11.5, anchor="start", halo=False)
    return y + 36 + 9 * 28


def _area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2


def wrap(text, width):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            if len(cur) + len(word) + 1 > width:
                lines.append(cur)
                cur = word
            else:
                cur = f"{cur} {word}".strip()
        lines.append(cur)
        lines.append("")
    return lines[:-1]


def lore_text(num):
    n = NAMES
    ford = num.get(n["ford"], "")
    stones = num.get(n["stones"], "")
    return (f"Long before the castle, travellers waded the {n['river']} at a shallow ford ({ford}), and a village "
            f"grew beside it. {n['stones']} ({stones}) were already old on the hill above. When raiders came over "
            f"{n['north_hills']}, the first Baron raised a tower on Castle Mount, where the hills curl round in a "
            f"horseshoe and every road can be watched. The tower grew into {n['castle']}; the village became the "
            f"walled market town of {n['town']}; the monks of {n['abbey']} brought learning, wool and wine.\n"
            f"Today four watch-fires guard the ridges, mills turn on wind and water, and three great fields feed "
            f"the vale in rotation: one wheat, one barley and beans, one resting under the sheep.\n"
            f"You are {YOU} - the Baron's hand in the vale. Every house on these sheets has a family and every road "
            f"a reason. Build it, walk it, and write its next chapter yourself.")


LM_OFFSETS = {}  # landmark number -> (dx, dy) in px, filled by build if needed


def main_sheet(W, H):
    svg = SVG(3560, 2580, f"{REALM} - master site plan")
    svg.a(f'<rect width="3560" height="2580" fill="{BG}"/><rect width="3560" height="2580" fill="url(#g100)"/>')
    v = View(0, 0, WORLD_SIZE, WORLD_SIZE, 70, 90, 2400 / WORLD_SIZE)
    draw_map(svg, W, H, v)
    # labels
    for lb in W.labels:
        size = lb["size"]
        kind = lb["kind"]
        font = SERIF if kind in ("place", "region") else SANS
        svg.text(v.X(lb["x"]), v.Y(lb["y"]), lb["t"], size=size, weight="bold" if kind in ("place", "region") else "normal",
                 italic=kind in ("water", "field"), spacing=4 if kind != "water" else 3, font=font,
                 rotate=lb.get("rot", 0), opacity=0.95)
        if lb.get("sub"):
            svg.text(v.X(lb["x"]), v.Y(lb["y"]) + size * 0.85, lb["sub"], size=12, italic=True, spacing=1.5, opacity=0.9)
    for p in W.peaks[:6]:
        X, Y = v.X(p["x"]), v.Y(p["y"])
        z = float(sample(H, p["x"], p["y"]))
        svg.text(X, Y + 22, f"{p['name']}  {z:.0f} m", size=12, italic=True, font=SERIF)
    # landmarks
    for lm in W.landmarks:
        X, Y = v.X(lm["x"]), v.Y(lm["y"])
        dx, dy = LM_OFFSETS.get(lm["n"], (20, -20))
        svg.a(f'<line x1="{X:.1f}" y1="{Y:.1f}" x2="{X + dx:.1f}" y2="{Y + dy:.1f}" stroke="{INK}" stroke-width="1" '
              f'stroke-dasharray="3 2"/><circle cx="{X:.1f}" cy="{Y:.1f}" r="2.2" fill="{INK}"/>')
        svg.a(f'<circle cx="{X + dx:.1f}" cy="{Y + dy:.1f}" r="12" fill="{BG}" stroke="{INK}" stroke-width="1.5"/>')
        svg.text(X + dx, Y + dy + 4.5, str(lm["n"]), size=12, weight="bold", halo=False)
    frame_and_grid(svg, v)

    # ---- side panel
    x0, x1 = 2560, 3500
    cx = (x0 + x1) / 2
    svg.a(f'<rect x="{x0}" y="40" width="{x1 - x0}" height="2500" fill="{BG}" stroke="{INK}" stroke-width="3"/>')
    svg.a(f'<rect x="{x0 + 12}" y="52" width="{x1 - x0 - 24}" height="200" fill="none" stroke="{INK}"/>')
    svg.text(cx, 95, "MASTER SITE PLAN  ·  SHEET 1 OF 3", size=13, spacing=6, halo=False, opacity=0.85)
    svg.text(cx, 150, REALM.upper(), size=50, weight="bold", spacing=6, font=SERIF, halo=False)
    svg.a(f'<line x1="{x0 + 80}" y1="172" x2="{x1 - 80}" y2="172" stroke="{INK}"/>')
    svg.text(cx, 200, REALM_TAGLINE, size=15, italic=True, font=SERIF, halo=False)
    svg.text(cx, 228, f"Surveyed for {YOU} - a living world of 2 km x 2 km, ready to build in 3D", size=12,
             italic=True, halo=False, opacity=0.9)
    compass(svg, x0 + 110, 360)
    how = ["HOW TO READ THIS MAP",
           "• 1 grid square = 128 m (A-P across, 1-16 down)",
           "• Thin lines join ground of equal height (5 m)",
           "  - lines close together = steep slope",
           "• Every 1 px of the heightmap = 1 metre",
           "• Heights: 0 m black ... 256 m white",
           "• Building IDs & sizes: sheets 2 and 3,",
           "  data/buildings.csv and the 3D model",
           f"• Start at landmark {next(l['n'] for l in W.landmarks if 'YOUR HOUSE' in l['name'])} - {YOUR_HOUSE}"]
    for i, ln in enumerate(how):
        svg.text(x0 + 210, 300 + i * 22, ln, size=13 if i else 15, anchor="start", weight="bold" if i == 0 else "normal",
                 halo=False, spacing=2 if i == 0 else 0)
    ly = legend(svg, x0 + 24, 530, x1 - x0 - 48)
    ky = ly + 30
    svg.text(x0 + 24, ky, "KEY TO LANDMARKS", size=16, anchor="start", weight="bold", spacing=4, halo=False)
    svg.a(f'<line x1="{x0 + 24}" y1="{ky + 8}" x2="{x1 - 24}" y2="{ky + 8}" stroke="{INK}"/>')
    n = len(W.landmarks)
    half = (n + 1) // 2
    for i, lm in enumerate(W.landmarks):
        col, row = divmod(i, half)
        sx = x0 + 34 + col * 460
        sy = ky + 34 + row * 25
        gx = chr(65 + int(lm["x"] // 128)) + str(int(lm["y"] // 128) + 1)
        svg.a(f'<circle cx="{sx}" cy="{sy - 4}" r="10" fill="none" stroke="{INK}"/>')
        svg.text(sx, sy, str(lm["n"]), size=10, weight="bold", halo=False)
        name = lm["name"] if len(lm["name"]) < 34 else lm["name"][:32] + "…"
        svg.text(sx + 18, sy, name, size=12, anchor="start", halo=False)
        svg.text(sx + 420, sy, gx, size=11, anchor="end", halo=False, opacity=0.75)
    sy = ky + 34 + half * 25 + 20
    scale_bar(svg, x0 + 30, sy, v, 500, 5)
    sy += 80
    svg.text(x0 + 24, sy, f"THE STORY OF {REALM.upper()}", size=16, anchor="start", weight="bold", spacing=4, halo=False)
    svg.a(f'<line x1="{x0 + 24}" y1="{sy + 8}" x2="{x1 - 24}" y2="{sy + 8}" stroke="{INK}"/>')
    num = {lm["name"]: lm["n"] for lm in W.landmarks}
    for i, ln in enumerate(wrap(lore_text(num), 92)):
        svg.text(x0 + 24, sy + 34 + i * 21, ln, size=14, anchor="start", italic=True, font=SERIF, halo=False)
    ny = sy + 34 + len(wrap(lore_text(num), 92)) * 21 + 30
    svg.text(x0 + 24, ny, "THE WORLD IN NUMBERS", size=16, anchor="start", weight="bold", spacing=4, halo=False)
    svg.a(f'<line x1="{x0 + 24}" y1="{ny + 8}" x2="{x1 - 24}" y2="{ny + 8}" stroke="{INK}"/>')
    road_km = sum(float(np.hypot(*np.diff(r["line"], axis=0).T).sum()) for r in W.roads) / 1000
    wall_m = sum(math.hypot(sg[2] - sg[0], sg[3] - sg[1]) for w in W.walls for sg in w["segments"])
    people = sum(1 for b in W.buildings if b.get("resident"))
    ha = sum(_area(f["poly"]) for f in W.fields if f["crop"] not in ("outline",)) / 1e4
    stats = [(f"{len(W.buildings)}", "buildings, each with an ID"), (f"{people}", "named households & trades"),
             (f"{len(W.trees):,}".replace(",", " "), "trees placed one by one"), (f"{road_km:.1f} km", "of roads, lanes & paths"),
             (f"{wall_m:,.0f} m".replace(",", " "), "of stone walls"), (f"{ha:.0f} ha", "of strip fields"),
             (f"{float(H.max()):.0f} m", f"highest ground ({NAMES['peak_n']})"), (f"{len(W.landmarks)}", "landmarks to discover")]
    for i, (big, small) in enumerate(stats):
        col, row = divmod(i, 4)
        sx, yy = x0 + 30 + col * 460, ny + 44 + row * 34
        svg.text(sx, yy, big, size=22, anchor="start", weight="bold", font=SERIF, halo=False)
        svg.text(sx + 130, yy - 2, small, size=13, anchor="start", halo=False)
    title_block(svg, x0 + 12, 2528 - 6 * 34, x1 - 12, 2528, [
        ("REALM", REALM), ("SURVEYED FOR", YOU), ("EXTENT", "2 048 m x 2 048 m  ·  elevation 0-256 m"),
        ("DATUM", "origin = NW corner · x east · y south"), ("DWG NO.", "AV-001  ·  REV B"), ("SHEET", "1 of 3")])
    return svg.done()


def detail_sheet(W, H, sheet_no, title, region, buildings_filter, notes, extra=None):
    x0r, y0r, x1r, y1r = region
    mw = 2300
    s = mw / (x1r - x0r)
    mh = (y1r - y0r) * s
    Wsvg, Hsvg = 3560, int(mh + 180)
    svg = SVG(Wsvg, Hsvg, f"{REALM} - {title}")
    svg.a(f'<rect width="{Wsvg}" height="{Hsvg}" fill="{BG}"/><rect width="{Wsvg}" height="{Hsvg}" fill="url(#g100)"/>')
    v = View(x0r, y0r, x1r, y1r, 70, 90, s)
    draw_map(svg, W, H, v, contour_step=1, index_step=5, detail=True, label_ids=True, shade_res=900)
    frame_and_grid(svg, v, step=20 if x1r - x0r < 500 else 40, labels=False)
    px0, px1 = 2460, 3500
    svg.a(f'<rect x="{px0}" y="40" width="{px1 - px0}" height="{Hsvg - 80}" fill="{BG}" stroke="{INK}" stroke-width="3"/>')
    svg.text((px0 + px1) / 2, 100, f"DETAIL SHEET {sheet_no} OF 3", size=13, spacing=6, halo=False, opacity=0.85)
    svg.text((px0 + px1) / 2, 150, title.upper(), size=40, weight="bold", spacing=4, font=SERIF, halo=False)
    svg.a(f'<line x1="{px0 + 60}" y1="170" x2="{px1 - 60}" y2="170" stroke="{INK}"/>')
    for i, ln in enumerate(notes):
        svg.text(px0 + 30, 205 + i * 21, ln, size=13, anchor="start", halo=False)
    y = 205 + len(notes) * 21 + 20
    cols = "ID     NAME                               W x D   WALL  ROOF  FL"
    svg.text(px0 + 30, y, cols, size=12, anchor="start", weight="bold", halo=False)
    svg.a(f'<line x1="{px0 + 30}" y1="{y + 7}" x2="{px1 - 30}" y2="{y + 7}" stroke="{INK}"/>')
    rows = [b for b in W.buildings if buildings_filter(b)]
    for i, b in enumerate(rows):
        yy = y + 26 + i * 19
        if yy > Hsvg - 120:
            svg.text(px0 + 30, yy, f"... {len(rows) - i} more in data/buildings.csv", size=12, anchor="start",
                     italic=True, halo=False)
            break
        nm = b["name"] if len(b["name"]) <= 34 else b["name"][:33] + "…"
        size = f'{b["w"]:.0f}x{b["d"]:.0f}' if b["shape"] != "round" else f'ø{b["w"]:.0f}'
        line = f'{b["id"].split("-")[1]:<6} {nm:<34} {size:>6} {b["h"]:>5.0f}m {b["roof"][:5]:<5} {b["floors"]}'
        svg.text(px0 + 30, yy, line.replace(" ", " "), size=12, anchor="start", halo=False)
    if extra:
        yy = y + 26 + len(rows) * 19 + 40
        svg.text(px0 + 30, yy, extra[0], size=15, anchor="start", weight="bold", spacing=3, halo=False)
        svg.a(f'<line x1="{px0 + 30}" y1="{yy + 8}" x2="{px1 - 30}" y2="{yy + 8}" stroke="{INK}"/>')
        for i, item in enumerate(extra[1]):
            col, row = i % 3, i // 3
            svg.text(px0 + 30 + col * 330, yy + 34 + row * 21, item, size=12, anchor="start", halo=False)
    scale_bar(svg, px0 + 30, Hsvg - 110, v, 100 if x1r - x0r < 500 else 200, 5)
    return svg.done()


def castle_sheet(W, H):
    cx, cy = 1024, 600
    return detail_sheet(W, H, 2, NAMES["castle"], (cx - 190, cy - 170, cx + 190, cy + 170),
                        lambda b: b["district"] == "C" and b["name"] != "Keep turret",
                        ["Numbers on the plan = building ID (C-###).",
                         "W x D = footprint in metres; WALL = wall height",
                         "above the highest ground under the building.",
                         "Contours every 1 m (bold every 5 m).",
                         "Plateau at 125 m; moat water at 122.5 m.",
                         "Curtain wall 11 m high, 3 m thick; inner",
                         "ward wall 13 m. Front-door dot shows facing."])


def town_sheet(W, H):
    tx, ty = 1024, 1080
    civic = {"church", "guildhall", "inn", "manor_house", "market_hall", "gatehouse", "smithy", "barn"}
    return detail_sheet(W, H, 3, f"{NAMES['town']} Town", (tx - 285, ty - 215, tx + 285, ty + 215),
                        lambda b: b["district"] == "T" and (b["type"] in civic),
                        ["Numbers on the plan = building ID (T-###).",
                         f"{sum(1 for b in W.buildings if b['district'] == 'T')} buildings inside the walls; every house",
                         "has a named resident and trade in buildings.csv.",
                         "Streets: High St 9 m, Market St 8 m, lanes 5 m.",
                         "Town wall 8 m high with 4 gatehouses.",
                         f"Your house: {YOUR_HOUSE}, on the market square.",
                         "Civic buildings listed below:"],
                        extra=("TRADES OF THE TOWN", _trades(W, "T")))


def _trades(W, district):
    from collections import Counter
    c = Counter(b["trade"] for b in W.buildings if b["district"] == district and b.get("trade"))
    return [f"{n:>3} x {t}" for t, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))]
