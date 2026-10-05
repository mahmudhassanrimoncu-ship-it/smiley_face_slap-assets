import {Circle, Line, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  ThreadGenerator,
  all,
  createRef,
  createSignal,
  easeInOutCubic,
  usePlayback,
} from '@canvas-commons/core';
import {HeatArrow} from '../components/cycle';
import {background, createCaption, createHeader, quiz} from '../components/ui';
import {C, FONT} from '../theme';

export default makeScene2D(function* (view) {
  background(view);
  const header = createHeader(view);
  const caption = createCaption(view);
  const phase = createSignal(0);
  yield (function* (): ThreadGenerator {
    while (true) {
      phase(phase() + usePlayback().deltaTime);
      yield;
    }
  })();

  yield* header.set('MYTH BUSTER');
  yield* quiz(view, {
    label: 'PREDICT',
    question: 'You leave a running fridge’s door open in a closed kitchen. Over time, the kitchen will…',
    options: [
      'get cooler',
      'get warmer',
      'stay at exactly the same temperature',
      'cool down until it is as cold as the fridge',
    ],
    answer: 1,
    why: 'It gets warmer! Let’s see why.',
    think: 7,
  });

  // ---------------- Kitchen picture ----------------
  const scene = createRef<Node>();
  const inArrows = createRef<Node>();
  const outArrows = createRef<Node>();
  const plug = createRef<Node>();
  const net = createRef<Rect>();
  const mercury = createRef<Rect>();
  view.add(
    <Node ref={scene} opacity={0} y={-40}>
      <Rect
        size={[1500, 640]}
        radius={30}
        fill={'#fffaf3'}
        stroke={'#e7c9a0'}
        lineWidth={5}
      />
      <Txt
        x={720}
        y={-285}
        anchor={[1, 0]}
        text={'CLOSED KITCHEN'}
        fontFamily={FONT}
        fontWeight={800}
        fontSize={28}
        letterSpacing={1.5}
        fill={'#a86b1d'}
      />
      {/* fridge body (front faces right) */}
      <Rect x={0} y={40} size={[260, 440]} radius={18} fill={'#eef3f9'} stroke={'#7f8da3'} lineWidth={5} />
      <Rect x={0} y={40} size={[210, 390]} radius={10} fill={C.coldTint} />
      <Txt x={0} y={40} text={'4 °C'} fontFamily={FONT} fontWeight={800} fontSize={40} fill={C.cold} />
      {/* open door */}
      <Line
        points={[
          [130, -180],
          [250, -230],
          [250, 330],
          [130, 260],
        ]}
        closed
        fill={'#dfe6ef'}
        stroke={'#7f8da3'}
        lineWidth={5}
      />
      <Txt x={190} y={-260} text={'door open'} fontFamily={FONT} fontWeight={600} fontSize={22} fill={C.muted} />
      {/* condenser on the back (left side) */}
      {Array.from({length: 8}, (_, i) => (
        <Rect x={-150} y={-110 + i * 44} size={[18, 30]} radius={6} fill={'#ee8f8f'} />
      ))}
      <Txt x={-150} y={300} text={'condenser (back)'} fontFamily={FONT} fontWeight={600} fontSize={22} fill={C.hot} />

      {/* heat taken from kitchen air */}
      <Node ref={inArrows} opacity={0}>
        {[-60, 40, 140].map(y => (
          <HeatArrow from={[520, y]} to={[290, y]} phase={phase} color={C.coldMid} />
        ))}
        <Txt x={410} y={-160} text={'Qin'} fontFamily={FONT} fontWeight={800} fontSize={40} fill={C.cold} />
        <Txt x={410} y={-120} text={'heat taken from kitchen air'} fontFamily={FONT} fontWeight={600} fontSize={22} fill={C.cold} />
      </Node>
      {/* heat dumped back into kitchen */}
      <Node ref={outArrows} opacity={0}>
        {[-30, 50, 130, 210].map(y => (
          <HeatArrow from={[-190, y]} to={[-480, y]} phase={phase} />
        ))}
        <Txt x={-340} y={-150} text={'Qout = Qin + Win'} fontFamily={FONT} fontWeight={800} fontSize={40} fill={C.warm} />
        <Txt x={-340} y={-110} text={'heat released into the same kitchen'} fontFamily={FONT} fontWeight={600} fontSize={22} fill={C.warm} />
      </Node>
      {/* electricity */}
      <Node ref={plug} opacity={0}>
        <Line
          points={[
            [0, -180],
            [0, -240],
            [-560, -240],
          ]}
          stroke={'#8a6a00'}
          lineWidth={5}
          lineDash={[14, 10]}
        />
        <Rect x={-580} y={-240} size={[40, 54]} radius={8} fill={'#fff4d6'} stroke={C.work} lineWidth={4} />
        <Txt x={-300} y={-268} text={'Win (electricity)'} fontFamily={FONT} fontWeight={800} fontSize={28} fill={'#8a6a00'} />
      </Node>
      {/* thermometer */}
      <Node x={620} y={150}>
        <Rect size={[30, 220]} radius={15} fill={'#fff'} stroke={C.muted} lineWidth={4} />
        <Rect
          ref={mercury}
          y={100}
          anchor={[0, 1]}
          width={14}
          height={70}
          radius={7}
          fill={C.hot}
        />
        <Circle y={115} size={46} fill={C.hot} stroke={C.muted} lineWidth={4} />
        <Txt y={-140} text={'kitchen'} fontFamily={FONT} fontWeight={700} fontSize={22} fill={C.muted} />
      </Node>
      <Rect
        ref={net}
        y={-320}
        layout
        padding={[14, 30]}
        radius={40}
        fill={C.warm}
        opacity={0}
      >
        <Txt
          text={'Net effect: the kitchen GAINS Win → it warms up'}
          fontFamily={FONT}
          fontWeight={800}
          fontSize={32}
          fill={'#fff'}
        />
      </Rect>
    </Node>,
  );

  yield* scene().opacity(1, 0.8);
  yield* all(
    inArrows().opacity(1, 0.6),
    caption.say('With the door open, the fridge pulls heat (Qin) out of the kitchen air in front of it…'),
  );
  yield* all(
    plug().opacity(1, 0.6),
    caption.say('…its compressor uses electrical work (Win)…'),
  );
  yield* all(
    outArrows().opacity(1, 0.6),
    caption.say('…and its condenser releases Qout = Qin + Win back into the SAME kitchen.'),
  );
  yield* all(
    net().opacity(1, 0.6),
    mercury().height(170, 3, easeInOutCubic),
    caption.say('More heat goes back into the room than was taken out, so the kitchen slowly gets warmer.'),
  );
  yield* caption.say(
    'A fridge only MOVES heat. To cool a space, the heat must be dumped somewhere else – that is why an air conditioner releases its heat outdoors.',
  );
  yield* all(scene().opacity(0, 0.6), caption.hide());
});
