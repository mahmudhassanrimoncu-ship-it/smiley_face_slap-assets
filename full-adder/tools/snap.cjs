// usage: node tools/snap.cjs <outdir> t1 t2 ...   -> writes PNG stills of the video at those times
const { chromium } = require('playwright');
const path = require('node:path');
const fs = require('node:fs');
(async () => {
const [outdir, ...times] = process.argv.slice(2);
fs.mkdirSync(outdir, { recursive: true });
const root = path.resolve(__dirname, '..');
const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
page.on('console', m => { if (m.type() === 'error') console.log('console:', m.text()); });
page.on('pageerror', e => console.log('pageerror:', e.message));
await page.goto('file://' + path.join(root, 'index.html'));
await page.evaluate(() => document.fonts.ready);
for (const t of times) {
  const data = await page.evaluate(tt => {
    const c = document.createElement('canvas'); c.width = 1920; c.height = 1080;
    FA.drawFrame(c.getContext('2d'), tt);
    return c.toDataURL('image/png');
  }, +t);
  fs.writeFileSync(path.join(outdir, `t${String(t).padStart(6, '0')}.png`), Buffer.from(data.split(',')[1], 'base64'));
}
await browser.close();
})();
