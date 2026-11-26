import {Circle, Gradient, Line, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  all,
  createRef,
  createSignal,
  easeInOutCubic,
  easeOutCubic,
  easeOutExpo,
  sequence,
  waitFor,
} from '@canvas-commons/core';
import {Chip, SourceTag, openScene, popIn, rng, sfx, slotLog, withSfx} from '../kit';
import {FONT, MONO, V} from '../theme';

const PW = 760;
const PH = 428;

function Subject(props: {x?: number; opacity?: number; stroke?: string}) {
  const fill = '#04060a';
  const s = props.stroke ?? V.cyan;
  return (
    <Node x={props.x ?? 0} y={40} opacity={props.opacity ?? 1}>
      <Rect x={-58} y={120} width={44} height={170} radius={20} fill={fill} stroke={s} lineWidth={3} rotation={8} />
      <Rect x={58} y={120} width={44} height={170} radius={20} fill={fill} stroke={s} lineWidth={3} rotation={-14} />
      <Rect x={-98} y={-40} width={38} height={150} radius={18} fill={fill} stroke={s} lineWidth={3} rotation={28} />
      <Rect x={100} y={-70} width={38} height={150} radius={18} fill={fill} stroke={s} lineWidth={3} rotation={-48} />
      <Rect y={-10} width={150} height={190} radius={50} fill={fill} stroke={s} lineWidth={3} />
      <Circle y={-150} size={84} fill={fill} stroke={s} lineWidth={3} />
    </Node>
  );
}

export default makeScene2D(function* (view) {
  const nar = yield* openScene(view, 's09_anatomy', V.amber);

  const gap = createSignal(92);
  const rot = createSignal(-28);
  const sy = createSignal(0.55);
  const camX = createSignal(0);
  const labX = createSignal(1);
  const stack = createRef<Node>();
  const layers = [0, 1, 2, 3, 4].map(() => createRef<Node>());
  const planes = [0, 1, 2, 3, 4].map(() => createRef<Rect>());
  const labels = [0, 1, 2, 3, 4].map(() => createRef<Node>());
  const names = ['FOOTAGE · UPSCALED + GRADED', 'TYPOGRAPHY', 'SUBJECT · MASK / ROTO', 'LIGHT', 'PARTICLES · GRAIN'];
  const lc = [V.muted, V.amber, V.cyan, V.ink, V.violet];
  const depth = [0.15, 0.35, 0.6, 0.8, 1.0];
  const r = rng(99);
  const parts = Array.from({length: 46}, () => ({x: r() * PW - PW / 2, y: r() * PH - PH / 2, s: 3 + r() * 7}));

  const contents = [
    // 0 footage
    <Node>
      <Rect
        size={[PW, PH]}
        fill={
          new Gradient({
            type: 'linear',
            from: [0, -PH / 2],
            to: [0, PH / 2],
            stops: [
              {offset: 0, color: '#0f3550'},
              {offset: 0.6, color: '#0a1726'},
              {offset: 1, color: '#183a24'},
            ],
          })
        }
      />
      {[-260, -90, 90, 260].map(x => (
        <Circle x={x} y={-150} size={60} fill={'#ffffff40'} />
      ))}
      <Txt y={150} text={'FOOTAGE SLOT A01'} fontFamily={MONO} fontWeight={700} fontSize={18} letterSpacing={3} fill={V.inkDim + '88'} />
    </Node>,
    // 1 typography
    <Txt y={-20} text={'LEGEND'} fontFamily={FONT} fontWeight={900} fontSize={168} letterSpacing={4} fill={V.amber} />,
    // 2 subject
    <Subject />,
    // 3 light
    <Node>
      <Circle
        x={150}
        y={-130}
        size={460}
        fill={
          new Gradient({
            type: 'radial',
            fromRadius: 0,
            toRadius: 230,
            stops: [
              {offset: 0, color: '#ffffffaa'},
              {offset: 0.25, color: '#ffd28a55'},
              {offset: 1, color: '#ffd28a00'},
            ],
          })
        }
      />
      <Rect x={150} y={-130} width={720} height={6} radius={3} fill={'#ffffffaa'} rotation={-8} />
    </Node>,
    // 4 particles
    <Node>
      {parts.map(p => (
        <Circle x={p.x} y={p.y} size={p.s} fill={'#fff'} opacity={0.6} />
      ))}
    </Node>,
  ];

  view.add(
    <Node ref={stack} y={-90}>
      {contents.map((c, i) => (
        <Node ref={layers[i]} y={() => (2 - i) * gap()} x={() => camX() * depth[i] * 140} opacity={0}>
          <Node scaleY={() => sy()}>
            <Node rotation={() => rot()}>
              <Rect ref={planes[i]} size={[PW, PH]} radius={4} clip fill={i === 0 ? V.panel : '#ffffff06'} stroke={lc[i] + 'aa'} lineWidth={2.5}>
                {c}
              </Rect>
            </Node>
          </Node>
          <Node ref={labels[i]} x={() => 560 * labX()} y={0}>
            <Line points={[[-150, 0], [-30, 0]]} stroke={lc[i]} lineWidth={2} lineDash={[5, 5]} />
            <Txt x={-20} anchor={[-1, 0]} text={names[i]} fontFamily={MONO} fontWeight={700} fontSize={22} letterSpacing={3} fill={lc[i]} />
          </Node>
        </Node>
      ))}
    </Node>,
  );
  slotLog('A01', 'Optional: replace the generic footage plate with a neutral, licensed sports or film still');

  /* ---------- line 0 ---------- */
  const t0 = createRef<Txt>();
  view.add(<Txt ref={t0} y={-440} text={'A GENERIC HIGH-DENSITY COMPOSITION'} fontFamily={MONO} fontWeight={700} fontSize={24} letterSpacing={6} fill={V.muted} opacity={0} />);
  yield* t0().opacity(1, 0.6);
  const ghost = createRef<Rect>();
  view.add(
    <Node y={-90}>
      <Node scaleY={0.55}>
        <Node rotation={-28}>
          <Rect ref={ghost} size={[PW, PH]} stroke={V.ink + '55'} lineWidth={2} lineDash={[12, 10]} opacity={0} />
        </Node>
      </Node>
    </Node>,
  );
  yield* ghost().opacity(1, 0.8);

  /* ---------- line 1 ---------- */
  yield* nar.at(1);
  const note = createRef<Node>();
  view.add(
    <Node ref={note} x={-640} y={-330} opacity={0}>
      <SourceTag text={'BUILT FOR THIS FILM · NOT FROM ANY CREATOR'} color={V.inkDim} />
    </Node>,
  );
  yield* note().opacity(1, 0.5);

  const reveal = function* (i: number) {
    sfx('pop');
    yield* all(layers[i]().opacity(1, 0.6), layers[i]().scale(0.9).scale(1, 0.8, easeOutExpo));
  };

  /* ---------- line 2: footage ---------- */
  yield* nar.at(2);
  yield* all(ghost().opacity(0, 0.5), reveal(0));

  /* ---------- line 3: subject ---------- */
  yield* nar.at(3);
  yield* reveal(2);
  // mask outline tracing
  const mask = createRef<Line>();
  const subjPlane = planes[2]();
  subjPlane.add(
    <Line
      ref={mask}
      y={40}
      points={[[-60, -205], [60, -205], [80, -110], [170, -150], [175, -110], [80, 10], [100, 210], [60, 215], [0, 80], [-55, 215], [-100, 210], [-80, 10], [-160, 20], [-160, -20], [-75, -100]]}
      closed
      stroke={V.cyan}
      lineWidth={3}
      lineDash={[10, 8]}
      end={0}
    />,
  );
  sfx('riser', 1.6);
  yield* mask().end(1, 1.6, easeInOutCubic);

  /* ---------- line 4: typography behind the subject ---------- */
  yield* nar.at(4);
  yield* reveal(1);
  yield* mask().opacity(0, 0.5);

  /* ---------- line 5: camera & parallax ---------- */
  yield* nar.at(5);
  const camIcon = createRef<Node>();
  view.add(
    <Node ref={camIcon} x={-760} y={-110} opacity={0}>
      <Rect width={110} height={74} radius={12} fill={V.panel2} stroke={V.ink} lineWidth={3} />
      <Line points={[[55, -22], [100, -40], [100, 40], [55, 22]]} closed fill={V.panel2} stroke={V.ink} lineWidth={3} />
      <Txt y={70} text={'3D CAMERA'} fontFamily={MONO} fontWeight={700} fontSize={18} letterSpacing={3} fill={V.ink} />
    </Node>,
  );
  yield* camIcon().opacity(1, 0.4);
  sfx('whoosh');
  yield* all(camX(-1, 1.6, easeInOutCubic), camIcon().y(-170, 1.6, easeInOutCubic));
  sfx('whoosh');
  yield* all(camX(1, 2.2, easeInOutCubic), camIcon().y(-50, 2.2, easeInOutCubic));
  yield* camX(0, 1.4, easeInOutCubic);

  /* ---------- line 6: light ---------- */
  yield* nar.at(6);
  yield* all(reveal(3), camIcon().opacity(0, 0.5));

  /* ---------- line 7: particles ---------- */
  yield* nar.at(7);
  yield* reveal(4);

  /* ---------- line 8: motion blur + velocity ---------- */
  yield* nar.at(8);
  const trail = createRef<Node>();
  planes[2]().add(
    <Node ref={trail} opacity={0}>
      {[1, 2, 3, 4].map(k => (
        <Subject x={-k * 26} opacity={0.22 - k * 0.04} stroke={V.cyan + '55'} />
      ))}
    </Node>,
  );
  const velo = createRef<Node>();
  view.add(
    <Node ref={velo} x={-700} y={170} opacity={0}>
      <Rect width={300} height={130} radius={14} fill={V.panel + 'ee'} stroke={V.line} lineWidth={2} />
      <Line points={Array.from({length: 40}, (_, i) => {
        const t = i / 39;
        const v = t < 0.5 ? 0.25 : Math.min(1, 0.25 + Math.pow((t - 0.5) / 0.3, 3));
        return [-120 + t * 240, 40 - v * 80] as [number, number];
      })} stroke={V.magenta} lineWidth={4} />
      <Txt y={-80} text={'VELOCITY'} fontFamily={MONO} fontWeight={700} fontSize={18} letterSpacing={3} fill={V.magenta} />
    </Node>,
  );
  sfx('whoosh');
  yield* all(trail().opacity(1, 0.6), popIn(velo(), 0.5, 20));

  /* ---------- line 9: collapse ---------- */
  yield* nar.at(9);
  sfx('whooshBig');
  yield* all(
    gap(0, 1.4, easeInOutCubic),
    rot(0, 1.4, easeInOutCubic),
    sy(1, 1.4, easeInOutCubic),
    labX(1.6, 1.0, easeInOutCubic),
    ...labels.map(l => l().opacity(0, 0.8)),
    ...planes.map((p, i) => (i > 0 ? all(p().stroke("#00000000", 1.2), p().fill("#00000000", 1.2)) : p().stroke(V.line, 1.2))),
    velo().opacity(0, 0.6),
    note().opacity(0, 0.6),
    t0().opacity(0, 0.6),
  );
  sfx('impact');
  yield* all(stack().scale(1.18, 3, easeInOutCubic), camX(0.8, 3, easeInOutCubic));

  /* ---------- line 10-11: a new image; the skills ---------- */
  yield* nar.at(10);
  yield* all(stack().scale(0.82, 1.2, easeInOutCubic), stack().x(-420, 1.2, easeInOutCubic), camX(0, 1.2));
  const skills = ['COMPOSITING', 'MASKING / ROTO', '3D', 'TYPOGRAPHY', 'TIMING'];
  const sk = createRef<Node>();
  view.add(
    <Node ref={sk} x={560} y={-110}>
      <Txt y={-260} text={'BUILDING IMAGES,\nNOT ONLY CUTTING THEM'} textAlign={'center'} fontFamily={FONT} fontWeight={900} fontSize={46} lineHeight={54} fill={V.ink} opacity={0} />
      {skills.map((s, i) => (
        <Node y={-120 + i * 78} opacity={0}>
          <Chip text={s} color={[V.cyan, V.amber, V.violet, V.magenta, V.green][i]} size={26} />
        </Node>
      ))}
    </Node>,
  );
  yield* popIn(sk().children()[0], 0.6, 20);
  yield* nar.at(11);
  yield* sequence(0.25, ...sk().children().slice(1).map(n => withSfx('tick', popIn(n, 0.4, 16))));
  yield* nar.end();
  yield* all(sk().opacity(0, 0.6), stack().opacity(0, 0.6), stack().scale(0.7, 0.6));
});
