import {makeScene2D} from '@canvas-commons/2d';
import {all, easeInOutSine, loop} from '@canvas-commons/core';
import {runStep} from '../components/step';
import {background} from '../components/ui';
import {C} from '../theme';

export default makeScene2D(function* (view) {
  background(view);
  yield* runStep(view, {
    header: 'STEP 2 · COMPRESSOR',
    color: C.hot,
    title: '2 · Compressor – work in',
    intro: 'Step 2: the cool gas is sucked into the compressor.',
    focus: {local: [0, -255], scale: 1.5, screen: [-500, -140]},
    panel: 'right',
    meters: {
      x: -500,
      y: 170,
      pressure: 0.22,
      pressureColor: C.cold,
      pressureLabel: 'low',
      temp: 0.32,
      tempColor: C.coolGas,
      tempLabel: 'cool',
    },
    bullets: [
      {
        text: 'Location: outside the cabinet, usually at the bottom of the back of the fridge.',
      },
      {
        text: 'It takes in the low-pressure, cool gas coming from the evaporator.',
        action: ctx => all(...ctx.meters.map(m => m.node.opacity(1, 0.5))),
      },
      {
        text: 'An electric motor does WORK on the gas, squeezing it into a smaller volume.',
        action: ctx =>
          loop(3, () =>
            all(
              ctx.cycle.workBolt.scale(1.35, 0.35, easeInOutSine).to(1, 0.35, easeInOutSine),
            ),
          ),
      },
      {
        text: 'Its pressure AND its temperature rise a lot.',
        action: ctx =>
          all(
            ctx.meters[0].to(0.9, C.hot, 'high'),
            ctx.meters[1].to(0.92, C.hot, 'hot'),
          ),
      },
      {
        text: 'It leaves as a high-pressure, HOT gas – now hotter than the room air.',
      },
      {
        text: 'The compressor is also the pump that keeps the refrigerant moving around the loop.',
      },
      {text: 'Effect: the gas gets hotter.', bold: true},
    ],
    outro: 'This is where the electrical energy enters the cycle. Without this work, heat could not be moved from cold to hot.',
    quiz: {
      question: 'What happens to the refrigerant gas inside the compressor?',
      options: [
        'Its pressure and temperature both rise',
        'Its pressure rises but its temperature falls',
        'Its pressure and temperature both fall',
        'It turns into a liquid and absorbs heat',
      ],
      answer: 0,
      why: 'The compressor does work on the gas, squeezing it: both its pressure and its temperature go up.',
    },
  });
});
