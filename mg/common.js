// Play Football RF — motion graphics engine (canvas, deterministic per-frame)
const W = 1920, H = 1080;
const C = {
  brown: '#3a2215', brownDeep: '#24140b', brownMid: '#5a3622', brownLight: '#8a5a3a',
  black: '#0a0908', white: '#f6f2ea', offwhite: '#d9cfc2'
};
const cv = document.getElementById('c');
cv.width = W; cv.height = H;
const ctx = cv.getContext('2d');

const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const prog = (t, a, b) => clamp((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const E = {
  out: x => 1 - Math.pow(1 - x, 3),
  out5: x => 1 - Math.pow(1 - x, 5),
  in: x => x * x * x,
  inOut: x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2,
  back: x => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); },
  elastic: x => x === 0 ? 0 : x === 1 ? 1 : Math.pow(2, -10 * x) * Math.sin((x * 10 - .75) * (2 * Math.PI / 3)) + 1,
};
// in/out envelope: rises during [a,a+d], falls during [b-d,b]
const env = (t, a, b, d = .4) => Math.min(E.out(prog(t, a, a + d)), 1 - E.in(prog(t, b - d, b)));
function rng(seed) { let s = seed % 2147483647; if (s <= 0) s += 2147483646; return () => (s = s * 16807 % 2147483647, (s - 1) / 2147483646); }
const fmt = n => Math.round(n).toLocaleString('pt-BR');

function mk(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return [c, c.getContext('2d')]; }

// ---------- dark-brown futsal court parquet ----------
function makeWood(w = W + 200, h = H + 200, seed = 7, opts = {}) {
  const [c, g] = mk(w, h);
  const r = rng(seed);
  const ph = opts.plank || 64;
  const tones = opts.tones || ['#3d2416', '#36200f', '#432817', '#2f1b0e', '#3a2314', '#46291a'];
  for (let y = 0; y < h; y += ph) {
    let x = -r() * 600;
    while (x < w) {
      const len = 380 + r() * 520;
      g.fillStyle = tones[Math.floor(r() * tones.length)];
      g.fillRect(x, y, len, ph);
      // grain streaks
      const n = 14 + Math.floor(r() * 10);
      for (let i = 0; i < n; i++) {
        const yy = y + r() * ph, amp = 1 + r() * 3, fr = .004 + r() * .01, ph0 = r() * 6;
        g.strokeStyle = r() < .5 ? 'rgba(0,0,0,.18)' : 'rgba(120,70,40,.14)';
        g.lineWidth = .6 + r() * 1.4;
        g.beginPath();
        for (let xx = x; xx <= x + len; xx += 12) g.lineTo(xx, yy + Math.sin(xx * fr + ph0) * amp);
        g.stroke();
      }
      // knot sometimes
      if (r() < .12) {
        const kx = x + r() * len, ky = y + ph / 2;
        const grd = g.createRadialGradient(kx, ky, 1, kx, ky, 14);
        grd.addColorStop(0, 'rgba(15,8,3,.55)'); grd.addColorStop(1, 'rgba(15,8,3,0)');
        g.fillStyle = grd; g.beginPath(); g.ellipse(kx, ky, 26, 9, 0, 0, 7); g.fill();
      }
      g.fillStyle = 'rgba(0,0,0,.55)'; g.fillRect(x + len - 1.5, y, 2, ph); // butt joint
      x += len;
    }
    g.fillStyle = 'rgba(0,0,0,.6)'; g.fillRect(0, y + ph - 1.5, w, 2);   // seam
    g.fillStyle = 'rgba(255,220,180,.05)'; g.fillRect(0, y, w, 1.5);     // bevel highlight
  }
  // varnish sheen
  const sh = g.createLinearGradient(0, 0, w, h);
  sh.addColorStop(0, 'rgba(255,200,150,.05)'); sh.addColorStop(.5, 'rgba(255,200,150,0)'); sh.addColorStop(1, 'rgba(0,0,0,.15)');
  g.fillStyle = sh; g.fillRect(0, 0, w, h);
  return c;
}

// ---------- film grain (precomputed tiles) ----------
const grainTiles = [];
for (let k = 0; k < 6; k++) {
  const [c, g] = mk(512, 512); const id = g.createImageData(512, 512); const r = rng(101 + k);
  for (let i = 0; i < id.data.length; i += 4) { const v = r() * 255; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 20; }
  g.putImageData(id, 0, 0); grainTiles.push(c);
}
function grain(t, a = 1) {
  const tile = grainTiles[Math.floor(t * 24) % grainTiles.length];
  ctx.save(); ctx.globalAlpha = a; ctx.globalCompositeOperation = 'overlay';
  ctx.fillStyle = ctx.createPattern(tile, 'repeat'); ctx.fillRect(0, 0, W, H); ctx.restore();
}
function vignette(a = .65) {
  const g = ctx.createRadialGradient(W / 2, H / 2, H * .35, W / 2, H / 2, H * .95);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${a})`);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}

// ---------- text helpers ----------
function txt(s, x, y, o = {}) {
  ctx.save();
  ctx.font = `${o.weight || ''} ${o.size || 80}px ${o.font || 'Anton'}`;
  ctx.textAlign = o.align || 'left'; ctx.textBaseline = o.base || 'alphabetic';
  ctx.letterSpacing = (o.ls || 0) + 'px';
  ctx.globalAlpha = o.alpha ?? 1;
  if (o.shadow) { ctx.shadowColor = o.shadow; ctx.shadowBlur = o.blur ?? 30; ctx.shadowOffsetY = o.sy ?? 8; }
  if (o.stroke) { ctx.lineWidth = o.lw || 3; ctx.strokeStyle = o.stroke; ctx.lineJoin = 'round'; ctx.strokeText(s, x, y); }
  if (o.color !== null) { ctx.fillStyle = o.color || C.white; ctx.fillText(s, x, y); }
  ctx.restore();
}
function measure(s, o = {}) {
  ctx.save(); ctx.font = `${o.weight || ''} ${o.size || 80}px ${o.font || 'Anton'}`; ctx.letterSpacing = (o.ls || 0) + 'px';
  const w = ctx.measureText(s).width; ctx.restore(); return w;
}
// text revealed upward from behind a mask line
function maskUp(s, x, y, k, o = {}) {
  const sz = o.size || 80;
  ctx.save(); ctx.beginPath();
  const w = measure(s, o) + 40;
  const left = o.align === 'center' ? x - w / 2 : o.align === 'right' ? x - w : x - 20;
  ctx.rect(left, y - sz * 1.15, w, sz * 1.35); ctx.clip();
  txt(s, x, y + (1 - E.out5(k)) * sz * 1.3, o); ctx.restore();
}
function rrect(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }

// check / cross marks (no emoji dependency)
function mark(type, x, y, s, k, color = C.white, lw = 14) {
  ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (type === 'ok') {
    const p = [[-.5, .02], [-.15, .38], [.55, -.4]];
    const L1 = Math.hypot(.35, .36), L2 = Math.hypot(.7, .78), tot = L1 + L2, d = k * tot;
    ctx.beginPath(); ctx.moveTo(x + p[0][0] * s, y + p[0][1] * s);
    if (d <= L1) { const q = d / L1; ctx.lineTo(x + lerp(p[0][0], p[1][0], q) * s, y + lerp(p[0][1], p[1][1], q) * s); }
    else { ctx.lineTo(x + p[1][0] * s, y + p[1][1] * s); const q = (d - L1) / L2; ctx.lineTo(x + lerp(p[1][0], p[2][0], q) * s, y + lerp(p[1][1], p[2][1], q) * s); }
    ctx.stroke();
  } else {
    const a = clamp(k * 2), b = clamp(k * 2 - 1);
    ctx.beginPath(); ctx.moveTo(x - .42 * s, y - .42 * s); ctx.lineTo(x + lerp(-.42, .42, a) * s, y + lerp(-.42, .42, a) * s); ctx.stroke();
    if (b > 0) { ctx.beginPath(); ctx.moveTo(x + .42 * s, y - .42 * s); ctx.lineTo(x + lerp(.42, -.42, b) * s, y + lerp(-.42, .42, b) * s); ctx.stroke(); }
  }
  ctx.restore();
}

// ---------- boot ----------
async function boot(scenes) {
  await Promise.all(['Anton', 'Bebas Neue', 'Archivo Black'].map(f => document.fonts.load(`80px "${f}"`)));
  let acc = 0; const list = scenes.map(s => { const o = { ...s, t0: acc }; acc += s.dur; return o; });
  window.DURATION = acc;
  window.renderFrame = t => {
    const s = list.find(s => t < s.t0 + s.dur) || list[list.length - 1];
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    ctx.clearRect(0, 0, W, H);
    s.draw(t - s.t0, s.dur, s);
  };
  window.renderFrame(0);
  window.READY = true;
}
