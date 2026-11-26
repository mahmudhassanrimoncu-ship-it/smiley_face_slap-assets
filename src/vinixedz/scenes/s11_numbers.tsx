import {Circle, Line, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  all,
  createRef,
  createSignal,
  easeInOutCubic,
  easeOutCubic,
  easeOutExpo,
  sequence,
  waitFor,
} from '@canvas-commons/core';
import {Chip, SourceTag, headline, openScene, popIn, refs, sfx, withSfx} from '../kit';
import {FONT, MONO, V} from '../theme';

type Bar = {label: string; value: number; display: string; src: string; color: string; flag?: string};
type Panel = {name: string; bars: Bar[]; note: string};

const PANELS: Panel[] = [
  {
    name: 'SLICX7',
    bars: [
      {label: 'vidIQ · Feb 2025', value: 1.52, display: '1.52M', src: refs('vidiq-slicx7'), color: V.cyan},
      {label: 'SponsorRadar · undated', value: 4.59, display: '4.59M', src: refs('sponsorradar-slicx7'), color: V.amber},
    ],
    note: '≈3× apart',
  },
  {
    name: 'BROXEDITZ',
    bars: [
      {label: 'vidIQ · Apr 2025', value: 2.78, display: '2.78M', src: refs('vidiq-broxeditz'), color: V.cyan},
      {label: 'Social Blade · undated', value: 3.7, display: '≈3.7M', src: refs('sb-broxeditz'), color: V.amber, flag: 'tracker notice: data collection stopped'},
    ],
    note: 'different dates',
  },
  {
    name: 'HEISTY',
    bars: [
      {label: 'YouTube · InfluencerMetric estimate', value: 1.1, display: '1.1M+ (estimate)', src: refs('influencermetric-heisty'), color: V.amber},
      {label: 'TikTok followers · snapshot', value: 0.3928, display: '≈393K', src: refs('tiktok-heisty'), color: V.violet},
      {label: 'Snapchat subscribers · May 2025', value: 0.017, display: '≈17K', src: refs('snapchat-heisty'), color: V.cyan},
    ],
    note: 'different platforms · one estimate',
  },
];

export default makeScene2D(function* (view) {
  const nar = yield* openScene(view, 's11_numbers', V.amber);

  /* ---------- line 0-1 ---------- */
  const h0 = yield* headline(view, 'DO THE NUMBERS AGREE?', {y: -110, size: 110});
  yield* nar.at(1);
  sfx('glitch');
  yield* all(h0.opacity(0, 0.12), h0.x(18, 0.12));
  h0.text('MESSIER THAN THEY LOOK');
  h0.fill(V.amber);
  yield* all(h0.opacity(1, 0.15), h0.x(0, 0.2));
  yield* waitFor(2.5);
  yield* h0.opacity(0, 0.4);

  /* ---------- line 2-4: three panels ---------- */
  const panelRefs = PANELS.map(() => createRef<Node>());
  const grow = PANELS.map(() => createSignal(0));
  const BW = 980;
  view.add(
    <Node y={-130}>
      {PANELS.map((p, i) => {
        const max = Math.max(...p.bars.map(b => b.value));
        return (
          <Node ref={panelRefs[i]} y={-245 + i * 235} opacity={0}>
            <Rect width={1640} height={i === 2 ? 236 : 210} radius={18} fill={V.panel + 'ee'} stroke={V.line} lineWidth={2} />
            <Txt x={-780} anchor={[-1, 0]} y={i === 2 ? -84 : -70} text={p.name} fontFamily={FONT} fontWeight={900} fontSize={40} fill={V.ink} />
            <Txt x={-380} anchor={[-1, 0]} y={i === 2 ? -84 : -70} text={(i === 2 ? 'audience figures  ·  ' : 'subscriber figures  ·  ') + p.note} fontFamily={MONO} fontWeight={700} fontSize={20} fill={V.amber} />
            {p.bars.map((b, j) => (
              <Node y={p.bars.length === 3 ? -30 + j * 50 : -6 + j * 66}>
                <Txt x={-780} anchor={[-1, 0]} y={-2} text={b.label} fontFamily={MONO} fontSize={18} fill={V.inkDim} />
                <Rect x={-380} anchor={[-1, 0]} width={BW - 160} height={p.bars.length === 3 ? 30 : 36} radius={8} fill={V.panel2} />
                <Rect x={-380} anchor={[-1, 0]} width={() => Math.max(4, ((BW - 160) * b.value * grow[i]()) / max)} height={p.bars.length === 3 ? 30 : 36} radius={8} fill={b.color} />
                <Txt x={() => -380 + Math.max(4, ((BW - 160) * b.value * grow[i]()) / max) + 16} anchor={[-1, 0]} text={b.display + '  ' + b.src} fontFamily={MONO} fontWeight={700} fontSize={22} fill={V.ink} opacity={() => grow[i]()} />
                {b.flag ? (
                  <Txt x={-380} anchor={[-1, 0]} y={30} text={'⚑ ' + b.flag} fontFamily={MONO} fontSize={16} fill={V.red} opacity={() => grow[i]()} />
                ) : null}
              </Node>
            ))}
          </Node>
        );
      })}
    </Node>,
  );
  const scaleNote = createRef<Node>();
  view.add(
    <Node ref={scaleNote} x={0} y={280} opacity={0}>
      <SourceTag text={'EACH PANEL USES ITS OWN SCALE'} />
    </Node>,
  );
  for (let i = 0; i < 3; i++) {
    yield* nar.at(2 + i);
    if (i === 0) yield scaleNote().opacity(1, 0.5);
    yield* withSfx('blip', popIn(panelRefs[i](), 0.5, 20));
    sfx('count', 1.2);
    yield* grow[i](1, 1.2, easeOutCubic);
  }

  /* ---------- line 5: why they differ ---------- */
  yield* nar.at(5);
  const why = createRef<Node>();
  view.add(
    <Node ref={why} y={-130}>
      {['DIFFERENT DATES', 'DIFFERENT TRACKERS', 'SAME CHANNEL?'].map((w, i) => (
        <Node x={-520 + i * 520} rotation={[-4, 3, -2][i]} opacity={0}>
          <Rect layout padding={[16, 28]} radius={10} fill={V.bg + 'ee'} stroke={V.red} lineWidth={4}>
            <Txt text={w} fontFamily={MONO} fontWeight={700} fontSize={34} letterSpacing={3} fill={V.red} />
          </Rect>
        </Node>
      ))}
    </Node>,
  );
  for (const n of why().children()) {
    sfx('shutter');
    yield* all(n.opacity(1, 0.12), n.scale(1.5).scale(1, 0.35, easeOutExpo));
    yield* waitFor(0.35);
  }

  /* ---------- line 6: no ranking ---------- */
  yield* nar.at(6);
  yield* all(why().opacity(0, 0.5), scaleNote().opacity(0, 0.5), ...panelRefs.map(p => p().opacity(0, 0.5)));
  const rank = createRef<Node>();
  const flick = createSignal(0);
  const names = ['HEISTY', 'FICTIC', 'EAGLE STAN', '10MOV', 'BROXEDITZ', 'SLICX7'];
  view.add(
    <Node ref={rank} y={-130} opacity={0}>
      {[0, 1, 2, 3, 4, 5].map(i => (
        <Node y={-250 + i * 92}>
          <Rect width={760} height={76} radius={12} fill={V.panel + 'ee'} stroke={V.line} lineWidth={2} />
          <Txt x={-330} text={`#${i + 1}`} fontFamily={MONO} fontWeight={700} fontSize={32} fill={V.muted} />
          <Txt x={-240} anchor={[-1, 0]} text={() => names[(i + Math.floor(flick())) % 6]} fontFamily={FONT} fontWeight={800} fontSize={36} fill={V.inkDim + '88'} />
        </Node>
      ))}
    </Node>,
  );
  yield* rank().opacity(1, 0.4);
  sfx('glitch');
  yield* flick(30, 2.2, easeOutCubic);
  const stamp = createRef<Rect>();
  view.add(
    <Rect ref={stamp} y={-130} rotation={-8} layout direction={'column'} alignItems={'center'} padding={[22, 40]} radius={12} fill={V.bg + 'ee'} stroke={V.amber} lineWidth={6} opacity={0}>
      <Txt text={'NO RANKING'} fontFamily={FONT} fontWeight={900} fontSize={96} fill={V.amber} />
      <Txt text={'INSUFFICIENT EVIDENCE'} fontFamily={MONO} fontWeight={700} fontSize={30} letterSpacing={6} fill={V.amber} />
    </Rect>,
  );
  sfx('impact');
  yield* all(stamp().opacity(1, 0.12), stamp().scale(1.6).scale(1, 0.4, easeOutExpo), rank().opacity(0.3, 0.4));

  /* ---------- line 7: BroxEditZ — two data points ---------- */
  yield* nar.at(7);
  yield* all(stamp().opacity(0, 0.4), rank().opacity(0, 0.4));
  const gx = createRef<Node>();
  const prog = createSignal(0);
  const v = createSignal(0);
  const X0 = -600;
  const X1 = 600;
  view.add(
    <Node ref={gx} y={-120} opacity={0}>
      <Txt y={-300} text={'BROXEDITZ · THE ONLY TWO POINTS WE HAVE'} fontFamily={MONO} fontWeight={700} fontSize={24} letterSpacing={5} fill={V.muted} />
      <Line points={[[X0 - 40, 200], [X1 + 60, 200]]} stroke={V.line} lineWidth={3} />
      <Line points={[[X0, 200], [X1, -200]]} stroke={V.cyan} lineWidth={3} lineDash={[12, 12]} end={() => prog()} />
      <Circle x={X0} y={200} size={26} fill={V.cyan} />
      <Txt x={X0} y={250} text={'21 JUN 2022 · JOINED'} fontFamily={MONO} fontSize={22} fill={V.inkDim} />
      <Circle x={X1} y={-200} size={30} fill={V.cyan} opacity={() => (prog() > 0.98 ? 1 : 0)} />
      <Txt x={X1} y={-260} text={() => `${v().toFixed(2)}M`} fontFamily={FONT} fontWeight={900} fontSize={64} fill={V.ink} opacity={() => (prog() > 0.98 ? 1 : 0)} />
      <Txt x={X1} y={-150} text={'27 APR 2025 · vidIQ ' + refs('vidiq-broxeditz')} fontFamily={MONO} fontSize={20} fill={V.inkDim} opacity={() => (prog() > 0.98 ? 1 : 0)} />
      <Rect x={0} y={60} rotation={-18.4} layout padding={[6, 14]} radius={6} fill={V.bg + 'ee'} stroke={V.amber} lineWidth={1.5}>
        <Txt text={'the path between is unknown'} fontFamily={MONO} fontSize={20} fill={V.amber} />
      </Rect>
      <Chip x={0} y={260} text={'< 3 YEARS'} color={V.cyan} size={26} />
    </Node>,
  );
  yield* gx().opacity(1, 0.5);
  sfx('riser', 1.6);
  yield* prog(1, 1.6, easeInOutCubic);
  sfx('count', 1.2);
  yield* v(2.78, 1.2, easeOutCubic);

  /* ---------- line 8: subs != complexity ---------- */
  yield* nar.at(8);
  yield* gx().opacity(0, 0.5);
  const ne = createRef<Node>();
  view.add(
    <Node ref={ne} y={-120} opacity={0}>
      <Txt x={-420} text={'SUBSCRIBERS'} fontFamily={FONT} fontWeight={900} fontSize={96} fill={V.cyan} />
      <Txt x={0} text={'≠'} fontFamily={FONT} fontWeight={900} fontSize={140} fill={V.ink} />
      <Txt x={420} text={'COMPLEXITY'} fontFamily={FONT} fontWeight={900} fontSize={96} fill={V.magenta} />
    </Node>,
  );
  sfx('impact');
  yield* all(ne().opacity(1, 0.3), ne().scale(1.2).scale(1, 0.6, easeOutExpo));

  /* ---------- line 9-10: the study nobody has done ---------- */
  yield* nar.at(9);
  yield* ne().opacity(0, 0.4);
  const study = createRef<Node>();
  const cells = createRef<Node>();
  view.add(
    <Node ref={study} y={-130}>
      <Node ref={cells} x={-300}>
        {Array.from({length: 8 * 14}, (_, k) => (
          <Rect x={-390 + (k % 14) * 60} y={-210 + Math.floor(k / 14) * 60} size={46} radius={6} fill={V.panel2} stroke={V.line} lineWidth={1.5} opacity={0} />
        ))}
        <Txt x={0} y={-275} text={'CHANNELS × UPLOADS'} fontFamily={MONO} fontWeight={700} fontSize={22} letterSpacing={5} fill={V.muted} />
      </Node>
      <Node x={560}>
        {['CONTROL: SUBJECT', 'CONTROL: TIMING', 'CONTROL: FREQUENCY', 'MEASURE: COMPLEXITY', 'MEASURE: GROWTH'].map((c, i) => (
          <Node y={-200 + i * 90} opacity={0}>
            <Chip text={c} color={i < 3 ? V.cyan : V.amber} size={22} />
          </Node>
        ))}
      </Node>
    </Node>,
  );
  yield* sequence(0.006, ...cells().children().map(n => n.opacity(1, 0.15)));
  yield* sequence(0.25, ...study().children()[1].children().map(n => withSfx('tick', popIn(n, 0.4, 14))));

  yield* nar.at(10);
  const ns = createRef<Rect>();
  view.add(
    <Rect ref={ns} y={-130} rotation={-6} layout padding={[18, 36]} radius={10} fill={V.bg + 'ee'} stroke={V.amber} lineWidth={5} opacity={0}>
      <Txt text={'NO PUBLISHED STUDY YET'} fontFamily={MONO} fontWeight={700} fontSize={46} letterSpacing={4} fill={V.amber} />
    </Rect>,
  );
  sfx('shutter');
  yield* all(ns().opacity(1, 0.12), ns().scale(1.5).scale(1, 0.4, easeOutExpo), study().opacity(0.35, 0.4));
  yield* nar.end();
  yield* all(ns().opacity(0, 0.6), study().opacity(0, 0.6));
});
