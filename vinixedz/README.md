# VINIXEDZ: "THE STANDARD MOVED"

*How a new generation of editors captured the community's attention, and what really changed.*

A long-form, investigative motion-graphics documentary (about 16 minutes, 1920×1080, 30 fps). It has **no voice-over and no synthetic speech**. A narration placeholder runs as one-sentence bottom subtitles, so you can record your own voice. The soundtrack is an original score with synthesised sound design.

## Deliverables

| # | Deliverable | File |
|---|---|---|
| 1 | Research report (verified / observed / hypothesis / speculation) | [`01-research-report.md`](01-research-report.md) |
| 2 | Bibliography with direct links (numbers match on-screen `[n]`) | [`02-bibliography.md`](02-bibliography.md) |
| 3 | Final title, alternative titles, thumbnail direction | [`03-script-and-storyboard.md`](03-script-and-storyboard.md) (top) |
| 4 | Full documentary script | [`03-script-and-storyboard.md`](03-script-and-storyboard.md) |
| 5 | Complete narration text | [`04-narration.md`](04-narration.md) |
| 6 | Bottom-subtitle text, sentence by sentence (plus timed SRT matching the render) | [`05-subtitles.md`](05-subtitles.md), [`05-subtitles.srt`](05-subtitles.srt) |
| 7 | Scene-by-scene storyboard | [`03-script-and-storyboard.md`](03-script-and-storyboard.md) |
| 8 | Motion-graphics instructions for every scene | [`03-script-and-storyboard.md`](03-script-and-storyboard.md) |
| 9 | Animation and transition descriptions | [`03-script-and-storyboard.md`](03-script-and-storyboard.md) |
| 10 | Statistical visualization specifications | [`06-data-visualization-spec.md`](06-data-visualization-spec.md) |
| 11 | Suggested footage and archival material (with slot timecodes) | [`07-footage-and-archival.md`](07-footage-and-archival.md) |
| 12 | Sound-design plan | [`08-sound-design.md`](08-sound-design.md) |
| 13 | Estimated duration of each scene | [`03-script-and-storyboard.md`](03-script-and-storyboard.md) (measured from the render), `build/timing.json` |
| 14 | Editing and production workflow | [`09-production-workflow.md`](09-production-workflow.md) |
| — | Rendered documentary (music, SFX, subtitle placeholders, footage slots) | [`../video/vinixedz-the-standard-moved.mp4`](../video/vinixedz-the-standard-moved.mp4) |
| — | Audio stems (original music / sound effects) | [`build/music_stem.m4a`](build/music_stem.m4a), [`build/sfx_stem.m4a`](build/sfx_stem.m4a). Full-quality WAVs are regenerated locally by `tools/post.py` |

## The short version of what the research found

- **The craft did expand.** Edits moved from mostly reshaping *time and motion* (velocity ramps, shakes, flashes) to *constructing images* (cut-outs, 3D camera, type in depth, light, particles).
- **But the stage changed at the same time**: Shorts launched in September 2020, revenue sharing started on 1 February 2023 (45% creator share), "viewed vs. swiped away" became a metric, Shorts were extended to three minutes in October 2024, and daily Shorts views rose from 70B to 200B+ (company figures).
- **Three of the six channels are football editors**, and four of the six name the same AI upscaler (Topaz) besides After Effects.
- **Their names became styles.** Other creators publish "Heisty like", "Eagle Stan like", "10Mov like", "Fictic like" and "Slicx7 like" tutorials, many of them recreating After Effects looks in phone apps.
- **Public subscriber numbers conflict** between trackers (for example, 1.52M vs. 4.59M for the same channel), and some figures are estimates or come from other platforms. So the film **refuses to rank** the creators. No study shows that editing complexity *causes* growth; that remains a hypothesis.

## Important caveats before publishing

1. The research environment could not open YouTube, Social Blade or vidIQ directly. Every figure is a dated search-index snapshot. **Re-verify all numbers on the live pages.**
2. **Confirm the exact channels** for "Fictic" (several channels share the name) and "10Mov" (two handles).
3. The footage slots are empty on purpose. Insert short, credited excerpts for commentary (see `07-footage-and-archival.md`).
4. The bottom subtitles are **placeholders** for your voice. Either keep them as captions or re-render without them (see `09-production-workflow.md`, step 5).
