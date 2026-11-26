#!/usr/bin/env python3
"""Original score + sound design for 'THE STANDARD MOVED'.

Everything here is synthesised from scratch with numpy (no samples, no
third-party audio), so the soundtrack is original and free of licensing
issues.  Music sections and sound-effect cues are placed from the render
log written by the Canvas Commons scenes (lines starting with VNX|...).

Usage:
    python3 audio.py render.log out_dir [total_frames]
Writes out_dir/music.wav, out_dir/sfx.wav and out_dir/mix.wav (44.1 kHz stereo).
"""
import sys
import wave
from pathlib import Path

import numpy as np

SR = 44100
FPS = 30
BPM = 92.0
BEAT = 60.0 / BPM
rng = np.random.default_rng(1234)


# ------------------------------------------------------------------ utils
def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def t_axis(n):
    return np.arange(n, dtype=np.float64) / SR


def env_adsr(n, a, d, s, r):
    e = np.ones(n) * s
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    A = min(A, n)
    e[:A] = np.linspace(0, 1, A, endpoint=False) if A else e[:A]
    D2 = min(D, max(0, n - A))
    if D2:
        e[A:A + D2] = np.linspace(1, s, D2, endpoint=False)
    R2 = min(R, n)
    if R2:
        e[n - R2:] *= np.linspace(1, 0, R2)
    return e


def fft_filter(x, lo=None, hi=None):
    """Brick-ish band-pass with soft edges, in the frequency domain."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.ones_like(f)
    if lo:
        g *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** 4)
    if hi:
        g *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * g, n)


def stereo(x, pan=0.0):
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    return np.stack([x * l, x * r], axis=1)


def reverb(x, secs=2.4, mix=0.3, seed=7):
    """Cheap convolution reverb with a decaying-noise impulse (per channel)."""
    g = np.random.default_rng(seed)
    n_ir = int(secs * SR)
    tt = t_axis(n_ir)
    out = np.zeros((len(x) + n_ir, 2))
    for ch in range(2):
        ir = g.standard_normal(n_ir) * np.exp(-tt * 3.2 / secs)
        ir = fft_filter(ir, lo=180, hi=6500)
        ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
        src = x[:, ch]
        N = 1 << int(np.ceil(np.log2(len(src) + n_ir)))
        y = np.fft.irfft(np.fft.rfft(src, N) * np.fft.rfft(ir, N), N)[: len(src) + n_ir]
        out[:, ch] = y
    dry = np.zeros_like(out)
    dry[: len(x)] = x
    return dry * (1 - mix) + out * mix


def saw(freq, n, harmonics=10, detune_cents=0.0, phase=0.0):
    tt = t_axis(n)
    f = freq * 2 ** (detune_cents / 1200)
    y = np.zeros(n)
    for k in range(1, harmonics + 1):
        if f * k > SR / 2 - 500:
            break
        y += np.sin(2 * np.pi * f * k * tt + phase * k) / k
    return y


# ------------------------------------------------------------- instruments
def pad_block(notes, n, bright=6, level=0.11):
    y = np.zeros(n)
    for i, m in enumerate(notes):
        for dc in (-7, 0, 6):
            y += saw(midi(m), n, harmonics=bright, detune_cents=dc, phase=rng.random() * 6.28)
    y *= level / (len(notes) * 3)
    y *= env_adsr(n, 1.2, 0.5, 1.0, 1.2)
    return y


def pluck(m, dur, level=0.18, bright=1.0):
    n = int(dur * SR)
    tt = t_axis(n)
    f = midi(m)
    y = (np.sin(2 * np.pi * f * tt) + 0.35 * bright * np.sin(2 * np.pi * 2 * f * tt)
         + 0.12 * bright * np.sin(2 * np.pi * 3 * f * tt))
    return y * np.exp(-tt * 5.5) * level * env_adsr(n, 0.004, 0, 1, 0.05)


def kick(level=0.55):
    n = int(0.45 * SR)
    tt = t_axis(n)
    f = 42 + 90 * np.exp(-tt * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-tt * 7) * level


def hat(level=0.06):
    n = int(0.07 * SR)
    x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))
    return x * np.exp(-t_axis(n) * 60) * level


def sub_pulse(m, n, level=0.22, rate=1.0):
    """Heartbeat-like sub bass pulse on every beat."""
    tt = t_axis(n)
    y = np.sin(2 * np.pi * midi(m) * tt)
    beat_t = (tt % (BEAT / rate))
    e = np.exp(-beat_t * 6.5)
    return y * e * level


# --------------------------------------------------------------- moods
PROG = {
    'minor': [[50, 53, 57, 62], [46, 50, 53, 58], [41, 45, 48, 57], [48, 52, 55, 60]],   # Dm Bb F C
    'nostalgic': [[46, 50, 53, 57], [41, 45, 48, 52], [48, 52, 55, 59], [50, 53, 57, 60]],
    'reflect': [[50, 53, 57, 62], [43, 46, 50, 55], [46, 50, 53, 58], [45, 49, 52, 57]],  # Dm Gm Bb A
}

MOOD = {
    's01_hook': dict(prog='minor', pad=0.9, sub=1.0, arp=0.0, kick=0, hat=0, bright=4),
    's02_title': dict(prog='minor', pad=1.0, sub=0.7, arp=0.0, kick=0, hat=0, bright=6),
    's03_rules': dict(prog='minor', pad=0.7, sub=0.0, arp=0.5, kick=0, hat=0, bright=5),
    's04_history': dict(prog='nostalgic', pad=0.8, sub=0.0, arp=0.8, kick=0, hat=0, bright=4),
    's05_vertical': dict(prog='nostalgic', pad=0.7, sub=0.5, arp=0.8, kick=1, hat=0, bright=6),
    's06_grammar': dict(prog='minor', pad=0.5, sub=0.0, arp=0.9, kick=0, hat=1, bright=5),
    's07_stage': dict(prog='minor', pad=0.7, sub=0.6, arp=0.6, kick=1, hat=1, bright=6),
    's08_creators': dict(prog='minor', pad=0.7, sub=0.8, arp=0.9, kick=2, hat=1, bright=7),
    's09_anatomy': dict(prog='minor', pad=0.8, sub=0.8, arp=1.0, kick=2, hat=1, bright=8),
    's10_compare': dict(prog='minor', pad=0.7, sub=0.8, arp=0.9, kick=2, hat=1, bright=7),
    's11_numbers': dict(prog='minor', pad=0.5, sub=0.0, arp=0.6, kick=0, hat=1, bright=4),
    's12_why': dict(prog='minor', pad=0.9, sub=0.7, arp=0.8, kick=1, hat=1, bright=7),
    's13_ceiling': dict(prog='reflect', pad=0.8, sub=0.0, arp=0.5, kick=0, hat=0, bright=4),
    's14_future': dict(prog='reflect', pad=0.9, sub=0.4, arp=0.4, kick=0, hat=0, bright=3),
    's15_end': dict(prog='reflect', pad=1.0, sub=0.6, arp=0.7, kick=1, hat=0, bright=6),
}


def section(scene, n, offset_beats=0):
    """Render one scene's music bed, length n samples (mono L/R pair)."""
    mood = MOOD[scene]
    prog = PROG[mood['prog']]
    bar = 4 * BEAT
    chord_len = 2 * bar
    out = np.zeros((n, 2))
    nch = int(np.ceil(n / (chord_len * SR))) + 1
    # pad + sub
    for c in range(nch):
        s0 = int(c * chord_len * SR)
        if s0 >= n:
            break
        blk = int((chord_len + 1.2) * SR)
        notes = prog[c % len(prog)]
        if mood['pad']:
            p = pad_block(notes, blk, bright=mood['bright'], level=0.10 * mood['pad'])
            l = pad_block([m + 12 for m in notes[1:3]], blk, bright=3, level=0.035 * mood['pad'])
            seg = np.stack([p * 0.9 + l * 0.6, p * 0.7 + l * 0.9], axis=1)
        else:
            seg = np.zeros((blk, 2))
        if mood['sub']:
            if scene in ('s01_hook', 's02_title'):
                sp = sub_pulse(notes[0] - 12, blk, level=0.20 * mood['sub'])
                sp *= env_adsr(blk, 0.3, 0, 1, 1.0)
            else:
                # sustained, softly breathing bass under the later chapters
                sp = np.sin(2 * np.pi * midi(notes[0] - 12) * t_axis(blk))
                sp *= env_adsr(blk, 0.8, 0, 1, 1.0) * 0.11 * mood['sub']
            seg += stereo(sp)
        e = min(n, s0 + blk)
        out[s0:e] += seg[: e - s0]
    # arpeggio (8ths)
    if mood['arp']:
        step = BEAT / 2
        k = 0
        while True:
            t0 = k * step
            s0 = int(t0 * SR)
            if s0 >= n:
                break
            c = int(t0 // chord_len)
            notes = prog[c % len(prog)]
            pattern = [0, 2, 1, 3, 2, 1, 3, 2]
            m = notes[pattern[k % 8]] + 12
            if mood['arp'] < 0.7 and k % 2:
                k += 1
                continue
            pl = pluck(m, 0.9, level=0.09 * mood['arp'], bright=mood['bright'] / 6)
            e = min(n, s0 + len(pl))
            out[s0:e] += stereo(pl[: e - s0], pan=0.35 if k % 2 else -0.35)
            k += 1
    # drums
    if mood['kick'] or mood['hat']:
        beat_n = int(n / (BEAT * SR)) + 1
        for b in range(beat_n):
            s0 = int(b * BEAT * SR)
            if mood['kick'] == 1 and b % 2 == 0 or mood['kick'] == 2:
                kk = kick(0.38 if mood['kick'] == 2 else 0.3)
                e = min(n, s0 + len(kk))
                out[s0:e] += stereo(kk[: e - s0])
            if mood['hat']:
                for off in (0.5,) if mood['hat'] == 1 else (0.25, 0.5, 0.75):
                    h0 = s0 + int(off * BEAT * SR)
                    hh = hat()
                    e = min(n, h0 + len(hh))
                    if h0 < n:
                        out[h0:e] += stereo(hh[: e - h0], pan=0.25)
    return out


# --------------------------------------------------------------- sfx
def sfx_whoosh(big=False):
    d = 1.15 if big else 0.6
    n = int(d * SR)
    tt = t_axis(n)
    x = fft_filter(rng.standard_normal(n), lo=250 if not big else 120, hi=5000)
    e = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 2
    pan = np.linspace(-0.8, 0.8, n)
    y = x * e * (0.22 if big else 0.16)
    out = np.stack([y * np.cos((pan + 1) * np.pi / 4), y * np.sin((pan + 1) * np.pi / 4)], axis=1)
    if big:
        f = 120 * np.exp(-tt * 2.5) + 40
        out += stereo(np.sin(2 * np.pi * np.cumsum(f) / SR) * e * 0.22)
    return out


def sfx_impact():
    n = int(2.2 * SR)
    tt = t_axis(n)
    f = 38 + 50 * np.exp(-tt * 9)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.6) * 0.6
    nz = fft_filter(rng.standard_normal(n), hi=2200) * np.exp(-tt * 14) * 0.35
    return reverb(stereo(body + nz), secs=2.0, mix=0.25)[:n]


def sfx_sub():
    n = int(1.8 * SR)
    tt = t_axis(n)
    return stereo(np.sin(2 * np.pi * 44 * tt) * np.exp(-tt * 2.2) * env_adsr(n, 0.05, 0, 1, 0.3) * 0.5)


def sfx_tick():
    n = int(0.03 * SR)
    tt = t_axis(n)
    return stereo(np.sin(2 * np.pi * 2600 * tt) * np.exp(-tt * 260) * 0.14, pan=0.1)


def sfx_blip():
    n = int(0.12 * SR)
    tt = t_axis(n)
    f = np.linspace(1150, 1700, n)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 30) * 0.15
    return reverb(stereo(y), secs=0.6, mix=0.2)[: int(0.5 * SR)]


def sfx_pop():
    n = int(0.09 * SR)
    tt = t_axis(n)
    f = np.linspace(700, 260, n)
    return stereo(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 40) * 0.2)


def sfx_riser(d):
    d = max(0.6, d)
    n = int(d * SR)
    tt = t_axis(n)
    k = tt / d
    nz = fft_filter(rng.standard_normal(n), lo=400, hi=9000) * (k ** 2) * 0.12
    f = 200 + 900 * k ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * (k ** 2) * 0.06
    return stereo(nz + tone)


def sfx_glitch():
    n = int(0.22 * SR)
    tt = t_axis(n)
    sq = np.sign(np.sin(2 * np.pi * 180 * tt)) * (rng.random(n) > 0.4)
    sq = np.round(sq * 4) / 4
    return stereo(sq * 0.08 * env_adsr(n, 0.002, 0, 1, 0.05), pan=-0.2)


def sfx_count(d):
    d = max(0.3, d)
    n = int(d * SR)
    out = np.zeros((n, 2))
    t = 0.0
    i = 0
    while t < d:
        s0 = int(t * SR)
        m = int(0.02 * SR)
        tt = t_axis(m)
        f = 1800 + 900 * (t / d)
        y = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 300) * 0.07
        e = min(n, s0 + m)
        out[s0:e] += stereo(y[: e - s0], pan=0.2 if i % 2 else -0.2)
        t += 0.035 + 0.08 * (t / d) ** 2  # slows down like an easing counter
        i += 1
    return out


def sfx_shutter():
    n = int(0.35 * SR)
    tt = t_axis(n)
    y = fft_filter(rng.standard_normal(n), lo=800) * np.exp(-tt * 50) * 0.25
    y += np.sin(2 * np.pi * 90 * tt) * np.exp(-tt * 18) * 0.35
    return stereo(y)


def sfx_swell(d):
    d = max(1.0, d)
    n = int(d * SR)
    tt = t_axis(n)
    k = tt / d
    x = fft_filter(rng.standard_normal(n), lo=200, hi=3000) * k ** 3 * 0.07
    tone = (np.sin(2 * np.pi * midi(62) * tt) + np.sin(2 * np.pi * midi(69) * tt)) * k ** 2 * 0.04
    return stereo(x + tone)


def make_sfx(kind, dur):
    return {
        'whoosh': lambda: sfx_whoosh(False),
        'whooshBig': lambda: sfx_whoosh(True),
        'impact': sfx_impact,
        'sub': sfx_sub,
        'tick': sfx_tick,
        'blip': sfx_blip,
        'pop': sfx_pop,
        'riser': lambda: sfx_riser(dur),
        'glitch': sfx_glitch,
        'count': lambda: sfx_count(dur),
        'shutter': sfx_shutter,
        'swell': lambda: sfx_swell(dur),
    }[kind]()


# --------------------------------------------------------------- io
def write_wav(path, x):
    x = np.clip(x, -1, 1)
    pcm = (x * 32767).astype('<i2')
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def parse_log(path):
    scenes, cues = [], []
    seen = set()
    for line in Path(path).read_text().splitlines():
        if line in seen:  # the renderer may re-run frames; log lines repeat
            continue
        seen.add(line)
        p = line.split('|')
        if len(p) < 4 or p[0] != 'VNX':
            continue
        kind, frame = p[1], int(p[2])
        if kind == 'SCENE':
            scenes.append((frame, p[3]))
        elif kind == 'SFX':
            cues.append((frame, p[3], float(p[4]) if len(p) > 4 and p[4] else 0.0))
    scenes.sort()
    cues.sort()
    return scenes, cues


def main():
    log, out_dir = sys.argv[1], Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    scenes, cues = parse_log(log)
    total_frames = int(sys.argv[3]) if len(sys.argv) > 3 else max(f for f, _ in scenes) + 30 * 20
    n_total = int(total_frames / FPS * SR) + SR
    music = np.zeros((n_total, 2), dtype=np.float64)

    # music beds with crossfades at scene boundaries
    bounds = [f for f, _ in scenes] + [total_frames]
    for i, (f0, name) in enumerate(scenes):
        s0 = int(f0 / FPS * SR)
        s1 = int(bounds[i + 1] / FPS * SR)
        tail = int(2.5 * SR)
        n = s1 - s0 + tail
        if name not in MOOD:
            continue
        print(f'music {name}: {(s1 - s0) / SR:.1f}s', flush=True)
        seg = section(name, n)
        fade_in = int(1.5 * SR) if i else int(3.0 * SR)
        seg[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
        seg[-tail:] *= np.linspace(1, 0, tail)[:, None]
        if i == len(scenes) - 1:
            # final scene: long fade to silence at the very end
            fl = int(6 * SR)
            end = s1 - s0
            seg[end - fl:end] *= np.linspace(1, 0, fl)[:, None]
            seg[end:] = 0
        e = min(n_total, s0 + n)
        music[s0:e] += seg[: e - s0]
    print('reverb on music…', flush=True)
    # reverb in chunks to bound memory
    wet = np.zeros_like(music)
    chunk = SR * 60
    for c0 in range(0, n_total, chunk):
        blk = music[c0:c0 + chunk]
        r = reverb(blk, secs=2.8, mix=0.35, seed=c0 // chunk)
        e = min(n_total, c0 + len(r))
        wet[c0:e] += r[: e - c0]
    music = wet

    sfx = np.zeros((n_total, 2))
    for f, kind, dur in cues:
        s0 = int(f / FPS * SR)
        x = make_sfx(kind, dur)
        e = min(n_total, s0 + len(x))
        sfx[s0:e] += x[: e - s0]
    print(f'{len(cues)} sound cues placed', flush=True)

    # gentle soft-clip limiter
    def norm(x, peak):
        m = np.max(np.abs(x)) + 1e-9
        return x * (peak / m)

    def rms_to(x, target_db):
        r = np.sqrt(np.mean(x ** 2)) + 1e-12
        return x * (10 ** (target_db / 20) / r)

    def limit(x, ceiling=0.89, block=256):
        """Block peak limiter with smoothed gain (no look-ahead clicks)."""
        n = len(x) // block * block
        pk = np.abs(x[:n]).max(axis=1).reshape(-1, block).max(axis=1)
        g = np.minimum(1.0, ceiling / np.maximum(pk, 1e-9))
        # hold the lowest gain over neighbouring blocks, then smooth (attack/release)
        k = 8
        gp = np.pad(g, (k, k), mode='edge')
        g = np.min(np.stack([gp[i:i + len(g)] for i in range(2 * k + 1)]), axis=0)
        ker = np.hanning(2 * k + 1)
        ker /= ker.sum()
        g = np.convolve(np.pad(g, (k, k), mode='edge'), ker, mode='valid')
        gs = np.repeat(g, block)
        y = x.copy()
        y[:n] *= gs[:, None]
        return np.clip(y, -ceiling, ceiling)

    music = limit(rms_to(music, -22), 0.6)
    sfx = limit(rms_to(sfx, -24), 0.8)
    mix = limit(rms_to(music + sfx, -17.5), 0.84)
    write_wav(out_dir / 'music.wav', music)
    write_wav(out_dir / 'sfx.wav', sfx)
    write_wav(out_dir / 'mix.wav', mix)
    print('done', n_total / SR, 'seconds')


if __name__ == '__main__':
    main()
