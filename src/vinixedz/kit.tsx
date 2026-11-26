import {
  Circle,
  Gradient,
  Line,
  Node,
  Rect,
  Txt,
  View2D,
} from '@canvas-commons/2d';
import {
  PlaybackState,
  ThreadGenerator,
  all,
  createRef,
  createSignal,
  easeInCubic,
  easeInOutCubic,
  easeOutCubic,
  easeOutExpo,
  linear,
  sequence,
  usePlayback,
  waitFor,
} from '@canvas-commons/core';
import data from './script.json';
import sources from './sources.json';

export const SRC_NUM: Record<string, number> = Object.fromEntries(
  (sources as {key: string}[]).map((x, i) => [x.key, i + 1]),
);
import {FONT, MONO, TAG_COLOR, Tag, V} from './theme';

/* ------------------------------------------------------------------ */
/* Render log: subtitle timing, sound cues and footage slots are       */
/* written to the console while rendering and collected afterwards.    */
/* ------------------------------------------------------------------ */
export function log(kind: string, ...parts: (string | number)[]) {
  const p = usePlayback();
  if (p.state === PlaybackState.Rendering) {
    console.log(`VNX|${kind}|${p.frame}|${parts.join('|')}`);
  }
}

export type Sfx =
  | 'whoosh'
  | 'whooshBig'
  | 'impact'
  | 'sub'
  | 'tick'
  | 'blip'
  | 'riser'
  | 'glitch'
  | 'count'
  | 'shutter'
  | 'pop'
  | 'swell';

/** Place a sound-design cue at the current frame. */
export function sfx(type: Sfx, dur = 0) {
  log('SFX', type, dur);
}

export function globalTime() {
  const p = usePlayback();
  return p.frame / p.fps;
}

/* ------------------------------------------------------------------ */
/* Deterministic pseudo random                                         */
/* ------------------------------------------------------------------ */
export function rng(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

/* ------------------------------------------------------------------ */
/* Backdrop: continuous across scenes because it is driven by the      */
/* global frame, so every cut between scenes is seamless.              */
/* ------------------------------------------------------------------ */
export function backdrop(view: View2D, accent: string = V.cyan) {
  view.fill(V.bg);
  const t = createSignal(0);
  const root = createRef<Node>();
  const r = rng(7);
  const dust = Array.from({length: 46}, () => ({
    x: r() * 2200 - 1100,
    y: r() * 1300 - 650,
    z: 0.3 + r() * 0.9,
    s: 2 + r() * 4,
  }));
  view.add(
    <Node ref={root} zIndex={-100}>
      <Rect
        size={[1920, 1080]}
        fill={
          new Gradient({
            type: 'radial',
            fromRadius: 0,
            toRadius: 1250,
            from: [0, -120],
            to: [0, -120],
            stops: [
              {offset: 0, color: V.bg2},
              {offset: 1, color: V.bg},
            ],
          })
        }
      />
      {/* perspective floor grid */}
      <Node y={160}>
        {Array.from({length: 23}, (_, i) => {
          const xBottom = (i - 11) * 230;
          return (
            <Line
              points={[
                [xBottom * 0.12, -40],
                [xBottom, 420],
              ]}
              stroke={V.lineSoft}
              lineWidth={1.5}
              opacity={0.55}
            />
          );
        })}
        {Array.from({length: 9}, (_, i) => (
          <Line
            points={() => {
              const k = ((i + (t() * 0.18) % 1) / 9) ** 2;
              const y = -40 + k * 460;
              const w = 140 + k * 2600;
              return [
                [-w / 2, y],
                [w / 2, y],
              ];
            }}
            stroke={V.lineSoft}
            lineWidth={1.5}
            opacity={() => 0.15 + 0.5 * ((i + (t() * 0.18) % 1) / 9)}
          />
        ))}
      </Node>
      {/* soft accent glow */}
      <Circle
        size={1100}
        x={() => Math.sin(t() * 0.07) * 260}
        y={() => -260 + Math.cos(t() * 0.05) * 80}
        fill={
          new Gradient({
            type: 'radial',
            fromRadius: 0,
            toRadius: 550,
            stops: [
              {offset: 0, color: accent + '1c'},
              {offset: 1, color: accent + '00'},
            ],
          })
        }
      />
      {/* drifting dust (parallax by depth) */}
      {dust.map(d => (
        <Circle
          size={d.s * d.z}
          fill={V.inkDim}
          opacity={0.12 + 0.25 * d.z}
          x={() => (((d.x + t() * 14 * d.z + 1100) % 2200) + 2200) % 2200 - 1100}
          y={() => d.y + Math.sin(t() * 0.3 * d.z + d.x) * 18}
        />
      ))}
      {/* vignette */}
      <Rect
        size={[1920, 1080]}
        fill={
          new Gradient({
            type: 'radial',
            fromRadius: 380,
            toRadius: 1150,
            stops: [
              {offset: 0, color: '#00000000'},
              {offset: 1, color: '#000000c8'},
            ],
          })
        }
      />
    </Node>,
  );
  function* loop(): ThreadGenerator {
    while (true) {
      t(globalTime());
      yield;
    }
  }
  t(globalTime());
  return {node: root(), loop};
}

/* ------------------------------------------------------------------ */
/* Bottom narration subtitles                                          */
/* ------------------------------------------------------------------ */
type Line_ = {text: string; tag?: Tag; src?: string[]};
type SceneData = {
  id: string;
  chapter: {n: string; title: string} | null;
  name: string;
  lines: Line_[];
};

export const SCRIPT = data as {title: string; subtitle: string; scenes: SceneData[]};

/** How long a sentence stays on screen. Not tied to any speaking speed. */
export function holdFor(text: string) {
  const words = text.trim().split(/\s+/).length;
  return Math.min(9.5, Math.max(4.2, 1.9 + 0.31 * words));
}

export function narration(view: View2D, sceneId: string) {
  const scene = SCRIPT.scenes.find(s => s.id === sceneId)!;
  const idx = createSignal(-1);
  let finished = false;
  const bar = createRef<Rect>();
  const txt = createRef<Txt>();
  const pill = createRef<Rect>();
  const pillTxt = createRef<Txt>();
  const pillDot = createRef<Circle>();
  view.add(
    <Node y={436} zIndex={100}>
      <Rect
        ref={bar}
        width={1560}
        height={112}
        radius={18}
        fill={'#05070cd0'}
        stroke={'#ffffff14'}
        lineWidth={1.5}
        opacity={0}
        layout
        justifyContent={'center'}
        alignItems={'center'}
        padding={[0, 48]}
      >
        <Txt
          ref={txt}
          text={''}
          width={1460}
          textWrap
          textAlign={'center'}
          fontFamily={FONT}
          fontWeight={500}
          fontSize={35}
          lineHeight={47}
          fill={V.ink}
        />
      </Rect>
      <Rect
        ref={pill}
        x={-780}
        y={-80}
        anchor={[-1, 0]}
        layout
        alignItems={'center'}
        gap={10}
        padding={[7, 16]}
        radius={8}
        fill={'#05070ce8'}
        stroke={V.green}
        lineWidth={1.5}
        opacity={0}
      >
        <Circle ref={pillDot} size={10} fill={V.green} />
        <Txt
          ref={pillTxt}
          text={'VERIFIED'}
          fontFamily={MONO}
          fontWeight={700}
          fontSize={17}
          letterSpacing={2}
          fill={V.green}
        />
      </Rect>
    </Node>,
  );

  function* run(): ThreadGenerator {
    for (let i = 0; i < scene.lines.length; i++) {
      const line = scene.lines[i];
      const hold = holdFor(line.text);
      txt().text(line.text);
      const tag = line.tag;
      if (tag) {
        const c = TAG_COLOR[tag];
        pill().stroke(c);
        pillDot().fill(c);
        pillTxt().fill(c);
        pillTxt().text(
          tag + (line.src ? '  ·  ' + line.src.map(k => `[${SRC_NUM[k]}]`).join('') : ''),
        );
      }
      idx(i);
      log('SUB', sceneId, i);
      txt().opacity(0);
      yield* all(
        bar().opacity(1, 0.3),
        txt().opacity(1, 0.35),
        pill().opacity(tag ? 1 : 0, 0.3),
      );
      yield* waitFor(hold - 0.65);
      yield* all(txt().opacity(0, 0.3), pill().opacity(0, 0.3));
      log('SUBEND', sceneId, i);
    }
    yield* bar().opacity(0, 0.3);
    finished = true;
  }

  return {
    idx,
    run,
    count: scene.lines.length,
    /** Wait until line i has started. */
    *at(i: number): ThreadGenerator {
      while (idx() < i) yield;
    },
    *end(): ThreadGenerator {
      while (!finished) yield;
    },
  };
}

/* ------------------------------------------------------------------ */
/* Chapter card                                                        */
/* ------------------------------------------------------------------ */
export function* chapterCard(
  view: View2D,
  n: string,
  title: string,
  accent: string = V.cyan,
): ThreadGenerator {
  const root = createRef<Node>();
  const num = createRef<Txt>();
  const ttl = createRef<Txt>();
  const lineL = createRef<Line>();
  const tagTxt = createRef<Txt>();
  const maskW = createSignal(0);
  view.add(
    <Node ref={root} zIndex={50}>
      <Txt
        ref={num}
        text={n}
        fontFamily={FONT}
        fontWeight={900}
        fontSize={420}
        fill={'#00000000'}
        stroke={accent}
        lineWidth={3}
        opacity={0}
        y={-60}
        letterSpacing={-10}
      />
      <Txt
        ref={tagTxt}
        text={`CHAPTER ${n}`}
        fontFamily={MONO}
        fontWeight={700}
        fontSize={24}
        letterSpacing={10}
        fill={accent}
        y={-300}
        opacity={0}
      />
      <Rect y={170} width={() => maskW()} height={130} clip>
        <Txt
          ref={ttl}
          text={title}
          fontFamily={FONT}
          fontWeight={900}
          fontSize={96}
          letterSpacing={6}
          fill={V.ink}
        />
      </Rect>
      <Line
        ref={lineL}
        points={[
          [-700, 250],
          [700, 250],
        ]}
        stroke={accent}
        lineWidth={4}
        end={0}
      />
    </Node>,
  );
  sfx('whooshBig');
  num().scale(1.25);
  yield* all(
    num().opacity(0.9, 0.6),
    num().scale(1, 0.9, easeOutExpo),
    tagTxt().opacity(1, 0.6),
    lineL().end(1, 0.9, easeInOutCubic),
    sequence(0.25, waitFor(0), maskW(1700, 0.9, easeOutExpo)),
  );
  sfx('sub');
  yield* waitFor(1.6);
  sfx('whoosh');
  yield* all(
    root().scale(2.6, 0.75, easeInCubic),
    root().opacity(0, 0.75, easeInCubic),
  );
  root().remove();
}

/* ------------------------------------------------------------------ */
/* Small UI pieces                                                     */
/* ------------------------------------------------------------------ */
export function SourceTag(props: {
  text: string;
  color?: string;
  x?: number;
  y?: number;
  opacity?: number;
}) {
  return (
    <Rect
      x={props.x ?? 0}
      y={props.y ?? 0}
      layout
      padding={[6, 12]}
      radius={6}
      fill={'#00000066'}
      stroke={props.color ?? V.faint}
      lineWidth={1.2}
      opacity={props.opacity ?? 1}
    >
      <Txt
        text={props.text}
        fontFamily={MONO}
        fontSize={16}
        fontWeight={500}
        letterSpacing={1}
        fill={props.color ?? V.muted}
      />
    </Rect>
  );
}

export function Label(props: {
  text: string;
  size?: number;
  color?: string;
  weight?: number;
  x?: number;
  y?: number;
  mono?: boolean;
  spacing?: number;
  opacity?: number;
  refFn?: (t: Txt) => void;
  align?: 'left' | 'center' | 'right';
  width?: number;
}) {
  return (
    <Txt
      ref={props.refFn}
      text={props.text}
      x={props.x ?? 0}
      y={props.y ?? 0}
      fontFamily={props.mono ? MONO : FONT}
      fontSize={props.size ?? 32}
      fontWeight={props.weight ?? 600}
      fill={props.color ?? V.ink}
      letterSpacing={props.spacing ?? 0}
      opacity={props.opacity ?? 1}
      textAlign={props.align ?? 'center'}
      width={props.width}
      textWrap={props.width ? true : false}
    />
  );
}

/** A reserved rectangle where the editor drops real footage. */
export function FootageSlot(props: {
  id: string;
  desc: string;
  w: number;
  h: number;
  x?: number;
  y?: number;
  accent?: string;
  refFn?: (r: Rect) => void;
  opacity?: number;
  small?: boolean;
}) {
  const accent = props.accent ?? V.cyan;
  const n = Math.ceil((props.w + props.h) / 38);
  return (
    <Rect
      ref={props.refFn}
      x={props.x ?? 0}
      y={props.y ?? 0}
      size={[props.w, props.h]}
      radius={14}
      fill={V.panel}
      stroke={accent + '88'}
      lineWidth={2}
      clip
      opacity={props.opacity ?? 1}
    >
      {Array.from({length: n}, (_, i) => (
        <Line
          points={[
            [-props.w / 2 - props.h + i * 38, props.h / 2],
            [-props.w / 2 + i * 38, -props.h / 2],
          ]}
          stroke={accent + '16'}
          lineWidth={10}
        />
      ))}
      <Txt
        y={props.small ? -14 : -24}
        text={'FOOTAGE SLOT ' + props.id}
        fontFamily={MONO}
        fontWeight={700}
        fontSize={props.small ? 15 : 20}
        letterSpacing={3}
        fill={accent}
      />
      <Txt
        y={props.small ? 14 : 18}
        width={props.w - 40}
        textWrap
        textAlign={'center'}
        text={props.desc}
        fontFamily={FONT}
        fontWeight={500}
        fontSize={props.small ? 15 : 20}
        lineHeight={props.small ? 20 : 27}
        fill={V.muted}
      />
      {/* corner brackets */}
      {[
        [-1, -1],
        [1, -1],
        [1, 1],
        [-1, 1],
      ].map(([sx, sy]) => (
        <Line
          points={[
            [(sx * props.w) / 2 - sx * 8, (sy * props.h) / 2 - sy * 34],
            [(sx * props.w) / 2 - sx * 8, (sy * props.h) / 2 - sy * 8],
            [(sx * props.w) / 2 - sx * 34, (sy * props.h) / 2 - sy * 8],
          ]}
          stroke={accent}
          lineWidth={3}
        />
      ))}
    </Rect>
  );
}

export function slotLog(id: string, desc: string) {
  log('SLOT', id, desc.replace(/\|/g, '/'));
}

/** Rounded data card. */
export function Card(props: {
  w: number;
  h: number;
  x?: number;
  y?: number;
  stroke?: string;
  refFn?: (r: Rect) => void;
  opacity?: number;
  children?: any;
  fill?: string;
}) {
  return (
    <Rect
      ref={props.refFn}
      x={props.x ?? 0}
      y={props.y ?? 0}
      size={[props.w, props.h]}
      radius={18}
      fill={props.fill ?? V.panel + 'ee'}
      stroke={props.stroke ?? V.line}
      lineWidth={2}
      opacity={props.opacity ?? 0}
      shadowColor={'#00000090'}
      shadowBlur={40}
      shadowOffsetY={14}
    >
      {props.children}
    </Rect>
  );
}

/** Pop a node in with a small rise. */
export function* popIn(node: Node, d = 0.55, dy = 30): ThreadGenerator {
  const y = node.y();
  node.y(y + dy);
  node.opacity(0);
  yield* all(node.opacity(1, d, easeOutCubic), node.y(y, d, easeOutExpo));
}

export function* fadeOut(nodes: Node[], d = 0.45): ThreadGenerator {
  yield* all(...nodes.map(n => n.opacity(0, d)));
}

/** Format a number for counters. */
export function fmt(v: number, decimals = 0, suffix = '') {
  return (
    v.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }) + suffix
  );
}

/** Animated number counter text. */
export function counter(
  initial = 0,
): {value: ReturnType<typeof createSignal<number>>} {
  return {value: createSignal(initial)};
}

export function* tickCount(
  sig: (v?: number, d?: number, e?: any) => any,
  to: number,
  d: number,
): ThreadGenerator {
  sfx('count', d);
  yield* sig(to, d, easeOutCubic);
}

/** Standard scene shell: backdrop, narration and optional chapter card. */
export function* openScene(
  view: View2D,
  sceneId: string,
  accent: string = V.cyan,
): Generator<any, ReturnType<typeof narration>, any> {
  const bg = backdrop(view, accent);
  yield bg.loop();
  const scene = SCRIPT.scenes.find(s => s.id === sceneId)!;
  log('SCENE', sceneId);
  const nar = narration(view, sceneId);
  if (scene.chapter) {
    yield* chapterCard(view, scene.chapter.n, scene.chapter.title, accent);
  }
  yield nar.run();
  return nar;
}

export {linear, easeInOutCubic};

/** Source reference string like "[4][5]". */
export function refs(...keys: string[]) {
  return keys.map(k => `[${SRC_NUM[k]}]`).join('');
}

export function Chip(props: {
  text: string;
  color?: string;
  x?: number;
  y?: number;
  size?: number;
  filled?: boolean;
  refFn?: (r: Rect) => void;
  opacity?: number;
}) {
  const c = props.color ?? V.cyan;
  return (
    <Rect
      ref={props.refFn}
      x={props.x ?? 0}
      y={props.y ?? 0}
      layout
      padding={[8, 18]}
      radius={40}
      fill={props.filled ? c : c + '18'}
      stroke={c}
      lineWidth={1.5}
      opacity={props.opacity ?? 1}
    >
      <Txt
        text={props.text}
        fontFamily={MONO}
        fontWeight={700}
        fontSize={props.size ?? 20}
        letterSpacing={2}
        fill={props.filled ? V.bg : c}
      />
    </Rect>
  );
}

/** Dated fact card used in timelines. */
export function DateCard(props: {
  date: string;
  title: string;
  body?: string;
  src?: string;
  color?: string;
  x?: number;
  y?: number;
  w?: number;
  refFn?: (r: Rect) => void;
  opacity?: number;
}) {
  const c = props.color ?? V.cyan;
  const w = props.w ?? 520;
  return (
    <Rect
      ref={props.refFn}
      x={props.x ?? 0}
      y={props.y ?? 0}
      width={w}
      layout
      direction={'column'}
      gap={10}
      padding={[26, 30]}
      radius={18}
      fill={V.panel + 'f0'}
      stroke={c + '99'}
      lineWidth={2}
      opacity={props.opacity ?? 0}
      shadowColor={'#00000090'}
      shadowBlur={40}
      shadowOffsetY={14}
    >
      <Txt text={props.date} fontFamily={MONO} fontWeight={700} fontSize={22} letterSpacing={4} fill={c} />
      <Txt
        text={props.title}
        width={w - 60}
        textWrap
        fontFamily={FONT}
        fontWeight={800}
        fontSize={38}
        lineHeight={46}
        fill={V.ink}
      />
      {props.body ? (
        <Txt
          text={props.body}
          width={w - 60}
          textWrap
          fontFamily={FONT}
          fontWeight={500}
          fontSize={24}
          lineHeight={33}
          fill={V.inkDim}
        />
      ) : null}
      {props.src ? (
        <Txt text={'SOURCE ' + props.src} fontFamily={MONO} fontSize={16} letterSpacing={2} fill={V.muted} />
      ) : null}
    </Rect>
  );
}

/** Big kinetic headline that slides and fades in. */
export function* headline(
  view: View2D,
  text: string,
  opts: {y?: number; size?: number; color?: string; outline?: boolean; x?: number} = {},
): Generator<any, Txt, any> {
  const t = createRef<Txt>();
  view.add(
    <Txt
      ref={t}
      text={text}
      x={(opts.x ?? 0) - 60}
      y={opts.y ?? -100}
      fontFamily={FONT}
      fontWeight={900}
      fontSize={opts.size ?? 120}
      letterSpacing={4}
      fill={opts.outline ? '#00000000' : opts.color ?? V.ink}
      stroke={opts.outline ? opts.color ?? V.cyan : undefined}
      lineWidth={opts.outline ? 3 : 0}
      opacity={0}
    />,
  );
  yield* all(t().opacity(1, 0.5), t().x(opts.x ?? 0, 0.9, easeOutExpo));
  return t();
}

/** Run a tween and fire a sound cue exactly when it starts. */
export function* withSfx(type: Sfx, task: ThreadGenerator): ThreadGenerator {
  sfx(type);
  yield* task;
}
