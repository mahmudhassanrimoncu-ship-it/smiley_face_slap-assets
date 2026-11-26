# Statistical visualization specifications

**Rule followed throughout:** no invented numbers.
- Every value on screen comes from a cited source and shows that source's number and date.
- Values from third-party trackers are labelled **THIRD-PARTY SNAPSHOT**.
- Company-reported figures are stamped as such.
- Where data was unavailable, the chart was **omitted** rather than estimated. Templates for those charts are in §B, to build once real data is collected.

Shared style for every chart:
- Bars: 8–10 px radius.
- Value labels: Inter 900.
- Axis and source labels: JetBrains Mono 16–24 px, muted grey #7D889E.
- Counters: ease-out cubic over 1.2–2.0 s, with a "count" tick SFX whose spacing slows as the counter decelerates.
- Source tag under every chart, in the form `SOURCE [n]`.

---

## A. Charts in the rendered video

### A1. Viewed vs. swiped away (Scene 1)
- **Type:** horizontal split bar, illustrative.
- **Data:** none. The split drifts between arbitrary positions to show that the metric exists.
- **Labelling:** `ILLUSTRATION · NO REAL VALUES SHOWN`. The metric's existence is cited [1].

### A2. Attention flow (Scene 1)
- **Type:** particle flow of 70 dots from one ring to another.
- **Data:** none. Labelled `ILLUSTRATION OF THE PREMISE · NOT DATA`.

### A3. Creator revenue share ring (Scene 7)
- **Value:** 45%, the creator share of allocated Shorts revenue [14].
- **Animation:** ring stroke from −90° sweeping 0 → 162° (45% of 360°); counter 0 → 45, ease-out cubic 1.6 s; pop SFX at the end.

### A4. Maximum Short length (Scene 7)
- **Values:** 60 s → 180 s from 15 Oct 2024, for square and vertical uploads [15].
- **Animation:** bar width ∝ seconds, max 180. A running `m:ss` label rides the bar head. A dashed marker shows the previous 60 s limit. Cubic in-out 1.8 s.

### A5. Average daily Shorts views (Scene 7)

| Bar | Value | Date | Source | Note |
|---|---|---|---|---|
| 1 | 70B | Mar 2024 | [16] | company-reported |
| 2 | 200B+ | Jun 2025 | [17] | company-reported ("over 200 billion") |

- **Scale:** linear, 0–200B maps to 520 px.
- **Call-out:** "≈2.9×", computed as 200 ÷ 70 = 2.86 and labelled "ratio of the two reported figures".
- **Stamp:** `COMPANY-REPORTED · NOT INDEPENDENTLY AUDITED`.

### A6. Creator profile stats (Scene 8)

| Creator | Shown value | Source and date | If missing |
|---|---|---|---|
| BroxEditZ | 2.78M subscribers | vidIQ, data 27 Apr 2025; joined 21 Jun 2022 [21] | — |
| Slicx7 | 1.52M subscribers | vidIQ, data 12 Feb 2025; created 2016 [23] | — |
| Eagle Stan | 173K subscribers | channel page search snapshot, undated [32] | — |
| 10Mov | — | — | "No reliable public subscriber figure found in this research." |
| Heisty | — | — | "The only YouTube figure found is an estimate. See Chapter 09." |
| Fictic | — | — | "Several channels use this name. Confirm the intended channel first." |

### A7. Tools matrix (Scene 8)
- **Layout:** 6 creators × 4 attributes.
- **Cells:**
  - **●** means stated by the channel or its description [19][22][25][27].
  - **?** means not established by the sources found. It is explicitly *not* "no".
- **Highlight:** a frame moves from the Football column (3 ●) to the Topaz column (4 ●).

### A8. Source-disagreement panels (Scene 11)
Each panel uses **its own linear scale**, which is stated on screen. The bar for the smaller value has a minimum width of 4 px so that it stays visible.

| Panel | Bar A | Bar B | Label |
|---|---|---|---|
| Slicx7 | 1.52M, vidIQ, Feb 2025 [23] | 4.59M, SponsorRadar, undated [24] | ≈3× apart |
| BroxEditZ | 2.78M, vidIQ, Apr 2025 [21] | ≈3.7M, Social Blade, undated, ⚑ data-collection notice [20] | different dates |
| Heisty | YouTube 1.1M+, InfluencerMetric estimate [30] | TikTok ≈393K followers [31]; Snapchat ≈17K subscribers, May 2025 [29] (third bar) | different platforms · one estimate |

### A9. "No ranking" board (Scene 11)
- Six rows whose names shuffle, then a stamp: `NO RANKING · INSUFFICIENT EVIDENCE`.
- No ordering is implied: the names cycle through the slots.

### A10. BroxEditZ two-point line (Scene 11)
- **Points:** (21 Jun 2022, joined) and (27 Apr 2025, 2.78M) [21].
- **Line:** **dashed**, labelled "the path between is unknown". It must never be drawn as a solid growth curve.
- **Chip:** "< 3 YEARS".

### A11. Hypothesis ring (Scene 12)
- Six **equal** segments; the caption reads "EQUAL SEGMENTS · RELATIVE WEIGHTS UNKNOWN".
- Do not resize the segments unless a real attribution study exists.

---

## B. Charts not in the video (data not verified yet): build when the data exists

### B1. Subscriber growth timelines (one per creator)
- **Collect:** monthly subscriber counts from the Social Blade "monthly" table (screenshot with date) or from Wayback Machine captures of the channel page, plus YouTube Data API snapshots going forward.
- **Draw:** a line per creator with points only at real observations. Use dashed interpolation between sparse points; mark data gaps with a hatched band.
- **Never** smooth through unknown periods or extrapolate.

### B2. Upload-frequency visualization
- **Collect:** YouTube Data API → `channels.list(part=contentDetails)` → uploads playlist → `playlistItems.list` (all pages) → `publishedAt`. Split Shorts from long-form with `videos.list(part=contentDetails)` (duration of 180 s or less plus vertical aspect, where determinable).
- **Draw:** a GitHub-style heat strip (weeks × days) or monthly bar columns per creator, aligned on a shared calendar axis with platform milestones (Feb 2023 revenue share, Oct 2024 three-minute Shorts) as vertical rules.

### B3. Video performance comparison
- **Collect:** the top 10 videos per channel by views (sort by Popular), recording the view count, publish date and access date.
- **Draw:** a dot plot of views (log scale) against publish date, colour-coded by channel. Annotate the representative video used in each footage slot.

### B4. Editing-complexity index (only if the study in research report §8 is run)
- Blind-rate N uploads per channel on a rubric: layer count, roto or mask presence, 3D camera, typography in depth, particles, retime complexity.
- Show a scatter of complexity score vs. views relative to channel median, **with the correlation coefficient and N printed**.

### B5. Animated rankings
Only if B1 data exists for all six channels on the **same dates from the same source**. Use a bar-chart race keyed to monthly snapshots, with the source and date always visible.
