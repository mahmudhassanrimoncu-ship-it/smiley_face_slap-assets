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

# Planar Vectors Workshop – interactive class

[`planar-vectors/index.html`](planar-vectors/index.html) is a self-contained interactive class on vectors in the plane. You drag points in live diagrams and answer checkpoint quizzes as you go.

- **Foundations (1–8):** equal vectors, triangle/parallelogram/polygon laws, subtraction (head − tail), scaling and the parallel/collinear test, position vectors and the section formula, components, comparing coefficients, the dot product
- **Toolkit:** a 4-step proof recipe and a geometry → vector dictionary
- **Theorem workshop (T1–T9):** the medians sum to zero, centroid, midpoint theorem, parallelogram diagonals, Varignon, trapezium midline, rhombus diagonals, angle in a semicircle, regular hexagon. Each has a draggable figure and a proof you reveal step by step
- **Practice:** 8 problems with worked solutions

Open the file in any browser. It needs no build step.
