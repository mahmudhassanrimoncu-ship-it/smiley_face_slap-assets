"""The city model: coast, rivers, walls, streets, sites, buildings and stones.

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



# =================================================================== Stonehallow (4 km)
from PIL import Image, ImageDraw  # noqa: E402

from config import SEA_LEVEL  # noqa: E402

RS = 0.5                    # layout rasters: pixels per metre (2 m cells)
RN = int(WORLD_SIZE * RS) + 1

TRADES = ("baker butcher cooper chandler weaver tailor cobbler potter fletcher bowyer brewer carpenter mason "
          "glover saddler goldsmith apothecary scribe draper spicer wheelwright dyer fuller tinker locksmith "
          "barber-surgeon cutler pewterer ropemaker mercer vintner furrier hatter bookbinder limner "
          "bellfounder armourer clockmaker glazier jeweller cheesemonger fishmonger pie-seller tanner "
          "parchmenter stonecarver lute-maker money-changer notary herbalist candlemaker sailmaker "
          "net-mender shipwright fisher salter cartographer astrologer juggler minstrel").split()

COAST = [(3350, -60), (3250, 250), (3330, 480), (3620, 600), (3780, 720), (3650, 840), (3400, 900), (3230, 980),
         (3120, 1150), (3200, 1350), (3300, 1520), (3150, 1750), (3030, 1950), (3000, 2100), (3010, 2260),
         (3000, 2380), (3150, 2470), (3120, 2750), (3250, 2950), (3520, 3080), (3560, 3220), (3380, 3330),
         (3220, 3500), (3300, 3800), (3250, 4160)]
CASTLE = (1650.0, 1150.0)
WALL_SOUTH = [(1480, 1290), (1330, 1340), (1240, 1460), (1180, 1600), (1120, 1720), (1110, 1880), (1150, 2050),
              (1190, 2230), (1260, 2420), (1420, 2520), (1600, 2560), (1800, 2590), (2000, 2560), (2200, 2500),
              (2420, 2450), (2620, 2425), (2800, 2425), (2985, 2395)]
WALL_NORTH = [(3015, 1955), (2930, 1820), (2820, 1660), (2680, 1520), (2575, 1400), (2565, 1180), (2470, 1020),
              (2250, 975), (2050, 1005), (1860, 1045)]
OLD_WALL = [(1530, 1395), (1720, 1370), (1950, 1395), (2150, 1455), (2235, 1600), (2215, 1730), (1960, 1750),
            (1740, 1755), (1545, 1735), (1495, 1590)]
ISLAND_C = (1845.0, 1905.0)

# district seeds: name, x, y, branch spacing, max street length, block depth, house fill, floors (lo, hi), style
DISTRICTS = [
    ("Old Town", "O", 1850, 1600, 28, 170, 20, 0.95, (3, 5), "mixed"),
    ("King's Isle", "I", 1845, 1905, 60, 90, 20, 0.6, (2, 3), "stone"),
    ("Castlegate", "C", 1600, 1380, 36, 140, 22, 0.85, (2, 4), "stone"),
    ("Palace Quarter", "P", 2280, 1200, 90, 200, 40, 0.55, (2, 3), "stone"),
    ("Merchant Quarter", "M", 2380, 1640, 36, 200, 24, 0.85, (3, 4), "mixed"),
    ("Harbour", "H", 2780, 1900, 40, 180, 24, 0.8, (2, 3), "timber"),
    ("Shipwrights' Reach", "Y", 2800, 2320, 70, 160, 30, 0.6, (1, 2), "timber"),
    ("Tanners' Reach", "T", 2520, 2230, 55, 160, 28, 0.75, (1, 2), "timber"),
    ("Southbank", "S", 1950, 2250, 32, 180, 22, 0.85, (2, 4), "timber"),
    ("Scholars' Hill", "U", 1400, 2200, 65, 170, 30, 0.65, (2, 3), "stone"),
    ("Westgate", "W", 1300, 1750, 40, 160, 24, 0.75, (2, 3), "mixed"),
    ("South Ward", "D", 1750, 2470, 40, 180, 24, 0.7, (2, 3), "timber"),
    ("Northgate", "N", 1330, 900, 80, 160, 30, 0.6, (1, 2), "timber"),
    ("Eastfold", "E", 3000, 1170, 70, 130, 30, 0.55, (1, 2), "timber"),
    ("Lantern Point", "L", 3200, 3080, 70, 120, 30, 0.5, (1, 2), "timber"),
    ("Outlands", "X", 0, 0, 120, 120, 40, 0.3, (1, 1), "timber"),
]


def district_at(x, y):
    best, bd = DISTRICTS[-1], 1e18
    for d in DISTRICTS[:-1]:
        dd = (x - d[2]) ** 2 + (y - d[3]) ** 2
        if dd < bd:
            best, bd = d, dd
    return best if bd < 520 ** 2 else DISTRICTS[-1]


def frame(cx, cy, heading):
    a = math.radians(heading)
    ca, sa = math.cos(a), math.sin(a)
    return lambda u, v: (cx + u * ca - v * sa, cy + u * sa + v * ca)


def zigzag(pts, step=70, amp=16, closed=False, rng=None):
    """Turn a rough outline into a jagged wall line with salients every ~step metres."""
    seq = list(pts) + ([pts[0]] if closed else [])
    out = []
    k = 0
    for (x0, y0), (x1, y1) in zip(seq, seq[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / step))
        nx, ny = -(y1 - y0) / L, (x1 - x0) / L
        for i in range(n):
            t = i / n
            off = (amp if k % 2 else -amp * 0.4) * (0.6 + 0.8 * (rng.random() if rng else 0.5))
            if i == 0:
                off = 0
            out.append((x0 + (x1 - x0) * t + nx * off, y0 + (y1 - y0) * t + ny * off))
            k += 1
    if not closed:
        out.append(seq[-1])
    return out


# ------------------------------------------------------------------ build
def build_layout():
    W = World()
    W.squares, W.churchyards, W.paved_polys, W.green_polys, W.groves = [], [], [], [], []
    W.earthworks, W.plateaus, W.pads, W.level_polys, W.cliffs, W.sites = [], [], [], [], [], []
    W.explicit_bridges, W.islands, W.vineyards = [], [], []
    _geography(W)
    _rasters(W)
    _main_roads(W)
    _walls(W)
    _castle(W)
    _old_town(W)
    _isle(W)
    _palace(W)
    _merchants_and_harbour(W)
    _military(W)
    _southbank(W)
    _scholars(W)
    _outside_south(W)
    _north_and_west(W)
    _coast_east(W)
    _grow_streets(W)
    _plazas(W)
    _churches(W)
    _houses(W)
    _vegetation(W)
    _labels(W)
    return W


def site(W, name, x, y, kind, desc, zone=None, landmark=True):
    W.sites.append(dict(name=name, kind=kind, x=round(x, 1), y=round(y, 1), desc=desc,
                        district=district_at(x, y)[0]))
    if landmark:
        W.landmark(name, round(x, 1), round(y, 1), desc)
    if zone is not None:
        _block(W, zone)


def _block(W, zone):
    """Mark ground as taken (no streets or ordinary houses): ('rect', x0,y0,x1,y1) | ('circle', x,y,r) | ('poly', pts)."""
    d = W.zone_draw
    if zone[0] == "rect":
        x0, y0, x1, y1 = zone[1:]
        d.rectangle([x0 * RS, y0 * RS, x1 * RS, y1 * RS], fill=255)
        W.reserve_box(x0, y0, x1, y1)
    elif zone[0] == "circle":
        x, y, r = zone[1:]
        d.ellipse([(x - r) * RS, (y - r) * RS, (x + r) * RS, (y + r) * RS], fill=255)
        W.reserve_box(x - r * 0.7, y - r * 0.7, x + r * 0.7, y + r * 0.7)
    else:
        d.polygon([(x * RS, y * RS) for x, y in zone[1]], fill=255)


# ------------------------------------------------------------------ geography
def _geography(W):
    base = spline(COAST, step=12)                         # rugged coast: coves and points on a smooth sweep
    rng = np.random.default_rng(SEED)
    n = len(base)
    noise = np.zeros(n)
    for wl, amp in ((40, 14), (13, 28), (5, 46)):
        ctrl = rng.normal(0, 1, n // wl + 3)
        noise += amp * np.interp(np.arange(n) / wl, np.arange(len(ctrl)), ctrl)
    tang = np.gradient(base, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    W.coast = base + np.stack([-tang[:, 1], tang[:, 0]], 1) * noise[:, None]
    W.sea_poly = [tuple(p) for p in W.coast] + [(4200, 4200), (4200, -100)]
    W.ridges = [
        dict(pts=spline([(-60, 330), (500, 300), (1000, 380), (1500, 300), (2100, 360), (2700, 300), (3300, 200)], step=10),
             h=70, w=260),
        dict(pts=spline([(330, -60), (300, 600), (380, 1200), (300, 1900), (360, 2600), (250, 3300)], step=10),
             h=55, w=230),
    ]
    W.peaks = [
        dict(name="Crownback", x=1500, y=260, h=45, rx=320, ry=200),
        dict(name="Windmill Down", x=2300, y=420, h=40, rx=260, ry=160),
        dict(name="Old Ring Hill", x=700, y=2600, h=60, rx=260, ry=220),
        dict(name="Grey Tor", x=300, y=1500, h=45, rx=220, ry=260),
        dict(name="South Down", x=1750, y=3500, h=30, rx=520, ry=260),
        dict(name="Raven Head", x=3600, y=720, h=25, rx=200, ry=140),
    ]
    W.cliffs = [dict(x=3640, y=720, r=280, h=26), dict(x=3470, y=3170, r=170, h=16)]
    W.plateaus = [dict(x=CASTLE[0], y=CASTLE[1], r=215, z=118, base=70, fall=170)]
    main = spline([(-30, 1500), (300, 1560), (600, 1500), (900, 1620), (1150, 1780), (1400, 1840), (1600, 1880),
                   (1700, 1810), (1850, 1790), (2000, 1825), (2080, 1900), (2250, 1960), (2450, 2050), (2650, 2110),
                   (2850, 2160), (2990, 2185), (3080, 2195)], step=4)
    W.waters.append(dict(id="WATER-01", name=N["river"], kind="river", width=58, line=main, to_sea=True, reach=150))
    split = int(np.argmin(np.hypot(main[:, 0] - 1600, main[:, 1] - 1880)))
    merge = int(np.argmin(np.hypot(main[:, 0] - 2080, main[:, 1] - 1900)))
    south = spline([(1600, 1880), (1700, 1980), (1850, 2015), (2000, 1985), (2080, 1900)], step=4)
    W.waters.append(dict(id="WATER-02", name=f"{N['river']} (south channel)", kind="river", width=40, line=south,
                         reach=60, levels_from="WATER-01", start_level=lambda s, i=split: float(s["levels"][i]),
                         end_level=lambda s, i=merge: float(s["levels"][i])))
    brook = spline([(1230, 180), (1280, 600), (1300, 900), (1290, 1150), (1200, 1350), (1080, 1550), (1040, 1700)], step=4)
    W.waters.append(dict(id="WATER-03", name=N["brook"], kind="stream", width=7, line=brook, reach=30))
    W.waters.append(dict(id="WATER-04", name=N["lake"], kind="lake", cx=520, cy=950, rx=230, ry=130,
                         line=np.array(ellipse_pts(520, 950, 230, 130, 64, 0.08, seed=4))))
    W.island = ellipse_pts(1845, 1905, 250, 92, 40)
    marsh = [(2600, 2470), (2980, 2450), (3060, 2520), (2960, 2700), (2700, 2690), (2580, 2600)]
    W.level_polys.append((marsh, SEA_LEVEL + 0.7))
    W.pastures.append(dict(name="Saltreed Marsh", poly=marsh, marsh=True))
    for i, (px, py, rx, ry) in enumerate([(2700, 2560, 30, 14), (2820, 2620, 22, 12), (2900, 2530, 26, 10)]):
        W.waters.append(dict(id=f"WATER-M{i}", name="Marsh pool", kind="pond", cx=px, cy=py, rx=rx, ry=ry,
                             line=np.array(ellipse_pts(px, py, rx, ry, 24))))
    pans = [(2990, 2560), (3090, 2560), (3080, 2720), (2990, 2720)]
    W.level_polys.append((pans, SEA_LEVEL + 0.4))
    for i in range(4):
        for j in range(3):
            x0, y0 = 2998 + i * 21, 2568 + j * 48
            W.fields.append(dict(name="Salt pan", field="Salt Pans", crop="saltpan",
                                 poly=[(x0, y0), (x0 + 18, y0), (x0 + 18, y0 + 44), (x0, y0 + 44)]))
    city = WALL_SOUTH + [(3060, 2390), (3080, 1950)] + WALL_NORTH + [(1700, 900), (1500, 1000)]
    W.city_poly = city
    W.built_polys = [city,
                     ellipse_pts(1340, 950, 170, 330, 30, 0.1, seed=11),            # Northgate suburb
                     ellipse_pts(3000, 1160, 140, 170, 30, 0.1, seed=12),           # Eastfold
                     ellipse_pts(3220, 3080, 140, 110, 30, 0.1, seed=13),           # Lantern Point
                     ellipse_pts(1830, 2640, 90, 70, 24, 0.1, seed=14),             # outside South Gate
                     ellipse_pts(1000, 1700, 110, 80, 24, 0.1, seed=15)]            # outside West Gate
    W.pads += [(1880, 1560, 110, 60, 0.9), (1650, 1440, 80, 35, 0.9), (2280, 1200, 230, 160, 0.6),
               (1600, 2400, 85, 85, 0.9), (1820, 2820, 230, 130, 0.8), (850, 2250, 180, 130, 0.8),
               (1300, 1620, 130, 130, 0.95), (1000, 1440, 110, 70, 0.9)]


def _rasters(W):
    W.zone_img = Image.new("L", (RN, RN), 0)
    W.zone_draw = ImageDraw.Draw(W.zone_img)
    d = W.zone_draw
    sea = [(x * RS, y * RS) for x, y in W.sea_poly]
    d.polygon(sea, fill=255)
    for w in W.waters:
        pts = [(x * RS, y * RS) for x, y in w["line"]]
        if w["kind"] in ("river", "stream"):
            d.line(pts, fill=255, width=int((w["width"] + (14 if w["kind"] == "river" else 8)) * RS))
        else:
            d.polygon(pts, fill=255)
    for poly, _ in W.level_polys:
        d.polygon([(x * RS, y * RS) for x, y in poly], fill=255)
    W.built_img = Image.new("L", (RN, RN), 0)
    bd = ImageDraw.Draw(W.built_img)
    for p in W.built_polys:
        bd.polygon([(x * RS, y * RS) for x, y in p], fill=255)


def _zone_now(W):
    W.zone = np.asarray(W.zone_img) > 0
    W.built = np.asarray(W.built_img) > 0


def _px(x, y):
    return (np.clip(np.asarray(x, dtype=float) * RS, 0, RN - 1).astype(int),
            np.clip(np.asarray(y, dtype=float) * RS, 0, RN - 1).astype(int))


def _free(W, xs, ys, street_ok=False, built=True):
    ix, iy = _px(xs, ys)
    bad = W.zone[iy, ix]
    if built:
        bad = bad | ~W.built[iy, ix]
    if not street_ok:
        bad = bad | W.street_mask[iy, ix]
    return ~bad


# ------------------------------------------------------------------ main roads & walls
def _main_roads(W):
    R = W.road
    R("North Road", "road", [(1300, -20), (1290, 300), (1340, 620), (1360, 900), (1390, 1150), (1420, 1310),
                             (1500, 1420), (1580, 1520), (1700, 1590), (1780, 1560)], 10, "cobble")
    R("West Road", "road", [(-20, 1300), (300, 1250), (700, 1180), (1000, 1360), (1110, 1500), (1240, 1520),
                            (1400, 1560), (1520, 1610), (1650, 1630)], 9, "cobble")
    R("Bridge Street", "street", [(1840, 1615), (1760, 1700), (1720, 1790), (1720, 1905), (1722, 2010),
                                  (1760, 2120), (1810, 2300), (1830, 2470), (1832, 2590), (1830, 2700)], 12, "cobble")
    R("South Road", "road", [(1830, 2700), (1790, 2960), (1720, 3300), (1760, 3700), (1700, 4120)], 9)
    R("West Bridge Street", "street", [(1330, 1560), (1370, 1700), (1382, 1840), (1390, 1980), (1420, 2120),
                                        (1350, 2330), (1260, 2420), (1100, 2420), (900, 2400), (600, 2350),
                                        (300, 2380), (-20, 2420)], 10, "cobble")
    R("Riverside Street", "street", [(1980, 1610), (2150, 1620), (2350, 1720), (2500, 1860), (2700, 1960),
                                     (2900, 1990), (3010, 1975)], 10, "cobble")
    R("Southbank Road", "street", [(1300, 2010), (1500, 2060), (1760, 2120), (2000, 2120), (2250, 2130),
                                   (2500, 2190), (2750, 2230), (2970, 2300), (3080, 2480), (3060, 2800),
                                   (3200, 3020), (3300, 3120)], 10, "cobble")
    R("Palace Way", "street", [(1860, 1520), (1980, 1400), (2100, 1360), (2300, 1380), (2480, 1400),
                               (2575, 1300), (2700, 1250), (2920, 1180), (3080, 1100), (3300, 900), (3550, 760)], 10, "cobble")
    R("Vineyard Lane", "lane", [(2470, 1020), (2400, 850), (2300, 600), (2300, 430)], 5)
    R("Mere Road", "road", [(700, 1180), (600, 1110), (520, 1080), (330, 1000), (-20, 900)], 6)
    R("Forest Track", "track", [(1340, 620), (1000, 520), (700, 350), (400, 200), (-20, 150)], 4)
    R("Old Ring Track", "track", [(900, 2400), (780, 2500), (700, 2600)], 4)
    R("Lantern Lane", "lane", [(3300, 3120), (3420, 3160), (3500, 3170)], 4)
    R("Raven Path", "path", [(3550, 760), (3700, 720), (3760, 720)], 2)
    R("Down Road", "track", [(1720, 3300), (1900, 3450), (2200, 3500), (2500, 3700)], 4)
    R("Abbey Lane", "lane", [(1790, 2960), (2000, 2930), (2250, 2900)], 5)


def _walls(W):
    rng = random.Random(SEED + 5)
    gates = {}
    roads = {r["name"]: r for r in W.roads}
    south = zigzag(WALL_SOUTH, rng=rng)
    north = zigzag(WALL_NORTH, rng=rng)
    W.wall_lines = [np.array(south), np.array(north)]
    for nm, rd in roads.items():
        if rd["kind"] not in ("road", "street", "lane"):
            continue
        for wl in W.wall_lines:
            d = dist_to(wl, rd["line"][:, 0], rd["line"][:, 1])
            i = int(np.argmin(d))
            if d[i] < 6:
                gx, gy = rd["line"][i]
                if all(math.hypot(gx - a, gy - b) > 60 for a, b in gates.values()):
                    gates[f"{nm} Gate"] = (float(gx), float(gy))
    names = {"North Road Gate": "North Gate", "West Road Gate": "West Gate", "Bridge Street Gate": "South Gate",
             "West Bridge Street Gate": "Scholars' Gate", "Southbank Road Gate": "Salt Gate",
             "Palace Way Gate": "Sea Gate", "Riverside Street Gate": "Harbour Gate", "Vineyard Lane Gate": "Vine Gate"}
    W.gates = {names.get(k, k): v for k, v in gates.items()}
    water = []
    for w in W.waters:
        if w["kind"] not in ("river", "stream"):
            continue
        for wl in W.wall_lines:
            d = dist_to(w["line"], wl[:, 0], wl[:, 1])
            for i in np.where(d < w["width"] / 2 + 4)[0]:
                x, y = wl[i]
                if all(math.hypot(x - a, y - b) > 50 for a, b in water):
                    water.append((float(x), float(y)))
    W.water_gates = water
    for line in (south, north):
        W.wall("City wall", "town", line, 13, 4, gaps=list(W.gates.values()) + water, gap_r=9)
        for k, (x, y) in enumerate(line):
            if k % 2 == 1 and all(math.hypot(x - a, y - b) > 30 for a, b in list(W.gates.values()) + water):
                W.tower("T", "Wall tower", x, y, 6.5, 19, roof=rng.choice(["cone", "crenel"]), group="City wall")
    for name, (x, y) in W.gates.items():
        rd = min(W.roads, key=lambda r: dist_to(r["line"], [x], [y])[0])
        i = int(np.argmin(np.hypot(rd["line"][:, 0] - x, rd["line"][:, 1] - y)))
        j = min(i + 2, len(rd["line"]) - 1)
        ang = math.degrees(math.atan2(rd["line"][j][1] - rd["line"][max(i - 2, 0)][1],
                                      rd["line"][j][0] - rd["line"][max(i - 2, 0)][0]))
        W.building("T", "gatehouse", name, x, y, 24, 18, ang + 90, 22, "crenel", material="stone", check=False,
                   passage_w=7, passage_h=8)
        t = math.radians(ang + 90)
        for s in (-1, 1):
            W.tower("T", f"{name} drum", x + s * 14 * math.cos(t), y + s * 14 * math.sin(t), 8, 25, roof="cone")
        W.landmark(name, x, y, "Gatehouse of the city wall.")
    for x, y in water:
        for s in (-1, 1):
            W.tower("T", "Water-gate tower", x, y + s * 40, 9, 24, roof="crenel")
        W.prop("chain_boom", x, y, 90, length=70)
    for x, y in [(3015, 1955), (2985, 2395)]:
        W.tower("T", "Sea tower", x, y, 12, 28, roof="crenel")
    # the old town's first wall: older, lower, with long stretches pulled down
    old = zigzag(OLD_WALL, step=55, amp=8, closed=True, rng=rng)
    keep = [(a, b) for i, (a, b) in enumerate(zip(old, old[1:] + old[:1])) if rng.random() < 0.6]
    for a, b in keep:
        W.wall("Old Town wall (ruinous)", "old", [a, b], 8, 2.5, material="stone")
        if rng.random() < 0.5:
            W.tower("O", "Old wall tower", *a, 5, 11, roof="cone", group="Old Town wall")
    W.landmark("The Old Town Wall", *OLD_WALL[3], "The city's first wall, 400 years old; long stretches pulled down for houses.")


# ------------------------------------------------------------------ the giant castle
def _castle(W):
    cx, cy = CASTLE
    L = lambda x, y: (cx + x, cy + y)
    b = W.building
    outer = [L(*p) for p in [(-175, -110), (-95, -165), (95, -165), (175, -110), (195, 40), (120, 150), (-120, 150), (-195, 40)]]
    W.wall("Crownhold outer curtain", "curtain", outer, 20, 5.5, closed=True, gaps=[L(0, 150), L(150, 95)], gap_r=12)
    towers = []
    for i, p in enumerate(outer):
        q = outer[(i + 1) % len(outer)]
        towers += [p, ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)]
    for k, (x, y) in enumerate(towers):
        if math.hypot(x - L(0, 150)[0], y - L(0, 150)[1]) < 20:
            continue
        W.tower("C", f"Outer Tower {k + 1}", x, y, 10 if k % 2 == 0 else 8, 28 if k % 2 == 0 else 24)
    inner = [L(-110, -100), L(110, -100), L(118, 60), L(-118, 60)]
    W.wall("Crownhold inner curtain", "inner", inner, 26, 5, closed=True, gaps=[L(0, 60)], gap_r=8)
    for k, p in enumerate(inner):
        q = inner[(k + 1) % 4]
        W.tower("C", ["King's Tower", "Queen's Tower", "Treasury Tower", "Chapel Tower"][k], *p, 11, 34)
        W.tower("C", "Inner wall tower", (p[0] + q[0]) / 2, (p[1] + q[1]) / 2, 7, 30)
    b("C", "keep", N["keep"], *L(0, -35), 38, 38, 180, 50, "crenel", material="stone", floors=8, check=False)
    for dx, dy in [(-19, -19), (19, -19), (-19, 19), (19, 19)]:
        W.tower("C", "Crown Tower turret", *L(dx, -35 + dy), 5, 58, group=N["keep"])
    b("C", "hall", "Great Hall of the Kings", *L(-70, -25), 56, 18, 90, 19, "gable", material="stone", check=False)
    b("C", "chapel", "Royal Chapel", *L(72, -50), 34, 14, 0, 17, "gable", material="stone", check=False)
    b("C", "palace", "Royal Apartments", *L(0, 35), 80, 15, 180, 17, "hip", material="stone", floors=3, check=False)
    b("C", "house", "Treasury", *L(72, 20), 24, 15, 270, 13, "hip", material="stone", floors=3, check=False)
    b("C", "barracks", "Barracks of the King's Guard", *L(-150, -20), 80, 14, 90, 10, "gable", material="stone", floors=2, check=False)
    b("C", "stables", "Royal Stables", *L(150, -20), 80, 14, 270, 8, "gable", material="timber", check=False)
    b("C", "armoury", "Armoury", *L(-90, 110), 34, 14, 0, 10, "gable", material="stone", floors=2, check=False)
    b("C", "mint", "Royal Mint", *L(90, 110), 30, 14, 0, 10, "gable", material="stone", floors=2, check=False)
    b("C", "house", "Great Kitchen", *L(-75, 38), 22, 16, 0, 10, "hip", material="stone", check=False)
    b("C", "gatehouse", "King's Gate", *L(0, 150), 34, 26, 180, 30, "crenel", material="stone", check=False,
      passage_w=7, passage_h=9)
    W.tower("C", "King's Gate drum (west)", *L(-19, 156), 10, 32)
    W.tower("C", "King's Gate drum (east)", *L(19, 156), 10, 32)
    b("C", "gatehouse", "Postern to the Sea Road", *L(150, 95), 16, 14, 135, 18, "crenel", material="stone",
      check=False, passage_w=4, passage_h=5)
    b("C", "gatehouse", "Inner Gate", *L(0, 60), 20, 15, 180, 26, "crenel", material="stone", check=False,
      passage_w=5, passage_h=7)
    W.prop("altar_stone", *L(-30, 95), name="The Crowning Stone", w=3.2, d=2.2, h=1.3)
    for k in range(8):
        W.prop("training_dummy", *L(-60 + k * 15, 125))
    W.prop("well", *L(35, -80), name="Keep well")
    W.paved_polys.append(outer)
    W.road("Castle Ramp", "street", [L(0, 165), L(-60, 210), L(-100, 260), (1500, 1420)], 9, "cobble")
    site(W, N["castle"], cx, cy, "castle", "The giant royal castle on its crag: two curtain walls, 26 towers and a 50 m keep.",
         zone=("circle", cx, cy, 215))
    W.landmark(N["keep"], *L(0, -35), "50 m great keep, eight storeys: the throne room is on the fifth.")
    W.landmark("The Crowning Stone", *L(-30, 95), "A prehistoric stone carried up from the river: every monarch is crowned on it.")


# ------------------------------------------------------------------ site kit
def courtyard(W, dist, name, cx, cy, w, d, heading, h=11, floors=2, material="stone", kind="college",
              depth=11, roof="gable", court="pasture"):
    F = frame(cx, cy, heading)
    b = W.building
    b(dist, kind, f"{name} (front range)", *F(0, -d / 2 + depth / 2), w, depth, heading, h, roof,
      material=material, floors=floors, check=False, group=name)
    b(dist, kind, f"{name} (back range)", *F(0, d / 2 - depth / 2), w, depth, heading + 180, h, roof,
      material=material, floors=floors, check=False, group=name)
    for s, nm in ((-1, "west"), (1, "east")):
        b(dist, kind, f"{name} ({nm} range)", *F(s * (w / 2 - depth / 2), 0), d - 2 * depth, depth,
          heading + (90 if s > 0 else 270), h, roof, material=material, floors=floors, check=False, group=name)
    ci = [F(-w / 2 + depth, -d / 2 + depth), F(w / 2 - depth, -d / 2 + depth), F(w / 2 - depth, d / 2 - depth),
          F(-w / 2 + depth, d / 2 - depth)]
    if court == "pasture":
        W.pastures.append(dict(name=f"{name} court", poly=ci))
    else:
        W.paved_polys.append(ci)
    return F


def ring_building(W, dist, name, cx, cy, r_out, r_in, h, n, kind="theatre", material="timber", roof="gable",
                  gap_deg=None, tiers=1):
    """Ring of wedge-shaped ranges round an open yard (playhouses, amphitheatres, bear gardens)."""
    for t in range(tiers):
        ro = r_in + (r_out - r_in) * (t + 1) / tiers
        ri = r_in + (r_out - r_in) * t / tiers
        for k in range(n):
            a = 360 * (k + 0.5) / n
            if gap_deg is not None and abs((a - gap_deg + 180) % 360 - 180) < 360 / n * 0.8:
                continue
            rm = (ro + ri) / 2
            x, y = cx + rm * math.cos(math.radians(a)), cy + rm * math.sin(math.radians(a))
            width = 2 * math.pi * rm / n + 0.6
            W.building(dist, kind, f"{name} (tier {t + 1})" if tiers > 1 else name, x, y, width, ro - ri,
                       a - 90, h * (t + 1) / tiers, roof if tiers == 1 else "flat",
                       material=material, check=False, group=name, floors=1)


def tents(W, name, x0, y0, x1, y1, step, rng, colors=("red", "blue", "cream"), heading=0, big=False):
    for gx in np.arange(x0 + step / 2, x1, step):
        for gy in np.arange(y0 + step / 2, y1, step):
            if rng.random() < 0.15:
                continue
            W.prop("tent", gx + rng.uniform(-1, 1), gy + rng.uniform(-1, 1), heading, color=rng.choice(colors),
                   w=round(rng.uniform(4, 6) * (1.6 if big else 1), 1), d=round(rng.uniform(3.5, 5) * (1.4 if big else 1), 1),
                   group=name)


def market(W, name, box, stalls, desc, kind="market", hall=None, landmark=True):
    W.squares.append(dict(name=name, box=box, kind=kind))
    site(W, name, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, kind, desc, zone=("rect",) + tuple(box), landmark=landmark)
    rng = W.rng
    x0, y0, x1, y1 = box
    n = 0
    for gy in np.arange(y0 + 9, y1 - 6, 8.5):
        for gx in np.arange(x0 + 9, x1 - 6, 6.5):
            if n >= stalls:
                break
            if rng.random() < 0.35 or math.hypot(gx - 1815, gy - 1530) < 24:     # keep off the Moot Hill
                continue
            W.prop("market_stall", gx, gy, 0 if int(gy) % 2 else 180, w=4.2, d=3, group=f"{name} stalls")
            n += 1
    if hall:
        W.building(district_at(*hall[:2])[1], "market_hall", f"{name} hall", *hall, 0, 7, "hip", material="timber",
                   check=False)


def stone_circle(W, name, cx, cy, r, n, h=(1.6, 2.6), group=None):
    for i in range(n):
        t = 2 * math.pi * i / n
        W.prop("standing_stone", cx + r * math.cos(t), cy + r * math.sin(t), math.degrees(t) + 90,
               h=round(W.rng.uniform(*h), 1), w=round(W.rng.uniform(1.0, 1.7), 1), d=0.8, group=group or name,
               lean=round(W.rng.uniform(-6, 6), 1))


def pocket_label(W, name, x, y, desc):
    """A small preserved prehistoric place: fenced, grassed, signposted."""
    W.prehistoric.append(dict(name=name, x=x, y=y, desc=desc))
    site(W, name, x, y, "prehistoric", desc)


# ------------------------------------------------------------------ old town
def _old_town(W):
    W.prehistoric = []
    rng = W.rng
    b = W.building
    market(W, "The Grand Market", (1785, 1505, 1975, 1612), 120,
           "Biggest market in the city: cloth, pots, poultry, cheese, everything; the Moot Hill rises in its corner.")
    W.earthworks.append(dict(kind="mound", name="Moot Hill", x=1815, y=1530, rx=14, ry=14, h=4.5))
    pocket_label(W, "Moot Hill", 1815, 1530, "A Bronze Age burial mound left in the Grand Market; the city's assemblies are still held on top.")
    b("O", "guildhall", "Guildhall of Stonehallow", 1880, 1490, 64, 18, 180, 18, "hip", material="stone", floors=3, check=False)
    b("O", "belfry", "Town Belfry", 1990, 1560, 14, 14, 270, 58, "spire", roof_h=16, material="stone", floors=10, check=False)
    b("O", "hall", "Town Hall", 1990, 1592, 30, 22, 270, 16, "hip", material="stone", floors=3, check=False)
    W.reserve_box(1840, 1475, 1925, 1500)
    W.prop("fountain", 1900, 1560, r=6)
    W.prop("market_cross", 1940, 1590, name="Market Cross")
    # the Kingstone and your house
    market(W, "Kingstone Square", (1625, 1585, 1690, 1640), 0, "Little square round the Kingstone.", kind="square",
           landmark=False)
    W.prop("menhir", 1657, 1612, 0, h=6.5, w=1.8, d=1.3, name="The Kingstone")
    pocket_label(W, "The Kingstone", 1657, 1612, "A 6 m menhir at the crossroads where the North and West roads meet. Older than any road.")
    b("O", "manor_house", f"{YOUR_HOUSE} (your house)", 1657, 1658, 18, 12, 0, 11, "hip", material="stone",
      floors=3, owner=YOU, check=False)
    W.reserve_box(1645, 1650, 1670, 1665)
    W.landmark(f"{YOUR_HOUSE} - YOUR HOUSE", 1657, 1658, f"Home of {YOU}, facing the Kingstone. Start here.")
    # more markets & halls
    b("O", "bazaar", "The Spice Bazaar (covered street)", 2075, 1520, 160, 16, 25, 9, "gable", material="timber",
      check=False)
    site(W, "The Spice Bazaar", 2075, 1520, "market", "A 160 m covered street of spice, silk and incense sellers.",
         zone=("poly", [(2000, 1475), (2160, 1545), (2150, 1568), (1990, 1497)]))
    b("O", "hall", "Wool Hall", 2010, 1685, 60, 22, 180, 12, "gable", material="stone", floors=2, check=False)
    site(W, "Wool Hall", 2010, 1685, "market", "Wool exchange: fleeces from a hundred hill farms are graded and sold.",
         zone=("rect", 1975, 1670, 2045, 1700))
    market(W, "Muster Square", (1575, 1415, 1725, 1470), 0, "Parade ground below the castle where the city militia drills.",
           kind="square")
    W.prop("statue", 1650, 1442, 0, h=6, name="Statue of the First King")
    market(W, "Shambles Market", (1960, 1620, 2010, 1660), 14, "The butchers' street-market (bring a strong stomach).")
    site(W, "The Sleeping Giant inn", 1740, 1660, "inn", "The oldest inn in the city, built against the Old Town wall.")
    b("O", "inn", N["inn"], 1740, 1662, 22, 14, 0, 11, "gable", material="timber", floors=3, check=False)
    W.reserve_box(1725, 1652, 1755, 1672)


def _isle(W):
    b = W.building
    c = N["cathedral"]
    b("I", "cathedral", f"{c} (nave)", 1830, 1905, 100, 28, 0, 32, "gable", material="stone", group=c, check=False)
    b("I", "cathedral", f"{c} (choir)", 1905, 1905, 50, 24, 0, 30, "gable", material="stone", group=c, check=False)
    b("I", "cathedral", f"{c} (transepts)", 1880, 1905, 24, 66, 0, 32, "gable", material="stone", group=c, check=False)
    b("I", "cathedral", f"{c} (crossing tower & spire)", 1880, 1905, 24, 24, 0, 60, "spire", roof_h=60,
      material="stone", group=c, check=False, floors=12)
    for dy in (-15, 15):
        b("I", "cathedral", f"{c} (west tower)", 1772, 1905 + dy, 16, 16, 0, 66, "crenel", material="stone",
          group=c, check=False, floors=12)
    b("I", "chapter_house", "Chapter House", 1940, 1950, 20, 20, 0, 14, "cone", roof_h=9, material="stone",
      shape="round", check=False)
    b("I", "palace", "Bishop's Palace", 1990, 1930, 36, 12, 90, 13, "hip", material="stone", floors=3, check=False)
    courtyard(W, "I", "Cloister", 1840, 1952, 56, 36, 0, h=9, floors=1, kind="cloister", depth=8)
    W.prop("dolmen", 1675, 1880, 20, name="The Three Kings' Table", w=5.5, d=3.2, h=2.6)
    pocket_label(W, "The Three Kings' Table", 1675, 1880, "A portal tomb on the Minster lawn; the island was holy before the Minster was.")
    W.green_polys.append(W.island)
    W.pastures.append(dict(name="Minster lawn", poly=[(1650, 1850), (1705, 1850), (1705, 1950), (1650, 1950)]))
    site(W, c, 1860, 1905, "cathedral", "Gothic cathedral on King's Isle; its spire reaches 120 m, the tallest thing in the realm.",
         zone=("poly", ellipse_pts(1855, 1905, 215, 80, 30)))
    br = dict(name="Grand Bridge (north span)", road="Bridge Street", x=1720.0, y=1800.0, heading=90.0, length=70.0,
              width=24.0, material="stone", arches=6, inhabited=True)
    W.explicit_bridges.append(br)
    for y in np.arange(1772, 1830, 8.2):
        for side in (-1, 1):
            first, trade = W.person(TRADES)
            b("R", "shop", f"Bridge house of {first} the {trade}", 1720 + side * 8.5, y + 4, 8, 7, 90 if side < 0 else 270,
              9, "gable", material="timber", floors=3, check=False, on_bridge=br["name"], trade=trade, resident=first)
    W.explicit_bridges.append(dict(name="Grand Bridge (south span)", road="Bridge Street", x=1722.0, y=2005.0,
                                   heading=90.0, length=62.0, width=14.0, material="stone", arches=5))
    W.landmark("The Grand Bridge", 1720, 1800, "Two stone spans across both arms of the river; the north span carries 14 shops.")


def _palace(W):
    b = W.building
    rng = W.rng
    x0, y0, x1, y1 = 2060, 1060, 2520, 1345
    W.wall("Palace garden wall", "precinct", [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 4, 1.2, closed=True,
           gaps=[(2280, y1), (x0, 1200)], gap_r=8)
    b("P", "palace", f"{N['palace']}", 2280, 1095, 170, 22, 180, 20, "hip", material="stone", floors=3, check=False)
    for dx in (-95, 95):
        b("P", "palace", f"{N['palace']} (wing)", 2280 + dx, 1125, 22, 70, 180, 18, "hip", material="stone",
          floors=3, check=False, group=N["palace"])
    # seven gardens
    mx, my, cell, n = 2090, 1150, 6.0, 11
    for s in _maze(n, random.Random(7)):
        W.wall("Queen's Maze", "hedge", [(mx + s[0] * cell, my + s[1] * cell), (mx + s[2] * cell, my + s[3] * cell)],
               2.4, 0.9, material="hedge")
    W.prop("sundial", mx + n * cell / 2, my + n * cell / 2)
    for k in range(8):
        px, py = 2180 + (k % 4) * 40, 1170 + (k // 4) * 42
        W.fields.append(dict(name="Parterre", field="Palace", crop="herbs",
                             poly=[(px, py), (px + 32, py), (px + 32, py + 34), (px, py + 34)]))
    W.prop("fountain", 2260, 1215, r=9)
    W.waters.append(dict(id="WATER-PG", name="Water Garden canal", kind="pond", cx=2400, cy=1300, rx=70, ry=12,
                         line=np.array(ellipse_pts(2400, 1300, 70, 12, 30))))
    for k in range(10):
        W.groves.append((2350 + (k % 5) * 30, 1170 + (k // 5) * 50, "apple", 5))
    for k in range(12):
        W.groves.append((2080 + k * 36, 1335, "lime", 13))
    # menagerie
    for k in range(6):
        px, py = 2420 + (k % 3) * 28, 1180 + (k // 3) * 34
        W.prop("pen", px, py, 0, w=22, d=26, group="Royal Menagerie pens")
        b("P", "shed", "Animal house", px, py - 9, 10, 6, 180, 4, "gable", material="timber", check=False)
    site(W, "The Royal Menagerie", 2450, 1200, "menagerie", "Lions, a bear, an elephant from the south and the King's white stags.",
         landmark=True)
    W.earthworks.append(dict(kind="mound", name="Giant's Grave", x=2140, y=1300, rx=42, ry=10, h=3.6, heading=8))
    pocket_label(W, "The Giant's Grave", 2140, 1300, "A 90 m long barrow kept as a lawn in the palace gardens.")
    W.green_polys.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    W.pastures.append(dict(name="Palace lawns", poly=[(x0 + 4, y0 + 60), (x1 - 4, y0 + 60), (x1 - 4, y1 - 4), (x0 + 4, y1 - 4)]))
    site(W, N["palace"], 2280, 1200, "palace", "The royal summer palace and its seven gardens: maze, parterres, orchard, "
         "water garden, lime walk, menagerie and the Giant's Grave.", zone=("rect", x0, y0, x1, y1))
    W.landmark("The Queen's Maze", mx + n * cell / 2, my + n * cell / 2, "A 66 m hedge maze with a sundial stone at its heart.")
    market(W, "Flower Market", (2095, 1380, 2165, 1425), 24, "Flowers, herbs and songbirds for the palace quarter.")
    for k in range(6):
        mb = b("P", "mansion", f"Townhouse of Lord {rng.choice(FIRST)}", *[(2200, 1450), (2330, 1440), (2450, 1460),
                                                                           (2140, 1560), (2560, 1500), (2470, 1560)][k],
               30, 18, rng.choice([0, 180]), 13, "hip", material="stone", floors=3, optional=True)
        if mb:
            _block(W, ("rect", mb["x"] - 20, mb["y"] - 14, mb["x"] + 20, mb["y"] + 14))
    W.vineyards = [(2080, 790, 2560, 960)]


# ------------------------------------------------------------------ merchants, harbour
def _merchants_and_harbour(W):
    b = W.building
    rng = W.rng
    b("M", "exchange", "Grain Exchange", 2410, 1620, 70, 30, 0, 14, "hip", material="stone", floors=2, check=False)
    site(W, "Grain Exchange", 2410, 1620, "market", "Corn factors shout prices under the great timber roof.",
         zone=("rect", 2370, 1600, 2450, 1640))
    for k, (x, y) in enumerate([(2270, 1560), (2330, 1745), (2560, 1640), (2190, 1700)]):
        courtyard(W, "M", f"Merchant palace of the {['Moneylenders', 'Wine Merchants', 'Spice Merchants', 'Silk Traders'][k]}",
                  x, y, 44, 40, rng.choice([0, 10, -10]), h=13, floors=3, kind="mansion", depth=10, roof="hip", court="paved")
        _block(W, ("rect", x - 26, y - 24, x + 26, y + 24))
    site(W, "Merchant Palaces", 2330, 1660, "quarter", "Four courtyard palaces of the great trading houses.", landmark=True)
    b("M", "hall", "Money-changers' Hall", 2300, 1480, 30, 16, 0, 11, "hip", material="stone", floors=2, check=False)
    W.reserve_box(2283, 1470, 2317, 1490)
    # harbour: quays, warehouses, ships, fish market, lighthouse on the breakwater
    river = W.waters[0]["line"]
    quay = [p for p in river if 2420 < p[0] < 2990]
    for i in range(0, len(quay) - 1, 8):
        x, y = quay[i]
        nx, ny = quay[min(i + 1, len(quay) - 1)]
        ang = math.degrees(math.atan2(ny - y, nx - x))
        n_x, n_y = math.sin(math.radians(ang)), -math.cos(math.radians(ang))      # towards the north bank
        if i % 24 == 0:
            W.prop("crane", x + n_x * 34, y + n_y * 34)
        if i % 16 == 8:
            W.prop("ship", x + n_x * 14, y + n_y * 14, ang, length=rng.choice([22, 26, 30]), w=7)
        wb = b("H", "warehouse", "Harbour warehouse", x + n_x * 60, y + n_y * 60, 26, 14, ang + 180, 12, "gable",
               material="timber", floors=3, optional=True)
        if wb:
            _block(W, ("poly", rect_corners(wb["x"], wb["y"], 30, 18, wb["heading"])))
    W.paved_polys.append([tuple(p) for p in [(2420, 1990), (2990, 2130), (2990, 2160), (2420, 2020)]])
    W.quay_poly = [(x, y - 52) for x, y in quay[::6]] + [(x, y - 26) for x, y in quay[::-6]]
    _block(W, ("poly", W.quay_poly))
    site(W, "King's Quay", 2700, 2060, "harbour", "Half a kilometre of stone quays, warehouses, treadwheel cranes and cogs from overseas.")
    market(W, "Fish Market", (2640, 1960, 2710, 1995), 26, "Fishwives, oysters and the catch of the morning boats.")
    for args in [("customs", "Custom House", 2580, 1975, 34, 14, 0, 12, "hip"),
                 ("chapel", "Sailors' Chapel of St. Nicholas", 2860, 2005, 22, 10, 0, 10, "gable")]:
        bb = b("H", *args, material="stone", floors=2, optional=True)
        if bb:
            _block(W, ("poly", rect_corners(bb["x"], bb["y"], bb["w"] + 4, bb["d"] + 4, bb["heading"])))
    b("H", "ropewalk", "The Ropewalk", 2600, 1875, 300, 8, 18, 4, "gable", material="timber", check=False)
    site(W, "The Ropewalk", 2600, 1875, "industry", "A shed 300 m long where hemp is twisted into ships' cables.",
         zone=("poly", [(2455, 1820), (2745, 1915), (2742, 1930), (2452, 1835)]))
    W.road("Breakwater", "pier", [(3030, 1975), (3120, 2010), (3210, 2040)], 9, "cobble")
    W.tower("H", "Harbour Light", 3215, 2042, 6, 30, roof="crenel")
    W.prop("beacon", 3215, 2042, lift=30)
    site(W, "Harbour Light", 3215, 2042, "lighthouse", "Lighthouse at the end of the breakwater guiding cogs into the river mouth.")


# ------------------------------------------------------------------ military
def _military(W):
    b = W.building
    rng = W.rng
    # the Star Citadel: a zig-zag bastioned fortress guarding the river where it enters the city
    cx, cy, r = 1300, 1620, 125
    pts = []
    for k in range(10):
        a = math.radians(k * 36 - 90)
        rr = r if k % 2 == 0 else r * 0.62
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    W.wall(N["citadel"], "curtain", pts, 12, 7, closed=True, gaps=[pts[5]], gap_r=6)
    for k in range(0, 10, 2):
        W.tower("W", "Citadel bastion tower", *pts[k], 7, 16, roof="crenel", group=N["citadel"])
    b("W", "barracks", "Citadel barracks (north)", cx, cy - 40, 70, 13, 180, 10, "gable", material="stone", floors=2, check=False)
    b("W", "barracks", "Citadel barracks (south)", cx, cy + 40, 70, 13, 0, 10, "gable", material="stone", floors=2, check=False)
    b("W", "magazine", "Powder & arrow magazine", cx - 45, cy, 16, 26, 90, 8, "hip", material="stone", check=False)
    b("W", "house", "Governor's house", cx + 45, cy, 18, 24, 270, 11, "hip", material="stone", floors=3, check=False)
    W.paved_polys.append(pts)
    site(W, N["citadel"], cx, cy, "military", "Five-pointed bastioned fortress guarding the river's entry into the city.",
         zone=("circle", cx, cy, r + 10))
    for k, (x, y) in enumerate([(1330, 1430), (1410, 1470)]):
        b("W", "arsenal", ["The Arsenal", "Armourers' Hall"][k], x, y, 70 - k * 20, 22, rng.choice([10, -10]), 13, "gable",
          material="stone", floors=2, check=False)
    site(W, "The Arsenal", 1360, 1450, "military", "Where the city's crossbows, pikes and siege engines are built and stored.",
         zone=("rect", 1290, 1415, 1445, 1490))
    # drill field and archery butts outside the west wall
    W.squares.append(dict(name="Drill Field", box=(900, 1380, 1100, 1500), kind="fair"))
    for k in range(6):
        W.prop("target", 1090, 1395 + k * 20, 270, group="Archery butts")
    for k in range(4):
        for j in range(6):
            W.prop("training_dummy", 930 + j * 12, 1420 + k * 18)
    site(W, "Drill Field & Archery Butts", 1000, 1440, "military", "Every man of the city must shoot at the butts on Sundays.",
         zone=("rect", 900, 1380, 1100, 1500))
    # the army camp
    x0, y0, x1, y1 = 680, 2130, 1020, 2370
    W.wall("Camp palisade", "palisade", [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 3.5, 0.6, closed=True,
           gaps=[(x1, 2250), ((x0 + x1) / 2, y0)], gap_r=8, material="wood")
    tents(W, N["camp"], x0 + 10, y0 + 10, x1 - 10, y1 - 70, 11, rng, colors=("cream", "cream", "red"))
    W.prop("pavilion", 850, 2330, r=9, name="Commander's pavilion")
    for k in range(5):
        b("X", "stables", "Horse lines", 720 + k * 60, 2350, 40, 8, 0, 4, "gable", material="timber", check=False)
    for k in range(3):
        W.prop("trebuchet", 1060 + k * 30, 2060, 0, group="Siege engines")
    b("X", "workshop", "Siege engine workshop", 1000, 2030, 50, 18, 0, 10, "gable", material="timber", check=False)
    site(W, N["camp"], 850, 2250, "military", "A standing camp of 2,000 soldiers: tents, horse lines and a palisade.",
         zone=("rect", x0, y0, x1, y1))
    site(W, "Siege Yard", 1040, 2050, "military", "Trebuchets and mangonels being built and tested.",
         zone=("rect", 970, 2010, 1110, 2085))
    W.squares.append(dict(name="Cavalry Paddocks", box=(470, 2120, 660, 2300), kind="fair"))
    for k in range(6):
        W.prop("pen", 500 + (k % 3) * 60, 2160 + (k // 3) * 80, 0, w=50, d=60, group="Paddock fences")
    site(W, "Cavalry Paddocks", 565, 2210, "military", "Grazing and training for the knights' horses.",
         zone=("rect", 470, 2120, 660, 2300))


# ------------------------------------------------------------------ south bank
def _southbank(W):
    b = W.building
    rng = W.rng
    market(W, "Night Market", (1850, 2140, 1940, 2195), 40, "Opens at dusk under lanterns: hot food, music, fortune-tellers.")
    for k in range(10):
        W.prop("lantern", 1850 + k * 10, 2140)
    ring_building(W, "S", N["playhouse"], 1995, 2245, 26, 17, 11, 20, gap_deg=270)
    b("S", "stage", "Playhouse stage", 1995, 2232, 14, 9, 180, 4, "gable", material="timber", check=False)
    site(W, N["playhouse"], 1995, 2245, "entertainment", "Round wooden playhouse for 1,500: comedies, tragedies and riots.",
         zone=("circle", 1995, 2245, 30))
    ring_building(W, "S", "Bear Garden", 2080, 2300, 17, 11, 7, 14, gap_deg=90)
    site(W, "Bear Garden", 2080, 2300, "entertainment", "Animal-baiting pit and its noisy galleries.", zone=("circle", 2080, 2300, 20))
    for k, (x, y) in enumerate([(2130, 2185), (1780, 2290)]):
        courtyard(W, "S", f"Bathhouse {['of the Swan', 'of the Mermaid'][k]}", x, y, 40, 32, 0, h=8, floors=2,
                  kind="bathhouse", depth=9, court="paved")
        W.prop("fountain", x, y, r=5)
        site(W, f"Bathhouse {['of the Swan', 'of the Mermaid'][k]}", x, y, "bathhouse", "Steam rooms, tubs and gossip.",
             zone=("rect", x - 22, y - 18, x + 22, y + 18))
    # pleasure gardens with a tiny stone circle
    x0, y0, x1, y1 = 2200, 2240, 2400, 2400
    W.wall("Lantern Gardens hedge", "hedge", [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 2.2, 1.0, closed=True,
           gaps=[(2300, y0)], gap_r=6, material="hedge")
    for k in range(30):
        W.prop("lantern", x0 + 10 + (k % 10) * 20, y0 + 20 + (k // 10) * 60)
    for k in range(16):
        W.groves.append((x0 + 15 + (k % 8) * 24, y0 + 50 + (k // 8) * 60, "lime", 11))
    b("S", "pavilion", "Music pavilion", 2250, 2330, 14, 14, 0, 6, "cone", roof_h=6, material="timber", shape="round", check=False)
    stone_circle(W, "The Nine Sisters", 2340, 2330, 12, 9)
    pocket_label(W, "The Nine Sisters", 2340, 2330, "Nine little stones in a ring, kept inside the pleasure gardens; lovers meet here.")
    W.green_polys.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    W.pastures.append(dict(name="Lantern Gardens", poly=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))
    site(W, "Lantern Gardens", 2300, 2320, "garden", "Pleasure gardens lit with a thousand lanterns on summer nights.",
         zone=("rect", x0, y0, x1, y1))
    # the great auditorium: stone amphitheatre for assemblies, plays and tournaments
    ring_building(W, "D", N["amphitheatre"], 1600, 2400, 78, 34, 18, 32, kind="amphitheatre", material="stone",
                  gap_deg=0, tiers=4)
    W.squares.append(dict(name="Auditorium arena", box=(1572, 2372, 1628, 2428), kind="fair"))
    site(W, N["amphitheatre"], 1600, 2400, "entertainment", "Stone amphitheatre seating 8,000 for proclamations, plays and tournaments.",
         zone=("circle", 1600, 2400, 82))
    market(W, "Cattle Market", (1840, 2440, 1960, 2515), 0, "Pens of cattle, sheep and pigs inside the South Gate.")
    for k in range(10):
        W.prop("pen", 1852 + (k % 5) * 22, 2458 + (k // 5) * 30, 0, w=18, d=24, group="Cattle pens")
    # tanners' reach: industry
    tx0, ty0 = 2420, 2140
    for k in range(4):
        b("T", "tannery", f"Tannery {k + 1}", tx0 + 20 + k * 45, ty0 + 25, 30, 14, 0, 7, "gable", material="timber", check=False)
        for j in range(6):
            W.prop("vat", tx0 + 8 + k * 45 + j * 5, ty0 + 45, color="brown")
    for k in range(3):
        b("T", "dyeworks", f"Dye works {k + 1}", tx0 + 30 + k * 55, ty0 + 85, 34, 14, 0, 7, "gable", material="timber", check=False)
        for j in range(6):
            W.prop("vat", tx0 + 16 + k * 55 + j * 5, ty0 + 105, color=["red", "blue", "yellow"][k])
    for k in range(3):
        b("T", "kiln", "Brick kiln", tx0 + 30 + k * 26, ty0 + 150, 12, 12, 0, 7, "cone", roof_h=8, material="stone",
          shape="round", check=False)
    b("T", "foundry", "Bell foundry", tx0 + 140, ty0 + 150, 26, 18, 0, 10, "gable", material="stone", check=False)
    b("T", "glassworks", "Glassworks", tx0 + 190, ty0 + 150, 18, 18, 0, 9, "cone", roof_h=10, material="stone",
      shape="round", check=False)
    b("T", "brewery", "Brewery of the Three Barrels", tx0 + 190, ty0 + 40, 30, 16, 180, 10, "gable", material="timber",
      floors=2, check=False)
    for k in range(8):
        W.prop("timber_stack", tx0 + 10 + k * 9, ty0 + 185)
    site(W, "Tanners' Reach", 2520, 2230, "industry", "Downwind and downstream: tanneries, dye vats in three colours, kilns, "
         "a bell foundry, glassworks and a brewery.", zone=("rect", tx0, ty0, tx0 + 215, ty0 + 195))
    # shipyard
    for k in range(4):
        x = 2690 + k * 60
        W.prop("ship", x, 2240, 75, length=30 - k * 2, w=8, slip=True, group="Ships on the slipways")
        b("Y", "shed", f"Slipway shed {k + 1}", x, 2295, 22, 14, 165, 10, "gable", material="timber", check=False)
    b("Y", "sail_loft", "Sail loft", 2700, 2350, 50, 14, 0, 12, "gable", material="timber", floors=3, check=False)
    b("Y", "arsenal", "Naval arsenal", 2800, 2360, 60, 18, 0, 12, "gable", material="stone", floors=2, check=False)
    W.waters.append(dict(id="WATER-MP", name="Mast pond", kind="pond", cx=2900, cy=2330, rx=34, ry=14,
                         line=np.array(ellipse_pts(2900, 2330, 34, 14, 24))))
    site(W, "The Shipyard", 2800, 2300, "industry", "Four slipways building war cogs for the crown, with a sail loft and mast pond.",
         zone=("rect", 2650, 2215, 2960, 2385))


def _scholars(W):
    b = W.building
    for k, (x, y, w, d) in enumerate([(1290, 2110, 80, 66), (1395, 2120, 76, 66), (1300, 2210, 86, 64)]):
        nm = ["College of the Seven Stars", "Henge College", "College of Physicians"][k]
        courtyard(W, "U", nm, x, y, w, d, [5, -4, 2][k], h=12, floors=3, kind="college")
        site(W, nm, x, y, "college", "A college of the university: hall, chapel, library and rooms round a grass court.",
             zone=("rect", x - w / 2 - 3, y - d / 2 - 3, x + w / 2 + 3, y + d / 2 + 3), landmark=k == 0)
    b("U", "library", "University Library", 1440, 2210, 52, 16, 180, 14, "hip", material="stone", floors=3, check=False)
    ring_building(W, "U", "Hall of Disputations", 1500, 2265, 22, 12, 10, 14, kind="auditorium", material="stone",
                  roof="flat", gap_deg=270)
    b("U", "auditorium", "Hall of Disputations (lectern hall)", 1500, 2252, 16, 8, 0, 8, "gable", material="stone", check=False)
    W.tower("U", "Observatory Tower", 1250, 2275, 7, 38, roof="cone")
    ring_building(W, "U", "Anatomy Theatre", 1440, 2275, 12, 6, 9, 10, kind="auditorium", material="timber", roof="flat")
    W.fields.append(dict(name="Physic Garden", field="University", crop="herbs",
                         poly=[(1270, 2250), (1330, 2250), (1330, 2300), (1270, 2300)]))
    for k in range(8):
        W.prop("standing_stone", 1300 + k * 8, 2330 + k * 3, 70, h=round(1.4 + W.rng.random(), 1), w=1.0, d=0.6,
               group="The Druids' Row")
    W.pastures.append(dict(name="Scholars' Park", poly=[(1260, 2310), (1380, 2310), (1380, 2360), (1260, 2360)]))
    pocket_label(W, "The Druids' Row", 1330, 2340, "Eight stones in a dead-straight line; the astronomers say it points at the midwinter sunrise.")
    site(W, "Scholars' Hill University", 1380, 2200, "college", "Three colleges, a library, an observatory, an anatomy theatre "
         "and the Hall of Disputations.", zone=("rect", 1245, 2070, 1530, 2365))
    market(W, "Book Market", (1460, 2080, 1520, 2120), 16, "Copyists, maps, almanacs and forbidden books under the counter.")
    W.explicit_bridges.append(dict(name="West Bridge", road="West Bridge Street", x=1382.0, y=1842.0, heading=90.0,
                                   length=100.0, width=12.0, material="stone", arches=6))
    for k, off in enumerate((-22, 22)):
        W.building("R", "watermill", f"West Bridge Mill {k + 1}", 1395 + 12, 1842 + off, 10, 9, 90, 7, "gable",
                   material="timber", check=False, on_bridge="West Bridge")
        W.prop("waterwheel", 1395 + 19, 1842 + off, 0, r=3.5, w=1.5, on_bridge="West Bridge")
    W.landmark("West Bridge", 1382, 1842, "Six arches and two corn mills where the scholars cross into the Westgate.")


# ------------------------------------------------------------------ beyond the south wall
def _outside_south(W):
    b = W.building
    rng = W.rng
    # the great fair
    x0, y0, x1, y1 = 1600, 2700, 2050, 2950
    W.squares.append(dict(name=N["fair"], box=(x0, y0, x1, y1), kind="fair"))
    tents(W, N["fair"], x0 + 10, y0 + 10, x0 + 220, y1 - 10, 14, rng, big=True)
    for k in range(4):
        W.prop("pavilion", x0 + 260 + k * 40, y0 + 30, r=6, name=f"Merchants' pavilion {k + 1}")
    W.prop("maypole", x0 + 330, y0 + 120)
    for k, (sx, sy) in enumerate([(x0 + 260, y0 + 200), (x0 + 400, y0 + 210)]):
        b("X", "stage", f"Fair stage {k + 1}", sx, sy, 16, 10, 180, 3, "flat", material="timber", check=False)
    W.wall("Tiltyard barrier", "fence", [(x0 + 280, y0 + 120), (x0 + 420, y0 + 120)], 1.5, 0.4, material="wood")
    for s in (-1, 1):
        b("X", "stand", "Tiltyard stand", x0 + 350, y0 + 120 + s * 22, 120, 8, 0 if s > 0 else 180, 4, "flat",
          material="timber", check=False)
    for k in range(5):
        W.prop("target", x0 + 430, y0 + 160 + k * 16, 270, group="Fair archery")
    site(W, N["fair"], 1825, 2825, "fair", "A fair field the size of the Old Town: tents, pavilions, stages, a jousting "
         "tiltyard, archery, a maypole. Busiest in late August.", zone=("rect", x0, y0, x1, y1))
    # cemetery
    cx0, cy0, cx1, cy1 = 1150, 2600, 1400, 2780
    W.wall("Cemetery wall", "precinct", [(cx0, cy0), (cx1, cy0), (cx1, cy1), (cx0, cy1)], 2.2, 0.8, closed=True,
           gaps=[(1275, cy0)], gap_r=5)
    for gx in range(cx0 + 12, cx1 - 8, 10):
        for gy in range(cy0 + 30, cy1 - 8, 8):
            if rng.random() < 0.55:
                W.prop("gravestone", gx + rng.uniform(-1, 1), gy, 0, group="Gravestones")
    b("X", "chapel", "Cemetery chapel", 1275, 2615, 18, 9, 0, 9, "gable", material="stone", check=False)
    W.churchyards.append((cx0, cy0, cx1, cy1))
    for k in range(10):
        W.groves.append((cx0 + 10 + k * 25, cy1 - 6, "yew", 9))
    site(W, "Field of Rest", 1275, 2690, "cemetery", "The great cemetery beyond the walls.", zone=("rect", cx0, cy0, cx1, cy1))
    # abbey
    courtyard(W, "X", "Whitecross Abbey cloister", 2300, 2930, 70, 60, 0, h=10, floors=2, kind="cloister")
    b("X", "church", "Whitecross Abbey church", 2300, 2880, 110, 20, 0, 22, "gable", material="stone", check=False)
    W.tower("X", "Whitecross Abbey tower", 2330, 2880, 9, 40, roof="cone")
    site(W, "Whitecross Abbey", 2300, 2910, "abbey", "Benedictine abbey with its own farms, fishponds and bees.",
         zone=("rect", 2230, 2860, 2370, 2965))
    for k in range(20):
        W.prop("beehive", 2240 + (k % 10) * 6, 2980 + (k // 10) * 6)
    # leper house
    courtyard(W, "X", "Leper House of St. Lazarus", 2550, 2850, 40, 32, 0, h=6, floors=1, kind="hospital", depth=8)
    site(W, "Leper House of St. Lazarus", 2550, 2850, "hospital", "Kept far outside the walls, with its own chapel and garden.",
         zone=("rect", 2528, 2832, 2572, 2868))
    # hillfort
    for r0, r1, hh in ((100, 116, -5), (118, 136, 4.5), (145, 160, 2.5)):
        W.earthworks.append(dict(kind="ring", name="The Old Ring", cx=700, cy=2600, r0=r0, r1=r1, h=hh, gaps=[60, 240], gap_w=14))
    b("X", "chapel", "Hermit's chapel", 700, 2600, 10, 6, 60, 6, "gable", material="stone", check=False)
    stone_circle(W, "Old Ring stones", 700, 2600, 30, 7, h=(1.4, 2.2))
    pocket_label(W, "The Old Ring", 700, 2600, "An Iron Age hillfort: three rings of ramparts on the hill; a hermit now lives inside.")
    site(W, "Saltreed Marsh", 2780, 2580, "nature", "Reedbeds, herons and smugglers' paths.")
    site(W, "Salt Pans", 3040, 2640, "industry", "Sea water evaporates in shallow pans; salt is the city's white gold.")
    b("X", "saltworks", "Salt house", 3030, 2740, 26, 12, 0, 6, "gable", material="timber", check=False)
    # farmland & windmills
    for name, (fx, fy, fw, fh, ang) in [("South Fields", (1300, 3200, 380, 260, 5)), ("South Fields", (2250, 3250, 420, 280, -4)),
                                        ("Down Fields", (1300, 3650, 360, 300, 3)), ("Down Fields", (2350, 3700, 400, 260, -6)),
                                        ("Abbey Fields", (2650, 3050, 280, 220, 8)), ("West Fields", (900, 3050, 320, 260, -3))]:
        x = -fw / 2
        while x < fw / 2 - 5:
            sw = min(rng.choice([18, 22, 26]), fw / 2 - x)
            a = math.radians(ang)
            px, py = fx + (x + sw / 2) * math.cos(a), fy + (x + sw / 2) * math.sin(a)
            W.fields.append(dict(name=f"{name} strip", field=name, crop=rng.choice(["wheat", "barley", "oats", "fallow", "beans"]),
                                 poly=[tuple(round(v, 2) for v in c) for c in rect_corners(px, py, sw, fh, ang)]))
            x += sw
        W.fields.append(dict(name=name, field=name, crop="outline",
                             poly=[tuple(round(v, 2) for v in c) for c in rect_corners(fx, fy, fw, fh, ang)]))
    for k, (wx, wy) in enumerate([(1650, 3480), (1800, 3450), (1950, 3520), (2100, 3470)]):
        b("X", "windmill", f"Down windmill {k + 1}", wx, wy, 7, 7, 180, 10, "gable", material="timber", sails=12, check=False)
    site(W, "South Down windmills", 1880, 3480, "industry", "Four post-mills grinding the southern harvest.")
    for k, (hx, hy) in enumerate([(1000, 3350), (2000, 3900), (2700, 3450)]):
        for j in range(6):
            first, trade = W.person(TRADES)
            b("X", "farmhouse", f"Farm of {first}", hx + (j % 3) * 40, hy + (j // 3) * 45, 16, 8, rng.choice([0, 90]), 4,
              "gable", material="timber", thatch=True, check=False)
        site(W, ["Netherby", "Oakhurst", "Saltby"][k], hx + 40, hy + 20, "hamlet", "Farming hamlet.", landmark=False)


def _north_and_west(W):
    b = W.building
    rng = W.rng
    market(W, "Haymarket", (1240, 960, 1320, 1010), 20, "Carters bring hay, straw and firewood down from the hills.")
    W.waters.append(dict(id="WATER-HW", name="Brigid's Well", kind="pond", cx=1180, cy=860, rx=6, ry=6,
                         line=np.array(ellipse_pts(1180, 860, 6, 6, 16))))
    W.prop("standing_stone", 1190, 850, 30, h=3.4, w=1.6, d=1.0, name="Brigid's Stone")
    b("N", "chapel", "Chapel of the Holy Well", 1160, 835, 16, 8, 0, 8, "gable", material="stone", check=False)
    pocket_label(W, "Brigid's Well & Stone", 1180, 855, "A holy spring guarded by an ancient standing stone; pilgrims tie ribbons to it.")
    courtyard(W, "N", "Pilgrims' Hospice", 1440, 820, 44, 36, 0, h=8, floors=2, kind="hospice")
    site(W, "Pilgrims' Hospice", 1440, 820, "hospice", "Free beds and soup for pilgrims arriving from the north.",
         zone=("rect", 1416, 800, 1464, 840))
    courtyard(W, "X", "Mere Abbey", 760, 1100, 70, 60, 10, h=10, floors=2, kind="cloister")
    b("X", "church", "Mere Abbey church", 760, 1050, 90, 18, 10, 20, "gable", material="stone", check=False)
    site(W, "Mere Abbey", 760, 1080, "abbey", "Cistercian abbey on the shore of the Mirror Mere.", zone=("rect", 700, 1030, 820, 1135))
    for k in range(3):
        W.prop("boat", 600 + k * 30, 1080, 20)
    b("X", "lodge", "Royal Hunting Lodge", 820, 240, 26, 12, 180, 9, "hip", material="timber", floors=2, check=False)
    site(W, "Royal Hunting Lodge", 820, 240, "lodge", "The King's lodge deep in the Royal Forest.", zone=("circle", 820, 240, 40))
    for k, (wx, wy) in enumerate([(1000, 470), (1550, 450), (2050, 520)]):
        b("X", "windmill", f"Hill windmill {k + 1}", wx, wy, 7, 7, 180, 10, "gable", material="timber", sails=12, check=False)
    W.road("Mill Hill Track", "track", [(1340, 620), (1550, 450), (2050, 520), (2300, 430)], 4)
    for k in range(3):
        b("X", "charcoal", "Charcoal burners' hut", 400 + k * 30, 600 + k * 20, 5, 4, 0, 2.5, "gable", material="wattle", check=False)
        W.prop("charcoal_clamp", 420 + k * 30, 620 + k * 20, r=4)
    x0, y0, x1, y1 = W.vineyards[0]
    for k in range(int((x1 - x0) / 60)):
        px = x0 + k * 60
        W.fields.append(dict(name="Vineyard", field="Crownback Vineyards", crop="vines",
                             poly=[(px, y0), (px + 54, y0), (px + 54, y1), (px, y1)]))
    b("X", "winery", "Wine press house", 2300, 970, 24, 12, 0, 7, "gable", material="stone", check=False)
    site(W, "Crownback Vineyards", 2320, 880, "farm", "South-facing terraces of vines above the palace.")
    market(W, "Horse Fair", (900, 1640, 980, 1720), 0, "Horse dealers' field outside the West Gate.", kind="fair")
    for k in range(4):
        W.prop("pen", 915 + (k % 2) * 36, 1660 + (k // 2) * 36, 0, w=30, d=30, group="Horse pens")


def _coast_east(W):
    b = W.building
    rng = W.rng
    _zone_now(W)
    placed = 0
    for _ in range(400):
        if placed >= 22:
            break
        x, y = rng.uniform(2930, 3110), rng.uniform(1040, 1320)
        ix, iy = _px([x, x + 25], [y, y])
        if W.zone[iy[0], ix[0]] or not W.zone[iy[1], ix[1]]:          # on land, within 25 m of the shore
            continue
        hd = rng.uniform(0, 360)
        c = rect_corners(x, y, 10, 8, hd)
        if W.blocked(c):
            continue
        first, trade = W.person(["fisher", "net-mender", "salter", "boatwright"])
        b("E", "hut", f"Stilt hut of {first} the {trade}", x, y, 8, 6, hd, 3.2, "gable",
          material="wattle", thatch=True, check=False, stilts=True)
        placed += 1
    for k in range(10):
        W.prop("drying_rack", 2980 + k * 8, 1300, 0, group="Fish drying racks")
    for k in range(6):
        W.prop("boat", 3110 + k * 6, 1120 + k * 18, 70 + k * 10)
    site(W, "Eastfold", 3020, 1170, "village", "Fishing village on Gull Bay: huts on stilts, drying racks and boats on the shingle.")
    W.tower("E", "Raven Light", 3760, 725, 7, 32, roof="crenel")
    W.prop("beacon", 3760, 725, lift=32)
    b("E", "house", "Lightkeeper's house", 3725, 740, 12, 8, 90, 5, "gable", material="stone", check=False)
    site(W, "Raven Light", 3760, 725, "lighthouse", "Lighthouse on the cliffs of Raven Head.")
    stone_circle(W, "The Sea Stones", 3600, 700, 9, 7, h=(1.2, 2.0))
    W.prop("altar_stone", 3660, 650, name="Cup-and-ring Rock", w=4, d=3, h=0.8)
    pocket_label(W, "The Sea Stones", 3600, 700, "A tiny stone ring and a rock carved with cups and rings, on the windiest cliff in the realm.")
    W.tower("X", "Gull Rock Sea Fort", 3720, 2300, 16, 22, roof="crenel")
    W.wall("Sea fort wall", "curtain", ellipse_pts(3720, 2300, 40, 34, 12), 8, 3, closed=True)
    W.islands = [ellipse_pts(3720, 2300, 120, 90, 30, 0.12, seed=21)]
    site(W, "Gull Rock Sea Fort", 3720, 2300, "military", "Round fort on an island guarding the river mouth; reached only by boat.")
    W.tower("L", "Lantern Point Light", 3490, 3170, 7, 28, roof="crenel")
    W.prop("beacon", 3490, 3170, lift=28)
    site(W, "Lantern Point", 3300, 3110, "village", "Smugglers' village and lighthouse on the southern headland.")


# ------------------------------------------------------------------ organic streets
def _grow_streets(W):
    """Grow lanes out of the main roads like a real town: wandering, branching, joining."""
    _zone_now(W)
    rng = random.Random(SEED + 9)
    occ = Image.new("L", (RN, RN), 0)
    od = ImageDraw.Draw(occ)
    pts_idx = {}

    def index_line(line, rid):
        for k, (x, y) in enumerate(line[::3]):
            pts_idx.setdefault((int(x // 24), int(y // 24)), []).append((x, y))

    def draw_line(line, width, clearance):
        od.line([(x * RS, y * RS) for x, y in line], fill=255, width=max(2, int((width + 2 * clearance) * RS)))

    for r in W.roads:
        if r["kind"] in ("road", "street", "lane", "pier"):
            dp = district_at(*r["line"][len(r["line"]) // 2])
            draw_line(r["line"], r["width"], dp[6] * 0.9)
            index_line(r["line"], r["id"])
    occ_arr = np.asarray(occ) > 0
    queue = []
    for r in list(W.roads):
        if r["kind"] not in ("road", "street", "lane"):
            continue
        line = r["line"]
        total = float(np.hypot(*np.diff(line, axis=0).T).sum())
        s = rng.uniform(10, 40)
        while s < total - 10:
            x, y, ang, _ = along(line, 1, start=s, end=s + 0.5)[0]
            dp = district_at(x, y)
            s += dp[4] * rng.uniform(0.7, 1.4)
            for side in (-1, 1):
                queue.append((x, y, ang + side * math.pi / 2, 0))
    rng.shuffle(queue)
    made = 0
    street_names = iter(STREET_NAMES)
    while queue and made < 4000:
        x, y, ang, depth = queue.pop()
        dp = district_at(x, y)
        if depth > 6:
            continue
        ix, iy = _px(x, y)
        if not W.built[iy, ix]:
            continue
        clearance = dp[6] * 0.9
        line = [(x, y)]
        left = False
        stop_join = None
        maxlen = dp[5] * rng.uniform(0.5, 1.2)
        L = 0.0
        a = ang + rng.gauss(0, 0.12)
        while L < maxlen:
            a += rng.gauss(0, 0.16)
            nx, ny = line[-1][0] + 9 * math.cos(a), line[-1][1] + 9 * math.sin(a)
            jx, jy = _px(nx, ny)
            if W.zone[jy, jx] or not W.built[jy, jx]:
                break
            occupied = occ_arr[jy, jx]
            if not left:
                if not occupied:
                    left = True
                elif L > 40:
                    break
            elif occupied:
                best, bd = None, 1e9
                for gx in range(int(nx // 24) - 2, int(nx // 24) + 3):
                    for gy in range(int(ny // 24) - 2, int(ny // 24) + 3):
                        for px_, py_ in pts_idx.get((gx, gy), ()):
                            dd = (px_ - nx) ** 2 + (py_ - ny) ** 2
                            if dd < bd:
                                best, bd = (px_, py_), dd
                if best is not None and bd < (clearance + 20) ** 2:
                    stop_join = best
                line.append((nx, ny))
                break
            line.append((nx, ny))
            L += 9
        if stop_join:
            line.append(stop_join)
        if L < 30 or not left:
            continue
        width = rng.choice([4, 5, 5, 6, 7]) if dp[1] != "O" else rng.choice([3.5, 4, 5])
        ln = resample(line, 3.0)
        name = next(street_names, f"Lane {made}")
        W.roads.append(dict(id=f"ROAD-{len(W.roads) + 1:04d}", name=name, kind="street", width=width,
                            surface="cobble" if dp[1] not in ("X", "N", "E", "L") else "dirt",
                            ctrl=[tuple(ln[0]), tuple(ln[-1])], line=ln))
        draw_line(ln, width, clearance)
        index_line(ln, made)
        occ_arr = np.asarray(occ) > 0
        made += 1
        tot = float(np.hypot(*np.diff(ln, axis=0).T).sum())
        s = rng.uniform(15, 30)
        while s < tot - 15:
            px_, py_, aa, _ = along(ln, 1, start=s, end=s + 0.5)[0]
            if rng.random() < 0.92:
                queue.insert(rng.randrange(len(queue) + 1), (px_, py_, aa + rng.choice([-1, 1]) * math.pi / 2, depth + 1))
            s += dp[4] * rng.uniform(0.8, 1.5)
    W.grown_streets = made
    _street_mask(W)


def _street_mask(W):
    img = Image.new("L", (RN, RN), 0)
    d = ImageDraw.Draw(img)
    for r in W.roads:
        if r["kind"] in ("path",):
            continue
        pts = [(x * RS, y * RS) for x, y in r["line"]]
        d.line(pts, fill=255, width=max(2, int(round((r["width"] + 1.5) * RS))), joint="curve")
    for s in W.squares:
        x0, y0, x1, y1 = s["box"]
        d.rectangle([x0 * RS, y0 * RS, x1 * RS, y1 * RS], fill=255)
    W.street_mask = np.asarray(img) > 0


STREET_NAMES = [
    "Threadneedle Row", "Candle Lane", "Bell Street", "Saddlers' Row", "Wool Street", "Pudding Lane", "Gold Street",
    "The Shambles", "Coopers' Row", "Silver Street", "Ink Lane", "Tanners' Walk", "Hatters' Lane", "Pie Corner",
    "Lantern Street", "Weavers' Row", "Glovers' Lane", "Spice Street", "Rope Walk Lane", "Chandlers' Row",
    "Parchment Lane", "Pilgrims' Way", "Ironmonger Lane", "Fullers' Row", "Dyers' Street", "Mint Street", "Cheapside",
    "Milk Street", "Wood Street", "Bread Street", "Honey Lane", "Friday Street", "Old Change", "Cornhill", "Poultry",
    "Garlick Hill", "Stone Street", "Menhir Lane", "Barrow Row", "Moot Lane", "Serpent Lane", "Raven Row",
    "Crown Street", "Bishop's Lane", "Abbot's Walk", "Scholars' Row", "Lamb Street", "Hart Street", "Swan Lane",
    "Fish Street", "Mill Row", "Water Lane", "Quay Street", "Ship Lane", "Anchor Row", "Salt Street", "Corn Street",
    "Hay Lane", "Cattle Row", "Horse Street", "Forge Lane", "Bellfounders' Row", "Clock Lane", "Lute Lane",
    "Painters' Row", "Glass Street", "Pewter Lane", "Jewel Street", "Kettle Row", "Oven Lane", "Brewers' Row",
    "Malt Street", "Vine Street", "Cellar Lane", "Hood Street", "Mantle Row", "Thimble Lane", "Needle Street",
    "Button Row", "Lace Lane", "Feather Street", "Quill Lane", "Lamp Row", "Wick Street", "Barrel Lane", "Hoop Row",
    "Crooked Lane", "Zigzag Steps", "Dog Leg Alley", "Seven Turns", "Cut-Throat Alley", "Sixpenny Steps",
    "Rat's Run", "Pigeon Lane", "Gutter Lane", "Hanging Sword Alley", "Fool's Corner", "Blind Man's Way",
    "Tumbledown Row", "Snake Street", "Corkscrew Lane", "Long Tangle", "Short Tangle", "Weasel Way", "Old Jewry",
    "Lombard Street", "Hanse Row", "Gull Street", "Tar Lane", "Net Row", "Oar Street", "Herring Lane",
] + [f"Nameless Lane {i}" for i in range(1, 1500)]


def _plazas(W):
    """Little squares where lanes meet: wells, fountains, crosses, statues, a tree."""
    rng = random.Random(SEED + 11)
    ends = [r["line"][-1] for r in W.roads if r["kind"] == "street"]
    placed = []
    for x, y in ends:
        if rng.random() > 0.22:
            continue
        if any(math.hypot(x - a, y - b) < 160 for a, b in placed):
            continue
        r = rng.uniform(12, 20)
        if not _free(W, [x - r, x + r, x, x], [y, y, y - r, y + r], street_ok=True).all():
            continue
        placed.append((x, y))
        W.squares.append(dict(name="Little square", box=(x - r, y - r, x + r, y + r), kind="square"))
        kind = rng.choice(["well", "fountain", "market_cross", "statue", "tree", "well", "pillory"])
        if kind == "tree":
            W.groves.append((x, y, "lime", 14))
        elif kind == "fountain":
            W.prop("fountain", x, y, r=4)
        elif kind == "statue":
            W.prop("statue", x, y, rng.uniform(0, 360), h=5, group="Statues")
        elif kind == "pillory":
            W.prop("stocks", x, y)
        else:
            W.prop(kind, x, y, group="Wells & crosses")
    _street_mask(W)


PARISHES = ["St. Agatha", "St. Bede", "St. Columba", "St. Dunstan", "St. Edith", "St. Fiacre", "St. Giles",
            "St. Hugh", "St. Ivo", "St. Jude", "St. Kenelm", "St. Lucy", "St. Martin", "St. Nicholas", "St. Olaf",
            "St. Petroc", "St. Quentin", "St. Rumbold", "St. Swithin", "St. Thomas"]


def _find_spot(W, x, y, w, d, radius=160):
    for r in range(0, radius, 8):
        for a in range(0, 360, 30 if r else 360):
            px, py = x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))
            for hd in (0, 90, 30, 120):
                c = rect_corners(px, py, w + 8, d + 8, hd)
                if not _free(W, [p[0] for p in c] + [px], [p[1] for p in c] + [py]).all() or W.blocked(c):
                    continue
                return px, py, hd
    return None


def _place_near(W, x, y, w, d, kind, name, district, h, roof, radius=160, **kw):
    spot = _find_spot(W, x, y, w, d, radius)
    if spot is None:
        return None
    px, py, hd = spot
    b = W.building(district, kind, name, px, py, w, d, hd, h, roof, check=False, **kw)
    _block(W, ("poly", rect_corners(px, py, w + 4, d + 4, hd)))
    _zone_now(W)
    return b


def _churches(W):
    rng = random.Random(SEED + 13)
    spots = [(1600, 1550), (2100, 1650), (1950, 1450), (2500, 1550), (2750, 1850), (1400, 1680), (1250, 1850),
             (1550, 2100), (1700, 2250), (2050, 2400), (1450, 2480), (2200, 2050), (2600, 2200), (1350, 1050),
             (2900, 1250), (1950, 2560), (2350, 1450), (1150, 2200), (3200, 3080), (1700, 1680)]
    k = 0
    for x, y in spots:
        name = f"Church of {PARISHES[k % len(PARISHES)]}"
        dp = district_at(x, y)
        ch = _place_near(W, x, y, rng.choice([24, 30, 36]), 11, "church", name, dp[1], 13, "gable", material="stone", floors=1)
        if ch is None:
            continue
        a2 = math.radians(ch["heading"])
        W.building(dp[1], "church", f"{name} (tower)", ch["x"] - (ch["w"] / 2 + 4) * math.cos(a2),
                   ch["y"] - (ch["w"] / 2 + 4) * math.sin(a2), 8, 8, ch["heading"], rng.choice([22, 26, 30]),
                   rng.choice(["spire", "crenel"]), roof_h=14, material="stone", check=False, group=name, floors=4)
        k += 1
    W.parish_count = k
    extras = [("Nunnery of St. Clare", "N", 1950, 1660, 40, 30), ("Greyfriars", "W", 1450, 1920, 46, 36),
              ("Blackfriars", "M", 2560, 1780, 46, 36), ("Hospital of St. Brigid", "S", 1640, 2160, 50, 36),
              ("Almshouses of the Twelve", "D", 1950, 2400, 44, 26), ("Jail & Court of Pie Powder", "O", 1720, 1500, 30, 24),
              ("Hall of the Mercers", "M", 2240, 1630, 26, 16), ("Hall of the Goldsmiths", "O", 1900, 1650, 24, 15),
              ("Hall of the Vintners", "M", 2450, 1720, 24, 15), ("Hall of the Fishmongers", "H", 2620, 1930, 26, 16),
              ("Hall of the Weavers", "S", 2100, 2160, 26, 16), ("Hall of the Masons", "D", 1700, 2500, 24, 15),
              ("Tavern of the Drowned Rat", "H", 2850, 1960, 18, 12), ("The Crooked Cup", "S", 1880, 2080, 16, 12),
              ("The Golden Goose", "D", 1550, 2520, 18, 12), ("The Mermaid", "H", 2750, 1900, 18, 12),
              ("The Sleeping Bishop", "I", 1780, 1965, 14, 10), ("Debtors' Prison", "S", 2200, 2200, 30, 22),
              ("Alchemist's Tower", "W", 1180, 1950, 10, 10), ("Clockmakers' Hall", "O", 2100, 1600, 22, 14)]
    for nm, dist, x, y, w, d in extras:
        if "Tower" in nm:
            W.tower(dist, nm, x, y, 6, 30, roof="cone")
            site(W, nm, x, y, "tower", "Smoke of strange colours pours from its windows at night.")
            continue
        if w >= 40:
            spot = _find_spot(W, x, y, w, d)
            if spot is None:
                continue
            px, py, hd = spot
            courtyard(W, dist, nm, px, py, w, d, hd, h=9, floors=2, kind="institution", depth=9)
            W.reserve(rect_corners(px, py, w + 2, d + 2, hd))
            _block(W, ("poly", rect_corners(px, py, w + 4, d + 4, hd)))
            site(W, nm, px, py, "institution", "One of the city's great religious or charitable houses.")
        else:
            kind = "hall" if "Hall" in nm else ("inn" if nm.startswith(("Tavern", "The")) else "institution")
            bb = _place_near(W, x, y, w, d, kind, nm, dist, 11 if kind == "hall" else 9, "hip",
                             material="timber" if kind == "inn" else "stone", floors=2)
            if bb:
                desc = {"hall": "Guild hall of one of the city's trades.", "inn": "Ale, gossip and trouble.",
                        "institution": "Locks, chains and a magistrate who can be bribed."}[kind]
                site(W, nm, bb["x"], bb["y"], kind, desc)


# ------------------------------------------------------------------ houses
def _houses(W):
    rng = random.Random(SEED + 17)
    _zone_now(W)
    count = 0
    for st in sorted(W.roads, key=lambda r: -r["width"]):
        if st["kind"] not in ("street", "road", "lane") or len(st["line"]) < 6:
            continue
        line = st["line"]
        total = float(np.hypot(*np.diff(line, axis=0).T).sum())
        for side in (1, -1):
            s = 3.0
            while s < total - 3:
                x0, y0, _, _ = along(line, 1, start=s, end=s + 0.5)[0]
                dp = district_at(x0, y0)
                lo, hi = (5.5, 9.5) if dp[1] in ("O", "M", "S", "H") else (8, 14)
                fw = rng.uniform(lo, hi)
                if s + fw / 2 >= total:
                    break
                x, y, ang, _ = along(line, 1, start=s + fw / 2, end=s + fw / 2 + 0.5)[0]
                gap = 0.4 if dp[7] > 0.8 else rng.uniform(2, 10)
                s += fw + gap
                if rng.random() > dp[7]:
                    continue
                dd = rng.uniform(9, 15) if dp[1] not in ("X", "N", "E", "L") else rng.uniform(7, 10)
                nx, ny = -math.sin(ang), math.cos(ang)
                off = st["width"] / 2 + 0.6 + dd / 2 + (0 if dp[7] > 0.8 else rng.uniform(0, 4))
                hx, hy = x + side * off * nx, y + side * off * ny
                hd = heading_facing(ang, side)
                c = rect_corners(hx, hy, fw, dd, hd)
                ci = rect_corners(hx, hy, fw - 2.6, dd - 2.6, hd)        # inset: the raster street edge is coarse
                if not _free(W, [p[0] for p in ci] + [hx], [p[1] for p in ci] + [hy]).all() or W.blocked(c):
                    continue
                floors = rng.randint(*dp[8])
                first, trade = W.person(TRADES)
                style = dp[9]
                stone = style == "stone" or (style == "mixed" and rng.random() < 0.3)
                kind = rng.choice(["house", "shop", "shop"]) if dp[1] in ("O", "M", "H", "S") else "house"
                rural = dp[1] in ("X", "N", "E", "L")
                W.building(dp[1], kind, f"{'Cottage' if rural else 'House'} of {first} the {trade}", hx, hy, fw, dd, hd,
                           3.1 * floors + (0.3 if rural else 0), rng.choice(["gable", "gable", "hip"]),
                           material="stone" if stone else ("wattle" if rural and rng.random() < 0.5 else "timber"),
                           floors=floors, trade=trade, resident=first, pad=0.15, check=False, thatch=rural)
                W.reserve(c)
                count += 1
                if dp[1] in ("O", "M") and rng.random() < 0.45:
                    bw, bd = rng.uniform(4.5, fw), rng.uniform(4.5, 7)
                    boff = off + dd / 2 + rng.uniform(1.0, 3.0) + bd / 2
                    bx, by = x + side * boff * nx, y + side * boff * ny
                    cc = rect_corners(bx, by, bw, bd, hd)
                    ci = rect_corners(bx, by, bw - 2, bd - 2, hd)
                    if _free(W, [p[0] for p in ci] + [bx], [p[1] for p in ci] + [by]).all() and not W.blocked(cc):
                        W.building(dp[1], "workshop", f"Workshop of {first} the {trade}", bx, by, bw, bd, hd, 3.2,
                                   "gable", material="timber", floors=1, check=False)
                        W.reserve(cc)
    W.house_count = count


def _maze(n, rng):
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
    walls.discard((0, n // 2, 0, n // 2 + 1))
    return sorted(walls)


# ------------------------------------------------------------------ nature
def _vegetation(W):
    W.forests += [
        dict(name=N["forest_n"], kind="royal forest", spacing=13,
             poly=[(-10, -10), (3300, -10), (3240, 240), (2900, 300), (2400, 330), (2050, 380), (1800, 420),
                   (1500, 560), (1200, 520), (900, 640), (600, 700), (300, 760), (-10, 740)]),
        dict(name=N["forest_w"], kind="mixed", spacing=13,
             poly=[(-10, 1150), (250, 1180), (420, 1400), (380, 1800), (450, 2050), (300, 2300), (-10, 2400)]),
        dict(name="Southwood", kind="mixed", spacing=13,
             poly=[(-10, 2700), (450, 2800), (600, 3100), (500, 3500), (-10, 3700)]),
        dict(name="Thornwood", kind="mixed", spacing=13,
             poly=[(2800, 3350), (3150, 3350), (3250, 3700), (3200, 4100), (2700, 4100), (2600, 3800)]),
        dict(name="Raven Wood", kind="coastal pines", spacing=12,
             poly=[(3330, 480), (3550, 560), (3500, 820), (3350, 880), (3260, 700)]),
    ]
    W.orchards.append(dict(name="Abbey orchard", poly=[(2380, 2870), (2470, 2870), (2470, 2950), (2380, 2950)], spacing=9))
    W.orchards.append(dict(name="Mere Abbey orchard", poly=[(830, 1060), (900, 1060), (900, 1130), (830, 1130)], spacing=9))


def _labels(W):
    L = W.labels
    L += [
        dict(t=N["castle"].upper(), x=1650, y=900, size=34, kind="place", sub="the royal castle on its crag"),
        dict(t="OLD TOWN", x=1880, y=1440, size=24, kind="place"),
        dict(t=N["island"].upper(), x=1860, y=1860, size=18, kind="place"),
        dict(t="PALACE QUARTER", x=2290, y=1020, size=20, kind="place"),
        dict(t="MERCHANT QUARTER", x=2400, y=1540, size=20, kind="place"),
        dict(t="THE HARBOUR", x=2830, y=1830, size=22, kind="place"),
        dict(t="SOUTHBANK", x=1950, y=2050, size=22, kind="place"),
        dict(t="SCHOLARS' HILL", x=1380, y=2040, size=20, kind="place"),
        dict(t="WESTGATE", x=1250, y=1360, size=18, kind="place"),
        dict(t="SOUTH WARD", x=1700, y=2580, size=18, kind="place"),
        dict(t="TANNERS' REACH", x=2520, y=2120, size=16, kind="place"),
        dict(t="SHIPWRIGHTS", x=2800, y=2200, size=16, kind="place"),
        dict(t="NORTHGATE", x=1330, y=700, size=18, kind="place"),
        dict(t="EASTFOLD", x=2960, y=1000, size=18, kind="place"),
        dict(t=N["forest_n"].upper(), x=1700, y=120, size=30, kind="region"),
        dict(t=N["hills"].upper(), x=900, y=420, size=22, kind="region"),
        dict(t=N["forest_w"].upper(), x=180, y=1750, size=24, kind="region"),
        dict(t=N["sea"].upper(), x=3800, y=1600, size=44, kind="water"),
        dict(t="GULL BAY", x=3330, y=1200, size=18, kind="water"),
        dict(t=N["headland"].upper(), x=3600, y=900, size=18, kind="region"),
        dict(t=N["river"].upper(), x=500, y=1580, size=24, kind="water", rot=-6),
        dict(t=N["river"].upper(), x=2500, y=2110, size=20, kind="water", rot=22),
        dict(t=N["lake"].upper(), x=520, y=955, size=18, kind="water"),
        dict(t="SALTREED MARSH", x=2780, y=2640, size=14, kind="field"),
        dict(t="SOUTH FIELDS", x=1800, y=3250, size=18, kind="field"),
    ]
