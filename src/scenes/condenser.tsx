import {makeScene2D} from '@canvas-commons/2d';
import {all} from '@canvas-commons/core';
import {runStep} from '../components/step';
import {background} from '../components/ui';
import {C} from '../theme';

export default makeScene2D(function* (view) {
  background(view);
  yield* runStep(view, {
    header: 'STEP 3 · CONDENSER',
    color: C.hot,
    title: '3 · Condenser – heat released',
    intro: 'Step 3: the hot, high-pressure gas flows into the condenser.',
    focus: {local: [600, 0], scale: 1.1, screen: [480, -40]},
    panel: 'left',
    meters: {
      x: 560,
      y: 290,
      pressure: 0.9,
      pressureColor: C.hot,
      pressureLabel: 'high',
      temp: 0.92,
      tempColor: C.hot,
      tempLabel: 'hot',
    },
    bullets: [
      {
        text: 'Location: outside the cabinet – the grid of tubes on the back (or underneath) of the fridge.',
        action: ctx => all(...ctx.meters.map(m => m.node.opacity(1, 0.5))),
      },
      {
        text: 'The gas is hotter than the room air, so heat flows OUT of it into the room.',
        action: ctx => ctx.cycle.heatOut.opacity(1, 0.6),
      },
      {
        text: 'Heat path: refrigerant → metal tubes (conduction) → surrounding air (convection). A fan, if fitted, speeds this up.',
      },
      {
        text: 'As it loses heat, the gas CONDENSES into a liquid. The pressure stays high.',
        action: ctx => ctx.meters[1].to(0.6, C.warm, 'warm', 2),
      },
      {
        text: 'The heat released = heat picked up inside the fridge + the compressor’s work.',
      },
      {text: 'Effect: the room around the fridge gets warmer.', bold: true},
    ],
    outro: 'That is why the back of a fridge feels warm. The refrigerant leaves as a warm, high-pressure liquid.',
    quiz: {
      question: 'What happens to the refrigerant in the condenser?',
      options: [
        'It absorbs heat from the room and evaporates',
        'It releases heat to the room and condenses into a liquid',
        'It is squeezed by a motor to raise its pressure',
        'Its pressure drops suddenly and it becomes very cold',
      ],
      answer: 1,
      why: 'In the condenser the hot gas gives its heat to the cooler room air and condenses into a high-pressure liquid.',
    },
  });
});
