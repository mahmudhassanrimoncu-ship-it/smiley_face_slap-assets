import {Circle, Line, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  ThreadGenerator,
  all,
  createRef,
  createSignal,
  easeInOutCubic,
  easeOutCubic,
  easeOutExpo,
  linear,
  loop,
  sequence,
  waitFor,
} from '@canvas-commons/core';
import {SourceTag, headline, openScene, popIn, refs, sfx, withSfx} from '../kit';
import {FONT, MONO, V} from '../theme';

const HYP = [
  {n: '1', t: 'THE STAGE', c: V.magenta},
  {n: '2', t: 'SUBJECT GRAVITY', c: V.green},
  {n: '3', t: 'NAME → STYLE', c: V.amber},
  {n: '4', t: 'DIFFUSION', c: V.cyan},
  {n: '5', t: 'LEVERAGE', c: V.violet},
];

const TITLES = [
  {t: 'Heisty Like Composition Tutorial', k: 'yt-heisty-like-comp'},
  {t: 'Eagle Stan Like Pennywise Edit In Alight Motion (+Preset)', k: 'yt-eaglestan-like'},
  {t: '@10Mov_Edits Like Shatter Effects On Alight Motion (+Full Materials)', k: 'yt-10mov-like'},
  {t: 'Fictic Editz Like Full Edit Preset On Alight Motion (+Preset)', k: 'yt-fictic-like'},
  {t: '@slicx7 Like New FC26 Cover Edits tutorial on capcut', k: 'yt-slicx7-like'},
];

export default makeScene2D(function* (view) {
  const nar = yield* openScene(view, 's12_why', V.amber);

  /* ---------- line 0 ---------- */
  const h0 = yield* headline(view, 'IF NOT ONLY COMPLEXITY…', {y: -110, size: 96});
  yield* waitFor(2);

  /* ---------- line 1: five chips ---------- */
  yield* nar.at(1);
  yield* h0.opacity(0, 0.4);
  const row = createRef<Node>();
  view.add(
    <Node ref={row} y={-440}>
      {HYP.map((h, i) => (
        <Node x={-720 + i * 360} opacity={0}>
          <Rect width={330} height={70} radius={35} fill={h.c + '14'} stroke={h.c + '66'} lineWidth={2} />
          <Circle x={-130} size={44} fill={h.c + '44'} />
          <Txt x={-130} text={h.n} fontFamily={FONT} fontWeight={900} fontSize={26} fill={V.ink} />
          <Txt x={20} text={h.t} fontFamily={MONO} fontWeight={700} fontSize={20} letterSpacing={2} fill={h.c} />
        </Node>
      ))}
    </Node>,
  );
  yield* sequence(0.15, ...row().children().map(n => withSfx('tick', popIn(n, 0.4, -20))));
  const big = createRef<Txt>();
  view.add(<Txt ref={big} y={-110} text={'FIVE HYPOTHESES'} fontFamily={FONT} fontWeight={900} fontSize={110} fill={V.ink} opacity={0} />);
  yield* big().opacity(1, 0.5);

  const focus = function* (i: number): ThreadGenerator {
    sfx('whoosh');
    yield* all(
      ...row().children().map((n, k) =>
        all(
          ((n as Node).children()[0] as Rect).fill(k === i ? HYP[k].c + '44' : HYP[k].c + '10', 0.4),
          ((n as Node).children()[0] as Rect).stroke(k === i ? HYP[k].c : HYP[k].c + '44', 0.4),
          n.scale(k === i ? 1.08 : 0.96, 0.4),
        ),
      ),
    );
  };
  let stage: Node | null = null;
  const swap = function* (node: Node): ThreadGenerator {
    if (stage) {
      const s = stage;
      yield* all(s.opacity(0, 0.4), s.y(s.y() - 30, 0.4));
      s.remove();
    }
    view.add(node);
    stage = node;
    yield* popIn(node, 0.6, 30);
  };

  /* ---------- line 2: the stage ---------- */
  yield* nar.at(2);
  yield* big().opacity(0, 0.3);
  yield* focus(0);
  const feed = createSignal(0);
  yield* swap(
    <Node y={-110}>
      <Rect width={300} height={540} radius={36} fill={'#000'} stroke={V.ink} lineWidth={4} clip>
        <Node y={() => -((feed() % 1) * 540)}>
          {[0, 1, 2].map(k => (
            <Rect y={k * 540} width={270} height={500} radius={14} fill={[V.magenta, V.cyan, V.amber][k] + '22'} stroke={[V.magenta, V.cyan, V.amber][k] + '66'} lineWidth={2} />
          ))}
        </Node>
      </Rect>
      <Node x={-380}>
        <Txt text={'$'} fontFamily={FONT} fontWeight={900} fontSize={140} fill={V.green} />
        <Txt y={110} text={'PAID FEED'} fontFamily={MONO} fontWeight={700} fontSize={22} letterSpacing={4} fill={V.green} />
      </Node>
      <Node x={380}>
        <Line points={[[0, 80], [0, -80]]} stroke={V.magenta} lineWidth={8} endArrow arrowSize={26} />
        <Txt y={130} text={'SWIPE-RANKED'} fontFamily={MONO} fontWeight={700} fontSize={22} letterSpacing={4} fill={V.magenta} />
      </Node>
    </Node> as unknown as Node,
  );
  yield loop(Infinity, function* () {
    yield* waitFor(0.9);
    yield* feed(feed() + 1, 0.45, easeInOutCubic);
  });

  /* ---------- line 3: subject gravity ---------- */
  yield* nar.at(3);
  yield* focus(1);
  const orb = createSignal(0);
  yield* swap(
    <Node y={-110}>
      <Circle x={-250} size={300} fill={V.green + '22'} stroke={V.green} lineWidth={3} />
      <Txt x={-250} text={'FOOTBALL'} fontFamily={FONT} fontWeight={900} fontSize={40} fill={V.green} />
      <Circle x={300} size={230} fill={V.amber + '22'} stroke={V.amber} lineWidth={3} />
      <Txt x={300} text={'FILM'} fontFamily={FONT} fontWeight={900} fontSize={40} fill={V.amber} />
      {Array.from({length: 14}, (_, k) => (
        <Circle
          size={16}
          fill={V.ink}
          x={() => (k < 8 ? -250 : 300) + Math.cos(orb() + k * 0.8) * (k < 8 ? 220 : 175)}
          y={() => Math.sin(orb() + k * 0.8) * (k < 8 ? 120 : 95)}
        />
      ))}
      <Txt y={250} text={'existing audiences pull edits into orbit'} fontFamily={MONO} fontSize={22} fill={V.muted} />
    </Node> as unknown as Node,
  );
  yield orb(40, 60, linear);

  /* ---------- line 4-5: the name becomes the style ---------- */
  yield* nar.at(4);
  yield* focus(2);
  yield* swap(
    <Node y={-110}>
      <Txt text={'THE NAME BECOMES THE STYLE'} fontFamily={FONT} fontWeight={900} fontSize={88} fill={V.amber} />
    </Node> as unknown as Node,
  );
  yield* nar.at(5);
  const list = createRef<Node>();
  yield* swap(
    <Node ref={list} y={-110}>
      <Rect y={-250} width={1300} height={70} radius={35} fill={V.panel2} stroke={V.line} lineWidth={2}>
        <Txt x={-600} anchor={[-1, 0]} text={'SEARCH ›  "… like" tutorial'} fontFamily={MONO} fontSize={26} fill={V.inkDim} />
      </Rect>
      {TITLES.map((t, i) => (
        <Node y={-150 + i * 84} opacity={0}>
          <Rect width={1300} height={70} radius={12} fill={V.panel + 'ee'} stroke={V.line} lineWidth={1.5} />
          <Rect x={-610} width={50} height={36} radius={6} fill={V.red + 'cc'} />
          <Txt x={-570} anchor={[-1, 0]} text={t.t} fontFamily={FONT} fontWeight={600} fontSize={28} fill={V.ink} />
          <Txt x={620} anchor={[1, 0]} text={refs(t.k)} fontFamily={MONO} fontSize={20} fill={V.muted} />
        </Node>
      ))}
    </Node> as unknown as Node,
  );
  yield* sequence(0.3, ...list().children().slice(1).map(n => withSfx('tick', popIn(n, 0.4, 16))));
  const tagT = createRef<Node>();
  view.add(<Node ref={tagT} y={275} opacity={0}><SourceTag text={'REAL VIDEO TITLES, QUOTED AS PUBLISHED'} /></Node>);
  yield* tagT().opacity(1, 0.4);

  /* ---------- line 6: a brand ---------- */
  yield* nar.at(6);
  yield* tagT().opacity(0, 0.3);
  yield* swap(
    <Node y={-110}>
      <Rect width={720} height={300} radius={24} stroke={V.amber} lineWidth={5} fill={V.amber + '12'} />
      <Txt y={-40} text={'NAME'} fontFamily={FONT} fontWeight={900} fontSize={110} fill={V.ink} />
      <Txt y={70} text={'= A RECOGNISABLE LOOK'} fontFamily={MONO} fontWeight={700} fontSize={32} letterSpacing={3} fill={V.amber} />
    </Node> as unknown as Node,
  );

  /* ---------- line 7: diffusion ---------- */
  yield* nar.at(7);
  yield* focus(3);
  const diff = createRef<Node>();
  const flow = createSignal(0);
  yield* swap(
    <Node ref={diff} y={-110}>
      <Rect x={-480} width={460} height={290} radius={18} fill={V.panel2} stroke={V.cyan} lineWidth={3} />
      <Txt x={-480} y={-40} text={'AFTER EFFECTS'} fontFamily={MONO} fontWeight={700} fontSize={30} fill={V.cyan} />
      <Txt x={-480} y={20} text={'original style'} fontFamily={FONT} fontWeight={500} fontSize={26} fill={V.inkDim} />
      {[0, 1, 2].map(k => (
        <Node x={360 + (k - 1) * 200} y={(k - 1) * 30}>
          <Rect width={150} height={270} radius={22} fill={'#000'} stroke={V.inkDim} lineWidth={3} />
          <Txt text={['ALIGHT\nMOTION', 'CAPCUT', 'ALIGHT\nMOTION'][k]} textAlign={'center'} fontFamily={MONO} fontWeight={700} fontSize={20} fill={V.inkDim} />
        </Node>
      ))}
      {[0, 1, 2].map(k => (
        <Line points={[[-240, 0], [360 + (k - 1) * 200 - 80, (k - 1) * 30]]} stroke={V.cyan} lineWidth={3} lineDash={[10, 10]} end={() => flow()} endArrow arrowSize={14} />
      ))}
      <Txt y={240} text={'tutorials named above recreate styles on phones ' + refs('yt-eaglestan-like', 'yt-10mov-like', 'yt-fictic-like', 'yt-slicx7-like')} fontFamily={MONO} fontSize={20} fill={V.muted} />
    </Node> as unknown as Node,
  );
  sfx('whoosh');
  yield* flow(1, 1.2, easeInOutCubic);

  /* ---------- line 8-9: rarity and arms race ---------- */
  yield* nar.at(8);
  const ar = createRef<Node>();
  const lift = createSignal(0);
  yield* swap(
    <Node ref={ar} y={-110}>
      {[0, 1, 2, 3, 4].map(k => (
        <Node x={-520 + k * 260}>
          <Rect y={() => 220 - (60 + k * 70 * lift()) / 2} width={150} height={() => 60 + k * 70 * lift()} radius={10} fill={V.cyan + '33'} stroke={V.cyan} lineWidth={2} />
          <Txt y={250} text={`MOVE ${k + 1}`} fontFamily={MONO} fontSize={18} fill={V.muted} />
          <Rect y={() => 190 - k * 70 * lift() - 40} width={() => 140 * (1 - k * 0.18)} height={10} radius={5} fill={V.magenta} opacity={() => lift()} />
        </Node>
      ))}
      <Txt x={-520} y={-250} anchor={[-1, 0]} text={'■ complexity of each signature move'} fontFamily={MONO} fontSize={20} fill={V.cyan} />
      <Txt x={-520} y={-215} anchor={[-1, 0]} text={'▬ how long it stays rare (illustrative)'} fontFamily={MONO} fontSize={20} fill={V.magenta} />
    </Node> as unknown as Node,
  );
  sfx('riser', 2);
  yield* lift(1, 2, easeInOutCubic);
  yield* nar.at(9);
  const armTxt = createRef<Txt>();
  view.add(<Txt ref={armTxt} y={-360} x={260} text={'AN ARMS RACE'} fontFamily={FONT} fontWeight={900} fontSize={64} fill={V.magenta} opacity={0} />);
  sfx('impact');
  yield* popIn(armTxt(), 0.5, 20);

  /* ---------- line 10: leverage ---------- */
  yield* nar.at(10);
  yield* armTxt().opacity(0, 0.3);
  yield* focus(4);
  const tilt = createSignal(10);
  yield* swap(
    <Node y={-80}>
      <Line points={[[-60, 180], [0, 80], [60, 180]]} closed fill={V.panel2} stroke={V.violet} lineWidth={3} />
      <Node y={80} rotation={() => tilt()}>
        <Rect width={1000} height={18} radius={9} fill={V.violet} />
        <Rect x={-420} y={-60} width={90} height={100} radius={10} fill={V.ink} />
        <Txt x={-420} y={-140} text={'1 EDITOR'} fontFamily={MONO} fontWeight={700} fontSize={22} fill={V.ink} />
        <Rect x={360} y={-110} width={260} height={200} radius={14} fill={V.violet + '33'} stroke={V.violet} lineWidth={3} />
        <Txt x={360} y={-110} text={'WORK'} fontFamily={FONT} fontWeight={900} fontSize={48} fill={V.violet} />
      </Node>
      <Txt y={-260} text={'SCRIPTS · PRESETS · AI TOOLS'} fontFamily={MONO} fontWeight={700} fontSize={28} letterSpacing={5} fill={V.violet} />
      <Txt y={250} text={'e.g. "Edit 10x Faster With This Free After Effects Script" ' + refs('yt-ae-script-10x')} fontFamily={MONO} fontSize={19} fill={V.muted} />
    </Node> as unknown as Node,
  );
  sfx('swell', 1.5);
  yield* tilt(-12, 1.5, easeInOutCubic);

  /* ---------- line 11-13: synthesis ring ---------- */
  yield* nar.at(11);
  const ring = createRef<Node>();
  const segs = [
    {t: 'COMPLEXITY', c: V.ink},
    ...HYP.map(h => ({t: h.t, c: h.c})),
  ];
  const grow = createSignal(0);
  yield* swap(
    <Node ref={ring} y={-60}>
      {segs.map((s, k) => (
        <Node>
          <Circle size={440} stroke={s.c} lineWidth={44} startAngle={-90 + k * 60 + 2} endAngle={() => -90 + k * 60 + 2 + 56 * grow()} />
          <Txt
            x={Math.cos(((-90 + k * 60 + 30) * Math.PI) / 180) * 370}
            y={Math.sin(((-90 + k * 60 + 30) * Math.PI) / 180) * 280}
            text={s.t}
            fontFamily={MONO}
            fontWeight={700}
            fontSize={22}
            fill={s.c}
            opacity={() => grow()}
          />
        </Node>
      ))}
      <Txt y={-10} text={'?'} fontFamily={FONT} fontWeight={900} fontSize={120} fill={V.ink} opacity={() => grow()} />
    </Node> as unknown as Node,
  );
  yield* all(...row().children().map(n => n.scale(1, 0.4)));
  sfx('swell', 1.6);
  yield* grow(1, 1.6, easeOutCubic);
  const wn = createRef<Node>();
  view.add(<Node ref={wn} y={300} opacity={0}><SourceTag text={'EQUAL SEGMENTS · RELATIVE WEIGHTS UNKNOWN'} /></Node>);
  yield* wn().opacity(1, 0.4);

  yield* nar.at(13);
  const cx = ring().children()[0] as Node;
  sfx('blip');
  yield* all(cx.scale(1.08, 0.6, easeOutExpo), ...ring().children().slice(1, 6).map(n => n.opacity(0.55, 0.6)));
  yield* nar.end();
  yield* all(ring().opacity(0, 0.6), row().opacity(0, 0.6), wn().opacity(0, 0.6));
});
