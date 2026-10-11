// Render the explainer to MP4: node tools/render.cjs <out.mp4> [workers] [fps]
// Each worker renders a slice of frames in headless Chromium and pipes JPEGs to ffmpeg;
// the slices are joined and the narration is muxed in.
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('node:child_process');
const path = require('node:path');
const fs = require('node:fs');
const root = path.resolve(__dirname, '..');
const out = path.resolve(process.argv[2] || 'full-adder.mp4');
const workers = +(process.argv[3] || 3), fps = +(process.argv[4] || 30);
global.window = {}; require(path.join(root, 'timeline.js'));
const total = window.TIMELINE.total, N = Math.ceil(total * fps);
const tmp = fs.mkdtempSync(path.join(path.dirname(out), '.render-'));

async function slice(w, browser) {
  const a = Math.floor((N * w) / workers), b = Math.floor((N * (w + 1)) / workers);
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.log('pageerror', e.message));
  await page.goto('file://' + path.join(root, 'index.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => { window.__c = document.createElement('canvas'); window.__c.width = 1920; window.__c.height = 1080; });
  const file = path.join(tmp, `part${w}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', String(fps), file], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = a; f < b; f++) {
    const data = await page.evaluate(t => { FA.drawFrame(window.__c.getContext('2d'), t); return window.__c.toDataURL('image/jpeg', 0.93); }, f / fps);
    const buf = Buffer.from(data.slice(data.indexOf(',') + 1), 'base64');
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - a) % 600 === 0) console.log(`worker ${w}: ${f - a}/${b - a}`);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => (c ? rej(new Error('ffmpeg ' + c)) : res())));
  return file;
}
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined });
  const parts = await Promise.all([...Array(workers).keys()].map(w => slice(w, browser)));
  await browser.close();
  fs.writeFileSync(path.join(tmp, 'list.txt'), parts.map(p => `file '${p}'`).join('\n'));
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', path.join(tmp, 'list.txt'),
    '-i', path.join(root, 'narration.mp3'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k',
    '-shortest', '-movflags', '+faststart', out], { stdio: 'inherit' });
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log('wrote', out);
})();
