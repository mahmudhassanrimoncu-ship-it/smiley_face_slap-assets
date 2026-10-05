import {View2D} from '@canvas-commons/2d';
import {ThreadGenerator, all, waitFor} from '@canvas-commons/core';
import {C} from '../theme';
import {Cycle, createCycle} from './cycle';
import {
  QuizSpec,
  createCaption,
  createHeader,
  createMeter,
  createPanel,
  quiz,
  readTime,
} from './ui';

export interface StepContext {
  view: View2D;
  cycle: Cycle;
  meters: ReturnType<typeof createMeter>[];
}

export interface StepBullet {
  text: string;
  bold?: boolean;
  color?: string;
  /** Runs in parallel with the bullet appearing. */
  action?: (ctx: StepContext) => ThreadGenerator;
}

export interface StepConfig {
  header: string;
  color: string;
  title: string;
  intro: string;
  focus: {local: [number, number]; scale: number; screen: [number, number]};
  panel: 'left' | 'right';
  panelWidth?: number;
  meters?: {
    x: number;
    y: number;
    pressure: number;
    pressureColor: string;
    pressureLabel: string;
    temp: number;
    tempColor: string;
    tempLabel: string;
  };
  bullets: StepBullet[];
  outro?: string;
  quiz: QuizSpec;
}

/** A fully visible, running refrigeration loop. */
export function* fullCycle(view: View2D) {
  const cycle = createCycle(view);
  cycle.speed(550);
  cycle.fanSpeed(320);
  yield cycle.run();
  return cycle;
}

export function* runStep(view: View2D, cfg: StepConfig): ThreadGenerator {
  const cycle: Cycle = yield* fullCycle(view);
  cycle.flowIcon.opacity(1);
  const header = createHeader(view);
  const caption = createCaption(view);

  yield* header.set(cfg.header, cfg.color);
  yield* caption.say(cfg.intro);
  yield* all(
    caption.hide(),
    cycle.flowIcon.opacity(0, 0.6),
    cycle.focus(cfg.focus.local, cfg.focus.scale, cfg.focus.screen, 1.6),
  );

  const meters: ReturnType<typeof createMeter>[] = [];
  if (cfg.meters) {
    const m = cfg.meters;
    meters.push(
      createMeter(view, {
        x: m.x,
        y: m.y,
        label: 'PRESSURE',
        value: m.pressure,
        color: m.pressureColor,
      }),
      createMeter(view, {
        x: m.x,
        y: m.y + 86,
        label: 'TEMPERATURE',
        value: m.temp,
        color: m.tempColor,
      }),
    );
    meters[0].setTag(m.pressureLabel);
    meters[1].setTag(m.tempLabel);
  }

  const width = cfg.panelWidth ?? 800;
  const panel = createPanel(view, {
    x: cfg.panel === 'right' ? 520 : -520,
    y: -420,
    width,
    title: cfg.title,
    color: cfg.color,
  });
  panel.node.anchor([0, -1]);
  yield* panel.open();

  const ctx: StepContext = {view, cycle, meters};
  for (const b of cfg.bullets) {
    if (b.action) {
      yield* all(
        panel.bullet(b.text, {bold: b.bold, color: b.color}),
        b.action(ctx),
      );
    } else {
      yield* panel.bullet(b.text, {bold: b.bold, color: b.color});
    }
  }
  yield* waitFor(1);

  yield* all(
    panel.close(),
    ...meters.map(m => m.node.opacity(0, 0.4)),
    cycle.focus([0, 0], 0.8, [-60, 10], 1.4),
  );
  if (cfg.outro) {
    yield* caption.say(cfg.outro, readTime(cfg.outro));
  }
  yield* quiz(view, cfg.quiz);
  yield* caption.hide();
}

export const STEP_COLORS = {
  evaporator: C.cold,
  compressor: C.hot,
  condenser: C.hot,
  valve: C.valve,
};
