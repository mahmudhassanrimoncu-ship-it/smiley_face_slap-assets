import {makeScene2D} from '@canvas-commons/2d';
import {all} from '@canvas-commons/core';
import {runStep} from '../components/step';
import {background} from '../components/ui';
import {C} from '../theme';

export default makeScene2D(function* (view) {
  background(view);
  yield* runStep(view, {
    header: 'STEP 1 · EVAPORATOR',
    color: C.cold,
    title: '1 · Evaporator – heat absorbed',
    intro: 'Step 1 happens inside the fridge, in the evaporator.',
    focus: {local: [-600, 0], scale: 1.15, screen: [-500, -60]},
    panel: 'right',
    meters: {
      x: -500,
      y: 300,
      pressure: 0.22,
      pressureColor: C.cold,
      pressureLabel: 'low',
      temp: 0.1,
      tempColor: C.cold,
      tempLabel: 'very cold',
    },
    bullets: [
      {
        text: 'The refrigerant arrives as a very cold, low-pressure mix of liquid and vapour.',
        action: ctx => all(...ctx.meters.map(m => m.node.opacity(1, 0.5))),
      },
      {
        text: 'It is colder than the food and air inside, so heat flows INTO it (hot → cold).',
        action: ctx => ctx.cycle.heatIn.opacity(1, 0.6),
      },
      {
        text: 'At this low pressure the refrigerant boils at a very low temperature – well below 0 °C.',
      },
      {
        text: 'The absorbed heat makes the liquid boil (evaporate). While it boils, it stays cold.',
      },
      {
        text: 'It leaves as a low-pressure, cool GAS heading to the compressor.',
      },
      {text: 'Effect: the inside of the fridge gets colder.', bold: true},
    ],
    outro: 'Evaporating needs a lot of energy, so as it boils the refrigerant carries heat away from the inside of the fridge.',
    quiz: {
      question: 'Why does heat flow from the food into the refrigerant in the evaporator?',
      options: [
        'The refrigerant is colder than the food and air inside',
        'The compressor pushes “cold” into the food',
        'The refrigerant is hotter than the food',
        'The fan blows outside air onto the food',
      ],
      answer: 0,
      why: 'Heat always flows from hotter to colder. The refrigerant is colder than the fridge’s contents, so it absorbs their heat and evaporates.',
    },
  });
});
