"""The world model: every road, river, wall, building, field and landmark.

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
        return f"{district}-{self._ids[district]:03d}"

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
                if kind not in ("house", "shop", "longhouse", "barn", "farmhouse"):
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


# =============================================================== the layout
CASTLE = (1024.0, 600.0)
TOWN = (1024.0, 1080.0)
TOWN_R = (240.0, 175.0)
PLATEAU_R = 135.0
PLATEAU_Z = 125.0


def build_layout():
    W = World()
    _landforms(W)
    _water(W)
    _roads(W)
    _castle(W)
    _town(W)
    _abbey(W)
    _villages(W)
    _outlying(W)
    _fields(W)
    _vegetation_regions(W)
    _labels(W)
    return W


def _landforms(W):
    # ridgelines: (control points, extra height m, half-width m)
    W.ridges = [
        dict(pts=spline([(-50, 260), (250, 190), (600, 110), (1000, 70), (1400, 110), (1800, 190), (2100, 250)], step=8),
             h=75, w=230),
        dict(pts=spline([(-40, 380), (120, 520), (230, 700), (250, 860)], step=8), h=55, w=150),
        dict(pts=spline([(2100, 380), (1960, 560), (1990, 780)], step=8), h=55, w=150),
    ]
    W.peaks = [  # name, x, y, extra height, radius x, radius y
        dict(name=N["peak_nw"], x=520, y=330, h=62, rx=200, ry=170),
        dict(name=N["peak_n"], x=1000, y=160, h=62, rx=260, ry=170),
        dict(name=N["peak_ne"], x=1500, y=300, h=66, rx=200, ry=170),
        dict(name=N["peak_w"], x=260, y=720, h=78, rx=170, ry=150),
        dict(name=N["spur_w"], x=690, y=600, h=42, rx=150, ry=120),
        dict(name=N["spur_e"], x=1380, y=640, h=48, rx=150, ry=130),
        dict(name="Mill Knoll", x=700, y=1340, h=7, rx=60, ry=60),
        dict(name="Southfold Rise", x=1000, y=1800, h=12, rx=320, ry=260),
    ]
    W.pits = [dict(name="Quarry", x=1300, y=700, rx=42, ry=28, depth=9)]


def _water(W):
    river = spline([(1800, -20), (1720, 250), (1640, 520), (1580, 800), (1500, 1040), (1380, 1260),
                    (1180, 1380), (950, 1420), (700, 1480), (420, 1600), (200, 1760), (-30, 1860)], step=4)
    W.waters.append(dict(id="WATER-01", name=N["river"], kind="river", width=27, line=river))
    brook = spline([(300, 700), (340, 860), (400, 980), (430, 1050), (500, 1110), (570, 1180), (585, 1300),
                    (610, 1420), (690, 1478)], step=4)
    W.waters.append(dict(id="WATER-02", name=N["brook"], kind="stream", width=6, line=brook))
    W.waters.append(dict(id="WATER-03", name=N["mere"], kind="lake", cx=1860, cy=1190, rx=120, ry=85,
                         line=np.array(ellipse_pts(1860, 1190, 120, 85, 64, 0.06, seed=5))))
    W.waters.append(dict(id="WATER-04", name="Castle Moat", kind="moat", cx=CASTLE[0], cy=CASTLE[1] - 6,
                         rx=115, ry=108, width=18, line=np.array(ellipse_pts(CASTLE[0], CASTLE[1] - 6, 115, 108, 72))))


def _roads(W):
    tw = TOWN
    gN, gS = (tw[0], tw[1] - TOWN_R[1]), (tw[0], tw[1] + TOWN_R[1])
    gW, gE = (tw[0] - TOWN_R[0], tw[1]), (tw[0] + TOWN_R[0], tw[1])
    W.gates = dict(N=gN, S=gS, W=gW, E=gE)
    W.road("King's Road (west)", "road", [(-10, 1060), (150, 1068), (300, 1055), (430, 1048), (560, 1060),
                                          (700, 1074), gW], 6)
    W.road("King's Road (east)", "road", [gE, (1380, 1070), (1480, 1040), (1560, 1015), (1660, 1030),
                                          (1740, 1040), (1860, 1050), (2060, 1080)], 6)
    W.road("South Road", "road", [gS, (1020, 1330), (1005, 1400), (1000, 1480), (1000, 1560), (992, 1650),
                                  (1000, 1760), (1010, 1880), (1000, 2060)], 6)
    W.road("Castle Way", "road", [(1024, 738), (985, 762), (962, 795), (1000, 826), (1065, 840), (1088, 866),
                                  (1055, 888), gN], 5, "cobble")
    W.road("Abbey Road", "lane", [(712, 1076), (660, 1000), (600, 930), (562, 898)], 4)
    W.road("Pilgrim Way", "track", [(462, 820), (420, 700), (400, 560), (300, 470), (150, 440), (-10, 430)], 3)
    W.road("Tiltyard Lane", "lane", [(1065, 840), (1180, 858), (1240, 878)], 4)
    W.road("Mill Lane", "lane", [(1300, 1074), (1318, 1170), (1305, 1262)], 4)
    W.road("Windmill Track", "track", [(752, 1078), (772, 1200), (712, 1322)], 3)
    W.road("Ford Track", "track", [(390, 1050), (300, 1110), (285, 1250), (292, 1350), (420, 1352), (540, 1362),
                                   (640, 1420), (700, 1480), (800, 1550), (900, 1590), (996, 1600)], 3)
    W.road("Lodge Track", "track", [(1800, 1043), (1832, 900), (1880, 700), (1910, 430)], 3)
    W.road("East Field Track", "track", [(1700, 1036), (1690, 1200), (1690, 1350), (1705, 1590), (1712, 1850),
                                         (1720, 2060)], 3)
    W.road("South Field Track", "track", [(1000, 1562), (1200, 1556), (1400, 1568), (1705, 1590)], 3)
    # footpaths up to the watch posts
    W.road("Ridge Path", "path", [(1024, 513), (1005, 430), (1000, 300), (1000, 172)], 2)
    W.road("Raven Path", "path", [(1005, 430), (860, 390), (700, 352), (535, 336)], 2)
    W.road("Beacon Path", "path", [(1005, 430), (1150, 385), (1350, 330), (1488, 306)], 2)
    W.road("Tor Path", "path", [(405, 600), (330, 660), (272, 712)], 2)
    W.road("Maidens' Path", "path", [(860, 390), (800, 312)], 2)


def _castle(W):
    cx, cy = CASTLE
    L = lambda x, y: (cx + x, cy + y)
    outer = [L(*p) for p in [(-70, -50), (-35, -82), (35, -82), (70, -50), (80, 25), (45, 70), (-45, 70), (-80, 25)]]
    W.wall("Outer curtain wall", "curtain", outer, 11, 3, closed=True, gaps=[L(0, 70), L(0, -82)], gap_r=7)
    names = ["Well Tower", "North-West Tower", "North-East Tower", "Bell Tower", "East Tower", "South-East Tower",
             "South-West Tower", "West Tower"]
    for (x, y), nm in zip(outer, names):
        W.tower("C", nm, x, y, 6.5, 16)
    inner = [L(-40, -76), L(40, -76), L(40, -8), L(-40, -8)]
    W.wall("Inner ward wall", "inner", inner, 13, 3, closed=True, gaps=[L(0, -8)], gap_r=4)
    for (x, y), nm in zip(inner, ["Lady Tower", "Kestrel Tower", "Treasury Tower", "Chapel Tower"]):
        W.tower("C", nm, x, y, 5, 18)
    b = W.building
    b("C", "keep", "Great Tower (the Keep)", *L(0, -46), 22, 22, 180, 28, "crenel", material="stone", floors=4, check=False)
    for dx, dy in [(-11, -11), (11, -11), (-11, 11), (11, 11)]:
        W.tower("C", "Keep turret", *L(dx, -46 + dy), 2.6, 32, group="Great Tower (the Keep)")
    b("C", "hall", "Great Hall", *L(22, -24), 26, 11, 180, 9, "gable", material="stone", floors=1)
    b("C", "chapel", "Castle Chapel", *L(-25, -24), 16, 8, 180, 7, "gable", material="stone")
    b("C", "kitchen", "Castle Kitchens", *L(-27, -62), 14, 10, 90, 6, "gable", material="stone")
    b("C", "gatehouse", "Inner Gate", *L(0, -8), 10, 8, 180, 12, "crenel", material="stone", check=False,
      passage_w=4, passage_h=5)
    b("C", "gatehouse", "Great Gatehouse", *L(0, 70), 18, 14, 180, 15, "crenel", material="stone", check=False,
      passage_w=4.5, passage_h=5.5)
    W.tower("C", "Gate drum (west)", *L(-10, 74), 5.5, 17, group="Great Gatehouse")
    W.tower("C", "Gate drum (east)", *L(10, 74), 5.5, 17, group="Great Gatehouse")
    b("C", "gatehouse", "Postern Gate", *L(0, -82), 7, 6, 0, 10, "crenel", material="stone", check=False,
      passage_w=2, passage_h=3)
    b("C", "stables", "Stables", *L(-62, 6), 32, 9, 90, 5, "gable", material="timber")
    b("C", "barracks", "Barracks", *L(62, 6), 32, 9, 270, 6, "gable", material="stone", floors=2)
    b("C", "smithy", "Castle Smithy", *L(-38, 48), 12, 9, 0, 4.5, "gable", material="stone")
    b("C", "granary", "Granary", *L(40, 48), 14, 9, 0, 6, "gable", material="stone")
    b("C", "armoury", "Armoury", *L(-60, -32), 16, 10, 90, 6, "gable", material="stone")
    b("C", "house", "Constable's House", *L(32, 14), 14, 9, 180, 8, "hip", material="stone", floors=2)
    b("C", "bakehouse", "Bakehouse & Brewhouse", *L(-30, 14), 13, 8, 180, 5, "gable", material="stone")
    b("C", "mews", "Falcon Mews", *L(-52, 34), 9, 6, 90, 4, "gable", material="timber")
    b("C", "guardhouse", "Guardhouse", *L(24, 58), 10, 7, 0, 5, "gable", material="stone")
    b("C", "dovecote", "Dovecote", *L(58, -32), 6, 6, 0, 8, "cone", material="stone", shape="round")
    W.prop("well", *L(18, -60), name="Keep well")
    W.prop("well", *L(22, 34), name="Bailey well")
    W.prop("training_dummy", *L(5, 30))
    W.prop("training_dummy", *L(-8, 32))
    W.prop("cart", *L(-20, 58), 30)
    # drawbridge and barbican
    W.prop("drawbridge", *L(0, 103), 0, w=5, length=26)
    bar = [L(-14, 140), L(-14, 118), L(14, 118), L(14, 140)]
    W.wall("Barbican", "barbican", bar, 8, 2.5, gaps=[L(0, 118), L(0, 140)], gap_r=6)
    W.tower("C", "Barbican turret (west)", *L(-14, 140), 3.5, 10)
    W.tower("C", "Barbican turret (east)", *L(14, 140), 3.5, 10)
    W.reserve_box(cx - PLATEAU_R, cy - PLATEAU_R, cx + PLATEAU_R, cy + PLATEAU_R)
    W.landmark("Great Tower (the Keep)", *L(0, -46), "28 m stone keep, last refuge of the castle; four storeys.")
    W.landmark("Inner Ward & Great Hall", *L(24, -22), "Lord's hall, chapel and kitchens behind a second wall.")
    W.landmark("Great Gatehouse", *L(0, 72), "Twin drum towers, portcullis and murder holes.")
    W.landmark("Drawbridge & Barbican", *L(0, 120), "Lifting bridge over the moat, guarded by a walled barbican.")
    W.landmark("Castle Moat", *L(-104, -30), "Spring-fed moat ringing the castle plateau.")
    W.landmark("Postern Gate", *L(0, -84), "Small north door to the ridge paths and watch posts.")


def _town(W):
    tx, ty = TOWN
    rx, ry = TOWN_R
    rel = lambda x, y: math.hypot((x - tx) / rx, (y - ty) / ry)
    wall_pts = ellipse_pts(tx, ty, rx, ry, 72, 0.0)
    g = W.gates
    W.wall("Town wall", "town", wall_pts, 8, 2.5, closed=True, gaps=list(g.values()), gap_r=5.5)
    for i, (x, y) in enumerate(wall_pts):
        if i % 6 == 3:
            W.tower("T", "Wall tower", x, y, 4.5, 11, roof="cone", group="Town wall")
    for key, nm in [("N", "North Gate"), ("S", "River Gate"), ("W", "West Gate"), ("E", "East Gate")]:
        x, y = g[key]
        W.building("T", "gatehouse", nm, x, y, 13, 10, 0 if key in "NS" else 90, 12, "crenel", material="stone",
                   check=False, passage_w=4.5, passage_h=5.5)
    # streets (resampled polylines with half-widths)
    streets = [
        W.road("High Street", "street", [g["N"], (tx, ty)], 9, "cobble"),
        W.road("High Street (south)", "street", [(tx, ty), g["S"]], 9, "cobble"),
        W.road("Market Street", "street", [g["W"], (tx, ty)], 8, "cobble"),
        W.road("Market Street (east)", "street", [(tx, ty), g["E"]], 8, "cobble"),
        W.road("Fish Lane", "street", [(930, 952), (928, 1080), (934, 1208)], 5, "cobble"),
        W.road("Mill Row", "street", [(1120, 952), (1121, 1080), (1114, 1208)], 5, "cobble"),
        W.road("Back Row (north)", "street", [(856, 1002), (1024, 998), (1192, 1002)], 5, "cobble"),
        W.road("Back Row (south)", "street", [(856, 1160), (1024, 1162), (1192, 1160)], 5, "cobble"),
    ]
    ring = ellipse_pts(tx, ty, rx * 0.84, ry * 0.84, 96)
    W.roads.append(dict(id=f"ROAD-{len(W.roads) + 1:02d}", name="Wall Walk Lane", kind="street", width=5,
                        surface="cobble", ctrl=ring, line=resample(ring + [ring[0]], 3.0), closed=True))
    streets.append(W.roads[-1])
    lines = [(s["line"], s["width"] / 2) for s in streets]
    W.town_streets = lines

    # market square and its civic buildings
    sq = (982, 1048, 1066, 1112)
    W.square = sq
    W.reserve_box(*sq)
    b = W.building
    b("T", "market_hall", "Market Hall", 1000, 1066, 18, 9, 0, 6, "hip", material="timber", check=False,
      open_ground_floor=True)
    W.prop("market_cross", 1042, 1094, name="Market Cross")
    W.prop("well", 1054, 1062, name="Market Well")
    W.prop("stocks", 990, 1102)
    for i, (sx, sy) in enumerate([(988, 1090), (996, 1090), (1004, 1090), (1012, 1104), (1020, 1104),
                                  (1034, 1056), (1042, 1056), (1050, 1056), (1058, 1076), (1058, 1084),
                                  (1030, 1104), (1060, 1100)]):
        W.prop("market_stall", sx, sy, 0 if sy > 1080 else 180, w=4, d=3)
    church = N["church"]
    b("T", "church", f"{church} (nave)", 1066, 1025, 30, 11, 0, 12, "gable", material="stone", group=church, check=False)
    b("T", "church", f"{church} (chancel)", 1088, 1025, 14, 8, 0, 10, "gable", material="stone", group=church, check=False)
    b("T", "church", f"{church} (transept)", 1072, 1025, 9, 24, 0, 12, "gable", material="stone", group=church, check=False)
    b("T", "church", f"{church} (bell tower)", 1046, 1025, 9, 9, 0, 22, "spire", roof_h=14, material="stone",
      group=church, check=False, floors=4)
    W.reserve_box(1036, 1006, 1112, 1044)
    W.churchyard = (1036, 1006, 1112, 1044)
    for i in range(14):
        gx = 1040 + (i % 7) * 10 + W.rng.uniform(-1, 1)
        gy = 1009 + (i // 7) * 30 + W.rng.uniform(-1, 1)
        W.prop("gravestone", gx, gy, 0)
    b("T", "guildhall", "Guildhall", 990, 1034, 24, 12, 180, 11, "hip", material="stone", floors=2)
    b("T", "inn", N["inn"], 990, 1126, 22, 13, 0, 9, "gable", material="timber", floors=2)
    b("T", "manor_house", f"{YOUR_HOUSE} (your house)", 1058, 1126, 16, 11, 0, 10, "hip", material="stone",
      floors=3, owner=YOU)
    b("T", "smithy", "Town Smithy", 835, 1091, 12, 9, 0, 5, "gable", material="stone")
    b("T", "barn", "Tithe Barn", 1036, 1222, 28, 12, 270, 7, "gable", material="stone")
    W.landmark("Market Square", 1024, 1080, "Heart of the town: market hall, cross, well and stalls.")
    W.landmark(church, 1066, 1025, "Parish church with a 36 m spire, the tallest thing in the vale.")
    W.landmark("Guildhall", 990, 1034, "Where the merchant guild meets and the town court sits.")
    W.landmark(N["inn"], 990, 1126, "The town's great inn - travellers, gossip and quests.")
    W.landmark(f"{YOUR_HOUSE} - YOUR HOUSE", 1058, 1126, f"Home of {YOU}. Start your journey here.")
    W.landmark("Town gates (N, W, E & River Gate)", *g["N"], "Four gatehouses close at curfew.")

    # burgage houses along every street
    def ok_inside(c):
        return all(rel(x, y) < 0.95 for x, y in c)

    for st in streets:
        for side in (1, -1):
            s = 4.0
            line = st["line"]
            total = float(np.hypot(*np.diff(line, axis=0).T).sum())
            while s < total - 4:
                fw = W.rng.uniform(7, 10.5)
                dd = W.rng.uniform(9, 12)
                x, y, ang, _ = along(line, 1, start=s + fw / 2, end=s + fw / 2 + 0.5)[0] if s + fw / 2 < total else (0, 0, 0, 0)
                s += fw + W.rng.uniform(0.3, 1.5)
                if x == 0:
                    break
                nx, ny = -math.sin(ang), math.cos(ang)
                off = st["width"] / 2 + 0.8 + dd / 2
                hx, hy = x + side * off * nx, y + side * off * ny
                hd = heading_facing(ang, side)
                c = rect_corners(hx, hy, fw, dd, hd)
                if not ok_inside(c) or W.near_line(c, lines, 0.3):
                    continue
                first, trade = W.person(TOWN_TRADES)
                kind = "shop" if W.rng.random() < 0.45 else "house"
                floors = W.rng.choice([2, 2, 2, 3])
                W.building("T", kind, f"House of {first} the {trade}", hx, hy, fw, dd, hd, 3 * floors,
                           W.rng.choice(["gable", "gable", "gable", "hip"]),
                           material=W.rng.choice(["timber", "timber", "timber", "stone"]), floors=floors,
                           trade=trade, resident=first, pad=0.3)


def _abbey(W):
    a = N["abbey"]
    W.zones.append(dict(name=a, kind="abbey", cx=560, cy=820, rx=120, ry=95))
    prec = [(460, 745), (660, 745), (660, 895), (460, 895)]
    W.wall("Abbey precinct wall", "precinct", prec, 3.2, 1.0, closed=True, gaps=[(562, 895), (460, 820)], gap_r=6)
    b = W.building
    b("A", "church", f"{a} (nave)", 540, 775, 46, 12, 0, 14, "gable", material="stone", group=a, check=False)
    b("A", "church", f"{a} (choir)", 578, 775, 20, 10, 0, 12, "gable", material="stone", group=a, check=False)
    b("A", "church", f"{a} (transepts)", 560, 775, 11, 30, 0, 14, "gable", material="stone", group=a, check=False)
    b("A", "church", f"{a} (crossing tower)", 560, 775, 11, 11, 0, 26, "spire", roof_h=10, material="stone",
      group=a, check=False)
    b("A", "cloister", "Chapter House & Dormitory", 571, 808, 36, 10, 90, 8, "gable", material="stone", check=False)
    b("A", "cloister", "Refectory", 548, 831, 36, 10, 180, 8, "gable", material="stone", check=False)
    b("A", "cloister", "Cellarium & Guest Range", 525, 808, 36, 10, 270, 8, "gable", material="stone", check=False)
    W.prop("garth", 548, 808, w=24, d=24)
    W.prop("well", 548, 808, name="Cloister well")
    b("A", "house", "Abbot's Lodging", 615, 815, 16, 9, 270, 8, "hip", material="stone", floors=2)
    b("A", "infirmary", "Infirmary", 622, 862, 18, 9, 180, 6, "gable", material="stone")
    b("A", "guest_house", "Pilgrims' Guest House", 520, 872, 18, 8, 0, 6, "gable", material="timber")
    b("A", "barn", "Abbey Barn", 478, 860, 26, 10, 90, 8, "gable", material="stone")
    b("A", "bakehouse", "Brewhouse & Bakehouse", 590, 878, 12, 8, 0, 5, "gable", material="stone")
    b("A", "gatehouse", "Abbey Gate", 562, 895, 9, 6, 180, 7, "gable", material="stone", check=False,
      passage_w=3, passage_h=4)
    W.orchards.append(dict(name="Abbey Orchard", poly=[(472, 752), (505, 752), (505, 838), (472, 838)], spacing=8))
    W.fields.append(dict(name="Herb Garden", field="Abbey", crop="herbs", poly=[(596, 790), (640, 790), (640, 804), (596, 804)]))
    for i, (px, py) in enumerate([(650, 940), (670, 966), (690, 992)]):
        W.waters.append(dict(id=f"WATER-P{i + 1}", name="Abbey fishpond", kind="pond", cx=px, cy=py, rx=17, ry=7,
                             heading=30, line=np.array(ellipse_pts(px, py, 17, 7, 24))))
        W.reserve(rect_corners(px, py, 38, 18, 30))
    W.landmark(a, 560, 790, "Benedictine abbey: church, cloister, infirmary and pilgrims' house.")
    W.landmark("Abbey fishponds", 670, 966, "Three stew ponds that feed the monks on fast days.")


def _village_row(W, district, road, s0, s1, trades, depth=42, avoid=()):
    line = road["line"]
    lines = W.road_lines() + W.water_lines()
    s = s0
    while s < s1:
        w = W.rng.uniform(12, 16)
        d = W.rng.uniform(6, 7.5)
        x, y, ang, _ = along(line, 1, start=s + w / 2, end=s + w / 2 + 0.5)[0]
        s += w + W.rng.uniform(5, 12)
        for side in (1, -1):
            if W.rng.random() > 0.8:
                continue
            nx, ny = -math.sin(ang), math.cos(ang)
            off = road["width"] / 2 + 3 + d / 2
            hx, hy = x + side * off * nx, y + side * off * ny
            hd = heading_facing(ang, side)
            croft_off = off + d / 2 + 1 + depth / 2
            cx_, cy_ = x + side * croft_off * nx, y + side * croft_off * ny
            hc = rect_corners(hx, hy, w + 1, d + 1, hd)
            cc = rect_corners(cx_, cy_, w + 4, depth, hd)
            if any(point_in_poly(px, py, a) for a in avoid for px, py in hc + cc):
                continue
            if W.blocked(hc) or W.blocked(cc) or W.near_line(hc, lines, 0.5) or W.near_line(cc, lines, 1.0):
                continue
            first, trade = W.person(trades)
            b = W.building(district, "longhouse", f"Cottage of {first} the {trade}", hx, hy, w, d, hd,
                           3.2, "gable", material=W.rng.choice(["wattle", "wattle", "timber"]), check=False,
                           roof_h=3.6, trade=trade, resident=first, thatch=True)
            W.reserve(cc)
            W.crofts.append(dict(owner=b["id"], poly=[tuple(map(lambda v: round(v, 2), p)) for p in cc]))
            if W.rng.random() < 0.45:
                bo = off + d / 2 + 9
                W.building(district, "barn", f"Barn of {first}", x + side * bo * nx, y + side * bo * ny,
                           W.rng.uniform(8, 11), 6, hd, 3.5, "gable", material="timber", check=False, thatch=True)


def _villages(W):
    roads = {r["name"]: r for r in W.roads}
    # --- Westbrook (on the King's Road where the West Brook crosses it)
    green = ellipse_pts(470, 1098, 40, 20, 32)
    W.pastures.append(dict(name="Westbrook Green", poly=green))
    W.waters.append(dict(id="WATER-P4", name="Village pond", kind="pond", cx=482, cy=1100, rx=10, ry=6,
                         line=np.array(ellipse_pts(482, 1100, 10, 6, 20))))
    W.reserve(rect_corners(470, 1098, 84, 44, 0))
    b = W.building
    b("W", "chapel", "St. Wulfric's Chapel", 405, 1086, 14, 7, 0, 6, "gable", material="stone")
    b("W", "inn", N["village_inn"], 545, 1082, 15, 8, 0, 6, "gable", material="timber", floors=2, thatch=True)
    b("W", "smithy", "Westbrook Smithy", 335, 1080, 10, 8, 0, 4, "gable", material="stone")
    W.prop("well", 455, 1074, name="Westbrook well")
    W.prop("maypole", 462, 1098)
    kr = roads["King's Road (west)"]
    _village_row(W, "W", kr, 230, 640, VILLAGE_TRADES, avoid=[green])
    W.pastures.append(dict(name="Westbrook Common", poly=ellipse_pts(150, 950, 135, 70, 40, 0.08, seed=8),
                           sheep=14))
    W.landmark(f"{N['west_village']} green & chapel", 470, 1098, "Village green, pond, maypole and chapel.")

    # --- Eastmere (between East Bridge and the mere)
    b("E", "inn", N["mere_inn"], 1772, 1062, 14, 8, 180, 6, "gable", material="timber", floors=2, thatch=True)
    b("E", "chapel", "Chapel of St. Peter", 1650, 1060, 12, 7, 180, 6, "gable", material="stone")
    for i, (hx, hy) in enumerate([(1812, 1112), (1880, 1110)]):
        b("E", "hut", "Fisher's hut", hx, hy, 7, 5, 180, 2.8, "gable", material="wattle", thatch=True)
    W.prop("jetty", 1846, 1112, 180, w=3, length=16)
    W.prop("boat", 1838, 1126, 80)
    W.prop("boat", 1858, 1130, 100)
    ke = roads["King's Road (east)"]
    lake = W.waters[2]["line"].tolist()
    _village_row(W, "E", ke, 380, 640, VILLAGE_TRADES, depth=38, avoid=[lake])
    W.orchards.append(dict(name="Eastmere Orchard", poly=[(1690, 880), (1800, 880), (1800, 955), (1690, 955)], spacing=9))
    W.reserve_box(1690, 880, 1800, 955)
    W.landmark(f"{N['east_village']} & {N['mere']}", 1860, 1190, "Fishing village on a reed-fringed mere.")

    # --- Southfold (shepherds' hamlet on the South Road)
    sr = roads["South Road"]
    b("S", "sheepfold", "Southfold Sheep Pen", 1080, 1770, 26, 18, 270, 1.4, "none", material="stone", fence=True)
    _village_row(W, "S", sr, 360, 640, VILLAGE_TRADES, depth=36)
    W.landmark(N["south_hamlet"], 1000, 1700, "Shepherds' hamlet with a great stone sheep pen.")


def _outlying(W):
    b = W.building
    river = W.waters[0]["line"]
    # watch posts on the hilltops
    for nm, (x, y), lm in [(f"{N['peak_nw']} Watchtower", (535, 336), True),
                           (f"{N['peak_ne']} Watchtower", (1490, 306), True),
                           (f"{N['peak_w']} Watchtower", (272, 712), True)]:
        b("O", "watchtower", nm, x, y, 8, 8, 180, 15, "crenel", material="stone", floors=3)
        W.prop("beacon", x + 6, y - 6)
        W.landmark(nm, x, y, "Lookout with a signal beacon, in sight of the castle keep.")
    W.tower("O", f"{N['peak_n']} Beacon", 1000, 168, 4, 9, roof="crenel")
    W.prop("beacon", 1000, 160)
    W.landmark(f"{N['peak_n']} Beacon", 1000, 168, "Highest point of the vale: the great warning fire.")
    # stone circle
    for i in range(9):
        t = 2 * math.pi * i / 9
        W.prop("standing_stone", 800 + 13 * math.cos(t), 304 + 13 * math.sin(t), math.degrees(t) + 90,
               h=round(W.rng.uniform(2.2, 3.4), 1))
    W.prop("altar_stone", 800, 304)
    W.landmark(N["stones"], 800, 304, "Ancient ring of nine stones older than the castle. Locals leave offerings.")
    # bridges, ford and the mills on the river
    W.prop("stepping_stones", 700, 1480, 160, length=30)
    W.landmark(N["ford"], 700, 1480, "Shallow crossing where the first settlers forded the Ash - the vale's namesake.")
    s_mill = None
    cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(river, axis=0).T))])
    for i, (x, y) in enumerate(river):
        if s_mill is None and y > 1290:
            s_mill = cum[i]
    x, y, ang, _ = along(river, 1, start=s_mill, end=s_mill + 0.5)[0]
    nx, ny = -math.sin(ang), math.cos(ang)
    side = -1 if ny > 0 else 1                         # the bank facing the town (north)
    mx, my = x + side * 26 * nx, y + side * 26 * ny
    hd = heading_facing(ang, side) + 180
    b("O", "watermill", "Ashford Watermill", mx, my, 14, 10, hd, 7, "gable", material="stone", floors=2)
    W.prop("waterwheel", x + side * 16.5 * nx, y + side * 16.5 * ny, math.degrees(ang), r=3.5, w=1.4)
    W.landmark("Ashford Watermill", mx, my, "Grinds the vale's grain; the miller takes one sack in sixteen.")
    x2, y2, ang2, _ = along(river, 1, start=s_mill + 70, end=s_mill + 70.5)[0]
    tx, ty = x2 + side * 34 * (-math.sin(ang2)), y2 + side * 34 * math.cos(ang2)
    b("O", "tannery", "Tannery", tx, ty, 12, 8, heading_facing(ang2, side) + 180, 5, "gable", material="timber")
    for k in range(4):
        W.prop("vat", tx - 10 + k * 5, ty + 9 * side)
    W.landmark("Tannery", tx, ty, "Smelly work kept downstream and outside the walls.")
    # windmill on its knoll
    b("O", "windmill", "Post Windmill", 712, 1334, 6, 6, 200, 9, "gable", material="timber", sails=11)
    W.landmark("Post Windmill", 712, 1334, "Turns to face the wind on a single great post.")
    # tiltyard
    W.zones.append(dict(name="Tiltyard", kind="tiltyard", cx=1300, cy=880, rx=70, ry=30))
    W.wall("Tilt barrier", "fence", [(1252, 880), (1348, 880)], 1.5, 0.4, material="wood")
    b("O", "stand", "Lords' Stand", 1300, 860, 40, 6, 180, 4, "flat", material="timber", check=False)
    b("O", "stand", "Common Stand", 1300, 902, 40, 6, 0, 3, "flat", material="timber", check=False)
    W.prop("pavilion", 1240, 880, r=4)
    W.prop("pavilion", 1360, 880, r=4)
    W.reserve_box(1230, 850, 1370, 910)
    W.landmark("Tiltyard", 1300, 880, "Jousting lists for the summer tourney.")
    # quarry
    b("O", "hut", "Quarrymen's Lodge", 1255, 728, 8, 5, 90, 3, "gable", material="timber")
    W.prop("crane", 1300, 690)
    for k in range(5):
        W.prop("stone_block", 1265 + k * 4, 745, w=2, d=1.2, h=1)
    W.landmark("Quarry", 1300, 700, "Where the castle's stone was cut. Still worked today.")
    # hunting lodge & charcoal burners
    b("O", "lodge", N["lodge"], 1915, 400, 18, 9, 180, 7, "hip", material="timber", floors=2)
    b("O", "kennels", "Kennels", 1890, 422, 10, 5, 90, 3, "gable", material="timber")
    W.zones.append(dict(name="Lodge clearing", kind="clearing", cx=1905, cy=405, rx=45, ry=40))
    W.landmark(N["lodge"], 1915, 400, "Royal hunting lodge deep in the deer forest.")
    b("O", "hut", "Charcoal Burner's Hut", 210, 330, 5, 4, 90, 2.5, "gable", material="wattle", thatch=True)
    for k, (px, py) in enumerate([(230, 316), (236, 344), (196, 352)]):
        W.prop("charcoal_clamp", px, py, r=4)
    W.zones.append(dict(name="Charcoal clearing", kind="clearing", cx=218, cy=335, rx=30, ry=28))
    W.landmark("Charcoal Burners' Camp", 218, 335, "Smoke rises day and night from the Wildwood clearing.")
    # farmsteads
    for i, (fx, fy, hd) in enumerate([(640, 1610, 0), (1400, 1450, 90), (2000, 1480, 270), (90, 1120, 0)]):
        first, _ = W.person(VILLAGE_TRADES)
        if b("O", "farmhouse", f"{first}'s Farm", fx, fy, 14, 7, hd, 3.5, "gable", material="timber",
             thatch=True) is None:
            continue
        a = math.radians(hd)
        b("O", "barn", f"{first}'s Barn", fx - 14 * math.sin(a), fy + 14 * math.cos(a), 18, 8, hd, 5, "gable",
          material="timber", check=False, thatch=True)
        W.prop("haystack", fx + 12 * math.cos(a), fy + 12 * math.sin(a))
        W.prop("haystack", fx + 15 * math.cos(a) + 5, fy + 15 * math.sin(a) + 4)
    W.landmark(N["bridge_s"], 0, 0, "Three-arched stone bridge below the River Gate.")
    W.landmark(N["bridge_e"], 0, 0, "Timber bridge carrying the King's Road east.")


def _fields(W):
    furlongs = {
        "West Field": ("fallow", [(150, 1240, 220, 180, -4), (420, 1240, 220, 180, 6),
                                  (150, 1470, 220, 200, 3), (410, 1440, 200, 140, -5)]),
        "Abbey Furlong": ("wheat", [(690, 1200, 125, 150, 0)]),
        "South Field": ("wheat", [(810, 1720, 220, 200, 4), (810, 1950, 220, 170, -3),
                                  (1200, 1700, 240, 200, -6), (1200, 1945, 260, 190, 5)]),
        "East Field": ("spring", [(1560, 1450, 220, 200, -4), (1820, 1470, 240, 200, 6),
                                  (1570, 1720, 230, 200, 3), (1850, 1740, 240, 220, -5)]),
    }
    crops = {"fallow": ["fallow", "fallow", "fallow", "grazing"], "wheat": ["wheat", "wheat", "rye"],
             "spring": ["barley", "oats", "beans", "peas", "barley"]}
    for fname, (season, blocks) in furlongs.items():
        for k, (cx, cy, w, h, ang) in enumerate(blocks):
            outline = rect_corners(cx, cy, w, h, ang)
            x = -w / 2
            while x < w / 2 - 5:
                sw = min(W.rng.choice([16, 18, 20, 22, 24]), w / 2 - x)
                scx = x + sw / 2
                a = math.radians(ang)
                px, py = cx + scx * math.cos(a), cy + scx * math.sin(a)
                W.fields.append(dict(name=f"{fname} strip", field=fname, furlong=k + 1,
                                     crop=W.rng.choice(crops[season]),
                                     poly=[tuple(round(v, 2) for v in c) for c in rect_corners(px, py, sw, h, ang)]))
                x += sw
            W.reserve(outline)
            W.fields.append(dict(name=f"{fname} furlong {k + 1}", field=fname, furlong=k + 1, crop="outline",
                                 poly=[tuple(round(v, 2) for v in c) for c in outline]))


def _vegetation_regions(W):
    W.forests = [
        dict(name=N["forest_nw"], kind="mixed", poly=[(0, 0), (430, 0), (400, 180), (340, 380), (230, 520),
                                                       (120, 600), (0, 620)], spacing=9.5),
        dict(name=N["forest_ne"], kind="deer forest", poly=[(1790, 0), (2048, 0), (2048, 880), (1960, 900),
                                                             (1880, 820), (1830, 620), (1800, 400)], spacing=9.5),
        dict(name=N["forest_sw"], kind="mixed", poly=[(0, 1700), (250, 1660), (450, 1720), (600, 1860),
                                                       (640, 2048), (0, 2048)], spacing=10),
    ]


def _labels(W):
    L = W.labels
    L += [
        dict(t=N["castle"].upper(), x=1024, y=432, size=30, kind="place", sub="seat of the Baron on Castle Mount"),
        dict(t=N["town"].upper(), x=1290, y=1180, size=30, kind="place", sub="walled market town"),
        dict(t=N["west_village"].upper(), x=470, y=1015, size=24, kind="place", sub="village"),
        dict(t=N["east_village"].upper(), x=1730, y=990, size=24, kind="place", sub="village"),
        dict(t=N["south_hamlet"].upper(), x=1110, y=1840, size=22, kind="place", sub="hamlet"),
        dict(t=N["north_hills"].upper(), x=760, y=60, size=20, kind="region"),
        dict(t=N["forest_nw"].upper(), x=170, y=210, size=22, kind="region"),
        dict(t=N["forest_ne"].upper(), x=1935, y=640, size=20, kind="region"),
        dict(t=N["forest_sw"].upper(), x=300, y=1930, size=20, kind="region"),
        dict(t="WEST FIELD", x=285, y=1365, size=15, kind="field", sub="fallow this year - sheep graze it"),
        dict(t="SOUTH FIELD", x=1005, y=1985, size=15, kind="field", sub="winter wheat & rye"),
        dict(t="EAST FIELD", x=1700, y=1605, size=15, kind="field", sub="barley, oats, beans & peas"),
        dict(t="ABBEY FURLONG", x=690, y=1112, size=11, kind="field"),
        dict(t="WESTBROOK COMMON", x=150, y=900, size=12, kind="field"),
        dict(t="CASTLE MOUNT", x=860, y=720, size=13, kind="region"),
        dict(t=N["river"].upper(), x=1640, y=600, size=18, kind="water", rot=-76),
        dict(t=N["river"].upper(), x=560, y=1525, size=18, kind="water", rot=-22),
        dict(t=N["brook"], x=318, y=820, size=12, kind="water", rot=72),
        dict(t=N["mere"], x=1880, y=1196, size=14, kind="water"),
    ]
