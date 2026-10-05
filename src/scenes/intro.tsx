import {Line, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  all,
  createRef,
  createSignal,
  easeOutBack,
  sequence,
  ThreadGenerator,
  usePlayback,
  waitFor,
} from '@canvas-commons/core';
import {HeatArrow} from '../components/cycle';
import {background, createCaption, quiz} from '../components/ui';
import {C, FONT} from '../theme';

function TempBox(props: {
  refFn: (r: Rect) => void;
  x: number;
  title: string;
  temp: string;
  color: string;
  tint: string;
}) {
  return (
    <Rect
      ref={props.refFn}
      x={props.x}
      y={-10}
      size={[440, 300]}
      radius={30}
      fill={props.tint}
      stroke={props.color}
      lineWidth={5}
      layout
      direction={'column'}
      justifyContent={'center'}
      alignItems={'center'}
      gap={12}
      opacity={0}
    >
      <Txt
        text={props.title}
        textAlign={'center'}
        fontFamily={FONT}
        fontWeight={800}
        fontSize={40}
        fill={props.color}
      />
      <Txt
        text={props.temp}
        fontFamily={FONT}
        fontWeight={800}
        fontSize={72}
        fill={props.color}
      />
    </Rect>
  );
}

export default makeScene2D(function* (view) {
  background(view);
  const caption = createCaption(view);

  // ---------------- Title ----------------
  const title = createRef<Node>();
  view.add(
    <Node ref={title} opacity={0} y={-30}>
      <Txt
        y={-60}
        text={'HOW A REFRIGERATOR WORKS'}
        fontFamily={FONT}
        fontWeight={800}
        fontSize={100}
        letterSpacing={2}
        fill={C.ink}
      />
      <Txt
        y={50}
        text={'A heat pump that moves heat from inside to the outside using work (electricity)'}
        fontFamily={FONT}
        fontWeight={500}
        fontSize={38}
        fill={C.muted}
      />
      <Rect y={120} width={220} height={8} radius={4} fill={C.cold} x={-112} />
      <Rect y={120} width={220} height={8} radius={4} fill={C.hot} x={112} />
    </Node>,
  );
  yield* all(title().opacity(1, 0.8), title().y(-60, 0.8));
  yield* waitFor(3);
  yield* title().opacity(0, 0.5);

  // ---------------- Hook question ----------------
  yield* quiz(view, {
    label: 'BEFORE WE START',
    question: 'True or false: a refrigerator works by making “cold” and putting it inside.',
    options: [
      'True – it produces cold and adds it to the inside',
      'False – it removes heat from the inside and dumps it outside',
    ],
    answer: 1,
    why: '“Cold” is not a substance – it is just less heat. A fridge pumps heat OUT of its inside and releases it into the room.',
    think: 6,
  });

  // ---------------- Natural heat flow ----------------
  const hot = createRef<Rect>();
  const cold = createRef<Rect>();
  const arrows = createRef<Node>();
  const phase = createSignal(0);
  const label = createRef<Txt>();
  view.add(
    <TempBox refFn={hot} x={-460} title={'HOT CUP OF TEA'} temp={'80 °C'} color={C.hot} tint={C.hotTint} />,
  );
  view.add(
    <TempBox refFn={cold} x={460} title={'ROOM AIR'} temp={'22 °C'} color={C.cold} tint={C.coldTint} />,
  );
  view.add(
    <Node ref={arrows} opacity={0} y={-10}>
      {[-60, 0, 60].map(y => (
        <HeatArrow from={[-200, y]} to={[200, y]} phase={phase} width={8} />
      ))}
    </Node>,
  );
  view.add(
    <Txt
      ref={label}
      y={-250}
      text={'Heat flows by itself from HOT to COLD'}
      fontFamily={FONT}
      fontWeight={800}
      fontSize={46}
      fill={C.ink}
      opacity={0}
    />,
  );
  const ticker = function* (): ThreadGenerator {
    while (true) {
      phase(phase() + usePlayback().deltaTime);
      yield;
    }
  };
  yield ticker();

  yield* sequence(0.2, hot().opacity(1, 0.5), cold().opacity(1, 0.5));
  yield* all(arrows().opacity(1, 0.6), label().opacity(1, 0.6));
  yield* caption.say(
    'Heat always flows naturally from a hotter object to a colder one – a hot drink cools down, it never heats up by itself.',
  );

  // ---------------- The fridge does the opposite ----------------
  const fridgeHot = createRef<Rect>();
  const fridgeCold = createRef<Rect>();
  const workTag = createRef<Rect>();
  yield* all(
    hot().opacity(0, 0.5),
    cold().opacity(0, 0.5),
    arrows().opacity(0, 0.5),
    label().opacity(0, 0.5),
  );
  hot().remove();
  cold().remove();
  view.add(
    <TempBox refFn={fridgeCold} x={-460} title={'INSIDE THE FRIDGE'} temp={'4 °C'} color={C.cold} tint={C.coldTint} />,
  );
  view.add(
    <TempBox refFn={fridgeHot} x={460} title={'KITCHEN AIR'} temp={'22 °C'} color={C.hot} tint={C.hotTint} />,
  );
  view.add(
    <Rect
      ref={workTag}
      y={140}
      layout
      padding={[14, 26]}
      radius={40}
      fill={'#fff4d6'}
      stroke={C.work}
      lineWidth={4}
      gap={12}
      alignItems={'center'}
      opacity={0}
      scale={0.8}
    >
      <Line
        points={[
          [10, -22],
          [-8, 4],
          [3, 4],
          [-4, 24],
          [14, -4],
          [2, -4],
          [10, -22],
        ]}
        closed
        fill={C.work}
        stroke={'#8a6a00'}
        lineWidth={2}
        width={30}
        height={48}
      />
      <Txt
        text={'needs WORK (electricity)'}
        fontFamily={FONT}
        fontWeight={800}
        fontSize={34}
        fill={'#8a6a00'}
      />
    </Rect>,
  );
  label().text('A fridge moves heat the “wrong” way: COLD → WARM');
  yield* sequence(0.2, fridgeCold().opacity(1, 0.5), fridgeHot().opacity(1, 0.5));
  yield* all(arrows().opacity(1, 0.6), label().opacity(1, 0.6));
  yield* caption.say(
    'A fridge does the opposite: it moves heat out of the cold inside and into the warmer kitchen.',
  );
  yield* all(workTag().opacity(1, 0.5), workTag().scale(1, 0.5, easeOutBack));
  yield* caption.say(
    'Heat never flows from cold to hot on its own. To force it, the fridge must use energy – work supplied as electricity.',
  );
  yield* caption.say(
    'It does this with a special fluid, the REFRIGERANT, that circulates around a sealed loop of pipes. Let’s build that loop.',
  );
  yield* all(
    fridgeCold().opacity(0, 0.5),
    fridgeHot().opacity(0, 0.5),
    arrows().opacity(0, 0.5),
    label().opacity(0, 0.5),
    workTag().opacity(0, 0.5),
    caption.hide(),
  );
});
