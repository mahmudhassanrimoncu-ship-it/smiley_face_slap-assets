import {Circle, Line, Node, Rect, Txt} from '@canvas-commons/2d';
import {
  Color,
  SimpleSignal,
  ThreadGenerator,
  Vector2,
  all,
  createRef,
  createSignal,
  easeInOutCubic,
  usePlayback,
} from '@canvas-commons/core';
import {C, FONT} from '../theme';

type Pt = [number, number];

/*
 * Diagram coordinates (before the root node is scaled):
 *
 *   (-520,-260) ───── compressor (0,-260) ─────► (520,-260)
 *        ▲                                          │
 *   evaporator (-520,0)                     condenser (520,0)
 *        │                                          ▼
 *   (-520, 240) ◄──── expansion valve (0,240) ─── (520, 240)
 *
 * The refrigerant travels clockwise on screen.
 */
const HW = 520;

export const LOC = {
  evaporator: new Vector2(-HW, 0),
  compressor: new Vector2(0, -255),
  condenser: new Vector2(HW, 0),
  valve: new Vector2(0, 240),
  fan: new Vector2(HW + 210, 0),
};

// A serpentine coil that starts at (cx, y0), stacks `passes` horizontal runs
// in direction `dir` (-1 = upwards, +1 = downwards) and ends back at cx.
function serpentine(
  cx: number,
  y0: number,
  dir: number,
  width: number,
  passes: number,
  r: number,
): Pt[] {
  const xL = cx - width / 2;
  const xR = cx + width / 2;
  const pts: Pt[] = [[cx, y0]];
  let side = xL;
  for (let i = 0; i < passes; i++) {
    const y = y0 + dir * 2 * r * i;
    if (i === passes - 1) {
      pts.push([cx, y]);
      break;
    }
    pts.push([side, y]);
    // semicircle bulging outwards
    const cy = y + dir * r;
    const theta0 = (-dir * Math.PI) / 2;
    const sweep = side === xR ? dir * Math.PI : -dir * Math.PI;
    for (let k = 1; k <= 12; k++) {
      const t = theta0 + (sweep * k) / 12;
      pts.push([side + r * Math.cos(t), cy + r * Math.sin(t)]);
    }
    side = side === xL ? xR : xL;
  }
  return pts;
}

const EVAP = {passes: 4, r: 24, width: 180, y0: 72};
const COND = {passes: 7, r: 16, width: 170, y0: -96};

function buildLoop() {
  const pts: Pt[] = [];
  pts.push([0, 240]); // expansion valve (s = 0)
  pts.push([-HW, 240]);
  const evap = serpentine(-HW, EVAP.y0, -1, EVAP.width, EVAP.passes, EVAP.r);
  const evapIn = pts.length;
  pts.push(...evap);
  const evapOut = pts.length - 1;
  pts.push([-HW, -260]);
  const comp = pts.length;
  pts.push([0, -260]);
  pts.push([HW, -260]);
  const cond = serpentine(HW, COND.y0, 1, COND.width, COND.passes, COND.r);
  const condIn = pts.length;
  pts.push(...cond);
  const condOut = pts.length - 1;
  pts.push([HW, 240]);
  pts.push([0, 240]); // back to the valve

  const cum: number[] = [0];
  for (let i = 1; i < pts.length; i++) {
    const dx = pts[i][0] - pts[i - 1][0];
    const dy = pts[i][1] - pts[i - 1][1];
    cum.push(cum[i - 1] + Math.hypot(dx, dy));
  }
  return {
    pts,
    cum,
    L: cum[cum.length - 1],
    compIndex: comp,
    s: {
      evapIn: cum[evapIn],
      evapOut: cum[evapOut],
      comp: cum[comp],
      condIn: cum[condIn],
      condOut: cum[condOut],
    },
  };
}

export const LOOP = buildLoop();

function pointAt(s: number): Vector2 {
  const {pts, cum, L} = LOOP;
  s = ((s % L) + L) % L;
  let lo = 0;
  let hi = cum.length - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (cum[mid] <= s) lo = mid;
    else hi = mid;
  }
  const seg = cum[hi] - cum[lo] || 1;
  const t = (s - cum[lo]) / seg;
  return new Vector2(
    pts[lo][0] + (pts[hi][0] - pts[lo][0]) * t,
    pts[lo][1] + (pts[hi][1] - pts[lo][1]) * t,
  );
}

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const frac = (a: number, b: number, s: number) =>
  Math.min(1, Math.max(0, (s - a) / (b - a)));

/*
 * Physical state of the refrigerant along the loop (s measured from the
 * expansion valve). Density: liquid is packed tightly and moves slowly, gas
 * is spread out and moves fast. Quality: fraction that is vapour.
 */
function stateAt(s: number) {
  const k = LOOP.s;
  if (s < k.evapIn) return {density: 1.8, quality: 0.25};
  if (s < k.evapOut) {
    const t = frac(k.evapIn, k.evapOut, s);
    return {density: lerp(1.8, 1.0, t), quality: lerp(0.25, 1, t)};
  }
  if (s < k.comp) return {density: 1.0, quality: 1};
  if (s < k.condIn) return {density: 1.4, quality: 1};
  if (s < k.condOut) {
    const t = frac(k.condIn, k.condOut, s);
    return {density: lerp(1.4, 2.6, t), quality: lerp(1, 0, t)};
  }
  return {density: 2.6, quality: 0};
}

const cold = new Color(C.cold);
const coolGas = new Color(C.coolGas);
const hot = new Color(C.hot);
const warmLiquid = new Color(C.warmLiquid);

function colorAt(s: number): Color {
  const k = LOOP.s;
  if (s < k.evapOut) return cold;
  if (s < k.comp) return Color.lerp(cold, coolGas, frac(k.evapOut, k.evapOut + 160, s));
  if (s < k.condIn) return hot;
  if (s < k.condOut) return Color.lerp(hot, warmLiquid, frac(k.condIn, k.condOut, s));
  return warmLiquid;
}

// Cumulative "mass" table so particles bunch up where the refrigerant is dense.
const STEP = 2;
const MASS: number[] = (() => {
  const table = [0];
  for (let s = STEP; s <= LOOP.L + STEP; s += STEP) {
    table.push(table[table.length - 1] + stateAt(s - STEP / 2).density * STEP);
  }
  return table;
})();
const TOTAL_MASS = MASS[Math.floor(LOOP.L / STEP)];

function sFromMass(m: number): number {
  m = ((m % TOTAL_MASS) + TOTAL_MASS) % TOTAL_MASS;
  let lo = 0;
  let hi = MASS.length - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (MASS[mid] <= m) lo = mid;
    else hi = mid;
  }
  const t = (m - MASS[lo]) / (MASS[hi] - MASS[lo] || 1);
  return (lo + t) * STEP;
}

const hash = (i: number) => {
  const x = Math.sin(i * 12.9898 + 4.1414) * 43758.5453;
  return x - Math.floor(x);
};

function wave(
  from: Vector2,
  to: Vector2,
  phase: number,
  amp = 9,
  wavelength = 46,
): Vector2[] {
  const dir = to.sub(from);
  const len = dir.magnitude;
  const u = dir.normalized;
  const n = new Vector2(-u.y, u.x);
  const out: Vector2[] = [];
  const steps = 28;
  for (let i = 0; i <= steps; i++) {
    const d = (len * i) / steps;
    const taper = Math.min(1, (len - d) / 34, d / 20);
    const off =
      amp * taper * Math.sin(((d / wavelength) * 2 - phase * 2.2) * Math.PI);
    out.push(from.add(u.scale(d)).add(n.scale(off)));
  }
  return out;
}

export function HeatArrow(props: {
  from: [number, number];
  to: [number, number];
  phase: SimpleSignal<number>;
  color?: string;
  width?: number;
}) {
  const from = new Vector2(props.from);
  const to = new Vector2(props.to);
  return (
    <Line
      points={() => wave(from, to, props.phase())}
      stroke={props.color ?? C.heat}
      lineWidth={props.width ?? 7}
      lineCap={'round'}
      lineJoin={'round'}
      endArrow
      arrowSize={18}
    />
  );
}

function Chip(props: {
  title: string;
  text: string;
  color: string;
  tint: string;
  x: number;
  y: number;
  refFn?: (r: Rect) => void;
}) {
  return (
    <Rect
      ref={props.refFn}
      x={props.x}
      y={props.y}
      fill={props.tint}
      stroke={props.color}
      lineWidth={2.5}
      radius={14}
      padding={[8, 18]}
      layout
      direction={'column'}
      alignItems={'center'}
    >
      <Txt
        text={props.title}
        fontFamily={FONT}
        fontWeight={800}
        fontSize={20}
        letterSpacing={1}
        fill={props.color}
      />
      <Txt
        text={props.text}
        fontFamily={FONT}
        fontWeight={600}
        fontSize={22}
        fill={props.color}
      />
    </Rect>
  );
}

export function Label(props: {
  n: number;
  text: string;
  color: string;
  x: number;
  y: number;
  refFn?: (r: Node) => void;
}) {
  return (
    <Rect
      ref={props.refFn}
      x={props.x}
      y={props.y}
      layout
      alignItems={'center'}
      gap={12}
    >
      <Circle size={44} fill={props.color} layout justifyContent={'center'} alignItems={'center'}>
        <Txt
          text={`${props.n}`}
          fontFamily={FONT}
          fontWeight={800}
          fontSize={26}
          fill={'#fff'}
        />
      </Circle>
      <Txt
        text={props.text}
        fontFamily={FONT}
        fontWeight={800}
        fontSize={30}
        fill={C.ink}
      />
    </Rect>
  );
}

export interface Cycle {
  root: Node;
  pipes: Node;
  particles: Node;
  cabinet: Rect;
  evapFrame: Rect;
  compressor: Node;
  condFrame: Rect;
  fan: Node;
  valve: Node;
  heatIn: Node;
  heatOut: Node;
  workBolt: Node;
  chips: Rect[];
  labels: Node[];
  flowIcon: Node;
  /** Refrigerant flow speed (mass units per second). */
  speed: SimpleSignal<number>;
  fanSpeed: SimpleSignal<number>;
  heatPhase: SimpleSignal<number>;
  /** Highlight a part of the loop: 0 = none, 1 = evaporator ... 4 = valve. */
  run(): ThreadGenerator;
  focus(
    local: [number, number],
    scale: number,
    screen: [number, number],
    time?: number,
  ): ThreadGenerator;
}

export interface CycleOptions {
  /** Initial root scale / position. */
  scale?: number;
  x?: number;
  y?: number;
  particles?: number;
}

export function createCycle(parent: Node, opts: CycleOptions = {}): Cycle {
  const root = createRef<Node>();
  const pipes = createRef<Node>();
  const particles = createRef<Node>();
  const cabinet = createRef<Rect>();
  const evapFrame = createRef<Rect>();
  const compressor = createRef<Node>();
  const condFrame = createRef<Rect>();
  const fan = createRef<Node>();
  const fanBlades = createRef<Node>();
  const valve = createRef<Node>();
  const heatIn = createRef<Node>();
  const heatOut = createRef<Node>();
  const workBolt = createRef<Node>();
  const flowIcon = createRef<Node>();
  const chips: Rect[] = [];
  const labels: Node[] = [];

  const phase = createSignal(0);
  const speed = createSignal(0);
  const fanSpeed = createSignal(0);
  const heatPhase = createSignal(0);
  const fanAngle = createSignal(0);

  const lowPts = LOOP.pts.slice(0, LOOP.compIndex + 1).map(p => new Vector2(p));
  const highPts = LOOP.pts.slice(LOOP.compIndex).map(p => new Vector2(p));

  const N = opts.particles ?? 150;
  const dots = [];
  for (let i = 0; i < N; i++) {
    const h = hash(i);
    const s = () => sFromMass((i / N) * TOTAL_MASS + phase());
    const isGas = () => h < stateAt(s()).quality;
    dots.push(
      <Circle
        position={() => pointAt(s())}
        size={() => (isGas() ? 12 : 11)}
        fill={() => (isGas() ? colorAt(s()).alpha(0.3) : colorAt(s()))}
        stroke={() => colorAt(s())}
        lineWidth={() => (isGas() ? 2.5 : 0)}
      />,
    );
  }

  parent.add(
    <Node ref={root} scale={opts.scale ?? 0.8} x={opts.x ?? -60} y={opts.y ?? 10}>
      {/* Cabinet = the inside of the fridge */}
      <Rect
        ref={cabinet}
        x={-600}
        y={0}
        size={[420, 440]}
        radius={26}
        fill={C.coldTint}
        stroke={'#9cc3ec'}
        lineWidth={4}
      >
        <Txt
          x={-188}
          y={-192}
          anchor={[-1, 0]}
          text={'INSIDE THE FRIDGE'}
          fontFamily={FONT}
          fontWeight={800}
          fontSize={22}
          letterSpacing={1}
          fill={C.cold}
        />
      </Rect>
      <Rect
        ref={evapFrame}
        x={-520}
        size={[244, 236]}
        radius={14}
        fill={'#ffffffaa'}
        stroke={'#b9d4f1'}
        lineWidth={3}
      />
      <Rect
        ref={condFrame}
        x={520}
        size={[232, 262]}
        radius={14}
        fill={C.hotTint}
        stroke={'#f0b4b4'}
        lineWidth={3}
      />
      {/* Fan */}
      <Node ref={fan} position={LOC.fan}>
        <Circle size={176} fill={'#eef1f5'} stroke={'#8a94a6'} lineWidth={6} />
        <Node ref={fanBlades} rotation={() => fanAngle()}>
          {[0, 120, 240].map(a => (
            <Node rotation={a}>
              <Rect y={-40} size={[34, 72]} radius={17} fill={'#6f7888'} />
            </Node>
          ))}
        </Node>
        <Circle size={30} fill={'#3d4452'} />
        <Txt
          y={118}
          text={'FAN'}
          fontFamily={FONT}
          fontWeight={700}
          fontSize={20}
          fill={C.muted}
        />
      </Node>

      {/* Pipes: outer coloured wall + pale interior */}
      <Node ref={pipes}>
        <Line points={lowPts} stroke={'#7fb2e5'} lineWidth={24} lineJoin={'round'} lineCap={'round'} />
        <Line points={highPts} stroke={'#ee8f8f'} lineWidth={24} lineJoin={'round'} lineCap={'round'} />
        <Line points={lowPts} stroke={'#f3f8fe'} lineWidth={15} lineJoin={'round'} lineCap={'round'} />
        <Line points={highPts} stroke={'#fff6f4'} lineWidth={15} lineJoin={'round'} lineCap={'round'} />
      </Node>

      <Node ref={particles}>{dots}</Node>

      {/* Compressor */}
      <Node ref={compressor} position={LOC.compressor}>
        <Rect y={92} size={[200, 18]} radius={6} fill={'#1d2128'} />
        <Rect y={-2} size={[156, 176]} radius={[64, 64, 22, 22]} fill={C.metal} />
        <Rect x={-46} y={-8} size={[22, 120]} radius={11} fill={'#ffffff22'} />
        <Rect x={92} y={-6} size={[30, 58]} radius={6} fill={C.metalLight} />
        <Node ref={workBolt} y={6}>
          <Line
            points={[
              [10, -42],
              [-16, 6],
              [4, 6],
              [-8, 42],
              [22, -8],
              [2, -8],
              [10, -42],
            ]}
            closed
            fill={C.work}
            stroke={'#8a6a00'}
            lineWidth={2}
          />
        </Node>
      </Node>

      {/* Expansion valve */}
      <Node ref={valve} position={LOC.valve}>
        <Rect x={-42} size={[16, 52]} radius={4} fill={C.brassDark} />
        <Rect x={42} size={[16, 52]} radius={4} fill={C.brassDark} />
        <Rect size={[76, 42]} radius={10} fill={C.brass} stroke={C.brassDark} lineWidth={3} />
        <Rect y={-32} size={[34, 26]} radius={6} fill={C.brass} stroke={C.brassDark} lineWidth={3} />
        <Rect y={-50} size={[48, 12]} radius={4} fill={C.brassDark} />
      </Node>

      {/* Heat flows */}
      <Node ref={heatIn} opacity={0}>
        {[-70, 0, 70].map(y => (
          <HeatArrow from={[-790, y]} to={[-652, y]} phase={heatPhase} />
        ))}
        <Txt
          x={-724}
          y={132}
          text={'HEAT IN'}
          fontFamily={FONT}
          fontWeight={800}
          fontSize={24}
          fill={C.heat}
        />
      </Node>
      <Node ref={heatOut} opacity={0}>
        {[-70, 0, 70].map(y => (
          <HeatArrow from={[836, y]} to={[964, y]} phase={heatPhase} />
        ))}
        <Txt
          x={900}
          y={132}
          text={'HEAT OUT'}
          fontFamily={FONT}
          fontWeight={800}
          fontSize={24}
          fill={C.heat}
        />
        <Txt
          x={900}
          y={166}
          text={'to the room'}
          fontFamily={FONT}
          fontWeight={600}
          fontSize={20}
          fill={C.heat}
        />
      </Node>

      {/* Flow-direction icon */}
      <Node ref={flowIcon} y={0} opacity={0}>
        <Circle
          size={110}
          startAngle={-50}
          endAngle={140}
          stroke={C.ink}
          lineWidth={6}
          endArrow
          arrowSize={16}
        />
        <Circle
          size={110}
          startAngle={130}
          endAngle={320}
          stroke={C.ink}
          lineWidth={6}
          endArrow
          arrowSize={16}
        />
        <Txt
          y={98}
          text={'REFRIGERANT FLOW'}
          fontFamily={FONT}
          fontWeight={800}
          fontSize={22}
          fill={C.ink}
        />
        <Txt
          y={126}
          text={'(clockwise, sealed loop)'}
          fontFamily={FONT}
          fontWeight={600}
          fontSize={19}
          fill={C.muted}
        />
      </Node>

      <Chip
        x={-260}
        y={-192}
        title={'LOW PRESSURE'}
        text={'cool gas'}
        color={C.cold}
        tint={C.coldTint}
        refFn={r => (chips[0] = r)}
      />
      <Chip
        x={260}
        y={-192}
        title={'HIGH PRESSURE'}
        text={'hot gas'}
        color={C.hot}
        tint={C.hotTint}
        refFn={r => (chips[1] = r)}
      />
      <Chip
        x={260}
        y={176}
        title={'HIGH PRESSURE'}
        text={'warm liquid'}
        color={'#c2410c'}
        tint={'#fff1e6'}
        refFn={r => (chips[2] = r)}
      />
      <Chip
        x={-260}
        y={176}
        title={'LOW PRESSURE'}
        text={'very cold liquid + vapour'}
        color={C.cold}
        tint={C.coldTint}
        refFn={r => (chips[3] = r)}
      />

      <Label n={1} text={'EVAPORATOR'} color={C.cold} x={-660} y={-305} refFn={r => (labels[0] = r)} />
      <Label n={2} text={'COMPRESSOR'} color={C.hot} x={0} y={-395} refFn={r => (labels[1] = r)} />
      <Label n={3} text={'CONDENSER'} color={C.hot} x={660} y={-305} refFn={r => (labels[2] = r)} />
      <Label n={4} text={'EXPANSION VALVE'} color={C.valve} x={0} y={318} refFn={r => (labels[3] = r)} />
    </Node>,
  );

  // chips sit on top of particles/pipes but are not part of the loop path
  return {
    root: root(),
    pipes: pipes(),
    particles: particles(),
    cabinet: cabinet(),
    evapFrame: evapFrame(),
    compressor: compressor(),
    condFrame: condFrame(),
    fan: fan(),
    valve: valve(),
    heatIn: heatIn(),
    heatOut: heatOut(),
    workBolt: workBolt(),
    chips,
    labels,
    flowIcon: flowIcon(),
    speed,
    fanSpeed,
    heatPhase,
    *run() {
      while (true) {
        const dt = usePlayback().deltaTime;
        phase(phase() + speed() * dt);
        fanAngle(fanAngle() + fanSpeed() * dt);
        heatPhase(heatPhase() + dt);
        yield;
      }
    },
    *focus(local, scale, screen, time = 1.2) {
      const pos = new Vector2(screen).sub(new Vector2(local).scale(scale));
      yield* all(
        root().scale(scale, time, easeInOutCubic),
        root().position(pos, time, easeInOutCubic),
      );
    },
  };
}

/** Hide every part of the diagram (for building it up piece by piece). */
export function hideAll(c: Cycle) {
  for (const n of [
    c.cabinet,
    c.evapFrame,
    c.compressor,
    c.condFrame,
    c.fan,
    c.valve,
    c.pipes,
    c.particles,
    c.flowIcon,
    ...c.chips,
    ...c.labels,
  ]) {
    n.opacity(0);
  }
}
