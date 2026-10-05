import {Layout, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {all, createRef, easeOutCubic, sequence, waitFor} from '@canvas-commons/core';
import {fullCycle} from '../components/step';
import {Op, Sym} from '../components/symbols';
import {background, createCaption, createHeader, pulse, quiz} from '../components/ui';
import {C, FONT} from '../theme';

const PX_PER_J = 3;
const BASE = 150;

function Bar(props: {
  x: number;
  value: number;
  color: string;
  refFn: (r: Rect) => void;
  y0?: number;
}) {
  return (
    <Rect
      ref={props.refFn}
      x={props.x}
      y={BASE - (props.y0 ?? 0) * PX_PER_J}
      anchor={[0, 1]}
      width={150}
      height={0}
      radius={[10, 10, 0, 0]}
      fill={props.color}
    />
  );
}

export default makeScene2D(function* (view) {
  background(view);
  const c = yield* fullCycle(view);
  c.flowIcon.opacity(1);
  c.heatIn.opacity(1);
  c.heatOut.opacity(1);
  const header = createHeader(view);
  const caption = createCaption(view);

  // ---------------- Recap of the whole loop ----------------
  yield* header.set('THE WHOLE CYCLE');
  yield* all(
    pulse(c.root, [-520, 0], 300, C.cold),
    caption.say('① Evaporator: the very cold refrigerant absorbs heat from inside the fridge and evaporates.'),
  );
  yield* all(
    pulse(c.root, [0, -255], 260, C.hot),
    caption.say('② Compressor: work (electricity) raises the gas’s pressure and temperature.'),
  );
  yield* all(
    pulse(c.root, [520, 0], 300, C.hot),
    caption.say('③ Condenser: the hot gas releases heat to the room and condenses into a liquid.'),
  );
  yield* all(
    pulse(c.root, [0, 225], 200, C.valve),
    caption.say('④ Expansion valve: the pressure drops, so the refrigerant becomes very cold – and the loop repeats.'),
  );

  // ---------------- Energy balance ----------------
  yield* header.set('ENERGY BALANCE');
  yield* all(caption.hide(), c.focus([77, -40], 0.5, [-480, -60], 1.4));

  const qin = createRef<Rect>();
  const win = createRef<Rect>();
  const outA = createRef<Rect>();
  const outB = createRef<Rect>();
  const labels = createRef<Node>();
  const eq = createRef<Layout>();
  const numbers = createRef<Txt>();
  const cop = createRef<Rect>();
  const title = createRef<Txt>();
  view.add(
    <Node>
      <Txt
        ref={title}
        x={490}
        y={-395}
        text={'Where does the energy go?'}
        fontFamily={FONT}
        fontWeight={800}
        fontSize={42}
        fill={C.ink}
        opacity={0}
      />
      <Rect x={490} y={BASE + 2} width={700} height={4} fill={C.ink} />
      <Bar x={250} value={100} color={C.coldMid} refFn={qin} />
      <Bar x={490} value={40} color={C.work} refFn={win} />
      <Bar x={730} value={100} color={C.coldMid} refFn={outA} />
      <Bar x={730} value={40} color={C.work} refFn={outB} y0={100} />
      <Node ref={labels}>
        {[
          {x: 250, a: 'Heat absorbed', b: 'inside (Qin)', v: '100 J', h: 100, col: C.cold},
          {x: 490, a: 'Work input', b: 'electricity (Win)', v: '40 J', h: 40, col: '#8a6a00'},
          {x: 730, a: 'Heat released', b: 'to the room (Qout)', v: '140 J', h: 140, col: C.warm},
        ].map(l => (
          <Node x={l.x} opacity={0}>
            <Txt y={BASE + 36} text={l.a} fontFamily={FONT} fontWeight={700} fontSize={26} fill={l.col} />
            <Txt y={BASE + 68} text={l.b} fontFamily={FONT} fontWeight={600} fontSize={24} fill={l.col} />
            <Txt y={BASE - l.h * PX_PER_J - 26} text={l.v} fontFamily={FONT} fontWeight={800} fontSize={32} fill={l.col} />
          </Node>
        ))}
      </Node>
      <Layout ref={eq} x={490} y={BASE + 160} layout alignItems={'center'} opacity={0}>
        <Sym main={'Q'} sub={'out'} color={C.warm} />
        <Op text={'='} color={C.ink} />
        <Sym main={'Q'} sub={'in'} color={C.cold} />
        <Op text={'+'} color={C.ink} />
        <Sym main={'W'} sub={'in'} color={'#8a6a00'} />
      </Layout>
      <Txt
        ref={numbers}
        x={490}
        y={BASE + 230}
        text={'140 J = 100 J + 40 J'}
        fontFamily={FONT}
        fontWeight={700}
        fontSize={34}
        fill={C.muted}
        opacity={0}
      />
    </Node>,
  );
  const labelNodes = labels().children();

  yield* title().opacity(1, 0.5);
  yield* all(
    qin().height(100 * PX_PER_J, 1.2, easeOutCubic),
    labelNodes[0].opacity(1, 0.6),
    caption.say('Each cycle, the refrigerant picks up heat from inside the fridge – call it Qin. Here: 100 joules.'),
  );
  yield* all(
    win().height(40 * PX_PER_J, 1.0, easeOutCubic),
    labelNodes[1].opacity(1, 0.6),
    caption.say('The compressor adds energy as work – Win. Here: 40 joules of electrical energy.'),
  );
  yield* all(
    sequence(0.5, outA().height(100 * PX_PER_J, 1.0, easeOutCubic), outB().height(40 * PX_PER_J, 1.0, easeOutCubic)),
    labelNodes[2].opacity(1, 0.6),
    caption.say('Energy cannot disappear, so the condenser must release BOTH to the room: 100 J + 40 J = 140 J.'),
  );
  yield* all(eq().opacity(1, 0.6), numbers().opacity(1, 0.6));
  yield* caption.say('Heat rejected = Heat absorbed + Work input.  So Qout is always bigger than Qin.');

  // ---- COP ----
  view.add(
    <Rect
      ref={cop}
      x={-480}
      y={290}
      layout
      direction={'column'}
      alignItems={'center'}
      padding={[20, 34]}
      radius={22}
      fill={C.card}
      stroke={C.cardLine}
      lineWidth={2}
      gap={6}
      opacity={0}
    >
      <Txt text={'Coefficient of performance'} fontFamily={FONT} fontWeight={700} fontSize={28} fill={C.muted} />
      <Layout alignItems={'center'}>
        <Txt text={'COP ='} fontFamily={FONT} fontWeight={800} fontSize={44} fill={C.ink} marginRight={14} />
        <Sym main={'Q'} sub={'in'} color={C.cold} size={44} />
        <Op text={'÷'} color={C.ink} size={44} />
        <Sym main={'W'} sub={'in'} color={'#8a6a00'} size={44} />
        <Op text={'= 100 ÷ 40 = 2.5'} color={C.ink} size={40} />
      </Layout>
    </Rect>,
  );
  yield* cop().opacity(1, 0.6);
  yield* caption.say(
    'How good is a fridge? COP = heat removed from inside ÷ work input. Here, 2.5 J of heat is moved for every 1 J of electricity.',
  );
  yield* waitFor(0.5);

  yield* quiz(view, {
    question: 'A fridge removes 200 J of heat from its inside and uses 50 J of electrical work. How much heat does it release into the room?',
    options: ['150 J', '200 J', '250 J', '50 J'],
    answer: 2,
    why: 'Qout = Qin + Win = 200 J + 50 J = 250 J. The room gets back all the heat taken from inside, plus the work.',
  });
  yield* caption.hide();
});
