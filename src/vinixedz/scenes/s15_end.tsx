import {Line, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  all,
  createRef,
  createSignal,
  easeInCubic,
  easeInOutCubic,
  easeOutExpo,
  sequence,
  waitFor,
} from '@canvas-commons/core';
import {Chip, openScene, popIn, sfx, withSfx} from '../kit';
import {FONT, MONO, V} from '../theme';

export default makeScene2D(function* (view) {
  const nar = yield* openScene(view, 's15_end', V.cyan);

  /* ---------- line 0 ---------- */
  const q = createRef<Txt>();
  view.add(
    <Txt ref={q} y={-120} width={1300} textWrap textAlign={'center'} text={'DID EDITING EVOLVE SO FAR THAT THE OLD STANDARD STOPPED BEING ENOUGH?'} fontFamily={FONT} fontWeight={900} fontSize={64} lineHeight={78} fill={V.ink} opacity={0} />,
  );
  yield* popIn(q(), 0.8, 30);

  /* ---------- line 1: craft ---------- */
  yield* nar.at(1);
  yield* q().opacity(0, 0.4);
  const craft = createRef<Node>();
  const stage = createRef<Node>();
  view.add(
    <Node ref={craft} x={-440} y={-130} opacity={0}>
      <Rect width={720} height={460} radius={24} fill={V.cyan + '10'} stroke={V.cyan} lineWidth={3} />
      <Txt y={-150} text={'THE CRAFT'} fontFamily={FONT} fontWeight={900} fontSize={68} fill={V.cyan} />
      <Txt y={-30} text={'MANIPULATING TIME'} fontFamily={MONO} fontWeight={700} fontSize={28} fill={V.inkDim} />
      <Txt y={30} text={'↓'} fontFamily={FONT} fontWeight={900} fontSize={48} fill={V.cyan} />
      <Txt y={90} text={'CONSTRUCTING IMAGES'} fontFamily={MONO} fontWeight={700} fontSize={28} fill={V.ink} />
    </Node>,
  );
  view.add(
    <Node ref={stage} x={440} y={-130} opacity={0}>
      <Rect width={720} height={460} radius={24} fill={V.magenta + '10'} stroke={V.magenta} lineWidth={3} />
      <Txt y={-150} text={'THE STAGE'} fontFamily={FONT} fontWeight={900} fontSize={68} fill={V.magenta} />
      {['VERTICAL FEEDS', 'PAID SHORTS', 'SWIPE METRICS', 'GLOBAL FANDOMS'].map((t, i) => (
        <Node y={-50 + i * 66} opacity={0}>
          <Chip text={t} color={V.magenta} size={22} />
        </Node>
      ))}
    </Node>,
  );
  yield* withSfx('pop', popIn(craft(), 0.6, 30));

  /* ---------- line 2: stage ---------- */
  yield* nar.at(2);
  yield* withSfx('pop', popIn(stage(), 0.6, 30));
  yield* sequence(0.2, ...stage().children().slice(2).map(n => withSfx('tick', popIn(n, 0.4, 14))));

  /* ---------- line 3: both at once ---------- */
  yield* nar.at(3);
  sfx('whooshBig');
  yield* all(craft().x(-372, 1.0, easeInOutCubic), stage().x(372, 1.0, easeInOutCubic), craft().opacity(0.85, 1), stage().opacity(0.85, 1));
  const both = createRef<Node>();
  view.add(
    <Node ref={both} y={-130} opacity={0}>
      <Rect layout padding={[16, 30]} radius={12} fill={V.bg + 'ee'} stroke={V.ink} lineWidth={3}>
        <Txt text={'THE NEW GENERATION: BOTH AT ONCE'} fontFamily={MONO} fontWeight={700} fontSize={32} letterSpacing={4} fill={V.ink} />
      </Rect>
    </Node>,
  );
  sfx('impact');
  yield* popIn(both(), 0.5, 20);

  /* ---------- line 4-5: the language beneath ---------- */
  yield* nar.at(4);
  const base = createRef<Node>();
  view.add(
    <Node ref={base} y={190} opacity={0}>
      <Rect width={1460} height={90} radius={12} fill={V.green + '22'} stroke={V.green} lineWidth={3} />
      <Txt text={'THE LANGUAGE · BUILT BY THE GENERATION BEFORE'} fontFamily={MONO} fontWeight={700} fontSize={28} letterSpacing={3} fill={V.green} />
    </Node>,
  );
  yield* all(craft().y(-170, 0.8, easeInOutCubic), stage().y(-170, 0.8, easeInOutCubic), both().y(-170, 0.8, easeInOutCubic));
  yield* withSfx('sub', popIn(base(), 0.6, 40));

  yield* nar.at(5);
  const brace = createRef<Line>();
  view.add(<Line ref={brace} points={[[-760, -440], [-800, -440], [-800, 235], [-760, 235]]} stroke={V.ink} lineWidth={3} end={0} />);
  const brace2 = createRef<Line>();
  view.add(<Line ref={brace2} points={[[760, -440], [800, -440], [800, 235], [760, 235]]} stroke={V.ink} lineWidth={3} end={0} />);
  yield* all(brace().end(1, 1.0, easeInOutCubic), brace2().end(1, 1.0, easeInOutCubic));

  /* ---------- line 6: the standard moved ---------- */
  yield* nar.at(6);
  yield* all(craft().opacity(0, 0.5), stage().opacity(0, 0.5), both().opacity(0, 0.5), base().opacity(0, 0.5), brace().opacity(0, 0.5), brace2().opacity(0, 0.5));
  const lvl = createSignal(120);
  const lx = createSignal(0);
  const level = createRef<Line>();
  view.add(
    <Line
      ref={level}
      points={() => [[-700 + lx(), lvl()], [700 + lx(), lvl()]]}
      stroke={V.cyan}
      lineWidth={6}
      shadowColor={V.cyan}
      shadowBlur={30}
      end={0}
    />,
  );
  yield* level().end(1, 0.8, easeInOutCubic);
  sfx('riser', 1.2);
  yield* lvl(-60, 1.2, easeInOutCubic);
  sfx('whoosh');
  yield* lx(260, 0.6, easeOutExpo);
  const t1 = createRef<Txt>();
  const t2 = createRef<Txt>();
  view.add(<Txt ref={t1} y={-200} text={'IT DID NOT JUST RISE.'} fontFamily={FONT} fontWeight={900} fontSize={88} fill={V.inkDim} opacity={0} />);
  view.add(<Txt ref={t2} y={60} text={'IT MOVED.'} fontFamily={FONT} fontWeight={900} fontSize={150} letterSpacing={10} fill={V.cyan} opacity={0} />);
  yield* popIn(t1(), 0.5, 20);
  sfx('impact');
  yield* all(t2().opacity(1, 0.2), t2().scale(1.3).scale(1, 0.7, easeOutExpo));

  /* ---------- line 7: end card ---------- */
  yield* nar.at(7);
  yield* all(t1().opacity(0, 0.5), t2().opacity(0, 0.5), level().opacity(0, 0.5));
  const end = createRef<Node>();
  const w = createSignal(0);
  view.add(
    <Node ref={end} y={-150}>
      <Rect width={() => w()} height={170} clip>
        <Txt text={'VINIXEDZ'} fontFamily={FONT} fontWeight={900} fontSize={170} letterSpacing={30} fill={V.ink} />
      </Rect>
      <Txt y={130} text={'DOCUMENTING THE EVOLUTION OF EDITING'} fontFamily={MONO} fontWeight={700} fontSize={26} letterSpacing={10} fill={V.cyan} opacity={0} />
    </Node>,
  );
  sfx('impact');
  yield* w(1500, 1.0, easeOutExpo);
  yield* end().children()[1].opacity(1, 0.6);
  yield* nar.end();

  /* credits */
  const cr = createRef<Node>();
  view.add(
    <Node ref={cr} y={250} opacity={0}>
      <Txt y={-20} text={'Sources and bibliography: see the description'} fontFamily={FONT} fontWeight={500} fontSize={28} fill={V.inkDim} />
      <Txt y={26} text={'Music and sound design: original · Motion graphics: built for this film'} fontFamily={FONT} fontWeight={500} fontSize={28} fill={V.inkDim} />
      <Txt y={72} text={'Creator footage used for commentary and analysis, credited on screen'} fontFamily={FONT} fontWeight={500} fontSize={28} fill={V.inkDim} />
    </Node>,
  );
  yield* cr().opacity(1, 0.8);
  yield* waitFor(6);
  sfx('swell', 3);
  yield* all(end().opacity(0, 2.5, easeInCubic), cr().opacity(0, 2.5, easeInCubic));
  yield* waitFor(1.5);
});
