"""Builds the 2049 x 2049 heightmap (1 sample per metre) from the world layout.

Order of operations:
  1. rolling base land, rising towards the northern hills
  2. ridgelines and named peaks (+ rugged noise on high ground)
  3. the castle mount with its flat plateau and moat ditch
  4. settlements, abbey and tiltyard flattened into gentle building pads
  5. rivers/streams/lake/ponds carved with water levels that always run downhill
  6. roads graded into the slopes (cut & fill), bridges left alone
  7. quarry pit, then upsampling to 1 m with a little fine detail
"""
import math

import numpy as np

from config import SEED, WORLD_SIZE
from geom import blur, fbm, polyline_field, resize, sample, smoothstep
from layout import CASTLE, PLATEAU_R, PLATEAU_Z

R = 1025                      # working resolution (2 m per cell)
CELL = WORLD_SIZE / (R - 1)
FINAL = 2049                  # export resolution (1 m per cell)


def build_heightmap(W):
    ys, xs = np.mgrid[0:R, 0:R].astype(np.float32) * CELL
    n_base = fbm(R, SEED, octaves=7, base=3)
    n_amp = fbm(R, SEED + 1, octaves=4, base=2)
    n_ridge = 1 - np.abs(2 * fbm(R, SEED + 2, octaves=7, base=4) - 1)

    h = 52 + 30 * (1 - ys / WORLD_SIZE) + 16 * (n_base - 0.5)

    hill = np.zeros_like(h)
    for r in W.ridges:
        d, _ = polyline_field(r["pts"], R, CELL, r["w"] * 2.6)
        hill += r["h"] * (0.6 + 0.8 * n_amp) * np.exp(-(d / r["w"]) ** 2)
    warp_x = 140 * (fbm(R, SEED + 3, octaves=4, base=3) - 0.5)       # domain warp: no perfect domes
    warp_y = 140 * (fbm(R, SEED + 4, octaves=4, base=3) - 0.5)
    for p in W.peaks:
        q = ((xs + warp_x - p["x"]) / p["rx"]) ** 2 + ((ys + warp_y - p["y"]) / p["ry"]) ** 2
        hill += p["h"] * np.exp(-q * 1.6) * (0.8 + 0.4 * n_amp)
    h += hill
    h += 26 * n_ridge**2 * smoothstep(20, 80, hill)            # crags on the high ground

    # ---- castle mount: flat plateau, steep-ish flanks, moat ditch on top
    cx, cy = CASTLE
    ang = np.arctan2(ys - cy, xs - cx)
    rr = np.hypot(xs - cx, ys - cy) / (1 + 0.06 * np.sin(3 * ang + 1.3) + 0.04 * np.sin(5 * ang))
    profile = 58 + (PLATEAU_Z - 58) * smoothstep(PLATEAU_R + 210, PLATEAU_R, rr)
    h = np.where(rr < PLATEAU_R, PLATEAU_Z, np.maximum(h, profile))
    moat = [w for w in W.waters if w["kind"] == "moat"][0]
    q = np.hypot((xs - moat["cx"]) / moat["rx"], (ys - moat["cy"]) / moat["ry"])
    md = np.abs(q - 1) * (moat["rx"] + moat["ry"]) / 2
    moat["level"] = PLATEAU_Z - 2.5
    h = np.where(md < 11, np.minimum(h, PLATEAU_Z - 6 + 6 * smoothstep(7, 11, md)), h)
    flat = smoothstep(PLATEAU_R + 10, PLATEAU_R - 5, rr).astype(np.float32)

    # ---- settlements: blend toward a heavily smoothed surface (gentle building pads)
    soft = blur(h, 60)
    pads = [(1024, 1080, 262, 196, 1.0), (430, 1070, 260, 110, 0.85), (1760, 1050, 190, 90, 0.85),
            (1000, 1700, 120, 200, 0.85), (560, 820, 125, 98, 1.0), (1300, 880, 80, 40, 1.0),
            (1905, 405, 50, 45, 0.7)]
    for x0, y0, rx, ry, k in pads:
        qq = np.hypot((xs - x0) / rx, (ys - y0) / ry)
        wgt = k * smoothstep(1.35, 1.0, qq)
        h = h * (1 - wgt) + soft * wgt
        flat = np.maximum(flat, wgt)
    for b in W.buildings:                                      # hilltop posts & lodge pads
        if b["type"] in ("watchtower", "tower") and b["district"] == "O":
            qq = np.hypot(xs - b["x"], ys - b["y"])
            top = float(sample(h, b["x"], b["y"]))
            wgt = smoothstep(16, 8, qq)
            h = h * (1 - wgt) + top * wgt
    for p in W.props:
        if p["type"] == "altar_stone":
            qq = np.hypot(xs - p["x"], ys - p["y"])
            top = float(sample(h, p["x"], p["y"]))
            wgt = smoothstep(30, 18, qq)
            h = h * (1 - wgt) + top * wgt

    # ---- water
    soft2 = blur(h, 20)
    river_d = np.full_like(h, np.inf)
    for w in W.waters:
        if w["kind"] not in ("river", "stream"):
            continue
        line = w["line"]
        ground = sample(soft2, line[:, 0], line[:, 1])
        drop = 1.6 if w["kind"] == "river" else 0.9
        level = np.minimum.accumulate(ground - drop)
        level = np.convolve(np.pad(level, 6, mode="edge"), np.ones(13) / 13, mode="valid")
        level = np.minimum.accumulate(level)
        w["levels"] = np.round(level, 2)
        cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(line, axis=0).T))])
        reach = 120 if w["kind"] == "river" else 35
        d, s = polyline_field(line, R, CELL, reach + 5)
        lv = np.interp(s, cum, level).astype(np.float32)
        half = w["width"] / 2
        bank = lv + (1.8 if w["kind"] == "river" else 0.8)
        fp = smoothstep(half + 2, reach, d)
        h = np.where(d < reach, bank + (h - bank) * fp, h)
        depth = 2.6 if w["kind"] == "river" else 1.2
        bed = lv - depth + (depth + 0.8) * (d / (half + 2.5)) ** 2
        h = np.where(d < half + 2.5, np.minimum(h, bed), h)
        if w["kind"] == "river":
            river_d = d
        flat = np.maximum(flat, smoothstep(reach, half, d))
    for w in W.waters:
        if w["kind"] not in ("lake", "pond"):
            continue
        rot = math.radians(w.get("heading", 0))
        dx, dy = xs - w["cx"], ys - w["cy"]
        lx, ly = dx * math.cos(rot) + dy * math.sin(rot), -dx * math.sin(rot) + dy * math.cos(rot)
        qq = np.hypot(lx / w["rx"], ly / w["ry"])
        ring = (qq > 1.15) & (qq < 1.3)
        w["level"] = round(float(h[ring].min()) - (1.0 if w["kind"] == "lake" else 0.4), 2)
        depth = 5.0 if w["kind"] == "lake" else 1.5
        target = w["level"] - depth * (1 - np.minimum(qq, 1) ** 2) - 0.2
        h = np.where(qq < 1.0, np.minimum(h, target), h)
        edge = (qq >= 1.0) & (qq < 1.5)
        h = np.where(edge, np.maximum(h, w["level"] + 0.3 * smoothstep(1.0, 1.2, qq)), h)
        flat = np.maximum(flat, smoothstep(1.6, 1.0, qq))

    # ---- roads graded into the land, except where they cross water
    soft3 = blur(h, 8)
    for r in W.roads:
        if r["kind"] == "path":
            continue
        half = r["width"] / 2
        d, _ = polyline_field(r["line"], R, CELL, half + 18)
        wgt = smoothstep(half + 14, half + 1, d) * 0.9 * smoothstep(20, 45, river_d)
        h = h * (1 - wgt) + soft3 * wgt
        flat = np.maximum(flat, wgt)

    # ---- quarry pit
    for p in W.pits:
        qq = np.hypot((xs - p["x"]) / p["rx"], (ys - p["y"]) / p["ry"])
        h = h - p["depth"] * smoothstep(1.0, 0.7, qq)

    # ---- to 1 m resolution + fine detail away from flattened ground
    H = resize(h, FINAL)
    detail = (fbm(FINAL, SEED + 7, octaves=4, base=96) - 0.5) * 1.4
    H = H + detail * (1 - resize(flat, FINAL, method=2))
    W.river_dist = resize(np.minimum(river_d, 400), FINAL)
    return H.astype(np.float32)


def slope_deg(H):
    gy, gx = np.gradient(H, WORLD_SIZE / (H.shape[0] - 1))
    return np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32)
