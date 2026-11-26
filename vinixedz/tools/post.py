#!/usr/bin/env python3
"""Turn the render log into subtitles, timing tables and the final video.

    python3 vinixedz/tools/post.py <render.log> <frames_dir> <out_dir>

Produces in out_dir:
  subtitles.srt            bottom narration placeholder, sentence by sentence
  timing.json              scene start/end and per-sentence timecodes
  footage_slots.md         every footage slot with its on-screen timecode
  music.wav / sfx.wav / mix.wav  (via audio.py)
  the-standard-moved.mp4   1920x1080, 30 fps, H.264 + AAC
  the-standard-moved_nosubs-reference.txt  note on how subtitles are burnt in
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FPS = 30


def tc(frame, srt=True):
    s = frame / FPS
    h, m = int(s // 3600), int(s % 3600 // 60)
    sec = s % 60
    if srt:
        return f'{h:02d}:{m:02d}:{int(sec):02d},{int(round((sec % 1) * 1000)):03d}'.replace(',1000', ',999')
    return f'{m:02d}:{sec:05.2f}' if h == 0 else f'{h}:{m:02d}:{sec:05.2f}'


def main():
    log, frames_dir, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    script = json.loads((ROOT / 'src/vinixedz/script.json').read_text())
    lines = {}
    for s in script['scenes']:
        for i, l in enumerate(s['lines']):
            lines[(s['id'], i)] = l

    seen, ev = set(), []
    for raw in log.read_text().splitlines():
        if raw in seen or not raw.startswith('VNX|'):
            continue
        seen.add(raw)
        p = raw.split('|')
        ev.append((int(p[2]), p[1], p[3:]))
    ev.sort(key=lambda e: e[0])
    total = len(list(frames_dir.glob('*.jpeg')))

    # ---- subtitles
    start, end = {}, {}
    for f, kind, args in ev:
        if kind == 'SUB':
            start.setdefault((args[0], int(args[1])), f)
        elif kind == 'SUBEND':
            end.setdefault((args[0], int(args[1])), f)
    keys = sorted(start, key=lambda k: start[k])
    missing = [k for k in lines if k not in start]
    if missing:
        print('WARNING: lines never shown:', missing)
    srt = []
    for n, k in enumerate(keys, 1):
        a, b = start[k], end.get(k, start[k] + 4 * FPS)
        srt.append(f'{n}\n{tc(a)} --> {tc(b)}\n{lines[k]["text"]}\n')
    (out / 'subtitles.srt').write_text('\n'.join(srt), encoding='utf-8')

    # ---- scene timing
    scenes = []
    sc = [(f, a[0]) for f, k, a in ev if k == 'SCENE']
    dedup = []
    for f, name in sc:
        if not dedup or dedup[-1][1] != name:
            dedup.append((f, name))
    for i, (f, name) in enumerate(dedup):
        nxt = dedup[i + 1][0] if i + 1 < len(dedup) else total
        meta = next(s for s in script['scenes'] if s['id'] == name)
        scenes.append({
            'id': name,
            'name': meta['name'],
            'chapter': meta['chapter'],
            'start': tc(f, False),
            'end': tc(nxt, False),
            'seconds': round((nxt - f) / FPS, 1),
            'lines': [
                {'i': i2, 'start': tc(start[(name, i2)], False), 'text': l['text'], 'tag': l.get('tag')}
                for i2, l in enumerate(meta['lines']) if (name, i2) in start
            ],
        })
    (out / 'timing.json').write_text(json.dumps({'total_seconds': round(total / FPS, 2), 'scenes': scenes}, indent=2, ensure_ascii=False))

    # ---- footage slots
    rows = ['| Slot | First on screen | What to insert |', '|---|---|---|']
    for f, kind, args in ev:
        if kind == 'SLOT':
            rows.append(f'| {args[0]} | {tc(f, False)} | {args[1]} |')
    (out / 'footage_slots.md').write_text('\n'.join(rows) + '\n')

    # ---- audio
    subprocess.run([sys.executable, str(HERE / 'audio.py'), str(log), str(out), str(total)], check=True)

    # ---- mux
    mp4 = out / 'the-standard-moved.mp4'
    subprocess.run([
        'ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(frames_dir / '%06d.jpeg'),
        '-i', str(out / 'mix.wav'), '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-tune', 'animation',
        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', str(mp4),
    ], check=True)
    # compact stems for sharing (the WAVs stay local; GitHub limits file size)
    for stem in ('music', 'sfx'):
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(out / f'{stem}.wav'), '-c:a', 'aac',
                        '-b:a', '192k', str(out / f'{stem}_stem.m4a')], check=True)
    print('wrote', mp4, f'{total / FPS:.1f}s')


if __name__ == '__main__':
    main()
