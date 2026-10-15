"""Ground-cover masks, tree placement and elevations for every object."""
import math

import numpy as np
from PIL import Image, ImageDraw

from config import SEED, WORLD_SIZE
from geom import blur, fbm, point_in_poly, rect_corners, sample, smoothstep
from terrain import FINAL, slope_deg

LAYERS = ["grass", "meadow", "farmland", "forest_floor", "rock", "mud", "dirt_road", "cobblestone"]
LAYER_COLORS = {  # used for the preview image and the 3D blockout terrain materials
    "grass": (104, 142, 70), "meadow": (150, 170, 92), "farmland": (128, 100, 64),
    "forest_floor": (62, 84, 44), "rock": (128, 124, 116), "mud": (92, 78, 58),
    "dirt_road": (176, 150, 108), "cobblestone": (150, 146, 138),
}
K = (FINAL - 1) / WORLD_SIZE   # pixels per metre


def _canvas():
    img = Image.new("L", (FINAL, FINAL), 0)
    return img, ImageDraw.Draw(img)


def _px(pts):
    return [(float(x) * K, float(y) * K) for x, y in pts]


def _line(draw, pts, width, val=255):
    p = _px(pts)
    draw.line(p, fill=val, width=max(1, int(round(width * K))), joint="curve")
    r = width * K / 2
    for x, y in (p[0], p[-1]):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=val)


def _arr(img, soften=0):
    a = np.asarray(img, dtype=np.float32) / 255.0
    return blur(a, soften) if soften else a


def build_masks(W, H):
    slope = slope_deg(H)
    W.slope = slope
    masks = {}

    img, d = _canvas()
    for p in W.pastures:
        d.polygon(_px(p["poly"]), fill=255)
    for f in W.fields:
        if f["crop"] in ("fallow", "grazing"):
            d.polygon(_px(f["poly"]), fill=255)
    rv = np.clip(1 - W.river_dist / 80, 0, 1) * 0.7                 # water meadows along the Ash
    masks["meadow"] = np.maximum(_arr(img, 2), rv)

    img, d = _canvas()
    for f in W.fields:
        if f["crop"] not in ("fallow", "grazing", "outline"):
            d.polygon(_px(f["poly"]), fill=255)
    for c in W.crofts:
        d.polygon(_px(c["poly"]), fill=200)
    masks["farmland"] = _arr(img, 1)

    img, d = _canvas()
    for f in W.forests:
        d.polygon(_px(f["poly"]), fill=255)
    for z in W.zones:
        if z["kind"] == "clearing":
            d.ellipse([(z["cx"] - z["rx"]) * K, (z["cy"] - z["ry"]) * K,
                       (z["cx"] + z["rx"]) * K, (z["cy"] + z["ry"]) * K], fill=0)
    W.forest_mask = _arr(img)
    masks["forest_floor"] = _arr(img, 6)

    img, d = _canvas()
    for p in W.pits:
        d.ellipse([(p["x"] - p["rx"] * 1.1) * K, (p["y"] - p["ry"] * 1.1) * K,
                   (p["x"] + p["rx"] * 1.1) * K, (p["y"] + p["ry"] * 1.1) * K], fill=255)
    masks["rock"] = np.maximum(smoothstep(30, 42, slope), _arr(img, 2))
    masks["rock"] = np.maximum(masks["rock"], smoothstep(222, 240, H) * smoothstep(14, 26, slope) * 0.8)

    img, d = _canvas()
    for w in W.waters:
        if w["kind"] in ("river", "stream"):
            _line(d, w["line"], w["width"] + 8)
        else:
            d.polygon(_px(w["line"]), fill=255)
            d.line(_px(list(w["line"]) + [w["line"][0]]), fill=255, width=int(6 * K))
    masks["mud"] = _arr(img, 2)
    if hasattr(W, "sea_mask"):                                  # sea floor and beaches
        from geom import blur as _blur
        shore = _blur(W.sea_mask.astype(np.float32), 8)
        masks["mud"] = np.maximum(masks["mud"], np.clip(shore * 3, 0, 1))

    img, d = _canvas()
    img2, d2 = _canvas()
    for r in W.roads:
        if r["surface"] == "grass":
            continue
        width = r["width"] + (0.5 if r["kind"] != "path" else 0)
        target = d2 if r["surface"] == "cobble" else d
        val = 150 if r["kind"] == "path" else 255
        _line(target, r["line"], width, val)
    for b in W.buildings:                                         # trodden yards round farms
        if b["type"] in ("farmhouse", "sheepfold", "watermill", "tannery", "lodge"):
            c = rect_corners(b["x"], b["y"], b["w"] + 10, b["d"] + 10, b["heading"])
            d.polygon(_px(c), fill=180)
    for z in W.zones:
        if z["kind"] in ("tiltyard",):
            d.ellipse([(z["cx"] - z["rx"]) * K, (z["cy"] - z["ry"]) * K,
                       (z["cx"] + z["rx"]) * K, (z["cy"] + z["ry"]) * K], fill=220)
    masks["dirt_road"] = _arr(img, 1)
    for sq in W.squares:
        x0, y0, x1, y1 = sq["box"]
        (d if sq["kind"] == "fair" else d2).rectangle([x0 * K, y0 * K, x1 * K, y1 * K], fill=255)
    masks["dirt_road"] = _arr(img, 1)
    for poly in W.paved_polys:
        d2.polygon(_px(poly), fill=230)
    for b in W.buildings:                                         # paved yards inside the walls
        if b["district"] not in ("X",):
            c = rect_corners(b["x"], b["y"], b["w"] + 2, b["d"] + 2, b["heading"])
            d2.polygon(_px(c), fill=255)
    masks["cobblestone"] = _arr(img2, 1)

    # composite: later layers paint over earlier ones
    weights = {k: np.zeros((FINAL, FINAL), np.float32) for k in LAYERS}
    weights["grass"][:] = 1
    for layer in ["meadow", "farmland", "forest_floor", "rock", "mud", "dirt_road", "cobblestone"]:
        m = np.clip(masks[layer], 0, 1)
        for k in LAYERS:
            weights[k] *= (1 - m)
        weights[layer] += m
    W.weights = weights
    return weights


def preview_image(weights, H):
    rgb = np.zeros((FINAL, FINAL, 3), np.float32)
    for k, wgt in weights.items():
        rgb += wgt[..., None] * np.array(LAYER_COLORS[k], np.float32)
    gy, gx = np.gradient(H)
    shade = np.clip(0.75 + (-gx * 0.6 - gy * 0.6) / np.sqrt(1 + gx**2 + gy**2) * 1.4, 0.45, 1.25)
    return np.clip(rgb * shade[..., None], 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ trees
def place_trees(W, H):
    rng = np.random.default_rng(SEED)
    occ_img, d = _canvas()
    for poly in W.built_polys:
        d.polygon(_px(poly), fill=255)
    for poly in W.green_polys:
        d.polygon(_px(poly), fill=0)
    for r in W.roads:
        _line(d, r["line"], r["width"] + 6)
    for b in W.buildings:
        d.polygon(_px(rect_corners(b["x"], b["y"], b["w"] + 8, b["d"] + 8, b["heading"])), fill=255)
    for c in W.crofts:
        d.polygon(_px(c["poly"]), fill=255)
    for f in W.fields:
        d.polygon(_px(f["poly"]), fill=255)
    for p in W.pastures:
        d.polygon(_px(p["poly"]), fill=255)
    for w in W.waters:
        if w["kind"] in ("river", "stream"):
            _line(d, w["line"], w["width"] + 10)
        else:
            d.polygon(_px(w["line"]), fill=255)
            d.line(_px(list(w["line"]) + [w["line"][0]]), fill=255, width=int(8 * K))
    for z in W.zones:
        d.ellipse([(z["cx"] - z["rx"]) * K, (z["cy"] - z["ry"]) * K,
                   (z["cx"] + z["rx"]) * K, (z["cy"] + z["ry"]) * K], fill=255)
    for o in W.orchards:
        d.polygon(_px(o["poly"]), fill=255)
    for p in W.props:
        d.ellipse([(p["x"] - 6) * K, (p["y"] - 6) * K, (p["x"] + 6) * K, (p["y"] + 6) * K], fill=255)
    occ = (np.asarray(occ_img) > 0) | getattr(W, "sea_mask", False)
    slope = W.slope
    clumps = fbm(FINAL, SEED + 11, octaves=5, base=12)
    trees = []

    def ok(x, y):
        ix, iy = int(x * K), int(y * K)
        if not (0 <= ix < FINAL and 0 <= iy < FINAL):
            return False
        return not occ[iy, ix] and slope[iy, ix] < 38

    def species_for(z, r):
        if z > 170:
            return "pine" if r < 0.75 else "birch"
        if z > 130:
            return ["pine", "oak", "birch", "beech"][int(r * 4)]
        return ["oak", "oak", "beech", "ash", "birch"][int(r * 5)]

    # forests: jittered grid
    for f in W.forests:
        s = f["spacing"]
        xs = [p[0] for p in f["poly"]]
        ys = [p[1] for p in f["poly"]]
        for gx in np.arange(min(xs), max(xs), s):
            for gy in np.arange(min(ys), max(ys), s):
                x, y = gx + rng.uniform(-s * 0.4, s * 0.4), gy + rng.uniform(-s * 0.4, s * 0.4)
                ix, iy = int(np.clip(x * K, 0, FINAL - 1)), int(np.clip(y * K, 0, FINAL - 1))
                if W.forest_mask[iy, ix] < 0.5 or W.river_dist[iy, ix] < 24 or not ok(x, y):
                    continue
                if clumps[iy, ix] < f.get("glades", 0.25) and rng.random() < 0.6:     # natural glades
                    continue
                z = float(H[iy, ix])
                trees.append((x, y, species_for(z, rng.random()), rng.uniform(10, 22), f["name"]))
    # hanging woods on hill slopes
    for gx in np.arange(0, WORLD_SIZE, 13.0):
        for gy in np.arange(0, WORLD_SIZE, 13.0):
            x, y = gx + rng.uniform(-5, 5), gy + rng.uniform(-5, 5)
            ix, iy = int(min(x * K, FINAL - 1)), int(min(y * K, FINAL - 1))
            if W.forest_mask[iy, ix] > 0.1:
                continue
            z, sl = float(H[iy, ix]), float(slope[iy, ix])
            p = 0.55 * smoothstep(105, 135, z) * smoothstep(6, 14, sl) * smoothstep(0.5, 0.7, clumps[iy, ix])
            if rng.random() < p and ok(x, y):
                trees.append((x, y, species_for(z, rng.random()), rng.uniform(8, 18), "hillside"))
    # alders & willows along the water
    for w in W.waters:
        if w["kind"] not in ("river", "stream"):
            continue
        line = w["line"]
        for i in range(0, len(line) - 1, 6):
            (x0, y0), (x1, y1) = line[i], line[i + 1]
            a = math.atan2(y1 - y0, x1 - x0)
            for side in (-1, 1):
                if rng.random() > 0.38:
                    continue
                off = w["width"] / 2 + rng.uniform(6, 11)
                x, y = x0 - side * off * math.sin(a), y0 + side * off * math.cos(a)
                if ok(x, y):
                    trees.append((x, y, rng.choice(["willow", "alder"]), rng.uniform(7, 12), "waterside"))
    # hedgerow trees along the country roads
    for r in W.roads:
        if r["kind"] not in ("road", "lane", "track"):
            continue
        line = r["line"]
        for i in range(4, len(line) - 1, 9):
            (x0, y0), (x1, y1) = line[i], line[i + 1]
            a = math.atan2(y1 - y0, x1 - x0)
            for side in (-1, 1):
                if rng.random() > 0.22:
                    continue
                off = r["width"] / 2 + 4.5
                x, y = x0 - side * off * math.sin(a), y0 + side * off * math.cos(a)
                if ok(x, y):
                    trees.append((x, y, rng.choice(["oak", "ash", "hawthorn"]), rng.uniform(6, 13), "hedgerow"))
    # orchards on a neat grid
    for o in W.orchards:
        xs = [p[0] for p in o["poly"]]
        ys = [p[1] for p in o["poly"]]
        for gx in np.arange(min(xs) + 4, max(xs) - 2, o["spacing"]):
            for gy in np.arange(min(ys) + 4, max(ys) - 2, o["spacing"]):
                if point_in_poly(gx, gy, o["poly"]):
                    trees.append((gx, gy, rng.choice(["apple", "apple", "pear", "plum"]), rng.uniform(4, 5.5), o["name"]))
    for x, y, sp, h in getattr(W, "groves", []):                 # hand-placed yews, limes and avenues
        trees.append((x, y, sp, h, "planted"))
    W.trees = [dict(x=round(float(x), 2), y=round(float(y), 2), species=s, height=round(float(h), 1), group=g)
               for x, y, s, h, g in trees]


# ------------------------------------------------------------------ elevations
def attach_heights(W, H):
    for b in W.buildings:
        if b["shape"] == "round":
            pts = [(b["x"] + b["w"] / 2 * math.cos(t), b["y"] + b["w"] / 2 * math.sin(t))
                   for t in np.linspace(0, 2 * math.pi, 9)]
        else:
            pts = rect_corners(b["x"], b["y"], b["w"], b["d"], b["heading"]) + [(b["x"], b["y"])]
        g = sample(H, [p[0] for p in pts], [p[1] for p in pts])
        b["z"] = round(float(g.min()) - 0.3, 2)            # floor level: lowest corner, slightly sunk
        b["ground_max"] = round(float(g.max()), 2)
        if b.get("on_bridge"):                              # houses and mills standing on a bridge deck
            deck = next(br["deck_z"] for br in W.bridges if br["name"] == b["on_bridge"])
            b["z"] = b["ground_max"] = round(deck, 2)
    for p in W.props:
        p["z"] = round(float(sample(H, p["x"], p["y"])) + p.get("lift", 0), 2)
        if p.get("on_bridge"):
            br = next(br for br in W.bridges if br["name"] == p["on_bridge"])
            p["z"] = round(br["water_z"] + 1.5, 2)
    for w in W.walls:
        zs = []
        for s in w["segments"]:
            g = sample(H, [s[0], s[2], (s[0] + s[2]) / 2], [s[1], s[3], (s[1] + s[3]) / 2])
            zs.append([round(float(g.min()) - 0.5, 2), round(float(g.max()), 2)])
        w["z"] = zs
    for t in W.trees:
        t["z"] = round(float(sample(H, t["x"], t["y"])), 2)
    for r in W.roads:
        r["z"] = np.round(sample(H, r["line"][:, 0], r["line"][:, 1]), 2)


def _bridge_heights(W, H, br, w):
    ang = br["heading"]
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    x, y, length = br["x"], br["y"], br["length"]
    gz = sample(H, [x - ca * length / 2, x + ca * length / 2], [y - sa * length / 2, y + sa * length / 2])
    j = int(np.argmin(np.hypot(w["line"][:, 0] - x, w["line"][:, 1] - y)))
    level = float(w["levels"][j])
    deck = max(float(gz.max()) + 0.2, level + (5.5 if w["kind"] == "river" else 1.2))
    far = length / 2 + 9
    end_z = sample(H, [x - ca * far, x + ca * far], [y - sa * far, y + sa * far])
    br.update(deck_z=round(deck, 2), water_z=round(level, 2), end_z=[round(float(e), 2) for e in end_z])


def find_bridges(W, H):
    """The named bridges of the layout, plus a small bridge wherever any other road meets water."""
    from geom import dist_to
    river = [w for w in W.waters if w["kind"] == "river"][0]
    for br in getattr(W, "explicit_bridges", []):
        _bridge_heights(W, H, br, river)
        W.bridges.append(br)
    for r in W.roads:
        if r["kind"] in ("avenue", "path"):
            continue
        for w in W.waters:
            if w["kind"] not in ("river", "stream"):
                continue
            dd = dist_to(w["line"], r["line"][:, 0], r["line"][:, 1])
            hit = dd < w["width"] / 2 + 1
            if not hit.any():
                continue
            idx = np.where(hit)[0]
            groups = np.split(idx, np.where(np.diff(idx) > 3)[0] + 1)
            for g in groups:
                i = int(g[len(g) // 2])
                x, y = r["line"][i]
                if any(math.hypot(x - b["x"], y - b["y"]) < 70 for b in W.bridges):
                    continue
                i0, i1 = max(i - 2, 0), min(i + 2, len(r["line"]) - 1)
                (x0, y0), (x1, y1) = r["line"][i0], r["line"][i1]
                ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
                br = dict(name="Brook bridge" if w["kind"] == "stream" else "River bridge", road=r["name"],
                          x=round(float(x), 2), y=round(float(y), 2), heading=round(ang % 360, 1),
                          length=round(w["width"] + (14 if w["kind"] == "river" else 6), 1),
                          width=r["width"] + 1.5, material="stone" if r["kind"] == "street" else "timber",
                          arches=1 if r["kind"] == "street" else 0)
                _bridge_heights(W, H, br, w)
                W.bridges.append(br)
