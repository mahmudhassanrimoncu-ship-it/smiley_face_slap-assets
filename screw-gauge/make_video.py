#!/usr/bin/env python3
"""Render the narrated explainer "How to Measure with a Screw Gauge".

Every frame is drawn procedurally with Pillow (2x supersampled), narration is
synthesised with Piper TTS, and ffmpeg muxes both into an MP4.

    pip install pillow numpy piper-tts
    # voice: en_US-lessac-medium.onnx (+ .json) from huggingface.co/rhasspy/piper-voices
    PIPER_VOICE=/path/to/en_US-lessac-medium.onnx python3 screw-gauge/make_video.py

Options:  --preview N   render only every Nth second as PNG stills into build/preview
          --scene K     with --preview, only scene K (1-based)
"""
import hashlib
import math
import os
import subprocess
import sys
import wave
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, SS, FPS = 1920, 1080, 2, 30
ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, 'build')
OUT = os.path.join(ROOT, '..', 'video', 'how-to-use-a-screw-gauge.mp4')
VOICE = os.environ.get('PIPER_VOICE', os.path.expanduser('~/voices/en_US-lessac-medium.onnx'))
FONT_DIR = '/usr/share/fonts/opentype/inter'

# ---------------------------------------------------------------- palette
# Same light palette as the refrigerator explainer (src/theme.ts).
BG = '#f4f7fb'
INK = '#14213d'
MUTED = '#5c6b82'
CARD = '#ffffff'
LINE = '#d9e2ef'
BLUE = '#1c7ed6'
BLUE_D = '#1864ab'
BLUE_T = '#e7f1fc'
RED = '#e03131'
RED_T = '#fdecec'
ORANGE = '#f76707'
AMBER = '#f2b705'
GREEN = '#2f9e44'
GREEN_T = '#e9f7ec'
FRAME = '#3b4f73'
STEEL = '#b9c3cf'
CHROME = '#d6dde6'
COPPER = '#c8742c'
HL = '#f59f00'


def rgb(c):
    if isinstance(c, tuple):
        return c
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, k):
    a, b = rgb(a), rgb(b)
    k = max(0.0, min(1.0, k))
    return tuple(int(round(a[i] + (b[i] - a[i]) * k)) for i in range(3))


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def seg(t, a, b):
    """Eased 0..1 progress of t between a and b."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return ease((t - a) / (b - a))


def lerp(a, b, k):
    return a + (b - a) * k


@lru_cache(maxsize=None)
def font(size, wt='m'):
    name = {'r': 'Regular', 'm': 'Medium', 'sb': 'SemiBold', 'b': 'Bold', 'xb': 'ExtraBold'}[wt]
    return ImageFont.truetype(os.path.join(FONT_DIR, f'Inter-{name}.otf'), max(1, int(round(size * SS))))


@lru_cache(maxsize=256)
def shade_strip(n, base, spec=0.55):
    """Vertical colour profile of a horizontal metal cylinder (n px tall)."""
    t = np.linspace(0, 1, max(n, 1))
    k = 0.72 + 0.30 * np.cos((t - 0.33) * math.pi * 1.1)
    hi = np.exp(-((t - 0.27) / 0.07) ** 2) * spec
    b = np.array(rgb(base), dtype=float)
    col = b[None, :] * k[:, None]
    col = col + (255 - col) * hi[:, None]
    return Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)[:, None, :])


class Cv:
    """Drawing surface in 1080p coordinates, rendered at SS x resolution."""

    def __init__(self, w=W, h=H, bg=BG):
        self.w, self.h, self.bg = w, h, rgb(bg)
        self.im = Image.new('RGB', (int(w * SS), int(h * SS)), self.bg)
        self.d = ImageDraw.Draw(self.im)

    def c(self, col, a=1.0):
        return rgb(col) if a >= 1 else mix(self.bg, col, a)

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, w=1, r=0, a=1.0):
        if a <= 0:
            return
        box = [x0 * SS, y0 * SS, x1 * SS, y1 * SS]
        if box[2] < box[0]:
            box[0], box[2] = box[2], box[0]
        if box[3] < box[1]:
            box[1], box[3] = box[3], box[1]
        kw = dict(fill=self.c(fill, a) if fill else None,
                  outline=self.c(outline, a) if outline else None, width=max(1, int(w * SS)))
        if r > 0:
            self.d.rounded_rectangle(box, radius=min(r * SS, (box[2] - box[0]) / 2, (box[3] - box[1]) / 2), **kw)
        else:
            self.d.rectangle(box, **kw)

    def line(self, pts, col, w=2, a=1.0):
        if a <= 0:
            return
        self.d.line([(x * SS, y * SS) for x, y in pts], fill=self.c(col, a), width=max(1, int(round(w * SS))), joint='curve')

    def circle(self, x, y, r, fill=None, outline=None, w=1, a=1.0):
        if a <= 0 or r <= 0:
            return
        self.d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS],
                       fill=self.c(fill, a) if fill else None,
                       outline=self.c(outline, a) if outline else None, width=max(1, int(w * SS)))

    def poly(self, pts, fill=None, outline=None, w=1, a=1.0):
        if a <= 0:
            return
        p = [(x * SS, y * SS) for x, y in pts]
        self.d.polygon(p, fill=self.c(fill, a) if fill else None)
        if outline:
            self.d.line(p + [p[0]], fill=self.c(outline, a), width=max(1, int(w * SS)), joint='curve')

    def text(self, x, y, s, size=32, col=INK, wt='m', anchor='la', a=1.0):
        if a <= 0 or not s:
            return
        self.d.text((x * SS, y * SS), s, font=font(size, wt), fill=self.c(col, a), anchor=anchor)

    def tw(self, s, size=32, wt='m'):
        return self.d.textlength(s, font=font(size, wt)) / SS

    def arrow(self, x0, y0, x1, y1, col, w=4, head=16, a=1.0, both=False):
        if a <= 0:
            return
        self.line([(x0, y0), (x1, y1)], col, w, a)
        for (ax, ay, bx, by) in ([(x0, y0, x1, y1), (x1, y1, x0, y0)] if both else [(x0, y0, x1, y1)]):
            ang = math.atan2(by - ay, bx - ax)
            p1 = (bx - head * math.cos(ang - 0.45), by - head * math.sin(ang - 0.45))
            p2 = (bx - head * math.cos(ang + 0.45), by - head * math.sin(ang + 0.45))
            self.poly([(bx, by), p1, p2], fill=col, a=a)

    def cyl(self, x0, x1, y0, y1, base, spec=0.55):
        if x1 < x0:
            x0, x1 = x1, x0
        X0, X1, Y0, Y1 = (int(round(v * SS)) for v in (x0, x1, y0, y1))
        if X1 - X0 < 1 or Y1 - Y0 < 1:
            return
        strip = shade_strip(Y1 - Y0, rgb(base), spec).resize((X1 - X0, Y1 - Y0), Image.NEAREST)
        self.im.paste(strip, (X0, Y0))

    def vcyl(self, x0, x1, y0, y1, base, spec=0.55):
        X0, X1, Y0, Y1 = (int(round(v * SS)) for v in (x0, x1, y0, y1))
        if X1 - X0 < 1 or Y1 - Y0 < 1:
            return
        strip = shade_strip(X1 - X0, rgb(base), spec).transpose(Image.TRANSPOSE)
        self.im.paste(strip.resize((X1 - X0, Y1 - Y0), Image.NEAREST), (X0, Y0))

    def veil(self, a, col=BG):
        if a > 0:
            self.im = Image.blend(self.im, Image.new('RGB', self.im.size, rgb(col)), clamp(a))
            self.d = ImageDraw.Draw(self.im)

    def paste(self, sub, x, y, r=18, a=1.0, border=LINE):
        if a <= 0:
            return
        mask = Image.new('L', sub.im.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, sub.im.size[0] - 1, sub.im.size[1] - 1], radius=r * SS,
                                               fill=int(255 * clamp(a)))
        self.im.paste(sub.im, (int(x * SS), int(y * SS)), mask)
        self.rect(x, y, x + sub.w, y + sub.h, outline=border, w=2, r=r, a=a)

    def frame_bytes(self):
        return self.im.resize((W, H), Image.LANCZOS).tobytes()


# ---------------------------------------------------------------- the screw gauge
# World units are millimetres.  x grows to the right, y grows downwards, the
# spindle axis is y = 0 and the anvil face is x = 0.
XS0 = 31.0          # main-scale zero on the sleeve
R_SLEEVE = 3.6
R_THIMBLE = 5.0
TH_LEN = 13.0
R_RATCHET = 3.1
RAT_LEN = 5.5


def view(cu, cv_, s, cx=960, cy=540):
    return (cu, cv_, s, cx, cy)


def lerp_view(a, b, k):
    s = math.exp(lerp(math.log(a[2]), math.log(b[2]), k))
    # keep the world point under the screen centre moving smoothly in screen space
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k), s, lerp(a[3], b[3], k), lerp(a[4], b[4], k))


def mapper(V):
    cu, cv_, s, cx, cy = V
    return (lambda u: cx + (u - cu) * s), (lambda v: cy + (v - cv_) * s), s


def full_view(r, s=17, cx=960, cy=555):
    cu = (XS0 + r + RAT_LEN + TH_LEN - 9) / 2
    return view(cu, 7.75, s, cx, cy)


def div_angle(d, c):
    """Angle (rad) of circular-scale division d from the reference line when c is on it."""
    return ((d - c + 25) % 50 - 25) / 50 * 2 * math.pi


def part_col(base, hl, key):
    h = hl.get(key, 0)
    return mix(base, HL, 0.55 * h) if h else rgb(base)


def draw_gauge(cv, V, reading, z=0.0, obj=None, hl=None, lock=0.0, numbers=True):
    """Draw the micrometer.

    reading: what the scales show (mm).  z: zero error, so the real gap is reading - z.
    obj: None | ('wire', diameter, dy) | ('sheet', thickness, dy)
    hl:  {part: 0..1} highlight strength.
    """
    hl = hl or {}
    X, Y, s = mapper(V)
    gap = max(0.0, reading - z)
    xe = XS0 + reading               # thimble edge
    c = reading * 100.0              # circular-scale division on the reference line
    phi = reading / 0.5 * 2 * math.pi
    lw = max(1.0, 0.12 * s)

    # frame: C-shaped bow + two bosses
    fcol = mix(FRAME, '#6f93d6', 0.7 * hl.get('frame', 0))
    outer = [(10 + 19 * math.cos(a), 2 + 24 * math.sin(a)) for a in np.linspace(math.pi, 0, 60)]
    inner = [(10 + 13 * math.cos(a), 2 + 17 * math.sin(a)) for a in np.linspace(0, math.pi, 60)]
    cv.poly([(X(u), Y(v)) for u, v in outer + inner], fill=fcol)
    cv.line([(X(u), Y(v)) for u, v in inner[3:-3]], mix(fcol, '#ffffff', 0.25), max(1, 0.25 * s))
    cv.rect(X(-9), Y(-5.5), X(-3), Y(5.5), fill=fcol, r=0.8 * s)
    cv.rect(X(17), Y(-6.5), X(29), Y(6.5), fill=fcol, r=0.8 * s)
    if hl.get('frame'):
        cv.poly([(X(u), Y(v)) for u, v in outer + inner], outline=HL, w=max(2, 0.3 * s), a=hl['frame'])
    if numbers and s >= 6:
        cv.text(X(10), Y(22.3), '0–15 mm   LC 0.01 mm', 1.25 * s, '#e3e9f2', 'sb', 'mm')

    # lock nut on top of the right boss
    lc = part_col('#55657f', hl, 'lock')
    cv.rect(X(20.3), Y(-8.3), X(24.7), Y(-6.3), fill=lc, r=0.3 * s)
    ang = math.radians(lerp(-55, -125, lock))
    cv.line([(X(22.5), Y(-8)), (X(22.5 + 3.4 * math.cos(ang)), Y(-8 + 3.4 * math.sin(ang)))], lc, max(2, 0.9 * s))
    cv.circle(X(22.5 + 3.4 * math.cos(ang)), Y(-8 + 3.4 * math.sin(ang)), 0.75 * s, fill=lc)
    if hl.get('lock'):
        cv.rect(X(19.8), Y(-12.5), X(25.2), Y(-5.8), outline=HL, w=max(2, 0.25 * s), r=0.6 * s, a=hl['lock'])

    # anvil and spindle
    cv.cyl(X(-3), X(0), Y(-2.6), Y(2.6), part_col(STEEL, hl, 'anvil'))
    cv.line([(X(0), Y(-2.6)), (X(0), Y(2.6))], '#6d7a8c', lw)
    cv.cyl(X(gap), X(17), Y(-2.6), Y(2.6), part_col(STEEL, hl, 'spindle'))
    cv.line([(X(gap), Y(-2.6)), (X(gap), Y(2.6))], '#6d7a8c', lw)
    for key, x0, x1 in (('anvil', -3, 0), ('spindle', gap, 17)):
        if hl.get(key):
            cv.rect(X(x0), Y(-2.6), X(x1), Y(2.6), outline=HL, w=max(2, 0.3 * s), a=hl[key])

    # object between the jaws
    if obj:
        kind, size, dy = obj
        if kind == 'wire':
            cv.vcyl(X(0), X(size), Y(dy - 9), Y(dy + 9), COPPER)
        else:
            cv.rect(X(0), Y(dy - 10), X(size), Y(dy + 13), fill='#9fb0c4', outline='#5f738c', w=max(1, 0.1 * s))

    # sleeve with main scale
    cv.cyl(X(29), X(XS0 + 16), Y(-R_SLEEVE), Y(R_SLEEVE), part_col(CHROME, hl, 'sleeve'))
    ink = '#1d2433'
    cv.line([(X(XS0 - 0.6), Y(0)), (X(XS0 + 16), Y(0))], ink, lw)
    for i in range(16):
        L = 1.9 if i % 5 == 0 else 1.25
        cv.line([(X(XS0 + i), Y(0)), (X(XS0 + i), Y(-L))], ink, lw)
        cv.line([(X(XS0 + i + 0.5), Y(0)), (X(XS0 + i + 0.5), Y(1.25))], ink, lw)
        if i % 5 == 0 and numbers:
            cv.text(X(XS0 + i), Y(-2.35), str(i), 1.15 * s, ink, 'sb', 'ms')
    cv.line([(X(XS0), Y(0)), (X(XS0), Y(1.6))], ink, lw)
    if hl.get('sleeve'):
        cv.rect(X(29), Y(-R_SLEEVE), X(XS0 + 16), Y(R_SLEEVE), outline=HL, w=max(2, 0.25 * s), a=hl['sleeve'])

    # thimble with circular scale
    tcol = part_col(CHROME, hl, 'thimble')
    cv.cyl(X(xe), X(xe + TH_LEN), Y(-R_THIMBLE), Y(R_THIMBLE), tcol)
    shade = mix(tcol, '#000000', 0.35)
    for k in range(40):                                      # knurled grip
        th = ((k / 40 * 2 * math.pi - phi + math.pi) % (2 * math.pi)) - math.pi
        if abs(th) < 1.4:
            y = -R_THIMBLE * math.sin(th)
            cv.line([(X(xe + 6.8), Y(y)), (X(xe + TH_LEN - 0.4), Y(y))], shade, max(1, 0.18 * s * math.cos(th)))
    cv.line([(X(xe + 6.5), Y(-R_THIMBLE)), (X(xe + 6.5), Y(R_THIMBLE))], shade, lw)
    for d in range(50):
        th = div_angle(d, c)
        if abs(th) > 1.42:
            continue
        y = -R_THIMBLE * math.sin(th)
        fade = clamp(math.cos(th) * 2.0)
        col = mix(tcol, ink, fade)
        L = 1.6 if d % 5 == 0 else 1.0
        cv.line([(X(xe), Y(y)), (X(xe + L), Y(y))], col, lw * (0.6 + 0.4 * math.cos(th)))
        if d % 5 == 0 and numbers and abs(th) < 1.25:
            cv.text(X(xe + 1.95), Y(y), str(d), 0.95 * s * (0.55 + 0.45 * math.cos(th)), col, 'sb', 'lm')
    cv.line([(X(xe), Y(-R_THIMBLE)), (X(xe), Y(R_THIMBLE))], '#4b5566', lw * 1.3)
    if hl.get('thimble'):
        cv.rect(X(xe), Y(-R_THIMBLE), X(xe + TH_LEN), Y(R_THIMBLE), outline=HL, w=max(2, 0.25 * s), a=hl['thimble'])

    # ratchet
    rx0, rx1 = xe + TH_LEN, xe + TH_LEN + RAT_LEN
    rcol = part_col('#a9b4c2', hl, 'ratchet')
    cv.cyl(X(rx0), X(rx1), Y(-R_RATCHET), Y(R_RATCHET), rcol)
    for k in range(24):
        th = ((k / 24 * 2 * math.pi - phi + math.pi) % (2 * math.pi)) - math.pi
        if abs(th) < 1.4:
            y = -R_RATCHET * math.sin(th)
            cv.line([(X(rx0 + 0.5), Y(y)), (X(rx1 - 0.3), Y(y))], mix(rcol, '#000000', 0.4), max(1, 0.15 * s))
    cv.rect(X(rx1 - 0.2), Y(-R_RATCHET * 0.8), X(rx1 + 0.6), Y(R_RATCHET * 0.8), fill=mix(rcol, '#000000', 0.25), r=0.4 * s)
    if hl.get('ratchet'):
        cv.rect(X(rx0), Y(-R_RATCHET), X(rx1 + 0.6), Y(R_RATCHET), outline=HL, w=max(2, 0.25 * s), a=hl['ratchet'])
    return X, Y, s


def mark_main(cv, V, u, below=False, col=ORANGE, a=1.0):
    """Re-draw one main-scale mark thick and coloured."""
    X, Y, s = mapper(V)
    L = 1.25 if below else (1.9 if round(u) % 5 == 0 else 1.25)
    y1 = 1.25 if below else -L
    cv.line([(X(XS0 + u), Y(0)), (X(XS0 + u), Y(y1))], col, max(3, 0.3 * s), a)


def mark_div(cv, V, reading, d, col=ORANGE, a=1.0, ring=True):
    """Highlight circular-scale division d."""
    X, Y, s = mapper(V)
    xe = XS0 + reading
    th = div_angle(d, reading * 100)
    if abs(th) > 1.3:
        return
    y = -R_THIMBLE * math.sin(th)
    L = 1.6 if d % 5 == 0 else 1.0
    cv.line([(X(xe), Y(y)), (X(xe + L), Y(y))], col, max(3, 0.28 * s), a)
    if ring:
        cv.circle(X(xe + L + 0.45), Y(y), 0.42 * s, outline=col, w=max(2, 0.1 * s), a=a)


def index_line(cv, V, reading, col=BLUE, a=1.0):
    X, Y, s = mapper(V)
    cv.line([(X(XS0 - 0.6), Y(0)), (X(XS0 + reading), Y(0))], col, max(3, 0.18 * s), a)


# ---------------------------------------------------------------- UI pieces
def card(cv, x0, y0, x1, y1, a=1.0, fill=CARD, outline=LINE, r=22):
    if a <= 0:
        return
    cv.rect(x0 + 4, y0 + 8, x1 + 4, y1 + 8, fill=mix(BG, '#9aa8bd', 0.35), r=r, a=a)
    cv.rect(x0, y0, x1, y1, fill=fill, outline=outline, w=2, r=r, a=a)


def pill(cv, x, y, s, size=28, fill=INK, col='#ffffff', a=1.0, anchor='mid', wt='sb'):
    w = cv.tw(s, size, wt) + size * 1.1
    h = size * 1.75
    x0 = x - w / 2 if anchor == 'mid' else x
    cv.rect(x0, y - h / 2, x0 + w, y + h / 2, fill=fill, r=h / 2, a=a)
    cv.text(x0 + w / 2, y, s, size, col, wt, 'mm', a)
    return x0, x0 + w


def callout(cv, ax, ay, lx, ly, s, col=INK, a=1.0, size=28):
    if a <= 0:
        return
    cv.line([(ax, ay), (lx, ly)], col, 2.5, a)
    cv.circle(ax, ay, 7, fill=col, a=a)
    cv.circle(ax, ay, 7, outline='#ffffff', w=2, a=a)
    pill(cv, lx, ly, s, size, fill=col, a=a)


def check(cv, x, y, sz, col=GREEN, a=1.0):
    cv.circle(x, y, sz, fill=col, a=a)
    cv.line([(x - sz * 0.45, y + sz * 0.02), (x - sz * 0.1, y + sz * 0.35), (x + sz * 0.48, y - sz * 0.32)],
            '#ffffff', sz * 0.22, a)


def clicks(cv, x, y, t, t0, t1, n=3):
    """'click!' bubbles popping between t0 and t1."""
    for i in range(n):
        tc = lerp(t0, t1, (i + 0.5) / n)
        k = (t - tc) / 0.7
        if 0 <= k <= 1:
            a = 1 - k
            pill(cv, x + 40 * (i % 2) - 20, y - 50 * k - 30 * i % 60, 'click!', 24, fill=ORANGE, a=a)


def wrap(cv, s, size, maxw, wt='m'):
    words, lines, cur = s.split(), [], ''
    for wd in words:
        nxt = (cur + ' ' + wd).strip()
        if cv.tw(nxt, size, wt) > maxw and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = nxt
    if cur:
        lines.append(cur)
    return lines


def para(cv, x, y, s, size, maxw, col=INK, wt='m', a=1.0, lh=1.35, anchor='la'):
    lines = wrap(cv, s, size, maxw, wt)
    for i, ln in enumerate(lines):
        if anchor == 'ma':
            cv.text(x, y + i * size * lh, ln, size, col, wt, 'ma', a)
        else:
            cv.text(x, y + i * size * lh, ln, size, col, wt, 'la', a)
    return y + len(lines) * size * lh


def step_pill(cv, n, s, a=1.0):
    x0, x1 = pill(cv, 60, 160, f'Step {n}', 26, fill=BLUE, a=a, anchor='left')
    cv.text(x1 + 18, 160, s, 30, INK, 'sb', 'lm', a)


def rows_card(cv, x0, y0, x1, rows, t, a=1.0, title=None, size=34):
    """rows: list of (appear_time, label, value, colour)."""
    y1 = y0 + 40 + (70 if title else 0) + 78 * len(rows)
    card(cv, x0, y0, x1, y1, a)
    y = y0 + 34
    if title:
        cv.text(x0 + 34, y + 10, title, 30, MUTED, 'sb', 'lm', a)
        y += 70
    for (ta, lab, val, col) in rows:
        k = seg(t, ta, ta + 0.5) * a
        if k <= 0:
            continue
        cv.text(x0 + 34, y + 20, lab, size * 0.8, MUTED, 'm', 'lm', k)
        cv.text(x1 - 34, y + 20, val, size, col, 'b', 'rm', k)
        y += 78
    return y1


# ---------------------------------------------------------------- scenes
class Beat:
    def __init__(self, say, draw, cap=None, extra=0.0, header=True):
        self.say, self.draw, self.cap, self.extra, self.header = say, draw, cap or say, extra, header


SCENES = []


def scene(title):
    sc = {'title': title, 'beats': []}
    SCENES.append(sc)
    return sc['beats']


# 1 · Introduction -----------------------------------------------------------
b = scene('Introduction')


def intro_title(cv, t, T):
    a = seg(t, 0, 0.8)
    cv.text(960, 175, 'How to Measure with a', 58, INK, 'b', 'mm', a)
    cv.text(960, 260, 'Screw Gauge', 104, BLUE_D, 'xb', 'mm', a)
    cv.text(960, 340, 'Parts  ·  Least count  ·  Zero error  ·  Taking a reading', 30, MUTED, 'm', 'mm', seg(t, 0.6, 1.4))
    r = 1.0 + 4.0 * seg(t, 1.0, T)
    draw_gauge(cv, full_view(3, 14, 960, 690), r, obj=None)


b.append(Beat("Welcome! In this lesson, you will learn how to measure very small lengths accurately, "
              "using a screw gauge, which is also called a micrometer screw gauge.",
              intro_title, header=False, extra=0.6))


def ruler_icon(cv, x, y, a):
    cv.rect(x - 150, y - 28, x + 150, y + 28, fill='#f3d27a', outline='#b38b1d', w=2, r=4, a=a)
    for i in range(31):
        L = 22 if i % 10 == 0 else (15 if i % 5 == 0 else 9)
        cv.line([(x - 140 + i * 9.33, y - 28), (x - 140 + i * 9.33, y - 28 + L)], '#5b4710', 2, a)


def vernier_icon(cv, x, y, a):
    cv.rect(x - 160, y - 30, x + 160, y - 4, fill='#c3ccd8', outline='#6d7a8c', w=2, a=a)
    cv.poly([(x - 160, y - 30), (x - 128, y - 30), (x - 128, y + 48), (x - 145, y + 34), (x - 160, y - 4)],
            fill='#9aa6b6', a=a)
    cv.rect(x - 70, y - 38, x + 10, y + 4, fill='#8796aa', outline='#5d6b80', w=2, r=4, a=a)
    cv.poly([(x - 100, y + 4), (x - 70, y + 4), (x - 70, y + 48), (x - 85, y + 34)], fill='#8796aa', a=a)
    for i in range(24):
        cv.line([(x - 120 + i * 11, y - 30), (x - 120 + i * 11, y - 22 if i % 5 else y - 16)], '#2b313b', 1.5, a)


def intro_compare(cv, t, T):
    items = [('Metre rule', '1 mm', ruler_icon), ('Vernier caliper', '0.1 mm', vernier_icon),
             ('Screw gauge', '0.01 mm', None)]
    for i, (name, acc, icon) in enumerate(items):
        a = seg(t, 0.3 + i * 0.22 * T, 0.8 + i * 0.22 * T)
        x = 400 + i * 560
        best = i == 2
        card(cv, x - 250, 150, x + 250, 520, a, fill=BLUE_T if best else CARD, outline=BLUE if best else LINE)
        cv.text(x, 200, name, 34, INK, 'b', 'mm', a)
        if icon:
            icon(cv, x, 320, a)
        elif a > 0.5:
            draw_gauge(cv, view(23, 7.75, 5.6, x, 318), 3.0, numbers=False)
        cv.text(x, 440, 'measures to', 24, MUTED, 'm', 'mm', a)
        cv.text(x, 482, acc, 44 if best else 38, BLUE_D if best else INK, 'xb', 'mm', a)
    a2 = seg(t, 0.68 * T, 0.68 * T + 0.6)
    cv.text(960, 585, 'Perfect for very small lengths:', 30, MUTED, 'sb', 'mm', a2)
    ex = [('diameter of a thin wire', 'wire'), ('thickness of a sheet', 'sheet'), ('diameter of a small ball', 'ball')]
    for i, (lab, kind) in enumerate(ex):
        a = seg(t, 0.7 * T + i * 0.5, 0.7 * T + i * 0.5 + 0.5)
        x = 400 + i * 560
        card(cv, x - 250, 625, x + 250, 900, a)
        if kind == 'wire':
            pts = [(x - 150 + k * 6, 735 + 28 * math.sin(k / 8)) for k in range(51)]
            cv.line(pts, COPPER, 10, a)
        elif kind == 'sheet':
            cv.poly([(x - 140, 760), (x - 40, 690), (x + 150, 690), (x + 50, 760)], fill='#b9c6d6', outline='#5f738c', w=2, a=a)
            cv.poly([(x - 140, 760), (x + 50, 760), (x + 50, 770), (x - 140, 770)], fill='#7d8fa6', a=a)
            cv.poly([(x + 50, 760), (x + 150, 690), (x + 150, 700), (x + 50, 770)], fill='#6a7c93', a=a)
        else:
            for k in range(10):
                q = k / 9
                cv.circle(x - 12 * q, 730 - 12 * q, 46 * (1 - 0.7 * q), fill=mix('#6d7a8c', '#ffffff', q ** 1.5), a=a)
        cv.text(x, 850, lab, 28, INK, 'sb', 'mm', a)


b.append(Beat("A metre rule can measure to one millimetre. A vernier caliper goes down to one tenth of a millimetre. "
              "But a screw gauge measures to one hundredth of a millimetre. That makes it perfect for the diameter of "
              "a thin wire, the thickness of a sheet of metal or paper, or the diameter of a small ball.",
              intro_compare,
              cap="A metre rule measures to 1 mm. A vernier caliper goes down to 0.1 mm. But a screw gauge measures to "
                  "0.01 mm. That makes it perfect for the diameter of a thin wire, the thickness of a sheet of metal "
                  "or paper, or the diameter of a small ball.", extra=1.0))

# 2 · Parts ---------------------------------------------------------------------
b = scene('Parts of a screw gauge')
FV5 = full_view(5)
LABELS = {
    'frame': ('Frame', lambda X, Y, g, xe: (X(-1.3), Y(16.5)), (300, 780)),
    'anvil': ('Anvil', lambda X, Y, g, xe: (X(-1.5), Y(-2.6)), (330, 250)),
    'spindle': ('Spindle', lambda X, Y, g, xe: (X(g + 5), Y(-2.6)), (690, 215)),
    'lock': ('Lock nut', lambda X, Y, g, xe: (X(22.5), Y(-11)), (1010, 175)),
    'sleeve': ('Sleeve + main scale', lambda X, Y, g, xe: (X(XS0 + 2), Y(3.6)), (1120, 760)),
    'thimble': ('Thimble + circular scale', lambda X, Y, g, xe: (X(xe + 4), Y(-5)), (1400, 215)),
    'ratchet': ('Ratchet', lambda X, Y, g, xe: (X(xe + TH_LEN + 3), Y(3.1)), (1640, 650)),
}


def parts_labels(cv, V, r, alphas):
    X, Y, s = mapper(V)
    for key, a in alphas.items():
        if a > 0:
            name, fn, (lx, ly) = LABELS[key]
            ax, ay = fn(X, Y, r, XS0 + r)
            callout(cv, ax, ay, lx, ly, name, INK if a < 0.99 else BLUE_D, a)


def p_frame(cv, t, T):
    h = seg(t, 0.5, 1.2)
    draw_gauge(cv, FV5, 5, hl={'frame': h * (0.75 + 0.25 * math.sin(t * 5))})
    parts_labels(cv, FV5, 5, {'frame': seg(t, 0.6, 1.2)})
    a = seg(t, 0.55 * T, 0.55 * T + 0.6)
    card(cv, 1210, 860 - 90, 1860, 935, a, fill=RED_T, outline='#f3b5b5')
    cv.text(1240, 852, 'Hold it by the frame — hand heat', 26, '#a61e1e', 'sb', 'lm', a)
    cv.text(1240, 892, 'expands the metal', 26, '#a61e1e', 'sb', 'lm', a)


b.append(Beat("Let's meet the parts. The U shaped metal frame holds everything together. "
              "Always hold the gauge by its frame, so the warmth of your hand doesn't expand the metal.",
              p_frame, cap="Let's meet the parts. The U-shaped metal frame holds everything together. Always hold the "
                           "gauge by its frame, so the warmth of your hand doesn't expand the metal."))


def p_jaws(cv, t, T):
    r = 5 - 2.5 * seg(t, 0.45 * T, 0.62 * T) + 2.5 * seg(t, 0.7 * T, 0.87 * T)
    hl = {'anvil': seg(t, 0.2, 0.8) * (1 - seg(t, 0.33 * T, 0.38 * T)), 'spindle': seg(t, 0.33 * T, 0.38 * T)}
    draw_gauge(cv, FV5, r, hl=hl)
    parts_labels(cv, FV5, r, {'frame': 0.6, 'anvil': seg(t, 0.3, 0.9), 'spindle': seg(t, 0.33 * T, 0.38 * T)})
    X, Y, s = mapper(FV5)
    a = seg(t, 0.85 * T, 0.85 * T + 0.5)
    cv.arrow(X(0) - 2, Y(4.4), X(r - 5 + 5) + 2, Y(4.4), BLUE, 3, 12, a, both=True)
    cv.text((X(0) + X(r)) / 2, Y(4.4) + 26, 'object goes here', 22, BLUE_D, 'sb', 'mm', a)


b.append(Beat("On the left is the anvil, a fixed flat stud. Facing it is the spindle, which moves in and out as you "
              "turn the screw. The object is held between these two flat faces.", p_jaws, extra=0.5))

ZOOM_SLEEVE = view(XS0 + 3.2, 0.6, 64, 960, 540)


def p_sleeve(cv, t, T):
    k = seg(t, 0.1, 1.6)
    V = lerp_view(FV5, ZOOM_SLEEVE, k)
    draw_gauge(cv, V, 5, hl={'sleeve': seg(t, 1.6, 2.2) * (1 - seg(t, 0.5 * T, 0.55 * T))})
    parts_labels(cv, V, 5, {kk: 0.6 * (1 - seg(t, 0, 0.5)) for kk in ('frame', 'anvil', 'spindle')})
    X, Y, s = mapper(V)
    a1 = seg(t, 0.35 * T, 0.35 * T + 0.6)
    a2 = seg(t, 0.62 * T, 0.62 * T + 0.6)
    index_line(cv, V, 5, BLUE, seg(t, 0.25 * T, 0.3 * T))
    pill(cv, X(XS0 - 3.5), Y(0), 'reference line', 24, fill=BLUE, a=seg(t, 0.25 * T, 0.3 * T))
    for i in range(1, 5):
        mark_main(cv, V, i, False, ORANGE, a1)
        mark_main(cv, V, i + 0.5, True, GREEN, a2)
    cv.arrow(X(XS0 + 1), Y(-4.6), X(XS0 + 2), Y(-4.6), ORANGE, 3, 12, a1, both=True)
    pill(cv, X(XS0 + 1.5), Y(-5.6), '1 mm marks (above)', 26, fill=ORANGE, a=a1)
    cv.arrow(X(XS0 + 1.5), Y(4.3), X(XS0 + 2), Y(4.3), GREEN, 3, 12, a2, both=True)
    pill(cv, X(XS0 + 1.75), Y(5.4), 'half-mm marks (below)', 26, fill=GREEN, a=a2)


b.append(Beat("The sleeve, or barrel, carries the main scale along a reference line. Above the line, it is marked "
              "in millimetres. Below the line, the marks fall halfway between, so together they show half millimetres.",
              p_sleeve, extra=0.8))

ZOOM_THIMBLE = view(XS0 + 9.5, 0, 64, 960, 540)


def p_thimble(cv, t, T):
    V = lerp_view(ZOOM_SLEEVE, ZOOM_THIMBLE, seg(t, 0, 1.2))
    r = 5 + 0.5 * seg(t, 0.35 * T, 0.9 * T)
    draw_gauge(cv, V, r, hl={'thimble': seg(t, 0.8, 1.4) * (1 - seg(t, 0.3 * T, 0.35 * T))})
    X, Y, s = mapper(V)
    a = seg(t, 0.25 * T, 0.25 * T + 0.6)
    card(cv, 1230, 140, 1870, 330, a)
    cv.text(1260, 190, 'Circular scale', 34, INK, 'b', 'lm', a)
    cv.text(1260, 242, '50 equal divisions', 30, BLUE_D, 'sb', 'lm', a)
    cv.text(1260, 286, 'around the thimble edge', 26, MUTED, 'm', 'lm', a)
    # turn counter dial
    ad = seg(t, 0.3 * T, 0.35 * T) * a
    cx, cy = 1770, 220
    cv.circle(cx, cy, 52, fill=BLUE_T, a=ad)
    ang = -math.pi / 2 + (r - 5) / 0.5 * 2 * math.pi
    cv.d.arc([(cx - 44) * SS, (cy - 44) * SS, (cx + 44) * SS, (cy + 44) * SS], -90,
             -90 + (r - 5) / 0.5 * 360 + 0.01, fill=cv.c(BLUE, ad), width=8 * SS)
    cv.line([(cx, cy), (cx + 34 * math.cos(ang), cy + 34 * math.sin(ang))], INK, 5, ad)
    cv.text(cx, cy + 82, f'{(r - 5) / 0.5:.2f} turn', 22, INK, 'sb', 'mm', ad)


b.append(Beat("The thimble turns around the sleeve, and it carries the spindle with it. Its edge carries the "
              "circular scale, which on this gauge is divided into fifty equal divisions. Watch the divisions pass "
              "the reference line as it turns.", p_thimble, extra=0.6))

FV55 = full_view(5.5)


def p_ratchet(cv, t, T):
    V = lerp_view(ZOOM_THIMBLE, FV55, seg(t, 0, 1.4))
    hr = seg(t, 1.4, 1.9) * (1 - seg(t, 0.5 * T, 0.55 * T))
    hlk = seg(t, 0.55 * T, 0.6 * T)
    lock = seg(t, 0.75 * T, 0.85 * T) - seg(t, 0.9 * T, 0.97 * T)
    draw_gauge(cv, V, 5.5, hl={'ratchet': hr, 'lock': hlk}, lock=lock)
    parts_labels(cv, V, 5.5, {'ratchet': seg(t, 1.4, 1.9), 'lock': hlk})
    X, Y, s = mapper(V)
    clicks(cv, X(XS0 + 5.5 + TH_LEN + 6), Y(-4), t, 0.25 * T, 0.48 * T)


b.append(Beat("At the end is the ratchet. You turn the ratchet for the final tightening. It slips and clicks once the "
              "right pressure is reached, so you never squeeze the object too hard. "
              "The lock nut clamps the spindle, so the reading cannot change while you read it.", p_ratchet))


def p_recap(cv, t, T):
    draw_gauge(cv, FV55, 5.5)
    keys = ['frame', 'anvil', 'spindle', 'sleeve', 'thimble', 'ratchet', 'lock']
    parts_labels(cv, FV55, 5.5, {k: seg(t, 0.2 + i * 0.12 * T, 0.6 + i * 0.12 * T) for i, k in enumerate(keys)})


b.append(Beat("So, the parts are: the frame, the anvil, the spindle, the sleeve with its main scale, the thimble with "
              "its circular scale, the ratchet, and the lock nut.", p_recap, extra=0.8))

# 3 · Pitch ---------------------------------------------------------------------
b = scene('The pitch of the screw')
PV = view(XS0 + 3.4, 0, 54, 960, 620)


def pitch_counters(cv, r, a):
    card(cv, 300, 135, 930, 300, a)
    card(cv, 990, 135, 1620, 300, a)
    n = r / 0.5
    cx, cy = 390, 218
    cv.circle(cx, cy, 52, fill=BLUE_T, a=a)
    frac = n - math.floor(n + 1e-9)
    cv.d.arc([(cx - 44) * SS, (cy - 44) * SS, (cx + 44) * SS, (cy + 44) * SS], -90, -90 + frac * 360 + 0.01,
             fill=cv.c(BLUE, a), width=8 * SS)
    ang = -math.pi / 2 + frac * 2 * math.pi
    cv.line([(cx, cy), (cx + 34 * math.cos(ang), cy + 34 * math.sin(ang))], INK, 5, a)
    cv.text(470, 190, 'Turns of the thimble', 26, MUTED, 'm', 'lm', a)
    cv.text(470, 245, f'{n:.1f}', 50, INK, 'xb', 'lm', a)
    cv.text(1030, 190, 'Distance the spindle moved', 26, MUTED, 'm', 'lm', a)
    cv.text(1030, 245, f'{r:.2f} mm', 50, BLUE_D, 'xb', 'lm', a)


def pitch_bracket(cv, V, r, a):
    X, Y, s = mapper(V)
    if r > 0.05:
        cv.arrow(X(XS0), Y(-4.3), X(XS0 + r), Y(-4.3), ORANGE, 4, 14, a, both=r > 0.3)


def pitch1(cv, t, T):
    r = 0.5 * seg(t, 0.35 * T, 0.95 * T)
    draw_gauge(cv, PV, r)
    pitch_counters(cv, r, seg(t, 0, 0.6))
    pitch_bracket(cv, PV, r, 1)


b.append(Beat("A screw gauge works on the principle of a screw. When you turn the thimble through one complete "
              "rotation, the spindle moves forward or backward by a fixed distance, called the pitch.", pitch1, extra=0.6))


def pitch2(cv, t, T):
    r = 0.5 + 1.5 * seg(t, 0.15 * T, 0.85 * T)
    draw_gauge(cv, PV, r)
    pitch_counters(cv, r, 1)
    pitch_bracket(cv, PV, r, 1)


b.append(Beat("Let's measure the pitch. Keep turning. After four complete turns, the edge of the thimble has moved "
              "two millimetres along the main scale.", pitch2,
              cap="Let's measure the pitch. Keep turning. After four complete turns, the edge of the thimble has moved "
                  "2 mm along the main scale.", extra=0.8))


def pitch3(cv, t, T):
    draw_gauge(cv, PV, 2.0)
    pitch_bracket(cv, PV, 2.0, 1)
    a0 = 1 - seg(t, 0, 0.5)
    pitch_counters(cv, 2.0, a0)
    a = seg(t, 0.4, 1.0)
    card(cv, 300, 120, 1620, 320, a)
    cv.text(960, 172, 'Pitch  =  distance moved  ÷  number of turns', 40, INK, 'b', 'mm', a)
    a2 = seg(t, 0.3 * T, 0.3 * T + 0.6)
    cv.text(960, 262, '=  2 mm ÷ 4  =  0.5 mm', 52, BLUE_D, 'xb', 'mm', a2)
    X, Y, s = mapper(PV)
    a3 = seg(t, 0.65 * T, 0.65 * T + 0.5)
    mark_main(cv, PV, 1.5, True, GREEN, a3)
    pill(cv, X(XS0 + 1.5), Y(3.8) + 30, '1 turn = 0.5 mm = one half-mm mark', 26, fill=GREEN, a=a3)


b.append(Beat("Pitch equals distance moved, divided by the number of turns. That's two millimetres divided by four, "
              "which is zero point five millimetres. So each full turn moves the spindle half a millimetre, "
              "exactly one mark on the half millimetre scale.", pitch3,
              cap="Pitch = distance moved ÷ number of turns = 2 mm ÷ 4 = 0.5 mm. So each full turn moves the spindle "
                  "half a millimetre — exactly one mark on the half-millimetre scale.", extra=0.8))

# 4 · Least count -------------------------------------------------------------
b = scene('Least count')
LV = view(XS0 + 2 + 6.2, 0, 70, 960, 560)


def lc1(cv, t, T):
    V = lerp_view(PV, LV, seg(t, 0, 1.2))
    r = 2.0 + 0.01 * seg(t, 0.4 * T, 0.7 * T)
    draw_gauge(cv, V, r)
    a = seg(t, 1.2, 1.7)
    index_line(cv, V, r, BLUE, a)
    mark_div(cv, V, r, 0, ORANGE, seg(t, 1.4, 1.9))
    mark_div(cv, V, r, 1, GREEN, seg(t, 0.4 * T, 0.5 * T))
    ac = seg(t, 0.55 * T, 0.55 * T + 0.6)
    card(cv, 1180, 150, 1860, 400, ac)
    cv.text(1215, 200, 'Turn by 1 division', 32, INK, 'b', 'lm', ac)
    cv.text(1215, 255, 'spindle moves  1/50  of the pitch', 28, MUTED, 'm', 'lm', ac)
    cv.text(1215, 330, '0.5 mm ÷ 50 = 0.01 mm', 40, BLUE_D, 'xb', 'lm', ac)


b.append(Beat("Now, one full turn is split into fifty divisions on the circular scale. So turning the thimble by just "
              "one division moves the spindle by one fiftieth of the pitch.", lc1, extra=0.8))


def lc2(cv, t, T):
    draw_gauge(cv, LV, 2.01)
    cv.veil(0.82 * seg(t, 0, 0.6))
    a = seg(t, 0.2, 0.8)
    card(cv, 260, 210, 1660, 720, a)
    cv.text(960, 285, 'Least count (LC)', 40, MUTED, 'sb', 'mm', a)
    cv.text(960, 395, 'LC  =  pitch  ÷  number of circular-scale divisions', 42, INK, 'b', 'mm', a)
    a2 = seg(t, 0.4 * T, 0.4 * T + 0.6)
    cv.text(960, 500, '=  0.5 mm ÷ 50', 46, INK, 'b', 'mm', a2)
    a3 = seg(t, 0.62 * T, 0.62 * T + 0.6)
    pill(cv, 960, 615, 'LC = 0.01 mm', 50, fill=BLUE_D, a=a3, wt='xb')


b.append(Beat("This smallest distance the gauge can measure is called its least count. Least count equals the pitch, "
              "divided by the number of divisions on the circular scale. Zero point five millimetres, divided by fifty, "
              "gives zero point zero one millimetres.", lc2,
              cap="This smallest distance the gauge can measure is called its least count. Least count = pitch ÷ number "
                  "of circular-scale divisions = 0.5 mm ÷ 50 = 0.01 mm.", extra=0.6))


def lc3(cv, t, T):
    draw_gauge(cv, LV, 2.01)
    cv.veil(0.82)
    a = seg(t, 0.2, 0.8)
    card(cv, 260, 180, 940, 560, a)
    cv.text(600, 240, 'This gauge', 32, MUTED, 'sb', 'mm', a)
    cv.text(600, 330, 'pitch 0.5 mm', 36, INK, 'b', 'mm', a)
    cv.text(600, 390, '50 divisions', 36, INK, 'b', 'mm', a)
    pill(cv, 600, 485, 'LC = 0.01 mm', 34, fill=BLUE_D, a=a)
    a2 = seg(t, 0.3 * T, 0.3 * T + 0.6)
    card(cv, 980, 180, 1660, 560, a2)
    cv.text(1320, 240, 'Another common gauge', 32, MUTED, 'sb', 'mm', a2)
    cv.text(1320, 330, 'pitch 1 mm', 36, INK, 'b', 'mm', a2)
    cv.text(1320, 390, '100 divisions', 36, INK, 'b', 'mm', a2)
    pill(cv, 1320, 485, 'LC = 0.01 mm', 34, fill=BLUE_D, a=a2)
    a3 = seg(t, 0.68 * T, 0.68 * T + 0.6)
    card(cv, 260, 620, 1660, 760, a3, fill=GREEN_T, outline='#b2dfbd')
    cv.text(960, 690, 'Always work out the least count of YOUR gauge first.', 36, '#1f6f30', 'b', 'mm', a3)


b.append(Beat("Some screw gauges have a pitch of one millimetre and one hundred divisions. Their least count is also "
              "zero point zero one millimetres. Always work out the least count of your own instrument first.", lc3,
              cap="Some screw gauges have a pitch of 1 mm and 100 divisions. Their least count is also 0.01 mm. "
                  "Always work out the least count of your own instrument first.", extra=0.6))

# 5 · Zero error ----------------------------------------------------------------
b = scene('Checking the zero error')
FV3 = full_view(3)


def ze1(cv, t, T):
    r = 3 - 3 * seg(t, 0.2 * T, 0.7 * T)
    draw_gauge(cv, FV3, r, hl={'ratchet': seg(t, 0.45 * T, 0.5 * T) * (1 - seg(t, 0.85 * T, 0.9 * T))})
    X, Y, s = mapper(FV3)
    clicks(cv, X(XS0 + r + TH_LEN + 6), Y(-4), t, 0.62 * T, 0.85 * T)
    a = seg(t, 0.72 * T, 0.8 * T)
    pill(cv, X(0), Y(-6.5), 'faces just touch', 26, fill=BLUE, a=a)


b.append(Beat("Before measuring anything, check for zero error. Clean the faces, then turn the ratchet until the "
              "anvil and spindle just touch. Then look closely at the scales.", ze1, extra=0.6))

ZV = view(XS0 + 6.6, 0, 70, 960, 545)


def ze_case(z, title, lines, colour, tint, marks):
    def draw(cv, t, T, z=z):
        V = lerp_view(FV3, ZV, seg(t, 0, 1.3)) if z == 0 else ZV
        draw_gauge(cv, V, z, z)
        a = seg(t, 1.0, 1.5) if z == 0 else 1
        index_line(cv, V, z, BLUE, a)
        for (d, col, ta) in marks:
            mark_div(cv, V, z, d, col, seg(t, ta * T, ta * T + 0.4))
        X, Y, s = mapper(V)
        pill(cv, X(XS0 - 3.4), Y(0), 'reference line', 24, fill=BLUE, a=a)
        ac = seg(t, 0.25 * T, 0.25 * T + 0.5)
        y1 = 190 + 90 + 52 * len(lines)
        card(cv, 1210, 160, 1870, y1, ac, fill=tint, outline=colour)
        cv.text(1245, 215, title, 36, colour, 'xb', 'lm', ac)
        for i, (ta, s_, wt) in enumerate(lines):
            cv.text(1245, 285 + 52 * i, s_, 29, INK, wt, 'lm', ac * seg(t, ta * T, ta * T + 0.5))
        if z == 0:
            check(cv, 1820, 215, 26, GREEN, ac)
    return draw


b.append(Beat("If the zero of the circular scale lines up exactly with the reference line, there is no zero error.",
              ze_case(0.0, 'No zero error', [(0.4, 'Zero is exactly on the line.', 'm'),
                                             (0.55, 'Zero error = 0', 'b')], GREEN, GREEN_T, [(0, GREEN, 0.3)]),
              extra=0.8))

b.append(Beat("If the zero of the circular scale is below the reference line, the gauge reads too much. This is a "
              "positive zero error. Here, the third division sits on the line, so the zero error is plus three, times "
              "zero point zero one, which is plus zero point zero three millimetres.",
              ze_case(0.03, 'Positive zero error', [(0.1, 'Zero is BELOW the line.', 'm'),
                                                    (0.45, 'Division 3 is on the line.', 'm'),
                                                    (0.7, 'Zero error = +3 × 0.01', 'b'),
                                                    (0.78, '            = +0.03 mm', 'b')],
                      RED, RED_T, [(0, ORANGE, 0.12), (3, GREEN, 0.45)]),
              cap="If the zero of the circular scale is below the reference line, the gauge reads too much: a positive "
                  "zero error. Here division 3 is on the line, so zero error = +3 × 0.01 = +0.03 mm.", extra=0.8))

b.append(Beat("If the zero of the circular scale is above the reference line, the gauge reads too little. This is a "
              "negative zero error. Here, division forty seven is on the line. Count the divisions still needed to "
              "reach fifty. That's three, so the zero error is minus zero point zero three millimetres.",
              ze_case(-0.03, 'Negative zero error', [(0.1, 'Zero is ABOVE the line.', 'm'),
                                                     (0.4, 'Division 47 is on the line.', 'm'),
                                                     (0.62, 'Zero error = −(50 − 47) × 0.01', 'b'),
                                                     (0.78, '            = −0.03 mm', 'b')],
                      BLUE_D, BLUE_T, [(0, ORANGE, 0.12), (47, GREEN, 0.4)]),
              cap="If the zero of the circular scale is above the reference line, the gauge reads too little: a "
                  "negative zero error. Here division 47 is on the line. Divisions still needed to reach 50: 3, so "
                  "zero error = −(50 − 47) × 0.01 = −0.03 mm.", extra=0.8))


def ze_rule(cv, t, T):
    draw_gauge(cv, ZV, -0.03, -0.03)
    cv.veil(0.85 * seg(t, 0, 0.6))
    a = seg(t, 0.2, 0.8)
    card(cv, 260, 170, 1660, 420, a)
    cv.text(960, 235, 'Correcting a reading', 32, MUTED, 'sb', 'mm', a)
    cv.text(960, 340, 'Corrected  =  observed reading  −  zero error', 46, INK, 'xb', 'mm', a)
    a2 = seg(t, 0.4 * T, 0.4 * T + 0.6)
    card(cv, 260, 470, 940, 720, a2, fill=RED_T, outline='#f3b5b5')
    cv.text(600, 530, 'Zero error +0.03 mm', 32, RED, 'b', 'mm', a2)
    cv.text(600, 620, 'subtract 0.03 mm', 40, INK, 'xb', 'mm', a2)
    a3 = seg(t, 0.62 * T, 0.62 * T + 0.6)
    card(cv, 980, 470, 1660, 720, a3, fill=BLUE_T, outline='#a5c8ef')
    cv.text(1320, 530, 'Zero error −0.03 mm', 32, BLUE_D, 'b', 'mm', a3)
    cv.text(1320, 620, 'add 0.03 mm', 40, INK, 'xb', 'mm', a3)


b.append(Beat("To correct any reading, always subtract the zero error. Corrected reading equals observed reading, "
              "minus zero error. With a positive zero error you subtract. With a negative zero error, subtracting a "
              "negative means you add.", ze_rule,
              cap="To correct any reading, always subtract the zero error: corrected reading = observed reading − zero "
                  "error. With a positive zero error you subtract; with a negative zero error, subtracting a negative "
                  "means you add.", extra=0.8))

# 6 · Taking a reading ---------------------------------------------------------
b = scene('Taking a reading: diameter of a wire')
Z6 = 0.03
D6 = 2.85
R6 = D6 + Z6
FV4 = full_view(4)


def m_open(cv, t, T):
    r = Z6 + (4 - Z6) * seg(t, 0.3 * T, 0.85 * T)
    draw_gauge(cv, FV4, r, Z6)
    step_pill(cv, 1, 'Open the jaws a little wider than the wire', seg(t, 0, 0.5))
    a = seg(t, 0.5 * T, 0.5 * T + 0.5)
    card(cv, 1300, 790, 1860, 930, a)
    cv.text(1330, 835, 'This gauge has a zero error', 26, MUTED, 'm', 'lm', a)
    cv.text(1330, 885, 'of +0.03 mm (checked earlier)', 26, INK, 'sb', 'lm', a)


b.append(Beat("Now let's measure the diameter of a wire, using a gauge with a zero error of plus zero point zero three "
              "millimetres. Step one. Turn the thimble backwards, to open a gap a little wider than the wire.", m_open,
              cap="Now let's measure the diameter of a wire, using a gauge with a zero error of +0.03 mm. Step 1: turn "
                  "the thimble backwards to open a gap a little wider than the wire.", extra=0.4))


def m_place(cv, t, T):
    dy = -5 * (1 - seg(t, 0.2 * T, 0.8 * T))
    draw_gauge(cv, FV4, 4, Z6, obj=('wire', D6, dy) if t > 0.15 * T else None)
    step_pill(cv, 2, 'Place the wire between anvil and spindle')


b.append(Beat("Step two. Place the wire between the anvil and the spindle, so that it touches the anvil face.",
              m_place, extra=0.6))


def m_close(cv, t, T):
    r = 4 - (4 - 3.1) * seg(t, 0.05 * T, 0.32 * T) - (3.1 - R6) * seg(t, 0.4 * T, 0.6 * T)
    lock = seg(t, 0.8 * T, 0.88 * T)
    hl = {'thimble': seg(t, 0, 0.3) * (1 - seg(t, 0.34 * T, 0.38 * T)),
          'ratchet': seg(t, 0.36 * T, 0.4 * T) * (1 - seg(t, 0.66 * T, 0.7 * T)),
          'lock': seg(t, 0.72 * T, 0.76 * T)}
    draw_gauge(cv, FV4, r, Z6, obj=('wire', D6, 0), hl=hl, lock=lock)
    X, Y, s = mapper(FV4)
    clicks(cv, X(XS0 + r + TH_LEN + 6), Y(-4), t, 0.52 * T, 0.7 * T)
    if t < 0.38 * T:
        step_pill(cv, 3, 'Turn the thimble until the spindle nearly touches')
    elif t < 0.72 * T:
        step_pill(cv, 3, 'Finish with the ratchet until it clicks')
    else:
        step_pill(cv, 4, 'Tighten the lock nut')


b.append(Beat("Step three. Turn the thimble forward until the spindle nearly touches the wire. Then use the ratchet for "
              "the final turn, until it clicks. Step four. Tighten the lock nut.", m_close, extra=0.6))

RV = view(XS0 + R6 + 6.4, 0, 70, 760, 545)


def reading_card(cv, t, rows_t, a=1.0):
    rows = [(rows_t[0], 'Main scale reading (MSR)', '2.5 mm', INK),
            (rows_t[1], 'Circular scale (CSR)', '38 × 0.01 = 0.38 mm', INK),
            (rows_t[2], 'Observed = MSR + CSR', '2.88 mm', BLUE_D),
            (rows_t[3], 'Corrected = 2.88 − (+0.03)', '2.85 mm', GREEN)]
    rows_card(cv, 1080, 135, 1880, rows, t, a, title='Reading', size=32)


def m_msr(cv, t, T):
    V = lerp_view(FV4, RV, seg(t, 0, 1.4))
    draw_gauge(cv, V, R6, Z6, obj=('wire', D6, 0), lock=1)
    step_pill(cv, 5, 'Read the main scale', seg(t, 0.2, 0.7))
    a1 = seg(t, 0.3 * T, 0.3 * T + 0.4)
    a2 = seg(t, 0.5 * T, 0.5 * T + 0.4)
    X, Y, s = mapper(V)
    mark_main(cv, V, 2, False, ORANGE, a1)
    pill(cv, X(XS0 + 2), Y(-4.7), '2 mm', 26, fill=ORANGE, a=a1)
    mark_main(cv, V, 2.5, True, GREEN, a2)
    pill(cv, X(XS0 + 2.5), Y(4.4), '+ 0.5 mm', 26, fill=GREEN, a=a2)
    reading_card(cv, t, [0.75 * T, 1e9, 1e9, 1e9], seg(t, 1.2, 1.7))


b.append(Beat("Step five. Read the main scale. Look for the last mark visible just to the left of the thimble edge. "
              "The two millimetre mark is visible, and so is the half millimetre mark after it. So the main scale "
              "reading is two point five millimetres.", m_msr,
              cap="Step 5: read the main scale. Look for the last mark visible just left of the thimble edge. The 2 mm "
                  "mark is visible, and so is the half-mm mark after it. So the main scale reading is 2.5 mm.",
              extra=0.6))


def m_csr(cv, t, T):
    draw_gauge(cv, RV, R6, Z6, obj=('wire', D6, 0), lock=1)
    step_pill(cv, 6, 'Read the circular scale')
    X, Y, s = mapper(RV)
    index_line(cv, RV, R6, BLUE, seg(t, 0.2 * T, 0.25 * T))
    mark_div(cv, RV, R6, 38, ORANGE, seg(t, 0.35 * T, 0.4 * T))
    pill(cv, X(XS0 + R6 + 5.0), Y(0), 'division 38', 26, fill=ORANGE, a=seg(t, 0.35 * T, 0.4 * T))
    mark_main(cv, RV, 2, False, ORANGE, 0.5)
    mark_main(cv, RV, 2.5, True, GREEN, 0.5)
    reading_card(cv, t, [-1, 0.65 * T, 1e9, 1e9])


b.append(Beat("Step six. Read the circular scale. Find the division that lines up with the reference line. Here it is "
              "division thirty eight. The circular scale reading is thirty eight times the least count, which is zero "
              "point three eight millimetres.", m_csr,
              cap="Step 6: read the circular scale. Find the division that lines up with the reference line. Here it is "
                  "division 38. Circular scale reading = 38 × 0.01 = 0.38 mm.", extra=0.6))


def m_total(cv, t, T):
    draw_gauge(cv, RV, R6, Z6, obj=('wire', D6, 0), lock=1)
    mark_main(cv, RV, 2, False, ORANGE, 0.5)
    mark_main(cv, RV, 2.5, True, GREEN, 0.5)
    mark_div(cv, RV, R6, 38, ORANGE, 0.6)
    reading_card(cv, t, [-1, -1, 0.3 * T, 1e9])
    a = seg(t, 0.35 * T, 0.35 * T + 0.5)
    card(cv, 1080, 600, 1880, 760, a, fill=BLUE_T, outline='#a5c8ef')
    cv.text(1480, 650, 'Reading = MSR + CSR × LC', 34, INK, 'b', 'mm', a)
    cv.text(1480, 712, '2.5 + 0.38 = 2.88 mm', 36, BLUE_D, 'xb', 'mm', a)


b.append(Beat("The observed reading equals the main scale reading, plus the circular scale reading. Two point five, "
              "plus zero point three eight, gives two point eight eight millimetres.", m_total,
              cap="Observed reading = main scale reading + circular scale reading = 2.5 + 0.38 = 2.88 mm.", extra=0.6))


def m_correct(cv, t, T):
    draw_gauge(cv, RV, R6, Z6, obj=('wire', D6, 0), lock=1)
    reading_card(cv, t, [-1, -1, -1, 0.45 * T])
    a = seg(t, 0.6 * T, 0.6 * T + 0.5)
    card(cv, 1080, 600, 1880, 800, a, fill=GREEN_T, outline='#b2dfbd')
    cv.text(1480, 655, 'Diameter of the wire', 30, '#1f6f30', 'sb', 'mm', a)
    cv.text(1480, 735, '2.85 mm', 64, GREEN, 'xb', 'mm', a)


b.append(Beat("Finally, correct for zero error. This gauge has a zero error of plus zero point zero three millimetres, "
              "so the diameter is two point eight eight, minus zero point zero three, which is two point eight five "
              "millimetres.", m_correct,
              cap="Finally, correct for zero error. This gauge has a zero error of +0.03 mm, so the diameter is "
                  "2.88 − 0.03 = 2.85 mm.", extra=1.0))

# 7 · Practice -----------------------------------------------------------------
b = scene('Your turn: thickness of a sheet')
Z7 = -0.02
T7 = 1.14
R7 = T7 + Z7
SMALL = full_view(3, 8.6, 345, 365)
PANEL = (660, 130, 1200, 790)       # x, y, w, h of the close-up panel
PV7 = view(XS0 + R7 + 5.0, 0, 62, 470, 400)


def practice_base(cv, t, marks):
    draw_gauge(cv, SMALL, R7, Z7, obj=('sheet', T7, 0), numbers=False, lock=1)
    cv.text(345, 155, 'Metal sheet in the gauge', 26, MUTED, 'sb', 'mm')
    sub = Cv(PANEL[2], PANEL[3], CARD)
    draw_gauge(sub, PV7, R7, Z7)
    marks(sub)
    pill(sub, 120, 40, 'Close-up', 22, fill=INK)
    cv.paste(sub, PANEL[0], PANEL[1])


def practice_info(cv, a=1.0):
    card(cv, 60, 600, 630, 800, a)
    cv.text(90, 645, 'Zero error  =  −0.02 mm', 30, INK, 'b', 'lm', a)
    cv.text(90, 700, 'Least count  =  0.01 mm', 30, INK, 'b', 'lm', a)
    cv.text(90, 755, 'Thickness = ?', 30, BLUE_D, 'xb', 'lm', a)


def pr1(cv, t, T):
    practice_base(cv, t, lambda s: None)
    practice_info(cv, seg(t, 0.4, 1.0))
    a = seg(t, 0.55 * T, 0.55 * T + 0.4)
    k = clamp((t - 0.55 * T) / (T - 0.55 * T))
    cx, cy = 340, 880
    cv.rect(cx - 230, cy - 45, cx + 230, cy + 45, fill=ORANGE, r=45, a=a)
    cv.rect(cx - 190, cy - 18, cx - 180, cy + 18, fill='#ffffff', a=a)
    cv.rect(cx - 170, cy - 18, cx - 160, cy + 18, fill='#ffffff', a=a)
    cv.text(cx - 135, cy, 'Pause & try it!', 32, '#ffffff', 'xb', 'lm', a)
    cv.d.arc([(cx + 160) * SS, (cy - 28) * SS, (cx + 216) * SS, (cy + 28) * SS], -90, -90 + 360 * (1 - k) + 0.01,
             fill=cv.c('#ffffff', a), width=6 * SS)


b.append(Beat("Your turn. Here we measure a thin metal sheet with a gauge that has a negative zero error of minus "
              "zero point zero two millimetres. Pause the video, and work out the thickness.", pr1,
              cap="Your turn! Here we measure a thin metal sheet with a gauge that has a zero error of −0.02 mm. "
                  "Pause the video and work out the thickness.", extra=4.0))


def pr2(cv, t, T):
    def marks(sub):
        mark_main(sub, PV7, 1, False, ORANGE, seg(t, 0.05 * T, 0.12 * T))
        X, Y, s = mapper(PV7)
        a = seg(t, 0.25 * T, 0.3 * T)
        pill(sub, X(XS0 + 1.5), Y(3.0) + 40, '1.5 mark hidden', 22, fill=MUTED, a=a)
        index_line(sub, PV7, R7, BLUE, seg(t, 0.45 * T, 0.5 * T))
        mark_div(sub, PV7, R7, 12, ORANGE, seg(t, 0.5 * T, 0.55 * T))
    practice_base(cv, t, marks)
    rows = [(0.15 * T, 'MSR', '1.0 mm', INK), (0.6 * T, 'CSR', '12 × 0.01 = 0.12 mm', INK),
            (0.82 * T, 'Observed', '1.12 mm', BLUE_D)]
    rows_card(cv, 60, 600, 630, rows, t, size=30)


b.append(Beat("The one millimetre mark is visible, but the next half millimetre mark is still hidden. So the main scale "
              "reading is one point zero millimetres. The circular scale shows division twelve, which is zero point one "
              "two millimetres. The observed reading is one point one two millimetres.", pr2,
              cap="The 1 mm mark is visible, but the next half-mm mark is still hidden, so MSR = 1.0 mm. The circular "
                  "scale shows division 12, so CSR = 0.12 mm. Observed reading = 1.12 mm.", extra=0.6))


def pr3(cv, t, T):
    practice_base(cv, t, lambda s: None)
    a = seg(t, 0.2, 0.7)
    card(cv, 60, 560, 630, 900, a, fill=GREEN_T, outline='#b2dfbd')
    cv.text(345, 610, 'Corrected thickness', 28, '#1f6f30', 'sb', 'mm', a)
    a2 = seg(t, 0.25 * T, 0.25 * T + 0.5)
    cv.text(345, 690, '1.12 − (−0.02)', 38, INK, 'b', 'mm', a2)
    a3 = seg(t, 0.55 * T, 0.55 * T + 0.5)
    cv.text(345, 800, '= 1.14 mm', 60, GREEN, 'xb', 'mm', a3)


b.append(Beat("Now correct it. One point one two, minus minus zero point zero two, is one point one two plus zero "
              "point zero two. The sheet is one point one four millimetres thick. Did you get it?", pr3,
              cap="Now correct it: 1.12 − (−0.02) = 1.12 + 0.02. The sheet is 1.14 mm thick. Did you get it?",
              extra=1.0))

# 8 · Repeat and average -------------------------------------------------------
b = scene('Repeat and take the mean')


def rep1(cv, t, T):
    a = seg(t, 0, 0.6)
    cv.line([(220, 330), (1700, 330)], mix(COPPER, '#5a2d0c', 0.2), 26, a)
    cv.line([(220, 324), (1700, 324)], '#e6a56a', 6, a)
    for i in range(4):
        x = 400 + i * 380
        ai = seg(t, 0.25 * T + i * 0.12 * T, 0.25 * T + i * 0.12 * T + 0.5)
        cv.line([(x, 290), (x, 370)], BLUE, 4, ai)
        pill(cv, x, 250, f'place {i + 1}', 24, fill=BLUE, a=ai)
        cx, cy = x, 610
        cv.circle(cx, cy, 110, fill=mix(COPPER, '#ffffff', 0.35), outline='#7a3e10', w=3, a=ai)
        aj = seg(t, 0.75 * T, 0.75 * T + 0.5)
        cv.arrow(cx - 110, cy, cx + 110, cy, INK, 4, 16, ai, both=True)
        cv.arrow(cx, cy - 110, cx, cy + 110, ORANGE, 4, 16, aj, both=True)
        cv.text(cx, 760, 'two readings at 90°', 24, MUTED, 'm', 'mm', aj)
    cv.text(960, 455, 'cross-section at each place', 26, MUTED, 'sb', 'mm', seg(t, 0.4 * T, 0.5 * T))


b.append(Beat("One reading is never enough. A wire may not be perfectly round, or perfectly uniform. So measure its "
              "diameter at several places along its length, and at each place, take two readings at right angles to "
              "each other.", rep1, extra=0.6))


def rep2(cv, t, T):
    x0, x1, y0 = 360, 1560, 150
    obs = ['2.88', '2.87', '2.89', '2.88']
    cor = ['2.85', '2.84', '2.86', '2.85']
    a = seg(t, 0, 0.6)
    card(cv, x0, y0, x1, y0 + 100 + 82 * 5, a)
    cols = [x0 + 130, x0 + 560, x0 + 980]
    for cx, h in zip(cols, ['Reading', 'Observed (mm)', 'Corrected (mm)']):
        cv.text(cx, y0 + 55, h, 30, MUTED, 'sb', 'mm', a)
    cv.line([(x0 + 30, y0 + 98), (x1 - 30, y0 + 98)], LINE, 2, a)
    for i in range(4):
        ai = seg(t, 0.15 * T + 0.1 * T * i, 0.15 * T + 0.1 * T * i + 0.4)
        y = y0 + 140 + 82 * i
        cv.text(cols[0], y, str(i + 1), 32, INK, 'b', 'mm', ai)
        cv.text(cols[1], y, obs[i], 32, INK, 'm', 'mm', ai)
        cv.text(cols[2], y, cor[i], 32, INK, 'b', 'mm', seg(t, 0.55 * T, 0.6 * T) * ai)
    am = seg(t, 0.7 * T, 0.7 * T + 0.5)
    y = y0 + 140 + 82 * 4
    cv.rect(x0 + 20, y - 36, x1 - 20, y + 36, fill=GREEN_T, r=14, a=am)
    cv.text(cols[0], y, 'Mean', 32, '#1f6f30', 'xb', 'mm', am)
    cv.text(cols[1], y, '(2.85 + 2.84 + 2.86 + 2.85) ÷ 4', 26, '#1f6f30', 'm', 'mm', am)
    cv.text(cols[2], y, '2.85 mm', 38, GREEN, 'xb', 'mm', am)
    cv.text(960, 820, 'Corrected = observed − (+0.03 mm)', 28, MUTED, 'm', 'mm', seg(t, 0.55 * T, 0.6 * T))


b.append(Beat("Record the readings in a table. Correct each one for the zero error, and then take the mean. Here the "
              "mean diameter of the wire is two point eight five millimetres.", rep2,
              cap="Record the readings in a table, correct each one for zero error, then take the mean. Here the mean "
                  "diameter of the wire is 2.85 mm.", extra=1.2))

# 9 · Precautions ---------------------------------------------------------------
b = scene('Precautions')
PRE = [('Always use the ratchet', "never force the thimble — don't squeeze the object"),
       ('Turn in one direction only', 'when closing on the object, to avoid backlash error'),
       ('Clean the anvil and spindle faces', 'dust adds to the reading'),
       ('Check the zero error first', 'and correct every reading for it'),
       ('Read straight on', 'eye directly in front of the scale, to avoid parallax'),
       ('Take several readings', 'at different places, then average')]


def pre_list(cv, t, T, shown, fresh):
    for i, (h, sub) in enumerate(PRE):
        if i >= shown:
            break
        a = seg(t, 0.3 + (i - fresh[0]) * fresh[1] * T, 0.8 + (i - fresh[0]) * fresh[1] * T) if i >= fresh[0] else 1
        y = 160 + i * 128
        card(cv, 300, y, 1620, y + 108, a)
        check(cv, 360, y + 54, 28, GREEN, a)
        cv.text(415, y + 38, h, 34, INK, 'b', 'lm', a)
        cv.text(415, y + 78, sub, 26, MUTED, 'm', 'lm', a)


b.append(Beat("A few precautions. Always use the ratchet, and never force the thimble, so that the object isn't "
              "squeezed out of shape.", lambda cv, t, T: pre_list(cv, t, T, 1, (0, 0.2))))
b.append(Beat("While closing on the object, turn the screw in one direction only. This avoids backlash error, caused by "
              "the small play between the screw and its nut.", lambda cv, t, T: pre_list(cv, t, T, 2, (1, 0.2))))
b.append(Beat("Keep the anvil and spindle faces clean. Check the zero error before you start. Read the scales with your "
              "eye directly in front of them to avoid parallax. And take several readings, then average.",
              lambda cv, t, T: pre_list(cv, t, T, 6, (2, 0.2)), extra=1.0))

# 10 · Summary ------------------------------------------------------------------
b = scene('Summary')
SUM = ['Find the least count:  LC = pitch ÷ number of divisions',
       'Check the zero error with the jaws closed (use the ratchet)',
       'Read the main scale (MSR) at the thimble edge',
       'Read the circular-scale division on the reference line (CSR)',
       'Correct for zero error, repeat, and take the mean']


def summary(cv, t, T):
    for i, s_ in enumerate(SUM):
        a = seg(t, 0.3 + i * 0.13 * T, 0.8 + i * 0.13 * T)
        y = 165 + i * 92
        cv.circle(330, y + 30, 28, fill=BLUE, a=a)
        cv.text(330, y + 30, str(i + 1), 28, '#ffffff', 'xb', 'mm', a)
        cv.text(385, y + 30, s_, 34, INK, 'sb', 'lm', a)
    a = seg(t, 0.72 * T, 0.72 * T + 0.6)
    card(cv, 260, 660, 1660, 880, a, fill=BLUE_T, outline=BLUE)
    cv.text(960, 725, 'Reading  =  MSR  +  CSR × LC', 50, INK, 'xb', 'mm', a)
    cv.text(960, 812, 'Corrected  =  Reading  −  Zero error', 42, BLUE_D, 'b', 'mm', a)


b.append(Beat("To summarise. Find the least count: the pitch divided by the number of divisions. Check the zero error. "
              "Take the main scale reading, and the circular scale reading. The reading equals the main scale reading, "
              "plus the circular scale reading times the least count. Then subtract the zero error, and average several "
              "readings.", summary, extra=1.2))


def outro(cv, t, T):
    a = seg(t, 0, 0.8)
    cv.text(960, 250, "You're ready to measure!", 72, BLUE_D, 'xb', 'mm', a)
    cv.text(960, 340, 'Thanks for watching', 36, MUTED, 'sb', 'mm', a)
    r = 0.5 + 2.0 * seg(t, 0.4, T)
    draw_gauge(cv, full_view(2.5, 14, 960, 700), r)


b.append(Beat("Now you are ready to measure with a screw gauge. Thanks for watching!", outro, header=False, extra=2.0))


# ---------------------------------------------------------------- narration
def tts(text):
    os.makedirs(os.path.join(BUILD, 'tts'), exist_ok=True)
    key = hashlib.sha1((VOICE + '|' + text).encode()).hexdigest()[:16]
    path = os.path.join(BUILD, 'tts', key + '.wav')
    if not os.path.exists(path):
        subprocess.run([sys.executable, '-m', 'piper', '-m', VOICE, '-f', path, '--length-scale', '1.05',
                        '--sentence-silence', '0.25'], input=text.encode(), check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with wave.open(path) as w:
        rate = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return data, rate


LEAD, PAD, SCENE_GAP = 0.5, 0.7, 0.6


def build_timeline():
    """Returns list of beats with absolute timings and the narration track."""
    items, audio, rate, t = [], [], 22050, 0.0
    for si, sc in enumerate(SCENES):
        for bi, bt in enumerate(sc['beats']):
            data, rate = tts(bt.say)
            speech = len(data) / rate
            dur = LEAD + speech + PAD + bt.extra + (SCENE_GAP if bi == len(sc['beats']) - 1 else 0)
            items.append(dict(scene=si, beat=bi, start=t, dur=dur, speech=speech))
            audio.append((t + LEAD, data))
            t += dur
    total = t
    track = np.zeros(int(total * rate) + rate, dtype=np.int32)
    for st, data in audio:
        i = int(st * rate)
        track[i:i + len(data)] += data
    track = np.clip(track, -32768, 32767).astype(np.int16)
    return items, track, rate, total


# ---------------------------------------------------------------- frame rendering
TL = None


def header(cv, si, frac):
    cv.rect(0, 0, W, 118, fill=BG)
    cv.line([(0, 118), (W, 118)], LINE, 2)
    cv.circle(68, 60, 26, fill=BLUE)
    cv.text(68, 60, str(si + 1), 26, '#ffffff', 'xb', 'mm')
    cv.text(110, 60, SCENES[si]['title'], 34, INK, 'b', 'lm')
    cv.text(1860, 60, 'Using a screw gauge', 24, MUTED, 'sb', 'rm')
    n = len(SCENES)
    gw = (1800 - 8 * (n - 1)) / n
    for i in range(n):
        x = 60 + i * (gw + 8)
        cv.rect(x, 100, x + gw, 106, fill=LINE, r=3)
        f = 1 if i < si else (frac if i == si else 0)
        if f > 0:
            cv.rect(x, 100, x + gw * f, 106, fill=BLUE, r=3)


def caption(cv, text, t, speech):
    # split into sentences and show the one being spoken (timed by character count)
    parts, cur = [], ''
    for i, ch in enumerate(text):
        cur += ch
        if ch in '.!?' and (i + 1 == len(text) or text[i + 1] == ' ') and len(cur.strip()) > 25:
            parts.append(cur.strip())
            cur = ''
    if cur.strip():
        if parts and len(cur.strip()) < 25:
            parts[-1] += ' ' + cur.strip()
        else:
            parts.append(cur.strip())
    total = sum(len(p) for p in parts)
    k = clamp((t - LEAD) / max(speech, 0.1)) * total
    acc, idx = 0, 0
    for i, p in enumerate(parts):
        if k <= acc + len(p) or i == len(parts) - 1:
            idx = i
            break
        acc += len(p)
    lines = wrap(cv, parts[idx], 31, 1640)
    h = 30 + 42 * len(lines)
    y0 = 1062 - h
    cv.rect(100, y0, 1820, 1062, fill=INK, r=18, a=0.92)
    for i, ln in enumerate(lines):
        cv.text(960, y0 + 15 + 21 + 42 * i, ln, 31, '#ffffff', 'm', 'mm')


def render(fi):
    t = fi / FPS
    items = TL
    it = items[-1]
    for x in items:
        if x['start'] <= t < x['start'] + x['dur']:
            it = x
            break
    sc = SCENES[it['scene']]
    bt = sc['beats'][it['beat']]
    lt = t - it['start']
    cv = Cv()
    bt.draw(cv, lt, it['dur'])
    if bt.header:
        sstart = min(x['start'] for x in items if x['scene'] == it['scene'])
        send = max(x['start'] + x['dur'] for x in items if x['scene'] == it['scene'])
        header(cv, it['scene'], (t - sstart) / (send - sstart))
    if lt < LEAD + it['speech'] + 0.4:
        caption(cv, bt.cap, lt, it['speech'])
    # fade between scenes
    sstart = min(x['start'] for x in items if x['scene'] == it['scene'])
    send = max(x['start'] + x['dur'] for x in items if x['scene'] == it['scene'])
    fade = min(1.0, (t - sstart) / 0.35, (send - t) / 0.35)
    if fade < 1:
        cv.veil(1 - max(0.0, fade))
    return cv.frame_bytes()


def init(tl):
    global TL
    TL = tl


def main():
    args = sys.argv[1:]
    items, track, rate, total = build_timeline()
    print(f'{len(items)} beats, {total:.1f} s ({total / 60:.1f} min)')
    init(items)
    if '--preview' in args:
        step = float(args[args.index('--preview') + 1])
        only = int(args[args.index('--scene') + 1]) - 1 if '--scene' in args else None
        out = os.path.join(BUILD, 'preview')
        os.makedirs(out, exist_ok=True)
        for f in os.listdir(out):
            os.remove(os.path.join(out, f))
        for it in items:
            if only is not None and it['scene'] != only:
                continue
            tt = it['start'] + 0.05
            while tt < it['start'] + it['dur']:
                fi = int(tt * FPS)
                Image.frombytes('RGB', (W, H), render(fi)).save(
                    os.path.join(out, f'{it["scene"] + 1:02d}-{it["beat"] + 1:02d}-{fi:06d}.png'))
                tt += step
        return
    os.makedirs(BUILD, exist_ok=True)
    wav = os.path.join(BUILD, 'narration.wav')
    with wave.open(wav, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(track.tobytes())
    nframes = int(total * FPS)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart', OUT],
                          stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=init, initargs=(items,)) as pool:
        for i, fr in enumerate(pool.imap(render, range(nframes), chunksize=6)):
            ff.stdin.write(fr)
            if i % (FPS * 30) == 0:
                print(f'  {i / FPS:6.1f} / {total:.1f} s', flush=True)
    ff.stdin.close()
    ff.wait()
    print('wrote', os.path.relpath(OUT))


if __name__ == '__main__':
    main()
