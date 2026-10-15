"""Builds the 2049 x 2049 heightmap (1 sample per metre) from the city layout.

Order of operations:
  1. rolling land rising to the northern hills, with ridges and peaks
  2. the castle crag: a flat-topped rock with cliffs to the north
  3. the walled city graded into gentle terraces sloping down to the river
  4. prehistoric earthworks: the henge ditch & bank, barrows, the long barrow
  5. river, brook and ponds carved so water always runs downhill
  6. the dry ditch outside the city wall, then streets graded into the slope
  7. upsampling to 1 m with fine detail outside built-up ground
"""
import math

import numpy as np

from config import SEED, WORLD_SIZE
from geom import blur, fbm, polyline_field, resize, sample, smoothstep

R = 1025                      # working resolution (2 m per cell)
CELL = WORLD_SIZE / (R - 1)
FINAL = 2049                  # export resolution (1 m per cell)


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

    h = 46 + 34 * (1 - ys / WORLD_SIZE) + 14 * (n_base - 0.5)
    hill = np.zeros_like(h)
    for r in W.ridges:
        d, _ = polyline_field(r["pts"], R, CELL, r["w"] * 2.6)
        hill += r["h"] * (0.6 + 0.8 * n_amp) * np.exp(-(d / r["w"]) ** 2)
    warp_x = 140 * (fbm(R, SEED + 3, octaves=4, base=3) - 0.5)
    warp_y = 140 * (fbm(R, SEED + 4, octaves=4, base=3) - 0.5)
    for p in W.peaks:
        q = ((xs + warp_x - p["x"]) / p["rx"]) ** 2 + ((ys + warp_y - p["y"]) / p["ry"]) ** 2
        hill += p["h"] * np.exp(-q * 1.6) * (0.8 + 0.4 * n_amp)
    h += hill
    h += 22 * n_ridge**2 * smoothstep(20, 80, hill)

    # ---- the walled city: blend toward a smooth surface that falls gently to the river
    city_q = _ellipse_q(xs, ys, *W.city_ellipse)
    soft = blur(h, 120)
    wgt = 0.85 * smoothstep(1.45, 0.85, city_q)
    h = h * (1 - wgt) + soft * wgt
    flat = wgt.copy()

    # ---- castle crag: flat top, cliffs, merges with the ridge behind
    for p in W.plateaus:
        ang = np.arctan2(ys - p["y"], xs - p["x"])
        rr = np.hypot(xs - p["x"], ys - p["y"]) / (1 + 0.05 * np.sin(3 * ang + 0.7) + 0.03 * np.sin(5 * ang))
        prof = p["base"] + (p["z"] - p["base"]) * smoothstep(p["r"] + p["fall"], p["r"], rr) ** 0.7
        crag = 10 * n_ridge * smoothstep(p["r"] + p["fall"], p["r"] + 8, rr) * smoothstep(p["r"] + 5, p["r"] + 30, rr)
        h = np.where(rr < p["r"], p["z"], np.maximum(h, prof + crag))
        flat = np.maximum(flat, smoothstep(p["r"] + 6, p["r"] - 4, rr))

    for x0, y0, rx, ry, k in W.pads:
        qq = np.hypot((xs - x0) / rx, (ys - y0) / ry)
        wgt = k * smoothstep(1.3, 1.0, qq)
        target = float(sample(blur(h, 30), x0, y0))
        h = h * (1 - wgt) + target * wgt
        flat = np.maximum(flat, wgt)

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
        else:  # mound / long barrow
            qq = _ellipse_q(xs, ys, e["x"], e["y"], e["rx"], e["ry"], e.get("heading", 0))
            h = h + e["h"] * np.clip(1 - qq**2, 0, 1) ** 0.6
            flat = np.maximum(flat, smoothstep(1.3, 1.0, qq))

    # ---- water
    soft2 = blur(h, 20)
    river_d = np.full_like(h, np.inf)
    for w in W.waters:
        if w["kind"] not in ("river", "stream"):
            continue
        line = w["line"]
        ground = sample(soft2, line[:, 0], line[:, 1])
        drop = 3.0 if w["kind"] == "river" else 1.0
        level = np.minimum.accumulate(ground - drop)
        level = np.convolve(np.pad(level, 6, mode="edge"), np.ones(13) / 13, mode="valid")
        level = np.minimum.accumulate(level)
        w["levels"] = np.round(level, 2)
        cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(line, axis=0).T))])
        reach = w.get("reach", 120 if w["kind"] == "river" else 30)
        d, s = polyline_field(line, R, CELL, reach + 5)
        lv = np.interp(s, cum, level).astype(np.float32)
        half = w["width"] / 2
        bank = lv + (2.2 if w["kind"] == "river" else 0.8)
        fp = smoothstep(half + 3, reach, d)
        h = np.where(d < reach, bank + (h - bank) * fp, h)
        depth = 3.5 if w["kind"] == "river" else 1.2
        bed = lv - depth + (depth + 0.8) * (d / (half + 2.5)) ** 2
        h = np.where(d < half + 2.5, np.minimum(h, bed), h)
        if w["kind"] == "river":
            river_d = d
        flat = np.maximum(flat, smoothstep(reach, half, d))
    for w in W.waters:
        if w["kind"] not in ("lake", "pond"):
            continue
        qq = _ellipse_q(xs, ys, w["cx"], w["cy"], w["rx"], w["ry"], w.get("heading", 0))
        ring = (qq > 1.15) & (qq < 1.3)
        w["level"] = round(float(h[ring].min()) - 0.4, 2)
        target = w["level"] - 1.5 * (1 - np.minimum(qq, 1) ** 2) - 0.2
        h = np.where(qq < 1.0, np.minimum(h, target), h)
        edge = (qq >= 1.0) & (qq < 1.5)
        h = np.where(edge, np.maximum(h, w["level"] + 0.3 * smoothstep(1.0, 1.2, qq)), h)
        flat = np.maximum(flat, smoothstep(1.6, 1.0, qq))

    # ---- the dry ditch outside the city wall
    cq = _ellipse_q(xs, ys, *W.city_ellipse)
    mean_r = (W.city_ellipse[2] + W.city_ellipse[3]) / 2
    dd = (cq - W.ditch_q) * mean_r
    ditch = np.clip(1 - (dd / 9) ** 2, 0, 1) * 4.5 * smoothstep(30, 60, river_d)
    h = h - ditch

    # ---- streets & roads graded into the land, except where they cross water
    soft3 = blur(h, 8)
    for r in W.roads:
        if r["kind"] == "path":
            continue
        half = r["width"] / 2
        d, _ = polyline_field(r["line"], R, CELL, half + 14)
        wgt = smoothstep(half + 10, half + 1, d) * 0.85 * smoothstep(34, 55, river_d)
        h = h * (1 - wgt) + soft3 * wgt
        flat = np.maximum(flat, wgt)

    H = resize(h, FINAL)
    detail = (fbm(FINAL, SEED + 7, octaves=4, base=96) - 0.5) * 1.4
    H = H + detail * (1 - resize(np.clip(flat, 0, 1), FINAL, method=2))
    W.river_dist = resize(np.minimum(river_d, 400), FINAL)
    return H.astype(np.float32)


def slope_deg(H):
    gy, gx = np.gradient(H, WORLD_SIZE / (H.shape[0] - 1))
    return np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32)
