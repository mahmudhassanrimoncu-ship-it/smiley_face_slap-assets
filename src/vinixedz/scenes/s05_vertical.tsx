import {Circle, Line, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  all,
  createRef,
  createSignal,
  easeInExpo,
  easeInOutCubic,
  easeOutExpo,
  linear,
  loop,
  sequence,
  waitFor,
} from '@canvas-commons/core';
import {DateCard, FootageSlot, openScene, popIn, refs, sfx, slotLog, withSfx} from '../kit';
import {FONT, MONO, V} from '../theme';

export default makeScene2D(function* (view) {
  /* The 16:9 frame carried over from the previous scene (match cut). */
  const frame = createRef<Rect>();
  const fw = createSignal(960);
  const fh = createSignal(540);
  view.add(
    <Rect
      ref={frame}
      y={-80}
      width={() => fw()}
      height={() => fh()}
      radius={14}
      fill={V.panel}
      stroke={V.amber + '88'}
      lineWidth={2}
      clip
    >
      <Txt text={'FOOTAGE SLOT H05'} fontFamily={MONO} fontWeight={700} fontSize={20} letterSpacing={3} fill={V.amber} />
    </Rect>,
  );
  frame().opacity(0.18);
  const nar = yield* openScene(view, 's05_vertical', V.green);

  /* ---------- line 0: the screen stands upright ---------- */
  yield* frame().opacity(1, 0.4);
  sfx('whooshBig');
  yield* all(
    frame().rotation(90, 0.9, easeInOutCubic),
    fw(620, 0.9, easeInOutCubic),
    fh(350, 0.9, easeInOutCubic),
  );
  frame().rotation(0);
  fw(350);
  fh(620);
  frame().removeChildren();
  frame().stroke(V.inkDim);
  frame().lineWidth(5);
  frame().radius(44);
  frame().fill('#000');
  sfx('impact');
  const inner = createRef<Node>();
  frame().add(
    <Node ref={inner}>
      <FootageSlot id={'V01'} desc={'Vertical velocity edit (any creator, credited)'} w={310} h={580} accent={V.green} small />
    </Node>,
  );
  slotLog('V01', 'Vertical velocity edit, phone-shot or 2020–2022 era, any creator (credited)');
  yield* frame().scale(1.06, 0.15).to(1, 0.4);

  /* ---------- line 1-4: phones and dates ---------- */
  yield* nar.at(1);
  yield* frame().x(-480, 1.0, easeInOutCubic);

  const cards = [createRef<Node>(), createRef<Node>(), createRef<Node>()];
  view.add(
    <Node x={330} y={-90}>
      <Node ref={cards[0]} y={-240} opacity={0}>
        <DateCard date={'DEC 2019'} title={'Alight Motion on iPhone'} body={'Keyframes and layers on mobile'} src={refs('appstore-alight')} color={V.green} w={720} opacity={1} />
      </Node>
      <Node ref={cards[1]} y={-10} opacity={0}>
        <DateCard date={'2020'} title={'CapCut goes international'} body={'ByteDance editor, formerly ViaMaker'} src={refs('wiki-capcut')} color={V.cyan} w={720} opacity={1} />
      </Node>
      <Node ref={cards[2]} y={220} opacity={0}>
        <DateCard date={'14 SEP 2020'} title={'YouTube Shorts announced'} body={'Beta launch in India first'} src={refs('cnbc-shorts-2020', 'google-blog-shorts-india')} color={V.magenta} w={720} opacity={1} />
      </Node>
    </Node>,
  );
  for (let i = 0; i < 3; i++) {
    yield* nar.at(2 + i);
    yield* withSfx('blip', popIn(cards[i](), 0.6, 30));
  }

  /* ---------- line 5-6: the velocity edit ---------- */
  yield* nar.at(5);
  sfx('whoosh');
  yield* all(...cards.map(c => all(c().opacity(0, 0.5), c().x(80, 0.5))));
  const title = createRef<Txt>();
  view.add(
    <Txt
      ref={title}
      x={330}
      y={-330}
      text={'THE VELOCITY EDIT'}
      fontFamily={FONT}
      fontWeight={900}
      fontSize={84}
      letterSpacing={4}
      fill={V.green}
      opacity={0}
    />,
  );
  yield* all(title().opacity(1, 0.4), title().x(300, 0.9, easeOutExpo));

  // demo stage: a "subject" crossing a lane with a speed ramp
  const lane = createRef<Node>();
  const p = createSignal(0);
  const speedTxt = createSignal('100%');
  view.add(
    <Node ref={lane} x={300} y={-120} opacity={0}>
      <Rect width={820} height={240} radius={16} fill={V.panel + 'dd'} stroke={V.line} lineWidth={2} />
      <Line points={[[-380, 60], [380, 60]]} stroke={V.faint} lineWidth={2} lineDash={[10, 10]} />
      {[0, 1, 2, 3, 4].map(k => (
        <Circle
          size={70}
          fill={V.green}
          opacity={k === 0 ? 1 : 0.12}
          x={() => -350 + 700 * Math.max(0, p() - k * 0.018)}
          y={10}
        />
      ))}
      <Txt x={-300} y={-80} text={'SPEED'} fontFamily={MONO} fontSize={22} fill={V.muted} letterSpacing={4} />
      <Txt x={-170} y={-80} text={() => speedTxt()} fontFamily={MONO} fontWeight={700} fontSize={30} fill={V.green} />
    </Node>,
  );
  yield* lane().opacity(1, 0.5);
  yield loop(Infinity, function* () {
    p(0);
    speedTxt('100%');
    yield* p(0.38, 0.5, linear);
    speedTxt('20%');
    sfx('sub');
    yield* p(0.48, 1.5, linear);
    speedTxt('400%');
    sfx('whoosh');
    yield* p(1, 0.3, easeInExpo);
    speedTxt('100%');
    yield* waitFor(0.6);
  });

  /* ---------- line 7: shakes, flashes, zooms ---------- */
  yield* nar.at(7);
  const flash = createRef<Rect>();
  view.add(<Rect ref={flash} size={[1920, 1080]} fill={'#ffffff'} opacity={0} zIndex={40} />);
  const words = ['SHAKE', 'FLASH', 'ZOOM', 'SYNC'];
  const wordRow = createRef<Node>();
  view.add(
    <Node ref={wordRow} x={300} y={150}>
      {words.map((w, i) => (
        <Txt x={-300 + i * 200} text={w} fontFamily={MONO} fontWeight={700} fontSize={34} letterSpacing={4} fill={V.inkDim} opacity={0} />
      ))}
    </Node>,
  );
  // shake
  sfx('impact');
  yield wordRow().children()[0].opacity(1, 0.3);
  for (let k = 0; k < 8; k++) {
    const a = 22 * Math.pow(0.7, k);
    yield* all(frame().x(-480 + (k % 2 ? a : -a), 0.05), frame().rotation(k % 2 ? a / 6 : -a / 6, 0.05));
  }
  yield* all(frame().x(-480, 0.05), frame().rotation(0, 0.05));
  // flash
  yield* waitFor(0.4);
  yield wordRow().children()[1].opacity(1, 0.3);
  sfx('glitch');
  yield* flash().opacity(0.85, 0.06).to(0, 0.35);
  // zoom
  yield* waitFor(0.3);
  yield wordRow().children()[2].opacity(1, 0.3);
  sfx('whoosh');
  yield* inner().scale(1.8, 0.35, easeInExpo).to(1, 0.5, easeOutExpo);
  yield* waitFor(0.3);
  yield* wordRow().children()[3].opacity(1, 0.3);

  /* ---------- line 8-9: shared language, a foundation ---------- */
  yield* nar.at(8);
  yield* all(lane().opacity(0, 0.5), title().opacity(0, 0.5));
  const base = createRef<Rect>();
  view.add(
    <Rect ref={base} x={300} y={190} width={0} height={90} radius={10} fill={V.green + '22'} stroke={V.green} lineWidth={2} />,
  );
  yield* all(
    base().width(900, 0.8, easeOutExpo),
    ...wordRow().children().map((w, i) => all(w.y(40, 0.8, easeInOutCubic), (w as Txt).fill(V.green, 0.8))),
  );
  const baseLbl = createRef<Txt>();
  view.add(
    <Txt ref={baseLbl} x={300} y={270} text={'THE SHARED GRAMMAR'} fontFamily={MONO} fontWeight={700} fontSize={22} letterSpacing={8} fill={V.green} opacity={0} />,
  );
  yield* baseLbl().opacity(1, 0.5);

  yield* nar.at(9);
  const ghosts = createRef<Node>();
  view.add(
    <Node ref={ghosts} x={300}>
      {[0, 1, 2, 3].map(i => (
        <Rect
          y={110 - i * 100}
          width={820 - i * 120}
          height={80}
          radius={10}
          stroke={V.inkDim + '55'}
          lineWidth={2}
          lineDash={[10, 8]}
          opacity={0}
        />
      ))}
    </Node>,
  );
  yield* sequence(0.25, ...ghosts().children().map(g => withSfx('tick', popIn(g, 0.5, 30))));
  yield* nar.end();
  yield* all(
    ghosts().opacity(0, 0.6),
    base().opacity(0, 0.6),
    baseLbl().opacity(0, 0.6),
    wordRow().opacity(0, 0.6),
    frame().opacity(0, 0.6),
    frame().scale(0.9, 0.6),
  );
});
