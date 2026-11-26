import {Line, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
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
import {Chip, FootageSlot, openScene, popIn, refs, sfx, slotLog, withSfx} from '../kit';
import {FONT, MONO, V} from '../theme';

type Profile = {
  name: string;
  handle: string;
  color: string;
  niche: string[];
  tools: string[];
  src: string;
  slot: string;
  stat?: {value: number; label: string; note: string; src: string};
  note?: string;
};

const PROFILES: Profile[] = [
  {
    name: 'BROXEDITZ',
    handle: '"That One Football Editor"',
    color: V.cyan,
    niche: ['FOOTBALL'],
    tools: ['AFTER EFFECTS', 'TOPAZ AI'],
    src: refs('yt-broxeditz'),
    slot: 'BroxEditZ — one representative Short (credited, short excerpt)',
    stat: {value: 2.78, label: 'M SUBSCRIBERS', note: 'vidIQ · data updated 27 Apr 2025 · joined 21 Jun 2022', src: refs('vidiq-broxeditz')},
  },
  {
    name: 'SLICX7',
    handle: '@slicx7',
    color: V.red,
    niche: ['FOOTBALL'],
    tools: ['AFTER EFFECTS', 'TOPAZ'],
    src: refs('yt-slicx7'),
    slot: 'Slicx7 — one representative Short (credited, short excerpt)',
    stat: {value: 1.52, label: 'M SUBSCRIBERS', note: 'vidIQ · data updated 12 Feb 2025 · created 2016', src: refs('vidiq-slicx7')},
  },
  {
    name: '10MOV',
    handle: '@10Mov_Edits',
    color: V.green,
    niche: ['FOOTBALL', 'MESSI', 'NEYMAR'],
    tools: ['AFTER EFFECTS', 'TOPAZ VIDEO AI'],
    src: refs('yt-10mov', 'tiktok-10mov'),
    slot: '10Mov — one representative edit (credited, short excerpt)',
    note: 'No reliable public subscriber figure found in this research.',
  },
  {
    name: 'HEISTY',
    handle: '@heisty710',
    color: V.amber,
    niche: ['MOVIES', 'SHOWS', 'ANIME', 'NOSTALGIA'],
    tools: ['AFTER EFFECTS', 'TOPAZ', 'ALIGHT MOTION'],
    src: refs('yt-heisty', 'patreon-heisty'),
    slot: 'Heisty — one representative edit (credited, short excerpt)',
    note: 'The only YouTube figure found is an estimate. See Chapter 09.',
  },
  {
    name: 'EAGLE STAN',
    handle: '@Eagle_Stan16',
    color: V.magenta,
    niche: ['FILM & TV FANDOM', 'PHONK'],
    tools: ['NOT STATED IN SOURCES FOUND'],
    src: refs('yt-eaglestan'),
    slot: 'Eagle Stan — one representative montage (credited, short excerpt)',
    stat: {value: 173, label: 'K SUBSCRIBERS', note: 'channel page in a search snapshot · undated', src: refs('yt-eaglestan')},
  },
  {
    name: 'FICTIC',
    handle: 'FicTic_Editz · Fictic Edits · Mini FicTic …',
    color: V.violet,
    niche: ['WHICH CHANNEL?'],
    tools: ['VARIES BY CHANNEL'],
    src: refs('yt-fictic-editz', 'yt-fictic-edits', 'yt-minifictic'),
    slot: 'Fictic — confirm the exact channel before inserting footage',
    note: 'Several channels use this name. Confirm the intended channel first.',
  },
];

function ProfileCard(props: {p: Profile; i: number; refFn: (n: Node) => void; value: () => number}) {
  const p = props.p;
  return (
    <Node ref={props.refFn} y={-110} opacity={0}>
      <Rect width={1480} height={620} radius={24} fill={V.panel + 'f2'} stroke={p.color + '88'} lineWidth={2} shadowColor={'#000000a0'} shadowBlur={50} shadowOffsetY={20} />
      <FootageSlot id={`C0${props.i + 1}`} desc={p.slot} w={300} h={540} x={-540} accent={p.color} small />
      <Node x={-330}>
        <Txt y={-220} anchor={[-1, 0]} text={p.name} fontFamily={FONT} fontWeight={900} fontSize={96} letterSpacing={3} fill={V.ink} />
        <Txt y={-140} anchor={[-1, 0]} text={p.handle} fontFamily={MONO} fontSize={26} fill={p.color} />
        <Txt y={-80} anchor={[-1, 0]} text={'NICHE'} fontFamily={MONO} fontWeight={700} fontSize={18} letterSpacing={4} fill={V.muted} />
        <Rect y={-36} anchor={[-1, 0]} layout gap={12}>
          {p.niche.map(n => (
            <Chip text={n} color={p.color} />
          ))}
        </Rect>
        <Txt y={20} anchor={[-1, 0]} text={'TOOLS NAMED BY THE CHANNEL'} fontFamily={MONO} fontWeight={700} fontSize={18} letterSpacing={4} fill={V.muted} />
        <Rect y={64} anchor={[-1, 0]} layout gap={12}>
          {p.tools.map(n => (
            <Chip text={n} color={V.inkDim} />
          ))}
        </Rect>
        <Rect y={200} x={0} anchor={[-1, 0]} width={900} height={150} radius={16} fill={V.bg + 'aa'} stroke={V.line} lineWidth={2}>
          {p.stat ? (
            <Node opacity={() => (props.value() > 0 ? 1 : 0)}>
              <Txt x={-420} y={-26} anchor={[-1, 0]} text={() => (p.stat!.value < 10 ? props.value().toFixed(2) : Math.round(props.value()).toString()) + p.stat!.label.slice(0, 1)} fontFamily={FONT} fontWeight={900} fontSize={64} fill={V.ink} />
              <Txt x={-130} y={-36} anchor={[-1, 0]} text={p.stat.label.slice(2)} fontFamily={MONO} fontWeight={700} fontSize={22} letterSpacing={4} fill={p.color} />
              <Txt x={-130} y={-6} anchor={[-1, 0]} text={'THIRD-PARTY SNAPSHOT'} fontFamily={MONO} fontSize={16} letterSpacing={3} fill={V.muted} />
              <Txt x={-420} y={44} anchor={[-1, 0]} text={p.stat.note + '  ' + p.stat.src} fontFamily={MONO} fontSize={18} fill={V.muted} />
            </Node>
          ) : (
            <Txt x={-420} anchor={[-1, 0]} width={840} textWrap text={p.note!} fontFamily={FONT} fontWeight={600} fontSize={30} fill={V.inkDim} />
          )}
        </Rect>
        <Txt y={292} anchor={[-1, 0]} text={'CHANNEL DESCRIPTION SOURCE ' + p.src} fontFamily={MONO} fontSize={16} letterSpacing={2} fill={V.muted} />
      </Node>
    </Node>
  );
}

export default makeScene2D(function* (view) {
  const nar = yield* openScene(view, 's08_creators', V.cyan);

  /* line 0 */
  const six = createRef<Txt>();
  view.add(<Txt ref={six} y={-110} text={'SIX CHANNELS'} fontFamily={FONT} fontWeight={900} fontSize={150} letterSpacing={8} fill={V.ink} opacity={0} />);
  yield* all(six().opacity(1, 0.4), six().scale(1.2).scale(1, 0.7, easeOutExpo));
  yield* waitFor(1.6);
  yield* six().opacity(0, 0.4);

  const cards = PROFILES.map(() => createRef<Node>());
  const vals = PROFILES.map(() => createSignal(0));
  PROFILES.forEach((p, i) => {
    view.add(<ProfileCard p={p} i={i} refFn={cards[i]} value={() => vals[i]()} />);
    slotLog(`C0${i + 1}`, p.slot);
  });

  // line index at which each card appears, and whether a second line animates its stat
  const order = [
    {card: 0, line: 1, statLine: 2},
    {card: 1, line: 3, statLine: 4},
    {card: 2, line: 5},
    {card: 3, line: 6},
    {card: 4, line: 7},
    {card: 5, line: 8},
  ];
  let prev: Node | null = null;
  for (const o of order) {
    yield* nar.at(o.line);
    const n = cards[o.card]();
    if (prev) {
      sfx('whoosh');
      const pv = prev;
      yield* all(pv.x(-700, 0.55, easeInOutCubic), pv.opacity(0, 0.55));
      pv.remove();
    }
    n.x(700);
    yield* all(n.x(0, 0.7, easeOutExpo), n.opacity(1, 0.5));
    const p = PROFILES[o.card];
    if (p.stat) {
      if (o.statLine) yield* nar.at(o.statLine);
      else yield* waitFor(0.6);
      sfx('count', 1.4);
      yield* vals[o.card](p.stat.value, 1.4, easeOutCubic);
    }
    prev = n;
  }

  /* ---------- line 9-10: matrix ---------- */
  yield* nar.at(9);
  sfx('whoosh');
  yield* all(prev!.opacity(0, 0.5), prev!.scale(0.9, 0.5));
  const cols = ['FOOTBALL', 'AFTER EFFECTS', 'TOPAZ', 'ALIGHT MOTION'];
  // 1 = stated by the channel or its description, 0 = not established by sources found
  const M = [
    ['BROXEDITZ', 1, 1, 1, 0],
    ['SLICX7', 1, 1, 1, 0],
    ['10MOV', 1, 1, 1, 0],
    ['HEISTY', 0, 1, 1, 1],
    ['EAGLE STAN', 0, 0, 0, 0],
    ['FICTIC', 0, 0, 0, 0],
  ];
  const mx = createRef<Node>();
  const cellRefs: Rect[][] = [];
  view.add(
    <Node ref={mx} y={-120} opacity={0}>
      {cols.map((c, j) => (
        <Txt x={-170 + j * 250} y={-290} text={c} fontFamily={MONO} fontWeight={700} fontSize={20} letterSpacing={3} fill={V.muted} />
      ))}
      {M.map((row, i) => (
        <Node y={-210 + i * 82}>
          <Txt x={-650} anchor={[-1, 0]} text={row[0] as string} fontFamily={FONT} fontWeight={800} fontSize={36} fill={V.ink} />
          {[1, 2, 3, 4].map(j => (
            <Rect
              ref={(r: Rect) => {
                (cellRefs[i] ??= [])[j - 1] = r;
              }}
              x={-170 + (j - 1) * 250}
              width={200}
              height={62}
              radius={10}
              fill={row[j] ? V.green + '22' : V.panel}
              stroke={row[j] ? V.green : V.line}
              lineWidth={2}
            >
              <Txt text={row[j] ? '●' : '?'} fontFamily={FONT} fontWeight={800} fontSize={30} fill={row[j] ? V.green : V.faint} />
            </Rect>
          ))}
        </Node>
      ))}
      <Txt y={290} text={'●  stated by the channel or its description      ?  not established by the sources found'} fontFamily={MONO} fontSize={19} fill={V.muted} />
    </Node>,
  );
  yield* withSfx('blip', popIn(mx(), 0.6, 30));
  // highlight football column
  yield* waitFor(0.8);
  const hl = createRef<Rect>();
  mx().add(<Rect ref={hl} x={-170} y={-210 + 2.5 * 82} width={230} height={6 * 82 + 20} radius={14} stroke={V.amber} lineWidth={4} opacity={0} />);
  sfx('tick');
  yield* hl().opacity(1, 0.4);

  yield* nar.at(10);
  sfx('tick');
  yield* hl().x(-170 + 2 * 250, 0.7, easeInOutCubic);

  /* ---------- line 11: shared workflow (hypothesis) ---------- */
  yield* nar.at(11);
  yield* all(mx().opacity(0, 0.5), mx().y(-160, 0.5));
  const flow = createRef<Node>();
  const steps = ['SOURCE CLIP', 'AI UPSCALE', 'COMPOSITE', 'FINAL EDIT'];
  const sc = [V.muted, V.green, V.cyan, V.magenta];
  view.add(
    <Node ref={flow} y={-120}>
      {steps.map((s, i) => (
        <Node x={-630 + i * 420} opacity={0}>
          <Rect width={330} height={150} radius={18} fill={V.panel + 'ee'} stroke={sc[i]} lineWidth={2.5} />
          <Txt text={s} fontFamily={MONO} fontWeight={700} fontSize={26} letterSpacing={3} fill={sc[i]} />
        </Node>
      ))}
      {[0, 1, 2].map(i => (
        <Line points={[[-630 + i * 420 + 175, 0], [-630 + (i + 1) * 420 - 175, 0]]} stroke={V.inkDim} lineWidth={3} endArrow arrowSize={14} end={0} />
      ))}
      <Txt y={150} text={'HYPOTHESIS · inferred from the tools channels name, not observed in their project files'} fontFamily={MONO} fontSize={19} fill={V.amber} opacity={0} />
    </Node>,
  );
  const fc = flow().children();
  for (let i = 0; i < 4; i++) {
    yield* withSfx('tick', popIn(fc[i], 0.4, 20));
    if (i < 3) yield* (fc[4 + i] as Line).end(1, 0.35, easeOutCubic);
  }
  yield* fc[7].opacity(1, 0.5);
  yield* nar.end();
  yield* all(flow().opacity(0, 0.6));
});
