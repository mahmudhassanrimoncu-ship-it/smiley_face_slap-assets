import {Circle, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  all,
  createRef,
  createSignal,
  easeInOutCubic,
  easeOutBack,
  easeOutExpo,
  loop,
  sequence,
  waitFor,
} from '@canvas-commons/core';
import {
  FootageSlot,
  Label,
  SourceTag,
  openScene,
  popIn,
  rng,
  sfx,
  slotLog,
} from '../kit';
import {FONT, MONO, V} from '../theme';

export default makeScene2D(function* (view) {
  const nar = yield* openScene(view, 's01_hook', V.magenta);

  /* ---------- phone with a scrolling feed ---------- */
  const phone = createRef<Rect>();
  const feed = createRef<Node>();
  const cardH = 560;
  const feedDescs = [
    'Any short fan edit (football)',
    'Any short fan edit (film)',
    'Any short fan edit (anime)',
    'Any short fan edit (nostalgia)',
    'Any short fan edit (football)',
    'Any short fan edit (film)',
  ];
  view.add(
    <Rect
      ref={phone}
      y={-70}
      size={[340, 620]}
      radius={44}
      fill={'#000'}
      stroke={V.inkDim}
      lineWidth={5}
      clip
      opacity={0}
      scale={0.9}
    >
      <Node ref={feed}>
        {feedDescs.map((d, i) => (
          <FootageSlot
            id={`F0${i + 1}`}
            desc={d}
            w={300}
            h={cardH - 20}
            y={i * cardH}
            accent={[V.magenta, V.cyan, V.amber][i % 3]}
            small
          />
        ))}
      </Node>
      <Rect y={-292} width={110} height={26} radius={13} fill={'#000'} />
    </Rect>,
  );
  slotLog('F01-F06', 'Feed montage inside phone: 6 short vertical fan edits, any creators, 1-2 s each');
  yield* all(phone().opacity(1, 0.8), phone().scale(1, 1, easeOutExpo));

  let swipes = 0;
  const swiping = createSignal(true);
  yield loop(Infinity, function* () {
    if (!swiping()) {
      yield* waitFor(0.2);
      return;
    }
    yield* waitFor(1.1);
    if (!swiping()) return;
    swipes++;
    sfx('tick');
    yield* feed().y(-(swipes % 5) * cardH, 0.45, easeInOutCubic);
  });

  /* ---------- line 1: viewed vs swiped ---------- */
  yield* nar.at(1);
  const metric = createRef<Node>();
  const split = createSignal(0.5);
  view.add(
    <Node ref={metric} x={560} y={-120} opacity={0}>
      <Label text={'VIEWED'} x={-170} y={-70} mono size={22} color={V.green} spacing={4} />
      <Label text={'SWIPED AWAY'} x={140} y={-70} mono size={22} color={V.magenta} spacing={4} />
      <Rect width={520} height={34} radius={17} fill={V.panel2} clip>
        <Rect
          x={() => -260 + (520 * split()) / 2}
          width={() => 520 * split()}
          height={34}
          fill={V.green}
        />
        <Rect
          x={() => 260 - (520 * (1 - split())) / 2}
          width={() => 520 * (1 - split())}
          height={34}
          fill={V.magenta}
        />
      </Rect>
      <Label
        text={'A real Shorts metric in YouTube analytics'}
        y={70}
        size={24}
        color={V.inkDim}
        weight={500}
      />
      <SourceTag text={'ILLUSTRATION · NO REAL VALUES SHOWN'} y={120} />
    </Node>,
  );
  sfx('blip');
  yield* all(phone().x(-380, 0.8, easeInOutCubic), popIn(metric()));
  yield sequence(
    0,
    split(0.72, 1.4, easeInOutCubic),
    split(0.38, 1.4, easeInOutCubic),
    split(0.6, 1.4, easeInOutCubic),
  );

  /* ---------- line 2: quiet revolution ---------- */
  yield* nar.at(2);
  const big = createRef<Node>();
  view.add(
    <Node ref={big} x={420} y={-90} opacity={0}>
      <Txt
        text={'A QUIET'}
        y={-70}
        fontFamily={FONT}
        fontWeight={900}
        fontSize={110}
        letterSpacing={4}
        fill={V.ink}
      />
      <Txt
        text={'REVOLUTION'}
        y={50}
        fontFamily={FONT}
        fontWeight={900}
        fontSize={110}
        letterSpacing={4}
        fill={'#00000000'}
        stroke={V.magenta}
        lineWidth={3}
      />
    </Node>,
  );
  sfx('whoosh');
  yield* all(metric().opacity(0, 0.4), metric().x(700, 0.5));
  yield* all(big().opacity(1, 0.6), big().x(360, 1.4, easeOutExpo));

  /* ---------- lines 3-4: attention illustration ---------- */
  yield* nar.at(3);
  swiping(false);
  yield* all(big().opacity(0, 0.5), phone().opacity(0, 0.6), phone().scale(0.85, 0.6));
  const att = createRef<Node>();
  const flow = createSignal(0);
  const r = rng(11);
  const dots = Array.from({length: 70}, () => ({
    a: r() * Math.PI * 2,
    rad: 20 + r() * 120,
    delay: r() * 0.8,
    jitter: r() * 60 - 30,
  }));
  view.add(
    <Node ref={att} y={-90} opacity={0}>
      <Circle x={-520} size={300} stroke={V.cyan + '66'} lineWidth={2} lineDash={[8, 10]} />
      <Circle x={520} size={300} stroke={V.magenta + '66'} lineWidth={2} lineDash={[8, 10]} />
      <Label text={'ESTABLISHED EDITORS'} x={-520} y={200} mono size={22} color={V.cyan} spacing={3} />
      <Label text={'NEW GENERATION'} x={520} y={200} mono size={22} color={V.magenta} spacing={3} />
      {dots.map(d => (
        <Circle
          size={12}
          fill={() => {
            const k = Math.min(1, Math.max(0, (flow() - d.delay) / 1));
            return k > 0.5 ? V.magenta : V.cyan;
          }}
          x={() => {
            const k = Math.min(1, Math.max(0, (flow() - d.delay) / 1));
            const e = k * k * (3 - 2 * k);
            return -520 + 1040 * e + Math.cos(d.a) * d.rad * 0.9;
          }}
          y={() => {
            const k = Math.min(1, Math.max(0, (flow() - d.delay) / 1));
            return Math.sin(d.a) * d.rad * 0.9 - Math.sin(k * Math.PI) * (90 + d.jitter);
          }}
          opacity={0.9}
        />
      ))}
      <SourceTag text={'ILLUSTRATION OF THE PREMISE · NOT DATA'} y={260} />
    </Node>,
  );
  yield* att().opacity(1, 0.7);
  yield* waitFor(1.2);
  sfx('swell', 3);
  yield* flow(1.25, 4.2, easeInOutCubic);

  /* ---------- line 4 ---------- */
  yield* nar.at(4);
  yield* flow(0.85, 2.5, easeInOutCubic);

  /* ---------- line 5: better? ---------- */
  yield* nar.at(5);
  yield* att().opacity(0, 0.5);
  const better = createRef<Txt>();
  view.add(
    <Txt
      ref={better}
      y={-90}
      text={'SIMPLY BETTER?'}
      fontFamily={FONT}
      fontWeight={900}
      fontSize={150}
      letterSpacing={6}
      fill={V.ink}
      opacity={0}
      scale={1.3}
    />,
  );
  sfx('impact');
  yield* all(better().opacity(1, 0.35), better().scale(1, 0.6, easeOutExpo));

  /* ---------- line 6: assume vs test ---------- */
  yield* nar.at(6);
  const pair = createRef<Node>();
  const strike = createRef<Rect>();
  view.add(
    <Node ref={pair} y={-90} opacity={0}>
      <Txt
        x={-330}
        text={'ASSUME'}
        fontFamily={FONT}
        fontWeight={900}
        fontSize={130}
        fill={V.muted}
      />
      <Rect ref={strike} x={-330} width={0} height={12} radius={6} fill={V.magenta} />
      <Txt
        x={360}
        text={'TEST'}
        fontFamily={FONT}
        fontWeight={900}
        fontSize={130}
        fill={V.green}
      />
    </Node>,
  );
  yield* all(better().opacity(0, 0.4), better().y(-160, 0.5));
  yield* pair().opacity(1, 0.5);
  sfx('shutter');
  yield* strike().width(560, 0.5, easeOutExpo);

  /* ---------- line 7: the central question ---------- */
  yield* nar.at(7);
  yield* pair().opacity(0, 0.5);
  const q = createRef<Node>();
  const qs = ['DID EDITING EVOLVE', 'SO FAR THAT', 'THE OLD STANDARD', 'STOPPED BEING ENOUGH?'];
  view.add(
    <Node ref={q} y={-110}>
      {qs.map((s, i) => (
        <Txt
          y={-150 + i * 100}
          x={i % 2 ? 80 : -80}
          text={s}
          fontFamily={FONT}
          fontWeight={i === 3 ? 900 : 800}
          fontSize={i === 3 ? 92 : 78}
          letterSpacing={3}
          fill={i === 3 ? V.magenta : V.ink}
          opacity={0}
        />
      ))}
      <Txt
        y={260}
        text={'THE CENTRAL QUESTION'}
        fontFamily={MONO}
        fontSize={22}
        letterSpacing={8}
        fill={V.muted}
        opacity={0}
      />
    </Node>,
  );
  const kids = q().children();
  yield* sequence(
    0.45,
    ...kids.map(k => all(k.opacity(1, 0.5), (k as Txt).x(0, 0.5))),
  );
  sfx('sub');
  yield* nar.end();
  yield* all(q().opacity(0, 0.6), q().scale(0.94, 0.6));
});
