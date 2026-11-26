import {Circle, Line, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  Vector2,
  all,
  createRef,
  createSignal,
  easeInExpo,
  easeInOutCubic,
  easeOutExpo,
  linear,
  sequence,
  waitFor,
} from '@canvas-commons/core';
import {Chip, SourceTag, openScene, popIn, sfx, withSfx} from '../kit';
import {FONT, MONO, V} from '../theme';

const W = 800;
const H = 450;

function ShotA(props: {refFn: (n: Node) => void; subjX?: () => number}) {
  return (
    <Node ref={props.refFn}>
      <Rect size={[W, H]} fill={'#0c3147'} />
      <Rect y={150} size={[W, 150]} fill={'#0a2536'} />
      <Circle x={props.subjX ?? 0} y={20} size={150} fill={V.cyan} />
      <Txt x={-300} y={-180} text={'SHOT A'} fontFamily={MONO} fontWeight={700} fontSize={22} fill={V.cyan} />
    </Node>
  );
}
function ShotB(props: {refFn: (n: Node) => void}) {
  return (
    <Node ref={props.refFn}>
      <Rect size={[W, H]} fill={'#3d0d26'} />
      <Rect y={150} size={[W, 150]} fill={'#2a081a'} />
      <Rect y={20} size={150} rotation={45} fill={V.magenta} />
      <Txt x={-300} y={-180} text={'SHOT B'} fontFamily={MONO} fontWeight={700} fontSize={22} fill={V.magenta} />
    </Node>
  );
}

export default makeScene2D(function* (view) {
  const nar = yield* openScene(view, 's10_compare', V.violet);

  const L = createRef<Node>();
  const R = createRef<Node>();
  const la = createRef<Node>();
  const lb = createRef<Node>();
  const ra = createRef<Node>();
  const rb = createRef<Node>();
  const lflash = createRef<Rect>();
  const lwrap = createRef<Node>();
  const rwrap = createRef<Node>();
  const maskR = createSignal(0);
  const subjX = createSignal(0);
  const typeX = createSignal(-1300);

  view.add(
    <Node y={-150}>
      <Node ref={L} x={-450} opacity={0} scale={0.98}>
        <Rect size={[W, H]} radius={16} clip stroke={V.line} lineWidth={3}>
          <Node ref={lwrap}>
            <ShotA refFn={la} />
            <Node opacity={0} ref={lb}>
              <ShotB refFn={() => {}} />
            </Node>
          </Node>
          <Rect ref={lflash} size={[W, H]} fill={'#fff'} opacity={0} />
        </Rect>
        <Txt y={-H / 2 - 40} text={'APPROACH 1'} fontFamily={MONO} fontWeight={700} fontSize={26} letterSpacing={6} fill={V.cyan} />
      </Node>
      <Node ref={R} x={450} opacity={0} scale={0.98}>
        <Rect size={[W, H]} radius={16} clip stroke={V.line} lineWidth={3}>
          <Node ref={rwrap}>
            <ShotA refFn={ra} subjX={() => subjX()} />
            <Circle size={() => maskR()} x={() => subjX() + 75} y={20} clip>
              <Node x={() => -(subjX() + 75)} y={-20}>
                <ShotB refFn={rb} />
              </Node>
            </Circle>
            <Circle size={() => maskR()} x={() => subjX() + 75} y={20} stroke={V.ink} lineWidth={() => (maskR() > 5 && maskR() < 1500 ? 4 : 0)} />
            <Rect x={() => typeX()} y={-40} width={900} height={110} fill={V.violet + 'dd'} rotation={-6}>
              <Txt text={'THE DROP'} fontFamily={FONT} fontWeight={900} fontSize={84} letterSpacing={12} fill={V.bg} />
            </Rect>
          </Node>
        </Rect>
        <Txt y={-H / 2 - 40} text={'APPROACH 2'} fontFamily={MONO} fontWeight={700} fontSize={26} letterSpacing={6} fill={V.violet} />
      </Node>
    </Node>,
  );

  /* ---------- line 0 ---------- */
  yield* sequence(0.2, popIn(L(), 0.6, 30), popIn(R(), 0.6, 30));
  const prob = createRef<Node>();
  view.add(
    <Node ref={prob} y={190} opacity={0}>
      <Chip text={'SAME PROBLEM:  SHOT A  →  SHOT B  ON THE DROP'} color={V.ink} size={24} />
    </Node>,
  );
  yield* prob().opacity(1, 0.5);

  /* ---------- line 1-2: approach 1 ---------- */
  yield* nar.at(1);
  yield* all(R().opacity(0.35, 0.4), prob().opacity(0, 0.4));
  const runA = function* () {
    lb().opacity(0);
    la().opacity(1);
    lwrap().scale(1);
    lwrap().position(Vector2.zero);
    sfx('riser', 0.8);
    yield* lwrap().scale(2.4, 0.8, easeInExpo);
    sfx('impact');
    la().opacity(0);
    lb().opacity(1);
    lwrap().scale(1.5);
    yield* all(lflash().opacity(0.9, 0.04).to(0, 0.3), lwrap().scale(1, 0.4, easeOutExpo));
    for (let k = 0; k < 8; k++) {
      const a = 26 * Math.pow(0.7, k);
      yield* lwrap().position(new Vector2(k % 2 ? a : -a, k % 2 ? -a / 2 : a / 2), 0.045);
    }
    yield* lwrap().position(Vector2.zero, 0.05);
    yield* waitFor(0.9);
  };
  yield* runA();
  yield* nar.at(2);
  const tagsL = createRef<Node>();
  view.add(
    <Node ref={tagsL} x={-450} y={140}>
      {['FAST', 'READABLE', 'INSTANT HIT'].map((t, i) => (
        <Node x={-250 + i * 250} opacity={0}>
          <Chip text={t} color={V.cyan} />
        </Node>
      ))}
    </Node>,
  );
  yield* sequence(0.2, ...tagsL().children().map(n => withSfx('tick', popIn(n, 0.4, 14))));
  yield* runA();

  /* ---------- line 3-4: approach 2 ---------- */
  yield* nar.at(3);
  yield* all(L().opacity(0.35, 0.4), R().opacity(1, 0.4), tagsL().opacity(0.35, 0.4));
  const runB = function* (withType: boolean) {
    maskR(0);
    subjX(-120);
    rwrap().scale(1);
    typeX(-1300);
    sfx('swell', 1.6);
    yield* all(
      subjX(40, 1.6, linear),
      rwrap().scale(1.12, 1.6, easeInOutCubic),
      maskR(1900, 1.6, t => (t < 0.35 ? 0.02 * (t / 0.35) : 0.02 + 0.98 * easeInOutCubic((t - 0.35) / 0.65))),
      withType ? (function* () {
        yield* waitFor(0.5);
        sfx('whoosh');
        yield* typeX(0, 0.5, easeOutExpo);
        yield* waitFor(0.3);
        yield* typeX(1300, 0.35, easeInExpo);
      })() : waitFor(0),
    );
    yield* rwrap().scale(1, 0.6, easeOutExpo);
    yield* waitFor(0.8);
  };
  yield* runB(false);
  yield* nar.at(4);
  yield* runB(true);
  yield* runB(true);

  /* ---------- line 5: the curves ---------- */
  yield* nar.at(5);
  yield* all(L().opacity(0, 0.5), R().opacity(0, 0.5), tagsL().opacity(0, 0.5));
  const t = createSignal(0);
  const curves = createRef<Node>();
  const CW = 560;
  const CH = 300;
  const ease = (x: number) => easeInOutCubic(x);
  const mk = (f: (x: number) => number) =>
    Array.from({length: 60}, (_, i) => [-CW / 2 + (i / 59) * CW, CH / 2 - f(i / 59) * CH] as [number, number]);
  view.add(
    <Node ref={curves} y={-150}>
      {[
        {x: -450, f: (x: number) => x, c: V.muted, lbl: 'LINEAR'},
        {x: 450, f: ease, c: V.violet, lbl: 'SHAPED (EASE IN / OUT)'},
      ].map(g => (
        <Node x={g.x} opacity={0}>
          <Rect width={CW + 80} height={CH + 160} radius={18} fill={V.panel + 'ee'} stroke={V.line} lineWidth={2} />
          <Txt y={-CH / 2 - 44} text={g.lbl} fontFamily={MONO} fontWeight={700} fontSize={22} letterSpacing={4} fill={g.c} />
          <Line points={mk(g.f)} stroke={g.c} lineWidth={5} />
          <Circle size={20} fill={V.ink} position={() => new Vector2(-CW / 2 + t() * CW, CH / 2 - g.f(t()) * CH)} />
          <Line points={[[-CW / 2, CH / 2 + 50], [CW / 2, CH / 2 + 50]]} stroke={V.faint} lineWidth={2} />
          <Circle size={34} fill={g.c} x={() => -CW / 2 + g.f(t()) * CW} y={CH / 2 + 50} />
        </Node>
      ))}
    </Node>,
  );
  yield* sequence(0.2, ...curves().children().map(n => popIn(n, 0.5, 20)));
  for (let k = 0; k < 3; k++) {
    t(0);
    yield* t(1, 1.5, linear);
    yield* waitFor(0.4);
  }

  /* ---------- line 6: trade-off ---------- */
  yield* nar.at(6);
  yield* curves().opacity(0, 0.5);
  const trade = createRef<Node>();
  view.add(
    <Node ref={trade} y={-150}>
      {[
        {k: 'PLANNING NEEDED', a: '▲', c: V.amber},
        {k: 'EASE OF COPYING', a: '▼', c: V.magenta},
      ].map((row, i) => (
        <Node y={-70 + i * 140} opacity={0}>
          <Rect width={980} height={110} radius={16} fill={V.panel + 'ee'} stroke={row.c} lineWidth={2} />
          <Txt x={-440} anchor={[-1, 0]} text={row.k} fontFamily={FONT} fontWeight={800} fontSize={46} fill={V.ink} />
          <Txt x={420} text={row.a} fontFamily={FONT} fontWeight={900} fontSize={60} fill={row.c} />
          <Txt x={300} text={'APPROACH 2'} fontFamily={MONO} fontSize={18} fill={V.muted} />
        </Node>
      ))}
    </Node>,
  );
  yield* sequence(0.3, ...trade().children().map(n => withSfx('tick', popIn(n, 0.5, 20))));

  /* ---------- line 7: note ---------- */
  yield* nar.at(7);
  const st = createRef<Node>();
  view.add(
    <Node ref={st} y={170} opacity={0}>
      <SourceTag text={'GENERIC DEMONSTRATIONS · NOT ATTRIBUTED TO ANY CREATOR'} color={V.inkDim} />
    </Node>,
  );
  yield* st().opacity(1, 0.5);
  yield* nar.end();
  yield* all(trade().opacity(0, 0.6), st().opacity(0, 0.6));
});
