import {Circle, Gradient, Line, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  Vector2,
  all,
  createRef,
  createSignal,
  easeInOutCubic,
  easeOutCubic,
  easeOutExpo,
  sequence,
  waitFor,
} from '@canvas-commons/core';
import {Chip, headline, openScene, popIn, rng, sfx, withSfx} from '../kit';
import {FONT, MONO, V} from '../theme';

export default makeScene2D(function* (view) {
  const nar = yield* openScene(view, 's13_ceiling', V.violet);

  /* ---------- line 0 ---------- */
  const h0 = yield* headline(view, 'THE PARADOX', {y: -110, size: 140});
  yield* waitFor(2);

  /* ---------- line 1-3: floor & ceiling ---------- */
  yield* nar.at(1);
  yield* all(h0.opacity(0, 0.4));
  const floorY = createSignal(-120);
  const ceilY = createSignal(-120);
  const g = createRef<Node>();
  view.add(
    <Node ref={g} y={-110}>
      <Rect
        x={-250}
        width={500}
        y={() => (floorY() + ceilY()) / 2}
        height={() => Math.max(0, floorY() - ceilY())}
        fill={
          new Gradient({
            type: 'linear',
            from: [0, -300],
            to: [0, 300],
            stops: [
              {offset: 0, color: V.magenta + '30'},
              {offset: 1, color: V.green + '30'},
            ],
          })
        }
      />
      <Line points={() => [[-560, floorY()], [60, floorY()]]} stroke={V.green} lineWidth={6} />
      <Line points={() => [[-560, ceilY()], [60, ceilY()]]} stroke={V.magenta} lineWidth={6} />
      <Txt x={-600} anchor={[1, 0]} y={() => floorY()} text={'FLOOR'} fontFamily={MONO} fontWeight={700} fontSize={26} letterSpacing={4} fill={V.green} />
      <Txt x={-600} anchor={[1, 0]} y={() => ceilY()} text={'CEILING'} fontFamily={MONO} fontWeight={700} fontSize={26} letterSpacing={4} fill={V.magenta} />
    </Node>,
  );
  const floorChips = createRef<Node>();
  const ceilChips = createRef<Node>();
  view.add(
    <Node ref={floorChips} x={420} y={-110 + 300}>
      {['PHONE APP', 'FREE PRESET'].map((c, i) => (
        <Node x={-150 + i * 290} opacity={0}>
          <Chip text={c} color={V.green} size={22} />
        </Node>
      ))}
    </Node>,
  );
  view.add(
    <Node ref={ceilChips} x={460} y={-110 - 330}>
      {['AFTER EFFECTS', 'PLUGINS', 'AI UPSCALER', 'POWERFUL COMPUTER'].map((c, i) => (
        <Node x={(i % 2) * 330 - 160} y={Math.floor(i / 2) * 64} opacity={0}>
          <Chip text={c} color={V.magenta} size={22} />
        </Node>
      ))}
    </Node>,
  );
  sfx('sub');
  yield* floorY(300, 1.6, easeInOutCubic);
  yield* sequence(0.2, ...floorChips().children().map(n => withSfx('tick', popIn(n, 0.4, 14))));

  yield* nar.at(2);
  sfx('riser', 1.6);
  yield* ceilY(-330, 1.6, easeInOutCubic);
  yield* sequence(0.2, ...ceilChips().children().map(n => withSfx('tick', popIn(n, 0.4, 14))));

  yield* nar.at(3);
  const gapTxt = createRef<Node>();
  view.add(
    <Node ref={gapTxt} x={-250} y={-110} opacity={0}>
      <Txt y={-36} text={'EASIER TO START'} fontFamily={FONT} fontWeight={900} fontSize={40} fill={V.green} />
      <Txt y={30} text={'HARDER TO STAND OUT'} fontFamily={FONT} fontWeight={900} fontSize={40} fill={V.magenta} />
    </Node>,
  );
  yield* popIn(gapTxt(), 0.6, 20);

  /* ---------- line 4 ---------- */
  yield* nar.at(4);
  yield* all(g().opacity(0, 0.5), floorChips().opacity(0, 0.5), ceilChips().opacity(0, 0.5), gapTxt().opacity(0, 0.5));
  const h4 = yield* headline(view, 'NOT A STORY ABOUT LOST TALENT', {y: -110, size: 76});

  /* ---------- line 5: grammar everywhere -> ordinary ---------- */
  yield* nar.at(5);
  yield* h4.opacity(0, 0.4);
  const net = createRef<Node>();
  const spread = createSignal(0);
  const r = rng(3);
  const nodes = Array.from({length: 44}, (_, k) => {
    const a = r() * Math.PI * 2;
    const d = 160 + r() * 520;
    return {x: Math.cos(a) * d * 1.25, y: Math.sin(a) * d * 0.5, t: (d - 160) / 520};
  });
  const hub = createRef<Circle>();
  view.add(
    <Node ref={net} y={-110}>
      {nodes.map(n => (
        <Line points={[[0, 0], [n.x, n.y]]} stroke={V.green + '55'} lineWidth={1.5} end={() => Math.min(1, Math.max(0, (spread() - n.t * 0.7) / 0.3))} />
      ))}
      {nodes.map(n => (
        <Circle x={n.x} y={n.y} size={18} fill={V.green} opacity={() => (spread() > n.t * 0.7 + 0.28 ? 1 : 0)} />
      ))}
      <Circle ref={hub} size={210} fill={V.green} />
      <Txt text={'THE\nGRAMMAR'} textAlign={'center'} fontFamily={FONT} fontWeight={900} fontSize={30} lineHeight={34} fill={V.bg} />
    </Node>,
  );
  sfx('swell', 2.5);
  yield* spread(1, 2.5, easeInOutCubic);
  const ord = createRef<Txt>();
  view.add(<Txt ref={ord} y={180} text={'EVERYWHERE  →  ORDINARY'} fontFamily={MONO} fontWeight={700} fontSize={32} letterSpacing={6} fill={V.inkDim} opacity={0} />);
  yield* all(ord().opacity(1, 0.6), hub().fill(V.muted, 1.4), ...net().children().slice(44, 88).map(c => (c as Circle).fill(V.muted, 1.4)));

  /* ---------- line 6: three paths ---------- */
  yield* nar.at(6);
  yield* all(net().opacity(0, 0.5), ord().opacity(0, 0.5));
  const paths = createRef<Node>();
  const pe = createSignal(0);
  const ends: [number, number, string, string][] = [
    [-560, -340, 'AUDIENCES → NEW FORMATS', V.cyan],
    [0, -380, 'SOME EDITORS MOVED WITH THEM', V.green],
    [560, -340, 'OTHERS KEPT THEIR STYLE', V.amber],
  ];
  view.add(
    <Node ref={paths} y={-110 + 200}>
      <Circle size={40} fill={V.ink} />
      {ends.map(([x, y, , c]) => (
        <Line points={[[0, 0], [x * 0.5, y * 0.6], [x, y]]} radius={60} stroke={c} lineWidth={5} end={() => pe()} endArrow arrowSize={16} />
      ))}
      {ends.map(([x, y, t, c]) => (
        <Txt x={x} y={y - 40} text={t} fontFamily={MONO} fontWeight={700} fontSize={22} letterSpacing={2} fill={c} opacity={() => pe()} />
      ))}
    </Node>,
  );
  sfx('whoosh');
  yield* pe(1, 1.6, easeInOutCubic);

  /* ---------- line 7: possible causes ---------- */
  yield* nar.at(7);
  yield* paths().opacity(0, 0.5);
  const causes = ['FORMAT CHANGES', 'RECOMMENDATION SHIFTS', 'UPLOAD PAUSES', 'AUDIENCE FATIGUE', 'QUALITY'];
  const cz = createRef<Node>();
  view.add(
    <Node ref={cz} y={-110}>
      <Txt y={-230} text={'A DROP IN ENGAGEMENT CAN REFLECT…'} fontFamily={MONO} fontWeight={700} fontSize={26} letterSpacing={5} fill={V.muted} />
      {causes.map((c, i) => (
        <Node x={(i % 3) * 520 - 520 + (i >= 3 ? 260 : 0)} y={i < 3 ? -80 : 60} opacity={0}>
          <Rect width={470} height={100} radius={16} fill={V.panel + 'ee'} stroke={V.amber} lineWidth={2} />
          <Txt text={c} fontFamily={FONT} fontWeight={800} fontSize={32} fill={V.ink} />
        </Node>
      ))}
      <Txt y={200} text={'equal weight shown on purpose: which one applies is unknown'} fontFamily={MONO} fontSize={20} fill={V.muted} />
    </Node>,
  );
  yield* sequence(0.2, ...cz().children().slice(1, 6).map(n => withSfx('tick', popIn(n, 0.4, 16))));

  /* ---------- line 8: private analytics ---------- */
  yield* nar.at(8);
  yield* cz().opacity(0, 0.5);
  const lock = createRef<Node>();
  view.add(
    <Node ref={lock} y={-130} opacity={0}>
      <Rect y={40} width={220} height={170} radius={24} fill={V.panel2} stroke={V.ink} lineWidth={5} />
      <Line points={[[-60, -45], [-60, -100], [60, -100], [60, -45]]} radius={60} stroke={V.ink} lineWidth={14} />
      <Circle y={30} size={34} fill={V.ink} />
      <Rect y={64} width={12} height={40} radius={6} fill={V.ink} />
      <Txt y={200} text={'EACH CHANNEL’S OWN ANALYTICS'} fontFamily={MONO} fontWeight={700} fontSize={28} letterSpacing={5} fill={V.inkDim} />
    </Node>,
  );
  sfx('shutter');
  yield* popIn(lock(), 0.6, 30);
  yield* nar.end();
  yield* lock().opacity(0, 0.6);
});
