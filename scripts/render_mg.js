// usage: node render_mg.js page.html out.mp4 [fps] [--stills t1,t2,...]  [--hash JSON]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const args = process.argv.slice(2);
  const html = args[0], out = args[1];
  const fps = Number(args[2] && !args[2].startsWith('--') ? args[2] : 30);
  const si = args.indexOf('--stills');
  const hi = args.indexOf('--hash');
  const alpha = args.includes('--alpha');
  const hash = hi >= 0 ? '#' + encodeURIComponent(args[hi + 1]) : '';
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('console', m => console.log('[page]', m.text()));
  p.on('pageerror', e => console.log('[pageerror]', e.message));
  await p.goto('file://' + path.resolve(html) + hash);
  await p.waitForFunction('window.READY===true', null, { timeout: 60000 });
  const canvas = await p.$('canvas');
  if (si >= 0) {
    const ts = args[si + 1].split(',').map(Number);
    for (const t of ts) {
      await p.evaluate(t => window.renderFrame(t), t);
      await canvas.screenshot({ path: out.replace(/\.png$/, '') + `_${t.toFixed(2)}.png`, omitBackground: alpha });
    }
    await b.close(); return;
  }
  const dur = await p.evaluate('window.DURATION');
  const enc = alpha ? ['-c:v', 'qtrle', '-pix_fmt', 'argb'] : ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', '-preset', 'medium'];
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-', ...enc, '-r', String(fps), out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(dur * fps);
  for (let i = 0; i < n; i++) {
    await p.evaluate(t => window.renderFrame(t), i / fps);
    const buf = alpha ? await canvas.screenshot({ type: 'png', omitBackground: true }) : await canvas.screenshot({ type: 'jpeg', quality: 94 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await b.close();
  console.log('done', out, n, 'frames');
})();
