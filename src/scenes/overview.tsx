import {Circle, Line, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {all, createRef, easeOutBack, sequence, waitFor} from '@canvas-commons/core';
import {createCycle, hideAll} from '../components/cycle';
import {background, createCaption, createHeader, pulse, quiz} from '../components/ui';
import {C, FONT} from '../theme';

export default makeScene2D(function* (view) {
  background(view);
  const c = createCycle(view);
  const header = createHeader(view);
  const caption = createCaption(view);
  hideAll(c);

  const pipeLines = c.pipes.children() as Line[];
  pipeLines.forEach(l => l.end(0));
  c.pipes.opacity(1);

  yield c.run();
  yield* header.set('THE SEALED LOOP');

  // ---- draw the loop ----
  yield* all(
    caption.say(
      'The refrigerant flows around a closed loop of pipes. It is sealed in – it never mixes with the air or the food.',
      0,
    ),
    sequence(1.4, all(pipeLines[0].end(1, 1.6), pipeLines[2].end(1, 1.6)), all(pipeLines[1].end(1, 1.6), pipeLines[3].end(1, 1.6))),
  );
  c.particles.opacity(0);
  c.speed(550);
  yield* c.particles.opacity(1, 1);
  yield* waitFor(2.5);

  // ---- the four parts ----
  yield* header.set('THE 4 MAIN PARTS');
  yield* all(
    c.cabinet.opacity(1, 0.6),
    c.evapFrame.opacity(1, 0.6),
    c.labels[0].opacity(1, 0.6),
  );
  yield* all(
    pulse(c.root, [-520, 0], 300, C.cold),
    caption.say('① EVAPORATOR – inside the fridge. Here the refrigerant absorbs heat.'),
  );
  yield* all(c.compressor.opacity(1, 0.6), c.labels[1].opacity(1, 0.6));
  yield* all(
    pulse(c.root, [0, -255], 260, C.hot),
    caption.say('② COMPRESSOR – an electric pump. It uses work to squeeze the gas.'),
  );
  c.fanSpeed(320);
  yield* all(
    c.condFrame.opacity(1, 0.6),
    c.fan.opacity(1, 0.6),
    c.labels[2].opacity(1, 0.6),
  );
  yield* all(
    pulse(c.root, [520, 0], 300, C.hot),
    caption.say('③ CONDENSER – outside the cabinet, usually on the back. Here the refrigerant releases heat to the room.'),
  );
  yield* all(c.valve.opacity(1, 0.6), c.labels[3].opacity(1, 0.6));
  yield* all(
    pulse(c.root, [0, 225], 200, C.valve),
    caption.say('④ EXPANSION VALVE – a narrow restriction (in many home fridges, a thin capillary tube) where the pressure drops.'),
  );

  // ---- direction ----
  yield* c.flowIcon.opacity(1, 0.6);
  yield* caption.say(
    'The refrigerant always travels the same way: Evaporator → Compressor → Condenser → Expansion valve → back to the Evaporator.',
  );

  // ---- two pressure sides ----
  yield* header.set('TWO SIDES OF THE LOOP');
  yield* all(...c.chips.map(ch => ch.opacity(1, 0.6)));
  yield* caption.say(
    'The compressor and the expansion valve split the loop into a HIGH-pressure side (red) and a LOW-pressure side (blue).',
  );

  // ---- dot legend ----
  const legend = createRef<Rect>();
  view.add(
    <Rect
      ref={legend}
      x={560}
      y={-482}
      layout
      alignItems={'center'}
      gap={18}
      padding={[12, 26]}
      radius={40}
      fill={C.card}
      stroke={C.cardLine}
      lineWidth={2}
      opacity={0}
      scale={0.9}
    >
      <Txt text={'KEY:'} fontFamily={FONT} fontWeight={800} fontSize={24} fill={C.muted} />
      <Circle size={18} fill={C.ink} />
      <Txt text={'liquid'} fontFamily={FONT} fontWeight={600} fontSize={24} fill={C.ink} />
      <Circle size={20} fill={'#14213d40'} stroke={C.ink} lineWidth={3} marginLeft={14} />
      <Txt text={'gas (vapour)'} fontFamily={FONT} fontWeight={600} fontSize={24} fill={C.ink} />
      <Rect width={30} height={10} radius={5} fill={C.coldMid} marginLeft={14} />
      <Txt text={'cold'} fontFamily={FONT} fontWeight={600} fontSize={24} fill={C.ink} />
      <Rect width={30} height={10} radius={5} fill={C.hot} marginLeft={14} />
      <Txt text={'hot'} fontFamily={FONT} fontWeight={600} fontSize={24} fill={C.ink} />
    </Rect>,
  );
  yield* all(legend().opacity(1, 0.5), legend().scale(1, 0.5, easeOutBack));
  yield* caption.say(
    'Watch the dots: solid dots are LIQUID, hollow dots are GAS. Liquid is dense, so its dots crowd together; gas spreads out.',
  );
  yield* caption.say(
    'Dot colour shows temperature: blue = cold, orange = warm, red = hot. Now let’s follow the refrigerant one step at a time.',
  );

  yield* quiz(view, {
    question: 'Starting at the evaporator, what is the correct order of the cycle?',
    options: [
      'Evaporator → Condenser → Compressor → Expansion valve',
      'Evaporator → Compressor → Condenser → Expansion valve',
      'Evaporator → Expansion valve → Condenser → Compressor',
      'Evaporator → Compressor → Expansion valve → Condenser',
    ],
    answer: 1,
    why: 'Evaporator → Compressor → Condenser → Expansion valve, then back to the evaporator. The loop repeats continuously.',
  });
  yield* all(caption.hide(), legend().opacity(0, 0.4));
});
