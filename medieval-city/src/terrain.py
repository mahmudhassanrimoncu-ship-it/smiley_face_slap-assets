"""Builds the heightmap (1 sample per metre) from the city layout.

Order of operations:
  1. land that rises from the coast towards the western and northern hills,
     with ridges, peaks and rugged high ground; the sea floor falls away offshore
  2. cliffs on the headlands
  3. the castle crag and other flat-topped hills
  4. built-up districts graded into gentle slopes; squares, compounds, marsh and salt pans levelled
  5. prehistoric earthworks: hillfort ramparts, barrows, mounds
  6. rivers and streams carved so water always runs downhill to the sea; lake and ponds
  7. streets and roads graded into the slopes
  8. upsampling to 1 m with fine detail outside built-up ground
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from config import SEA_LEVEL, SEED, WORLD_SIZE
from geom import blur, fbm, polyline_field, resize, sample, smoothstep

R = 1025                      # working resolution
CELL = WORLD_SIZE / (R - 1)   # 4 m per cell
FINAL = WORLD_SIZE + 1        # export resolution (1 m per cell)


def _poly_mask(polys, res=R, cell=CELL):
    img = Image.new("L", (res, res), 0)
    d = ImageDraw.Draw(img)
    for p in polys:
        d.polygon([(x / cell, y / cell) for x, y in p], fill=255)
    return np.asarray(img, dtype=np.float32) / 255.0


def _ellipse_q(xs, ys, cx, cy, rx, ry, heading=0.0):
    rot = math.radians(heading)
    dx, dy = xs - cx, ys - cy
    lx, ly = dx * math.cos(rot) + dy * math.sin(rot), -dx * math.sin(rot) + dy * math.cos(rot)
    return np.hypot(lx / rx, ly / ry)


def build_heightmap(W):
    ys, xs = np.mgrid[0:R, 0:R].astype(np.float32) * CELL
    n_base = fbm(R, SEED, octaves=7, base=3)
    n_amp = fbm(R, SEED + 1, octaves=4, base=2)
    n_ridge = 1 - np.abs(2 * fbm(R, SEED + 2, octaves=7, base=4) - 1)

    # ---- land and sea: signed distance from the coast (positive inland)
    sea = _poly_mask([W.sea_poly])
    d_coast, _ = polyline_field(W.coast, R, CELL, 3000)
    for isl in getattr(W, "islands", []):                    # islands rise out of the sea
        sea = np.minimum(sea, 1 - _poly_mask([isl]))
        d_i, _ = polyline_field(np.array(isl + [isl[0]]), R, CELL, 3000)
        d_coast = np.minimum(d_coast, d_i)
    signed = np.where(sea > 0.5, -d_coast, d_coast)
    land = SEA_LEVEL + 3 + 0.016 * np.clip(signed, 0, None) + 18 * (n_base - 0.5) * smoothstep(0, 300, signed)
    seabed = SEA_LEVEL - 2 - np.minimum(16, 0.02 * np.clip(-signed, 0, None))
    h = np.where(signed > 0, land, seabed)

    hill = np.zeros_like(h)
    for r in W.ridges:
        d, _ = polyline_field(r["pts"], R, CELL, r["w"] * 2.6)
        hill += r["h"] * (0.6 + 0.8 * n_amp) * np.exp(-(d / r["w"]) ** 2)
    warp_x = 220 * (fbm(R, SEED + 3, octaves=4, base=3) - 0.5)
    warp_y = 220 * (fbm(R, SEED + 4, octaves=4, base=3) - 0.5)
    for p in W.peaks:
        q = ((xs + warp_x - p["x"]) / p["rx"]) ** 2 + ((ys + warp_y - p["y"]) / p["ry"]) ** 2
        hill += p["h"] * np.exp(-q * 1.6) * (0.8 + 0.4 * n_amp)
    hill *= smoothstep(-20, 120, signed)
    h += hill
    h += 20 * n_ridge**2 * smoothstep(25, 90, hill)

    # ---- headland cliffs: land inside these circles stands high right to the water's edge
    for c in W.cliffs:
        q = np.hypot(xs - c["x"], ys - c["y"]) / c["r"]
        lift = c["h"] * smoothstep(1.0, 0.55, q) * smoothstep(-4, 18, signed)
        h = np.where(signed > 0, h + lift, h)

    # ---- castle crag and flat-topped hills
    flat = np.zeros_like(h)
    for p in W.plateaus:
        ang = np.arctan2(ys - p["y"], xs - p["x"])
        rr = np.hypot(xs - p["x"], ys - p["y"]) / (1 + 0.07 * np.sin(3 * ang + 0.7) + 0.04 * np.sin(5 * ang))
        t = smoothstep(p["r"] + p["fall"], p["r"], rr) ** 0.7          # 1 on the plateau, 0 beyond its flanks
        crag = 12 * n_ridge * smoothstep(p["r"] + p["fall"], p["r"] + 10, rr) * smoothstep(p["r"] + 5, p["r"] + 40, rr)
        h = np.where(rr < p["r"], p["z"], np.maximum(h, h + (p["z"] - h) * t + crag * (t > 0)))
        flat = np.maximum(flat, smoothstep(p["r"] + 6, p["r"] - 4, rr))

    # ---- built-up ground graded into gentle slopes
    built = blur(_poly_mask(W.built_polys), 12)
    soft = blur(h, 40)
    wgt = 0.8 * built * smoothstep(0, 40, signed)
    h = h * (1 - wgt) + soft * wgt
    flat = np.maximum(flat, wgt)
    for x0, y0, rx, ry, k in W.pads:
        qq = np.hypot((xs - x0) / rx, (ys - y0) / ry)
        w2 = k * smoothstep(1.3, 1.0, qq)
        target = max(float(sample(soft, x0, y0)), SEA_LEVEL + 2.5)
        h = h * (1 - w2) + target * w2
        flat = np.maximum(flat, w2)
    for poly, z in W.level_polys:
        m = blur(_poly_mask([poly]), 3)
        h = h * (1 - m) + z * m
        flat = np.maximum(flat, m)

    # ---- prehistoric earthworks
    for e in W.earthworks:
        if e["kind"] == "ring":
            rr = np.hypot(xs - e["cx"], ys - e["cy"])
            ang = np.degrees(np.arctan2(ys - e["cy"], xs - e["cx"])) % 360
            gap = np.zeros_like(rr)
            for g in e.get("gaps", []):
                da = np.abs((ang - g + 180) % 360 - 180) * np.pi / 180 * rr
                gap = np.maximum(gap, smoothstep(e["gap_w"] / 2 + 6, e["gap_w"] / 2, da))
            mid, half = (e["r0"] + e["r1"]) / 2, (e["r1"] - e["r0"]) / 2
            prof = np.clip(1 - ((rr - mid) / half) ** 2, 0, 1)
            h = h + e["h"] * prof * (1 - gap)
        else:
            qq = _ellipse_q(xs, ys, e["x"], e["y"], e["rx"], e["ry"], e.get("heading", 0))
            h = h + e["h"] * np.clip(1 - qq**2, 0, 1) ** 0.6
            flat = np.maximum(flat, smoothstep(1.3, 1.0, qq))

    # ---- rivers & streams: levels fall monotonically and reach the sea at sea level
    soft2 = blur(h, 6)
    river_d = np.full_like(h, np.inf)
    for w in W.waters:
        if w["kind"] not in ("river", "stream"):
            continue
        line = w["line"]
        if "levels_from" in w:                     # a channel that shares its parent's levels
            src = next(v for v in W.waters if v["id"] == w["levels_from"])
            level = np.interp(np.linspace(0, 1, len(line)), [0, 1], [w["start_level"](src), w["end_level"](src)])
        else:
            ground = sample(soft2, line[:, 0], line[:, 1])
            drop = 3.5 if w["kind"] == "river" else 1.2
            level = np.minimum.accumulate(ground - drop)
            level = np.convolve(np.pad(level, 6, mode="edge"), np.ones(13) / 13, mode="valid")
            level = np.minimum.accumulate(np.maximum(level, SEA_LEVEL + 0.15))
            if w.get("to_sea"):
                level = np.maximum(SEA_LEVEL + 0.1, level - (level[-1] - SEA_LEVEL - 0.1) * np.linspace(0, 1, len(level)) ** 2)
        w["levels"] = np.round(level, 2)
        cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(line, axis=0).T))])
        reach = w.get("reach", 140 if w["kind"] == "river" else 30)
        d, s = polyline_field(line, R, CELL, reach + 5)
        lv = np.interp(s, cum, level).astype(np.float32)
        half = w["width"] / 2
        bank = lv + (2.4 if w["kind"] == "river" else 0.8)
        fp = smoothstep(half + 3, reach, d)
        onland = signed > 2                                   # rivers shape the land, never the sea floor
        h = np.where((d < reach) & onland, bank + (h - bank) * fp, h)
        depth = 4.0 if w["kind"] == "river" else 1.2
        bed = lv - depth + (depth + 0.8) * (d / (half + 3)) ** 2
        h = np.where(d < half + 3, np.minimum(h, bed), h)
        if w["kind"] == "river":
            river_d = np.minimum(river_d, d)
        flat = np.maximum(flat, smoothstep(reach, half, d))
    for w in W.waters:
        if w["kind"] not in ("lake", "pond"):
            continue
        qq = _ellipse_q(xs, ys, w["cx"], w["cy"], w["rx"], w["ry"], w.get("heading", 0))
        t = np.linspace(0, 2 * np.pi, 48, endpoint=False)
        rot = math.radians(w.get("heading", 0))
        ex, ey = 1.22 * w["rx"] * np.cos(t), 1.22 * w["ry"] * np.sin(t)
        shore = sample(h, w["cx"] + ex * math.cos(rot) - ey * math.sin(rot), w["cy"] + ex * math.sin(rot) + ey * math.cos(rot))
        w["level"] = round(max(float(shore.min()) - (1.0 if w["kind"] == "lake" else 0.4), SEA_LEVEL + 0.5), 2)
        depth = 6.0 if w["kind"] == "lake" else 1.5
        target = w["level"] - depth * (1 - np.minimum(qq, 1) ** 2) - 0.2
        h = np.where(qq < 1.0, np.minimum(h, target), h)
        edge = (qq >= 1.0) & (qq < 1.5)
        h = np.where(edge, np.maximum(h, w["level"] + 0.3 * smoothstep(1.0, 1.2, qq)), h)
        flat = np.maximum(flat, smoothstep(1.6, 1.0, qq))

    # ---- streets & roads graded into the land, except where they cross water
    soft3 = blur(h, 3)
    for r in W.roads:
        if r["kind"] in ("path", "avenue"):
            continue
        half = r["width"] / 2
        d, _ = polyline_field(r["line"], R, CELL, half + 16)
        wgt = smoothstep(half + 12, half + 2, d) * 0.8 * smoothstep(40, 70, river_d)
        h = h * (1 - wgt) + soft3 * wgt
        flat = np.maximum(flat, wgt)

    H = resize(h, FINAL)
    detail = (fbm(FINAL, SEED + 7, octaves=4, base=192) - 0.5) * 1.6
    H = H + detail * (1 - resize(np.clip(flat, 0, 1), FINAL, method=2))
    W.river_dist = resize(np.minimum(river_d, 600), FINAL)
    W.sea_mask = resize(sea, FINAL, method=2) > 0.5
    return H.astype(np.float32)


def slope_deg(H):
    gy, gx = np.gradient(H, WORLD_SIZE / (H.shape[0] - 1))
    return np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32)
