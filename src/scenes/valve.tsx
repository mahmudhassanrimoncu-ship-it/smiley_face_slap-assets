import {makeScene2D} from '@canvas-commons/2d';
import {all} from '@canvas-commons/core';
import {runStep} from '../components/step';
import {background} from '../components/ui';
import {C} from '../theme';

export default makeScene2D(function* (view) {
  background(view);
  yield* runStep(view, {
    header: 'STEP 4 · EXPANSION VALVE',
    color: C.valve,
    title: '4 · Expansion valve – pressure drop',
    intro: 'Step 4: the warm, high-pressure liquid reaches the expansion valve.',
    focus: {local: [0, 230], scale: 1.6, screen: [-500, -90]},
    panel: 'right',
    meters: {
      x: -500,
      y: 190,
      pressure: 0.9,
      pressureColor: C.hot,
      pressureLabel: 'high',
      temp: 0.6,
      tempColor: C.warm,
      tempLabel: 'warm',
    },
    bullets: [
      {
        text: 'The liquid is forced through a very narrow opening (in many home fridges, a long thin capillary tube).',
        action: ctx => all(...ctx.meters.map(m => m.node.opacity(1, 0.5))),
      },
      {
        text: 'Its pressure drops suddenly.',
        action: ctx => ctx.meters[0].to(0.22, C.cold, 'low'),
      },
      {
        text: 'At the low pressure, part of the liquid instantly boils into vapour. That takes heat from the rest of the refrigerant, so its temperature falls sharply.',
        action: ctx => ctx.meters[1].to(0.1, C.cold, 'very cold', 2),
      },
      {
        text: 'No work is done and no heat is added here – the cooling comes from the pressure drop.',
      },
      {
        text: 'It leaves as a very cold, low-pressure mix of liquid and vapour, ready for the evaporator again.',
      },
      {text: 'Effect: the refrigerant becomes very cold.', bold: true},
    ],
    outro: 'The loop is complete: the very cold refrigerant re-enters the evaporator and the cycle repeats, over and over.',
    quiz: {
      question: 'Why is the refrigerant very cold just after the expansion valve?',
      options: [
        'Its pressure drops suddenly, so part of it evaporates and cools the rest',
        'The fan blows cold air over the valve',
        'The compressor removes heat from it',
        'Ice inside the valve cools it down',
      ],
      answer: 0,
      why: 'The sudden pressure drop lowers its boiling point. Some liquid flashes to vapour, which takes heat from the rest, so it gets very cold.',
    },
  });
});
