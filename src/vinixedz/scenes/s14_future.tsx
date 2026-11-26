import {Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  all,
  createRef,
  createSignal,
  easeInOutCubic,
  easeOutExpo,
  sequence,
  waitFor,
} from '@canvas-commons/core';
import {DateCard, headline, openScene, popIn, refs, rng, sfx} from '../kit';
import {FONT, MONO, V} from '../theme';

export default makeScene2D(function* (view) {
  const nar = yield* openScene(view, 's14_future', V.magenta);

  /* ---------- line 0 ---------- */
  const h0 = yield* headline(view, 'WHERE NEXT?', {y: -110, size: 160});
  yield* waitFor(1.5);

  /* ---------- line 1: Veo 3 ---------- */
  yield* nar.at(1);
  yield* h0.opacity(0, 0.4);
  const c = createRef<Node>();
  view.add(
    <Node ref={c} y={-130} opacity={0}>
      <DateCard
        date={'JUN 2025'}
        title={'Google’s Veo 3 video model is coming to Shorts'}
        body={'Announced alongside the 200-billion daily views figure'}
        src={refs('tubefilter-veo3')}
        color={V.green}
        w={860}
        opacity={1}
      />
    </Node>,
  );
  yield* popIn(c(), 0.6, 30);

  /* ---------- line 2: speculation zone ---------- */
  yield* nar.at(2);
  yield* c().opacity(0, 0.4);
  const zone = createRef<Rect>();
  const zl = createRef<Txt>();
  view.add(<Rect ref={zone} size={[1840, 1000]} y={-10} radius={24} stroke={V.magenta} lineWidth={4} lineDash={[24, 16]} opacity={0} />);
  view.add(<Txt ref={zl} y={-470} text={'SPECULATION ZONE'} fontFamily={MONO} fontWeight={700} fontSize={28} letterSpacing={12} fill={V.magenta} opacity={0} />);
  sfx('glitch');
  yield* all(zone().opacity(1, 0.3), zl().opacity(1, 0.3), zone().scale(1.04).scale(1, 0.5, easeOutExpo));

  /* ---------- line 3: density becomes cheap ---------- */
  yield* nar.at(3);
  const stack = createRef<Node>();
  const r = rng(8);
  const N = 26;
  view.add(
    <Node ref={stack} y={-120}>
      {Array.from({length: N}, (_, k) => (
        <Rect
          x={(r() - 0.5) * 900}
          y={(r() - 0.5) * 380}
          width={360}
          height={203}
          radius={10}
          fill={[V.cyan, V.magenta, V.amber, V.violet][k % 4] + '14'}
          stroke={[V.cyan, V.magenta, V.amber, V.violet][k % 4] + '66'}
          lineWidth={2}
          rotation={(r() - 0.5) * 20}
          opacity={0}
        />
      ))}
    </Node>,
  );
  sfx('riser', 2.4);
  yield* sequence(0.07, ...stack().children().map(n => all(n.opacity(1, 0.3), n.scale(0.6).scale(1, 0.4, easeOutExpo))));
  const lbl = createRef<Txt>();
  view.add(<Txt ref={lbl} y={-120} text={'VISUAL DENSITY, ON DEMAND?'} fontFamily={FONT} fontWeight={900} fontSize={72} fill={V.ink} opacity={0} />);
  yield* lbl().opacity(1, 0.5);

  /* ---------- line 4: taste ---------- */
  yield* nar.at(4);
  sfx('whooshBig');
  yield* all(
    lbl().opacity(0, 0.4),
    ...stack().children().map(n => all(n.x(0, 1.2, easeInOutCubic), n.y(0, 1.2, easeInOutCubic), n.rotation(0, 1.2, easeInOutCubic), n.opacity(0, 1.2))),
  );
  const taste = createRef<Node>();
  view.add(
    <Node ref={taste} y={-130} opacity={0}>
      <Txt text={'TASTE'} fontFamily={FONT} fontWeight={900} fontSize={220} letterSpacing={24} fill={V.ink} />
      <Txt y={160} text={'MOMENT  ·  MUSIC  ·  MEANING'} fontFamily={MONO} fontWeight={700} fontSize={34} letterSpacing={10} fill={V.magenta} />
    </Node>,
  );
  sfx('impact');
  yield* all(taste().opacity(1, 0.4), taste().scale(1.15).scale(1, 1.0, easeOutExpo));

  /* ---------- line 5: what they leave out ---------- */
  yield* nar.at(5);
  yield* taste().opacity(0, 0.5);
  const one = createRef<Node>();
  const fade = createSignal(1);
  view.add(
    <Node ref={one} y={-120}>
      {Array.from({length: 7}, (_, k) => (
        <Rect
          y={(3 - k) * 22}
          x={(3 - k) * 22}
          width={720}
          height={405}
          radius={14}
          fill={k === 6 ? V.panel : '#00000000'}
          stroke={k === 6 ? V.ink : V.inkDim + '55'}
          lineWidth={k === 6 ? 3 : 2}
          opacity={() => (k === 6 ? 1 : fade())}
        />
      ))}
      <Txt text={'WHAT THEY CHOOSE\nTO LEAVE OUT'} textAlign={'center'} fontFamily={FONT} fontWeight={900} fontSize={56} lineHeight={64} fill={V.ink} x={-66} y={-66} />
    </Node>,
  );
  yield* popIn(one(), 0.6, 20);
  sfx('swell', 2.2);
  yield* all(fade(0, 2.2, easeInOutCubic), ...one().children().slice(0, 6).map(n => n.position([-66, -66], 2.2, easeInOutCubic)));
  yield* nar.end();
  yield* all(one().opacity(0, 0.7), zone().opacity(0, 0.7), zl().opacity(0, 0.7));
});
