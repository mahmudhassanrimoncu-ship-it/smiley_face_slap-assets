"""Geometry, noise and raster helpers shared by every stage of the build.

Coordinate convention used everywhere ("map coordinates"):
    x = metres east of the west edge   (0 .. 2048)
    y = metres south of the north edge (0 .. 2048)  -> same as reading an image
A building's `heading` is the compass direction its front door faces
(0 = north, 90 = east, clockwise), which is also its rotation in degrees.
"""
import math

import numpy as np
from PIL import Image


# ------------------------------------------------------------------ curves
def _quads(pts, closed):
    n = len(pts)
    get = (lambda i: pts[i % n]) if closed else (lambda i: pts[max(0, min(n - 1, i))])
    for i in range(n if closed else n - 1):
        p0, p1, p2, p3 = get(i - 1), get(i), get(i + 1), get(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        yield p1, c1, c2, p2


def spline(pts, closed=False, step=4.0):
    """Smooth Catmull-Rom curve through `pts`, resampled every `step` metres."""
    raw = []
    for p1, c1, c2, p2 in _quads(pts, closed):
        for j in range(32):
            t = j / 32
            mt = 1 - t
            raw.append((mt**3 * p1[0] + 3 * mt * mt * t * c1[0] + 3 * mt * t * t * c2[0] + t**3 * p2[0],
                        mt**3 * p1[1] + 3 * mt * mt * t * c1[1] + 3 * mt * t * t * c2[1] + t**3 * p2[1]))
    raw.append(tuple(pts[0]) if closed else tuple(pts[-1]))
    return resample(raw, step)


def resample(poly, step):
    p = np.asarray(poly, dtype=np.float64)
    seg = np.hypot(*np.diff(p, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    n = max(2, int(round(cum[-1] / step)) + 1)
    s = np.linspace(0, cum[-1], n)
    return np.stack([np.interp(s, cum, p[:, 0]), np.interp(s, cum, p[:, 1])], axis=1)


def arc(poly):
    return np.concatenate([[0], np.cumsum(np.hypot(*np.diff(poly, axis=0).T))])


def along(poly, step, start=None, end=None):
    """(x, y, tangent_angle_rad, s) every `step` metres along a resampled polyline."""
    cum = arc(poly)
    s0 = step / 2 if start is None else start
    s1 = cum[-1] if end is None else end
    out = []
    for s in np.arange(s0, s1, step):
        i = min(np.searchsorted(cum, s) - 1, len(poly) - 2)
        i = max(i, 0)
        t = (s - cum[i]) / max(cum[i + 1] - cum[i], 1e-9)
        p, q = poly[i], poly[i + 1]
        out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t,
                    math.atan2(q[1] - p[1], q[0] - p[0]), s))
    return out


def point_at(poly, s):
    return along(poly, 1, start=s, end=s + 0.5)[0]


def dist_to(poly, x, y):
    """Distance from point(s) to polyline (vectorised over points)."""
    x = np.atleast_1d(np.asarray(x, dtype=np.float64))[:, None]
    y = np.atleast_1d(np.asarray(y, dtype=np.float64))[:, None]
    p, q = poly[:-1], poly[1:]
    dx, dy = q[:, 0] - p[:, 0], q[:, 1] - p[:, 1]
    L2 = np.maximum(dx * dx + dy * dy, 1e-9)
    t = np.clip(((x - p[:, 0]) * dx + (y - p[:, 1]) * dy) / L2, 0, 1)
    return np.hypot(x - (p[:, 0] + t * dx), y - (p[:, 1] + t * dy)).min(axis=1)


def polyline_field(poly, res, cell, maxd):
    """Distance (m) and along-curve position (m) to `poly` on a res x res grid."""
    d = np.full((res, res), np.inf, np.float32)
    s = np.zeros((res, res), np.float32)
    cum = arc(poly)
    for i in range(len(poly) - 1):
        (x0, y0), (x1, y1) = poly[i], poly[i + 1]
        lo_x = max(int((min(x0, x1) - maxd) / cell), 0)
        hi_x = min(int((max(x0, x1) + maxd) / cell) + 2, res)
        lo_y = max(int((min(y0, y1) - maxd) / cell), 0)
        hi_y = min(int((max(y0, y1) + maxd) / cell) + 2, res)
        if lo_x >= hi_x or lo_y >= hi_y:
            continue
        gx = np.arange(lo_x, hi_x) * cell
        gy = np.arange(lo_y, hi_y) * cell
        X, Y = np.meshgrid(gx, gy)
        dx, dy = x1 - x0, y1 - y0
        L2 = max(dx * dx + dy * dy, 1e-9)
        t = np.clip(((X - x0) * dx + (Y - y0) * dy) / L2, 0, 1)
        dd = np.hypot(X - (x0 + t * dx), Y - (y0 + t * dy)).astype(np.float32)
        sub_d = d[lo_y:hi_y, lo_x:hi_x]
        m = dd < sub_d
        sub_d[m] = dd[m]
        s[lo_y:hi_y, lo_x:hi_x][m] = (cum[i] + t * math.sqrt(L2))[m]
    return d, s


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ rasters
def box_blur(a, r):
    if r < 1:
        return a
    r = int(r)
    out = a.astype(np.float64)
    for axis in (0, 1):
        pad = [(0, 0), (0, 0)]
        pad[axis] = (r + 1, r)
        c = np.cumsum(np.pad(out, pad, mode="edge"), axis=axis)
        if axis == 0:
            out = (c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)
        else:
            out = (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)
    return out.astype(np.float32)


def blur(a, r):
    """Approximate Gaussian blur (three box passes)."""
    for _ in range(3):
        a = box_blur(a, max(1, r // 2))
    return a


def resize(a, res, method=Image.BICUBIC):
    return np.asarray(Image.fromarray(a.astype(np.float32), mode="F").resize((res, res), method))


def fbm(res, seed, octaves=6, base=3, persistence=0.5):
    rng = np.random.default_rng(seed)
    out = np.zeros((res, res), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = base * 2**o + 1
        if n > res:
            break
        out += amp * resize(rng.random((n, n)).astype(np.float32), res)
        tot += amp
        amp *= persistence
    out /= tot
    return (out - out.min()) / (out.max() - out.min())


def sample(grid, x, y, size=2048.0):
    """Bilinear sample of a square grid covering 0..size metres."""
    res = grid.shape[0]
    fx = np.clip(np.asarray(x, dtype=np.float64) / size * (res - 1), 0, res - 1.001)
    fy = np.clip(np.asarray(y, dtype=np.float64) / size * (res - 1), 0, res - 1.001)
    ix, iy = fx.astype(int), fy.astype(int)
    tx, ty = fx - ix, fy - iy
    return (grid[iy, ix] * (1 - tx) * (1 - ty) + grid[iy, ix + 1] * tx * (1 - ty)
            + grid[iy + 1, ix] * (1 - tx) * ty + grid[iy + 1, ix + 1] * tx * ty)


# ------------------------------------------------------------------ rectangles
def rect_corners(x, y, w, d, heading_deg):
    """Corners of a w (along local x) by d (along local y) rectangle rotated by heading."""
    a = math.radians(heading_deg)
    ux, uy = math.cos(a), math.sin(a)          # local x axis on the map
    vx, vy = -math.sin(a), math.cos(a)         # local y axis on the map (towards the back)
    hw, hd = w / 2, d / 2
    return [(x + sx * hw * ux + sy * hd * vx, y + sx * hw * uy + sy * hd * vy)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def rects_overlap(c1, c2):
    """Separating-axis test for two convex quads."""
    for poly in (c1, c2):
        for i in range(4):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % 4]
            nx, ny = y0 - y1, x1 - x0
            p1 = [nx * px + ny * py for px, py in c1]
            p2 = [nx * px + ny * py for px, py in c2]
            if max(p1) <= min(p2) or max(p2) <= min(p1):
                return False
    return True


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            inside = not inside
    return inside


def ellipse_pts(cx, cy, rx, ry, n=64, wobble=0.0, seed=0):
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 2 * math.pi, 3)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        k = 1 + wobble * (0.6 * math.sin(2 * t + ph[0]) + 0.3 * math.sin(3 * t + ph[1]) + 0.15 * math.sin(5 * t + ph[2]))
        pts.append((cx + rx * k * math.cos(t), cy + ry * k * math.sin(t)))
    return pts
