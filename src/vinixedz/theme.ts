export const FONT = 'Inter, DejaVu Sans, sans-serif';
export const MONO = 'JetBrains Mono, DejaVu Sans Mono, monospace';

/** Dark cinematic palette. */
export const V = {
  bg: '#06080d',
  bg2: '#0b0f18',
  panel: '#0e1320',
  panel2: '#131a2b',
  line: '#232c42',
  lineSoft: '#182033',
  ink: '#eef2f8',
  inkDim: '#c3cbd9',
  muted: '#7d889e',
  faint: '#3a4560',

  cyan: '#3fe3ff',
  magenta: '#ff3d7f',
  amber: '#ffb648',
  green: '#4cf0a0',
  violet: '#8f7dff',
  red: '#ff5a5a',
};

export type Tag = 'VERIFIED' | 'OBSERVED' | 'HYPOTHESIS' | 'SPECULATION' | 'NOTE';

export const TAG_COLOR: Record<Tag, string> = {
  VERIFIED: V.green,
  OBSERVED: V.cyan,
  HYPOTHESIS: V.amber,
  SPECULATION: V.magenta,
  NOTE: V.inkDim,
};
