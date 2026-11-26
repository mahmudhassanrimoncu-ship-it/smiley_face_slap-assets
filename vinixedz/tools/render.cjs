// Usage: node render.js <logfile>
const {chromium} = require('playwright');
const fs = require('fs');
(async () => {
  const out = fs.createWriteStream(process.argv[2] || 'render.log');
  const b = await chromium.launch({args: ['--disable-gpu-vsync', '--disable-background-timer-throttling', '--disable-renderer-backgrounding']});
  const p = await b.newPage({viewport: {width: 1600, height: 1000}});
  p.on('console', m => { const t = m.text(); if (t.startsWith('VNX|')) out.write(t + '\n'); else if (m.type() === 'error' && !t.includes('TUNNEL')) console.log('ERR', t); });
  p.on('pageerror', e => console.log('PAGEERROR: ' + e.message));
  await p.goto('http://localhost:9000/src/vinixedz');
  await p.waitForTimeout(12000);
  const ok = await p.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => x.innerText.trim() === 'RENDER'); if (b) { b.click(); return true; } return false; });
  console.log('clicked', ok);
  const t0 = Date.now();
  await p.waitForTimeout(3000);
  let last = '';
  while (true) {
    await p.waitForTimeout(5000);
    const txt = await p.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => /^(RENDER|ABORT|CANCEL)/i.test(x.innerText.trim())); return b ? b.innerText.trim() : 'none'; });
    const fr = await p.locator('span[title="Current frame"]').innerText().catch(() => '?');
    if (fr !== last) { console.log(`${((Date.now()-t0)/1000).toFixed(0)}s btn=${txt} frame=${fr}`); last = fr; }
    if (txt === 'RENDER') break;
  }
  out.end();
  await b.close();
})();
