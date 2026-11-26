import {Circle, Line, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  all,
  createRef,
  createSignal,
  easeInOutCubic,
  easeInOutQuint,
  easeOutExpo,
  sequence,
  waitFor,
} from '@canvas-commons/core';
import {DateCard, FootageSlot, openScene, popIn, refs, sfx, slotLog} from '../kit';
import {FONT, MONO, V} from '../theme';

const Y0 = 1988;
const PX = 230;
const pos = (y: number) => (y - Y0) * PX;

export default makeScene2D(function* (view) {
  const nar = yield* openScene(view, 's04_history', V.amber);

  const cam = createSignal(-pos(1991.5));
  const zoom = createSignal(1);
  const world = createRef<Node>();
  const track = createRef<Line>();

  type Ev = {
    year: number;
    date: string;
    title: string;
    body: string;
    src: string;
    slot?: {id: string; desc: string; w: number; h: number};
    up: boolean;
    color: string;
  };
  const events: Ev[] = [
    {
      year: 1991.5,
      date: '1990s',
      title: 'Anime music videos',
      body: 'Fan-made, cut on home computers',
      src: refs('twc-amv-genesis'),
      slot: {id: 'H01', desc: 'Archival AMV, 4:3 (1990s–2000s)', w: 300, h: 225},
      up: true,
      color: V.magenta,
    },
    {
      year: 1993,
      date: 'JAN 1993',
      title: 'After Effects 1.0',
      body: 'Built by CoSA · bought by Aldus the same year',
      src: refs('wiki-ae', 'wiki-cosa'),
      slot: {id: 'H02', desc: 'After Effects 1.0 interface (archival screenshot)', w: 300, h: 200},
      up: false,
      color: V.cyan,
    },
    {
      year: 1994.7,
      date: '1994',
      title: 'Adobe',
      body: 'Adobe merges with Aldus; After Effects becomes an Adobe product',
      src: refs('cosa-history'),
      up: true,
      color: V.cyan,
    },
    {
      year: 2009,
      date: '2009',
      title: '100,000+ AMVs listed',
      body: 'AnimeMusicVideos.org — the community hub',
      src: refs('fanlore-amv'),
      up: true,
      color: V.magenta,
    },
    {
      year: 2012.5,
      date: 'JUL 2012',
      title: 'Element 3D',
      body: 'Video Copilot brings real-time 3D objects into After Effects',
      src: refs('cgchannel-element3d'),
      slot: {id: 'H03', desc: 'Element 3D launch demo (2012)', w: 300, h: 170},
      up: false,
      color: V.amber,
    },
  ];
  const cards = events.map(() => createRef<Node>());
  const yearLbl = createRef<Txt>();

  view.add(
    <Node ref={world} y={-20} scale={() => zoom()} x={() => cam() * zoom()}>
      <Line
        ref={track}
        points={[
          [pos(1988), 0],
          [pos(2016), 0],
        ]}
        stroke={V.line}
        lineWidth={4}
        end={0}
      />
      {Array.from({length: 2016 - 1988 + 1}, (_, i) => {
        const y = 1988 + i;
        const major = y % 5 === 0;
        return (
          <Node x={pos(y)}>
            <Line
              points={[
                [0, major ? -18 : -8],
                [0, major ? 18 : 8],
              ]}
              stroke={major ? V.muted : V.faint}
              lineWidth={2}
            />
            {major ? (
              <Txt y={44} text={String(y)} fontFamily={MONO} fontSize={22} fill={V.muted} />
            ) : null}
          </Node>
        );
      })}
      {events.map((e, i) => (
        <Node ref={cards[i]} x={pos(e.year)} opacity={0}>
          <Circle size={22} fill={e.color} shadowColor={e.color} shadowBlur={20} />
          <Line
            points={[
              [0, e.up ? -14 : 14],
              [0, e.up ? -70 : 70],
            ]}
            stroke={e.color}
            lineWidth={2}
            lineDash={[6, 6]}
          />
          <Node y={e.up ? -260 : 215}>
            <DateCard
              date={e.date}
              title={e.title}
              body={e.body}
              src={e.src}
              color={e.color}
              w={e.slot ? 470 : 520}
              x={e.slot ? -170 : 0}
              opacity={1}
            />
            {e.slot ? (
              <FootageSlot
                id={e.slot.id}
                desc={e.slot.desc}
                w={e.slot.w}
                h={e.slot.h}
                x={250}
                accent={e.color}
                small
              />
            ) : null}
          </Node>
        </Node>
      ))}
    </Node>,
  );
  view.add(
    <Txt
      ref={yearLbl}
      x={-900}
      y={-440}
      anchor={[-1, 0]}
      text={() => {
        const y = Y0 + -cam() / PX;
        return Math.floor(y).toString();
      }}
      fontFamily={MONO}
      fontWeight={700}
      fontSize={64}
      fill={V.ink + '55'}
      opacity={0}
    />,
  );
  slotLog('H01', 'Archival AMV, 4:3 (1990s–2000s) — only with permission or under fair-use review');
  slotLog('H02', 'After Effects 1.0 interface screenshot (archival)');
  slotLog('H03', 'Video Copilot Element 3D launch demo (July 2012)');

  /* line 0: the track draws */
  sfx('riser', 1.5);
  yield* all(track().end(1, 1.6, easeInOutCubic), yearLbl().opacity(1, 1));

  const goTo = function* (year: number, d = 1.6) {
    sfx(Math.abs(-pos(year) - cam()) > 2000 ? 'whooshBig' : 'whoosh');
    yield* cam(-pos(year), d, easeInOutQuint);
  };

  /* line 1: AMVs */
  yield* nar.at(1);
  sfx('pop');
  yield* popIn(cards[0](), 0.6, 20);

  /* line 2: forward to 2009 */
  yield* nar.at(2);
  yield* goTo(2009, 2.0);
  sfx('pop');
  yield* popIn(cards[3](), 0.6, 20);

  /* line 3: rewind to 1993 */
  yield* nar.at(3);
  yield* goTo(1993.6, 1.4);
  sfx('pop');
  yield* popIn(cards[1](), 0.6, 20);

  /* line 4: Adobe */
  yield* nar.at(4);
  sfx('pop');
  yield* popIn(cards[2](), 0.6, 20);

  /* line 5: studios */
  yield* nar.at(5);
  const studio = createRef<Node>();
  view.add(
    <Node ref={studio} y={-30} opacity={0}>
      <Rect width={760} height={110} radius={55} fill={V.bg + 'ee'} stroke={V.muted} lineWidth={2} />
      <Txt
        text={'ADVANCED COMPOSITING  →  PROFESSIONAL STUDIOS'}
        fontFamily={MONO}
        fontWeight={700}
        fontSize={24}
        letterSpacing={3}
        fill={V.inkDim}
      />
    </Node>,
  );
  yield* all(studio().opacity(1, 0.5), zoom(0.92, 1.2, easeInOutCubic));
  yield* waitFor(3);
  yield* studio().opacity(0, 0.5);

  /* line 6: Element 3D */
  yield* nar.at(6);
  yield* all(goTo(2012.5, 2.0), zoom(1, 2.0, easeInOutCubic));
  sfx('pop');
  yield* popIn(cards[4](), 0.6, 20);

  /* line 7: tutorials */
  yield* nar.at(7);
  const tut = createRef<Node>();
  view.add(
    <Node ref={tut} x={560} y={-250} opacity={0}>
      {[0, 1, 2].map(i => (
        <Rect
          x={i * 24}
          y={i * 24}
          width={340}
          height={190}
          radius={14}
          fill={V.panel2}
          stroke={V.amber + '88'}
          lineWidth={2}
        >
          <Circle size={64} fill={V.amber + 'cc'} />
          <Line
            points={[
              [-10, -16],
              [18, 0],
              [-10, 16],
            ]}
            closed
            fill={V.bg}
          />
        </Rect>
      ))}
      <Txt y={170} x={24} text={'TUTORIALS'} fontFamily={MONO} fontWeight={700} fontSize={26} letterSpacing={6} fill={V.amber} />
    </Node>,
  );
  slotLog('H04', 'Montage of 3-4 classic After Effects tutorial thumbnails (screenshots, credited)');
  yield* popIn(tut(), 0.6, 30);

  /* line 8: widescreen era — zoom out, then the 16:9 frame */
  yield* nar.at(8);
  yield* all(tut().opacity(0, 0.5), zoom(0.36, 2.2, easeInOutCubic), cam(-pos(2002), 2.2, easeInOutCubic), yearLbl().opacity(0, 1));
  const frame = createRef<Node>();
  view.add(
    <Node ref={frame} y={-80} opacity={0}>
      <FootageSlot id={'H05'} desc={'Archival widescreen fan edit / montage (16:9, ~2010–2015)'} w={960} h={540} accent={V.amber} />
      <Txt y={-310} text={'THE WIDESCREEN ERA'} fontFamily={FONT} fontWeight={900} fontSize={44} letterSpacing={10} fill={V.amber} />
    </Node>,
  );
  slotLog('H05', 'Archival widescreen fan edit or montage, 16:9, roughly 2010–2015');
  sfx('shutter');
  yield* all(world().opacity(0.25, 0.8), frame().opacity(1, 0.8), frame().scale(0.9).scale(1, 1.2, easeOutExpo));
  yield* nar.end();
  yield* all(world().opacity(0, 0.6), (frame().children()[1] as Txt).opacity(0, 0.5));
});
