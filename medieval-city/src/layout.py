"""The city model: every street, river, wall, building, monument and stone.

All positions are map coordinates in metres (see geom.py). Nothing here
depends on the terrain; elevations are attached later by `attach_heights`.
"""
import math
import random

import numpy as np

from config import NAMES, SEED, WORLD_SIZE, YOU, YOUR_HOUSE
from geom import (along, dist_to, ellipse_pts, point_in_poly, rect_corners, rects_overlap,
                  resample, spline)

N = NAMES
FIRST = ("Wat Hob Agnes Matilda Gilbert Alys Robin Joan Hugh Edith Piers Maud Simon Isabel Geoffrey "
         "Margery Ralph Cecily Walter Emma Adam Beatrice Thomas Rose Osbert Godwin Elena Roger Juliana "
         "Nicholas Avice Henry Ivetta Richard Amice Stephen Hawise Martin Sybil Laurence Mabel Jordan "
         "Petronilla Baldwin Ida Alan Felice Odo Christiana").split()
TOWN_TRADES = ("baker butcher cooper chandler weaver tailor cobbler potter fletcher bowyer brewer carpenter "
               "mason glover saddler goldsmith apothecary scribe draper spicer wheelwright thatcher "
               "dyer fuller tinker locksmith barber-surgeon cutler pewterer ropemaker").split()
VILLAGE_TRADES = ("ploughman cottar shepherd reeve beekeeper swineherd hayward carter thatcher "
                  "woodward smith-hand dairymaid ale-wife woodcutter hedger").split()


class World:
    def __init__(self):
        self.rng = random.Random(SEED)
        self.buildings, self.walls, self.props = [], [], []
        self.roads, self.waters, self.fields, self.crofts = [], [], [], []
        self.zones, self.forests, self.orchards, self.pastures = [], [], [], []
        self.ridges, self.peaks, self.pits = [], [], []
        self.labels, self.landmarks, self.trees, self.bridges = [], [], [], []
        self._grid = {}
        self._ids = {}
        self.size = WORLD_SIZE

    # ----------------------------------------------------------- registry helpers
    def _next_id(self, district):
        self._ids[district] = self._ids.get(district, 0) + 1
        return f"{district}-{self._ids[district]:04d}"

    def _cells(self, corners):
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        for gx in range(int(min(xs) // 48), int(max(xs) // 48) + 1):
            for gy in range(int(min(ys) // 48), int(max(ys) // 48) + 1):
                yield gx, gy

    def blocked(self, corners):
        seen = set()
        for cell in self._cells(corners):
            for idx, other in self._grid.get(cell, ()):
                if idx in seen:
                    continue
                seen.add(idx)
                if rects_overlap(corners, other):
                    return True
        return False

    def reserve(self, corners):
        self._rc = getattr(self, "_rc", 0) + 1
        idx = self._rc
        for cell in self._cells(corners):
            self._grid.setdefault(cell, []).append((idx, corners))

    def reserve_box(self, x0, y0, x1, y1):
        self.reserve([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    def near_line(self, corners, lines, pad):
        xs = np.array([c[0] for c in corners] + [sum(c[0] for c in corners) / 4])
        ys = np.array([c[1] for c in corners] + [sum(c[1] for c in corners) / 4])
        for ln, half in lines:
            if (dist_to(ln, xs, ys) < half + pad).any():
                return True
        return False

    def building(self, district, kind, name, x, y, w, d, heading=0.0, h=5.0, roof="gable", roof_h=None,
                 material="timber", floors=1, check=True, pad=0.6, avoid_lines=None, group=None,
                 shape="rect", **extra):
        corners = rect_corners(x, y, w + 2 * pad, d + 2 * pad, heading)
        if check:
            if self.blocked(corners):
                if not extra.get("optional") and kind not in ("house", "shop", "longhouse", "barn", "farmhouse",
                                                               "workshop", "tenement", "stable", "storehouse"):
                    print(f"  ! could not place {name} ({kind}) - something is in the way")
                return None
            if avoid_lines and self.near_line(corners, avoid_lines, 0.5):
                return None
        self.reserve(corners)
        if roof_h is None:
            roof_h = {"gable": min(w, d) * 0.55, "hip": min(w, d) * 0.45, "cone": w * 0.9,
                      "spire": w * 1.8}.get(roof, 0.0)
        b = dict(id=self._next_id(district), name=name, type=kind, district=district, group=group or name,
                 shape=shape, x=round(x, 2), y=round(y, 2), w=round(w, 2), d=round(d, 2),
                 heading=round(heading % 360, 1), h=round(h, 2), roof=roof, roof_h=round(roof_h, 2),
                 material=material, floors=floors)
        extra.pop("optional", None)
        b.update(extra)
        self.buildings.append(b)
        return b

    def tower(self, district, name, x, y, r, h, roof="crenel", material="stone", group=None):
        return self.building(district, "tower", name, x, y, 2 * r, 2 * r, 0, h, roof,
                             material=material, check=False, shape="round", group=group)

    def wall(self, name, kind, pts, height, thickness, closed=False, gaps=(), gap_r=7.0, material="stone"):
        pts = [tuple(p) for p in pts]
        seq = pts + [pts[0]] if closed else pts
        segs = []
        for p, q in zip(seq, seq[1:]):
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            keep = [(0.0, 1.0)]                       # cut a gap-sized opening out of the segment
            for gx, gy in gaps:
                t = ((gx - p[0]) * (q[0] - p[0]) + (gy - p[1]) * (q[1] - p[1])) / (L * L)
                px, py = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
                if math.hypot(gx - px, gy - py) > gap_r or t < -gap_r / L or t > 1 + gap_r / L:
                    continue
                c0, c1 = t - gap_r / L, t + gap_r / L
                keep = [iv for a, b in keep for iv in ((a, min(b, c0)), (max(a, c1), b)) if iv[1] - iv[0] > 1e-3]
            for a, b in keep:
                s0 = (p[0] + (q[0] - p[0]) * a, p[1] + (q[1] - p[1]) * a)
                s1 = (p[0] + (q[0] - p[0]) * b, p[1] + (q[1] - p[1]) * b)
                segs.append([round(s0[0], 2), round(s0[1], 2), round(s1[0], 2), round(s1[1], 2)])
                self.reserve(_seg_corners(s0, s1, thickness + 1.0))
        self.walls.append(dict(id=f"WALL-{len(self.walls) + 1:02d}", name=name, kind=kind, height=height,
                               thickness=thickness, material=material, segments=segs))

    def prop(self, kind, x, y, heading=0.0, **extra):
        p = dict(type=kind, x=round(x, 2), y=round(y, 2), heading=round(heading % 360, 1))
        p.update(extra)
        self.props.append(p)
        return p

    def road(self, name, kind, ctrl, width, surface="dirt"):
        line = spline(ctrl, step=3.0)
        r = dict(id=f"ROAD-{len(self.roads) + 1:02d}", name=name, kind=kind, width=width, surface=surface,
                 ctrl=[tuple(map(float, c)) for c in ctrl], line=line)
        self.roads.append(r)
        return r

    def landmark(self, name, x, y, desc):
        self.landmarks.append(dict(n=len(self.landmarks) + 1, name=name, x=x, y=y, desc=desc))

    def road_lines(self, kinds=None):
        return [(r["line"], r["width"] / 2) for r in self.roads if kinds is None or r["kind"] in kinds]

    def water_lines(self):
        return [(w["line"], w["width"] / 2 + 2) for w in self.waters if w["kind"] in ("river", "stream")]

    def person(self, trades):
        return self.rng.choice(FIRST), self.rng.choice(trades)


def _seg_corners(p, q, t):
    ang = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    return rect_corners((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, L, t, ang)


def heading_facing(street_angle, side):
    """Heading for a building on `side` (+1/-1) of a street so its front faces the street."""
    return math.degrees(street_angle) + (0 if side > 0 else 180)


# =============================================================== Stonehallow
from PIL import Image, ImageDraw  # noqa: E402

CITY = (1024.0, 1070.0, 830.0, 750.0)        # wall ellipse: cx, cy, rx, ry
CASTLE = (1024.0, 420.0)
HENGE = (1024.0, 905.0)
MARKET = (894.0, 1135.0, 1154.0, 1255.0)
CLOSE = (560.0, 960.0, 800.0, 1160.0)
GARDENS = (1230.0, 400.0, 1520.0, 625.0)
CROWN_SQ = (954.0, 610.0, 1094.0, 680.0)
PARK = (520.0, 790.0, 190.0, 110.0)           # ellipse
UNIVERSITY = (400.0, 1370.0, 580.0, 1500.0)
HOSPITAL = (1250.0, 1565.0, 1380.0, 1650.0)
ABBEY = (700.0, 1565.0, 880.0, 1715.0)
MOUNDS = (1100.0, 1630.0, 1300.0, 1730.0)
FRIARY_W = (300.0, 860.0, 420.0, 975.0)
FRIARY_E = (1620.0, 1150.0, 1740.0, 1255.0)
CORN = (979.0, 1500.0, 1069.0, 1560.0)
HAY = (685.0, 638.0, 755.0, 688.0)
FISH = (1255.0, 1266.0, 1325.0, 1300.0)
K = 2048 / 2048.0                             # raster pixels per metre (1 m)

TRADES = ("baker butcher cooper chandler weaver tailor cobbler potter fletcher bowyer brewer carpenter mason "
          "glover saddler goldsmith apothecary scribe draper spicer wheelwright dyer fuller tinker locksmith "
          "barber-surgeon cutler pewterer ropemaker mercer vintner furrier hatter bookbinder limner "
          "bellfounder armourer clockmaker glazier jeweller cheesemonger fishmonger pie-seller tanner "
          "parchmenter stonecarver lute-maker money-changer notary herbalist candlemaker").split()
GUILDS = ["Mercers", "Goldsmiths", "Weavers", "Vintners", "Masons", "Fishmongers", "Drapers", "Bakers"]


def city_q(x, y):
    cx, cy, rx, ry = CITY
    return np.hypot((np.asarray(x) - cx) / rx, (np.asarray(y) - cy) / ry)


def build_layout():
    W = World()
    W.city_ellipse = CITY
    W.ditch_q = 1.035
    W.squares, W.churchyards, W.paved_polys, W.green_polys, W.groves = [], [], [], [], []
    W.earthworks, W.plateaus, W.pads = [], [], []
    _landforms(W)
    _water(W)
    _zones_raster(W)
    _main_streets(W)
    _castle(W)
    _city_wall(W)
    _henge(W)
    _prehistory(W)
    _centre(W)
    _cathedral(W)
    _gardens_and_park(W)
    _institutions(W)
    _generic_streets(W)
    _churches_and_guilds(W)
    _houses(W)
    _outside(W)
    _vegetation(W)
    _labels(W)
    return W


# ------------------------------------------------------------------ land & water
def _landforms(W):
    W.ridges = [
        dict(pts=spline([(-50, 170), (300, 140), (700, 120), (1024, 130), (1400, 110), (1800, 150), (2100, 190)], step=8),
             h=70, w=200),
        dict(pts=spline([(-40, 300), (60, 600), (40, 900)], step=8), h=30, w=140),
        dict(pts=spline([(2090, 320), (1990, 620), (2010, 900)], step=8), h=30, w=140),
    ]
    W.peaks = [
        dict(name="Crownback", x=1024, y=150, h=55, rx=260, ry=150),
        dict(name="Windmill Hill", x=520, y=170, h=40, rx=200, ry=140),
        dict(name="Beacon Knoll", x=1560, y=160, h=45, rx=200, ry=140),
        dict(name="South Down", x=1024, y=1980, h=14, rx=500, ry=180),
    ]
    W.pits = []
    W.plateaus = [dict(x=CASTLE[0], y=CASTLE[1], r=205, z=118, base=72, fall=150)]
    W.pads = [(1024, 645, 90, 50, 0.9), (1024, 1195, 150, 75, 0.9), (680, 1060, 140, 115, 0.8),
              (1375, 515, 160, 125, 0.7), (1024, 1530, 60, 45, 0.8)]


def _water(W):
    river = spline([(-30, 1230), (180, 1250), (380, 1290), (600, 1325), (820, 1345), (1024, 1352), (1230, 1345),
                    (1430, 1320), (1640, 1330), (1830, 1375), (2080, 1420)], step=4)
    W.waters.append(dict(id="WATER-01", name=N["river"], kind="river", width=56, line=river, reach=110))
    brook = spline([(720, -10), (690, 200), (650, 400), (600, 560), (560, 690), (505, 800), (500, 930),
                    (480, 1050), (470, 1190), (455, 1290)], step=4)
    W.waters.append(dict(id="WATER-02", name=N["brook"], kind="stream", width=6, line=brook, reach=26))
    for i, (px, py, rx, ry) in enumerate([(1300, 600, 26, 12), (1460, 600, 26, 12), (585, 770, 22, 14)]):
        W.waters.append(dict(id=f"WATER-P{i + 1}", name="Garden pond" if i < 2 else "Park mere", kind="pond",
                             cx=px, cy=py, rx=rx, ry=ry, line=np.array(ellipse_pts(px, py, rx, ry, 28))))


def _zones_raster(W):
    """Rasterised 'no generic streets/houses here' mask, 1 px = 1 m."""
    img = Image.new("L", (2049, 2049), 0)
    d = ImageDraw.Draw(img)
    cx, cy = CASTLE
    d.ellipse([cx - 220, cy - 210, cx + 220, cy + 205], fill=255)
    hx, hy = HENGE
    d.ellipse([hx - 232, hy - 232, hx + 232, hy + 232], fill=255)
    for box in (MARKET, CLOSE, GARDENS, CROWN_SQ, UNIVERSITY, HOSPITAL, ABBEY, MOUNDS, FRIARY_W, FRIARY_E,
                CORN, HAY, FISH):
        d.rectangle(box, fill=255)
    px, py, rx, ry = PARK
    d.ellipse([px - rx, py - ry, px + rx, py + ry], fill=255)
    river = W.waters[0]
    d.line([tuple(p) for p in river["line"]], fill=255, width=int(river["width"] + 16))
    quay = [p for p in river["line"] if 1100 < p[0] < 1720]
    d.line([(x, y - 30) for x, y in quay], fill=255, width=44)        # quayside apron
    brook = W.waters[1]
    d.line([tuple(p) for p in brook["line"]], fill=255, width=14)
    W.zone_img = img
    W.zone = np.asarray(img) > 0


def _free(W, xs, ys, street_ok=False):
    xs = np.clip(np.asarray(xs, dtype=float), 0, 2048).astype(int)
    ys = np.clip(np.asarray(ys, dtype=float), 0, 2048).astype(int)
    bad = W.zone[ys, xs]
    if not street_ok:
        bad = bad | W.street_mask[ys, xs]
    return ~bad


# ------------------------------------------------------------------ streets
def _main_streets(W):
    cx, cy, rx, ry = CITY
    gate = lambda deg: (cx + rx * math.cos(math.radians(deg)), cy + ry * math.sin(math.radians(deg)))
    beyond = lambda deg, k=1.16: (cx + rx * k * math.cos(math.radians(deg)), cy + ry * k * math.sin(math.radians(deg)))
    hx, hy = HENGE
    ring = lambda deg, r=225: (hx + r * math.cos(math.radians(deg)), hy + r * math.sin(math.radians(deg)))
    W.gates = {"East Gate": gate(0), "South Gate": gate(90), "West Gate": gate(180), "North-East Gate": gate(315),
               "South-West Gate": gate(135), "North-West Gate": gate(225), "South-East Gate": gate(45)}
    ringpts = [ring(a) for a in range(0, 360, 6)]
    W.roads.append(dict(id="ROAD-01", name="The Stone Ring", kind="street", width=12, surface="cobble",
                        ctrl=ringpts, line=resample(ringpts + [ringpts[0]], 3.0), closed=True))
    W.road("Crown Way", "street", [(1024, 588), (1024, 612)], 14, "cobble")
    W.road("Henge Gate Walk (north)", "street", [(1024, 680), ring(270)], 12, "cobble")
    W.road("Market Way", "street", [ring(90), (1024, 1135)], 14, "cobble")
    W.road("Bridge Street", "street", [(1024, 1255), (1024, 1352), (1024, 1500)], 12, "cobble")
    W.road("South Street", "street", [(1024, 1560), (1018, 1680), gate(90), beyond(90)], 10, "cobble")
    W.road("East Street", "street", [ring(-15), (1500, 900), (1700, 990), gate(0), beyond(0, 1.25)], 10, "cobble")
    W.road("West Street", "street", [ring(186), (640, 920), (420, 990), gate(180), beyond(180, 1.25)], 10, "cobble")
    W.road("Palace Street", "street", [ring(-60), (1250, 680), (1400, 655), gate(315), beyond(315)], 10, "cobble")
    W.road("Forest Street", "street", [ring(240), (800, 690), (720, 663), (560, 600), gate(225), beyond(225)], 10, "cobble")
    W.road("Mill Street", "street", [ring(150), (845, 1200), (800, 1345), (640, 1480), gate(135), beyond(135)], 10, "cobble")
    W.road("Harbour Road", "street", [(1069, 1530), (1300, 1520), (1500, 1560), gate(45), beyond(45)], 10, "cobble")
    W.road("Westgate Road", "road", [beyond(180, 1.25), (-10, 1050)], 8)
    W.road("Coast Road", "road", [beyond(0, 1.25), (2060, 1100)], 8)
    W.road("Forest Road", "road", [beyond(225), (180, 380), (-10, 300)], 7)
    W.road("Palace Road", "road", [beyond(315), (1880, 340), (2060, 260)], 7)
    W.road("South Road", "road", [beyond(90), (1024, 2060)], 8)
    W.road("Mill Road", "road", [beyond(135), (200, 1840), (-10, 1900)], 7)
    W.road("Harbour Down Road", "road", [beyond(45), (1880, 1860), (2060, 1960)], 7)
    W.road("Ridge Road", "track", [(1024, 230), (700, 240), (520, 200), (300, 230), (-10, 260)], 4)
    W.road("Beacon Track", "track", [(1024, 230), (1300, 210), (1560, 180)], 4)
    W.road("Castle Back Path", "path", [(1024, 290), (1024, 230)], 2)
    # streets are drawn into a mask so houses can be packed against them quickly
    W.main_street_count = len(W.roads)


def _street_mask(W):
    img = Image.new("L", (2049, 2049), 0)
    d = ImageDraw.Draw(img)
    for r in W.roads:
        pts = [tuple(p) for p in r["line"]]
        d.line(pts, fill=255, width=max(2, int(round(r["width"] + 1.2))), joint="curve")
        rr = (r["width"] + 1.2) / 2
        for x, y in (pts[0], pts[-1]):
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)
    for w in W.waters:
        if w["kind"] == "stream":
            d.line([tuple(p) for p in w["line"]], fill=255, width=12)
    for s in W.squares:
        d.rectangle(s["box"], fill=255)
    W.street_mask = np.asarray(img) > 0


def _generic_streets(W):
    """A spider's web of ring streets and radial lanes, cut wherever a protected place stands."""
    cx, cy, rx, ry = CITY
    rng = W.rng
    cands = []
    for k, s in enumerate([0.43, 0.5, 0.57, 0.64, 0.71, 0.78, 0.85, 0.92]):
        pts = []
        for a in range(0, 360, 4):
            t = math.radians(a)
            j = 1 + 0.015 * math.sin(3 * t + k) + 0.01 * math.sin(7 * t + 2 * k)
            pts.append((cx + rx * s * j * math.cos(t), cy + ry * s * j * math.sin(t)))
        cands.append((f"Ring Street {k + 1}", resample(pts + [pts[0]], 3.0), 7 if k % 2 == 0 else 5))
    for i in range(30):
        a = math.radians(i * 12 + 4)
        ctrl = []
        for s in (0.33, 0.55, 0.75, 0.96):
            ja = a + rng.uniform(-0.035, 0.035)
            ctrl.append((cx + rx * s * math.cos(ja), cy + ry * s * math.sin(ja)))
        cands.append((f"Radial Lane {i + 1}", spline(ctrl, step=3.0), 7))
    for i in range(30):
        a = math.radians(i * 12 + 10)
        for s0, s1 in ((0.5, 0.64), (0.64, 0.78), (0.78, 0.92)):
            ctrl = [(cx + rx * s * math.cos(a + rng.uniform(-0.02, 0.02)), cy + ry * s * math.sin(a + rng.uniform(-0.02, 0.02)))
                    for s in (s0, (s0 + s1) / 2, s1)]
            cands.append((f"Lane {i + 1}-{int(s0 * 100)}", spline(ctrl, step=3.0), 5))
    names = iter(STREET_NAMES)
    for base, line, width in cands:
        ok = _free(W, line[:, 0], line[:, 1], street_ok=True) & (city_q(line[:, 0], line[:, 1]) < 0.955)
        start = None
        for i in range(len(line) + 1):
            if i < len(line) and ok[i]:
                if start is None:
                    start = i
                continue
            if start is not None and i - start >= 12:
                seg = line[start:i]
                nm = next(names, base)
                W.roads.append(dict(id=f"ROAD-{len(W.roads) + 1:03d}", name=nm, kind="street", width=width,
                                    surface="cobble", ctrl=[tuple(seg[0]), tuple(seg[-1])], line=seg))
            start = None
    _street_mask(W)


STREET_NAMES = [
    "Threadneedle Row", "Candle Lane", "Bell Street", "Saddlers' Row", "Wool Street", "Pudding Lane", "Gold Street",
    "Shambles", "Cooper's Row", "Silver Street", "Ink Lane", "Tanners' Walk", "Hatters' Lane", "Pie Corner",
    "Lantern Street", "Weavers' Row", "Glovers' Lane", "Spice Street", "Rope Walk", "Chandlers' Row", "Parchment Lane",
    "Pilgrims' Way", "Ironmonger Lane", "Fullers' Row", "Dyers' Street", "Mint Street", "Cheapside", "Milk Street",
    "Wood Street", "Bread Street", "Honey Lane", "Friday Street", "Old Change", "Cornhill", "Poultry", "Garlick Hill",
    "Stone Street", "Menhir Lane", "Barrow Row", "Henge Walk", "Serpent Lane", "Raven Row", "Crown Street",
    "Bishop's Lane", "Abbot's Walk", "Scholars' Row", "Lamb Street", "Hart Street", "Swan Lane", "Fish Street",
    "Mill Row", "Water Lane", "Quay Street", "Ship Lane", "Anchor Row", "Salt Street", "Corn Street", "Hay Lane",
    "Cattle Row", "Horse Street", "Forge Lane", "Bellfounders' Row", "Clock Lane", "Lute Lane", "Painters' Row",
    "Glass Street", "Pewter Lane", "Jewel Street", "Kettle Row", "Oven Lane", "Brewers' Row", "Malt Street",
    "Vine Street", "Cellar Lane", "Hood Street", "Mantle Row", "Thimble Lane", "Needle Street", "Button Row",
    "Lace Lane", "Feather Street", "Quill Lane", "Lamp Row", "Wick Street", "Barrel Lane", "Hoop Row",
] + [f"Little Lane {i}" for i in range(1, 200)]


# ------------------------------------------------------------------ castle
def _castle(W):
    cx, cy = CASTLE
    L = lambda x, y: (cx + x, cy + y)
    b = W.building
    outer = [L(*p) for p in [(-160, -95), (-90, -135), (90, -135), (160, -95), (175, 40), (110, 125), (-110, 125),
                             (-175, 40)]]
    W.wall("Crownhold outer curtain", "curtain", outer, 18, 5, closed=True, gaps=[L(0, 125)], gap_r=12)
    towers = []
    for i, p in enumerate(outer):
        q = outer[(i + 1) % len(outer)]
        towers += [p, ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)]
    for k, (x, y) in enumerate(towers):
        if math.hypot(x - L(0, 125)[0], y - L(0, 125)[1]) < 20:
            continue
        W.tower("C", f"Outer Tower {k + 1}", x, y, 9 if k % 2 == 0 else 7, 26 if k % 2 == 0 else 22)
    inner = [L(-100, -85), L(100, -85), L(108, 55), L(-108, 55)]
    W.wall("Crownhold inner curtain", "inner", inner, 24, 5, closed=True, gaps=[L(0, 55)], gap_r=8)
    for k, p in enumerate(inner):
        q = inner[(k + 1) % 4]
        W.tower("C", ["King's Tower", "Queen's Tower", "Treasury Tower", "Chapel Tower"][k], *p, 10, 32)
        mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        if k != 2:
            W.tower("C", "Inner wall tower", *mid, 7, 28)
    b("C", "keep", N["keep"], *L(0, -28), 34, 34, 180, 46, "crenel", material="stone", floors=7, check=False)
    for dx, dy in [(-17, -17), (17, -17), (-17, 17), (17, 17)]:
        W.tower("C", "Crown Tower turret", *L(dx, -28 + dy), 4.5, 54, group=N["keep"])
    b("C", "hall", "Great Hall of the Kings", *L(-66, -22), 52, 18, 90, 18, "gable", material="stone", floors=1)
    b("C", "chapel", "Royal Chapel of St. Stephen", *L(66, -40), 32, 13, 0, 16, "gable", material="stone")
    b("C", "palace", "Royal Apartments", *L(0, 32), 70, 15, 180, 16, "hip", material="stone", floors=3)
    b("C", "kitchen", "Great Kitchen", *L(-70, 34), 20, 14, 0, 9, "hip", material="stone")
    b("C", "house", "Treasury & Jewel House", *L(66, 18), 22, 14, 270, 12, "hip", material="stone", floors=3)
    b("C", "barracks", "Barracks of the King's Guard", *L(-138, -10), 70, 13, 90, 9, "gable", material="stone", floors=2)
    b("C", "stables", "Royal Stables", *L(138, -10), 70, 13, 270, 7, "gable", material="timber")
    b("C", "armoury", "Armoury", *L(-85, 100), 26, 13, 0, 9, "gable", material="stone", floors=2)
    b("C", "mint", "Royal Mint", *L(85, 100), 26, 13, 0, 9, "gable", material="stone", floors=2)
    b("C", "house", "Constable's Lodging", *L(-60, -110), 30, 12, 180, 10, "hip", material="stone", floors=2)
    b("C", "granary", "Granaries", *L(60, -110), 34, 12, 180, 9, "gable", material="stone")
    b("C", "gatehouse", "King's Gate (great gatehouse)", *L(0, 125), 32, 24, 180, 28, "crenel", material="stone",
      check=False, passage_w=6, passage_h=8)
    W.tower("C", "King's Gate drum (west)", *L(-17, 130), 9, 30)
    W.tower("C", "King's Gate drum (east)", *L(17, 130), 9, 30)
    b("C", "gatehouse", "Inner Gate", *L(0, 55), 18, 14, 180, 24, "crenel", material="stone", check=False,
      passage_w=5, passage_h=7)
    bar = [L(-22, 168), L(-22, 140), L(22, 140), L(22, 168)]
    W.wall("Crownhold barbican", "barbican", bar, 11, 3.5, gaps=[L(0, 140), L(0, 168)], gap_r=8)
    W.tower("C", "Barbican turret (west)", *L(-22, 168), 5, 14)
    W.tower("C", "Barbican turret (east)", *L(22, 168), 5, 14)
    W.prop("altar_stone", *L(0, 85), name=N["crowning_stone"], w=3.2, d=2.2, h=1.3)
    W.prop("well", *L(30, -70), name="Keep well")
    W.prop("well", *L(-30, 100), name="Bailey well")
    for k in range(6):
        W.prop("training_dummy", *L(-40 + k * 16, 102))
    W.paved_polys.append(outer)
    W.landmark(N["castle"], *L(0, 0), "A giant concentric castle on the crag: two rings of walls, 24 towers, 46 m keep.")
    W.landmark(N["keep"], *L(0, -28), "The 46 m great keep, seven storeys, seat of the Crown.")
    W.landmark("Great Hall of the Kings", *L(-66, -22), "Where the court feasts and the king hears petitions.")
    W.landmark(N["crowning_stone"], *L(0, 85), "A prehistoric stone carried up from the henge: every monarch is crowned on it.")
    W.landmark("King's Gate", *L(0, 128), "Great gatehouse with twin 30 m drum towers and a walled barbican.")


def _city_wall(W):
    cx, cy, rx, ry = CITY
    pts = ellipse_pts(cx, cy, rx, ry, 160, 0.0)
    castle_r = 205
    keep = [p for p in pts if math.hypot(p[0] - CASTLE[0], p[1] - CASTLE[1]) > castle_r]
    river = W.waters[0]["line"]
    segs_pts = []
    run = []
    for p in pts + [pts[0]]:
        inside_castle = math.hypot(p[0] - CASTLE[0], p[1] - CASTLE[1]) < castle_r - 12
        if inside_castle:
            if len(run) > 1:
                segs_pts.append(run)
            run = []
        else:
            run.append(p)
    if len(run) > 1:
        segs_pts.append(run)
    gates = list(W.gates.values())
    water_gates = []
    for x, y in pts:
        if dist_to(river, x, y)[0] < 30 and all(math.hypot(x - a, y - c) > 60 for a, c in water_gates):
            water_gates.append((x, y))
    W.water_gates = water_gates
    for i, run in enumerate(segs_pts):
        W.wall("City wall", "town", run, 12, 3.5, gaps=gates + water_gates, gap_r=8)
    # towers every ~75 m
    acc, last = 0.0, None
    k = 0
    for p in keep:
        if last is not None:
            acc += math.hypot(p[0] - last[0], p[1] - last[1])
        last = p
        if acc > 75 and all(math.hypot(p[0] - g[0], p[1] - g[1]) > 30 for g in gates + water_gates):
            k += 1
            W.tower("T", f"City wall tower {k}", *p, 6, 18, roof="cone", group="City wall")
            acc = 0
    for name, (x, y) in W.gates.items():
        a = math.degrees(math.atan2((y - cy) / ry, (x - cx) / rx))
        W.building("T", "gatehouse", name, x, y, 22, 16, a + 90, 20, "crenel", material="stone", check=False,
                   passage_w=6, passage_h=7)
        t = math.radians(a + 90)
        for s in (-1, 1):
            W.tower("T", f"{name} drum", x + s * 12 * math.cos(t), y + s * 12 * math.sin(t), 7, 22, roof="cone")
    for i, (x, y) in enumerate(water_gates):
        nm = "West Water Gate" if x < 1024 else "East Water Gate"
        for s in (-1, 1):
            W.tower("T", f"{nm} tower", x, y + s * 36, 8, 22, roof="crenel")
        W.prop("chain_boom", x, y, 90, length=60)
    W.landmark("City wall & seven gates", *W.gates["West Gate"],
               f"{k} towers, seven gatehouses and two water gates where the {N['river']} passes under chains.")


# ------------------------------------------------------------------ the prehistoric heart
def _henge(W):
    hx, hy = HENGE
    W.earthworks.append(dict(kind="ring", name="Henge ditch", cx=hx, cy=hy, r0=150, r1=178, h=-7.5,
                             gaps=[0, 90, 180, 270], gap_w=24))
    W.earthworks.append(dict(kind="ring", name="Henge bank", cx=hx, cy=hy, r0=182, r1=212, h=5.0,
                             gaps=[0, 90, 180, 270], gap_w=24))
    rng = W.rng
    for i in range(98):
        t = 2 * math.pi * (i + 0.5) / 98
        if any(abs(((math.degrees(t) - g + 180) % 360) - 180) < 4 for g in (0, 90, 180, 270)):
            continue
        W.prop("standing_stone", hx + 140 * math.cos(t), hy + 140 * math.sin(t), math.degrees(t) + 90,
               h=round(rng.uniform(3.2, 5.4), 1), w=round(rng.uniform(1.8, 3.0), 1), d=round(rng.uniform(0.9, 1.5), 1),
               group="Great Circle", lean=round(rng.uniform(-6, 6), 1))
    for (ccx, ccy, r, n, grp) in [(hx, hy - 55, 48, 27, "North Circle"), (hx, hy + 58, 52, 29, "South Circle")]:
        for i in range(n):
            t = 2 * math.pi * i / n
            W.prop("standing_stone", ccx + r * math.cos(t), ccy + r * math.sin(t), math.degrees(t) + 90,
                   h=round(rng.uniform(2.8, 4.4), 1), w=round(rng.uniform(1.4, 2.4), 1),
                   d=round(rng.uniform(0.8, 1.2), 1), group=grp, lean=round(rng.uniform(-5, 5), 1))
    # the Cove: three giant stones forming an open box facing north-east
    for dx, dy, hd in [(-5, 0, 90), (0, -5, 0), (5, 0, 90)]:
        W.prop("standing_stone", hx + dx, hy - 55 + dy, hd + 45, h=6.2, w=4.6, d=1.6, group=N["cove"])
    W.prop("menhir", hx, hy + 58, 0, h=7.5, w=2.2, d=1.6, name=N["obelisk"])
    for a in (35, 150, 215, 320):                      # four ancient yews inside the bank
        t = math.radians(a)
        W.groves.append((hx + 110 * math.cos(t), hy + 110 * math.sin(t), "yew", 14))
    W.green_polys.append(ellipse_pts(hx, hy, 214, 214, 48))
    W.pastures.append(dict(name="Hallow Green", poly=ellipse_pts(hx, hy, 148, 148, 48), sheep=24))
    # the avenue: paired stones from the east entrance down to the river
    av = spline([(hx + 212, hy), (1320, 950), (1400, 1040), (1450, 1150), (1470, 1250), (1478, 1300)], step=3)
    W.avenue = av
    for x, y, ang, s in along(av, 22.0):
        for side in (-1, 1):
            nx, ny = -math.sin(ang), math.cos(ang)
            W.prop("standing_stone", x + side * 8 * nx, y + side * 8 * ny, math.degrees(ang),
                   h=round(rng.uniform(2.4, 3.6), 1), w=round(rng.uniform(1.4, 2.2), 1), d=1.0, group=N["avenue"],
                   lean=round(rng.uniform(-4, 4), 1))
    W.roads.append(dict(id=f"ROAD-{len(W.roads) + 1:02d}", name=N["avenue"], kind="avenue", width=12,
                        surface="grass", ctrl=[tuple(av[0]), tuple(av[-1])], line=av))
    img = ImageDraw.Draw(W.zone_img)
    img.line([tuple(p) for p in av], fill=255, width=34)
    W.zone = np.asarray(W.zone_img) > 0
    # your house, at the henge's west entrance
    t = math.radians(200)
    W.building("H", "manor_house", f"{YOUR_HOUSE} (your house)", hx + 252 * math.cos(t), hy + 252 * math.sin(t),
               18, 12, 110, 11, "hip", material="stone", floors=3, owner=YOU, check=False)
    W.landmark(N["henge"], hx, hy, "A 420 m henge, 4,000 years older than the city: ditch, bank and 150 standing stones.")
    W.landmark(N["cove"], hx, hy - 55, "Three giant stones at the heart of the North Circle; oaths are sworn here.")
    W.landmark(N["obelisk"], hx, hy + 58, "The tallest stone of the South Circle, the city's midsummer sundial.")
    W.landmark(N["avenue"], 1400, 1040, "Two rows of stones winding 600 m from the henge to the river.")
    W.landmark(f"{YOUR_HOUSE} - YOUR HOUSE", hx + 252 * math.cos(t), hy + 252 * math.sin(t),
               f"Home of {YOU}, keeper of the ancient stones. Start here.")


def _prehistory(W):
    rng = W.rng
    W.earthworks.append(dict(kind="mound", name=N["long_barrow"], x=470, y=770, rx=60, ry=14, h=5.5, heading=12))
    a = math.radians(12)
    fx, fy = 470 + 64 * math.cos(a), 770 + 64 * math.sin(a)
    for k in range(-2, 3):
        W.prop("standing_stone", fx - k * 4 * math.sin(a), fy + k * 4 * math.cos(a), 12 + 90, h=3.2 - abs(k) * 0.4,
               w=2.0, d=0.8, group=f"{N['long_barrow']} forecourt")
    W.landmark(N["long_barrow"], 470, 770, "A 120 m chambered long barrow, the tomb of the 'giant' the city's tales remember.")
    for k in range(13):
        W.prop("standing_stone", 590 + k * 6.5, 720 + k * 9.5, 55, h=round(1.8 + rng.random() * 1.4, 1), w=1.1, d=0.7,
               group=N["row"])
    W.landmark(N["row"], 630, 780, "Thirteen stones in a dead-straight line pointing at the midwinter sunrise.")
    W.prop("dolmen", 620, 985, 20, name=N["dolmen"], w=5.5, d=3.2, h=2.6)
    W.landmark(N["dolmen"], 620, 985, "A portal tomb on the Minster lawn; three kings' bones are said to lie beneath.")
    x0, y0, x1, y1 = MOUNDS
    for k, (dx, dy, r, h) in enumerate([(30, 30, 16, 4), (80, 22, 12, 3), (130, 35, 18, 4.5), (170, 70, 11, 2.6),
                                        (110, 78, 14, 3.4), (55, 75, 10, 2.4), (150, 15, 9, 2.0)]):
        W.earthworks.append(dict(kind="mound", name="Round barrow", x=x0 + dx, y=y0 + dy, rx=r, ry=r, h=h))
    W.pastures.append(dict(name=N["barrows"], poly=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))
    W.green_polys.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    W.landmark(N["barrows"], (x0 + x1) / 2, (y0 + y1) / 2, "Seven Bronze Age burial mounds kept as a public meadow.")


# ------------------------------------------------------------------ centre: squares, markets, bridge
def _square(W, name, box, stalls=0, kind="market"):
    W.squares.append(dict(name=name, box=box, kind=kind))
    W.reserve_box(*box)
    x0, y0, x1, y1 = box
    rng = W.rng
    placed = 0
    for row_y in np.arange(y0 + 10, y1 - 8, 9):
        for col_x in np.arange(x0 + 10, x1 - 8, 7):
            if placed >= stalls:
                return
            if rng.random() < 0.3:
                continue
            W.prop("market_stall", col_x, row_y, 0 if (row_y // 9) % 2 else 180, w=4.2, d=3)
            placed += 1


def _crossing(W, road_name):
    road = [r for r in W.roads if r["name"] == road_name][0]
    river = W.waters[0]["line"]
    d = dist_to(river, road["line"][:, 0], road["line"][:, 1])
    i = int(np.argmin(d))
    return float(road["line"][i][0]), float(road["line"][i][1])


def _centre(W):
    b = W.building
    x0, y0, x1, y1 = MARKET
    _square(W, N["market"], MARKET, stalls=150)
    W.prop("menhir", 1024, 1195, 0, h=9.0, w=1.8, d=1.4, name=N["needle"])
    W.prop("fountain", 960, 1195, r=6)
    W.prop("fountain", 1088, 1195, r=6)
    W.prop("market_cross", 1024, 1150, name="Market Cross")
    W.prop("stocks", 1010, 1240)
    b("M", "cloth_hall", N["cloth_hall"], 1188, 1195, 110, 26, 270, 16, "gable", material="stone", floors=3, check=False)
    b("M", "belfry", "The Belfry", 1188, 1195, 16, 16, 270, 66, "spire", roof_h=18, material="stone", floors=10,
      check=False, group=N["cloth_hall"])
    b("M", "guildhall", N["guildhall"], 860, 1195, 80, 24, 90, 18, "hip", material="stone", floors=3, check=False)
    b("M", "guildhall", "Guildhall tower", 860, 1150, 12, 12, 90, 34, "spire", roof_h=12, material="stone",
      check=False, group=N["guildhall"])
    W.reserve_box(1172, 1135, 1204, 1255)
    W.reserve_box(845, 1150, 875, 1240)
    W.landmark(N["market"], 1024, 1195, "A 260 x 120 m square with 150 stalls, fountains and the Needle at its heart.")
    W.landmark(N["needle"], 1024, 1195, "A 9 m prehistoric menhir left standing in the market: deals are sealed by touching it.")
    W.landmark(N["cloth_hall"], 1188, 1195, "Vast cloth market with an 84 m belfry, the tallest tower in the city.")
    W.landmark(N["guildhall"], 860, 1195, "Seat of the city council and the twelve great guilds.")
    # crown square and the column
    _square(W, N["crown_square"], CROWN_SQ, stalls=0, kind="square")
    W.prop("column", 1024, 645, h=32, r=2.2, name=N["column"])
    for dx in (-50, 50):
        W.prop("statue", 1024 + dx, 625, 180, h=6, name="Statue of a king")
        W.prop("fountain", 1024 + dx, 662, r=5)
    W.landmark(N["column"], 1024, 645, "A 32 m column topped by the first king, facing the stones he swore to protect.")
    _square(W, N["hay_market"], HAY, stalls=18)
    _square(W, N["fish_market"], FISH, stalls=22)
    _square(W, N["corn_market"], CORN, stalls=24)
    W.prop("market_cross", 1024, 1530, name="Corn Cross")
    W.landmark(N["hay_market"], 720, 663, "Carters and hay wains from the northern farms.")
    W.landmark(N["fish_market"], 1290, 1283, "Fresh catch straight off the boats at King's Quay.")
    W.landmark(N["corn_market"], 1024, 1530, "Grain market on the south bank, by the Old Bridge.")
    # the Old Bridge with houses on it
    river = W.waters[0]
    W.explicit_bridges = []
    br = dict(name=N["old_bridge"], road="Bridge Street", x=1024.0, y=1352.0, heading=90.0, length=150.0, width=26.0,
              material="stone", arches=19, inhabited=True)
    W.explicit_bridges.append(br)
    for y in np.arange(1286, 1420, 8.2):
        if abs(y - 1352) < 14:
            continue
        for side in (-1, 1):
            first, trade = W.person(TRADES)
            b("R", "shop", f"Bridge house of {first} the {trade}", 1024 + side * 9.5, y + 4, 8, 7.5,
              90 if side < 0 else 270, 9, "gable", material="timber", floors=3, check=False, on_bridge=N["old_bridge"],
              trade=trade, resident=first)
    b("R", "chapel", "Bridge Chapel of St. Thomas", 1040, 1352, 10, 16, 90, 9, "gable", material="stone",
      check=False, on_bridge=N["old_bridge"])
    W.landmark(N["old_bridge"], 1024, 1352, "A 150 m stone bridge of 19 arches carrying 28 shops and houses and a chapel.")
    mbx, mby = _crossing(W, "Mill Street")
    br2 = dict(name=N["mill_bridge"], road="Mill Street", x=mbx, y=mby, heading=115.0, length=110.0,
               width=12.0, material="stone", arches=7)
    W.explicit_bridges.append(br2)
    ux, uy = math.cos(math.radians(115)), math.sin(math.radians(115))
    for k, off in enumerate((-24, 0, 24)):
        mx, my = mbx + off * ux + 13 * uy, mby + off * uy - 13 * ux        # hung off the downstream side
        b("R", "watermill", f"Bridge Mill {k + 1}", mx, my, 10, 9, 115, 7, "gable", material="timber",
          check=False, on_bridge=N["mill_bridge"])
        W.prop("waterwheel", mx + 6.5 * uy, my - 6.5 * ux, 115 + 90, r=3.5, w=1.5, on_bridge=N["mill_bridge"])
    W.landmark(N["mill_bridge"], mbx, mby, "Seven arches with three corn mills hung off its side.")
    # quayside warehouses, cranes and ships
    quay = [p for p in river["line"] if 1100 < p[0] < 1700]
    for i in range(0, len(quay) - 1, 9):
        x, y = quay[i]
        nx, ny = quay[min(i + 1, len(quay) - 1)]
        ang = math.degrees(math.atan2(ny - y, nx - x))
        if abs(x - 1478) < 30 or abs(x - 1290) < 45:
            continue
        b("R", "warehouse", f"Warehouse {i // 9 + 1}", x, y - 52, 24, 13, ang + 180, 11, "gable", material="timber",
          floors=3, optional=True)
        if i % 27 == 0:
            W.prop("crane", x, y - 34)
        if i % 18 == 9:
            W.prop("ship", x, y - 14, ang, length=26, w=7)
    W.landmark(N["quay"], 1400, 1290, "Warehouses, treadwheel cranes and sea-going cogs on the River Wend.")


def _cathedral(W):
    b = W.building
    c = N["cathedral"]
    b("K", "cathedral", f"{c} (nave)", 650, 1040, 110, 30, 0, 32, "gable", material="stone", group=c, check=False)
    b("K", "cathedral", f"{c} (choir)", 730, 1040, 50, 26, 0, 30, "gable", material="stone", group=c, check=False)
    b("K", "cathedral", f"{c} (Lady Chapel)", 767, 1040, 24, 15, 0, 18, "gable", material="stone", group=c, check=False)
    b("K", "cathedral", f"{c} (transepts)", 705, 1040, 26, 74, 0, 32, "gable", material="stone", group=c, check=False)
    b("K", "cathedral", f"{c} (crossing tower)", 705, 1040, 26, 26, 0, 62, "spire", roof_h=58, material="stone",
      group=c, check=False, floors=12)
    for dy in (-20, 20):
        b("K", "cathedral", f"{c} (west tower)", 586, 1040 + dy, 18, 18, 0, 68, "crenel", material="stone",
          group=c, check=False, floors=12)
    b("K", "cloister", "Cloister east range & dormitory", 692, 1100, 50, 10, 90, 10, "gable", material="stone", check=False)
    b("K", "cloister", "Cloister south range & library", 660, 1132, 54, 10, 180, 10, "gable", material="stone", check=False)
    b("K", "cloister", "Cloister west range", 628, 1100, 50, 10, 270, 10, "gable", material="stone", check=False)
    b("K", "chapter_house", "Chapter House", 724, 1100, 22, 22, 0, 14, "cone", roof_h=10, material="stone",
      shape="round", check=False)
    b("K", "palace", "Bishop's Palace", 760, 1140, 40, 14, 180, 13, "hip", material="stone", floors=3, check=False)
    b("K", "house", "Deanery", 585, 1135, 22, 12, 0, 10, "hip", material="stone", floors=2, check=False)
    W.prop("garth", 660, 1100, w=40, d=40)
    W.wall("Cathedral close wall", "precinct", [(560, 960), (800, 960), (800, 1160), (560, 1160)], 3.5, 1.0, closed=True,
           gaps=[(680, 960), (800, 1060), (560, 1060)], gap_r=6)
    W.green_polys.append([(560, 960), (800, 960), (800, 1160), (560, 1160)])
    W.pastures.append(dict(name="Minster Green", poly=[(565, 965), (795, 965), (795, 1015), (565, 1015)]))
    W.churchyards.append((565, 965, 795, 1015))
    for k in range(18):
        W.prop("gravestone", 575 + (k % 9) * 24, 1000 + (k // 9) * 10)
    W.groves += [(575, 975, "yew", 12), (790, 975, "yew", 13), (575, 1150, "lime", 15), (790, 1150, "lime", 15)]
    W.landmark(c, 705, 1040, "Gothic cathedral 200 m long; its spire reaches 120 m, the tallest thing in the realm.")


def _gardens_and_park(W):
    b = W.building
    x0, y0, x1, y1 = GARDENS
    W.wall("Queen's Gardens wall", "precinct", [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 3, 1.0, closed=True,
           gaps=[(1375, y1), (x0, 520)], gap_r=6)
    b("G", "palace", "Summer Palace & Orangery", 1375, 432, 90, 18, 180, 14, "hip", material="stone", floors=2, check=False)
    for k, (px, py) in enumerate([(1255, 450), (1495, 450)]):
        b("G", "pavilion", "Garden pavilion", px, py, 10, 10, 0, 6, "cone", roof_h=5, material="stone", shape="round",
          check=False)
    # maze of clipped hedges
    mx, my, cell, n = 1270, 495, 6.0, 10
    rng = random.Random(7)
    walls = _maze(n, rng)
    segs = []
    for (ax, ay, bx, by) in walls:
        segs.append([(mx + ax * cell, my + ay * cell), (mx + bx * cell, my + by * cell)])
    for s in segs:
        W.wall(N["maze"], "hedge", s, 2.4, 0.9, material="hedge")
    W.landmark(N["maze"], mx + n * cell / 2, my + n * cell / 2, "A 60 m hedge maze; at its heart a sundial stone.")
    W.prop("sundial", mx + n * cell / 2, my + n * cell / 2)
    # parterres and an avenue of limes
    for k in range(6):
        px = 1360 + (k % 3) * 46
        py = 490 + (k // 3) * 44
        W.fields.append(dict(name="Parterre", field="Gardens", crop="herbs",
                             poly=[(px, py), (px + 36, py), (px + 36, py + 34), (px, py + 34)]))
    W.prop("fountain", 1428, 555, r=8)
    for k in range(9):
        W.groves.append((1255 + k * 28, 470, "lime", 13))
        W.groves.append((1255 + k * 28, 612, "lime", 13))
    W.green_polys.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    W.pastures.append(dict(name="Gardens lawn", poly=[(x0 + 3, y0 + 30), (x1 - 3, y0 + 30), (x1 - 3, y1 - 3), (x0 + 3, y1 - 3)]))
    W.landmark(N["gardens"], 1375, 520, "Royal pleasure gardens: parterres, ponds, lime avenues and the summer palace.")
    # King's Park: natural woodland inside the walls
    px, py, rx, ry = PARK
    park = ellipse_pts(px, py, rx, ry, 48, 0.08, seed=3)
    W.forests.append(dict(name=N["park"], kind="park woodland", poly=park, spacing=11, glades=0.35))
    W.green_polys.append(park)
    b("G", "lodge", "Park Keeper's Lodge", 640, 860, 14, 8, 200, 6, "gable", material="timber", check=False)
    W.landmark(N["park"], px, py, "Ancient woodland kept wild inside the walls, with deer, a mere and the barrow.")


def _maze(n, rng):
    """Perfect maze on an n x n grid; returns wall segments in cell units."""
    visited = [[False] * n for _ in range(n)]
    walls = set()
    for i in range(n + 1):
        for j in range(n):
            walls.add((j, i, j + 1, i))
            walls.add((i, j, i, j + 1))
    stack = [(0, 0)]
    visited[0][0] = True
    while stack:
        x, y = stack[-1]
        nb = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
              if 0 <= x + dx < n and 0 <= y + dy < n and not visited[y + dy][x + dx]]
        if not nb:
            stack.pop()
            continue
        nx, ny = rng.choice(nb)
        if nx != x:
            wx = max(x, nx)
            walls.discard((wx, y, wx, y + 1))
        else:
            wy = max(y, ny)
            walls.discard((x, wy, x + 1, wy))
        visited[ny][nx] = True
        stack.append((nx, ny))
    walls.discard((0, n // 2, 0, n // 2 + 1))        # entrance on the west side
    return sorted(walls)


def _quad(W, district, name, box, chapel=True):
    """A quadrangle of ranges round a courtyard (colleges, hospital, friaries)."""
    x0, y0, x1, y1 = box
    w, d = x1 - x0, y1 - y0
    b = W.building
    b(district, "college", f"{name} (north range)", (x0 + x1) / 2, y0 + 6, w, 11, 0, 11, "gable", material="stone",
      floors=3, check=False)
    b(district, "college", f"{name} (south range)", (x0 + x1) / 2, y1 - 6, w, 11, 180, 11, "gable", material="stone",
      floors=3, check=False)
    b(district, "college", f"{name} (west range)", x0 + 6, (y0 + y1) / 2, d - 24, 11, 270, 11, "gable",
      material="stone", floors=3, check=False)
    b(district, "chapel" if chapel else "college", f"{name} ({'chapel' if chapel else 'east range'})", x1 - 6,
      (y0 + y1) / 2, d - 24, 11, 90, 14 if chapel else 11, "gable", material="stone", floors=1, check=False)
    W.pastures.append(dict(name=f"{name} court", poly=[(x0 + 13, y0 + 13), (x1 - 13, y0 + 13), (x1 - 13, y1 - 13),
                                                       (x0 + 13, y1 - 13)]))


def _institutions(W):
    x0, y0, x1, y1 = UNIVERSITY
    _quad(W, "U", "Starlight College", (x0, y0, x0 + 85, y0 + 70))
    _quad(W, "U", "Henge College", (x0 + 95, y0, x1, y0 + 70))
    W.building("U", "library", "University Library", (x0 + x1) / 2, y0 + 92, 60, 16, 0, 14, "hip", material="stone",
               floors=3, check=False)
    W.fields.append(dict(name=N["physic_garden"], field="University", crop="herbs",
                         poly=[(x0 + 10, y0 + 104), (x1 - 10, y0 + 104), (x1 - 10, y1 - 4), (x0 + 10, y1 - 4)]))
    W.landmark(N["university"], (x0 + x1) / 2, y0 + 40, "Two colleges, a great library and the Physic Garden of healing herbs.")
    _quad(W, "S", N["hospital"], HOSPITAL)
    W.landmark(N["hospital"], (HOSPITAL[0] + HOSPITAL[2]) / 2, (HOSPITAL[1] + HOSPITAL[3]) / 2,
               "Infirmary, almshouse and herb garden run by the Brigidine sisters.")
    ax0, ay0, ax1, ay1 = ABBEY
    b = W.building
    b("S", "church", f"{N['abbey']} church", (ax0 + ax1) / 2, ay0 + 20, 120, 20, 0, 22, "gable", material="stone",
      check=False)
    b("S", "church", f"{N['abbey']} tower", (ax0 + ax1) / 2 + 20, ay0 + 20, 16, 16, 0, 40, "spire", roof_h=20,
      material="stone", check=False, group=f"{N['abbey']} church")
    _quad(W, "S", f"{N['abbey']} cloister", (ax0 + 30, ay0 + 40, ax1 - 30, ay1 - 25), chapel=False)
    W.landmark(N["abbey"], (ax0 + ax1) / 2, ay0 + 60, "Benedictine abbey whose monks first wrote down the legends of the stones.")
    for nm, box in ((N["friary_w"], FRIARY_W), (N["friary_e"], FRIARY_E)):
        _quad(W, "W" if box is FRIARY_W else "E", nm, box)
        W.landmark(nm, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, "A friary of preaching brothers.")


# ------------------------------------------------------------------ churches, guild halls, houses
def _place_near(W, x, y, w, d, kind, name, district, h, roof, radius=90, **kw):
    for r in range(0, radius, 6):
        for a in range(0, 360, 30 if r else 360):
            px, py = x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))
            for hd in (0, 90):
                c = rect_corners(px, py, w + 8, d + 8, hd)
                xs, ys = [p[0] for p in c], [p[1] for p in c]
                if not _free(W, xs + [px], ys + [py]).all() or city_q(px, py) > 0.92:
                    continue
                if W.blocked(c):
                    continue
                return W.building(district, kind, name, px, py, w, d, hd, h, roof, check=False, **kw)
    return None


PARISHES = ["St. Agatha", "St. Bede", "St. Columba", "St. Dunstan", "St. Edith", "St. Fiacre", "St. Giles",
            "St. Hugh", "St. Ivo", "St. Jude", "St. Kenelm", "St. Lucy", "St. Martin", "St. Nicholas"]


def _churches_and_guilds(W):
    cx, cy, rx, ry = CITY
    k = 0
    for i, a in enumerate(range(10, 360, 26)):
        s = 0.62 if i % 2 else 0.8
        x, y = cx + rx * s * math.cos(math.radians(a)), cy + ry * s * math.sin(math.radians(a))
        name = f"Church of {PARISHES[k % len(PARISHES)]}"
        ch = _place_near(W, x, y, 30, 11, "church", name, _district(x, y), 13, "gable", material="stone", floors=1)
        if ch is None:
            continue
        a2 = math.radians(ch["heading"])
        tx, ty = ch["x"] - 18 * math.cos(a2), ch["y"] - 18 * math.sin(a2)
        W.building(ch["district"], "church", f"{name} (tower)", tx, ty, 8, 8, ch["heading"], 26, "spire", roof_h=14,
                   material="stone", check=False, group=name, floors=4)
        k += 1
    W.parish_count = k
    mx, my = 1024, 1195
    for i, g in enumerate(GUILDS):
        a = math.radians(i * 45 + 20)
        _place_near(W, mx + 230 * math.cos(a), my + 160 * math.sin(a), 22, 13, "guildhall", f"{g}' Hall",
                    "M", 14, "hip", material="stone", floors=3, radius=120)


def _district(x, y):
    if city_q(x, y) > 1.0:
        return "X"
    river = 1340
    if y > river + 20:
        return "S"
    if math.hypot(x - 1024, y - 1195) < 260:
        return "M"
    a = math.degrees(math.atan2(y - CITY[1], x - CITY[0]))
    if -60 <= a <= 60:
        return "E"
    if a > 120 or a < -120:
        return "W"
    return "N"


def _houses(W):
    rng = W.rng
    cx, cy = CITY[0], CITY[1]
    order = sorted(W.roads, key=lambda r: -r["width"])
    count = 0
    for st in order:
        if st["kind"] not in ("street",) or len(st["line"]) < 6:
            continue
        line = st["line"]
        total = float(np.hypot(*np.diff(line, axis=0).T).sum())
        for side in (1, -1):
            s = 3.0
            while s < total - 3:
                fw = rng.uniform(5.5, 9.5)
                if s + fw / 2 >= total:
                    break
                x, y, ang, _ = along(line, 1, start=s + fw / 2, end=s + fw / 2 + 0.5)[0]
                s += fw + rng.uniform(0.0, 0.7)
                dd = rng.uniform(9, 15)
                nx, ny = -math.sin(ang), math.cos(ang)
                off = st["width"] / 2 + 0.6 + dd / 2
                hx, hy = x + side * off * nx, y + side * off * ny
                if city_q(hx, hy) > 0.95:
                    continue
                hd = heading_facing(ang, side)
                c = rect_corners(hx, hy, fw, dd, hd)
                xs = [p[0] for p in c] + [hx]
                ys = [p[1] for p in c] + [hy]
                if not _free(W, xs, ys).all() or W.blocked(c):
                    continue
                centre = math.hypot((hx - cx) / CITY[2], (hy - cy) / CITY[3])
                floors = max(2, min(5, int(round(rng.gauss(4.4 - 2.6 * centre, 0.7)))))
                first, trade = W.person(TRADES)
                dist = _district(hx, hy)
                kind = "shop" if rng.random() < 0.5 else "house"
                stone = rng.random() < (0.35 if centre < 0.45 else 0.12)
                W.building(dist, kind, f"House of {first} the {trade}", hx, hy, fw, dd, hd, 3.1 * floors,
                           rng.choice(["gable", "gable", "gable", "hip"]), material="stone" if stone else "timber",
                           floors=floors, trade=trade, resident=first, pad=0.15, check=False)
                W.reserve(c)
                count += 1
                if rng.random() < 0.6:                       # rear workshop or kitchen range
                    bw, bd = rng.uniform(4.5, fw), rng.uniform(4.5, 8)
                    boff = off + dd / 2 + rng.uniform(1.0, 4.0) + bd / 2
                    bx, by = x + side * boff * nx, y + side * boff * ny
                    cc = rect_corners(bx, by, bw, bd, hd)
                    if _free(W, [p[0] for p in cc] + [bx], [p[1] for p in cc] + [by]).all() and not W.blocked(cc) \
                            and city_q(bx, by) < 0.95:
                        W.building(dist, "workshop", f"Workshop of {first} the {trade}", bx, by, bw, bd, hd,
                                   3.0 * rng.choice([1, 1, 2]), "gable", material="timber", floors=1, check=False)
                        W.reserve(cc)
    W.house_count = count
    _infill(W)


def _infill(W):
    """Fill the backs of the blocks: tenements, stables and workshops reached by alleys."""
    rng = W.rng
    cx, cy = CITY[0], CITY[1]
    n = 0
    for gy in np.arange(330, 1820, 8.5):
        for gx in np.arange(200, 1850, 8.5):
            x, y = gx + rng.uniform(-2, 2), gy + rng.uniform(-2, 2)
            if city_q(x, y) > 0.93 or rng.random() > 0.8:
                continue
            if not _free(W, [x], [y])[0]:
                continue
            hd = (math.degrees(math.atan2(y - cy, x - cx)) + rng.choice([0, 90]) + rng.uniform(-4, 4)) % 360
            for w, d in ((rng.uniform(6, 9), rng.uniform(6, 9)), (rng.uniform(4, 5.5), rng.uniform(4, 5.5))):
                c = rect_corners(x, y, w + 2.4, d + 2.4, hd)      # 1.2 m alley all round
                if _free(W, [p[0] for p in c], [p[1] for p in c]).all() and not W.blocked(c):
                    break
            else:
                continue
            first, trade = W.person(TRADES)
            kind = rng.choice(["tenement", "tenement", "workshop", "stable", "storehouse"])
            floors = rng.choice([1, 2, 2, 3]) if kind == "tenement" else 1
            W.building(_district(x, y), kind, f"{kind.title()} of {first} the {trade}", x, y, w, d, hd,
                       3.0 * floors + (0.6 if kind != "tenement" else 0), "gable", material="timber",
                       floors=floors, trade=trade, resident=first, check=False, pad=0)
            W.reserve(c)
            n += 1
    W.infill_count = n


# ------------------------------------------------------------------ outside the walls
def _outside(W):
    rng = W.rng
    b = W.building
    # ribbon suburbs along the roads beyond the gates
    for r in list(W.roads):
        if r["kind"] not in ("road", "street"):
            continue
        line = r["line"]
        total = float(np.hypot(*np.diff(line, axis=0).T).sum())
        for side in (1, -1):
            s = 5.0
            while s < total - 6:
                fw = rng.uniform(8, 13)
                x, y, ang, _ = along(line, 1, start=s, end=s + 0.5)[0]
                s += fw + rng.uniform(2, 9)
                dd = rng.uniform(7, 10)
                nx, ny = -math.sin(ang), math.cos(ang)
                off = r["width"] / 2 + 3 + dd / 2
                hx, hy = x + side * off * nx, y + side * off * ny
                if not 1.07 < city_q(hx, hy) < 1.4:
                    continue
                hd = heading_facing(ang, side)
                c = rect_corners(hx, hy, fw, dd, hd)
                if W.blocked(c) or not _free(W, [p[0] for p in c], [p[1] for p in c]).all():
                    continue
                first, trade = W.person(TRADES)
                b("X", "house", f"Cottage of {first} the {trade}", hx, hy, fw, dd, hd, 3.4, "gable",
                  material="timber", floors=1, trade=trade, resident=first, thatch=True, check=False)
                W.reserve(c)
    # fairs outside the east and west gates
    for name, (fx, fy) in ((N["cattle_market"], (1955, 990)), ("Horse Fair", (95, 990))):
        box = (fx - 55, fy - 45, fx + 55, fy + 45)
        W.squares.append(dict(name=name, box=box, kind="fair"))
        for k in range(12):
            W.prop("pen", box[0] + 12 + (k % 4) * 26, box[1] + 15 + (k // 4) * 28, w=16, d=12)
        W.reserve_box(*box)
        W.landmark(name, fx, fy, "Livestock fair outside the gate every Thursday.")
    # windmills on the hills
    for k, (wx, wy) in enumerate([(430, 230), (600, 205), (1650, 190)]):
        b("X", "windmill", f"Windmill {k + 1}", wx, wy, 7, 7, 180, 10, "gable", material="timber", sails=12,
          check=False)
    # fields in the corners
    for name, (fx, fy, fw, fh, ang) in [("South-West Fields", (150, 1960, 230, 140, 4)),
                                        ("South-East Fields", (1880, 1950, 260, 150, -5)),
                                        ("South Fields", (1300, 1940, 220, 140, 3)),
                                        ("South Fields", (760, 1950, 240, 130, -3))]:
        x = -fw / 2
        while x < fw / 2 - 5:
            sw = min(rng.choice([16, 20, 24]), fw / 2 - x)
            a = math.radians(ang)
            px, py = fx + (x + sw / 2) * math.cos(a), fy + (x + sw / 2) * math.sin(a)
            W.fields.append(dict(name=f"{name} strip", field=name, crop=rng.choice(["wheat", "barley", "oats", "fallow"]),
                                 poly=[tuple(round(v, 2) for v in c) for c in rect_corners(px, py, sw, fh, ang)]))
            x += sw
        W.fields.append(dict(name=name, field=name, crop="outline",
                             poly=[tuple(round(v, 2) for v in c) for c in rect_corners(fx, fy, fw, fh, ang)]))


def _vegetation(W):
    W.forests += [
        dict(name=N["forest_n"], kind="royal forest", poly=[(0, 0), (2048, 0), (2048, 330), (1700, 330), (1400, 270),
                                                             (1250, 250), (800, 250), (650, 270), (300, 320),
                                                             (0, 420)], spacing=10),
        dict(name=N["forest_se"], kind="mixed", poly=[(1900, 1500), (2048, 1450), (2048, 1850), (1960, 1800)], spacing=10),
        dict(name=N["forest_sw"], kind="mixed", poly=[(0, 1420), (130, 1450), (170, 1700), (0, 1820)], spacing=10),
    ]
    W.orchards.append(dict(name="Hospital orchard", poly=[(1255, 1655), (1380, 1655), (1380, 1690), (1255, 1690)], spacing=9))


def _labels(W):
    L = W.labels
    L += [
        dict(t=N["castle"].upper(), x=1024, y=232, size=34, kind="place", sub="royal castle on the crag"),
        dict(t=N["henge"].upper(), x=1024, y=905, size=28, kind="place", sub="the prehistoric heart of the city"),
        dict(t=N["market"].upper(), x=1024, y=1290, size=20, kind="place"),
        dict(t=N["cathedral"].upper(), x=680, y=948, size=20, kind="place"),
        dict(t=N["gardens"].upper(), x=1375, y=392, size=16, kind="place"),
        dict(t=N["park"].upper(), x=520, y=660, size=18, kind="region"),
        dict(t="SOUTHBANK", x=1360, y=1470, size=26, kind="place", sub="tanners, scholars and sailors"),
        dict(t="NORTH WARD", x=760, y=520, size=22, kind="place"),
        dict(t="EAST WARD", x=1640, y=830, size=22, kind="place"),
        dict(t="WEST WARD", x=330, y=1180, size=22, kind="place"),
        dict(t=N["forest_n"].upper(), x=1700, y=110, size=22, kind="region"),
        dict(t=N["hills"].upper(), x=760, y=70, size=18, kind="region"),
        dict(t=N["river"].upper(), x=260, y=1300, size=20, kind="water", rot=12),
        dict(t=N["river"].upper(), x=1700, y=1385, size=20, kind="water", rot=10),
        dict(t=N["avenue"], x=1370, y=1080, size=13, kind="field", rot=58),
        dict(t=N["university"], x=490, y=1530, size=12, kind="field"),
    ]
