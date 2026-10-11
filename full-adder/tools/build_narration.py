"""Synthesize the narration with Piper and write the timeline the animation follows.

usage: python build_narration.py <piper-binary> <voice.onnx> <work-dir>

Outputs (next to script.json):
  timeline.js     window.TIMELINE = {...}  scene/cue start times in seconds
  narration.mp3   the full voice track, already aligned to the timeline
"""
import json, os, subprocess, sys, wave

piper, voice, work = sys.argv[1:4]
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
script = json.load(open(os.path.join(root, "script.json")))
os.makedirs(work, exist_ok=True)

SCENE_PAD = 0.9   # silence at the start of each scene
CUE_GAP = 0.55    # breathing room after each line
RATE = None

def synth(cid, text):
    global RATE
    out = os.path.join(work, cid + ".wav")
    if not os.path.exists(out):
        subprocess.run([piper, "-m", voice, "-f", out, "--length-scale", "1.06",
                        "--sentence-silence", "0.3"], input=text.encode(), check=True,
                       stderr=subprocess.DEVNULL)
    with wave.open(out) as w:
        RATE = w.getframerate()
        return w.readframes(w.getnframes()), w.getnframes() / w.getframerate()

t = 0.0
scenes, pcm = [], bytearray()
def pad_to(sec):
    need = int(round(sec * RATE)) * 2 - len(pcm)
    if need > 0:
        pcm.extend(b"\0" * need)

for sc in script:
    s0 = t
    t += SCENE_PAD
    cues = []
    for c in sc["cues"]:
        audio, dur = synth(c["id"], c["text"])
        pad_to(t)
        pcm.extend(audio)
        length = max(dur + CUE_GAP, c.get("min", 0))
        cues.append({"id": c["id"], "text": c["text"], "start": round(t - s0, 3),
                     "dur": round(length, 3), "speech": round(dur, 3)})
        t += length
    scenes.append({"id": sc["id"], "title": sc["title"], "start": round(s0, 3),
                   "dur": round(t - s0, 3), "cues": cues})
t += 1.5
pad_to(t)

tl = {"total": round(t, 3), "scenes": scenes}
with open(os.path.join(root, "timeline.js"), "w") as f:
    f.write("window.TIMELINE = " + json.dumps(tl, indent=1) + ";\n")

wav = os.path.join(work, "narration.wav")
with wave.open(wav, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(bytes(pcm))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-af", "loudnorm=I=-16:TP=-1.5",
                "-ar", "44100", "-ac", "1", "-b:a", "64k", os.path.join(root, "narration.mp3")], check=True)
print(f"total {t:.1f}s, {sum(len(s['cues']) for s in scenes)} cues")
