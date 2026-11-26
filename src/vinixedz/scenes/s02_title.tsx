import {Line, Node, Rect, Txt, makeScene2D} from '@canvas-commons/2d';
import {
  all,
  createRef,
  createSignal,
  easeInCubic,
  easeInOutCubic,
  easeOutExpo,
  sequence,
  waitFor,
} from '@canvas-commons/core';
import {SCRIPT, openScene, sfx} from '../kit';
import {FONT, MONO, V} from '../theme';

export default makeScene2D(function* (view) {
  const nar = yield* openScene(view, 's02_title', V.cyan);

  /* the "standard": a glowing level line with a stage below it */
  const level = createRef<Line>();
  const stage = createRef<Rect>();
  const lvlY = createSignal(60);
  const stageX = createSignal(0);
  view.add(
    <Node>
      <Rect
        ref={stage}
        x={() => stageX()}
        y={() => lvlY() + 140}
        width={1100}
        height={200}
        radius={10}
        fill={V.panel}
        stroke={V.line}
        lineWidth={2}
        opacity={0}
      >
        {Array.from({length: 12}, (_, i) => (
          <Rect x={-500 + i * 91} width={4} height={200} fill={V.lineSoft} />
        ))}
      </Rect>
      <Line
        ref={level}
        points={() => [
          [-800, lvlY()],
          [800, lvlY()],
        ]}
        stroke={V.cyan}
        lineWidth={6}
        shadowColor={V.cyan}
        shadowBlur={30}
        end={0}
      />
    </Node>,
  );
  yield* all(level().end(1, 1.2, easeInOutCubic), stage().opacity(1, 1.2));
  sfx('riser', 2.2);
  yield* waitFor(0.6);
  yield* lvlY(-20, 1.4, easeInOutCubic);
  sfx('whoosh');
  yield* stageX(-1500, 0.9, easeInCubic);

  yield* nar.end();

  /* ---------- title reveal ---------- */
  const title = createRef<Node>();
  const wA = createSignal(0);
  const wB = createSignal(0);
  view.add(
    <Node ref={title}>
      <Txt
        y={-330}
        text={'A VINIXEDZ DOCUMENTARY'}
        fontFamily={MONO}
        fontSize={26}
        letterSpacing={12}
        fill={V.muted}
        opacity={0}
      />
      <Rect y={-170} width={() => wA()} height={190} clip>
        <Txt
          text={'THE STANDARD'}
          fontFamily={FONT}
          fontWeight={900}
          fontSize={170}
          letterSpacing={4}
          fill={V.ink}
        />
      </Rect>
      <Rect y={120} width={() => wB()} height={190} clip>
        <Txt
          text={'MOVED'}
          fontFamily={FONT}
          fontWeight={900}
          fontSize={210}
          letterSpacing={30}
          fill={'#00000000'}
          stroke={V.cyan}
          lineWidth={4}
        />
      </Rect>
      <Txt
        y={300}
        width={1300}
        textWrap
        textAlign={'center'}
        text={SCRIPT.subtitle}
        fontFamily={FONT}
        fontWeight={500}
        fontSize={30}
        fill={V.inkDim}
        opacity={0}
      />
    </Node>,
  );
  sfx('impact');
  yield* all(lvlY(-20 + 0, 0.01), wA(1500, 0.9, easeOutExpo));
  sfx('impact');
  yield* all(wB(1500, 0.9, easeOutExpo), lvlY(232, 0.9, easeOutExpo));
  const kids = title().children();
  yield* sequence(0.3, kids[0].opacity(1, 0.6), kids[3].opacity(1, 0.6));
  sfx('sub');
  yield* waitFor(3.2);
  sfx('whooshBig');
  yield* all(
    title().scale(1.6, 0.8, easeInCubic),
    title().opacity(0, 0.8, easeInCubic),
    level().opacity(0, 0.6),
  );
});
