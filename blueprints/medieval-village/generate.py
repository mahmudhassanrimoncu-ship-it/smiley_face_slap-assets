#!/usr/bin/env python3
"""Generates medieval-village-blueprint.svg, a blueprint-style site plan of a
fictional medieval barony: a hilltop castle ringed by hills, a walled market
town, three villages, open-field farmland, a river with a watermill, an abbey,
forests and more.

    python3 generate.py          # writes medieval-village-blueprint.svg
"""
import math
import random
from pathlib import Path

W, H = 2400, 1600
MX0, MY0, MX1, MY1 = 40, 40, 1880, 1560          # map frame
BG = "#173b6c"
INK = "#e9f2ff"
WATER = "#23508e"
LABEL_FONT = "'Courier New', Courier, monospace"
TITLE_FONT = "Georgia, 'Times New Roman', serif"

out = []
a = out.append
rng = random.Random(1247)


def f(v):
    return f"{v:.1f}"


# ---------------------------------------------------------------- geometry
def _bez_controls(p0, p1, p2, p3):
    c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
    c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
    return c1, c2


def _seg_quads(pts, closed):
    n = len(pts)
    get = (lambda i: pts[i % n]) if closed else (lambda i: pts[max(0, min(n - 1, i))])
    for i in range(n if closed else n - 1):
        p0, p1, p2, p3 = get(i - 1), get(i), get(i + 1), get(i + 2)
        c1, c2 = _bez_controls(p0, p1, p2, p3)
        yield p1, c1, c2, p2


def smooth(pts, closed=False):
    d = f"M{f(pts[0][0])},{f(pts[0][1])}"
    for _, c1, c2, p2 in _seg_quads(pts, closed):
        d += f" C{f(c1[0])},{f(c1[1])} {f(c2[0])},{f(c2[1])} {f(p2[0])},{f(p2[1])}"
    return d + ("Z" if closed else "")


def dense(pts, closed=False, per=24):
    res = []
    for p1, c1, c2, p2 in _seg_quads(pts, closed):
        for j in range(per):
            t = j / per
            mt = 1 - t
            res.append((
                mt**3 * p1[0] + 3 * mt * mt * t * c1[0] + 3 * mt * t * t * c2[0] + t**3 * p2[0],
                mt**3 * p1[1] + 3 * mt * mt * t * c1[1] + 3 * mt * t * t * c2[1] + t**3 * p2[1],
            ))
    res.append(pts[0] if closed else pts[-1])
    return res


def along(dpts, step):
    """Points every `step` px along a dense polyline: (x, y, angle_deg)."""
    res, acc, nxt = [], 0.0, step / 2
    for (x0, y0), (x1, y1) in zip(dpts, dpts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        while seg > 0 and acc + seg >= nxt:
            t = (nxt - acc) / seg
            res.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t,
                        math.degrees(math.atan2(y1 - y0, x1 - x0))))
            nxt += step
        acc += seg
    return res


def min_dist(x, y, dpts):
    return min(math.hypot(x - px, y - py) for px, py in dpts)


class Blob:
    """Irregular closed shape; scaled copies nest, which makes contour rings."""

    def __init__(self, cx, cy, rx, ry, seed, amp=0.13):
        r = random.Random(seed)
        self.cx, self.cy, self.rx, self.ry, self.amp = cx, cy, rx, ry, amp
        self.ph = [r.uniform(0, 2 * math.pi) for _ in range(4)]

    def k(self, t):
        p = self.ph
        return 1 + self.amp * (0.55 * math.sin(2 * t + p[0]) + 0.3 * math.sin(3 * t + p[1])
                               + 0.18 * math.sin(5 * t + p[2]) + 0.1 * math.sin(7 * t + p[3]))

    def pt(self, t, scale=1.0, shift=(0, 0)):
        k = self.k(t) * scale
        return (self.cx + shift[0] * (1 - scale) + self.rx * k * math.cos(t),
                self.cy + shift[1] * (1 - scale) + self.ry * k * math.sin(t))

    def pts(self, scale=1.0, shift=(0, 0), n=40):
        return [self.pt(2 * math.pi * i / n, scale, shift) for i in range(n)]

    def path(self, scale=1.0, shift=(0, 0), n=40):
        return smooth(self.pts(scale, shift, n), True)

    def rel(self, x, y):
        dx, dy = (x - self.cx) / self.rx, (y - self.cy) / self.ry
        return math.hypot(dx, dy) / self.k(math.atan2(dy, dx))

    def inside(self, x, y, scale=1.0):
        return self.rel(x, y) < scale


# ---------------------------------------------------------------- drawing
def stroke_path(d, w, color=INK, extra=""):
    a(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" '
      f'stroke-linecap="round" stroke-linejoin="round" {extra}/>')


def cased(d, outer, inner, fill=BG):
    """Two-line 'cased' stroke: the blueprint convention for walls and roads."""
    stroke_path(d, outer)
    stroke_path(d, inner, fill)


def text(x, y, s, size=13, anchor="middle", weight="normal", italic=False,
         spacing=0, font=LABEL_FONT, halo=True, opacity=1, rotate=0):
    style = "italic" if italic else "normal"
    halo_attr = (f'stroke="{BG}" stroke-width="5" paint-order="stroke" stroke-linejoin="round" '
                 if halo else "")
    rot = f' transform="rotate({rotate} {f(x)} {f(y)})"' if rotate else ""
    a(f'<text x="{f(x)}" y="{f(y)}" font-family="{font}" font-size="{size}" '
      f'text-anchor="{anchor}" font-weight="{weight}" font-style="{style}" '
      f'letter-spacing="{spacing}" fill="{INK}" opacity="{opacity}" {halo_attr}{rot}>{s}</text>')


def place_name(x, y, name, sub=None, size=22):
    text(x, y, name, size=size, weight="bold", spacing=4, font=TITLE_FONT)
    if sub:
        text(x, y + size * 0.9, sub, size=11, spacing=2, italic=True, opacity=0.85)


def house(x, y, w, h, ang, hatch=False):
    fill = "url(#hatch)" if hatch else BG
    ridge = (f'<line x1="{f(-w / 2 + 2)}" y1="0" x2="{f(w / 2 - 2)}" y2="0"/>' if w >= h
             else f'<line x1="0" y1="{f(-h / 2 + 2)}" x2="0" y2="{f(h / 2 - 2)}"/>')
    a(f'<g transform="translate({f(x)} {f(y)}) rotate({f(ang)})" stroke="{INK}" stroke-width="1.2">'
      f'<rect x="{f(-w / 2)}" y="{f(-h / 2)}" width="{f(w)}" height="{f(h)}" fill="{fill}"/>'
      f'<g stroke-width="0.7" opacity="0.8">{ridge}</g></g>')


def tower(x, y, r=13):
    a(f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="{BG}" stroke="{INK}" stroke-width="2.2"/>')
    a(f'<circle cx="{f(x)}" cy="{f(y)}" r="{r * 0.62:.1f}" fill="none" stroke="{INK}" stroke-width="0.8"/>')


def callouts_marker(n, x, y, tx=None, ty=None):
    if tx is not None:
        a(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(tx)}" y2="{f(ty)}" stroke="{INK}" '
          f'stroke-width="0.9" stroke-dasharray="3 2"/>')
        a(f'<circle cx="{f(tx)}" cy="{f(ty)}" r="2.2" fill="{INK}"/>')
    a(f'<circle cx="{f(x)}" cy="{f(y)}" r="11" fill="{BG}" stroke="{INK}" stroke-width="1.4"/>')
    a(f'<text x="{f(x)}" y="{f(y + 4)}" font-family="{LABEL_FONT}" font-size="12" '
      f'font-weight="bold" text-anchor="middle" fill="{INK}">{n}</text>')


def tree(x, y, r):
    a(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{BG}" stroke="{INK}" stroke-width="1.1"/>')
    a(f'<path d="M{f(x - r * 0.45)},{f(y + r * 0.1)} q{f(r * 0.45)},{f(-r * 0.7)} {f(r * 0.9)},0" '
      f'fill="none" stroke="{INK}" stroke-width="0.7" opacity="0.7"/>')
    a(f'<circle cx="{f(x)}" cy="{f(y)}" r="1.1" fill="{INK}"/>')


def scatter(n_try, region, avoid, min_d, radius):
    placed = []
    for _ in range(n_try):
        x, y = rng.uniform(region[0], region[2]), rng.uniform(region[1], region[3])
        if any(fn(x, y) for fn in avoid):
            continue
        if all(math.hypot(x - px, y - py) > min_d for px, py, _ in placed):
            placed.append((x, y, rng.uniform(*radius)))
    return placed


# ================================================================= LAYOUT
CASTLE = (960, 395)
CASTLE_HILL = Blob(960, 410, 320, 250, seed=21, amp=0.07)
MOAT = Blob(960, 400, 195, 160, seed=11, amp=0.05)
TOWN = Blob(960, 1000, 280, 195, seed=31, amp=0.06)

HILLS = [  # cx, cy, rx, ry, rings, seed, peak height
    (560, 230, 250, 160, 5, 1, 212),
    (850, 95, 230, 100, 4, 2, 188),
    (1180, 110, 240, 100, 4, 3, 196),
    (1500, 270, 210, 145, 5, 4, 224),
    (330, 560, 170, 140, 4, 5, 164),
    (1380, 520, 140, 110, 4, 6, 151),
]

RIVER = [(1910, 150), (1800, 300), (1740, 470), (1700, 640), (1630, 800), (1590, 960),
         (1610, 1120), (1570, 1300), (1610, 1450), (1590, 1610)]
RIVER_D = dense(RIVER)
STREAM = [(1330, 190), (1250, 275), (1190, 330), (1150, 380)]

GATE_N = TOWN.pt(-math.pi / 2)
GATE_S = TOWN.pt(math.pi / 2)
GATE_W = TOWN.pt(math.pi)
GATE_E = TOWN.pt(0)

ROAD_CASTLE = [(960, 607), (935, 670), (985, 740), (955, 790), GATE_N]
ROAD_WEST = [GATE_W, (560, 995), (450, 975), (340, 985), (220, 1000), (30, 990)]
ROAD_EAST = [GATE_E, (1380, 1000), (1500, 990), (1600, 985), (1720, 975), (1800, 985), (1890, 995)]
ROAD_SOUTH = [GATE_S, (950, 1290), (970, 1380), (985, 1480), (1000, 1570)]
LANE_ABBEY = [(940, 680), (830, 705), (720, 725), (662, 738)]
LANE_TILT = [(975, 722), (1040, 722), (1098, 722)]
LANE_MILL = [(1720, 975), (1700, 880), (1700, 820)]
ROAD_NW = [(560, 745), (450, 715), (250, 700), (30, 680)]
TRACKS = [
    [(380, 990), (395, 1150), (370, 1300), (395, 1570)],
    [(985, 1480), (850, 1500), (640, 1520), (560, 1570)],
    [(1760, 980), (1740, 1150), (1760, 1300), (1740, 1570)],
    [(970, 1380), (1100, 1330), (1330, 1330), (1480, 1360)],
]

# ================================================================= SVG
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
a('<title>Medieval Village — Blueprint Site Plan</title>')
a(f'''<defs>
  <pattern id="g20" width="20" height="20" patternUnits="userSpaceOnUse">
    <path d="M20 0H0V20" fill="none" stroke="{INK}" stroke-width="0.5" opacity="0.10"/></pattern>
  <pattern id="g100" width="100" height="100" patternUnits="userSpaceOnUse">
    <rect width="100" height="100" fill="url(#g20)"/>
    <path d="M100 0H0V100" fill="none" stroke="{INK}" stroke-width="0.9" opacity="0.16"/></pattern>
  <pattern id="furrow" width="6" height="6" patternUnits="userSpaceOnUse">
    <line x1="3" y1="0" x2="3" y2="6" stroke="{INK}" stroke-width="0.8" opacity="0.6"/></pattern>
  <pattern id="furrowH" width="7" height="7" patternUnits="userSpaceOnUse">
    <line x1="0" y1="3.5" x2="7" y2="3.5" stroke="{INK}" stroke-width="0.8" opacity="0.6"/></pattern>
  <pattern id="fallow" width="9" height="9" patternUnits="userSpaceOnUse">
    <circle cx="2" cy="2" r="0.9" fill="{INK}" opacity="0.7"/>
    <circle cx="6.5" cy="6.5" r="0.9" fill="{INK}" opacity="0.7"/></pattern>
  <pattern id="cobble" width="8" height="8" patternUnits="userSpaceOnUse">
    <circle cx="4" cy="4" r="0.7" fill="{INK}" opacity="0.45"/></pattern>
  <pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="5" height="5" fill="{BG}"/>
    <line x1="0" y1="0" x2="0" y2="5" stroke="{INK}" stroke-width="0.9" opacity="0.8"/></pattern>
  <pattern id="waves" width="18" height="8" patternUnits="userSpaceOnUse">
    <rect width="18" height="8" fill="{WATER}"/>
    <path d="M1 5 q2.5 -3 5 0 t5 0" fill="none" stroke="{INK}" stroke-width="0.7" opacity="0.55"/></pattern>
  <pattern id="grass" width="26" height="20" patternUnits="userSpaceOnUse">
    <path d="M4 8 l2 4 l2 -4 M17 18 l2 -4 l2 4 M14 5 l1.5 3 l1.5 -3" fill="none"
      stroke="{INK}" stroke-width="0.8" opacity="0.6"/></pattern>
  <radialGradient id="vignette" cx="50%" cy="50%" r="75%">
    <stop offset="60%" stop-color="#000" stop-opacity="0"/>
    <stop offset="100%" stop-color="#000" stop-opacity="0.35"/></radialGradient>
  <clipPath id="mapclip"><rect x="{MX0}" y="{MY0}" width="{MX1 - MX0}" height="{MY1 - MY0}"/></clipPath>
</defs>''')

# sheet + grid
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<rect width="{W}" height="{H}" fill="url(#g100)"/>')

a('<g clip-path="url(#mapclip)">')

# ---------------------------------------------------------------- hills
a('<g id="hills">')
for cx, cy, rx, ry, rings, seed, peak in HILLS:
    b = Blob(cx, cy, rx, ry, seed)
    shift = (cx + random.Random(seed).uniform(-30, 30), cy + random.Random(seed + 9).uniform(-20, 20))
    scales = [1 - i * (0.8 / rings) for i in range(rings)]
    for i, s in enumerate(scales):
        bold = i % 2 == 0
        a(f'<path d="{b.path(s, shift)}" fill="{INK}" fill-opacity="0.035" stroke="{INK}" '
          f'stroke-width="{1.5 if bold else 0.8}" opacity="{0.75 if bold else 0.55}"/>')
    px, py = (shift[0] + cx) / 2 + 30, (shift[1] + cy) / 2 + 26
    a(f'<path d="M{f(px)},{f(py - 6)} l5,9 h-10z" fill="none" stroke="{INK}" stroke-width="1.1"/>')
    text(px + 9, py + 3, f"{peak} m", size=10, anchor="start", opacity=0.85)
# castle mount
for s in (1, 0.86, 0.72):
    a(f'<path d="{CASTLE_HILL.path(s)}" fill="{INK}" fill-opacity="0.04" stroke="{INK}" '
      f'stroke-width="{1.5 if s == 1 else 0.9}" opacity="0.7"/>')
a('</g>')

# ---------------------------------------------------------------- forests, pasture, orchard
river_near = lambda x, y: min_dist(x, y, RIVER_D[::3]) < 32
trees = scatter(900, (45, 45, 320, 480), [lambda x, y: Blob(560, 230, 250, 160, 1).inside(x, y, 0.55)],
                21, (7, 11))
trees += scatter(700, (1690, 45, 1880, 400), [river_near, lambda x, y: Blob(1500, 270, 210, 145, 4).inside(x, y, 0.5)],
                 21, (7, 11))
trees += scatter(300, (1660, 1495, 1880, 1560), [river_near], 20, (6, 10))
trees += scatter(200, (45, 1495, 300, 1560), [], 20, (6, 10))
for x, y, r in trees:
    tree(x, y, r)

PASTURE = Blob(250, 820, 150, 70, seed=41)
a(f'<path d="{PASTURE.path()}" fill="url(#grass)" stroke="{INK}" stroke-width="1" stroke-dasharray="6 4"/>')
for sx, sy in [(200, 805), (230, 835), (300, 810), (275, 850), (330, 835)]:  # sheep
    a(f'<ellipse cx="{sx}" cy="{sy}" rx="5" ry="3.2" fill="{BG}" stroke="{INK}" stroke-width="0.9"/>')
    a(f'<circle cx="{sx + 5.5}" cy="{sy - 1}" r="1.6" fill="{INK}"/>')

for i, x in enumerate(range(1735, 1870, 22)):  # orchard
    for j, y in enumerate(range(700, 860, 22)):
        ox = 11 if j % 2 else 0
        if x + ox < 1872:
            a(f'<circle cx="{x + ox}" cy="{y}" r="5.5" fill="{BG}" stroke="{INK}" stroke-width="0.9"/>')
            a(f'<circle cx="{x + ox}" cy="{y}" r="1" fill="{INK}"/>')
a(f'<rect x="1722" y="688" width="155" height="170" fill="none" stroke="{INK}" stroke-width="1" '
  f'stroke-dasharray="2 3" opacity="0.8"/>')

# ---------------------------------------------------------------- open fields
FIELDS = [  # cx, cy, w, h, angle
    (165, 1170, 220, 160, -8), (410, 1150, 210, 140, 6), (170, 1395, 230, 200, 4),
    (430, 1395, 220, 190, -5), (725, 1300, 170, 160, 8), (720, 1455, 190, 100, -4),
    (1200, 1235, 220, 150, -9), (1235, 1430, 250, 140, 5), (1755, 1185, 180, 150, 5),
    (1760, 1400, 190, 180, -6),
]
a('<g id="fields">')
for cx, cy, w, h, ang in FIELDS:
    a(f'<g transform="translate({cx} {cy}) rotate({ang})">')
    x = -w / 2
    vertical = rng.random() < 0.6
    while x < w / 2 - 6:
        sw = min(rng.choice([18, 22, 26, 30]), w / 2 - x)
        roll = rng.random()
        fill = "url(#fallow)" if roll < 0.15 else ("url(#furrowH)" if roll < 0.3 else "url(#furrow)")
        if vertical:
            a(f'<rect x="{f(x)}" y="{f(-h / 2)}" width="{f(sw)}" height="{f(h)}" fill="{fill}" '
              f'stroke="{INK}" stroke-width="0.9" opacity="0.95"/>')
        else:
            yy = -h / 2 + (x + w / 2) * h / w
            a(f'<rect x="{f(-w / 2)}" y="{f(yy)}" width="{f(w)}" height="{f(sw * h / w)}" fill="{fill}" '
              f'stroke="{INK}" stroke-width="0.9" opacity="0.95"/>')
        x += sw
    a(f'<rect x="{f(-w / 2)}" y="{f(-h / 2)}" width="{w}" height="{h}" fill="none" stroke="{INK}" '
      f'stroke-width="2"/>')
    a('</g>')
a('</g>')

# hedgerow tracks between the fields
for t in TRACKS:
    d = smooth(t)
    stroke_path(d, 7)
    stroke_path(d, 5, BG)
    stroke_path(d, 1, INK, 'stroke-dasharray="5 5" opacity="0.6"')

# ---------------------------------------------------------------- water
river_d = smooth(RIVER)
stroke_path(river_d, 34)
stroke_path(river_d, 30, WATER)
stroke_path(river_d, 1, INK, 'stroke-dasharray="14 10" opacity="0.5"')
stroke_path(river_d, 1, INK, 'stroke-dasharray="6 18" opacity="0.4" transform="translate(-7 2)"')
stream_d = smooth(STREAM)
stroke_path(stream_d, 10)
stroke_path(stream_d, 7, WATER)

a(f'<path d="{MOAT.path()}" fill="url(#waves)" stroke="{INK}" stroke-width="2"/>')
a(f'<path d="{MOAT.path(0.8)}" fill="{BG}" stroke="{INK}" stroke-width="2"/>')
a(f'<path d="{MOAT.path(0.8)}" fill="{INK}" fill-opacity="0.05" stroke="none"/>')

# ---------------------------------------------------------------- roads
for r, (o, i) in [(ROAD_NW, (16, 13)), (ROAD_WEST, (20, 16)), (ROAD_EAST, (20, 16)),
                  (ROAD_SOUTH, (20, 16)), (ROAD_CASTLE, (22, 18)), (LANE_ABBEY, (12, 9)),
                  (LANE_TILT, (12, 9)), (LANE_MILL, (12, 9))]:
    stroke_path(smooth(r), o)
for r, (o, i) in [(ROAD_NW, (16, 13)), (ROAD_WEST, (20, 16)), (ROAD_EAST, (20, 16)),
                  (ROAD_SOUTH, (20, 16)), (ROAD_CASTLE, (22, 18)), (LANE_ABBEY, (12, 9)),
                  (LANE_TILT, (12, 9)), (LANE_MILL, (12, 9))]:
    stroke_path(smooth(r), i, BG)
for r in (ROAD_WEST, ROAD_EAST, ROAD_SOUTH, ROAD_CASTLE):
    stroke_path(smooth(r), 0.8, INK, 'stroke-dasharray="2 8" opacity="0.55"')

# bridge where the east road crosses the river
east_d = dense(ROAD_EAST)
bx, by = min(east_d, key=lambda p: min_dist(p[0], p[1], RIVER_D[::2]))
BRIDGE = (bx, by)
a(f'<g transform="translate({f(bx)} {f(by)}) rotate(-3)" stroke="{INK}">'
  f'<rect x="-34" y="-12" width="68" height="24" fill="{BG}" stroke-width="2"/>'
  f'<line x1="-34" y1="-7" x2="34" y2="-7" stroke-width="0.8"/>'
  f'<line x1="-34" y1="7" x2="34" y2="7" stroke-width="0.8"/>'
  + "".join(f'<rect x="{x - 3}" y="-16" width="6" height="32" fill="{BG}" stroke-width="1.2"/>'
            for x in (-20, 0, 20))
  + '</g>')

# ---------------------------------------------------------------- market town
a('<g id="town">')
ring_lane = TOWN.path(0.76)
stroke_path(ring_lane, 11)
stroke_path(ring_lane, 8, BG)
for p0, p1 in [((GATE_N[0], GATE_N[1]), (GATE_S[0], GATE_S[1])), (GATE_W, GATE_E)]:
    d = f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}"
    stroke_path(d, 20)
for p0, p1 in [(GATE_N, GATE_S), (GATE_W, GATE_E)]:
    stroke_path(f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}", 16, BG)
# cross lanes
for d in ["M840,850 L870,1150", "M1080,850 L1050,1150", "M760,920 L1160,930", "M770,1080 L1150,1075"]:
    stroke_path(d, 9)
    stroke_path(d, 6.5, BG)

SQUARE = (878, 948, 1042, 1052)
CHURCH_ZONE = (1043, 905, 1158, 988)
GUILD_ZONE = (884, 902, 950, 946)


def in_box(x, y, box, pad=0):
    return box[0] - pad < x < box[2] + pad and box[1] - pad < y < box[3] + pad


lanes_dense = [dense([(840, 850), (870, 1150)]), dense([(1080, 850), (1050, 1150)]),
               dense([(760, 920), (1160, 930)]), dense([(770, 1080), (1150, 1075)])]
for gx in range(690, 1240, 21):
    for gy in range(800, 1210, 21):
        x, y = gx + rng.uniform(-2, 2), gy + rng.uniform(-2, 2)
        rel = TOWN.rel(x, y)
        if rel > 0.9 or 0.68 < rel < 0.84:
            continue
        if abs(x - 960) < 20 or abs(y - 1000) < 20:
            continue
        if in_box(x, y, SQUARE, 10) or in_box(x, y, CHURCH_ZONE, 4) or in_box(x, y, GUILD_ZONE, 4):
            continue
        if any(min_dist(x, y, ld[::2]) < 14 for ld in lanes_dense):
            continue
        if rng.random() < 0.88:
            w, h = rng.uniform(13, 16), rng.uniform(15, 18)
            if rng.random() < 0.5:
                w, h = h, w
            house(x, y, w, h, rng.uniform(-3, 3), hatch=rng.random() < 0.12)

# market square
x0, y0, x1, y1 = SQUARE
a(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="{BG}" stroke="{INK}" stroke-width="1.6"/>')
a(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="url(#cobble)"/>')
for sx, sy in [(896, 964), (920, 964), (1000, 964), (1024, 964), (896, 1036), (920, 1036),
               (1000, 1036), (1024, 1036), (896, 990), (896, 1012), (1024, 990), (1024, 1012)]:
    a(f'<g stroke="{INK}" stroke-width="1"><rect x="{sx - 8}" y="{sy - 6}" width="16" height="12" fill="{BG}"/>'
      f'<path d="M{sx - 8},{sy - 6} L{sx + 8},{sy + 6} M{sx + 8},{sy - 6} L{sx - 8},{sy + 6}" stroke-width="0.6"/></g>')
a(f'<circle cx="960" cy="1000" r="13" fill="{BG}" stroke="{INK}" stroke-width="2"/>')
a(f'<circle cx="960" cy="1000" r="8" fill="none" stroke="{INK}" stroke-width="0.8"/>')
a(f'<path d="M960,992 V1008 M952,1000 H968" stroke="{INK}" stroke-width="1.6"/>')
a(f'<circle cx="985" cy="1028" r="6" fill="url(#waves)" stroke="{INK}" stroke-width="1.4"/>')  # well

# parish church (cruciform, apse to the east)
a(f'<rect x="{CHURCH_ZONE[0]}" y="{CHURCH_ZONE[1]}" width="{CHURCH_ZONE[2] - CHURCH_ZONE[0]}" '
  f'height="{CHURCH_ZONE[3] - CHURCH_ZONE[1]}" fill="none" stroke="{INK}" stroke-width="1" stroke-dasharray="4 3"/>')
a(f'<g stroke="{INK}" stroke-width="1.8" fill="url(#hatch)">'
  f'<path d="M1068,934 H1132 A12,12 0 0 1 1132,958 H1068 Z"/>'
  f'<rect x="1101" y="918" width="16" height="56"/>'
  f'<rect x="1050" y="936" width="18" height="20" fill="{BG}"/>'
  f'<path d="M1050,936 L1068,956 M1068,936 L1050,956" stroke-width="0.8"/></g>')
for gx, gy in [(1060, 972), (1075, 976), (1090, 972), (1130, 976), (1145, 970), (1140, 918), (1060, 918)]:
    a(f'<path d="M{gx},{gy - 4} V{gy + 4} M{gx - 3},{gy - 1} H{gx + 3}" stroke="{INK}" stroke-width="0.9"/>')
# guildhall with arcade
a(f'<rect x="890" y="908" width="54" height="32" fill="url(#hatch)" stroke="{INK}" stroke-width="1.8"/>')
for cx in range(896, 944, 8):
    a(f'<circle cx="{cx}" cy="944" r="1.6" fill="{INK}"/>')

# town wall, towers and gates
wall_pts = TOWN.pts(1.0, n=40)
cased(smooth(wall_pts, True), 10, 4.5)
for i, (x, y) in enumerate(TOWN.pts(1.0, n=20)):
    if i % 5:
        tower(x, y, 8)
for gx, gy, ang in [(*GATE_N, 0), (*GATE_S, 0), (*GATE_W, 90), (*GATE_E, 90)]:
    a(f'<g transform="translate({f(gx)} {f(gy)}) rotate({ang})" stroke="{INK}" stroke-width="1.8" fill="{BG}">'
      f'<rect x="-11" y="-12" width="22" height="24"/>'
      f'<line x1="-4" y1="-12" x2="-4" y2="12" stroke-width="0.8"/>'
      f'<line x1="4" y1="-12" x2="4" y2="12" stroke-width="0.8"/>'
      f'<rect x="-21" y="-9" width="10" height="18"/><rect x="11" y="-9" width="10" height="18"/></g>')
a('</g>')

# ---------------------------------------------------------------- villages
def village(road, x_or_y_range, axis, seed, depth=42, skip=lambda x, y: False):
    vr = random.Random(seed)
    for x, y, ang in along(dense(road), 30):
        v = x if axis == "x" else y
        if not (x_or_y_range[0] <= v <= x_or_y_range[1]):
            continue
        for side in (-1, 1):
            if vr.random() > 0.78:
                continue
            nx, ny = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
            hx, hy = x + side * 25 * nx, y + side * 25 * ny
            if skip(hx, hy):
                continue
            # croft (back garden plot)
            a(f'<g transform="translate({f(x)} {f(y)}) rotate({f(ang)})">'
              f'<rect x="-13" y="{f(min(side * 32, side * (32 + depth)))}" width="26" height="{depth}" '
              f'fill="none" stroke="{INK}" stroke-width="0.8" stroke-dasharray="3 3" opacity="0.75"/></g>')
            house(hx, hy, vr.uniform(18, 24), vr.uniform(11, 14), ang + vr.uniform(-4, 4),
                  hatch=vr.random() < 0.15)


GREEN = Blob(395, 1050, 48, 24, seed=51)
village(ROAD_WEST, (235, 540), "x", 61, skip=lambda x, y: GREEN.inside(x, y, 1.6))
a(f'<path d="{GREEN.path()}" fill="url(#grass)" stroke="{INK}" stroke-width="1.2"/>')
a(f'<ellipse cx="408" cy="1052" rx="14" ry="8" fill="url(#waves)" stroke="{INK}" stroke-width="1.2"/>')
village(ROAD_EAST, (1650, 1870), "x", 62)
village(ROAD_SOUTH, (1300, 1530), "y", 63)
# village chapels
for cx, cy, ang in [(300, 940, -3), (1000, 1405, 80)]:
    a(f'<g transform="translate({cx} {cy}) rotate({ang})" stroke="{INK}" stroke-width="1.6">'
      f'<path d="M-16,-8 H10 A8,8 0 0 1 10,8 H-16 Z" fill="url(#hatch)"/>'
      f'<rect x="-24" y="-6" width="8" height="12" fill="{BG}"/></g>')

# ---------------------------------------------------------------- castle
cx, cy = CASTLE
outer = [(-120, -62), (-60, -105), (60, -105), (120, -62), (132, 40), (72, 95), (-72, 95), (-132, 40)]
outer = [(cx + x, cy + y) for x, y in outer]
poly = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in outer) + "Z"
a(f'<path d="{poly}" fill="{INK}" fill-opacity="0.04" stroke="none"/>')
cased(poly, 11, 5)
for x, y in outer:
    tower(x, y, 14)
# inner ward
inner = [(900, 305), (1020, 305), (1020, 425), (900, 425)]
ipoly = "M" + " L".join(f"{x},{y}" for x, y in inner) + "Z"
cased(ipoly, 8, 3.5)
for x, y in inner:
    tower(x, y, 10)
a(f'<rect x="952" y="419" width="16" height="12" fill="{BG}" stroke="{INK}" stroke-width="1.4"/>')
# keep with corner turrets
a(f'<rect x="935" y="322" width="50" height="50" fill="url(#hatch)" stroke="{INK}" stroke-width="2.6"/>')
a(f'<rect x="945" y="332" width="30" height="30" fill="none" stroke="{INK}" stroke-width="1"/>')
for tx, ty in [(935, 322), (985, 322), (935, 372), (985, 372)]:
    a(f'<rect x="{tx - 6}" y="{ty - 6}" width="12" height="12" fill="{BG}" stroke="{INK}" stroke-width="1.6"/>')
# great hall & chapel in the inner ward
a(f'<rect x="976" y="382" width="36" height="32" fill="{BG}" stroke="{INK}" stroke-width="1.6"/>')
a(f'<line x1="976" y1="398" x2="1012" y2="398" stroke="{INK}" stroke-width="0.7"/>')
a(f'<path d="M908,386 H926 A7,7 0 0 1 926,400 H908 Z" fill="url(#hatch)" stroke="{INK}" stroke-width="1.4"/>')
# outer bailey buildings
for x, y, w, h in [(850, 440, 42, 18), (1030, 440, 45, 18), (852, 322, 22, 40), (1046, 318, 22, 34)]:
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{BG}" stroke="{INK}" stroke-width="1.4"/>')
    a(f'<line x1="{x + 2}" y1="{y + h / 2}" x2="{x + w - 2}" y2="{y + h / 2}" stroke="{INK}" stroke-width="0.6"/>'
      if w > h else
      f'<line x1="{x + w / 2}" y1="{y + 2}" x2="{x + w / 2}" y2="{y + h - 2}" stroke="{INK}" stroke-width="0.6"/>')
a(f'<circle cx="1060" cy="380" r="7" fill="url(#waves)" stroke="{INK}" stroke-width="1.4"/>')
# gatehouse, drawbridge, barbican
a(f'<rect x="950" y="476" width="20" height="38" fill="{BG}" stroke="{INK}" stroke-width="1.8"/>')
tower(938, 495, 12)
tower(982, 495, 12)
a(f'<rect x="951" y="514" width="18" height="52" fill="{BG}" stroke="{INK}" stroke-width="1.6"/>')
for y in range(520, 566, 6):
    a(f'<line x1="951" y1="{y}" x2="969" y2="{y}" stroke="{INK}" stroke-width="0.6"/>')
cased("M934,606 V572 H986 V606", 9, 4)
tower(934, 572, 8)
tower(986, 572, 8)

# ---------------------------------------------------------------- abbey & fishponds
PRECINCT = Blob(600, 760, 125, 78, seed=71, amp=0.08)
a(f'<path d="{PRECINCT.path()}" fill="none" stroke="{INK}" stroke-width="1.6" stroke-dasharray="8 4"/>')
a(f'<g stroke="{INK}" stroke-width="1.8">'
  f'<path d="M538,702 H640 A11,11 0 0 1 640,724 H538 Z" fill="url(#hatch)"/>'
  f'<rect x="585" y="728" width="54" height="54" fill="{BG}"/>'
  f'<rect x="597" y="740" width="30" height="30" fill="url(#grass)" stroke-width="1"/>'
  f'<rect x="562" y="728" width="20" height="62" fill="{BG}"/>'
  f'<rect x="642" y="738" width="20" height="24" fill="{BG}"/>'
  f'<rect x="590" y="786" width="44" height="16" fill="{BG}"/></g>')
for px, py in [(650, 812), (668, 838), (690, 864)]:
    a(f'<rect x="{px}" y="{py}" width="44" height="18" rx="7" fill="url(#waves)" stroke="{INK}" stroke-width="1.4"/>')

# ---------------------------------------------------------------- tiltyard
a(f'<g stroke="{INK}"><rect x="1098" y="698" width="176" height="48" fill="{BG}" stroke-width="1.8"/>'
  f'<line x1="1115" y1="722" x2="1257" y2="722" stroke-width="2.5"/>'
  f'<rect x="1150" y="684" width="70" height="12" fill="url(#hatch)" stroke-width="1.2"/>'
  f'<rect x="1150" y="748" width="70" height="12" fill="url(#hatch)" stroke-width="1.2"/></g>')

# ---------------------------------------------------------------- watermill
a(f'<g stroke="{INK}"><path d="M1640,760 C1660,790 1660,830 1636,850" fill="none" stroke-width="7"/>'
  f'<path d="M1640,760 C1660,790 1660,830 1636,850" fill="none" stroke="{WATER}" stroke-width="4"/>'
  f'<rect x="1668" y="782" width="44" height="34" fill="url(#hatch)" stroke-width="1.8"/>'
  f'<rect x="1650" y="790" width="14" height="22" fill="{BG}" stroke-width="1.4"/>'
  f'<path d="M1650,795 H1664 M1650,801 H1664 M1650,807 H1664" stroke-width="0.8"/></g>')

# ---------------------------------------------------------------- windmill
wx, wy = 590, 1250
a(f'<circle cx="{wx}" cy="{wy}" r="24" fill="none" stroke="{INK}" stroke-width="1" stroke-dasharray="3 3"/>')
a(f'<g transform="translate({wx} {wy}) rotate(20)" stroke="{INK}" stroke-width="1.2" fill="{BG}">'
  + "".join(f'<rect x="-3" y="-30" width="6" height="22" transform="rotate({r})"/>' for r in (0, 90, 180, 270))
  + '<rect x="-7" y="-7" width="14" height="14" stroke-width="1.8"/></g>')

# ---------------------------------------------------------------- watchtowers & quarry
WATCH = [(560, 215), (1500, 255), (300, 545)]
for x, y in WATCH:
    a(f'<g stroke="{INK}"><rect x="{x - 13}" y="{y - 13}" width="26" height="26" fill="{BG}" stroke-width="2.2"/>'
      f'<rect x="{x - 8}" y="{y - 8}" width="16" height="16" fill="none" stroke-width="0.8"/>'
      f'<path d="M{x},{y - 5} L{x + 1.5},{y - 1.5} L{x + 5},{y} L{x + 1.5},{y + 1.5} L{x},{y + 5} '
      f'L{x - 1.5},{y + 1.5} L{x - 5},{y} L{x - 1.5},{y - 1.5}Z" fill="{INK}" stroke="none"/></g>')
stroke_path(smooth([(560, 228), (600, 330), (700, 420), (790, 470), (842, 500)]), 1.3, INK, 'stroke-dasharray="6 4"')
stroke_path(smooth([(1500, 268), (1420, 380), (1300, 450), (1150, 520), (1080, 548)]), 1.3, INK, 'stroke-dasharray="6 4"')
QUARRY = Blob(1290, 590, 34, 20, seed=81, amp=0.15)
a(f'<path d="{QUARRY.path()}" fill="{BG}" stroke="{INK}" stroke-width="1.8"/>')
for i in range(18):
    t = 2 * math.pi * i / 18
    x0q, y0q = QUARRY.pt(t)
    x1q, y1q = QUARRY.pt(t, 0.72)
    a(f'<line x1="{f(x0q)}" y1="{f(y0q)}" x2="{f(x1q)}" y2="{f(y1q)}" stroke="{INK}" stroke-width="1"/>')

# ---------------------------------------------------------------- labels
place_name(960, 205, "ASHFORD CASTLE", "seat of the Baron, upon Castle Mount", size=24)
place_name(1340, 845, "ASHFORD", "walled market town", size=22)
place_name(395, 905, "WESTBROOK", "village", size=19)
place_name(1785, 1078, "EASTMERE", "village", size=19)
place_name(1080, 1535, "SOUTHFOLD", "hamlet", size=19)
text(210, 760, "COMMON PASTURE", size=11, spacing=2, italic=True)
text(175, 300, "WILDWOOD", size=16, spacing=6, weight="bold", font=TITLE_FONT)
text(1790, 395, "KING'S CHASE", size=14, spacing=4, weight="bold", font=TITLE_FONT)
text(1800, 685, "ORCHARD", size=11, spacing=2, italic=True)
text(300, 1270, "NORTH FIELD", size=12, spacing=3, italic=True)
text(1220, 1340, "SOUTH FIELD", size=12, spacing=3, italic=True)
text(1760, 1300, "EAST FIELD", size=12, spacing=3, italic=True)
text(1675, 560, "RIVER ASH", size=15, spacing=5, italic=True, rotate=-72)
text(1612, 1235, "RIVER ASH", size=15, spacing=5, italic=True, rotate=95)
text(1250, 255, "Castle Brook", size=11, italic=True, rotate=-45)
text(1186, 676, "TILTYARD", size=10, spacing=2)
text(600, 684, "ST. HILDA'S ABBEY", size=12, spacing=2, weight="bold")
text(1290, 636, "QUARRY", size=10, spacing=2, italic=True)
text(140, 676, "to Northgate →", size=10, italic=True, opacity=0.8, rotate=0)
text(70, 1016, "← to Westmarch", size=10, italic=True, opacity=0.8, anchor="start")
text(1866, 940, "to the Coast →", size=10, italic=True, opacity=0.8, anchor="end")

CALLOUTS = [
    (1, 892, 262, 935, 330), (2, 1040, 262, 1012, 306), (3, 900, 520, 945, 500), (4, 1022, 600, 988, 590),
    (5, 1135, 400, 1148, 420), (6, 850, 1000, 900, 990), (7, 1180, 900, 1117, 930), (8, 870, 880, 900, 910),
    (9, 690, 1110, 702, 1080), (10, 1690, 740, 1680, 785), (11, 560, 1300, 585, 1260), (12, 610, 175, 572, 205),
    (13, 1555, 215, 1512, 244), (14, 520, 790, 568, 770), (15, 1300, 690, 1274, 708), (16, 745, 880, 725, 870),
    (17, 452, 1085, 430, 1065), (18, 1590, 1045, BRIDGE[0], BRIDGE[1] + 14), (19, 1236, 592, 1258, 590),
    (20, 340, 520, 312, 535),
]
for n, x, y, tx, ty in CALLOUTS:
    callouts_marker(n, x, y, tx, ty)

a('</g>')  # end map clip

# map frame
a(f'<rect x="{MX0}" y="{MY0}" width="{MX1 - MX0}" height="{MY1 - MY0}" fill="none" stroke="{INK}" stroke-width="3"/>')
a(f'<rect x="{MX0 - 8}" y="{MY0 - 8}" width="{MX1 - MX0 + 16}" height="{MY1 - MY0 + 16}" fill="none" '
  f'stroke="{INK}" stroke-width="1"/>')
for i, gx in enumerate(range(MX0, MX1, 200)):
    a(f'<line x1="{gx}" y1="{MY0 - 8}" x2="{gx}" y2="{MY0}" stroke="{INK}" stroke-width="1"/>')
    a(f'<line x1="{gx}" y1="{MY1}" x2="{gx}" y2="{MY1 + 8}" stroke="{INK}" stroke-width="1"/>')
    if gx + 100 < MX1:
        a(f'<text x="{gx + 100}" y="{MY0 - 12}" font-family="{LABEL_FONT}" font-size="11" fill="{INK}" '
          f'text-anchor="middle" opacity="0.8">{chr(65 + i)}</text>')
        a(f'<text x="{gx + 100}" y="{MY1 + 22}" font-family="{LABEL_FONT}" font-size="11" fill="{INK}" '
          f'text-anchor="middle" opacity="0.8">{chr(65 + i)}</text>')
for i, gy in enumerate(range(MY0, MY1, 200)):
    a(f'<line x1="{MX0 - 8}" y1="{gy}" x2="{MX0}" y2="{gy}" stroke="{INK}" stroke-width="1"/>')
    if gy + 100 < MY1:
        a(f'<text x="{MX0 - 20}" y="{gy + 104}" font-family="{LABEL_FONT}" font-size="11" fill="{INK}" '
          f'text-anchor="middle" opacity="0.8">{i + 1}</text>')

# ================================================================= PANEL
PX0, PX1 = 1905, 2360
PW = PX1 - PX0
PC = (PX0 + PX1) / 2
a(f'<rect x="{PX0}" y="{MY0}" width="{PW}" height="{MY1 - MY0}" fill="{BG}" stroke="{INK}" stroke-width="3"/>')

# title
a(f'<rect x="{PX0 + 10}" y="{MY0 + 10}" width="{PW - 20}" height="180" fill="none" stroke="{INK}" stroke-width="1"/>')
text(PC, 88, "SITE PLAN", size=14, spacing=8, halo=False, opacity=0.85)
text(PC, 128, "ASHFORD VALE", size=36, weight="bold", spacing=5, font=TITLE_FONT, halo=False)
a(f'<line x1="{PX0 + 50}" y1="146" x2="{PX1 - 50}" y2="146" stroke="{INK}" stroke-width="1"/>')
text(PC, 168, "A Medieval Barony — Castle, Market Town,", size=12, italic=True, halo=False)
text(PC, 186, "Villages &amp; Demesne Lands", size=12, italic=True, halo=False)

# compass rose
rx, ry = PC, 330
a(f'<g transform="translate({rx} {ry})" stroke="{INK}">'
  f'<circle r="78" fill="none" stroke-width="1"/><circle r="70" fill="none" stroke-width="0.6" stroke-dasharray="2 3"/>'
  + "".join(f'<line x1="0" y1="-70" x2="0" y2="-62" transform="rotate({d})" stroke-width="1"/>' for d in range(0, 360, 15))
  + '<path d="M0,-66 L10,-10 L0,0Z" fill="#e9f2ff"/><path d="M0,-66 L-10,-10 L0,0Z" fill="none" stroke-width="1.2"/>'
  '<path d="M0,66 L10,10 L0,0Z" fill="none" stroke-width="1.2"/><path d="M0,66 L-10,10 L0,0Z" fill="#e9f2ff"/>'
  '<path d="M66,0 L10,-10 L0,0Z" fill="#e9f2ff"/><path d="M66,0 L10,10 L0,0Z" fill="none" stroke-width="1.2"/>'
  '<path d="M-66,0 L-10,10 L0,0Z" fill="#e9f2ff"/><path d="M-66,0 L-10,-10 L0,0Z" fill="none" stroke-width="1.2"/>'
  '<circle r="4" fill="#173b6c" stroke-width="1.4"/></g>')
for lbl, dx, dy in [("N", 0, -88), ("S", 0, 100), ("E", 94, 5), ("W", -94, 5)]:
    text(rx + dx, ry + dy, lbl, size=16, weight="bold", font=TITLE_FONT, halo=False)

# legend
LY = 450
text(PX0 + 22, LY, "LEGEND", size=15, anchor="start", weight="bold", spacing=4, halo=False)
a(f'<line x1="{PX0 + 22}" y1="{LY + 8}" x2="{PX1 - 22}" y2="{LY + 8}" stroke="{INK}" stroke-width="1"/>')
legend = [
    ("Contour line (hills)", "contour"), ("Curtain / town wall with tower", "wall"),
    ("Road · lane", "road"), ("Field track &amp; hedgerow", "track"), ("River · moat · pond", "water"),
    ("Dwelling (hatched: hall or shop)", "house"), ("Croft (garden plot)", "croft"),
    ("Strip fields — ploughed / fallow", "field"), ("Woodland", "tree"),
    ("Pasture / green", "grass"), ("Orchard", "orchard"), ("Spot height", "spot"),
]
for i, (label, kind) in enumerate(legend):
    y = LY + 34 + i * 30
    sx = PX0 + 30
    if kind == "contour":
        a(f'<path d="M{sx},{y + 4} q15,-14 30,-4 t30,0" fill="none" stroke="{INK}" stroke-width="1.5"/>'
          f'<path d="M{sx + 8},{y + 8} q12,-8 22,-2 t22,0" fill="none" stroke="{INK}" stroke-width="0.8" opacity="0.6"/>')
    elif kind == "wall":
        cased(f"M{sx},{y} H{sx + 60}", 10, 4.5)
        tower(sx + 30, y, 8)
    elif kind == "road":
        cased(f"M{sx},{y - 4} H{sx + 32}", 18, 14)
        cased(f"M{sx + 42},{y - 4} H{sx + 60}", 11, 8)
    elif kind == "track":
        stroke_path(f"M{sx},{y - 4} H{sx + 60}", 7)
        stroke_path(f"M{sx},{y - 4} H{sx + 60}", 5, BG)
        stroke_path(f"M{sx},{y - 4} H{sx + 60}", 1, INK, 'stroke-dasharray="5 5" opacity="0.6"')
    elif kind == "water":
        a(f'<rect x="{sx}" y="{y - 12}" width="60" height="16" fill="url(#waves)" stroke="{INK}" stroke-width="1.4"/>')
    elif kind == "house":
        house(sx + 15, y - 4, 22, 13, 0)
        house(sx + 45, y - 4, 22, 13, 0, hatch=True)
    elif kind == "croft":
        a(f'<rect x="{sx + 10}" y="{y - 14}" width="40" height="20" fill="none" stroke="{INK}" '
          f'stroke-width="0.8" stroke-dasharray="3 3"/>')
    elif kind == "field":
        a(f'<rect x="{sx}" y="{y - 13}" width="20" height="18" fill="url(#furrow)" stroke="{INK}" stroke-width="0.9"/>'
          f'<rect x="{sx + 20}" y="{y - 13}" width="20" height="18" fill="url(#furrowH)" stroke="{INK}" stroke-width="0.9"/>'
          f'<rect x="{sx + 40}" y="{y - 13}" width="20" height="18" fill="url(#fallow)" stroke="{INK}" stroke-width="0.9"/>')
    elif kind == "tree":
        for k in range(3):
            tree(sx + 10 + k * 20, y - 4, 8)
    elif kind == "grass":
        a(f'<rect x="{sx}" y="{y - 13}" width="60" height="18" fill="url(#grass)" stroke="{INK}" '
          f'stroke-width="1" stroke-dasharray="6 4"/>')
    elif kind == "orchard":
        for k in range(4):
            a(f'<circle cx="{sx + 8 + k * 15}" cy="{y - 4}" r="5" fill="{BG}" stroke="{INK}" stroke-width="0.9"/>')
    elif kind == "spot":
        a(f'<path d="M{sx + 25},{y - 10} l5,9 h-10z" fill="none" stroke="{INK}" stroke-width="1.1"/>')
        text(sx + 34, y - 2, "212 m", size=10, anchor="start", halo=False)
    text(sx + 76, y, label, size=12, anchor="start", halo=False)

# key to numbered features
KY = LY + 34 + len(legend) * 30 + 10
text(PX0 + 22, KY, "KEY", size=15, anchor="start", weight="bold", spacing=4, halo=False)
a(f'<line x1="{PX0 + 22}" y1="{KY + 8}" x2="{PX1 - 22}" y2="{KY + 8}" stroke="{INK}" stroke-width="1"/>')
KEY = [
    "Keep (great tower)", "Inner ward &amp; great hall", "Gatehouse &amp; drawbridge", "Barbican",
    "Moat (fed by Castle Brook)", "Market square &amp; cross", "Parish church &amp; yard", "Guildhall",
    "Town wall &amp; four gates", "Watermill &amp; mill race", "Windmill on mound",
    "Watchtower — Raven Hill", "Watchtower — Beacon Hill", "St. Hilda's Abbey",
    "Tiltyard (jousting list)", "Abbey fishponds", "Village green &amp; pond", "Ash Bridge",
    "Stone quarry", "Watchtower — West Tor",
]
for i, item in enumerate(KEY):
    y = KY + 30 + i * 21
    a(f'<circle cx="{PX0 + 34}" cy="{y - 4}" r="9" fill="none" stroke="{INK}" stroke-width="1"/>')
    a(f'<text x="{PX0 + 34}" y="{y}" font-family="{LABEL_FONT}" font-size="10" font-weight="bold" '
      f'text-anchor="middle" fill="{INK}">{i + 1}</text>')
    text(PX0 + 52, y, item, size=12, anchor="start", halo=False)

# scale bar (100 px = 50 m)
SY = KY + 30 + len(KEY) * 21 + 14
text(PX0 + 22, SY, "SCALE  1 : 2 500 (approx.)", size=11, anchor="start", spacing=1, halo=False)
bx0 = PX0 + 30
for k in range(4):
    fill = INK if k % 2 == 0 else BG
    a(f'<rect x="{bx0 + k * 100}" y="{SY + 10}" width="100" height="8" fill="{fill}" stroke="{INK}" stroke-width="1"/>')
for k, lbl in enumerate(["0", "50", "100", "150", "200 m"]):
    text(bx0 + k * 100, SY + 34, lbl, size=10, halo=False)

# title block
TY = SY + 52
rows = [("DRAWN", "Royal Surveyor"), ("PROJECT", "Ashford Vale Survey"), ("DWG NO.", "MV-001  ·  REV A"),
        ("SHEET", "1 of 1"), ("DATE", "Anno Domini MCCCXLII")]
rh = (MY1 - 10 - TY) / len(rows)
a(f'<rect x="{PX0 + 10}" y="{TY}" width="{PW - 20}" height="{MY1 - 10 - TY}" fill="none" stroke="{INK}" stroke-width="1.4"/>')
for i, (k, v) in enumerate(rows):
    y = TY + i * rh
    if i:
        a(f'<line x1="{PX0 + 10}" y1="{f(y)}" x2="{PX1 - 10}" y2="{f(y)}" stroke="{INK}" stroke-width="0.8"/>')
    text(PX0 + 22, y + rh / 2 + 4, k, size=10, anchor="start", spacing=2, halo=False, opacity=0.8)
    text(PX0 + 120, y + rh / 2 + 4, v, size=12, anchor="start", halo=False)
a(f'<line x1="{PX0 + 108}" y1="{TY}" x2="{PX0 + 108}" y2="{MY1 - 10}" stroke="{INK}" stroke-width="0.8"/>')

# vignette for a printed-blueprint feel
a(f'<rect width="{W}" height="{H}" fill="url(#vignette)" pointer-events="none"/>')
a('</svg>')

dest = Path(__file__).with_name("medieval-village-blueprint.svg")
dest.write_text("\n".join(out))
print(f"wrote {dest} ({dest.stat().st_size // 1024} KB)")
