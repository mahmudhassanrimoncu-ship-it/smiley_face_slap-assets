# Sound design plan

**No speech, no synthetic voice anywhere.** The soundtrack is music plus sound effects, leaving the centre of the mix free for your own voice-over.

Every sound in the rendered video is **original**. It was synthesised from scratch by [`tools/audio.py`](tools/audio.py) using numpy oscillators, filtered noise and a convolution reverb built from generated impulses. No samples, loops or third-party audio were used, so there is nothing to license. Re-running the script reproduces the same audio.

Deliverables (in `vinixedz/build/` after running `post.py`):
- `music.wav`: music stem
- `sfx.wav`: sound-effects stem
- `mix.wav`: the combined track muxed into the MP4

## 1. Score

Key of D minor, 92 BPM, two-bar chord changes. Each scene gets a mood. Moods crossfade at scene boundaries: 1.5 s in, 2.5 s tail.

| Scene | Mood | Progression | Layers |
|---|---|---|---|
| 1 Cold open | dark heartbeat | Dm–B♭–F–C | low pad, **sub "heartbeat" pulse** on every beat |
| 2 Title | rise | Dm–B♭–F–C | brighter pad, pulse; riser and impacts from SFX |
| 3 The question | curious | Dm–B♭–F–C | pad, sparse plucked arpeggio (quarters) |
| 4 Before the feed | nostalgic | B♭–F–C–Dm | warm pad, plucked 8th-note arpeggio |
| 5 Vertical turn | pulse | B♭–F–C–Dm | pad, arpeggio, half-time kick, sustained bass |
| 6 Old grammar | analytic | Dm–B♭–F–C | thin pad, arpeggio, off-beat hats |
| 7 Money and the swipe | pulse | Dm–B♭–F–C | pad, arpeggio, kick, hats, bass |
| 8–10 Creators / Anatomy / Compare | drive | Dm–B♭–F–C | brightest pad, four-on-the-floor kick, hats, bass, arpeggio |
| 11 Numbers | analytic | Dm–B♭–F–C | pared back: arpeggio and hats only, so counters and stamps can read |
| 12 Why | build | Dm–B♭–F–C | full pad, kick, hats, bass |
| 13 Floor and ceiling | reflect | Dm–Gm–B♭–A | soft pad, sparse arpeggio |
| 14 Future | airy | Dm–Gm–B♭–A | dark, very soft pad, minimal arpeggio |
| 15 Conclusion | finale | Dm–Gm–B♭–A | full pad, bass, kick; a 6 s fade to silence |

All music passes through a 2.8 s stereo convolution reverb at 35% wet.

## 2. Sound-effect vocabulary

Each effect is triggered from the animation code with `sfx('<name>')`, so it lands on the exact frame of the visual event.

| Name | Sound | Used for |
|---|---|---|
| `whoosh` | band-passed noise swell with an L→R pan | card swaps, camera moves, transitions |
| `whooshBig` | longer, darker whoosh plus falling sub | chapter cards, long timeline jumps, collapses |
| `impact` | pitched-down sine thump plus noise, short reverb | title hits, "SIMPLY BETTER?", stamps, big reveals |
| `sub` | soft 44 Hz boom | landing moments, foundations |
| `riser` | rising noise plus a sweeping tone | build-ups before reveals and curve draws |
| `swell` | reverse-style pad swell | emotional turns, collapses, endings |
| `tick` | 2.6 kHz micro click | list items, feed swipes, highlights |
| `blip` | short upward UI chirp | data cards appearing |
| `pop` | short downward pitch pop | cards and nodes popping in |
| `count` | rapid ticks that slow down with the easing | every animated counter |
| `shutter` | click, noise and low thump | rubber stamps, "ASSUME" strike-through |
| `glitch` | crushed square-wave burst | headline swaps, flashes, speculation zone |

**Mixing rules:**
- Effects sit about 6–10 dB under impacts.
- UI sounds (`tick`, `blip`, `count`) are kept tiny so that they reinforce motion without fatiguing.
- Bass impacts are reserved for chapter cards and title moments, not every card.

## 3. Mixing in your voice-over

1. Import `music.wav` and `sfx.wav` as separate tracks (not just `mix.wav`) so you can control them independently.
2. Record your narration from `04-narration.md`. Aim for about −16 LUFS integrated for the voice track.
3. Duck the music 6–9 dB under the voice with sidechain compression (attack 30 ms, release 400 ms) or keyframes. Leave SFX mostly un-ducked, but pull `count` and `tick` down 3 dB under speech.
4. Target the final master at −14 LUFS integrated, −1 dBTP true peak (YouTube normalises to about −14).
5. If your read is slower than the subtitle timing, extend the hold of the relevant scene. See `09-production-workflow.md`.
