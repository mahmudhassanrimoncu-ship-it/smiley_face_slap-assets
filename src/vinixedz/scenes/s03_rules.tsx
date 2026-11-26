import {Circle, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  all,
  createRef,
  easeInOutCubic,
  easeOutBack,
  easeOutExpo,
  sequence,
  waitFor,
} from '@canvas-commons/core';
import {FootageSlot, openScene, popIn, sfx, slotLog, withSfx} from '../kit';
import {FONT, MONO, TAG_COLOR, Tag, V} from '../theme';

const CREATORS = [
  {name: 'HEISTY', handle: '@heisty710', c: V.amber},
  {name: 'FICTIC', handle: 'several channels share this name', c: V.violet},
  {name: 'EAGLE STAN', handle: '@Eagle_Stan16', c: V.magenta},
  {name: '10MOV', handle: '@10Mov_Edits', c: V.green},
  {name: 'BROXEDITZ', handle: 'channel UCbH8ThM…', c: V.cyan},
  {name: 'SLICX7', handle: '@slicx7', c: V.red},
];

export default makeScene2D(function* (view) {
  const nar = yield* openScene(view, 's03_rules', V.cyan);

  /* ---------- line 0-1: genre mosaic ---------- */
  const genres = ['FOOTBALL', 'FILM', 'ANIME', 'NOSTALGIA'];
  const gcol = [V.green, V.amber, V.magenta, V.violet];
  const mosaic = createRef<Node>();
  view.add(
    <Node ref={mosaic} y={-110}>
      {genres.map((g, i) => (
        <Node x={-570 + i * 380} opacity={0}>
          <FootageSlot
            id={`G0${i + 1}`}
            desc={`Representative ${g.toLowerCase()} fan edit`}
            w={300}
            h={480}
            accent={gcol[i]}
            small
          />
          <Txt
            y={290}
            text={g}
            fontFamily={MONO}
            fontWeight={700}
            fontSize={26}
            letterSpacing={6}
            fill={gcol[i]}
          />
        </Node>
      ))}
    </Node>,
  );
  slotLog('G01-G04', 'One representative fan edit each: football, film, anime, nostalgia (vertical)');
  yield* sequence(0.15, ...mosaic().children().map(n => popIn(n, 0.6, 60)));
  yield mosaic().x(-40, 12, easeInOutCubic);

  yield* nar.at(1);
  for (const n of mosaic().children()) {
    sfx('tick');
    yield* all(n.scale(1.06, 0.25), waitFor(0.6));
    yield* n.scale(1, 0.3);
  }

  /* ---------- line 2: six channels ---------- */
  yield* nar.at(2);
  sfx('whoosh');
  yield* all(mosaic().opacity(0, 0.5), mosaic().y(-160, 0.5));
  mosaic().remove();
  const grid = createRef<Node>();
  const header = createRef<Txt>();
  view.add(
    <Txt
      ref={header}
      y={-430}
      text={'SIX CHANNELS · SUGGESTED BY THE VINIXEDZ COMMUNITY'}
      fontFamily={MONO}
      fontWeight={700}
      fontSize={24}
      letterSpacing={6}
      fill={V.muted}
      opacity={0}
    />,
  );
  view.add(
    <Node ref={grid} y={-120}>
      {CREATORS.map((c, i) => (
        <Rect
          x={-520 + (i % 3) * 520}
          y={-120 + Math.floor(i / 3) * 240}
          width={470}
          height={190}
          radius={18}
          fill={V.panel + 'f0'}
          stroke={c.c + '99'}
          lineWidth={2}
          opacity={0}
        >
          <Rect x={-225} width={10} height={190} fill={c.c} />
          <Txt
            y={-22}
            text={c.name}
            fontFamily={FONT}
            fontWeight={900}
            fontSize={54}
            letterSpacing={3}
            fill={V.ink}
          />
          <Txt y={38} text={c.handle} fontFamily={MONO} fontSize={20} fill={c.c} />
        </Rect>
      ))}
    </Node>,
  );
  yield* header().opacity(1, 0.5);
  yield* sequence(
    0.18,
    ...grid().children().map(n => withSfx('pop', popIn(n, 0.5, 40))),
  );

  /* ---------- line 3: not one movement ---------- */
  yield* nar.at(3);
  const offs = [
    [-40, -30, -4],
    [30, 40, 3],
    [-20, 50, 5],
    [50, -40, -3],
    [-30, 20, -5],
    [20, -50, 4],
  ];
  sfx('whoosh');
  yield* all(
    ...grid().children().map((n, i) =>
      all(
        n.x(n.x() + offs[i][0] * 1.4, 1.2, easeInOutCubic),
        n.y(n.y() + offs[i][1] * 1.4, 1.2, easeInOutCubic),
        n.rotation(offs[i][2], 1.2, easeInOutCubic),
      ),
    ),
  );

  /* ---------- line 4: one rule ---------- */
  yield* nar.at(4);
  yield* all(grid().opacity(0, 0.5), header().opacity(0, 0.5), grid().scale(0.9, 0.5));
  grid().remove();
  const rule = createRef<Txt>();
  view.add(
    <Txt
      ref={rule}
      y={-120}
      text={'ONE RULE'}
      fontFamily={FONT}
      fontWeight={900}
      fontSize={190}
      letterSpacing={10}
      fill={V.ink}
      opacity={0}
      scale={1.4}
    />,
  );
  sfx('impact');
  yield* all(rule().opacity(1, 0.3), rule().scale(1, 0.7, easeOutExpo));

  /* ---------- line 5: the four labels ---------- */
  yield* nar.at(5);
  yield* all(rule().y(-400, 0.7, easeInOutCubic), rule().scale(0.45, 0.7, easeInOutCubic));
  const tags: Tag[] = ['VERIFIED', 'OBSERVED', 'HYPOTHESIS', 'SPECULATION'];
  const defs = [
    'We can point to a source.',
    'Visible in the work, but not measured.',
    'A reasoned explanation, not proven.',
    'Exactly that — speculation.',
  ];
  const tagNodes = createRef<Node>();
  view.add(
    <Node ref={tagNodes} y={-170}>
      {tags.map((t, i) => (
        <Node x={-630 + i * 420} opacity={0}>
          <Rect
            width={380}
            height={86}
            radius={14}
            fill={TAG_COLOR[t] + '1a'}
            stroke={TAG_COLOR[t]}
            lineWidth={2.5}
            layout
            alignItems={'center'}
            justifyContent={'center'}
            gap={14}
          >
            <Circle size={16} fill={TAG_COLOR[t]} />
            <Txt
              text={t}
              fontFamily={MONO}
              fontWeight={700}
              fontSize={30}
              letterSpacing={4}
              fill={TAG_COLOR[t]}
            />
          </Rect>
          <Txt
            y={120}
            width={360}
            textWrap
            textAlign={'center'}
            text={defs[i]}
            fontFamily={FONT}
            fontWeight={600}
            fontSize={32}
            lineHeight={42}
            fill={V.inkDim}
            opacity={0}
          />
        </Node>
      ))}
    </Node>,
  );
  const tn = tagNodes().children();
  yield* sequence(
    0.2,
    ...tn.map(n =>
      withSfx('blip', all(n.opacity(1, 0.4), n.scale(0.8).scale(1, 0.5, easeOutBack))),
    ),
  );

  /* ---------- line 6-7: definitions ---------- */
  yield* nar.at(6);
  for (const i of [0, 1]) {
    yield* (tn[i] as Node).children()[1].opacity(1, 0.5);
    yield* waitFor(0.6);
  }
  yield* nar.at(7);
  for (const i of [2, 3]) {
    yield* (tn[i] as Node).children()[1].opacity(1, 0.5);
    yield* waitFor(0.6);
  }
  yield* nar.end();
  sfx('whoosh');
  yield* all(tagNodes().opacity(0, 0.6), rule().opacity(0, 0.6), tagNodes().y(-230, 0.6));
});
