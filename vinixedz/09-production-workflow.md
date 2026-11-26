# Editing and production workflow

## What is in the repo

```
src/vinixedz.ts               project entry (15 scenes)
src/vinixedz/script.json      SINGLE SOURCE OF TRUTH: every narration/subtitle sentence, labels, sources
src/vinixedz/sources.json     bibliography (numbers = on-screen [n])
src/vinixedz/kit.tsx          visual system: backdrop, subtitles, chapter cards, footage slots, data widgets
src/vinixedz/scenes/*.tsx     one file per scene
vinixedz/tools/audio.py       original music + SFX synthesiser
vinixedz/tools/post.py        render log → SRT, timing, footage list, audio, MP4
vinixedz/tools/docs.py        script.json → narration, subtitle sheet, storyboard, bibliography
vinixedz/0x-*.md              research and production documents
```

## Step 1: verify the data (before anything is public)

1. Confirm the exact channel URL for each of the six names, especially Fictic and 10Mov (research report §0).
2. Re-check every third-party figure on its live page and update `script.json` and the `PROFILES` / `PANELS` constants in `s08_creators.tsx` and `s11_numbers.tsx` if anything changed. Keep the source and date with every number.
3. Optional: collect the data for the deferred charts (`06-data-visualization-spec.md` §B).

## Step 2: record the voice-over

- Read from `04-narration.md`. The sentences are identical to the on-screen subtitles.
- Record in one quiet room, about 20–30 cm from the mic. Leave about 1 s of silence between sentences, which makes editing easy.
- Do not try to match the subtitle timing; the subtitles are placeholders.

## Step 3: fit picture and voice

You have two options:
- **A. Keep the rendered picture.** Lay your voice-over on the timeline and nudge sentences so each starts near its subtitle card (the `Shown at` column in `05-subtitles.md`). Where your read runs long, use freeze-frames or a 2–5% slow-down on that section. Where it runs short, leave the extra air for the music.
- **B. Re-time the source (most precise).** In `kit.tsx`, `holdFor(text)` decides how long each card stays up. Replace it with a lookup of your actual sentence durations (for example, from your DAW's region list), re-render, and the visuals re-time automatically, because every animation waits on `nar.at(i)`. Then run `post.py` again to regenerate the SRT, the timing table and the audio cue placement.

## Step 4: replace the footage slots

- Use `07-footage-and-archival.md` for what goes where, with first timecodes.
- In Premiere or Resolve: place the clip above the video, scale and position it to the slot's frame, and add a 14 px corner radius mask. For a parallax feel, add a gentle 102% → 100% scale over the clip's duration.
- In After Effects: import the MP4, set the slot frames as track mattes (draw a shape layer over the slot area), and parent each clip to a null if the slot moves.

## Step 5: subtitles

- **Burnt-in placeholders:** the rendered MP4 already shows the bottom subtitle cards. For the final upload you will probably want to **remove** them (your voice is now the narration) or keep them as an accessibility layer.
- **To get a clean picture without subtitles:** in `kit.tsx → narration()`, set the bar and pill opacity to 0 (keep the timing logic), re-render, and upload `05-subtitles.srt` to YouTube as closed captions. Edit the SRT text if your read differs.

## Step 6: rebuild or extend in After Effects (optional)

Every scene in `03-script-and-storyboard.md` has motion notes written in AE terms. A good split:
- Keep the rendered data and graphics plates as-is.
- Composite creator footage and your own screen recordings in AE.
- Rebuild only the showcase layer stack (Scene 9) as real 3D layers if you want true camera depth of field.

## Rendering and assembly commands

```bash
npm install
```

```bash
npm start
```

Open `http://localhost:9000/src/vinixedz` and press **RENDER**. The frames go to `output/vinixedz-the-standard-moved/`.

To capture the render log needed by `post.py`, render headlessly with the Playwright helper used for this build (`vinixedz/tools/render.cjs`; run it while `npm start` is serving: `node vinixedz/tools/render.cjs render.log`). Alternatively, copy the editor's browser console lines that start with `VNX|` into a file.

```bash
python3 vinixedz/tools/post.py render.log output/vinixedz-the-standard-moved vinixedz/build
```

```bash
python3 vinixedz/tools/docs.py vinixedz/build/timing.json
```

## Step 7: final mix and export

- Voice at about −16 LUFS; music ducked 6–9 dB under the voice; master at −14 LUFS integrated, −1 dBTP (see `08-sound-design.md`).
- Export H.264 at 1080p30, 16–20 Mbps, or 4K if you rebuild at a higher resolution (raise `size` in `src/vinixedz.meta` to 3840×2160 and re-render; everything is vector).

## Step 8: publishing checklist

- [ ] Every number re-verified with its date, and the sources listed in the description (copy from `02-bibliography.md`).
- [ ] Every creator clip credited on screen; creators notified.
- [ ] No ranking language in the title, thumbnail or description that the film itself does not support.
- [ ] Captions uploaded (SRT).
- [ ] Chapters in the description, using the scene start times from `03-script-and-storyboard.md`.
