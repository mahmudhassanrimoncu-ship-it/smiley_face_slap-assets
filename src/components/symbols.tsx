import {Layout, Txt} from '@canvas-commons/2d';
import {FONT} from '../theme';

/** A symbol with a subscript, e.g. Q_out. */
export function Sym(props: {
  main: string;
  sub: string;
  color: string;
  size?: number;
}) {
  const size = props.size ?? 54;
  return (
    <Layout alignItems={'end'}>
      <Txt
        text={props.main}
        fontFamily={FONT}
        fontWeight={800}
        fontSize={size}
        fill={props.color}
      />
      <Txt
        text={props.sub}
        fontFamily={FONT}
        fontWeight={700}
        fontSize={size * 0.55}
        fill={props.color}
        marginBottom={-size * 0.12}
      />
    </Layout>
  );
}

export function Op(props: {text: string; color: string; size?: number}) {
  return (
    <Txt
      text={props.text}
      fontFamily={FONT}
      fontWeight={700}
      fontSize={props.size ?? 54}
      fill={props.color}
      marginLeft={18}
      marginRight={18}
    />
  );
}
