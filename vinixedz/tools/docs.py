#!/usr/bin/env python3
"""Generate the bibliography, narration script and subtitle sheet from the
single source of truth (src/vinixedz/script.json + sources.json), so the
on-screen text, the narration and the documents can never drift apart.

    python3 vinixedz/tools/docs.py [timing.json]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'vinixedz'
script = json.loads((ROOT / 'src/vinixedz/script.json').read_text())
sources = json.loads((ROOT / 'src/vinixedz/sources.json').read_text())
num = {s['key']: i + 1 for i, s in enumerate(sources)}
timing = None
if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
    timing = {s['id']: s for s in json.loads(Path(sys.argv[1]).read_text())['scenes']}


def chapter_title(s):
    if s['chapter']:
        return f"Chapter {s['chapter']['n']}: {s['chapter']['title'].title()}"
    return s['name']


# ---------------------------------------------------------------- bibliography
used = {}
for s in script['scenes']:
    for i, l in enumerate(s['lines']):
        for k in l.get('src', []):
            used.setdefault(k, []).append(f"{s['id']} line {i + 1}")
b = ['# Bibliography', '',
     'Numbers match the `[n]` references in the on-screen source pills and in the research report.',
     'Access: November 2026, through search-engine indexes. YouTube, Social Blade and vidIQ pages could not be opened directly from the research environment (see the research report, §0).',
     'Third-party analytics (vidIQ, Social Blade, SponsorRadar, InfluencerMetric) are **snapshots** and disagree with each other. Re-check them before publishing.', '']
for i, s in enumerate(sources, 1):
    where = '; '.join(used.get(s['key'], [])) or 'research report only'
    b.append(f"{i}. **{s['title']}**  \n   <{s['url']}>  \n   _Type:_ {s['type']} · _Used in:_ {where}")
(OUT / '02-bibliography.md').write_text('\n'.join(b) + '\n')

# ---------------------------------------------------------------- narration
n = ['# Narration script (for your own voice-over recording)', '',
     'These are the **same sentences, in the same order**, as the bottom subtitles in the video.',
     'They are written for natural reading, not for any particular speed. Record freely, then retime the',
     'picture or the subtitles to your take. Labels in brackets are **not** read aloud; they show which',
     'evidence label appears on screen with that sentence.', '']
k = 0
for s in script['scenes']:
    head = chapter_title(s)
    if timing and s['id'] in timing:
        head += f"  ·  ({timing[s['id']]['start']}–{timing[s['id']]['end']})"
    n += [f'## {head}', '']
    for l in s['lines']:
        k += 1
        tag = f" _[{l['tag']}{' ' + ''.join(f'[{num[x]}]' for x in l.get('src', [])) if l.get('src') else ''}]_" if l.get('tag') else ''
        n.append(f"{k}. {l['text']}{tag}")
    n.append('')
words = sum(len(l['text'].split()) for s in script['scenes'] for l in s['lines'])
n += ['---', f'{k} sentences · {words} words. At a relaxed documentary pace (130–150 words per minute), the read takes about {words / 150:.0f}–{words / 130:.0f} minutes.']
(OUT / '04-narration.md').write_text('\n'.join(n) + '\n')

# ---------------------------------------------------------------- subtitle sheet
t = ['# Bottom subtitles, sentence by sentence', '',
     'One sentence per card, shown for a few seconds each; not word-by-word captions. The timed version is `05-subtitles.srt`.', '',
     '| # | Scene | Shown at | Subtitle | Label |', '|---|---|---|---|---|']
k = 0
for s in script['scenes']:
    tl = {x['i']: x['start'] for x in timing[s['id']]['lines']} if timing and s['id'] in timing else {}
    for i, l in enumerate(s['lines']):
        k += 1
        t.append(f"| {k} | {s['id']} | {tl.get(i, '')} | {l['text']} | {l.get('tag', '')} |")
(OUT / '05-subtitles.md').write_text('\n'.join(t) + '\n')
print('ok', k, 'sentences')

# ---------------------------------------------------------------- storyboard
tpl = (Path(__file__).parent / 'storyboard_template.md').read_text()
k = 0
for s in script['scenes']:
    rows = []
    for i, l in enumerate(s['lines']):
        k += 1
        at = ''
        if timing and s['id'] in timing:
            at = next((f" `{x['start']}`" for x in timing[s['id']]['lines'] if x['i'] == i), '')
        tag = f" — *{l['tag']}*" if l.get('tag') else ''
        rows.append(f"{k}.{at} {l['text']}{tag}")
    tpl = tpl.replace('{{LINES:%s}}' % s['id'], '\n'.join(rows))
    dur = 'duration: see timing.json'
    if timing and s['id'] in timing:
        t = timing[s['id']]
        dur = f"{t['start']}–{t['end']} ({t['seconds']} s)"
    tpl = tpl.replace('{{DUR:%s}}' % s['id'], dur)
if timing:
    tot = json.loads(Path(sys.argv[1]).read_text())['total_seconds']
    tpl = tpl.replace('{{TOTAL}}', f"{int(tot // 60)} min {tot % 60:.0f} s")
else:
    tpl = tpl.replace('{{TOTAL}}', 'about 16 minutes')
(OUT / '03-script-and-storyboard.md').write_text(tpl)
print('storyboard ok')

# ---------------------------------------------------------------- footage list
ft = (Path(__file__).parent / 'footage_template.md').read_text()
slots = ROOT / 'vinixedz/build/footage_slots.md'
ft = ft.replace('{{SLOTS}}', slots.read_text() if slots.exists() else '_Run post.py to generate the slot table._')
(OUT / '07-footage-and-archival.md').write_text(ft)
print('footage ok')
