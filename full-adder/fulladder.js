/* Full adder explainer: deterministic renderer.
   drawFrame(ctx, t) paints the 1920x1080 frame for time t (seconds) using window.TIMELINE.
   The same kit drawing powers the interactive lab on the page. */
(function () {
  'use strict';
  const W = 1920, H = 1080;
  const TAU = Math.PI * 2;

  // ---------- palette (the video is a single, deliberately dark "night workbench") ----------
  const C = {
    bg: '#0E1820', bg2: '#13222D', panel: '#182B38', panel2: '#1F3646', line: '#2E4859',
    text: '#EAF1F5', dim: '#8DA3B2', faint: '#4F6878',
    one: '#FFB23F', zero: '#3A5263', teal: '#5CCAD8',
    A: '#FFD84D', B: '#67DB7C', Cin: '#5AB0FF', X: '#FF9440', N: '#C38CFF', S: '#FFFFFF', CO: '#FF6FAE',
    led: '#FF3B30', pcb: '#173246', pcb2: '#1C3B52', silk: '#DCE7EE',
    bb: '#ECE8DE', bbShade: '#D8D3C6', hole: '#3C3A36', rail: '#D9443C', railB: '#3A6FD8',
    chip: '#1B1B1F', pin: '#BFC6CC', red: '#E23B33', black: '#26272B',
  };
  const NETCOL = { A: C.A, B: C.B, C: C.Cin, X: C.X, N1: C.N, N2: C.N, S: C.S, CO: C.CO, vcc: C.red, gnd: C.black };
  const F = {
    disp: '"Barlow Condensed", "Arial Narrow", sans-serif',
    body: '"IBM Plex Sans", "Segoe UI", system-ui, sans-serif',
    mono: '"IBM Plex Mono", ui-monospace, Menlo, monospace',
  };

  // ---------- math helpers ----------
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, k) => a + (b - a) * k;
  const seg = (t, a, b) => clamp((t - a) / (b - a));
  const ease = k => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
  const eo = k => 1 - Math.pow(1 - k, 3);
  const evalFA = (A, B, Cn) => {
    const X = A ^ B, S = X ^ Cn, N1 = A & B, N2 = X & Cn;
    return { A, B, C: Cn, X, S, N1, N2, CO: N1 | N2, vcc: 1, gnd: 0 };
  };
  const bits = n => [(n >> 2) & 1, (n >> 1) & 1, n & 1];

  // ---------- drawing helpers ----------
  function font(ctx, size, fam = F.body, weight = 400) { ctx.font = `${weight} ${size}px ${fam}`; }
  function text(ctx, s, x, y, o = {}) {
    ctx.save();
    font(ctx, o.size || 28, o.font || F.body, o.weight || 400);
    ctx.fillStyle = o.color || C.text;
    ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
    ctx.textAlign = o.align || 'left';
    ctx.textBaseline = o.base || 'alphabetic';
    if (o.ls) ctx.letterSpacing = o.ls + 'px';
    if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = o.glowBlur || 18; }
    ctx.fillText(s, x, y);
    ctx.restore();
  }
  function rr(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  }
  function box(ctx, x, y, w, h, o = {}) {
    rr(ctx, x, y, w, h, o.r == null ? 14 : o.r);
    if (o.fill) { ctx.fillStyle = o.fill; ctx.fill(); }
    if (o.stroke) { ctx.lineWidth = o.lw || 2; ctx.strokeStyle = o.stroke; ctx.stroke(); }
  }
  function wrap(ctx, s, maxW) {
    const words = s.split(' '), lines = [];
    let cur = '';
    for (const w of words) {
      const test = cur ? cur + ' ' + w : w;
      if (ctx.measureText(test).width > maxW && cur) { lines.push(cur); cur = w; } else cur = test;
    }
    if (cur) lines.push(cur);
    return lines;
  }
  function para(ctx, s, x, y, maxW, o = {}) {
    ctx.save();
    font(ctx, o.size || 28, o.font || F.body, o.weight || 400);
    const lines = wrap(ctx, s, maxW);
    const lh = o.lh || (o.size || 28) * 1.35;
    lines.forEach((l, i) => text(ctx, l, x, y + i * lh, o));
    ctx.restore();
    return lines.length * lh;
  }
  function arrow(ctx, x1, y1, x2, y2, col, lw = 4, head = 14) {
    const a = Math.atan2(y2 - y1, x2 - x1);
    ctx.save(); ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = lw; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2 - Math.cos(a) * head * 0.8, y2 - Math.sin(a) * head * 0.8); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - Math.cos(a - 0.45) * head, y2 - Math.sin(a - 0.45) * head);
    ctx.lineTo(x2 - Math.cos(a + 0.45) * head, y2 - Math.sin(a + 0.45) * head);
    ctx.closePath(); ctx.fill(); ctx.restore();
  }
  function pill(ctx, s, x, y, o = {}) {
    ctx.save();
    font(ctx, o.size || 22, o.font || F.disp, o.weight || 600);
    if (o.ls) ctx.letterSpacing = o.ls + 'px';
    const w = ctx.measureText(s).width + (o.padX || 18) * 2, h = (o.size || 22) * 1.6;
    const bx = o.align === 'center' ? x - w / 2 : o.align === 'right' ? x - w : x;
    ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
    box(ctx, bx, y - h / 2, w, h, { r: h / 2, fill: o.fill || C.panel2, stroke: o.stroke, lw: o.lw });
    ctx.fillStyle = o.color || C.text; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(s, bx + w / 2, y + 1);
    ctx.restore();
    return w;
  }

  // a toggle switch, lever animates with v in [0,1]
  function toggle(ctx, x, y, v, o = {}) {
    const s = o.scale || 1;
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    box(ctx, -30, -50, 60, 100, { r: 12, fill: '#0B1218', stroke: v > 0.5 ? (o.col || C.one) : C.line, lw: 3 });
    const ly = lerp(22, -22, ease(v));
    ctx.fillStyle = '#2B3B47'; ctx.beginPath(); ctx.arc(0, 0, 13, 0, TAU); ctx.fill();
    ctx.strokeStyle = '#C9D3DA'; ctx.lineWidth = 9; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, ly); ctx.stroke();
    ctx.fillStyle = '#F2F5F7'; ctx.beginPath(); ctx.arc(0, ly, 11, 0, TAU); ctx.fill();
    if (o.label) text(ctx, o.label, 0, -66, { size: 30, font: F.disp, weight: 700, align: 'center', color: o.col || C.text });
    if (o.showVal !== false) text(ctx, v > 0.5 ? '1' : '0', 0, 88, { size: 30, font: F.mono, weight: 600, align: 'center', color: v > 0.5 ? C.one : C.faint });
    ctx.restore();
  }
  // a lamp, k in [0,1]
  function lamp(ctx, x, y, k, o = {}) {
    const r = o.r || 34, col = o.col || C.one;
    ctx.save();
    if (k > 0.01) {
      const g = ctx.createRadialGradient(x, y, r * 0.3, x, y, r * 3.2);
      g.addColorStop(0, hexA(col, 0.55 * k)); g.addColorStop(1, hexA(col, 0));
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r * 3.2, 0, TAU); ctx.fill();
    }
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU);
    ctx.fillStyle = mix('#26323B', col, k); ctx.fill();
    ctx.lineWidth = 4; ctx.strokeStyle = k > 0.5 ? '#FFFFFF55' : C.line; ctx.stroke();
    if (k > 0.05) { ctx.beginPath(); ctx.arc(x - r * 0.3, y - r * 0.3, r * 0.28, 0, TAU); ctx.fillStyle = `rgba(255,255,255,${0.55 * k})`; ctx.fill(); }
    if (o.label) text(ctx, o.label, x, y + r + 40, { size: o.lsize || 26, font: F.disp, weight: 700, align: 'center', color: o.lcol || C.text, ls: 1 });
    ctx.restore();
  }
  function hexA(hex, a) {
    const n = parseInt(hex.slice(1, 7), 16);
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
  }
  function mix(h1, h2, k) {
    const a = parseInt(h1.slice(1, 7), 16), b = parseInt(h2.slice(1, 7), 16);
    const ch = s => Math.round(lerp((a >> s) & 255, (b >> s) & 255, clamp(k)));
    return `rgb(${ch(16)},${ch(8)},${ch(0)})`;
  }

  // ---------- gate symbols (centered, 100 x 80 at scale 1) ----------
  function gatePath(ctx, type) {
    ctx.beginPath();
    if (type === 'AND') {
      ctx.moveTo(-50, -40); ctx.lineTo(0, -40); ctx.arc(0, 0, 40, -Math.PI / 2, Math.PI / 2); ctx.lineTo(-50, 40); ctx.closePath();
    } else {
      const bx = type === 'XOR' ? -42 : -50;
      ctx.moveTo(bx, -40); ctx.quadraticCurveTo(12, -40, 50, 0); ctx.quadraticCurveTo(12, 40, bx, 40);
      ctx.quadraticCurveTo(bx + 24, 0, bx, -40); ctx.closePath();
    }
  }
  function gate(ctx, type, x, y, o = {}) {
    const s = o.scale || 1, on = o.out || 0;
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
    gatePath(ctx, type);
    ctx.fillStyle = o.fill || C.panel2; ctx.fill();
    ctx.lineWidth = 4 / s * Math.max(1, s * 0.9);
    ctx.strokeStyle = on ? C.one : (o.stroke || '#7F98A8');
    if (on) { ctx.shadowColor = C.one; ctx.shadowBlur = 16; }
    ctx.stroke(); ctx.shadowBlur = 0;
    if (type === 'XOR') {
      ctx.beginPath(); ctx.moveTo(-56, -40); ctx.quadraticCurveTo(-32, 0, -56, 40); ctx.stroke();
    }
    if (o.name !== false) text(ctx, o.name || type, type === 'AND' ? -8 : -2, 9, { size: 24, font: F.disp, weight: 700, align: 'center', color: on ? C.one : C.dim });
    ctx.restore();
  }

  // ---------- signal wires for the schematic ----------
  function polyLen(pts) { let L = 0; for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); return L; }
  function polyAt(pts, d) {
    for (let i = 1; i < pts.length; i++) {
      const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      if (d <= l) { const k = d / l; return [lerp(pts[i - 1][0], pts[i][0], k), lerp(pts[i - 1][1], pts[i][1], k)]; }
      d -= l;
    }
    return pts[pts.length - 1];
  }
  function polyPart(pts, frac) {
    const L = polyLen(pts) * frac, out = [pts[0]];
    let d = 0;
    for (let i = 1; i < pts.length; i++) {
      const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      if (d + l >= L) { const k = (L - d) / l; out.push([lerp(pts[i - 1][0], pts[i][0], k), lerp(pts[i - 1][1], pts[i][1], k)]); return out; }
      out.push(pts[i]); d += l;
    }
    return out;
  }
  function sigWire(ctx, pts, col, v, t, o = {}) {
    const draw = o.draw == null ? 1 : o.draw;
    if (draw <= 0) return;
    const p = draw < 1 ? polyPart(pts, draw) : pts;
    ctx.save();
    ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
    const baseA = ctx.globalAlpha;
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    const path = () => { ctx.beginPath(); ctx.moveTo(p[0][0], p[0][1]); for (let i = 1; i < p.length; i++) ctx.lineTo(p[i][0], p[i][1]); };
    if (v) {
      ctx.shadowColor = col; ctx.shadowBlur = 20; ctx.strokeStyle = col; ctx.lineWidth = o.lw || 7; path(); ctx.stroke();
      ctx.shadowBlur = 0;
      const L = polyLen(p), gap = 36, off = (t * 140) % gap;
      ctx.fillStyle = '#FFFFFF';
      for (let d = off; d < L; d += gap) { const q = polyAt(p, d); ctx.globalAlpha = 0.85 * baseA; ctx.beginPath(); ctx.arc(q[0], q[1], 3.2, 0, TAU); ctx.fill(); }
    } else {
      ctx.strokeStyle = hexA(col, 0.32); ctx.lineWidth = o.lw || 7; path(); ctx.stroke();
    }
    if (o.dot) { ctx.globalAlpha = baseA; ctx.fillStyle = v ? col : hexA(col, 0.6); ctx.beginPath(); ctx.arc(o.dot[0], o.dot[1], 9, 0, TAU); ctx.fill(); }
    ctx.restore();
  }

  // ---------- schematic of the full adder (local coordinates ~1300 x 700) ----------
  const SCH = {
    gates: {
      x1: { type: 'XOR', x: 450, y: 200, out: 'X' }, x2: { type: 'XOR', x: 800, y: 260, out: 'S' },
      a2: { type: 'AND', x: 800, y: 440, out: 'N2' }, a1: { type: 'AND', x: 800, y: 580, out: 'N1' },
      o1: { type: 'OR', x: 1010, y: 510, out: 'CO' },
    },
    wires: [
      { id: 'wA', net: 'A', pts: [[105, 150], [300, 150], [300, 180], [400, 180]] },
      { id: 'wAa', net: 'A', pts: [[300, 180], [300, 560], [750, 560]], dot: [300, 180] },
      { id: 'wB', net: 'B', pts: [[105, 250], [340, 250], [340, 220], [400, 220]] },
      { id: 'wBa', net: 'B', pts: [[340, 250], [340, 600], [750, 600]], dot: [340, 250] },
      { id: 'wX', net: 'X', pts: [[500, 200], [620, 200], [620, 240], [750, 240]] },
      { id: 'wXa', net: 'X', pts: [[620, 240], [620, 420], [750, 420]], dot: [620, 240] },
      { id: 'wC', net: 'C', pts: [[105, 350], [680, 350], [680, 280], [750, 280]] },
      { id: 'wCa', net: 'C', pts: [[680, 350], [680, 460], [750, 460]], dot: [680, 350] },
      { id: 'wN2', net: 'N2', pts: [[850, 440], [920, 440], [920, 490], [960, 490]] },
      { id: 'wN1', net: 'N1', pts: [[850, 580], [920, 580], [920, 530], [960, 530]] },
      { id: 'wS', net: 'S', pts: [[850, 260], [1140, 260]] },
      { id: 'wCO', net: 'CO', pts: [[1060, 510], [1140, 510]] },
    ],
  };
  // vis: map id -> alpha (gates by key, wires by id, inputs 'iA','iB','iC', lamps 'lS','lCO'); draw: map id -> draw progress
  function schematic(ctx, st, t, vis = {}, o = {}) {
    const a = id => (vis[id] == null ? (vis._all == null ? 1 : vis._all) : vis[id]);
    const dr = id => (o.draw && o.draw[id] != null ? o.draw[id] : 1);
    for (const w of SCH.wires) if (a(w.id) > 0) sigWire(ctx, w.pts, NETCOL[w.net], st[w.net], t, { alpha: a(w.id), draw: dr(w.id), dot: w.dot && dr(w.id) >= 1 ? w.dot : null });
    for (const k in SCH.gates) {
      const g = SCH.gates[k];
      if (a(k) > 0) gate(ctx, g.type, g.x, g.y, { out: st[g.out], alpha: a(k) });
    }
    const ins = [['iA', 'A', 150, 'A', C.A], ['iB', 'B', 250, 'B', C.B], ['iC', 'C', 350, 'Cin', C.Cin]];
    for (const [id, net, y, lab, col] of ins) {
      if (a(id) <= 0) continue;
      ctx.save(); ctx.globalAlpha *= a(id);
      toggle(ctx, 50, y, o.lever ? o.lever[net] : st[net], { scale: 0.62, col, showVal: false });
      text(ctx, lab, 4, y + 10, { size: 32, font: F.disp, weight: 700, align: 'right', color: col });
      text(ctx, String(st[net]), 92, y - 22, { size: 24, font: F.mono, weight: 600, color: st[net] ? C.one : C.faint });
      ctx.restore();
    }
    if (a('lS') > 0) { ctx.save(); ctx.globalAlpha *= a('lS'); lamp(ctx, 1180, 260, st.S, { r: 36, label: 'SUM', col: C.one }); ctx.restore(); }
    if (a('lCO') > 0) { ctx.save(); ctx.globalAlpha *= a('lCO'); lamp(ctx, 1180, 510, st.CO, { r: 36, label: 'CARRY OUT', col: C.one }); ctx.restore(); }
  }

  // ======================================================================
  //                        THE TRAINER KIT (1800 x 900)
  // ======================================================================
  const P = 30, BX0 = 300, NCOL = 48;
  const ROWY = { 'T+': 222, 'T-': 252, a: 300, b: 330, c: 360, d: 390, e: 420, f: 480, g: 510, h: 540, i: 570, j: 600, 'B+': 648, 'B-': 678 };
  const hx = c => BX0 + (c - 1) * P;
  const Hh = (c, r) => ({ x: hx(c), y: ROWY[r] });
  const SWX = i => 420 + (i - 1) * 150, SWY = 812, SWSOCK = 748;
  const LEDX = i => 420 + (i - 1) * 150, LEDY = 64, LEDSOCK = 150;
  const PWR = { vcc: { x: 130, y: 330 }, gnd: { x: 130, y: 450 } };
  const CHIPS = [
    { id: 'xor', c0: 5, name: '7486', kind: 'XOR', net: ['A', 'B', 'X', 'X', 'C', 'S'] },
    { id: 'and', c0: 19, name: '7408', kind: 'AND', net: ['A', 'B', 'N1', 'X', 'C', 'N2'] },
    { id: 'or', c0: 33, name: '7432', kind: 'OR', net: ['N1', 'N2', 'CO', null, null, null] },
  ];
  // pin n of a chip -> breadboard hole
  const pinHole = (chip, n) => (n <= 7 ? Hh(chip.c0 + n - 1, 'f') : Hh(chip.c0 + 14 - n, 'e'));
  const LED_CO = 4, LED_S = 5;
  const sock = (kind, i) => kind === 'sw' ? { x: SWX(i), y: SWSOCK } : { x: LEDX(i), y: LEDSOCK };
  // wiring list: step = build step (2..7), bow = sideways bend of the jumper
  const WIRES = [
    { step: 2, net: 'vcc', col: C.red, a: PWR.vcc, b: Hh(1, 'T+'), bow: 0.18, say: "Connect the kit", from: '+5V socket', to: 'red (+) rail' },
    { step: 2, net: 'gnd', col: C.black, a: PWR.gnd, b: Hh(1, 'B-'), bow: 0.2, say: "and ground to the blue", from: 'GND socket', to: 'blue (−) rail' },
    { step: 2, net: 'vcc', col: C.red, a: Hh(5, 'a'), b: Hh(5, 'T+'), bow: 0, say: "a red wire from pin fourteen", from: 'XOR pin 14', to: 'red rail' },
    { step: 2, net: 'gnd', col: C.black, a: Hh(11, 'j'), b: Hh(11, 'B-'), bow: 0, say: "a black wire from pin seven", from: 'XOR pin 7', to: 'blue rail' },
    { step: 2, net: 'vcc', col: C.red, a: Hh(19, 'a'), b: Hh(19, 'T+'), bow: 0, say: "a red wire from pin fourteen", from: 'AND pin 14', to: 'red rail' },
    { step: 2, net: 'gnd', col: C.black, a: Hh(25, 'j'), b: Hh(25, 'B-'), bow: 0, say: "a black wire from pin seven", from: 'AND pin 7', to: 'blue rail' },
    { step: 2, net: 'vcc', col: C.red, a: Hh(33, 'a'), b: Hh(33, 'T+'), bow: 0, say: "a red wire from pin fourteen", from: 'OR pin 14', to: 'red rail' },
    { step: 2, net: 'gnd', col: C.black, a: Hh(39, 'j'), b: Hh(39, 'B-'), bow: 0, say: "a black wire from pin seven", from: 'OR pin 7', to: 'blue rail' },
    { step: 3, net: 'A', col: C.A, a: sock('sw', 1), b: Hh(5, 'j'), bow: 0.05, say: "Wire switch one", from: 'Switch 1 (A)', to: 'XOR pin 1' },
    { step: 3, net: 'B', col: C.B, a: sock('sw', 2), b: Hh(6, 'j'), bow: -0.08, say: "Wire switch two", from: 'Switch 2 (B)', to: 'XOR pin 2' },
    { step: 3.5, net: 'A', col: C.A, a: Hh(5, 'i'), b: Hh(19, 'i'), bow: 0.13, say: "from the XOR pin one strip", from: 'XOR pin 1 strip', to: 'AND pin 1' },
    { step: 3.5, net: 'B', col: C.B, a: Hh(6, 'h'), b: Hh(20, 'h'), bow: 0.2, say: "from the XOR pin two strip", from: 'XOR pin 2 strip', to: 'AND pin 2' },
    { step: 4, net: 'X', col: C.X, a: Hh(7, 'g'), b: Hh(8, 'g'), bow: 0.5, say: "A short jumper", from: 'XOR pin 3', to: 'XOR pin 4' },
    { step: 4, net: 'C', col: C.Cin, a: sock('sw', 3), b: Hh(9, 'j'), bow: -0.1, say: "Then wire switch three", from: 'Switch 3 (Cin)', to: 'XOR pin 5' },
    { step: 5, net: 'X', col: C.X, a: Hh(7, 'i'), b: Hh(22, 'i'), bow: -0.1, say: "Wire XOR pin three", from: 'XOR pin 3 strip', to: 'AND pin 4' },
    { step: 5, net: 'C', col: C.Cin, a: Hh(9, 'h'), b: Hh(23, 'h'), bow: -0.17, say: "And wire Carry in", from: 'XOR pin 5 strip', to: 'AND pin 5' },
    { step: 6, net: 'N1', col: C.N, a: Hh(21, 'i'), b: Hh(33, 'i'), bow: 0.14, say: "Wire AND pin three", from: 'AND pin 3', to: 'OR pin 1' },
    { step: 6, net: 'N2', col: C.N, a: Hh(24, 'j'), b: Hh(34, 'j'), bow: -0.12, say: "and AND pin six", from: 'AND pin 6', to: 'OR pin 2' },
    { step: 7, net: 'CO', col: C.CO, a: Hh(35, 'g'), b: sock('led', LED_CO), bow: 0.1, say: "Wire OR pin three", from: 'OR pin 3', to: `LED ${LED_CO} (left · Carry out)` },
    { step: 7, net: 'S', col: C.S, a: Hh(10, 'g'), b: sock('led', LED_S), bow: -0.12, say: "Wire XOR pin six", from: 'XOR pin 6', to: `LED ${LED_S} (right · Sum)` },
  ];
  const STEPS = [
    { n: 1, title: 'Place the chips', short: 'Chips' },
    { n: 2, title: 'Power: rails and pins 14 / 7', short: 'Power' },
    { n: 3, title: 'Inputs A and B', short: 'A and B' },
    { n: 4, title: 'Sum chain (XOR → XOR)', short: 'Sum chain' },
    { n: 5, title: 'Second AND gate', short: 'AND #2' },
    { n: 6, title: 'OR gate → Carry out', short: 'OR gate' },
    { n: 7, title: 'Output LEDs', short: 'LEDs' },
  ];

  function wireCurve(w) {
    const mx = (w.a.x + w.b.x) / 2, my = (w.a.y + w.b.y) / 2;
    const dx = w.b.x - w.a.x, dy = w.b.y - w.a.y, d = Math.hypot(dx, dy) || 1;
    // perpendicular pointing "up" for left-to-right wires
    let nx = dy / d, ny = -dx / d;
    if (ny > 0 || (ny === 0 && nx > 0)) { nx = -nx; ny = -ny; }
    return { cx: mx + nx * w.bow * d, cy: my + ny * w.bow * d };
  }
  function qpt(w, cp, k) {
    const u = 1 - k;
    return [u * u * w.a.x + 2 * u * k * cp.cx + k * k * w.b.x, u * u * w.a.y + 2 * u * k * cp.cy + k * k * w.b.y];
  }
  function jumper(ctx, w, o) {
    const draw = o.draw == null ? 1 : o.draw;
    if (draw <= 0) return;
    const cp = wireCurve(w), N = 40, n = Math.max(2, Math.round(N * draw));
    const pts = []; for (let i = 0; i <= n; i++) pts.push(qpt(w, cp, (i / n) * draw));
    const path = () => { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (const p of pts) ctx.lineTo(p[0], p[1]); };
    ctx.save(); ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    // shadow on the board
    ctx.strokeStyle = 'rgba(0,0,0,0.28)'; ctx.lineWidth = 9; ctx.save(); ctx.translate(3, 5); path(); ctx.stroke(); ctx.restore();
    if (o.hot) { ctx.shadowColor = w.col === C.black ? '#888' : w.col; ctx.shadowBlur = 22; }
    ctx.strokeStyle = w.col === C.S ? '#9AA6AE' : 'rgba(0,0,0,0.55)'; ctx.lineWidth = 10; path(); ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.strokeStyle = w.col; ctx.lineWidth = 7; path(); ctx.stroke();
    ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 2; ctx.save(); ctx.translate(-1.5, -1.5); path(); ctx.stroke(); ctx.restore();
    if (o.hot && o.flow) {
      ctx.setLineDash([6, 18]); ctx.lineDashOffset = -o.t * 60; ctx.strokeStyle = 'rgba(255,255,255,0.85)'; ctx.lineWidth = 3; path(); ctx.stroke(); ctx.setLineDash([]);
    }
    // metal ends
    ctx.fillStyle = '#C7CDD1';
    const end = p => { ctx.beginPath(); ctx.arc(p[0], p[1], 5, 0, TAU); ctx.fill(); };
    end(pts[0]); if (draw >= 1) end(pts[pts.length - 1]);
    ctx.restore();
  }

  function holeAt(ctx, x, y) {
    ctx.fillStyle = C.hole; ctx.fillRect(x - 5, y - 5, 10, 10);
    ctx.fillStyle = 'rgba(255,255,255,0.18)'; ctx.fillRect(x - 5, y + 3, 10, 2);
  }
  function breadboard(ctx, o) {
    // body
    box(ctx, 262, 188, 1484, 520, { r: 12, fill: C.bb });
    box(ctx, 262, 188, 1484, 520, { r: 12, stroke: C.bbShade, lw: 3 });
    ctx.fillStyle = C.bbShade; ctx.fillRect(268, 436, 1472, 26); // groove
    ctx.fillStyle = 'rgba(0,0,0,0.08)'; ctx.fillRect(268, 436, 1472, 5);
    // rail stripes
    const stripe = (y, col) => { ctx.fillStyle = col; ctx.fillRect(hx(1) - 10, y - 1.5, hx(NCOL) - hx(1) + 20, 3); };
    stripe(205, C.rail); stripe(269, C.railB); stripe(631, C.rail); stripe(695, C.railB);
    text(ctx, '+', 280, 230, { size: 26, weight: 600, color: C.rail, align: 'center' });
    text(ctx, '−', 280, 260, { size: 26, weight: 600, color: C.railB, align: 'center' });
    text(ctx, '+', 280, 656, { size: 26, weight: 600, color: C.rail, align: 'center' });
    text(ctx, '−', 280, 686, { size: 26, weight: 600, color: C.railB, align: 'center' });
    // holes
    for (let c = 1; c <= NCOL; c++) {
      for (const r of 'abcdefghij') holeAt(ctx, hx(c), ROWY[r]);
      if (c % 6 !== 0) for (const r of ['T+', 'T-', 'B+', 'B-']) holeAt(ctx, hx(c), ROWY[r]);
    }
    for (const c of [1, 5, 10, 15, 20, 25, 30, 35, 40, 45]) {
      text(ctx, String(c), hx(c), 290 - 10, { size: 13, font: F.mono, color: '#8C877A', align: 'center' });
      text(ctx, String(c), hx(c), 627, { size: 13, font: F.mono, color: '#8C877A', align: 'center' });
    }
    for (const r of 'abcdefghij') {
      text(ctx, r, 282, ROWY[r] + 5, { size: 14, font: F.mono, color: '#8C877A', align: 'center' });
      text(ctx, r, 1730, ROWY[r] + 5, { size: 14, font: F.mono, color: '#8C877A', align: 'center' });
    }
  }
  function xray(ctx, k, o = {}) {
    if (k <= 0) return;
    ctx.save(); ctx.globalAlpha = k;
    ctx.fillStyle = 'rgba(236,232,222,0.55)'; ctx.fillRect(262, 188, 1484, 520);
    const strip = (x1, y1, x2, y2, col, w) => {
      ctx.strokeStyle = col; ctx.lineWidth = w; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
    };
    for (let c = 1; c <= NCOL; c++) {
      const hiT = o.hiCol === c ? o.hiK || 0 : 0;
      strip(hx(c), ROWY.a, hx(c), ROWY.e, hiT ? mix('#9AA3A8', C.one, hiT) : '#9AA3A8', 14);
      strip(hx(c), ROWY.f, hx(c), ROWY.j, o.hiColB === c ? mix('#9AA3A8', C.teal, o.hiKB || 0) : '#9AA3A8', 14);
    }
    const rk = o.railK || 0;
    for (const [r, col] of [['T+', C.rail], ['T-', C.railB], ['B+', C.rail], ['B-', C.railB]]) {
      strip(hx(1), ROWY[r], hx(NCOL), ROWY[r], rk ? mix('#9AA3A8', col, rk) : '#9AA3A8', 12);
    }
    ctx.globalAlpha = k * 0.9;
    for (let c = 1; c <= NCOL; c++) {
      for (const r of 'abcdefghij') holeAt(ctx, hx(c), ROWY[r]);
      if (c % 6 !== 0) for (const r of ['T+', 'T-', 'B+', 'B-']) holeAt(ctx, hx(c), ROWY[r]);
    }
    ctx.restore();
  }
  function chip(ctx, ch, o = {}) {
    const x1 = hx(ch.c0) - 16, x2 = hx(ch.c0 + 6) + 16;
    ctx.save(); ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
    if (o.lift) ctx.translate(0, -o.lift);
    // legs
    ctx.fillStyle = C.pin;
    for (let n = 1; n <= 14; n++) { const p = pinHole(ch, n); ctx.fillRect(p.x - 5, n <= 7 ? 470 : 416, 10, 14); }
    ctx.shadowColor = 'rgba(0,0,0,0.5)'; ctx.shadowBlur = 10; ctx.shadowOffsetY = 4;
    box(ctx, x1, 426, x2 - x1, 48, { r: 5, fill: C.chip });
    ctx.shadowColor = 'transparent';
    ctx.fillStyle = '#333338'; ctx.beginPath(); ctx.arc(x1, 450, 9, -Math.PI / 2, Math.PI / 2); ctx.fill();
    ctx.fillStyle = '#4A4A50'; ctx.beginPath(); ctx.arc(x1 + 14, 465, 3, 0, TAU); ctx.fill();
    text(ctx, (o.family || '74LS') + ch.name.slice(2), (x1 + x2) / 2 + 4, 448, { size: 15, font: F.mono, weight: 600, color: '#D9DDE0', align: 'center' });
    text(ctx, ch.kind, (x1 + x2) / 2 + 4, 467, { size: 14, font: F.disp, weight: 700, color: ch.kind === 'XOR' ? C.X : ch.kind === 'AND' ? C.N : C.CO, align: 'center', ls: 1 });
    ctx.restore();
  }
  function pinTag(ctx, x, y, s, o = {}) {
    const up = o.up !== false;
    ctx.save(); ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
    ctx.strokeStyle = o.col || C.teal; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(x, y, 11 + Math.sin((o.t || 0) * 6) * 2, 0, TAU); ctx.stroke();
    ctx.restore();
    pill(ctx, s, x + (o.dx || 0), y + (up ? -34 : 34) + (o.dy || 0), { size: 17, font: F.body, weight: 600, fill: '#0E1820E8', color: o.col || C.teal, align: 'center', padX: 9, alpha: o.alpha });
  }

  // o: {wires: fn(i,w)->{draw,alpha} or null, chips: alpha/lift, st, power, t, lever, hiPins:[...]}
  function kit(ctx, o) {
    const st = o.st || evalFA(0, 0, 0), t = o.t || 0, power = o.power || 0;
    // board
    box(ctx, 0, 0, 1800, 900, { r: 26, fill: C.pcb });
    ctx.save(); rr(ctx, 0, 0, 1800, 900, 26); ctx.clip();
    ctx.strokeStyle = 'rgba(255,255,255,0.035)'; ctx.lineWidth = 1;
    for (let x = 20; x < 1800; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 900); ctx.stroke(); }
    ctx.restore();
    for (const [x, y] of [[26, 26], [1774, 26], [26, 874], [1774, 874]]) { ctx.fillStyle = '#0B1E2B'; ctx.beginPath(); ctx.arc(x, y, 10, 0, TAU); ctx.fill(); }
    text(ctx, 'DIGITAL LOGIC TRAINER', 40, 868, { size: 26, font: F.disp, weight: 700, color: C.silk, ls: 3, alpha: 0.85 });
    text(ctx, 'MODEL DL-2', 1760, 868, { align: 'right', size: 18, font: F.disp, weight: 600, color: C.silk, ls: 2, alpha: 0.5 });
    // power block
    box(ctx, 40, 188, 180, 380, { r: 12, stroke: 'rgba(220,231,238,0.35)', lw: 2 });
    text(ctx, 'POWER', 130, 222, { size: 24, font: F.disp, weight: 700, color: C.silk, align: 'center', ls: 3 });
    lamp(ctx, 130, 262, power, { r: 10, col: '#4DFF7A' });
    text(ctx, 'ON', 160, 268, { size: 16, font: F.disp, weight: 600, color: C.silk, alpha: 0.7 });
    for (const [k, lab, col] of [['vcc', '+5V  VCC', C.red], ['gnd', 'GND  0V', '#111']]) {
      const p = PWR[k];
      ctx.fillStyle = col; ctx.beginPath(); ctx.arc(p.x, p.y, 26, 0, TAU); ctx.fill();
      ctx.fillStyle = '#0A0A0A'; ctx.beginPath(); ctx.arc(p.x, p.y, 10, 0, TAU); ctx.fill();
      ctx.strokeStyle = '#ffffff40'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(p.x, p.y, 26, 0, TAU); ctx.stroke();
      text(ctx, lab, p.x, p.y + 56, { size: 20, font: F.disp, weight: 700, color: C.silk, align: 'center', ls: 1 });
    }
    // LED strip
    text(ctx, 'LOGIC  INDICATORS', 40, 72, { size: 20, font: F.disp, weight: 700, color: C.silk, ls: 2, alpha: 0.8 });
    for (let i = 1; i <= 8; i++) {
      const x = LEDX(i);
      let on = 0;
      if (power && o.ledNet) { const net = o.ledNet[i]; if (net) on = st[net]; }
      if (o.ledForce && o.ledForce[i] != null) on = o.ledForce[i];
      lamp(ctx, x, LEDY + 4, on, { r: 17, col: C.led });
      text(ctx, 'L' + i, x + 32, LEDY + 11, { size: 18, font: F.disp, weight: 700, color: C.silk, alpha: 0.85 });
      ctx.fillStyle = '#0A0A0A'; ctx.fillRect(x - 7, LEDSOCK - 7, 14, 14);
      ctx.strokeStyle = '#ffffff50'; ctx.lineWidth = 1.5; ctx.strokeRect(x - 9, LEDSOCK - 9, 18, 18);
    }
    // switches
    text(ctx, 'LOGIC SWITCHES', 40, 760, { size: 20, font: F.disp, weight: 700, color: C.silk, ls: 2, alpha: 0.8 });
    text(ctx, 'UP = 1 = +5V', 40, 786, { size: 18, font: F.disp, weight: 600, color: C.silk, ls: 2, alpha: 0.6 });
    for (let i = 1; i <= 8; i++) {
      const x = SWX(i), net = o.swNet && o.swNet[i];
      let v = 0;
      if (net && o.lever) v = o.lever[net];
      else if (net) v = st[net];
      if (o.swForce && o.swForce[i] != null) v = o.swForce[i];
      ctx.fillStyle = '#0A0A0A'; ctx.fillRect(x - 7, SWSOCK - 7, 14, 14);
      ctx.strokeStyle = '#ffffff50'; ctx.lineWidth = 1.5; ctx.strokeRect(x - 9, SWSOCK - 9, 18, 18);
      ctx.save(); ctx.translate(x, SWY + 12); ctx.scale(0.62, 0.62);
      toggle(ctx, 0, 0, v, { showVal: false, col: o.swCol && o.swCol[i] });
      ctx.restore();
      text(ctx, 'S' + i, x + 30, SWY + 52, { size: 18, font: F.disp, weight: 700, color: C.silk, alpha: 0.85 });
    }
    breadboard(ctx, o);
    if (o.xray) xray(ctx, o.xray, o.xrayOpt || {});
    // chips
    if (o.chips !== 0) for (let i = 0; i < 3; i++) {
      const ca = typeof o.chips === 'function' ? o.chips(i) : { alpha: o.chips == null ? 1 : o.chips };
      if (ca.alpha > 0) chip(ctx, CHIPS[i], ca);
    }
    // wires
    if (o.wires) WIRES.forEach((w, i) => {
      const s = o.wires(i, w);
      if (!s || s.draw <= 0) return;
      jumper(ctx, w, { draw: s.draw, alpha: s.alpha, hot: power > 0.5 && (w.net === 'vcc' || st[w.net] === 1) && w.net !== 'gnd', flow: true, t });
    });
    if (o.over) o.over(ctx);
  }
  const KIT_LEDNET = { [LED_CO]: 'CO', [LED_S]: 'S' };
  const KIT_SWNET = { 1: 'A', 2: 'B', 3: 'C' };
  const KIT_SWCOL = { 1: C.A, 2: C.B, 3: C.Cin };

  // ======================================================================
  //                                 SCENES
  // ======================================================================
  // C(id) => {p (0..1 through cue), t (seconds since start), on, s, d}
  const S = {};

  // ---- 1. intro
  S.intro = (ctx, lt, Q) => {
    const k = eo(seg(lt, 0.2, 1.6));
    // kit preview on the right, running through combos
    const n = Math.floor(lt / 1.8) % 8, [a, b, c] = bits(n);
    ctx.save(); ctx.globalAlpha = k; ctx.translate(lerp(1100, 960, k), 250); ctx.scale(0.5, 0.5);
    kit(ctx, { st: evalFA(a, b, c), t: lt, power: 1, wires: () => ({ draw: 1 }), ledNet: KIT_LEDNET, swNet: KIT_SWNET, swCol: KIT_SWCOL });
    ctx.restore();
    text(ctx, 'THE FULL ADDER', 120, 380, { size: 132, font: F.disp, weight: 700, color: C.text, alpha: k, ls: 2 });
    text(ctx, 'from schoolbook addition', 124, 450, { size: 40, color: C.dim, alpha: eo(seg(lt, 0.8, 2)) });
    text(ctx, 'to glowing wires on your breadboard', 124, 500, { size: 40, color: C.dim, alpha: eo(seg(lt, 1.1, 2.3)) });
    const q = Q('i2');
    if (q.on) {
      const tags = ['No background needed', '3 chips', '20 wires', '1 trainer kit'];
      let x = 124;
      tags.forEach((s, i) => { const kk = eo(seg(q.t, i * 0.35, i * 0.35 + 0.6)); x += pill(ctx, s, x, 600, { size: 26, alpha: kk, fill: C.panel2, color: i ? C.text : C.one, padX: 20 }) + 14; });
    }
    // small binary sparkle: A + B + Cin = ?
    text(ctx, '1 + 1 + 1 = 11₂', 124, 210, { size: 34, font: F.mono, color: C.one, alpha: k * 0.9 });
  };

  // ---- 2. column addition
  S.column = (ctx, lt, Q) => {
    const c1 = Q('c1'), c2 = Q('c2'), c3 = Q('c3'), c4 = Q('c4'), c5 = Q('c5');
    const mv = ease(seg(c4.t, 0, 1.2)) * (c4.on ? 1 : 0);
    ctx.save();
    ctx.translate(lerp(0, -470, mv), lerp(0, 40, mv));
    const sc = lerp(1, 0.78, mv);
    ctx.translate(960, 470); ctx.scale(sc, sc); ctx.translate(-960, -470);
    const TX = 860, OX = 1040, dsz = 150;
    const app = eo(seg(c1.t, 0.2, 1.2));
    // column highlight
    let hx_ = OX, hk = c1.on ? eo(seg(c1.t, 2.5, 3.2)) : 0;
    if (c3.on) hx_ = lerp(OX, TX, ease(seg(c3.t, 0, 0.6)));
    if (c4.on) hx_ = OX;
    box(ctx, hx_ - 85, 210, 170, 580, { r: 18, stroke: hexA(C.teal, hk * 0.9), lw: 4, fill: hexA(C.teal, hk * 0.07) });
    text(ctx, '4', TX, 420, { size: dsz, font: F.mono, weight: 500, align: 'center', alpha: app });
    text(ctx, '7', OX, 420, { size: dsz, font: F.mono, weight: 500, align: 'center', alpha: app });
    text(ctx, '+', 700, 580, { size: dsz, font: F.mono, weight: 500, align: 'center', alpha: app, color: C.dim });
    text(ctx, '3', TX, 580, { size: dsz, font: F.mono, weight: 500, align: 'center', alpha: app });
    text(ctx, '8', OX, 580, { size: dsz, font: F.mono, weight: 500, align: 'center', alpha: app });
    ctx.fillStyle = hexA(C.text, app); ctx.fillRect(660, 620, 480, 6);
    // c2: 7 + 8 = 15 note, 5 drops, 1 flies to carry
    if (c2.on) {
      const nk = eo(seg(c2.t, 0.3, 1));
      if (!c4.on) text(ctx, '7 + 8 = 15', 1240, 440, { size: 64, font: F.mono, color: C.one, alpha: nk * (1 - seg(c3.t, 0, 0.5)) });
      const d5 = eo(seg(c2.t, c2.at('So we write') + 0.4, c2.at('So we write') + 1.2));
      text(ctx, '5', OX, lerp(440, 760, d5), { size: dsz, font: F.mono, weight: 600, align: 'center', color: C.one, alpha: d5 });
      const f1 = ease(seg(c2.t, c2.at('and carry'), c2.at('and carry') + 1.3));
      if (f1 > 0) {
        const x = lerp(1306, TX, f1), y = lerp(440, 230, f1) - Math.sin(f1 * Math.PI) * 120;
        text(ctx, '1', x, y, { size: lerp(64, 70, f1), font: F.mono, weight: 600, align: 'center', color: C.CO });
        if (f1 >= 1) text(ctx, 'carry', TX, 168, { size: 26, align: 'center', color: C.CO });
      }
    }
    if (c3.on) {
      const nk = eo(seg(c3.t, 0.6, 1.3));
      if (!c4.on) text(ctx, '4 + 3 + 1 = 8', 1240, 440, { size: 64, font: F.mono, color: C.one, alpha: nk });
      const d8 = eo(seg(c3.t, c3.at('makes eight'), c3.at('makes eight') + 0.8));
      text(ctx, '8', TX, lerp(440, 760, d8), { size: dsz, font: F.mono, weight: 600, align: 'center', color: C.one, alpha: d8 });
    }
    ctx.restore();
    // c4: the column machine
    if (c4.on) {
      const bk = eo(seg(c4.t, 0.8, 1.8));
      const bx = 1080, by = 300, bw = 340, bh = 330;
      ctx.save(); ctx.globalAlpha = bk;
      box(ctx, bx, by, bw, bh, { r: 22, fill: C.panel, stroke: C.teal, lw: 3 });
      text(ctx, 'ONE COLUMN', bx + bw / 2, by + bh / 2 - 6, { size: 44, font: F.disp, weight: 700, align: 'center', color: C.teal, ls: 2 });
      text(ctx, '7 + 8 + 0', bx + bw / 2, by + bh / 2 + 44, { size: 30, font: F.mono, align: 'center', color: C.dim });
      ctx.restore();
      const ins = [['top digit', '7', C.A], ['bottom digit', '8', C.B], ['carry in', '0', C.Cin]];
      const inAt = [c4.at('a digit from the top'), c4.at('a digit from the bottom'), c4.at('and a carry coming')];
      ins.forEach(([lab, v, col], i) => {
        const k = eo(seg(c4.t, inAt[i], inAt[i] + 0.6));
        if (k <= 0) return;
        const y = by + 75 + i * 90;
        ctx.save(); ctx.globalAlpha = k;
        arrow(ctx, bx - 190, y, bx - 8, y, col, 5);
        text(ctx, lab, bx - 200, y + 10, { size: 28, align: 'right', color: col });
        text(ctx, v, bx - 100, y - 14, { size: 30, font: F.mono, weight: 600, align: 'center', color: C.text });
        ctx.restore();
      });
      const outs = [['digit to write', '5', C.S, 120], ['carry out', '1', C.CO, 230]];
      const outAt = [c4.at('a digit to write'), c4.at('and a carry to pass')];
      outs.forEach(([lab, v, col, dy], i) => {
        const k = eo(seg(c4.t, outAt[i], outAt[i] + 0.6));
        if (k <= 0) return;
        const y = by + dy;
        ctx.save(); ctx.globalAlpha = k;
        arrow(ctx, bx + bw + 8, y, bx + bw + 170, y, col, 5);
        text(ctx, lab, bx + bw + 182, y + 10, { size: 28, color: col });
        text(ctx, v, bx + bw + 90, y - 14, { size: 30, font: F.mono, weight: 600, align: 'center', color: C.text });
        ctx.restore();
      });
    }
    if (c5.on) {
      const k = eo(seg(c5.t, 0.2, 1));
      text(ctx, '3 in  →  2 out', 1250, 760, { size: 64, font: F.disp, weight: 700, align: 'center', color: C.one, alpha: k, ls: 2 });
      text(ctx, '= a FULL ADDER', 1250, 830, { size: 44, font: F.disp, weight: 600, align: 'center', color: C.text, alpha: eo(seg(c5.t, 2.2, 3)), ls: 2 });
    }
  };

  // ---- 3. binary
  S.binary = (ctx, lt, Q) => {
    const b1 = Q('b1'), b2 = Q('b2'), b3 = Q('b3'), b4 = Q('b4');
    const swOut = b2.on ? ease(seg(b2.t, 0, 0.7)) : 0;
    if (swOut < 1) {
      ctx.save(); ctx.globalAlpha = (1 - swOut) * eo(seg(b1.t, 0, 0.8));
      toggle(ctx, 720, 440, 0, { scale: 1.8, showVal: false });
      text(ctx, '0', 720, 640, { size: 90, font: F.mono, weight: 600, align: 'center', color: C.faint });
      text(ctx, 'off · down · 0 V', 720, 700, { size: 30, align: 'center', color: C.dim });
      const up = eo(seg(b1.t, 2.4, 3.0));
      toggle(ctx, 1200, 440, up, { scale: 1.8, showVal: false });
      text(ctx, '1', 1200, 640, { size: 90, font: F.mono, weight: 600, align: 'center', color: C.one });
      text(ctx, 'on · up · 5 V', 1200, 700, { size: 30, align: 'center', color: C.dim });
      lamp(ctx, 1400, 440, up, { r: 34 });
      text(ctx, 'Only two digits:', 960, 210, { size: 44, font: F.disp, weight: 600, align: 'center', color: C.text, ls: 1 });
      ctx.restore();
    }
    const cards = [
      { eq: '0 + 0', dec: '= 0', c: 0, s: 0, cue: b2, ph: 'Zero plus zero' },
      { eq: '0 + 1', dec: '= 1', c: 0, s: 1, cue: b2, ph: 'Zero plus one' },
      { eq: '1 + 1', dec: '= 2', c: 1, s: 0, cue: b3, ph: 'But one plus one', rv: 'So we write' },
      { eq: '1 + 1 + 1', dec: '= 3', c: 1, s: 1, cue: b4, ph: 'one plus one plus one', rv: 'Write down' },
    ];
    const cw = 380, gap = 40, x0 = (W - (cw * 4 + gap * 3)) / 2;
    cards.forEach((cd, i) => {
      if (!cd.cue.on) return;
      const t0 = cd.cue.at(cd.ph), k = eo(seg(cd.cue.t, t0, t0 + 0.6));
      if (k <= 0) return;
      const x = x0 + i * (cw + gap), y = 240 + (1 - k) * 40;
      const active = (i === 2 && b3.on && !b4.on) || (i === 3 && b4.on);
      ctx.save(); ctx.globalAlpha = k;
      box(ctx, x, y, cw, 520, { r: 22, fill: C.panel, stroke: active ? C.teal : C.line, lw: active ? 4 : 2 });
      text(ctx, cd.eq, x + cw / 2, y + 100, { size: 60, font: F.mono, weight: 500, align: 'center' });
      text(ctx, cd.dec + ' in decimal', x + cw / 2, y + 160, { size: 26, align: 'center', color: C.dim });
      ctx.fillStyle = C.line; ctx.fillRect(x + 40, y + 200, cw - 80, 2);
      const rk = cd.rv ? eo(seg(cd.cue.t, cd.cue.at(cd.rv), cd.cue.at(cd.rv) + 0.6)) : eo(seg(cd.cue.t, t0 + 0.8, t0 + 1.4));
      text(ctx, String(cd.c), x + cw / 2 - 55, y + 330, { size: 120, font: F.mono, weight: 600, align: 'center', color: cd.c ? C.CO : C.faint, alpha: rk });
      text(ctx, String(cd.s), x + cw / 2 + 55, y + 330, { size: 120, font: F.mono, weight: 600, align: 'center', color: cd.s ? C.one : C.faint, alpha: rk });
      text(ctx, 'carry', x + cw / 2 - 55, y + 385, { size: 26, align: 'center', color: C.CO, alpha: rk });
      text(ctx, 'write', x + cw / 2 + 55, y + 385, { size: 26, align: 'center', color: C.one, alpha: rk });
      if (i === 2) text(ctx, 'like 15: write 5, carry 1', x + cw / 2, y + 470, { size: 24, align: 'center', color: C.dim, alpha: eo(seg(b3.t, b3.at("It's just like"), b3.at("It's just like") + 0.6)) });
      if (i === 3) text(ctx, 'three = one, one', x + cw / 2, y + 470, { size: 24, align: 'center', color: C.dim, alpha: eo(seg(b4.p, 0.6, 0.8)) });
      ctx.restore();
    });
  };

  // ---- the "full adder box" used in scene 4
  function faBox(ctx, x, y, s, st, lev, o = {}) {
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    const ins = [['A', C.A, -110], ['B', C.B, 0], ['Cin', C.Cin, 110]];
    for (const [n, col, dy] of ins) {
      const key = n === 'Cin' ? 'C' : n;
      sigWire(ctx, [[-300, dy], [-200, dy]], col, st[key], o.t || 0);
      toggle(ctx, -350, dy, lev[key], { scale: 0.75, showVal: false, col });
      text(ctx, n, -400, dy + 12, { size: 38, font: F.disp, weight: 700, align: 'right', color: col });
    }
    box(ctx, -200, -190, 400, 380, { r: 26, fill: C.panel, stroke: C.teal, lw: 4 });
    text(ctx, 'FULL', 0, -20, { size: 64, font: F.disp, weight: 700, align: 'center', color: C.teal, ls: 4 });
    text(ctx, 'ADDER', 0, 50, { size: 64, font: F.disp, weight: 700, align: 'center', color: C.teal, ls: 4 });
    sigWire(ctx, [[200, -40], [270, -40], [270, -110], [300, -110]], C.CO, st.CO, o.t || 0);
    sigWire(ctx, [[200, 40], [430, 40], [430, -110]], C.S, st.S, o.t || 0);
    lamp(ctx, 300, -150, st.CO, { r: 40, col: C.one });
    lamp(ctx, 430, -150, st.S, { r: 40, col: C.one });
    text(ctx, 'CARRY', 300, -220, { size: 28, font: F.disp, weight: 700, align: 'center', color: C.CO, ls: 1 });
    text(ctx, 'SUM', 430, -220, { size: 28, font: F.disp, weight: 700, align: 'center', color: C.S, ls: 1 });
    ctx.restore();
  }
  function countDots(ctx, x, y, n, k = 1) {
    for (let i = 0; i < 3; i++) {
      ctx.beginPath(); ctx.arc(x + i * 40, y, 13, 0, TAU);
      ctx.fillStyle = i < n ? hexA(C.one, k) : hexA(C.zero, k); ctx.fill();
    }
  }
  const leverFor = (states, idx, lt, tchange) => {
    // animate toggles between successive state rows
    const cur = states[idx], prev = states[Math.max(0, idx - 1)];
    const k = ease(seg(lt, tchange, tchange + 0.35));
    return { A: lerp(prev[0], cur[0], k), B: lerp(prev[1], cur[1], k), C: lerp(prev[2], cur[2], k) };
  };

  // ---- 4. count the ones
  S.count = (ctx, lt, Q) => {
    const k1 = Q('k1'), k2 = Q('k2'), k3 = Q('k3'), k4 = Q('k4'), k5 = Q('k5'), k6 = Q('k6');
    let row = [0, 0, 0], prevRow = [0, 0, 0], tch = 0;
    if (k2.on && !k3.on) { const seq = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [1, 1, 1], [0, 1, 0], [0, 1, 1]]; const i = Math.min(seq.length - 1, Math.floor(k2.t / 1.6)); row = seq[i]; prevRow = seq[Math.max(0, i - 1)]; tch = k2.s + i * 1.6; }
    if (k3.on) { const seq = [[0, 0, 0], [0, 0, 1], [0, 1, 1], [1, 1, 1]]; const cuts = [0, k3.at('Count one'), k3.at('Count two'), k3.at('Count three')]; let i = 0; for (let j = 0; j < 4; j++) if (k3.t >= cuts[j]) i = j; row = seq[i]; prevRow = seq[Math.max(0, i - 1)]; tch = k3.s + cuts[i]; }
    let hiRow = -1;
    if (k4.on) { const i = Math.min(7, Math.floor(k4.p * 9)); row = bits(i); prevRow = bits(Math.max(0, i - 1)); tch = k4.s + i * k4.d / 9; hiRow = i; }
    if (k5.on || k6.on) { const base = k5.on ? k5.s : k5.s; const i = Math.floor((lt - base) / 1.3) % 8; row = bits(i); prevRow = bits((i + 7) % 8); tch = base + Math.floor((lt - base) / 1.3) * 1.3; hiRow = i; }
    const kk = ease(seg(lt, tch, tch + 0.35));
    const lev = { A: lerp(prevRow[0], row[0], kk), B: lerp(prevRow[1], row[1], kk), C: lerp(prevRow[2], row[2], kk) };
    const st = evalFA(row[0], row[1], row[2]);
    const n = row[0] + row[1] + row[2];
    const mv = k4.on ? ease(seg(k4.t, 0, 1.2)) : 0;
    const bx = lerp(900, 470, mv), by = lerp(470, 360, mv), bs = lerp(1, 0.62, mv);
    const ba = eo(seg(k1.t, 0, 1));
    ctx.save(); ctx.globalAlpha = ba; faBox(ctx, bx, by, bs, st, lev, { t: lt }); ctx.restore();
    // count readout
    if (k2.on) {
      const ck = eo(seg(k2.t, 1.5, 2.3));
      const cx = lerp(560, 230, mv), cy = lerp(800, 620, mv);
      ctx.save(); ctx.globalAlpha = ck;
      text(ctx, 'ones switched on', cx, cy - 40, { size: 28, color: C.dim });
      countDots(ctx, cx + 20, cy, n);
      text(ctx, '= ' + n, cx + 140, cy + 14, { size: 46, font: F.mono, weight: 600, color: C.one });
      if (!k4.on) {
        text(ctx, 'in binary:', cx + 360, cy - 40, { size: 28, color: C.dim });
        text(ctx, `${st.CO} ${st.S}`, cx + 360, cy + 16, { size: 56, font: F.mono, weight: 600, color: C.text });
        text(ctx, '→ the two lights', cx + 500, cy + 12, { size: 30, color: C.dim });
      }
      ctx.restore();
    }
    // truth table
    if (k4.on) {
      const tx = 990, ty = 170, rh = 72;
      const cols = [['A', 1040, C.A], ['B', 1130, C.B], ['Cin', 1225, C.Cin], ['count', 1385, C.dim], ['CARRY', 1570, C.CO], ['SUM', 1720, C.S]];
      const tk = eo(seg(k4.t, 0.6, 1.4));
      ctx.save(); ctx.globalAlpha = tk;
      box(ctx, tx, ty - 20, 840, 690, { r: 20, fill: C.panel });
      for (const [h, x, col] of cols) text(ctx, h, x, ty + 30, { size: 30, font: F.disp, weight: 700, align: 'center', color: col, ls: 1 });
      ctx.fillStyle = C.line; ctx.fillRect(tx + 20, ty + 48, 800, 2); ctx.fillRect(1300, ty + 4, 2, 640); ctx.fillRect(1470, ty + 4, 2, 640);
      for (let r = 0; r < 8; r++) {
        const rk = eo(seg(k4.p, r / 9, r / 9 + 0.1));
        if (rk <= 0) continue;
        const [a, b, c] = bits(r), s = evalFA(a, b, c), cnt = a + b + c, y = ty + 100 + r * rh;
        ctx.save(); ctx.globalAlpha = tk * rk;
        if (r === hiRow) box(ctx, tx + 12, y - 46, 816, rh - 6, { r: 12, fill: hexA(C.teal, 0.13), stroke: hexA(C.teal, 0.6), lw: 2 });
        const oddK = k5.on || k6.on ? eo(seg(k5.p, 0.05, 0.2)) : 0;
        const twoK = k5.on || k6.on ? eo(seg(k5.t, k5.at('The Carry light'), k5.at('The Carry light') + 0.6)) : 0;
        if (s.S && oddK) box(ctx, 1670, y - 42, 100, rh - 14, { r: 10, fill: hexA(C.one, 0.22 * oddK) });
        if (s.CO && twoK) box(ctx, 1520, y - 42, 100, rh - 14, { r: 10, fill: hexA(C.CO, 0.22 * twoK) });
        [a, b, c].forEach((v, i) => text(ctx, String(v), cols[i][1], y, { size: 38, font: F.mono, weight: 500, align: 'center', color: v ? C.text : C.faint }));
        countDots(ctx, 1345, y - 12, cnt, 1);
        text(ctx, String(s.CO), 1570, y, { size: 38, font: F.mono, weight: 600, align: 'center', color: s.CO ? C.CO : C.faint });
        text(ctx, String(s.S), 1720, y, { size: 38, font: F.mono, weight: 600, align: 'center', color: s.S ? C.one : C.faint });
        ctx.restore();
      }
      ctx.restore();
    }
    // rules
    const rk = k5.on ? eo(seg(k5.p, 0.05, 0.25)) : 0, rk2 = k5.on ? eo(seg(k5.t, k5.at('The Carry light'), k5.at('The Carry light') + 0.6)) : 0;
    if (rk > 0) {
      ctx.save(); ctx.globalAlpha = rk;
      box(ctx, 110, 700, 760, 84, { r: 16, fill: C.panel, stroke: C.one, lw: k6.on ? 4 : 2 });
      text(ctx, 'SUM', 140, 756, { size: 40, font: F.disp, weight: 700, color: C.one, ls: 2 });
      text(ctx, '= an ODD number of ones (1 or 3)', 240, 755, { size: 32, color: C.text });
      ctx.restore();
    }
    if (rk2 > 0) {
      ctx.save(); ctx.globalAlpha = rk2;
      box(ctx, 110, 800, 760, 84, { r: 16, fill: C.panel, stroke: C.CO, lw: k6.on ? 4 : 2 });
      text(ctx, 'CARRY', 140, 856, { size: 40, font: F.disp, weight: 700, color: C.CO, ls: 2 });
      text(ctx, '= TWO OR MORE ones (2 or 3)', 270, 855, { size: 32, color: C.text });
      ctx.restore();
    }
  };

  // ---- 5. gates
  function seriesCircuit(ctx, x, y, a, b, type) {
    // tiny battery + two switches + lamp
    const on = type === 'AND' ? a & b : a | b;
    ctx.save(); ctx.translate(x, y);
    ctx.strokeStyle = on ? C.one : '#5F7889'; ctx.lineWidth = 4; ctx.lineJoin = 'round';
    const sw = (sx, sy, v) => {
      ctx.fillStyle = ctx.strokeStyle; ctx.beginPath(); ctx.arc(sx - 22, sy, 5, 0, TAU); ctx.arc(sx + 22, sy, 5, 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.moveTo(sx - 22, sy); ctx.lineTo(sx + (v ? 22 : 16), sy - (v ? 0 : 22)); ctx.stroke();
    };
    // battery
    ctx.beginPath(); ctx.moveTo(-180, -14); ctx.lineTo(-180, 14); ctx.moveTo(-168, -6); ctx.lineTo(-168, 6); ctx.stroke();
    if (type === 'AND') {
      ctx.beginPath(); ctx.moveTo(-180, -14); ctx.lineTo(-180, -50); ctx.lineTo(-90, -50); ctx.moveTo(-46, -50); ctx.lineTo(28, -50); ctx.moveTo(72, -50); ctx.lineTo(150, -50); ctx.lineTo(150, -24);
      ctx.moveTo(150, 24); ctx.lineTo(150, 50); ctx.lineTo(-168, 50); ctx.lineTo(-168, 6); ctx.stroke();
      sw(-68, -50, a); sw(50, -50, b);
      text(ctx, 'A', -68, -82, { size: 22, font: F.disp, weight: 700, align: 'center', color: C.A });
      text(ctx, 'B', 50, -82, { size: 22, font: F.disp, weight: 700, align: 'center', color: C.B });
    } else {
      ctx.beginPath(); ctx.moveTo(-180, -14); ctx.lineTo(-180, -60); ctx.lineTo(-30, -60); ctx.moveTo(14, -60); ctx.lineTo(80, -60); ctx.lineTo(80, -10);
      ctx.moveTo(-110, -60); ctx.lineTo(-110, -16); ctx.lineTo(-30, -16); ctx.moveTo(14, -16); ctx.lineTo(80, -16);
      ctx.moveTo(80, -60); ctx.lineTo(150, -60); ctx.lineTo(150, -24);
      ctx.moveTo(150, 24); ctx.lineTo(150, 50); ctx.lineTo(-168, 50); ctx.lineTo(-168, 6); ctx.stroke();
      sw(-8, -60, a); sw(-8, -16, b);
      text(ctx, 'A', -60, -70, { size: 22, font: F.disp, weight: 700, align: 'center', color: C.A });
      text(ctx, 'B', -60, -24, { size: 22, font: F.disp, weight: 700, align: 'center', color: C.B });
    }
    ctx.restore();
    lamp(ctx, x + 150, y, on, { r: 22 });
  }
  S.gates = (ctx, lt, Q) => {
    const g1 = Q('g1'), g2 = Q('g2'), g3 = Q('g3'), g4 = Q('g4'), g5 = Q('g5');
    const types = ['AND', 'OR', 'XOR'], cues = [g2, g3, g4];
    const rules = ['ON only if BOTH inputs are on', 'ON if EITHER input is on (or both)', 'ON only if the inputs are DIFFERENT'];
    const fn = [(a, b) => a & b, (a, b) => a | b, (a, b) => a ^ b];
    let active = -1; cues.forEach((c, i) => { if (c.on) active = i; });
    if (g5.on) active = 2;
    types.forEach((ty, i) => {
      const cx = 330 + i * 630;
      const appear = eo(seg(g1.t, 0.6 + i * 0.4, 1.4 + i * 0.4));
      const dimK = active === -1 ? 1 : active === i ? 1 : 0.32;
      ctx.save(); ctx.globalAlpha = appear * dimK;
      box(ctx, cx - 290, 110, 580, 790, { r: 24, fill: active === i ? C.panel : C.bg2, stroke: active === i ? C.teal : C.line, lw: active === i ? 3 : 2 });
      // input cycle
      const c = cues[i];
      let n = 0, lev = [0, 0];
      if (c.on || (i === 2 && g5.on)) {
        const tt = i === 2 && g5.on ? lt - g4.s : c.t;
        n = Math.floor(tt / 1.7) % 4;
        const prev = (n + 3) % 4, kk = ease(seg(tt % 1.7, 0, 0.3));
        lev = [lerp((prev >> 1) & 1, (n >> 1) & 1, kk), lerp(prev & 1, n & 1, kk)];
      }
      const a = (n >> 1) & 1, b = n & 1, out = active === i ? fn[i](a, b) : 0;
      const gy = 260;
      sigWire(ctx, [[cx - 150, gy - 20], [cx - 60, gy - 20]], C.A, active === i ? a : 0, lt, { lw: 6 });
      sigWire(ctx, [[cx - 150, gy + 20], [cx - 60, gy + 20]], C.B, active === i ? b : 0, lt, { lw: 6 });
      sigWire(ctx, [[cx + 60, gy], [cx + 150, gy]], C.one, out, lt, { lw: 6 });
      toggle(ctx, cx - 190, gy - 32, active === i ? lev[0] : 0, { scale: 0.42, showVal: false, col: C.A });
      toggle(ctx, cx - 190, gy + 32, active === i ? lev[1] : 0, { scale: 0.42, showVal: false, col: C.B });
      gate(ctx, ty, cx, gy, { scale: 1.2, out, name: false });
      lamp(ctx, cx + 180, gy, out, { r: 26 });
      text(ctx, ty, cx, 170, { size: 48, font: F.disp, weight: 700, align: 'center', color: active === i ? C.teal : C.text, ls: 3 });
      para(ctx, rules[i], cx - 250, 365, 500, { size: 28, weight: 600, align: 'left' });
      // mini truth table
      const ty0 = 470;
      ['A', 'B', 'out'].forEach((h, j) => text(ctx, h, cx - 120 + j * 120, ty0, { size: 26, font: F.disp, weight: 700, align: 'center', color: [C.A, C.B, C.one][j] }));
      for (let r = 0; r < 4; r++) {
        const ra = (r >> 1) & 1, rb = r & 1, ro = fn[i](ra, rb), y = ty0 + 46 + r * 44;
        if (active === i && r === n) box(ctx, cx - 170, y - 32, 340, 42, { r: 10, fill: hexA(C.teal, 0.16) });
        [ra, rb, ro].forEach((v, j) => text(ctx, String(v), cx - 120 + j * 120, y, { size: 30, font: F.mono, weight: 500, align: 'center', color: v ? (j === 2 ? C.one : C.text) : C.faint }));
      }
      if (i < 2) {
        text(ctx, i === 0 ? 'switches in a row' : 'switches side by side', cx, 688, { size: 24, align: 'center', color: C.dim });
        seriesCircuit(ctx, cx - 20, 820, active === i ? a : 0, active === i ? b : 0, ty);
      } else {
        const ok = active === 2 ? eo(seg(g4.t, g4.at('Another way'), g4.at('Another way') + 0.6)) : 0;
        text(ctx, 'count the ones:', cx, 740, { size: 26, align: 'center', color: C.dim, alpha: Math.max(ok, 0.5) });
        text(ctx, 'odd → ON', cx, 800, { size: 46, font: F.disp, weight: 700, align: 'center', color: C.one, alpha: Math.max(ok, 0.35), ls: 2 });
        text(ctx, 'even → OFF', cx, 852, { size: 34, font: F.disp, weight: 600, align: 'center', color: C.dim, alpha: Math.max(ok, 0.35), ls: 2 });
      }
      ctx.restore();
    });
    if (g5.on) {
      const k = eo(seg(g5.t, 0.3, 1.1));
      ctx.save(); ctx.globalAlpha = k;
      box(ctx, 160, 380, 1600, 240, { r: 26, fill: '#0E1820F2', stroke: C.one, lw: 4 });
      text(ctx, 'XOR = odd detector', 960, 480, { size: 78, font: F.disp, weight: 700, align: 'center', color: C.one, ls: 2 });
      text(ctx, 'and SUM needs exactly an odd detector', 960, 560, { size: 40, align: 'center', color: C.text });
      ctx.restore();
    }
  };

  // ---- schematic scenes share a frame
  const SX = 70, SY = 150, SS = 1.03;
  function inSchem(ctx, fn) { ctx.save(); ctx.translate(SX, SY); ctx.scale(SS, SS); fn(); ctx.restore(); }
  function sidePanel(ctx, st, o = {}) {
    const x = 1470, y = 150, w = 400;
    box(ctx, x, y, w, o.h || 380, { r: 20, fill: C.panel });
    text(ctx, o.title || 'RIGHT NOW', x + 28, y + 50, { size: 26, font: F.disp, weight: 700, color: C.dim, ls: 2 });
    const n = st.A + st.B + st.C;
    [['A', st.A, C.A], ['B', st.B, C.B], ['Cin', st.C, C.Cin]].forEach(([l, v, col], i) => {
      text(ctx, l, x + 50 + i * 110, y + 105, { size: 30, font: F.disp, weight: 700, align: 'center', color: col });
      text(ctx, String(v), x + 50 + i * 110, y + 155, { size: 46, font: F.mono, weight: 600, align: 'center', color: v ? C.text : C.faint });
    });
    text(ctx, 'ones on', x + 28, y + 220, { size: 26, color: C.dim });
    countDots(ctx, x + 170, y + 212, n);
    text(ctx, String(n), x + 330, y + 226, { size: 44, font: F.mono, weight: 600, color: C.one });
    if (o.rules !== false) {
      text(ctx, n % 2 ? 'odd  → SUM 1' : 'even → SUM 0', x + 28, y + 290, { size: 32, font: F.mono, weight: 500, color: n % 2 ? C.one : C.faint });
      if (o.carry) text(ctx, n >= 2 ? '≥ 2  → CARRY 1' : '< 2  → CARRY 0', x + 28, y + 340, { size: 32, font: F.mono, weight: 500, color: n >= 2 ? C.CO : C.faint });
    }
  }
  function stepStates(seq, tt, per) {
    const i = Math.min(seq.length - 1, Math.max(0, Math.floor(tt / per)));
    const prev = seq[Math.max(0, i - 1)], cur = seq[i], kk = ease(seg(tt - i * per, 0, 0.35));
    return { st: evalFA(cur[0], cur[1], cur[2]), lev: { A: lerp(prev[0], cur[0], kk), B: lerp(prev[1], cur[1], kk), C: lerp(prev[2], cur[2], kk) }, i };
  }
  function ann(ctx, s, x, y, col, k, size = 26) {
    if (k <= 0) return;
    pill(ctx, s, x, y, { size, font: F.body, weight: 600, fill: '#0E1820EE', stroke: col, lw: 2, color: col, align: 'center', alpha: k });
  }

  S.sum = (ctx, lt, Q) => {
    const s1 = Q('s1'), s2 = Q('s2'), s3 = Q('s3');
    let st = evalFA(0, 0, 0), lev = null;
    if (s1.on && !s2.on) { const r = stepStates([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]], s1.t - 1.2, 1.8); st = r.st; lev = r.lev; }
    if (s2.on && !s3.on) { const r = stepStates([[1, 0, 0], [1, 0, 1], [0, 0, 0], [0, 0, 1]], s2.t, 2.2); st = r.st; lev = r.lev; }
    if (s3.on) { const r = stepStates([[1, 0, 0], [1, 1, 0], [1, 1, 1], [0, 1, 1], [1, 0, 1]], s3.t, s3.d / 5); st = r.st; lev = r.lev; }
    const ap = id => eo(seg(lt, ...id));
    const x2k = s2.on ? eo(seg(s2.t, 0, 1)) : 0;
    const vis = {
      _all: 0.06,
      iA: ap([0.2, 1]), iB: ap([0.2, 1]), wA: ap([0.4, 1.2]), wB: ap([0.4, 1.2]), x1: ap([0.6, 1.4]),
      wX: s1.on ? eo(seg(s1.t, 1, 2)) : 0,
      iC: x2k, wC: x2k, x2: x2k, wS: x2k, lS: x2k,
    };
    inSchem(ctx, () => {
      schematic(ctx, st, lt, vis, { lever: lev || st });
      ann(ctx, 'A XOR B: odd so far?', 560, 140, C.X, s1.on ? eo(seg(s1.t, 3, 4)) : 0);
      ann(ctx, 'Cin = 1 flips it', 760, 335, C.Cin, s2.on ? eo(seg(s2.p, 0.3, 0.45)) : 0);
    });
    sidePanel(ctx, st, { title: 'COUNT CHECK', rules: s2.on, carry: false, h: 330 });
  };

  S.carry = (ctx, lt, Q) => {
    const r1 = Q('r1'), r2 = Q('r2'), r3 = Q('r3'), r4 = Q('r4'), r5 = Q('r5');
    let row = [0, 0, 0], lev = null;
    let st;
    if (r2.on && !r3.on) { const r = stepStates([[0, 0, 0], [1, 1, 0]], r2.t, 1.5); st = r.st; lev = r.lev; }
    else if (r3.on && !r4.on) { const r = stepStates([[1, 1, 0], [1, 0, 1], [0, 1, 1]], r3.t, r3.d / 3); st = r.st; lev = r.lev; }
    else if (r4.on || r5.on) { const base = r4.s; const r = stepStates([[1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1], [1, 0, 0], [0, 0, 1], [0, 1, 1], [1, 1, 0], [1, 1, 1], [1, 0, 1]], lt - base, 2.2); st = r.st; lev = r.lev; }
    else st = evalFA(row[0], row[1], row[2]);
    const sumAlpha = 0.35;
    const k2 = r2.on ? eo(seg(r2.t, 0, 1.2)) : 0, k3 = r3.on ? eo(seg(r3.t, 0, 1.2)) : 0, k4 = r4.on ? eo(seg(r4.t, 0, 1.2)) : 0;
    const vis = {
      iA: 1, iB: 1, iC: 1, wA: 1, wB: 1, wC: 1, x1: 1, wX: 1,
      x2: sumAlpha, wS: sumAlpha, lS: sumAlpha,
      a1: k2, wAa: k2, wBa: k2,
      a2: k3, wXa: k3, wCa: k3,
      o1: k4, wN1: k4, wN2: k4, wCO: k4, lCO: k4,
    };
    const draw = { wAa: k2, wBa: k2, wXa: k3, wCa: k3, wN1: k4, wN2: k4, wCO: k4 };
    inSchem(ctx, () => {
      if (r5.on) { // pulse the reused XOR branch
        const pk = 0.5 + 0.5 * Math.sin(r5.t * 5);
        ctx.save(); ctx.strokeStyle = hexA(C.X, 0.35 * pk); ctx.lineWidth = 26; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
        ctx.beginPath(); ctx.moveTo(500, 200); ctx.lineTo(620, 200); ctx.lineTo(620, 420); ctx.lineTo(750, 420); ctx.stroke(); ctx.restore();
      }
      schematic(ctx, st, lt, vis, { lever: lev || st, draw });
      ann(ctx, 'way 1: A AND B', 800, 650, C.N, k2);
      ann(ctx, 'way 2: (A XOR B) AND Cin', 860, 375, C.N, k3);
      ann(ctx, 'either way → carry', 1060, 590, C.CO, k4);
      if (r5.on) ann(ctx, 'reused XOR output', 520, 330, C.X, eo(seg(r5.t, 0.3, 1)));
    });
    sidePanel(ctx, st, { title: 'COUNT CHECK', carry: true, h: 380 });
  };

  S.circuit = (ctx, lt, Q) => {
    const f1 = Q('f1');
    let idx = -1;
    for (let i = 0; i < 8; i++) if (Q('f' + (i + 2)).on) idx = i;
    let st = evalFA(0, 0, 0), lev = null;
    if (idx >= 0) {
      const cq = Q('f' + (idx + 2));
      const prev = bits(Math.max(0, idx - 1)), cur = bits(idx), kk = ease(seg(cq.t, 0, 0.35));
      st = evalFA(cur[0], cur[1], cur[2]);
      lev = { A: lerp(prev[0], cur[0], kk), B: lerp(prev[1], cur[1], kk), C: lerp(prev[2], cur[2], kk) };
    }
    const ap = eo(seg(f1.t, 0, 1));
    inSchem(ctx, () => { ctx.save(); ctx.globalAlpha = ap; schematic(ctx, st, lt, {}, { lever: lev || st }); ctx.restore(); });
    // compact truth table
    const x = 1470, y = 130, w = 400;
    box(ctx, x, y, w, 720, { r: 20, fill: C.panel });
    const cols = [['A', x + 60, C.A], ['B', x + 120, C.B], ['Cin', x + 185, C.Cin], ['C', x + 280, C.CO], ['S', x + 345, C.S]];
    cols.forEach(([h, cx, col]) => text(ctx, h, cx, y + 52, { size: 30, font: F.disp, weight: 700, align: 'center', color: col }));
    text(ctx, 'out', x + 312, y + 22, { size: 18, font: F.disp, weight: 600, align: 'center', color: C.dim, ls: 2 });
    ctx.fillStyle = C.line; ctx.fillRect(x + 236, y + 20, 2, 680);
    for (let r = 0; r < 8; r++) {
      const [a, b, c] = bits(r), s = evalFA(a, b, c), ry = y + 120 + r * 74;
      if (r === idx) box(ctx, x + 14, ry - 46, w - 28, 64, { r: 12, fill: hexA(C.teal, 0.18), stroke: C.teal, lw: 2 });
      const done = r < idx || (idx === 7 && r === 7);
      [a, b, c].forEach((v, j) => text(ctx, String(v), cols[j][1], ry, { size: 36, font: F.mono, align: 'center', color: v ? C.text : C.faint }));
      const show = r <= idx;
      text(ctx, show ? String(s.CO) : '·', cols[3][1], ry, { size: 36, font: F.mono, weight: 600, align: 'center', color: s.CO && show ? C.CO : C.faint });
      text(ctx, show ? String(s.S) : '·', cols[4][1], ry, { size: 36, font: F.mono, weight: 600, align: 'center', color: s.S && show ? C.one : C.faint });
      if (done) text(ctx, '✓', x + 385, ry, { size: 26, align: 'center', color: C.B });
    }
  };

  // ---- kit camera: map kit point (kx,ky) to screen (sx,sy) with scale s
  function kitCam(ctx, kx, ky, s, sx = 960, sy = 470) { ctx.translate(sx, sy); ctx.scale(s, s); ctx.translate(-kx, -ky); }
  const KITFULL = { kx: 900, ky: 450, s: 0.98, sx: 960, sy: 500 };
  function spot(ctx, rects, k) {
    // darken everything except rects (kit coordinates); ctx already in kit space
    if (k <= 0) return;
    ctx.save();
    ctx.beginPath(); ctx.rect(-2000, -2000, 6000, 6000);
    for (const [x, y, w, h] of rects) { ctx.moveTo(x, y); ctx.lineTo(x, y + h); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w, y); ctx.closePath(); }
    ctx.fillStyle = `rgba(6,12,16,${0.62 * k})`; ctx.fill('evenodd');
    for (const [x, y, w, h] of rects) box(ctx, x, y, w, h, { r: 14, stroke: hexA(C.teal, k), lw: 4 });
    ctx.restore();
  }
  S.kit = (ctx, lt, Q) => {
    const t2 = Q('t2'), t3 = Q('t3'), t4 = Q('t4'), t5 = Q('t5');
    let rect = null, label = null;
    if (t2.on && !t3.on) { rect = [30, 178, 200, 400]; label = ['power: +5V and GND', 235, 600]; }
    if (t3.on && !t4.on) { rect = [370, 718, 1150, 170]; label = ['logic switches', 1540, 790]; }
    if (t4.on && !t5.on) { rect = [370, 14, 1150, 160]; label = ['LEDs', 1540, 100]; }
    if (t5.on) { rect = [252, 180, 1504, 536]; label = ['breadboard', 1500, 740]; }
    const cur = [t2, t3, t4, t5].find(c => c.on && c.t < c.d) || t2;
    const sk = rect ? eo(seg(cur.t, 0, 0.6)) : 0;
    const swv = t3.on && !t4.on ? (Math.floor(t3.t / 1.6) % 2) : 0;
    const ledv = t4.on && !t5.on ? (Math.floor(t4.t / 1.2) % 2) : 0;
    ctx.save(); kitCam(ctx, KITFULL.kx, KITFULL.ky, KITFULL.s, KITFULL.sx, KITFULL.sy);
    const ka = eo(seg(lt, 0, 1));
    ctx.globalAlpha = ka;
    kit(ctx, { t: lt, power: 0, chips: 0, swForce: { 1: ease(seg(t3.t % 1.6, 0, 0.3)) * swv + (1 - ease(seg(t3.t % 1.6, 0, 0.3))) * (1 - swv) }, ledForce: { 1: ledv } });
    spot(ctx, rect ? [rect] : [], sk);
    if (t3.on && !t4.on) {
      pill(ctx, swv ? 'S1 up → +5V = 1' : 'S1 down → 0V = 0', 420, 680, { size: 26, font: F.body, weight: 600, fill: '#0E1820F0', stroke: C.teal, color: swv ? C.one : C.dim, align: 'center' });
    }
    if (t4.on && !t5.on) pill(ctx, ledv ? 'L1 gets +5V → lit' : 'L1 gets 0V → dark', 420, 205, { size: 26, font: F.body, weight: 600, fill: '#0E1820F0', stroke: C.teal, color: ledv ? C.led : C.dim, align: 'center' });
    if (t2.on && !t3.on) {
      const k = eo(seg(t2.p, 0.4, 0.55));
      pill(ctx, '5 V = 1', 300, 330, { size: 28, font: F.mono, weight: 600, fill: '#0E1820F0', stroke: C.red, color: C.one, alpha: k });
      pill(ctx, '0 V = 0', 300, 450, { size: 28, font: F.mono, weight: 600, fill: '#0E1820F0', stroke: '#888', color: C.dim, alpha: k });
    }
    ctx.restore();
    if (label && sk > 0) { /* label inside kit space handled by pills */ }
  };

  S.breadboard = (ctx, lt, Q) => {
    const d1 = Q('d1'), d2 = Q('d2'), d3 = Q('d3'), d4 = Q('d4');
    // camera: zoom on the left part, pull back for rails
    const z1 = { kx: 600, ky: 455, s: 1.75 }, z2 = { kx: 900, ky: 440, s: 1.08 };
    const zk = d4.on ? ease(seg(d4.t, 0, 1.6)) : 0;
    const zin = ease(seg(lt, 0.2, 2.2));
    const kx = lerp(lerp(900, z1.kx, zin), z2.kx, zk), ky = lerp(lerp(450, z1.ky, zin), z2.ky, zk), s = lerp(lerp(0.98, z1.s, zin), z2.s, zk);
    const xr = d1.on ? eo(seg(d1.p, 0.55, 0.85)) : 0;
    const hiK = d2.on ? 0.5 + 0.5 * Math.sin(d2.t * 4) : 0;
    const showWire = d2.on ? eo(seg(d2.p, 0.45, 0.6)) : 0;
    ctx.save(); kitCam(ctx, kx, ky, s, 960, 470);
    kit(ctx, {
      t: lt, power: 0, chips: d3.on ? (i => ({ alpha: i === 0 ? eo(seg(d3.t, 0.5, 1.3)) : 0 })) : 0,
      xray: xr, xrayOpt: { hiCol: d2.on && !d3.on ? 8 : -1, hiK: d2.on ? 1 : 0, railK: d4.on ? eo(seg(d4.p, 0.15, 0.3)) : 0 },
    });
    if (d2.on && !d3.on) {
      // a strip of five glows; a demo wire plugged into it
      ctx.save(); ctx.strokeStyle = hexA(C.one, 0.5 + 0.5 * hiK); ctx.lineWidth = 4;
      box(ctx, hx(8) - 16, ROWY.a - 16, 32, ROWY.e - ROWY.a + 32, { r: 10, stroke: C.one, lw: 4 }); ctx.restore();
      jumper(ctx, { a: { x: hx(8), y: ROWY.b }, b: { x: hx(14), y: ROWY.c }, col: C.A, bow: 0.3 }, { draw: showWire, hot: showWire >= 1, flow: true, t: lt });
      if (showWire >= 1) for (const r of 'acde') { ctx.fillStyle = hexA(C.one, 0.6 + 0.4 * hiK); ctx.beginPath(); ctx.arc(hx(8), ROWY[r], 7, 0, TAU); ctx.fill(); }
      pill(ctx, 'these 5 holes = one connection', hx(8), ROWY.a - 52, { size: 20, font: F.body, weight: 600, fill: '#0E1820F0', stroke: C.one, color: C.one, align: 'center', alpha: eo(seg(d2.p, 0.15, 0.3)) });
    }
    if (d3.on && !d4.on) {
      const gk = eo(seg(d3.t, 0, 0.6));
      ctx.save(); ctx.globalAlpha = gk;
      ctx.fillStyle = hexA(C.teal, 0.25 + 0.15 * Math.sin(d3.t * 4)); ctx.fillRect(hx(1) - 20, 438, hx(20) - hx(1), 22);
      pill(ctx, 'groove: top and bottom halves are NOT connected', hx(19), 450, { size: 18, font: F.body, weight: 600, fill: '#0E1820F0', stroke: C.teal, color: C.teal, align: 'center' });
      ctx.restore();
      const ck = eo(seg(d3.p, 0.55, 0.7));
      if (ck > 0) for (let n = 1; n <= 14; n++) { const p = pinHole(CHIPS[0], n); ctx.save(); ctx.globalAlpha = ck; ctx.strokeStyle = n <= 7 ? C.teal : C.one; ctx.lineWidth = 3; ctx.strokeRect(p.x - 12, n <= 7 ? ROWY.f - 12 : ROWY.a - 12, 24, n <= 7 ? ROWY.j - ROWY.f + 24 : ROWY.e - ROWY.a + 24); ctx.restore(); }
      if (ck > 0) pill(ctx, 'each leg gets its own strip', hx(8), ROWY.j + 50, { size: 20, font: F.body, weight: 600, fill: '#0E1820F0', stroke: C.teal, color: C.teal, align: 'center', alpha: ck });
    }
    if (d4.on) {
      const k = eo(seg(d4.p, 0.2, 0.35));
      pill(ctx, '+ rail: every hole connected → +5V', 1100, 160, { size: 22, font: F.body, weight: 600, fill: '#0E1820F0', stroke: C.rail, color: '#FF8A80', align: 'center', alpha: k });
      pill(ctx, '− rail: every hole connected → GND', 1100, 735, { size: 22, font: F.body, weight: 600, fill: '#0E1820F0', stroke: C.railB, color: '#8EB4FF', align: 'center', alpha: k });
      const sk = eo(seg(d4.p, 0.72, 0.85));
      if (sk > 0) {
        ctx.save(); ctx.globalAlpha = sk;
        jumper(ctx, { a: { x: hx(23), y: ROWY['T+'] }, b: { x: hx(25), y: ROWY['T+'] }, col: C.red, bow: 0.4 }, { draw: 1 });
        pill(ctx, 'split rail? bridge it', hx(24), 130, { size: 20, font: F.body, weight: 600, fill: '#0E1820F0', stroke: C.one, color: C.one, align: 'center' });
        ctx.restore();
      }
    }
    ctx.restore();
  };

  // ---- big chip pinout
  function bigChip(ctx, cx, cy, o = {}) {
    const w = o.w || 980, h = o.h || 300, pinW = w / 7;
    ctx.save(); ctx.translate(cx, cy);
    ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
    const pinX = n => (n <= 7 ? -w / 2 + pinW * (n - 0.5) : -w / 2 + pinW * (14 - n + 0.5));
    for (let n = 1; n <= 14; n++) {
      const x = pinX(n), bottom = n <= 7;
      const hi = o.hi && o.hi[n];
      ctx.fillStyle = hi || C.pin;
      ctx.fillRect(x - 18, bottom ? h / 2 - 4 : -h / 2 - 56, 36, 60);
      if (o.nums !== false) {
        const k = o.numK ? o.numK(n) : 1;
        text(ctx, String(n), x, bottom ? h / 2 + 100 : -h / 2 - 78, { size: 40, font: F.mono, weight: 600, align: 'center', color: hi || C.text, alpha: k });
      }
    }
    box(ctx, -w / 2, -h / 2, w, h, { r: 14, fill: C.chip, stroke: '#3A3A42', lw: 3 });
    ctx.fillStyle = '#2E2E35'; ctx.beginPath(); ctx.arc(-w / 2, 0, 34, -Math.PI / 2, Math.PI / 2); ctx.fill();
    ctx.fillStyle = '#45454D'; ctx.beginPath(); ctx.arc(-w / 2 + 50, h / 2 - 46, 12, 0, TAU); ctx.fill();
    if (o.label) text(ctx, o.label, 0, o.gates ? -h / 2 + 46 : 16, { size: o.gates ? 34 : 64, font: F.mono, weight: 600, align: 'center', color: '#E2E5E8' });
    if (o.gates) {
      const gk = o.gates;
      // gate 1 & 2 (bottom row), gates 3 & 4 faint (top row, pointing left)
      const draw = (inA, inB, out, top, al, gy) => {
        const xa = pinX(inA), xb = pinX(inB), xo = pinX(out), gx = (xb + xo) / 2;
        const pe = top ? -h / 2 : h / 2, ya = top ? gy + 16 : gy - 16, yb = top ? gy - 16 : gy + 16;
        ctx.save(); ctx.globalAlpha *= al; ctx.strokeStyle = '#C9D3DA'; ctx.lineWidth = 4; ctx.lineJoin = 'round';
        ctx.beginPath(); ctx.moveTo(xa, pe); ctx.lineTo(xa, ya); ctx.lineTo(gx - 40, ya); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(xb, pe); ctx.lineTo(xb, yb); ctx.lineTo(gx - 40, yb); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(gx + 40, gy); ctx.lineTo(xo, gy); ctx.lineTo(xo, pe); ctx.stroke();
        gate(ctx, o.kind, gx, gy, { scale: 0.8, name: false, fill: '#2A2A31' });
        ctx.restore();
      };
      draw(1, 2, 3, false, gk, 50); draw(4, 5, 6, false, gk, 50);
      draw(13, 12, 11, true, gk * 0.3, -50); draw(10, 9, 8, true, gk * 0.3, -50);
    }
    ctx.restore();
    return pinX;
  }
  S.chips = (ctx, lt, Q) => {
    const p1 = Q('p1'), p2 = Q('p2'), p3 = Q('p3'), p4 = Q('p4');
    if (!p2.on) {
      const info = [['74LS86', 'XOR', C.X, 'four XOR gates'], ['74LS08', 'AND', C.N, 'four AND gates'], ['74LS32', 'OR', C.CO, 'four OR gates']];
      const chAt = [p1.at('The seventy four eighty'), p1.at('The seventy four oh'), p1.at('The seventy four thirty')];
      info.forEach(([nm, kind, col, sub], i) => {
        const k = eo(seg(p1.t, chAt[i], chAt[i] + 0.7));
        const cx = 400 + i * 560;
        ctx.save(); ctx.globalAlpha = k;
        ctx.translate(cx, 420); ctx.scale(0.42, 0.42);
        bigChip(ctx, 0, 0, { label: nm, nums: false });
        ctx.restore();
        ctx.save(); ctx.globalAlpha = k;
        gate(ctx, kind, cx, 620, { scale: 0.9, name: false, stroke: col });
        text(ctx, kind, cx, 730, { size: 48, font: F.disp, weight: 700, align: 'center', color: col, ls: 3 });
        text(ctx, sub, cx, 780, { size: 28, align: 'center', color: C.dim });
        ctx.restore();
      });
      text(ctx, 'LS or HC, both fine', 960, 200, { size: 32, align: 'center', color: C.dim, alpha: eo(seg(p1.t, p1.at('You may see'), p1.at('You may see') + 0.6)) });
      return;
    }
    // p2..p4: one big chip
    const mv = p4.on ? ease(seg(p4.t, 0, 1.2)) : 0;
    const counter = p2.on ? seg(p2.t, p2.at('pin one is'), p2.at('up to pin fourteen') + 1.2) * 14 : 14;
    const hi = {};
    if (p3.on) { const k = 0.5 + 0.5 * Math.sin(p3.t * 5); hi[14] = mix(C.red, '#FF8A80', k); hi[7] = mix('#5A6670', '#B8C4CC', k); }
    const cy = lerp(470, 430, mv);
    ctx.save();
    const pinX = bigChip(ctx, 960, cy, {
      label: p4.on ? '' : '74LS86', hi, gates: p4.on ? eo(seg(p4.t, 0.6, 1.6)) : 0, kind: 'XOR',
      numK: n => eo(seg(counter, n - 1, n - 0.4)),
    });
    ctx.restore();
    if (p2.on && !p3.on) {
      const nk = eo(seg(p2.t, p2.at('With the notch'), p2.at('With the notch') + 0.6));
      pill(ctx, '◀ notch = left', 420, cy - 220, { size: 30, font: F.body, weight: 600, fill: C.panel2, color: C.teal, alpha: nk });
      // a dot that travels the pin path
      if (counter > 0 && counter < 14) {
        const n = Math.min(14, Math.floor(counter) + 1), x = 960 + pinX(n), y = cy + (n <= 7 ? 260 : -250);
        ctx.fillStyle = C.one; ctx.beginPath(); ctx.arc(x, y - 35, 10, 0, TAU); ctx.fill();
      }
      if (counter > 7.2) arrow(ctx, 960 + pinX(7) + 70, cy + 120, 960 + pinX(7) + 70, cy - 120, C.one, 4);
    }
    if (p3.on && !p4.on) {
      const k = eo(seg(p3.t, 0.3, 1));
      pill(ctx, 'pin 14 = VCC (+5V)', 960 + pinX(14), cy - 300, { size: 30, font: F.body, weight: 600, fill: C.panel2, stroke: C.red, color: '#FF8A80', align: 'center', alpha: k });
      pill(ctx, 'pin 7 = GND', 960 + pinX(7), cy + 310, { size: 30, font: F.body, weight: 600, fill: C.panel2, stroke: '#999', color: C.text, align: 'center', alpha: k });
    }
    if (p4.on) {
      const k = eo(seg(p4.t, p4.at('Gate one'), p4.at('Gate one') + 0.6));
      pill(ctx, 'gate 1:  1, 2 → 3', 960 + pinX(2), cy + 310, { size: 28, font: F.mono, weight: 600, fill: C.panel2, stroke: C.teal, color: C.teal, align: 'center', alpha: k });
      pill(ctx, 'gate 2:  4, 5 → 6', 960 + pinX(5), cy + 310, { size: 28, font: F.mono, weight: 600, fill: C.panel2, stroke: C.teal, color: C.teal, align: 'center', alpha: eo(seg(p4.t, p4.at('Gate two'), p4.at('Gate two') + 0.6)) });
      const sk = eo(seg(p4.p, 0.12, 0.3));
      text(ctx, 'same layout on 7486 · 7408 · 7432', 960, 150, { size: 38, font: F.disp, weight: 600, align: 'center', color: C.one, alpha: sk, ls: 1 });
    }
  };

  // ---- build steps
  const BUILD = { kx: 900, ky: 450, s: 0.86, sx: 818, sy: 455 };
  function buildPanel(ctx, step, o = {}) {
    const x = 1612, y = 70, w = 290;
    box(ctx, x, y, w, 740, { r: 18, fill: C.panel });
    text(ctx, o.title || 'BUILD STEPS', x + 22, y + 44, { size: 24, font: F.disp, weight: 700, color: C.dim, ls: 2 });
    STEPS.forEach((s, i) => {
      const yy = y + 100 + i * 90, done = s.n < step, cur = s.n === step;
      if (cur) box(ctx, x + 10, yy - 40, w - 20, 76, { r: 12, fill: hexA(C.teal, 0.16), stroke: C.teal, lw: 2 });
      ctx.beginPath(); ctx.arc(x + 42, yy - 2, 18, 0, TAU); ctx.fillStyle = done ? C.B : cur ? C.teal : C.panel2; ctx.fill();
      text(ctx, done ? '✓' : String(s.n), x + 42, yy + 7, { size: 22, font: F.mono, weight: 600, align: 'center', color: done || cur ? '#0E1820' : C.dim });
      text(ctx, s.short, x + 74, yy + 8, { size: 28, font: F.disp, weight: 600, color: cur ? C.text : done ? C.dim : C.faint, ls: 1 });
    });
  }
  function stepStrip(ctx, s, sub, k) {
    if (k <= 0) return;
    ctx.save(); ctx.globalAlpha = k;
    box(ctx, 40, 852, 1862, 82, { r: 16, fill: C.panel });
    text(ctx, s, 66, 905, { size: 34, font: F.disp, weight: 700, color: C.teal, ls: 1 });
    ctx.font = `700 34px ${F.disp}`; ctx.letterSpacing = '1px';
    const w = ctx.measureText(s).width; ctx.letterSpacing = '0px';
    text(ctx, sub, 66 + w + 28, 904, { size: 27, color: C.text });
    ctx.restore();
  }
  S.build = (ctx, lt, Q) => {
    const cues = ['w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'w7', 'w8', 'w9'].map(Q);
    const stepOfCue = [1, 2, 3, 3.5, 4, 5, 6, 7, 8];
    let ci = 0; cues.forEach((c, i) => { if (c.on) ci = i; });
    const step = stepOfCue[ci], cq = cues[ci];
    const chipK = cues[0].on ? i => ({ alpha: eo(seg(cues[0].p, 0.2 + i * 0.15, 0.32 + i * 0.15)), lift: (1 - eo(seg(cues[0].p, 0.2 + i * 0.15, 0.32 + i * 0.15))) * 60 }) : 1;
    const wiresOf = s => WIRES.map((w, i) => (w.step === s ? i : -1)).filter(i => i >= 0);
    const curList = wiresOf(step);
    // each wire starts when the narration names it; wires sharing a phrase follow each other
    const startOf = i => { const w = WIRES[i]; const same = curList.filter(j => WIRES[j].say === w.say); return cq.at(w.say) + same.indexOf(i) * 0.75; };
    const wireState = (i, w) => {
      if (w.step < step) return { draw: 1, alpha: step === 8 ? 1 : 0.75 };
      if (w.step > step) return null;
      const t0 = startOf(i);
      return { draw: ease(seg(cq.t, t0, t0 + 1.1)), alpha: 1 };
    };
    ctx.save(); kitCam(ctx, BUILD.kx, BUILD.ky, BUILD.s, BUILD.sx, BUILD.sy);
    kit(ctx, { t: lt, power: 0, chips: chipK, wires: wireState, swNet: KIT_SWNET, swCol: KIT_SWCOL });
    // tags on the endpoints of the current wires
    if (step >= 2 && step <= 7) curList.forEach((i, k) => {
      const w = WIRES[i], t0 = startOf(i);
      const tk = eo(seg(cq.t, t0 - 0.3, t0)) * (1 - eo(seg(cq.t, t0 + 2.6, t0 + 3.2)));
      if (step === 2 && k >= 2) return; // power pins tagged collectively below
      if (tk <= 0) return;
      const up = w.b.y < 470;
      pinTag(ctx, w.a.x, w.a.y, w.from, { t: lt, alpha: tk, col: w.col === C.black ? '#BBC' : w.col === C.S ? '#FFF' : w.col, up: w.a.y < 470 && w.a.y > 200 ? true : w.a.y > 470 });
      pinTag(ctx, w.b.x, w.b.y, w.to, { t: lt, alpha: tk, col: w.col === C.black ? '#BBC' : w.col === C.S ? '#FFF' : w.col, up: up, dx: w.b.y < 200 ? 0 : 0 });
    });
    if (step === 2) {
      const k = eo(seg(cq.t, cq.at('for every chip'), cq.at('for every chip') + 0.5)) * (1 - eo(seg(cq.p, 0.92, 1)));
      for (const ch of CHIPS) {
        const p14 = pinHole(ch, 14), p7 = pinHole(ch, 7);
        pinTag(ctx, p14.x, p14.y, 'pin 14', { t: lt, alpha: k, col: '#FF8A80', up: true, dy: -30 });
        pinTag(ctx, p7.x, p7.y, 'pin 7', { t: lt, alpha: k, col: '#CCD', up: false, dy: 30 });
      }
    }
    if (step === 1) {
      const k = eo(seg(cq.p, 0.75, 0.85));
      for (const ch of CHIPS) pill(ctx, 'notch ◀', hx(ch.c0) - 10, 386, { size: 18, font: F.body, weight: 600, fill: '#0E1820F0', stroke: C.teal, color: C.teal, align: 'center', alpha: k });
    }
    if (step === 7) {
      const k = eo(seg(cq.p, 0.75, 0.88));
      pill(ctx, 'CARRY · SUM  → reads as a binary number', (LEDX(LED_CO) + LEDX(LED_S)) / 2 + 200, 30, { size: 20, font: F.body, weight: 600, fill: '#0E1820F0', stroke: C.one, color: C.one, align: 'center', alpha: k });
    }
    ctx.restore();
    buildPanel(ctx, Math.floor(step));
    const desc = {
      1: ['STEP 1', 'Chips across the groove, notches left: 7486 (XOR) · 7408 (AND) · 7432 (OR)'],
      2: ['STEP 2', '+5V → red rail · GND → blue rail · each chip: pin 14 → red, pin 7 → blue'],
      3: ['STEP 3', 'Switch 1 (A) → XOR pin 1 · Switch 2 (B) → XOR pin 2'],
      3.5: ['STEP 3', 'XOR pin 1 strip → AND pin 1 · XOR pin 2 strip → AND pin 2'],
      4: ['STEP 4', 'XOR pin 3 → XOR pin 4 · Switch 3 (Cin) → XOR pin 5 · pin 6 = SUM'],
      5: ['STEP 5', 'XOR pin 3 → AND pin 4 · XOR pin 5 strip (Cin) → AND pin 5'],
      6: ['STEP 6', 'AND pin 3 → OR pin 1 · AND pin 6 → OR pin 2 · OR pin 3 = CARRY OUT'],
      7: ['STEP 7', `OR pin 3 → LED ${LED_CO} (left, Carry) · XOR pin 6 → LED ${LED_S} (right, Sum)`],
      8: ['DONE', '20 wires: 8 power + 12 signal. Check each against the list before power-on.'],
    }[step];
    stepStrip(ctx, desc[0], desc[1], eo(seg(cq.t, 0, 0.5)));
  };

  // ---- power on and test
  S.test = (ctx, lt, Q) => {
    const x1 = Q('x1'), x2 = Q('x2');
    const power = x1.on ? eo(seg(x1.t, 1.0, 1.3)) : 0;
    let idx = 0, lev = { A: 0, B: 0, C: 0 };
    if (x2.on) {
      const per = x2.d / 8.3;
      idx = Math.min(7, Math.floor(x2.t / per));
      const prev = bits(Math.max(0, idx - 1)), cur = bits(idx), kk = ease(seg(x2.t - idx * per, 0, 0.35));
      lev = { A: lerp(prev[0], cur[0], kk), B: lerp(prev[1], cur[1], kk), C: lerp(prev[2], cur[2], kk) };
    }
    const [a, b, c] = bits(idx), st = evalFA(a, b, c);
    ctx.save(); kitCam(ctx, BUILD.kx, BUILD.ky, BUILD.s, BUILD.sx, BUILD.sy);
    kit(ctx, { t: lt, power, st, lever: lev, wires: () => ({ draw: 1 }), ledNet: KIT_LEDNET, swNet: KIT_SWNET, swCol: KIT_SWCOL });
    if (x1.on && !x2.on) pill(ctx, 'power ON', 130, 160, { size: 22, font: F.body, weight: 600, fill: '#0E1820F0', stroke: '#4DFF7A', color: '#4DFF7A', align: 'center', alpha: power });
    ctx.restore();
    // truth table panel
    const x = 1612, y = 70, w = 290;
    box(ctx, x, y, w, 740, { r: 18, fill: C.panel });
    text(ctx, 'TEST ALL 8', x + 22, y + 44, { size: 24, font: F.disp, weight: 700, color: C.dim, ls: 2 });
    const cols = [['A', x + 40, C.A], ['B', x + 85, C.B], ['Ci', x + 130, C.Cin], ['n', x + 180, C.dim], ['C', x + 222, C.CO], ['S', x + 260, C.S]];
    cols.forEach(([h, cx, col]) => text(ctx, h, cx, y + 92, { size: 26, font: F.disp, weight: 700, align: 'center', color: col }));
    ctx.fillStyle = C.line; ctx.fillRect(x + 156, y + 64, 2, 640); ctx.fillRect(x + 202, y + 64, 2, 640);
    for (let r = 0; r < 8; r++) {
      const [ra, rb, rc] = bits(r), s = evalFA(ra, rb, rc), ry = y + 150 + r * 72;
      const cur = x2.on && r === idx;
      if (cur) box(ctx, x + 12, ry - 42, w - 24, 60, { r: 10, fill: hexA(C.teal, 0.18), stroke: C.teal, lw: 2 });
      const shown = x2.on && r <= idx;
      [ra, rb, rc].forEach((v, j) => text(ctx, String(v), cols[j][1], ry, { size: 30, font: F.mono, align: 'center', color: v ? C.text : C.faint }));
      text(ctx, String(ra + rb + rc), cols[3][1], ry, { size: 30, font: F.mono, align: 'center', color: C.dim });
      text(ctx, shown ? String(s.CO) : '·', cols[4][1], ry, { size: 30, font: F.mono, weight: 600, align: 'center', color: shown && s.CO ? C.CO : C.faint });
      text(ctx, shown ? String(s.S) : '·', cols[5][1], ry, { size: 30, font: F.mono, weight: 600, align: 'center', color: shown && s.S ? C.one : C.faint });
    }
    const n = a + b + c;
    stepStrip(ctx, x2.on ? `A=${a}  B=${b}  Cin=${c}` : 'PREDICT FIRST',
      x2.on ? `${n} on → ${n % 2 ? 'odd → SUM on' : 'even → SUM off'} · ${n >= 2 ? 'two or more → CARRY on' : 'fewer than two → CARRY off'}  →  lights read ${st.CO}${st.S}` : 'odd count → SUM · two or more → CARRY', eo(seg(lt, 0.3, 1)));
  };

  // ---- troubleshooting
  S.debug = (ctx, lt, Q) => {
    const cards = [
      ['e2', 'Nothing lights at all', 'Every chip: pin 14 to +5V, pin 7 to GND. Rails bridged? Kit switched on?', C.red],
      ['e3', 'A chip gets hot', 'It is in backwards. Power off now, check the notch faces left.', C.X],
      ['e4', 'Sum right, Carry wrong (or reverse)', 'Test one gate at a time: move an LED wire to pin 3 or pin 6 and check that gate’s rule.', C.teal],
      ['e5', 'An output stuck on', 'A floating input reads as 1 on LS chips: look for a wire in the wrong strip. HC chips: tie pins 9, 10, 12, 13 to GND.', C.CO],
    ];
    text(ctx, 'Check in this order', 120, 130, { size: 44, font: F.disp, weight: 700, color: C.text, ls: 1, alpha: eo(seg(lt, 0.2, 1)) });
    let cur = -1; cards.forEach((c, i) => { if (Q(c[0]).on) cur = i; });
    cards.forEach(([id, title, body, col], i) => {
      const q = Q(id);
      if (!q.on) return;
      const k = eo(seg(q.t, 0, 0.7));
      const x = 120 + (i % 2) * 860, y = 180 + Math.floor(i / 2) * 360;
      ctx.save(); ctx.globalAlpha = k * (cur === i ? 1 : 0.55);
      box(ctx, x, y + (1 - k) * 30, 820, 320, { r: 22, fill: C.panel, stroke: cur === i ? col : C.line, lw: cur === i ? 4 : 2 });
      ctx.beginPath(); ctx.arc(x + 60, y + 68, 28, 0, TAU); ctx.fillStyle = col; ctx.fill();
      text(ctx, String(i + 1), x + 60, y + 80, { size: 32, font: F.mono, weight: 600, align: 'center', color: '#0E1820' });
      text(ctx, title, x + 110, y + 80, { size: 40, font: F.disp, weight: 700, color: C.text });
      para(ctx, body, x + 40, y + 150, 740, { size: 30, color: C.dim, lh: 44 });
      ctx.restore();
    });
  };

  // ---- recap + ripple adder
  S.recap = (ctx, lt, Q) => {
    const z1 = Q('z1'), z2 = Q('z2'), z3 = Q('z3');
    const out = z3.on ? ease(seg(z3.t, 0, 0.8)) : 0;
    if (out < 1) {
      ctx.save(); ctx.globalAlpha = 1 - out;
      const k1 = eo(seg(z1.t, 0, 1));
      const n = Math.floor(lt / 1.4) % 8, [a, b, c] = bits(n);
      ctx.save(); ctx.globalAlpha *= k1; faBox(ctx, 640, 470, 0.85, evalFA(a, b, c), { A: a, B: b, C: c }, { t: lt }); ctx.restore();
      if (z2.on) {
        const ka = eo(seg(z2.p, 0.05, 0.2)), kb = eo(seg(z2.p, 0.45, 0.6));
        ctx.save(); ctx.globalAlpha *= ka;
        box(ctx, 1120, 260, 700, 200, { r: 20, fill: C.panel, stroke: C.one, lw: 3 });
        text(ctx, 'SUM = odd count', 1150, 330, { size: 50, font: F.disp, weight: 700, color: C.one, ls: 1 });
        text(ctx, 'A XOR B XOR Cin', 1150, 400, { size: 36, font: F.mono, color: C.text });
        text(ctx, 'two XOR gates', 1150, 440, { size: 26, color: C.dim });
        ctx.restore();
        ctx.save(); ctx.globalAlpha *= kb;
        box(ctx, 1120, 500, 700, 230, { r: 20, fill: C.panel, stroke: C.CO, lw: 3 });
        text(ctx, 'CARRY = two or more', 1150, 570, { size: 50, font: F.disp, weight: 700, color: C.CO, ls: 1 });
        text(ctx, '(A AND B) OR', 1150, 635, { size: 34, font: F.mono, color: C.text });
        text(ctx, '(Cin AND (A XOR B))', 1150, 680, { size: 34, font: F.mono, color: C.text });
        text(ctx, 'two AND gates + one OR gate', 1150, 716, { size: 26, color: C.dim });
        ctx.restore();
      }
      ctx.restore();
    }
    if (z3.on) {
      // 4-bit ripple adder: 0110 + 0111 = 1101
      const A = [0, 1, 1, 0], B = [0, 1, 1, 1]; // index 0 = MSB
      const k = eo(seg(z3.t, 0.4, 1.4));
      const prog = seg(z3.p, 0.25, 0.75) * 4; // columns processed from the right
      ctx.save(); ctx.globalAlpha = k;
      text(ctx, '0110 + 0111  (6 + 7)', 960, 170, { size: 46, font: F.mono, weight: 600, align: 'center', color: C.text });
      let carry = 0; const sums = [], carries = [];
      for (let col = 3; col >= 0; col--) { const s = evalFA(A[col], B[col], carry); sums[col] = s.S; carries[col] = carry; carry = s.CO; }
      const finalCarry = carry;
      for (let col = 0; col < 4; col++) {
        const x = 330 + col * 400, y = 430, done = 3 - col < prog;
        const active = Math.floor(prog) === 3 - col;
        box(ctx, x - 130, y - 110, 260, 220, { r: 20, fill: C.panel, stroke: active ? C.one : done ? C.teal : C.line, lw: active ? 4 : 2 });
        text(ctx, 'FA', x, y + 22, { size: 64, font: F.disp, weight: 700, align: 'center', color: done ? C.teal : C.dim, ls: 3 });
        text(ctx, `A=${A[col]}`, x - 60, y - 150, { size: 30, font: F.mono, align: 'center', color: C.A });
        text(ctx, `B=${B[col]}`, x + 60, y - 150, { size: 30, font: F.mono, align: 'center', color: C.B });
        arrow(ctx, x - 60, y - 135, x - 60, y - 112, C.A, 3, 10); arrow(ctx, x + 60, y - 135, x + 60, y - 112, C.B, 3, 10);
        lamp(ctx, x, y + 180, done ? sums[col] : 0, { r: 30 });
        text(ctx, done ? String(sums[col]) : '?', x, y + 270, { size: 50, font: F.mono, weight: 600, align: 'center', color: done ? (sums[col] ? C.one : C.faint) : C.faint });
        // carry arrow from the right neighbour
        if (col < 3) {
          const cv = carries[col], cd = 3 - (col + 1) < prog;
          sigWire(ctx, [[x + 270, y], [x + 132, y]], C.CO, cd ? cv : 0, lt, { lw: 6 });
          if (cd) text(ctx, 'carry ' + cv, x + 200, y - 18, { size: 24, font: F.mono, align: 'center', color: cv ? C.CO : C.faint });
        }
      }
      text(ctx, 'Cin = 0', 330 + 3 * 400 + 210, 440, { size: 26, font: F.mono, color: C.faint });
      if (prog >= 4) {
        lamp(ctx, 120, 610, finalCarry, { r: 30 });
        text(ctx, String(finalCarry), 120, 700, { size: 50, font: F.mono, weight: 600, align: 'center', color: finalCarry ? C.CO : C.faint });
        sigWire(ctx, [[200, 430], [120, 430], [120, 570]], C.CO, finalCarry, lt, { lw: 6 });
      }
      const ek = eo(seg(z3.p, 0.78, 0.9));
      text(ctx, '= 1101  (13)', 960, 820, { size: 54, font: F.mono, weight: 600, align: 'center', color: C.one, alpha: ek });
      ctx.restore();
      const fk = eo(seg(z3.p, 0.9, 1));
      text(ctx, 'You built the first column.', 960, 900, { size: 46, font: F.disp, weight: 700, align: 'center', color: C.teal, alpha: fk, ls: 2 });
    }
  };

  // ======================================================================
  //                        frame composition
  // ======================================================================
  const TL = () => window.TIMELINE;
  function locate(t) {
    const tl = TL();
    let sc = tl.scenes[0];
    for (const s of tl.scenes) if (t >= s.start) sc = s;
    return { sc, lt: t - sc.start };
  }
  function cueFn(sc, lt) {
    const map = {};
    sc.cues.forEach(c => (map[c.id] = c));
    return id => {
      const c = map[id];
      if (!c) return { on: false, t: 0, p: 0, s: 0, d: 1, at: () => 0 };
      const at = sub => { const i = c.text.indexOf(sub); if (i < 0) console.warn('phrase not found', id, sub); return i < 0 ? 0 : (i / c.text.length) * c.speech; };
      return { on: lt >= c.start, t: Math.max(0, lt - c.start), p: clamp((lt - c.start) / c.dur), s: c.start, d: c.dur, at };
    };
  }
  // subtitles: split the cue's text into sentence chunks timed by character count
  function captionAt(sc, lt) {
    let cue = null;
    for (const c of sc.cues) if (lt >= c.start) cue = c;
    if (!cue) return null;
    const tt = lt - cue.start;
    if (tt > cue.speech + 0.6) return null;
    const parts = cue.text.match(/[^.?!:]+[.?!:]+["']?|[^.?!:]+$/g).map(s => s.trim());
    const chunks = [];
    for (const p of parts) {
      if (p.length > 110 && p.includes(',')) {
        const sub = p.split(/(?<=,)\s/); let cur = '';
        for (const s of sub) { if ((cur + ' ' + s).length > 95 && cur) { chunks.push(cur); cur = s; } else cur = cur ? cur + ' ' + s : s; }
        if (cur) chunks.push(cur);
      } else chunks.push(p);
    }
    const total = chunks.reduce((a, s) => a + s.length, 0);
    let acc = 0;
    for (const ch of chunks) { acc += ch.length; if (tt <= (acc / total) * cue.speech) return ch; }
    return chunks[chunks.length - 1];
  }
  function drawCaption(ctx, s) {
    if (!s) return;
    ctx.save();
    font(ctx, 36, F.body, 400);
    const lines = wrap(ctx, s, 1560);
    const lh = 48, h = lines.length * lh + 30, y0 = 1062 - h;
    const w = Math.max(...lines.map(l => ctx.measureText(l).width)) + 60;
    box(ctx, 960 - w / 2, y0, w, h, { r: 14, fill: 'rgba(6,11,15,0.82)' });
    lines.forEach((l, i) => text(ctx, l, 960, y0 + 50 + i * lh, { size: 36, align: 'center', color: '#F4F7F9' }));
    ctx.restore();
  }
  function drawFrame(ctx, t, opt = {}) {
    const tl = TL();
    t = clamp(t, 0, tl.total);
    const { sc, lt } = locate(t);
    ctx.save();
    ctx.setTransform(opt.scale || 1, 0, 0, opt.scale || 1, 0, 0);
    ctx.fillStyle = C.bg; ctx.fillRect(0, 0, W, H);
    const g = ctx.createRadialGradient(960, 420, 100, 960, 420, 1200);
    g.addColorStop(0, '#152634'); g.addColorStop(1, C.bg);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.textBaseline = 'alphabetic';
    const Q = cueFn(sc, lt);
    ctx.save();
    try { S[sc.id](ctx, lt, Q, sc); } catch (e) { console.error(sc.id, e); }
    ctx.restore();
    // chapter tag
    const idx = tl.scenes.indexOf(sc);
    const kitScene = ['build', 'test'].includes(sc.id);
    if (!kitScene || lt < 3) {
      const ck = kitScene ? 1 - seg(lt, 2.4, 3) : 1;
      pill(ctx, `${String(idx + 1).padStart(2, '0')}  ${sc.title.toUpperCase()}`, 40, 42, { size: 22, ls: 2, fill: '#0E1820D0', color: C.dim, alpha: ck * (sc.id === 'intro' ? seg(lt, 3, 4) : 1) });
    }
    // fades between scenes
    const fin = 1 - seg(lt, 0, 0.45), fout = seg(lt, sc.dur - 0.35, sc.dur);
    const f = Math.max(fin, idx === tl.scenes.length - 1 ? seg(t, tl.total - 1.2, tl.total) : fout);
    if (f > 0) { ctx.fillStyle = `rgba(14,24,32,${f})`; ctx.fillRect(0, 0, W, H); }
    if (opt.captions !== false) drawCaption(ctx, captionAt(sc, lt));
    ctx.restore();
    return { scene: sc, index: idx };
  }

  // interactive lab: full kit, all wires, live
  function drawLab(ctx, st, opt = {}) {
    const lev = opt.lever || st;
    ctx.save();
    ctx.setTransform(opt.scale || 1, 0, 0, opt.scale || 1, 0, 0);
    ctx.fillStyle = opt.bg || C.bg; ctx.fillRect(0, 0, 1800, 900);
    const maxStep = opt.step == null ? 8 : opt.step;
    kit(ctx, {
      t: opt.t || 0, power: opt.power == null ? 1 : opt.power, st, lever: lev,
      chips: 1, wires: (i, w) => (w.step <= maxStep + (maxStep === 3 ? 0.5 : 0) ? { draw: 1, alpha: opt.focus != null && Math.floor(w.step) !== opt.focus ? 0.25 : 1 } : null),
      ledNet: KIT_LEDNET, swNet: KIT_SWNET, swCol: KIT_SWCOL,
    });
    ctx.restore();
  }
  // switch hit areas in kit coordinates
  const LAB_HITS = [1, 2, 3].map(i => ({ net: KIT_SWNET[i], x: SWX(i) - 40, y: SWSOCK + 10, w: 80, h: 130 }));

  window.FA = { drawFrame, drawLab, evalFA, WIRES, STEPS, LAB_HITS, W, H, LED_CO, LED_S, KIT: { w: 1800, h: 900 }, timeline: TL };
})();
