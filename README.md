# How a Refrigerator Works – animated explainer

An ~11.5-minute animated lesson built with [Canvas Commons](https://canvascommons.io/) that explains the vapour-compression refrigeration cycle, with built-in "pause & think" quizzes and a final 6-question test.

**Video:** [`video/how-a-refrigerator-works.mp4`](video/how-a-refrigerator-works.mp4) (1920×1080, 30 fps, no audio)

## Contents
1. Intro – heat flows hot → cold by itself; a fridge moves it the other way using work
2. The sealed loop and its 4 parts, high- vs low-pressure sides, liquid/gas key
3. Evaporator · 4. Compressor · 5. Condenser · 6. Expansion valve (each with pressure/temperature meters and a quiz)
7. Energy balance: Qout = Qin + Win, COP
8. Myth buster: why an open fridge door warms the kitchen
9. Final test + summary

## Editing / re-rendering
```bash
npm install
npm start          # opens the Canvas Commons editor at http://localhost:9000
```
Press **RENDER** in the editor (image sequence → `output/`), then:
```bash
ffmpeg -framerate 30 -i output/how-a-refrigerator-works/%06d.jpeg \
  -c:v libx264 -crf 22 -pix_fmt yuv420p video/how-a-refrigerator-works.mp4
```

---

# Build a Full Adder – narrated explainer + virtual trainer kit

A ~12-minute narrated lesson that starts from adding numbers by hand and ends with a working full adder (7486 XOR, 7408 AND, 7432 OR) on a breadboard trainer kit. The big idea: **a full adder counts how many of its three inputs are on.** Sum = odd count, Carry = two or more.

**Video:** [`video/full-adder-explained.mp4`](video/full-adder-explained.mp4) (1920×1080, 30 fps, male voice narration (Piper "ryan"), burned-in captions)

**Interactive page:** [`full-adder/index.html`](full-adder/index.html) has the same video in a player with chapters, a clickable virtual kit (flip A/B/Cin and watch the wires glow), a 20-wire checklist, the truth table and the pinout.

Chapters: adding one column · binary · count the ones · gates as tiny judges · building Sum · building Carry · full circuit through all 8 inputs · the trainer kit · how a breadboard connects · the three chips & pinout · 7 build steps · power-on test · troubleshooting · recap & 4-bit ripple adder.

## Re-generating
Plain canvas + JS, no build step. The narration text lives in `full-adder/script.json`.
```bash
# 1. narration (Piper TTS) -> timeline.js + narration.mp3
pip install piper-tts   # plus the voice en_US-ryan-high.onnx (rhasspy/piper-voices)
python full-adder/tools/build_narration.py $(which piper) en_US-ryan-high.onnx /tmp/cues
# 2. frames -> MP4 (headless Chromium via Playwright, ffmpeg)
node full-adder/tools/render.cjs video/full-adder-explained.mp4 3 30
# stills for checking: node full-adder/tools/snap.cjs /tmp/snaps 120 300
```
