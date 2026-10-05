import {Circle, Layout, Node, Rect, Txt, View2D} from '@canvas-commons/2d';
import {
  ThreadGenerator,
  all,
  createRef,
  createSignal,
  easeOutBack,
  linear,
  sequence,
  waitFor,
} from '@canvas-commons/core';
import {C, FONT} from '../theme';

export function background(view: View2D) {
  view.fill(C.bg);
  view.add(<Rect size={[1920, 1080]} fill={C.bg} />);
}

/** Reading time for a caption: generous because there is no voice-over. */
export function readTime(text: string, min = 2.6) {
  const words = text.split(/\s+/).length;
  return Math.max(min, 1.0 + words * 0.32);
}

/* ------------------------------------------------------------------ */
/* Section header (top-left)                                           */
/* ------------------------------------------------------------------ */
export function createHeader(view: View2D, initial = '') {
  const pill = createRef<Rect>();
  const txt = createRef<Txt>();
  view.add(
    <Rect
      ref={pill}
      x={-930}
      y={-482}
      anchor={[-1, 0]}
      layout
      padding={[12, 26]}
      radius={40}
      fill={C.ink}
      opacity={initial ? 1 : 0}
    >
      <Txt
        ref={txt}
        text={initial}
        fontFamily={FONT}
        fontWeight={800}
        fontSize={26}
        letterSpacing={1.5}
        fill={'#fff'}
      />
    </Rect>,
  );
  return {
    node: pill(),
    *set(text: string, color: string = C.ink): ThreadGenerator {
      if (pill().opacity() > 0) yield* pill().opacity(0, 0.25);
      txt().text(text);
      pill().fill(color);
      yield* pill().opacity(1, 0.35);
    },
  };
}

/* ------------------------------------------------------------------ */
/* Bottom caption bar                                                  */
/* ------------------------------------------------------------------ */
export function createCaption(view: View2D, y = 448) {
  const box = createRef<Rect>();
  const txt = createRef<Txt>();
  view.add(
    <Rect
      ref={box}
      y={y}
      width={1640}
      height={130}
      radius={24}
      fill={C.card}
      stroke={C.cardLine}
      lineWidth={2}
      shadowColor={'#0b1b3a22'}
      shadowBlur={24}
      shadowOffsetY={6}
      opacity={0}
      layout
      justifyContent={'center'}
      alignItems={'center'}
      padding={[0, 50]}
    >
      <Txt
        ref={txt}
        text={''}
        width={1540}
        textWrap
        textAlign={'center'}
        fontFamily={FONT}
        fontWeight={500}
        fontSize={36}
        lineHeight={50}
        fill={C.ink}
      />
    </Rect>,
  );
  return {
    node: box(),
    /** Show a caption and keep it on screen long enough to read. */
    *say(text: string, hold?: number): ThreadGenerator {
      if (box().opacity() > 0 && txt().text() !== '') {
        yield* txt().opacity(0, 0.25);
      }
      txt().text(text);
      if (box().opacity() < 1) {
        txt().opacity(1);
        yield* box().opacity(1, 0.35);
      } else {
        yield* txt().opacity(1, 0.3);
      }
      yield* waitFor(hold ?? readTime(text));
    },
    /** Same as say() but returns immediately after the text appears. */
    *show(text: string): ThreadGenerator {
      yield* this.say(text, 0);
    },
    *hide(): ThreadGenerator {
      yield* box().opacity(0, 0.3);
      txt().text('');
    },
  };
}

/* ------------------------------------------------------------------ */
/* Info panel with bullet points                                       */
/* ------------------------------------------------------------------ */
export function createPanel(
  view: View2D,
  props: {x: number; y: number; width: number; title: string; color: string},
) {
  const box = createRef<Rect>();
  view.add(
    <Rect
      ref={box}
      x={props.x}
      y={props.y}
      width={props.width}
      radius={26}
      fill={C.card}
      stroke={props.color}
      lineWidth={3}
      shadowColor={'#0b1b3a26'}
      shadowBlur={30}
      shadowOffsetY={8}
      layout
      direction={'column'}
      gap={18}
      padding={[30, 36]}
      opacity={0}
    >
      <Txt
        text={props.title}
        fontFamily={FONT}
        fontWeight={800}
        fontSize={36}
        fill={props.color}
      />
      <Rect height={4} width={80} radius={2} fill={props.color} />
    </Rect>,
  );
  return {
    node: box(),
    *open(): ThreadGenerator {
      box().scale(0.92);
      yield* all(box().opacity(1, 0.4), box().scale(1, 0.4, easeOutBack));
    },
    *close(): ThreadGenerator {
      yield* box().opacity(0, 0.35);
    },
    /** Add a bullet; returns after it has faded in plus reading time. */
    *bullet(
      text: string,
      opts: {color?: string; hold?: number; bold?: boolean} = {},
    ): ThreadGenerator {
      const row = createRef<Layout>();
      box().add(
        <Layout ref={row} gap={16} alignItems={'start'} opacity={0}>
          <Circle
            size={14}
            marginTop={14}
            fill={opts.color ?? props.color}
          />
          <Txt
            text={text}
            width={props.width - 72 - 30}
            textWrap
            fontFamily={FONT}
            fontWeight={opts.bold ? 700 : 500}
            fontSize={30}
            lineHeight={42}
            fill={opts.bold ? (opts.color ?? props.color) : C.ink}
          />
        </Layout>,
      );
      yield* row().opacity(1, 0.4);
      yield* waitFor(opts.hold ?? readTime(text));
    },
  };
}

/* ------------------------------------------------------------------ */
/* Quiz card                                                           */
/* ------------------------------------------------------------------ */
export interface QuizSpec {
  label?: string;
  question: string;
  options: string[];
  answer: number;
  why: string;
  think?: number;
}

export function* quiz(view: View2D, q: QuizSpec): ThreadGenerator {
  const overlay = createRef<Node>();
  const dim = createRef<Rect>();
  const card = createRef<Rect>();
  const why = createRef<Rect>();
  const options: Rect[] = [];
  const letters: Circle[] = [];
  const remaining = createSignal(1);
  const think = q.think ?? 6;

  view.add(
    <Node ref={overlay}>
      <Rect ref={dim} size={[1920, 1080]} fill={'#0b1530'} opacity={0} />
      <Rect
        ref={card}
        y={-40}
        width={1360}
        radius={32}
        fill={C.card}
        layout
        direction={'column'}
        alignItems={'center'}
        gap={22}
        padding={[38, 60, 44, 60]}
        opacity={0}
        scale={0.9}
        shadowColor={'#00000055'}
        shadowBlur={60}
      >
        <Layout width={1240} justifyContent={'space-between'} alignItems={'center'}>
          <Rect layout padding={[10, 22]} radius={30} fill={'#fff4d6'} gap={10}>
            <Txt
              text={q.label ?? 'QUICK CHECK'}
              fontFamily={FONT}
              fontWeight={800}
              fontSize={24}
              letterSpacing={1.5}
              fill={'#9a6700'}
            />
          </Rect>
          <Layout alignItems={'center'} gap={14}>
            <Txt
              text={'Pause & think'}
              fontFamily={FONT}
              fontWeight={600}
              fontSize={24}
              fill={C.muted}
            />
            <Circle
              size={64}
              stroke={'#e3e8f0'}
              lineWidth={7}
              layout
              justifyContent={'center'}
              alignItems={'center'}
            >
              <Circle
                layout={false}
                size={64}
                stroke={C.work}
                lineWidth={7}
                startAngle={-90}
                endAngle={() => -90 + 360 * remaining()}
                lineCap={'round'}
              />
              <Txt
                text={() => `${Math.max(1, Math.ceil(remaining() * think))}`}
                fontFamily={FONT}
                fontWeight={800}
                fontSize={26}
                fill={C.ink}
              />
            </Circle>
          </Layout>
        </Layout>
        <Txt
          text={q.question}
          width={1240}
          textWrap
          textAlign={'center'}
          fontFamily={FONT}
          fontWeight={700}
          fontSize={42}
          lineHeight={56}
          fill={C.ink}
          marginBottom={6}
        />
        {q.options.map((o, i) => (
          <Rect
            ref={r => (options[i] = r)}
            width={1180}
            radius={18}
            fill={'#f5f7fb'}
            stroke={'#d6deea'}
            lineWidth={3}
            layout
            alignItems={'center'}
            gap={22}
            padding={[14, 22]}
            opacity={0}
          >
            <Circle
              ref={r => (letters[i] = r)}
              size={48}
              fill={C.ink}
              layout
              justifyContent={'center'}
              alignItems={'center'}
            >
              <Txt
                text={'ABCD'[i]}
                fontFamily={FONT}
                fontWeight={800}
                fontSize={26}
                fill={'#fff'}
              />
            </Circle>
            <Txt
              text={o}
              width={1060}
              textWrap
              fontFamily={FONT}
              fontWeight={600}
              fontSize={32}
              lineHeight={42}
              fill={C.ink}
            />
          </Rect>
        ))}
        <Rect
          ref={why}
          width={1180}
          radius={18}
          fill={'#e9f7ec'}
          layout
          padding={[16, 26]}
          opacity={0}
        >
          <Txt
            text={`✓  ${q.why}`}
            width={1128}
            textWrap
            fontFamily={FONT}
            fontWeight={600}
            fontSize={30}
            lineHeight={42}
            fill={'#1f6e33'}
          />
        </Rect>
      </Rect>
    </Node>,
  );

  yield* all(
    dim().opacity(0.55, 0.4),
    card().opacity(1, 0.45),
    card().scale(1, 0.45, easeOutBack),
  );
  yield* sequence(0.15, ...options.map(o => o.opacity(1, 0.3)));
  yield* remaining(0, think, linear);

  const ok = options[q.answer];
  yield* all(
    ...options.map((o, i) =>
      i === q.answer ? o.opacity(1, 0.3) : o.opacity(0.35, 0.3),
    ),
    ok.fill('#e9f7ec', 0.3),
    ok.stroke(C.good, 0.3),
    letters[q.answer].fill(C.good, 0.3),
    ok.scale(1.03, 0.3, easeOutBack),
    why().opacity(1, 0.4),
  );
  yield* waitFor(readTime(q.why, 3.5) + 0.8);
  yield* all(card().opacity(0, 0.35), dim().opacity(0, 0.35));
  overlay().remove();
}

/* ------------------------------------------------------------------ */
/* Simple horizontal meter (pressure / temperature)                    */
/* ------------------------------------------------------------------ */
export function createMeter(
  parent: Node,
  props: {x: number; y: number; label: string; value: number; color: string},
) {
  const fill = createRef<Rect>();
  const tag = createRef<Txt>();
  const root = createRef<Layout>();
  const W = 360;
  parent.add(
    <Layout ref={root} x={props.x} y={props.y} direction={'column'} gap={10} layout opacity={0}>
      <Layout justifyContent={'space-between'} width={W}>
        <Txt
          text={props.label}
          fontFamily={FONT}
          fontWeight={800}
          fontSize={24}
          letterSpacing={1}
          fill={C.ink}
        />
        <Txt
          ref={tag}
          text={''}
          fontFamily={FONT}
          fontWeight={700}
          fontSize={24}
          fill={props.color}
        />
      </Layout>
      <Rect width={W} height={26} radius={13} fill={'#e3e8f0'} clip>
        <Rect
          ref={fill}
          layout={false}
          x={-W / 2}
          anchor={[-1, 0]}
          width={W * props.value}
          height={26}
          radius={13}
          fill={props.color}
        />
      </Rect>
    </Layout>,
  );
  return {
    node: root(),
    *to(value: number, color: string, label: string, time = 1.2): ThreadGenerator {
      tag().text(label);
      yield* all(
        fill().width(W * value, time),
        fill().fill(color, time),
        tag().fill(color, time),
      );
    },
    setTag(label: string) {
      tag().text(label);
    },
  };
}

/** Pulsing highlight ring around a point (in the given parent's space). */
export function* pulse(
  parent: Node,
  pos: [number, number],
  size: number,
  color: string,
  times = 2,
): ThreadGenerator {
  const ring = createRef<Circle>();
  parent.add(
    <Circle
      ref={ring}
      position={pos}
      size={size}
      stroke={color}
      lineWidth={8}
      opacity={0}
    />,
  );
  for (let i = 0; i < times; i++) {
    ring().size(size * 0.8).opacity(0.9);
    yield* all(ring().size(size * 1.25, 0.9), ring().opacity(0, 0.9));
  }
  ring().remove();
}
