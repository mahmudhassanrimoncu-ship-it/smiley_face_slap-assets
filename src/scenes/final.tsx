import {Circle, Layout, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {all, createRef, easeOutBack, sequence, waitFor} from '@canvas-commons/core';
import {QuizSpec, background, createCaption, createHeader, quiz} from '../components/ui';
import {C, FONT} from '../theme';

const QUESTIONS: QuizSpec[] = [
  {
    question: 'In which part does the refrigerant change from a liquid into a gas?',
    options: ['Condenser', 'Evaporator', 'Compressor', 'It never changes state'],
    answer: 1,
    why: 'In the evaporator the cold liquid absorbs heat from inside the fridge and boils into a gas.',
  },
  {
    question: 'Which part raises the pressure of the refrigerant?',
    options: ['Expansion valve', 'Evaporator', 'Compressor', 'Condenser'],
    answer: 2,
    why: 'The compressor does work on the gas, raising its pressure and temperature. The expansion valve does the opposite: it lowers the pressure.',
  },
  {
    question: 'Why does the back of a fridge feel warm?',
    options: [
      'The evaporator is on the back',
      'The condenser there releases heat to the room',
      'Cold air is leaking out of the back',
      'The expansion valve heats the refrigerant',
    ],
    answer: 1,
    why: 'The condenser releases the heat taken from inside the fridge, plus the compressor’s work, into the room.',
  },
  {
    question: 'What is the refrigerant like just before it enters the expansion valve?',
    options: [
      'A low-pressure, very cold gas',
      'A high-pressure, hot gas',
      'A high-pressure, warm liquid',
      'A low-pressure mix of liquid and vapour',
    ],
    answer: 2,
    why: 'It has just condensed in the condenser, so it is a warm liquid that is still at high pressure.',
  },
  {
    question: 'A fridge removes 300 J of heat from its inside using 100 J of electrical work. How much heat goes into the room?',
    options: ['200 J', '300 J', '400 J', '100 J'],
    answer: 2,
    why: 'Qout = Qin + Win = 300 J + 100 J = 400 J.',
  },
  {
    question: 'Which sentence best describes what a refrigerator does?',
    options: [
      'It creates cold and adds it to the inside',
      'It moves heat from the inside to the outside, using work',
      'It destroys the heat inside the fridge',
      'It moves heat from the room into the fridge',
    ],
    answer: 1,
    why: 'A fridge is a heat pump: it uses work (electricity) to move heat from the cold inside to the warmer room.',
  },
];

const STEPS = [
  {
    n: 1,
    name: 'EVAPORATOR',
    sub: 'Heat absorbed inside',
    text: 'Very cold, low-pressure refrigerant absorbs heat from inside and evaporates into a gas.',
    effect: 'Inside gets colder',
    color: C.cold,
    tint: C.coldTint,
  },
  {
    n: 2,
    name: 'COMPRESSOR',
    sub: 'Work in',
    text: 'Electrical work squeezes the gas, raising its pressure and temperature.',
    effect: 'Gas gets hotter',
    color: C.hot,
    tint: C.hotTint,
  },
  {
    n: 3,
    name: 'CONDENSER',
    sub: 'Heat released outside',
    text: 'Hot gas releases heat to the room air and condenses into a high-pressure liquid.',
    effect: 'Room gets warmer',
    color: C.hot,
    tint: C.hotTint,
  },
  {
    n: 4,
    name: 'EXPANSION VALVE',
    sub: 'Pressure drop',
    text: 'Pressure drops suddenly; part of the liquid evaporates and the refrigerant becomes very cold.',
    effect: 'Refrigerant cools',
    color: C.valve,
    tint: C.valveTint,
  },
];

export default makeScene2D(function* (view) {
  background(view);
  const header = createHeader(view);
  const caption = createCaption(view);

  yield* header.set('FINAL TEST');
  yield* caption.say(
    'Time to test yourself! 6 questions. Answer each one before the timer runs out – pause the video if you need more time.',
  );
  yield* caption.hide();
  for (let i = 0; i < QUESTIONS.length; i++) {
    yield* quiz(view, {
      ...QUESTIONS[i],
      label: `QUESTION ${i + 1} OF ${QUESTIONS.length}`,
      think: 8,
    });
    yield* waitFor(0.3);
  }

  // ---------------- Summary ----------------
  yield* header.set('SUMMARY');
  const cards: Rect[] = [];
  const row = createRef<Layout>();
  view.add(
    <Layout ref={row} y={-110} layout gap={28} alignItems={'stretch'}>
      {STEPS.map((s, i) => (
        <Rect
          ref={r => (cards[i] = r)}
          width={410}
          radius={24}
          fill={C.card}
          stroke={s.color}
          lineWidth={3}
          layout
          direction={'column'}
          alignItems={'center'}
          gap={14}
          padding={[26, 24]}
          opacity={0}
          shadowColor={'#0b1b3a1a'}
          shadowBlur={20}
        >
          <Layout alignItems={'center'} gap={12}>
            <Circle size={46} fill={s.color} layout justifyContent={'center'} alignItems={'center'}>
              <Txt text={`${s.n}`} fontFamily={FONT} fontWeight={800} fontSize={26} fill={'#fff'} />
            </Circle>
            <Txt text={s.name} fontFamily={FONT} fontWeight={800} fontSize={28} fill={C.ink} />
          </Layout>
          <Txt text={s.sub} fontFamily={FONT} fontWeight={700} fontSize={24} fill={s.color} />
          <Txt
            text={s.text}
            width={360}
            textWrap
            textAlign={'center'}
            fontFamily={FONT}
            fontWeight={500}
            fontSize={26}
            lineHeight={36}
            fill={C.ink}
            grow={1}
          />
          <Rect layout padding={[10, 18]} radius={14} fill={s.tint}>
            <Txt text={`Effect: ${s.effect}`} fontFamily={FONT} fontWeight={700} fontSize={24} fill={s.color} />
          </Rect>
        </Rect>
      ))}
    </Layout>,
  );
  for (const card of cards) card.scale(0.9);
  yield* sequence(
    0.35,
    ...cards.map(card => all(card.opacity(1, 0.4), card.scale(1, 0.4, easeOutBack))),
  );
  yield* caption.say('The four steps repeat continuously while the fridge runs: heat in, work in, heat out, pressure drop.');

  const facts = createRef<Node>();
  view.add(
    <Node ref={facts} y={240} opacity={0}>
      <Layout layout gap={30}>
        {[
          ['A fridge does not create cold –', 'it removes heat from the inside.'],
          ['Moving heat from cold to hot', 'needs work (electricity).'],
          ['Qout = Qin + Win', 'heat rejected = heat absorbed + work'],
        ].map(([a, b]) => (
          <Rect
            layout
            direction={'column'}
            alignItems={'center'}
            width={560}
            padding={[16, 20]}
            radius={18}
            fill={'#fff4d6'}
            gap={4}
          >
            <Txt text={a} fontFamily={FONT} fontWeight={800} fontSize={27} fill={C.ink} />
            <Txt text={b} fontFamily={FONT} fontWeight={500} fontSize={25} fill={C.ink} />
          </Rect>
        ))}
      </Layout>
    </Node>,
  );
  yield* all(facts().opacity(1, 0.6), caption.hide());
  yield* waitFor(9);

  yield* all(row().opacity(0, 0.6), facts().opacity(0, 0.6), header.node.opacity(0, 0.6));
  const end = createRef<Node>();
  view.add(
    <Node ref={end} opacity={0}>
      <Txt y={-40} text={'Now you know how a refrigerator works!'} fontFamily={FONT} fontWeight={800} fontSize={64} fill={C.ink} />
      <Txt
        y={40}
        text={'Evaporator → Compressor → Condenser → Expansion valve → repeat'}
        fontFamily={FONT}
        fontWeight={600}
        fontSize={34}
        fill={C.muted}
      />
    </Node>,
  );
  yield* end().opacity(1, 0.8);
  yield* waitFor(4);
  yield* end().opacity(0, 0.8);
});
