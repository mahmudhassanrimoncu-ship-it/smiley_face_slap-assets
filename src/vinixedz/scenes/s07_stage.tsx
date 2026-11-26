import {Circle, Gradient, Line, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  all,
  createRef,
  createSignal,
  easeInOutCubic,
  easeOutCubic,
  easeOutExpo,
  waitFor,
} from '@canvas-commons/core';
import {DateCard, SourceTag, headline, openScene, popIn, refs, sfx, withSfx} from '../kit';
import {FONT, MONO, V} from '../theme';

export default makeScene2D(function* (view) {
  const nar = yield* openScene(view, 's07_stage', V.magenta);

  /* ---------- line 0 ---------- */
  const h0 = yield* headline(view, 'THE PLATFORM', {y: -120, size: 140, color: V.ink});
  yield* waitFor(2.5);

  /* ---------- line 1: revenue sharing ---------- */
  yield* nar.at(1);
  yield* all(h0.opacity(0, 0.4), h0.y(-200, 0.4));
  const c1 = createRef<Node>();
  view.add(
    <Node ref={c1} x={-430} y={-150} opacity={0}>
      <DateCard
        date={'01 FEB 2023'}
        title={'Shorts revenue sharing begins'}
        body={'For creators in the YouTube Partner Program'}
        src={refs('9to5-shorts-revenue', 'androidcentral-shorts-ypp')}
        color={V.magenta}
        w={640}
        opacity={1}
      />
    </Node>,
  );
  yield* withSfx('blip', popIn(c1(), 0.6, 30));

  /* ---------- line 2: 45% ring ---------- */
  yield* nar.at(2);
  const pct = createSignal(0);
  const ring = createRef<Node>();
  view.add(
    <Node ref={ring} x={470} y={-150} opacity={0}>
      <Circle size={340} stroke={V.panel2} lineWidth={34} />
      <Circle
        size={340}
        stroke={V.magenta}
        lineWidth={34}
        lineCap={'round'}
        startAngle={-90}
        endAngle={() => -90 + 3.6 * pct()}
      />
      <Txt text={() => `${Math.round(pct())}%`} fontFamily={FONT} fontWeight={900} fontSize={96} fill={V.ink} />
      <Txt y={230} width={520} textWrap textAlign={'center'} text={'creator share of the revenue allocated to them'} fontFamily={FONT} fontWeight={500} fontSize={26} fill={V.inkDim} />
      <SourceTag y={300} text={'SOURCE ' + refs('nbc-shorts-revenue')} />
    </Node>,
  );
  yield* ring().opacity(1, 0.4);
  sfx('count', 1.6);
  yield* pct(45, 1.6, easeOutCubic);
  sfx('pop');

  /* ---------- line 3: viewed vs swiped ---------- */
  yield* nar.at(3);
  yield* all(c1().opacity(0, 0.5), ring().opacity(0, 0.5));
  const m = createRef<Node>();
  view.add(
    <Node ref={m} y={-150} opacity={0}>
      <Rect width={1000} height={230} radius={20} fill={V.panel + 'ee'} stroke={V.line} lineWidth={2} />
      <Txt y={-60} text={'VIEWED  vs.  SWIPED AWAY'} fontFamily={FONT} fontWeight={900} fontSize={62} fill={V.ink} />
      <Txt y={20} text={'Shorts metric in YouTube analytics'} fontFamily={FONT} fontWeight={500} fontSize={28} fill={V.inkDim} />
      <SourceTag y={80} text={'SOURCE ' + refs('yt-help-content-performance')} />
    </Node>,
  );
  yield* withSfx('blip', popIn(m(), 0.6, 30));

  /* ---------- line 4: three-minute Shorts ---------- */
  yield* nar.at(4);
  yield* m().opacity(0, 0.4);
  const len = createSignal(60);
  const dur = createRef<Node>();
  view.add(
    <Node ref={dur} y={-150} opacity={0}>
      <Txt y={-150} text={'15 OCT 2024 · MAXIMUM SHORT LENGTH'} fontFamily={MONO} fontWeight={700} fontSize={24} letterSpacing={5} fill={V.cyan} />
      <Rect x={-600} anchor={[-1, 0]} width={1200} height={60} radius={30} fill={V.panel2} />
      <Rect x={-600} anchor={[-1, 0]} width={() => (len() / 180) * 1200} height={60} radius={30} fill={V.cyan} />
      <Line points={[[-200, -50], [-200, 50]]} stroke={V.ink + '88'} lineWidth={2} lineDash={[6, 6]} />
      <Txt x={-200} y={80} text={'previous limit · 60 s'} fontFamily={MONO} fontSize={20} fill={V.muted} />
      <Txt y={-80} x={() => -600 + (len() / 180) * 1200 - 60} text={() => {
        const s = Math.round(len());
        return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
      }} fontFamily={FONT} fontWeight={900} fontSize={46} fill={V.ink} />
      <SourceTag y={150} text={'SOURCE ' + refs('yt-help-3min-shorts') + ' · square and vertical uploads'} />
    </Node>,
  );
  yield* dur().opacity(1, 0.5);
  sfx('count', 1.8);
  yield* len(180, 1.8, easeInOutCubic);

  /* ---------- line 5-6: daily views ---------- */
  yield* nar.at(5);
  yield* dur().opacity(0, 0.4);
  const a = createSignal(0);
  const b = createSignal(0);
  const chart = createRef<Node>();
  const H = 440;
  const max = 200;
  view.add(
    <Node ref={chart} y={-110} opacity={0}>
      <Txt y={-H / 2 - 110} text={'AVERAGE DAILY SHORTS VIEWS · COMPANY-REPORTED'} fontFamily={MONO} fontWeight={700} fontSize={24} letterSpacing={4} fill={V.muted} />
      <Line points={[[-420, H / 2], [420, H / 2]]} stroke={V.line} lineWidth={2} />
      <Rect x={-180} y={H / 2} anchor={[0, 1]} width={220} height={() => (a() / max) * H} radius={[10, 10, 0, 0]} fill={V.cyan} />
      <Rect x={180} y={H / 2} anchor={[0, 1]} width={220} height={() => (b() / max) * H} radius={[10, 10, 0, 0]} fill={V.magenta} />
      <Txt x={-180} y={() => H / 2 - (a() / max) * H - 40} text={() => `${Math.round(a())}B`} fontFamily={FONT} fontWeight={900} fontSize={54} fill={V.ink} opacity={() => (a() > 0.5 ? 1 : 0)} />
      <Txt x={180} y={() => H / 2 - (b() / max) * H - 40} text={() => `${Math.round(b())}B${b() >= 199.5 ? '+' : ''}`} fontFamily={FONT} fontWeight={900} fontSize={54} fill={V.ink} opacity={() => (b() > 0.5 ? 1 : 0)} />
      <Txt x={-180} y={H / 2 + 34} text={'MAR 2024'} fontFamily={MONO} fontWeight={700} fontSize={24} fill={V.cyan} />
      <Txt x={180} y={H / 2 + 34} text={'JUN 2025'} fontFamily={MONO} fontWeight={700} fontSize={24} fill={V.magenta} />
      <SourceTag x={-180} y={H / 2 + 76} text={refs('thewrap-200b')} />
      <SourceTag x={180} y={H / 2 + 76} text={refs('yt-blog-cannes-2025')} />
    </Node>,
  );
  yield* chart().opacity(1, 0.5);
  sfx('count', 1.4);
  yield* a(70, 1.4, easeOutExpo);

  yield* nar.at(6);
  sfx('count', 2);
  yield* b(200, 2, easeOutExpo);
  sfx('impact');
  const ratio = createRef<Node>();
  view.add(
    <Node ref={ratio} x={660} y={-200} opacity={0}>
      <Txt text={'≈ 2.9×'} fontFamily={FONT} fontWeight={900} fontSize={88} fill={V.amber} />
      <Txt y={70} width={360} textWrap textAlign={'center'} text={'ratio of the two reported figures'} fontFamily={FONT} fontWeight={500} fontSize={24} fill={V.inkDim} />
    </Node>,
  );
  yield* popIn(ratio(), 0.5, 20);

  /* ---------- line 7: stamp ---------- */
  yield* nar.at(7);
  const stamp = createRef<Rect>();
  view.add(
    <Rect ref={stamp} y={-120} rotation={-6} layout padding={[18, 34]} radius={10} stroke={V.amber} lineWidth={5} fill={V.bg + 'cc'} opacity={0} scale={1.6}>
      <Txt text={'COMPANY-REPORTED · NOT INDEPENDENTLY AUDITED'} fontFamily={MONO} fontWeight={700} fontSize={34} letterSpacing={3} fill={V.amber} />
    </Rect>,
  );
  sfx('shutter');
  yield* all(stamp().opacity(1, 0.15), stamp().scale(1, 0.35, easeOutExpo));

  /* ---------- line 8-9: the stage ---------- */
  yield* nar.at(8);
  yield* all(chart().opacity(0, 0.5), ratio().opacity(0, 0.5), stamp().opacity(0, 0.5));
  const st = createRef<Node>();
  view.add(
    <Node ref={st} y={-90} opacity={0}>
      <Line
        points={[[-90, -460], [90, -460], [420, 260], [-420, 260]]}
        closed
        fill={
          new Gradient({
            type: 'linear',
            from: [0, -460],
            to: [0, 260],
            stops: [
              {offset: 0, color: V.ink + '30'},
              {offset: 1, color: V.ink + '00'},
            ],
          })
        }
      />
      <Rect width={300} height={530} radius={34} fill={'#000'} stroke={V.ink} lineWidth={4} />
      <Rect y={290} width={1000} height={30} radius={15} fill={V.panel2} />
      <Txt y={0} text={'THE\nSTAGE'} textAlign={'center'} fontFamily={FONT} fontWeight={900} fontSize={64} lineHeight={70} fill={V.ink} />
    </Node>,
  );
  sfx('swell', 3);
  yield* all(st().opacity(1, 1.0), st().scale(0.92).scale(1, 2.5, easeOutCubic));

  yield* nar.at(9);
  const two = createRef<Node>();
  view.add(
    <Node ref={two} y={-90}>
      <Node x={-560} opacity={0}>
        <Txt text={'THE FIRST\nSECOND'} textAlign={'center'} fontFamily={FONT} fontWeight={900} fontSize={58} lineHeight={64} fill={V.magenta} />
      </Node>
      <Node x={560} opacity={0}>
        <Txt text={'A REASON TO\nWATCH AGAIN'} textAlign={'center'} fontFamily={FONT} fontWeight={900} fontSize={58} lineHeight={64} fill={V.cyan} />
      </Node>
    </Node>,
  );
  yield* withSfx('pop', popIn(two().children()[0], 0.5, 20));
  yield* waitFor(0.4);
  yield* withSfx('pop', popIn(two().children()[1], 0.5, 20));
  yield* nar.end();
  yield* all(st().opacity(0, 0.6), two().opacity(0, 0.6), st().scale(1.2, 0.6));
});
