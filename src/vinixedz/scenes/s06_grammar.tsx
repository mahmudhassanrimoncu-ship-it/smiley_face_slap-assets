import {Circle, Line, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  Vector2,
  all,
  createRef,
  createSignal,
  easeInOutCubic,
  easeOutExpo,
  linear,
  sequence,
  waitFor,
} from '@canvas-commons/core';
import {openScene, popIn, rng, sfx, withSfx} from '../kit';
import {FONT, MONO, V} from '../theme';

/* graph area */
const GW = 900;
const GH = 380;
const GX = -260; // panel centre x
const GY = -130;

/** Speed profile used for the time-remap demo, t in [0,1] -> speed factor. */
function speed(t: number) {
  // 1.0 -> dip to 0.2 -> hold -> spike 4.0 -> back to 1.0
  if (t < 0.18) return 1 - (t / 0.18) * 0.8;
  if (t < 0.55) return 0.2;
  if (t < 0.7) return 0.2 + ((t - 0.55) / 0.15) * 3.8;
  if (t < 0.8) return 4.0 - ((t - 0.7) / 0.1) * 3.0;
  return 1.0;
}
const smooth = (f: (t: number) => number) => (t: number) => {
  let s = 0;
  for (let k = -3; k <= 3; k++) s += f(Math.min(1, Math.max(0, t + k * 0.012)));
  return s / 7;
};
const spd = smooth(speed);

function graphPoint(t: number, v: number, vmax: number): [number, number] {
  return [-GW / 2 + t * GW, GH / 2 - (v / vmax) * GH];
}

export default makeScene2D(function* (view) {
  const nar = yield* openScene(view, 's06_grammar', V.green);

  /* ---------- line 0-1: graph panel ---------- */
  const panel = createRef<Node>();
  const curve = createRef<Line>();
  const yLbl = createRef<Txt>();
  const title = createRef<Txt>();
  const pts: [number, number][] = [];
  for (let i = 0; i <= 160; i++) pts.push(graphPoint(i / 160, spd(i / 160), 4.4));
  view.add(
    <Node ref={panel} x={GX} y={GY} opacity={0}>
      <Rect width={GW + 120} height={GH + 140} radius={20} fill={V.panel + 'ee'} stroke={V.line} lineWidth={2} />
      <Txt ref={title} y={-GH / 2 - 40} x={-GW / 2} anchor={[-1, 0]} text={'TIME REMAP · SPEED GRAPH'} fontFamily={MONO} fontWeight={700} fontSize={22} letterSpacing={4} fill={V.green} />
      {[0, 1, 2, 3, 4].map(k => (
        <Line points={[graphPoint(0, k, 4.4), graphPoint(1, k, 4.4)]} stroke={V.lineSoft} lineWidth={1.5} />
      ))}
      <Line points={[graphPoint(0, 1, 4.4), graphPoint(1, 1, 4.4)]} stroke={V.muted} lineWidth={1.5} lineDash={[8, 8]} />
      <Txt ref={yLbl} x={-GW / 2 - 34} y={graphPoint(0, 1, 4.4)[1]} text={'100%'} fontFamily={MONO} fontSize={16} fill={V.muted} />
      <Txt x={GW / 2 - 40} y={GH / 2 + 30} text={'TIME →'} fontFamily={MONO} fontSize={18} fill={V.muted} />
      <Line ref={curve} points={pts} stroke={V.green} lineWidth={5} end={0} shadowColor={V.green} shadowBlur={14} />
    </Node>,
  );
  yield* withSfx('blip', popIn(panel(), 0.6, 30));

  /* preview box on the right */
  const prev = createRef<Node>();
  const ball = createSignal(0);
  view.add(
    <Node ref={prev} x={600} y={GY} opacity={0}>
      <Rect width={420} height={GH + 140} radius={20} fill={V.panel + 'ee'} stroke={V.line} lineWidth={2} clip>
        <Line points={[[0, -220], [0, 220]]} stroke={V.lineSoft} lineWidth={2} lineDash={[8, 8]} />
      </Rect>
      <Circle size={60} fill={V.green} y={() => -150 + ball() * 360} />
      <Txt y={-GH / 2 - 40} text={'PREVIEW'} fontFamily={MONO} fontWeight={700} fontSize={22} letterSpacing={4} fill={V.muted} />
    </Node>,
  );
  yield* nar.at(1);
  yield* popIn(prev(), 0.6, 30);

  /* ---------- line 2: draw curve, playhead + labels ---------- */
  yield* nar.at(2);
  sfx('riser', 1.6);
  yield* curve().end(1, 1.6, easeInOutCubic);
  const labels = createRef<Node>();
  view.add(
    <Node ref={labels} x={GX} y={GY}>
      {[
        {t: 0.1, txt: 'RAMP DOWN', c: V.inkDim},
        {t: 0.37, txt: 'SLOW-MO HOLD', c: V.cyan},
        {t: 0.68, txt: 'SNAP', c: V.magenta},
      ].map(l => {
        const [x, y] = graphPoint(l.t, spd(l.t), 4.4);
        return (
          <Node x={x} y={y - 46} opacity={0}>
            <Rect layout padding={[6, 12]} radius={6} fill={V.bg + 'dd'} stroke={l.c} lineWidth={1.5}>
              <Txt text={l.txt} fontFamily={MONO} fontWeight={700} fontSize={18} letterSpacing={2} fill={l.c} />
            </Rect>
          </Node>
        );
      })}
    </Node>,
  );
  yield* sequence(0.3, ...labels().children().map(n => withSfx('tick', popIn(n, 0.4, 14))));

  // playhead
  const ph = createSignal(0);
  const head = createRef<Node>();
  view.add(
    <Node ref={head} x={GX} y={GY}>
      <Line points={() => [[-GW / 2 + ph() * GW, -GH / 2], [-GW / 2 + ph() * GW, GH / 2]]} stroke={V.ink + '88'} lineWidth={2} />
      <Circle size={18} fill={V.ink} position={() => new Vector2(...graphPoint(ph(), spd(ph()), 4.4))} />
    </Node>,
  );
  // integrate position from speed for the preview
  const integ: number[] = [0];
  for (let i = 1; i <= 400; i++) integ.push(integ[i - 1] + spd(i / 400));
  const posAt = (t: number) => integ[Math.round(t * 400)] / integ[400];
  const runPlayhead = function* (d: number) {
    ph(0);
    yield* ph(1, d, linear);
  };
  for (let k = 0; k < 2; k++) {
    ph(0);
    yield* all(
      runPlayhead(3.2),
      (function* () {
        const steps = 96;
        for (let i = 0; i <= steps; i++) {
          ball(posAt(i / steps));
          yield* waitFor(3.2 / steps);
        }
      })(),
    );
  }

  /* ---------- line 3: shake ---------- */
  yield* nar.at(3);
  title().text('SHAKE · POSITION + ROTATION');
  title().fill(V.amber);
  const shakeA: [number, number][] = [];
  const shakeB: [number, number][] = [];
  for (let i = 0; i <= 200; i++) {
    const t = i / 200;
    const env = Math.exp(-t * 5);
    shakeA.push([-GW / 2 + t * GW, -Math.sin(t * 60) * env * GH * 0.42]);
    shakeB.push([-GW / 2 + t * GW, -Math.sin(t * 47 + 1) * env * GH * 0.25]);
  }
  yield* all(curve().opacity(0, 0.4), labels().opacity(0, 0.4), head().opacity(0, 0.4), yLbl().opacity(0, 0.4));
  const sh1 = createRef<Line>();
  const sh2 = createRef<Line>();
  panel().add(<Line ref={sh1} points={shakeA} stroke={V.amber} lineWidth={4} end={0} />);
  panel().add(<Line ref={sh2} points={shakeB} stroke={V.violet} lineWidth={3} end={0} />);
  panel().add(
    <Node x={GW / 2 - 140} y={-GH / 2 + 20}>
      <Txt text={'— POSITION'} fontFamily={MONO} fontSize={18} fill={V.amber} anchor={[-1, 0]} />
      <Txt y={28} text={'— ROTATION'} fontFamily={MONO} fontSize={18} fill={V.violet} anchor={[-1, 0]} />
    </Node>,
  );
  sfx('impact');
  yield* all(sh1().end(1, 1.2, easeOutExpo), sh2().end(1, 1.2, easeOutExpo));
  // shake the preview with ghost copies (motion blur)
  const pv = prev().children()[1] as Circle;
  pv.y(0);
  for (let rep = 0; rep < 2; rep++) {
    sfx('impact');
    for (let k = 0; k < 10; k++) {
      const a = 60 * Math.pow(0.72, k);
      yield* all(pv.x(k % 2 ? a : -a, 0.045), pv.y(k % 2 ? -a / 3 : a / 3, 0.045));
    }
    yield* all(pv.x(0, 0.05), pv.y(0, 0.05));
    yield* waitFor(0.8);
  }

  /* ---------- line 4: flash / zoom transition ---------- */
  yield* nar.at(4);
  yield* all(sh1().opacity(0, 0.4), sh2().opacity(0, 0.4), ...panel().children().slice(-1).map(n => n.opacity(0, 0.4)));
  title().text('ZOOM TRANSITION · SCALE OVER TIME');
  title().fill(V.cyan);
  const zPts: [number, number][] = [];
  for (let i = 0; i <= 200; i++) {
    const t = i / 200;
    const v = t < 0.5 ? 1 + 3 * Math.pow(t / 0.5, 3) : 1 + 3 * Math.pow((1 - t) / 0.5, 3);
    zPts.push([-GW / 2 + t * GW, GH / 2 - ((v - 1) / 3) * GH * 0.9 - 10]);
  }
  const zl = createRef<Line>();
  const cutLn = createRef<Node>();
  panel().add(<Line ref={zl} points={zPts} stroke={V.cyan} lineWidth={4} end={0} />);
  panel().add(
    <Node ref={cutLn} opacity={0}>
      <Line points={[[0, -GH / 2], [0, GH / 2]]} stroke={V.ink} lineWidth={2} lineDash={[6, 6]} />
      <Rect y={-GH / 2 + 30} layout padding={[6, 12]} radius={6} fill={V.bg} stroke={V.ink} lineWidth={1.5}>
        <Txt text={'CUT HIDDEN HERE'} fontFamily={MONO} fontWeight={700} fontSize={18} fill={V.ink} />
      </Rect>
    </Node>,
  );
  yield* zl().end(1, 1.0, easeInOutCubic);
  yield* cutLn().opacity(1, 0.4);
  // preview: shot A -> flash -> shot B
  const box = prev().children()[0] as Rect;
  const shotA = createRef<Rect>();
  const shotB = createRef<Rect>();
  const wf = createRef<Rect>();
  box.add(
    <Node>
      <Rect ref={shotA} size={[420, 520]} fill={'#0d3b52'}>
        <Txt text={'SHOT A'} fontFamily={FONT} fontWeight={900} fontSize={60} fill={V.cyan} />
      </Rect>
      <Rect ref={shotB} size={[420, 520]} fill={'#4a0f2c'} opacity={0}>
        <Txt text={'SHOT B'} fontFamily={FONT} fontWeight={900} fontSize={60} fill={V.magenta} />
      </Rect>
      <Rect ref={wf} size={[420, 520]} fill={'#fff'} opacity={0} />
    </Node>,
  );
  pv.opacity(0);
  for (let rep = 0; rep < 2; rep++) {
    shotA().scale(1);
    shotA().opacity(1);
    shotB().opacity(0);
    sfx('riser', 0.7);
    yield* shotA().scale(3, 0.7, t => t * t * t);
    sfx('glitch');
    shotA().opacity(0);
    shotB().opacity(1);
    shotB().scale(3);
    yield* all(wf().opacity(0.9, 0.04).to(0, 0.3), shotB().scale(1, 0.7, easeOutExpo));
    yield* waitFor(0.7);
  }

  /* ---------- line 5: beat sync ---------- */
  yield* nar.at(5);
  const wave = createRef<Node>();
  const r = rng(5);
  const beats = [0.08, 0.31, 0.54, 0.77];
  view.add(
    <Node ref={wave} x={GX} y={GY + GH / 2 + 125} opacity={0}>
      {Array.from({length: 110}, (_, i) => {
        const t = i / 110;
        const near = Math.min(...beats.map(b => Math.abs(t - b)));
        const h = 8 + (near < 0.02 ? 70 : 10 + r() * 26);
        return <Rect x={-GW / 2 + t * GW} width={5} height={h} radius={2} fill={near < 0.02 ? V.magenta : V.faint} />;
      })}
      {beats.map(b => (
        <Line points={[[-GW / 2 + b * GW, -60], [-GW / 2 + b * GW, -300 - 140]]} stroke={V.magenta + '66'} lineWidth={2} lineDash={[6, 6]} />
      ))}
    </Node>,
  );
  yield* all(wave().opacity(1, 0.6), zl().opacity(0.25, 0.6), cutLn().opacity(0, 0.4));
  const kf = createRef<Node>();
  view.add(
    <Node ref={kf} x={GX} y={GY}>
      {beats.map(b => (
        <Rect x={-GW / 2 + b * GW} y={GH / 2 - 20} size={22} rotation={45} fill={V.magenta} opacity={0} />
      ))}
    </Node>,
  );
  for (const k of kf().children()) {
    sfx('tick');
    yield* all(k.opacity(1, 0.15), k.scale(1.6, 0.1).to(1, 0.3));
    yield* waitFor(0.45);
  }

  /* ---------- line 6: many small decisions ---------- */
  yield* nar.at(6);
  const many = createRef<Node>();
  const r2 = rng(21);
  view.add(
    <Node ref={many} x={GX} y={GY}>
      {Array.from({length: 46}, () => (
        <Rect x={-GW / 2 + r2() * GW} y={-GH / 2 + 20 + r2() * (GH - 40)} size={12} rotation={45} fill={V.ink} opacity={0} />
      ))}
    </Node>,
  );
  yield* sequence(0.03, ...many().children().map(n => n.opacity(0.75, 0.2)));

  /* ---------- line 7-8: what it transforms ---------- */
  yield* nar.at(7);
  sfx('whoosh');
  yield* all(panel().opacity(0, 0.5), prev().opacity(0, 0.5), wave().opacity(0, 0.5), kf().opacity(0, 0.5), many().opacity(0, 0.5));
  const table = createRef<Node>();
  const rows = [
    {k: 'TIME', v: '✓', c: V.green},
    {k: 'MOTION', v: '✓', c: V.green},
    {k: 'THE IMAGE ITSELF', v: '—', c: V.muted},
  ];
  view.add(
    <Node ref={table} y={-150}>
      <Txt y={-200} text={'WHAT THE OLD GRAMMAR MOSTLY TRANSFORMS'} fontFamily={MONO} fontWeight={700} fontSize={24} letterSpacing={6} fill={V.muted} />
      {rows.map((row, i) => (
        <Node y={-90 + i * 110} opacity={0}>
          <Rect width={900} height={90} radius={14} fill={V.panel + 'ee'} stroke={V.line} lineWidth={2} />
          <Txt x={-400} anchor={[-1, 0]} text={row.k} fontFamily={FONT} fontWeight={800} fontSize={44} fill={row.c === V.muted ? V.muted : V.ink} />
          <Txt x={380} text={row.v} fontFamily={FONT} fontWeight={900} fontSize={52} fill={row.c} />
        </Node>
      ))}
    </Node>,
  );
  const tr = table().children().slice(1);
  yield* sequence(0.35, ...tr.map(n => withSfx('tick', popIn(n, 0.5, 20))));

  yield* nar.at(8);
  const last = tr[2] as Node;
  sfx('swell', 2);
  yield* all(
    ((last.children()[0]) as Rect).stroke(V.magenta, 0.8),
    ((last.children()[1]) as Txt).fill(V.magenta, 0.8),
    last.scale(1.06, 0.8, easeInOutCubic),
  );
  yield* nar.end();
  yield* all(table().opacity(0, 0.6), table().y(-200, 0.6));
});
