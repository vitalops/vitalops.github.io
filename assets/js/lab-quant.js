/* Quantisation lab: a live, in-browser look at what weight quantisation does to one
   transformer linear layer. Mount with <div data-lab="quant"></div>.
   Everything is computed here: a seeded synthetic 1024x1024 weight matrix with a few
   outlier input channels, a calibration activation sample with a few salient channels,
   and real quantise -> dequantise for BF16, FP8 E4M3, INT8, INT4 and NVFP4.
   No libraries, no network. */
(function () {
  'use strict';

  var K = 1024, N = 1024, T = 16;          // input channels, output channels, calibration tokens
  var SALIENT = [37, 140, 262, 291, 455, 610, 777, 930];   // channels with large activations
  var SPIKES = [118, 300, 640, 871];                        // input channels with outlier weights
  var N0 = 17;                                              // output channel shown in the inset
  var TK0 = 256, TN = 64;                                   // heatmap tile: inputs 256..319, outputs 0..63
  var W0 = 256, W1 = 384;                                   // inset window rows
  var FMTS = ['bf16', 'fp8', 'int8', 'int4c', 'int4g', 'nvfp4'];
  var GROUPS = [32, 64, 128, 256];
  var FP4 = [0, 0.5, 1, 1.5, 2, 3, 4, 6];
  var HW = window.VO_HW || null;
  var BW_EFF = 0.75;                                        // share of peak bandwidth a decode step reaches (assumption, as in the planner)

  /* what the selected GPU does with a format: from the catalogue's tensor-core rates only, no guesses */
  function support(fmt, g) {
    if (!g) return null;
    var f = g.flops || {};
    switch (fmt) {
      case 'bf16': return { native: true, rate: 'bf16', how: 'BF16 tensor cores' };
      case 'fp8': return f.fp8 ? { native: true, rate: 'fp8', how: 'FP8 tensor cores' } : { native: false, rate: 'bf16', how: 'no FP8 tensor cores: weights dequantised to BF16 at matmul time' };
      case 'int8': return { native: !!f.int8, rate: 'bf16', how: (f.int8 ? 'INT8 tensor cores exist (W8A8); ' : '') + 'weight-only INT8 as shown here is dequantised to BF16 at matmul time' };
      case 'int4c': case 'int4g': return { native: false, rate: f.fp8 ? 'fp8' : 'bf16', how: 'weight-only: dequantised at matmul time on every GPU, to ' + (f.fp8 ? 'FP8' : 'BF16') };
      case 'nvfp4': return f.fp4 ? { native: true, rate: 'fp4', how: 'FP4 tensor cores' } : { native: false, rate: f.fp8 ? 'fp8' : 'bf16', how: 'no FP4 tensor cores: dequantised to ' + (f.fp8 ? 'FP8' : 'BF16') + ' at matmul time' };
    }
  }

  /* ───────── numerics ───────── */
  function mulberry32(a) {
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      var t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  // round |a| to a float grid with m mantissa bits, minimum normal exponent emin, saturating at max
  function rfloat(x, m, emin, max) {
    if (x === 0) return 0;
    var s = x < 0 ? -1 : 1, a = x * s;
    var e = Math.floor(Math.log2(a));
    if (e < emin) e = emin;
    var step = Math.pow(2, e - m);
    var r = Math.round(a / step) * step;
    return s * (r > max ? max : r);
  }
  function e4m3(x) { return rfloat(x, 3, -6, 448); }
  function fp16(x) { return rfloat(x, 10, -14, 65504); }
  var f32 = new Float32Array(1), u32 = new Uint32Array(f32.buffer);
  function bf16(x) {
    f32[0] = x; var u = u32[0];
    u = (u + 0x7FFF + ((u >>> 16) & 1)) >>> 0;
    u32[0] = (u & 0xFFFF0000) >>> 0;
    return f32[0];
  }
  function fp4(x) {
    var s = x < 0 ? -1 : 1, a = x * s, r;
    if (a < 0.25) r = 0; else if (a < 0.75) r = 0.5; else if (a < 1.25) r = 1; else if (a < 1.75) r = 1.5;
    else if (a < 2.5) r = 2; else if (a < 3.5) r = 3; else if (a < 5) r = 4; else r = 6;
    return s * r;
  }
  var E4M3_POS = (function () {           // every positive finite E4M3 value
    var v = [];
    for (var e = 0; e < 16; e++) for (var m = 0; m < 8; m++) {
      if (e === 15 && m === 7) continue;  // NaN
      v.push(e === 0 ? m / 8 * Math.pow(2, -6) : (1 + m / 8) * Math.pow(2, e - 7));
    }
    return v.filter(function (x) { return x > 0; });
  })();

  /* ───────── synthetic layer ───────── */
  var D = null;
  function gen() {
    var rnd = mulberry32(20251103), spare = null;
    function gauss() {
      if (spare !== null) { var s = spare; spare = null; return s; }
      var u = 0, v = 0; while (u === 0) u = rnd(); v = rnd();
      var r = Math.sqrt(-2 * Math.log(u)); spare = r * Math.sin(2 * Math.PI * v); return r * Math.cos(2 * Math.PI * v);
    }
    var Wt = new Float32Array(N * K);       // column-major: Wt[n*K + k] is W[k][n]
    var rowS = new Float32Array(K), colS = new Float32Array(N), isSpike = new Uint8Array(K);
    for (var k = 0; k < K; k++) rowS[k] = 0.8 + 0.4 * rnd();
    for (var n = 0; n < N; n++) colS[n] = 0.6 + 0.8 * rnd();
    SPIKES.forEach(function (k) { isSpike[k] = 1; });
    for (n = 0; n < N; n++) for (k = 0; k < K; k++) {
      var g = gauss(); if (rnd() < 0.15) g *= 2.2;          // heavy tails
      var w = 0.016 * g * rowS[k] * colS[n];
      if (isSpike[k] && rnd() < 0.3) w = (rnd() < 0.5 ? -1 : 1) * 0.02 * (6 + 8 * rnd()) * colS[n];
      Wt[n * K + k] = w;
    }
    Wt[N0 * K + 300] = 0.31;                // the inset column carries a clear outlier
    var X = new Float32Array(T * K), xs = new Float32Array(K), isSal = new Uint8Array(K);
    for (k = 0; k < K; k++) xs[k] = 0.5 + rnd();
    SALIENT.forEach(function (k) { xs[k] = 18 + 27 * rnd(); isSal[k] = 1; });
    for (var t = 0; t < T; t++) for (k = 0; k < K; k++) X[t * K + k] = gauss() * xs[k];
    var xmean = new Float32Array(K), xrms = new Float32Array(K), mm = 0;
    for (k = 0; k < K; k++) {
      var a = 0, b = 0;
      for (t = 0; t < T; t++) { var x = X[t * K + k]; a += Math.abs(x); b += x * x; }
      xmean[k] = a / T; xrms[k] = Math.sqrt(b / T); mm += xmean[k];
    }
    mm /= K;
    var wN2 = 0, amax = 0;
    for (var i = 0; i < Wt.length; i++) { wN2 += Wt[i] * Wt[i]; var aw = Math.abs(Wt[i]); if (aw > amax) amax = aw; }
    var yN2 = 0;
    for (n = 0; n < N; n++) { var off = n * K; for (t = 0; t < T; t++) { var d = 0, xo = t * K; for (k = 0; k < K; k++) d += X[xo + k] * Wt[off + k]; yN2 += d * d; } }
    var B = 97, hist = new Float64Array(B), hw = 2 * amax / B;
    for (i = 0; i < Wt.length; i++) { var bi = Math.floor((Wt[i] + amax) / hw); if (bi >= B) bi = B - 1; hist[bi]++; }
    D = { Wt: Wt, X: X, xmean: xmean, xrms: xrms, xmm: mm, wN2: wN2, yN2: yN2, amax: amax, hist: hist, hw: hw, isSal: isSal, isSpike: isSpike };
    return D;
  }

  /* ───────── formats ───────── */
  function bits(fmt, G) {
    switch (fmt) {
      case 'bf16': return 16;
      case 'fp8': return 8 + 32 / (K * N);
      case 'int8': return 8 + 16 / K;                 // FP16 scale per output channel
      case 'int4c': return 4 + 20 / K;                // FP16 scale + 4-bit zero per output channel
      case 'int4g': return 4 + 20 / G;                // FP16 scale + 4-bit zero per group
      case 'nvfp4': return 4 + 8 / 16 + 32 / (K * N); // E4M3 scale per 16, FP32 per tensor
    }
  }
  function name(fmt, G) {
    return { bf16: 'BF16', fp8: 'FP8 E4M3', int8: 'INT8 per-channel', int4c: 'INT4 per-channel', int4g: 'INT4 g' + G, nvfp4: 'NVFP4' }[fmt];
  }
  function short(fmt, G) {
    return { bf16: 'BF16', fp8: 'FP8', int8: 'INT8', int4c: 'INT4 /ch', int4g: 'INT4 g' + G, nvfp4: 'NVFP4' }[fmt];
  }
  function desc(fmt, G) {
    return {
      bf16: 'Brain float 16: 8 exponent and 7 mantissa bits. The reference most checkpoints ship in.',
      fp8: 'FP8 E4M3 with one FP32 scale for the whole tensor: 4 exponent and 3 mantissa bits, largest value 448. Native on Hopper and Blackwell tensor cores.',
      int8: '8-bit integers, symmetric, with one FP16 scale per output channel.',
      int4c: '4-bit integers with one FP16 scale and 4-bit zero point per output channel. A single outlier stretches the grid for the whole channel.',
      int4g: '4-bit integers with an FP16 scale and 4-bit zero point for every ' + G + ' input weights, as GPTQ and AWQ checkpoints store them.',
      nvfp4: 'FP4 E2M1 values (0, 0.5, 1, 1.5, 2, 3, 4, 6) with an FP8 E4M3 scale per block of 16 and one FP32 tensor scale. Native on Blackwell.'
    }[fmt];
  }

  function asym(a, q, o, len, L) {
    var lo = Infinity, hi = -Infinity, k;
    for (k = o; k < o + len; k++) { var v = a[k]; if (v < lo) lo = v; if (v > hi) hi = v; }
    if (lo > 0) lo = 0; if (hi < 0) hi = 0;
    var sc = fp16((hi - lo) / L);
    if (!sc) { for (k = o; k < o + len; k++) q[k] = 0; return; }
    var z = Math.round(-lo / sc); if (z < 0) z = 0; if (z > L) z = L;
    for (k = o; k < o + len; k++) {
      var c = Math.round(a[k] / sc) + z; if (c < 0) c = 0; else if (c > L) c = L;
      q[k] = (c - z) * sc;
    }
  }
  function asymLevels(a, o, len, L) {
    var lo = Infinity, hi = -Infinity;
    for (var k = o; k < o + len; k++) { if (a[k] < lo) lo = a[k]; if (a[k] > hi) hi = a[k]; }
    if (lo > 0) lo = 0; if (hi < 0) hi = 0;
    var sc = fp16((hi - lo) / L), z = Math.min(L, Math.max(0, Math.round(-lo / sc))), out = [];
    for (var c = 0; c <= L; c++) out.push((c - z) * sc);
    return out;
  }
  function symScale(a, o, len) {
    var m = 0; for (var k = o; k < o + len; k++) { var v = Math.abs(a[k]); if (v > m) m = v; }
    return fp16(m / 127);
  }
  function nvScale(a, o, len, nvt) {
    var m = 0; for (var k = o; k < o + len; k++) { var v = Math.abs(a[k]); if (v > m) m = v; }
    return e4m3(m / 6 / nvt) * nvt;
  }
  function qcol(a, q, fmt, G, ctx) {
    var k, o;
    switch (fmt) {
      case 'bf16': for (k = 0; k < K; k++) q[k] = bf16(a[k]); break;
      case 'fp8': var s8 = ctx.fp8s; for (k = 0; k < K; k++) q[k] = e4m3(a[k] / s8) * s8; break;
      case 'int8':
        var s = symScale(a, 0, K);
        for (k = 0; k < K; k++) { var c = s ? Math.round(a[k] / s) : 0; q[k] = (c > 127 ? 127 : c < -127 ? -127 : c) * s; }
        break;
      case 'int4c': asym(a, q, 0, K, 15); break;
      case 'int4g': for (o = 0; o < K; o += G) asym(a, q, o, G, 15); break;
      case 'nvfp4':
        for (o = 0; o < K; o += 16) {
          var sb = nvScale(a, o, 16, ctx.nvt);
          for (k = o; k < o + 16; k++) q[k] = sb ? fp4(a[k] / sb) * sb : 0;
        }
        break;
    }
  }
  function groupOf(fmt, G) {             // inset group bounds for the salient channel 291
    if (fmt === 'int4g') { var g0 = Math.floor(291 / G) * G; return [g0, g0 + G]; }
    if (fmt === 'nvfp4') return [288, 304];
    return [0, K];
  }
  function levels(fmt, G, a, ctx) {
    var gb = groupOf(fmt, G), i, out = [];
    switch (fmt) {
      case 'bf16': return null;
      case 'fp8': E4M3_POS.forEach(function (v) { out.push(v * ctx.fp8s, -v * ctx.fp8s); }); out.push(0); return out;
      case 'int8': var s = symScale(a, 0, K); for (i = -127; i <= 127; i++) out.push(i * s); return out;
      case 'int4c': case 'int4g': return asymLevels(a, gb[0], gb[1] - gb[0], 15);
      case 'nvfp4': var sb = nvScale(a, 288, 16, ctx.nvt); FP4.forEach(function (v) { out.push(v * sb, -v * sb); }); return out;
    }
  }

  /* run one configuration. s: per-input-channel AWQ scale or null. cols: subset of output channels or null */
  function run(fmt, G, s, cols, detail) {
    var d = D, Wt = d.Wt, X = d.X, k, n, t, ci;
    var amax = 0;
    if (fmt === 'fp8' || fmt === 'nvfp4') {
      for (n = 0; n < N; n++) for (k = 0; k < K; k++) { var v = Math.abs(Wt[n * K + k] * (s ? s[k] : 1)); if (v > amax) amax = v; }
    }
    var ctx = { fp8s: amax / 448, nvt: amax / (448 * 6) };
    var a = new Float32Array(K), q = new Float32Array(K), e = new Float32Array(K);
    var eW2 = 0, eY2 = 0, wN2 = 0, yN2 = 0;
    var tile = detail ? new Float32Array(TN * 64) : null, inset = null;
    var list = cols || null, cnt = list ? list.length : N;
    for (ci = 0; ci < cnt; ci++) {
      n = list ? list[ci] : ci;
      var off = n * K;
      if (s) for (k = 0; k < K; k++) a[k] = Wt[off + k] * s[k]; else for (k = 0; k < K; k++) a[k] = Wt[off + k];
      qcol(a, q, fmt, G, ctx);
      for (k = 0; k < K; k++) { var w = Wt[off + k], wh = s ? q[k] / s[k] : q[k]; e[k] = w - wh; eW2 += e[k] * e[k]; if (list) wN2 += w * w; }
      for (t = 0; t < T; t++) {
        var xo = t * K, dd = 0, yy = 0;
        for (k = 0; k < K; k++) dd += X[xo + k] * e[k];
        eY2 += dd * dd;
        if (list) { for (k = 0; k < K; k++) yy += X[xo + k] * Wt[off + k]; yN2 += yy * yy; }
      }
      if (detail && n < TN) for (k = 0; k < 64; k++) tile[n * 64 + k] = e[TK0 + k];
      if (detail && n === N0) {
        var gb = groupOf(fmt, G), r0 = Math.max(gb[0], W0), r1 = Math.min(gb[1], W1);
        inset = { r0: r0, r1: r1, glen: gb[1] - gb[0], a: Array.prototype.slice.call(a, r0, r1), q: Array.prototype.slice.call(q, r0, r1), lv: levels(fmt, G, a, ctx) };
      }
    }
    return { eW2: eW2, eY2: eY2, wN2: list ? wN2 : d.wN2, yN2: list ? yN2 : d.yN2, tile: tile, inset: inset };
  }

  function scalesFor(alpha) {
    if (!alpha) return null;
    var s = new Float32Array(K);
    for (var k = 0; k < K; k++) s[k] = Math.pow(D.xmean[k] / D.xmm, alpha);
    return s;
  }
  var alphaCache = {};
  function searchAlpha(fmt, G) {          // AWQ: grid-search the scale exponent on a column subset
    var key = fmt + G;
    if (alphaCache[key] !== undefined) return alphaCache[key];
    if (fmt === 'bf16') return (alphaCache[key] = 0);
    var cols = []; for (var n = 3; n < N; n += 16) cols.push(n);
    var best = 0, bestE = Infinity;
    for (var i = 0; i <= 10; i++) {
      var al = i / 10, r = run(fmt, G, scalesFor(al), cols, false);
      if (r.eY2 < bestE * 0.97) { bestE = r.eY2; best = al; }
    }
    return (alphaCache[key] = best);
  }

  var cache = {};
  function keyOf(fmt, G, prot) { return fmt + '|' + (fmt === 'int4g' ? G : 0) + '|' + (prot ? 1 : 0); }
  function result(fmt, G, prot) {
    var key = keyOf(fmt, G, prot);
    if (cache[key]) return cache[key];
    var alpha = prot ? searchAlpha(fmt, G) : 0, s = scalesFor(alpha);
    var r = run(fmt, G, s, null, true), salMul = 0;
    if (s) { for (var i = 0; i < SALIENT.length; i++) salMul += s[SALIENT[i]]; salMul /= SALIENT.length; }
    var res = {
      fmt: fmt, G: G, prot: prot, alpha: alpha, salMul: salMul, bits: bits(fmt, G),
      wErr: Math.sqrt(r.eW2 / r.wN2), yErr: Math.sqrt(r.eY2 / r.yN2),
      sqnr: 10 * Math.log10(r.wN2 / Math.max(r.eW2, 1e-30)), tile: r.tile, inset: r.inset
    };
    cache[key] = res;
    return res;
  }

  /* background queue: fill the comparison and the likely next clicks */
  var queue = [], qBusy = false, insts = [];
  function enqueue(keys, front) {
    keys.forEach(function (k) { if (!cache[keyOf(k[0], k[1], k[2])]) { if (front) queue.unshift(k); else queue.push(k); } });
    pump();
  }
  function pump() {
    if (qBusy) return; qBusy = true;
    setTimeout(function step() {
      while (queue.length && cache[keyOf(queue[0][0], queue[0][1], queue[0][2])]) queue.shift();
      if (!queue.length) { qBusy = false; insts.forEach(function (i) { i.status(); }); return; }
      var j = queue.shift(); result(j[0], j[1], j[2]);
      insts.forEach(function (i) { i.bars(); i.status(); });
      setTimeout(step, 16);
    }, 30);
  }

  /* ───────── formatting ───────── */
  function pct(x) { x *= 100; return (x < 0.1 ? x.toFixed(3) : x < 1 ? x.toFixed(2) : x < 10 ? x.toFixed(1) : x.toFixed(0)) + '%'; }
  function gb(b) { return b >= 100 ? b.toFixed(0) : b.toFixed(1); }
  function css(v, el) { return getComputedStyle(el || document.documentElement).getPropertyValue(v).trim(); }
  function lum(c) { var m = (c || '').match(/\d+(\.\d+)?/g); if (!m || m.length < 3) return 1; return (0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]) / 255; }
  function hex(c) {
    c = (c || '').replace('#', '');
    if (c.length === 3) c = c.split('').map(function (x) { return x + x; }).join('');
    var n = parseInt(c, 16); return isNaN(n) ? [63, 92, 246] : [n >> 16 & 255, n >> 8 & 255, n & 255];
  }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }

  /* ───────── styles ───────── */
  var CSS = [
    '.lq{--lq-r:12px;font-family:var(--font,Inter,system-ui,sans-serif);color:var(--ink2,#334155);background:var(--white,#fff);border:1px solid var(--line,#e2e8f0);border-radius:var(--lq-r);box-shadow:0 1px 2px rgba(16,24,40,.05);overflow:hidden;font-size:14px;line-height:1.5;text-align:left;max-width:100%;box-sizing:border-box}',
    '.lq *,.lq *::before,.lq *::after{box-sizing:border-box}',
    '.lq-head{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;padding:8px 16px;border-bottom:1px solid var(--line,#e2e8f0);background:var(--bg,#f5f6fa)}',
    '.lq-title{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;min-width:0}',
    '.lq-title b{color:var(--ink,#0f172a);font-size:14px;font-weight:600}',
    '.lq-title span{font-family:var(--mono,monospace);font-size:12px;color:var(--ink3,#5b687c)}',
    '.lq-status{font-size:12px;color:var(--ink3,#5b687c);white-space:nowrap;display:flex;align-items:center;gap:6px}',
    '.lq-status i{width:7px;height:7px;border-radius:50%;background:var(--ok,#059669);display:inline-block}',
    '.lq-status.busy i{background:var(--brand,#3f5cf6);animation:lq-pulse 1s ease-in-out infinite}',
    '@keyframes lq-pulse{50%{opacity:.3}}',
    '.lq-ctrls{display:flex;flex-wrap:wrap;gap:10px 22px;align-items:flex-end;padding:12px 16px 0}',
    '.lq-ctl{display:flex;flex-direction:column;gap:6px;min-width:0;max-width:100%}',
    '.lq-lab{font-size:11.5px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--ink3,#5b687c)}',
    '.lq-seg{display:inline-flex;flex-wrap:wrap;border:1px solid var(--line,#e2e8f0);border-radius:8px;background:var(--white,#fff);padding:2px;gap:2px;max-width:100%}',
    '.lq-seg button{appearance:none;border:0;background:transparent;font:inherit;font-size:13px;font-weight:500;color:var(--ink2,#334155);padding:5px 10px;border-radius:6px;cursor:pointer;white-space:nowrap;font-variant-numeric:tabular-nums}',
    '.lq-seg button:hover{background:var(--line2,#eef2f7);color:var(--ink,#0f172a)}',
    '.lq-seg button[aria-checked="true"]{background:var(--brand,#3f5cf6);color:#fff}',
    '.lq-seg button:disabled{color:var(--ink4,#94a3b8);cursor:default;background:transparent}',
    '.lq-seg button em{font-style:normal;font-family:var(--mono,monospace);font-size:9px;letter-spacing:.04em;text-transform:uppercase;margin-left:5px;opacity:.7}',
    '.lq select{font:inherit;font-size:13px;color:var(--ink,#0f172a);background:var(--white,#fff);border:1px solid var(--line,#e2e8f0);border-radius:7px;padding:5px 8px;max-width:100%}',
    '.lq-gpu dl.lq-on{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:3px 8px;margin:2px 0 0;font-size:11.5px}',
    '.lq-gpu dl.lq-on dt{color:var(--ink3,#5b687c);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.lq-gpu dl.lq-on dd{margin:0;font-family:var(--mono,monospace);font-variant-numeric:tabular-nums;color:var(--ink,#0f172a);text-align:right;white-space:nowrap}',
    '.lq-gpu dd.ok{color:var(--ok,#059669)}.lq-gpu dd.dq,.lq-gpu .dq{color:var(--warn,#b45309)}',
    '.lq-gpu .lq-how{font-size:11px;color:var(--ink3,#5b687c);margin:5px 0 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.lq-cap{margin:4px 0 0;font-size:11px;color:var(--ink3,#5b687c);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.lq-gsub{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}',
    '.lq-seg.sm button{font-size:12px;padding:3px 8px}',
    '.lq-seg button[aria-checked="true"]:disabled{background:var(--line2,#eef2f7);color:var(--ink3,#5b687c)}',
    '.lq button:focus-visible,.lq input:focus-visible+.lq-sw-t,.lq summary:focus-visible,.lq-row:focus-visible{outline:2px solid var(--brand,#3f5cf6);outline-offset:2px}',
    '.lq-sw{display:inline-flex;align-items:center;gap:9px;cursor:pointer;font-size:13.5px;font-weight:500;color:var(--ink,#0f172a);padding-bottom:5px;position:relative}',
    '.lq-sw input{position:absolute;opacity:0;width:1px;height:1px;margin:0}',
    '.lq-sw-t{width:32px;height:18px;border-radius:9px;background:var(--ink4,#94a3b8);position:relative;flex:none;transition:background .15s}',
    '.lq-sw-t::after{content:"";position:absolute;left:2px;top:2px;width:14px;height:14px;border-radius:50%;background:#fff;transition:left .15s;box-shadow:0 1px 2px rgba(0,0,0,.2)}',
    '.lq-sw input:checked+.lq-sw-t{background:var(--brand,#3f5cf6)}',
    '.lq-sw input:checked+.lq-sw-t::after{left:16px}',
    '.lq-desc{margin:8px 16px 0;font-size:12.5px;color:var(--ink3,#5b687c);max-width:110ch}',
    '.lq-desc b{color:var(--ink2,#334155);font-weight:600}',
    '.lq-body{display:grid;grid-template-columns:minmax(0,1fr);gap:12px;padding:12px 16px 14px}',
    '.lq-cols{display:grid;grid-template-columns:minmax(0,1fr);gap:12px}',
    '.lq.lq-mid .lq-cols{grid-template-columns:repeat(2,minmax(0,1fr))}',
    '.lq.lq-wide .lq-cols{grid-template-columns:repeat(4,minmax(0,1fr))}',
    '.lq-col{display:flex;flex-direction:column;gap:12px;min-width:0}',
    '.lq-panel{border:1px solid var(--line,#e2e8f0);border-radius:10px;padding:8px 12px 10px;min-width:0;background:var(--white,#fff)}',
    '.lq-ph{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:6px;min-height:24px}',
    '.lq.lq-wide .lq-ph{flex-wrap:nowrap}.lq.lq-wide .lq-ph>b{white-space:nowrap}.lq.lq-wide .lq-ph>span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}',
    '.lq-ph b{font-size:13px;font-weight:600;color:var(--ink,#0f172a)}',
    '.lq-ph span{font-size:12px;color:var(--ink3,#5b687c)}',
    '.lq-ph .lq-sp{flex:1}',
    '.lq-chk{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--ink2,#334155);cursor:pointer;margin-left:auto}',
    '.lq-chk input{accent-color:var(--brand,#3f5cf6);margin:0}',
    '.lq svg{display:block;width:100%;height:auto;overflow:visible}',
    '.lq svg text{font-family:var(--mono,monospace);font-size:10px;fill:var(--ink3,#5b687c)}',
    '.lq-heat{position:relative;padding-top:14px}',
    '.lq-heat canvas{display:block;width:100%;aspect-ratio:1/1;border-radius:4px;border:1px solid var(--line,#e2e8f0);image-rendering:pixelated}',
    '.lq-marks{position:absolute;left:0;right:0;top:0;height:14px}',
    '.lq-marks i{position:absolute;top:0;transform:translateX(-50%);font-style:normal;font-family:var(--mono,monospace);font-size:9.5px;line-height:12px;color:var(--ink3,#5b687c);white-space:nowrap}',
    '.lq-marks i::after{content:"";display:block;width:1px;height:3px;background:currentColor;margin:0 auto}',
    '.lq-marks i.w{color:var(--brandD,#2737bd)}',
    '.lq-axes{display:flex;justify-content:space-between;gap:8px;font-family:var(--mono,monospace);font-size:10.5px;color:var(--ink3,#5b687c);margin-top:4px}',
    '.lq-legend{display:flex;align-items:center;gap:6px;margin-top:6px;font-family:var(--mono,monospace);font-size:10.5px;color:var(--ink3,#5b687c)}',
    '.lq-legend i{flex:1;height:6px;border-radius:3px;border:1px solid var(--line,#e2e8f0)}',
    '.lq-key{display:flex;flex-wrap:wrap;gap:4px 12px;margin-top:6px;font-size:11.5px;color:var(--ink3,#5b687c)}',
    '.lq-key span{display:inline-flex;align-items:center;gap:5px}',
    '.lq-key i{display:inline-block}',
    '.lq-k-o{width:6px;height:6px;border-radius:50%;background:var(--ink4,#94a3b8)}',
    '.lq-k-q{width:9px;height:2px;background:var(--brand,#3f5cf6)}',
    '.lq-k-g{width:10px;height:1px;background:var(--brand200,#bdcdff)}',
    '.lq-k-s{width:7px;height:7px;border-radius:50%;border:1.5px solid var(--brandD,#2737bd)}',
    '.lq-metrics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;background:var(--line,#e2e8f0);border:1px solid var(--line,#e2e8f0);border-radius:10px;overflow:hidden}',
    '.lq.lq-mid .lq-metrics{grid-template-columns:repeat(3,minmax(0,1fr))}',
    '.lq.lq-wide .lq-metrics{grid-template-columns:repeat(6,minmax(0,1fr))}',
    '.lq-m{background:var(--white,#fff);padding:7px 10px;min-width:0}',
    '.lq-m small{display:block;font-size:11px;color:var(--ink3,#5b687c);line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.lq-m b{display:block;font-family:var(--mono,monospace);font-variant-numeric:tabular-nums;font-size:17px;font-weight:500;color:var(--ink,#0f172a);margin-top:2px;letter-spacing:-.01em;white-space:nowrap}',
    '.lq-m em{display:block;font-style:normal;font-size:11.5px;color:var(--ink3,#5b687c);font-family:var(--mono,monospace);font-variant-numeric:tabular-nums}',
    '.lq-m em.ok{color:var(--ok,#059669)}',
    '.lq-cmp-h,.lq-row{display:grid;grid-template-columns:84px minmax(0,1fr) minmax(0,1fr);gap:10px;align-items:center}',
    '.lq-cmp-h{font-size:11px;color:var(--ink3,#5b687c);padding:0 6px 4px;border-bottom:1px solid var(--line2,#eef2f7)}',
    '.lq-row{padding:4px 6px;border-radius:6px;cursor:pointer;font-size:12px}',
    '.lq-row:hover{background:var(--line2,#eef2f7)}',
    '.lq-row.on{background:var(--brand50,#eff4ff)}',
    '.lq-row.on .lq-fn{color:var(--brandD,#2737bd);font-weight:600}',
    '.lq-fn{font-family:var(--mono,monospace);font-size:12px;color:var(--ink,#0f172a);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.lq-bar{display:flex;align-items:center;gap:6px;min-width:0}',
    '.lq-bar i{display:block;height:8px;border-radius:2px;background:var(--brand200,#bdcdff);min-width:2px;transition:width .3s ease}',
    '.lq-row.on .lq-bar i{background:var(--brand,#3f5cf6)}',
    '.lq-bar span{font-family:var(--mono,monospace);font-variant-numeric:tabular-nums;font-size:11px;color:var(--ink2,#334155);white-space:nowrap}',
    '.lq-bar span.pend{color:var(--ink4,#94a3b8)}',
    '.lq-note{font-size:11.5px;color:var(--ink3,#5b687c);margin-top:6px}',
    '.lq-more{border-top:1px solid var(--line,#e2e8f0);padding:0 16px}',
    '.lq-more summary{cursor:pointer;padding:11px 0;font-size:13px;font-weight:600;color:var(--ink,#0f172a);list-style:none;display:flex;align-items:center;gap:8px}',
    '.lq-more summary::-webkit-details-marker{display:none}',
    '.lq-more summary::before{content:"";width:6px;height:6px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:rotate(-45deg);transition:transform .15s;margin-right:2px}',
    '.lq-more[open] summary::before{transform:rotate(45deg)}',
    '.lq-more div{padding:0 0 14px;font-size:13px;color:var(--ink2,#334155);max-width:92ch}',
    '.lq-more p{margin:0 0 8px}',
    '.lq-more dl{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:4px 14px;margin:0 0 10px}',
    '.lq-more dt{font-family:var(--mono,monospace);font-size:12px;color:var(--ink,#0f172a)}',
    '.lq-more dd{margin:0}',
    '.lq-load{padding:48px 16px;text-align:center;color:var(--ink3,#5b687c);font-size:13px}',
    '@media (max-width:520px){.lq-cmp-h,.lq-row{grid-template-columns:70px minmax(0,1fr) minmax(0,1fr);gap:6px}.lq-more dl{grid-template-columns:minmax(0,1fr)}.lq-more dd{margin-bottom:6px}}',
    '@media (prefers-reduced-motion:reduce){.lq *{transition:none!important;animation:none!important}}'
  ].join('\n');
  function injectCSS() {
    if (document.getElementById('lab-quant-css')) return;
    var st = document.createElement('style'); st.id = 'lab-quant-css'; st.textContent = CSS;
    document.head.appendChild(st);
  }

  /* ───────── widget ───────── */
  var uid = 0;
  function mount(root) {
    if (root.__lq) return; root.__lq = true;
    var id = 'lq' + (++uid);
    var LAB = window.VO_LAB || null;
    var S = { fmt: 'int4g', G: 128, prot: false, log: true, heat: 'act', gpu: LAB ? LAB.gpu : 'h100' };
    var segBtn = function (val, label, attr) { return '<button type="button" role="radio" aria-checked="false" data-' + attr + '="' + val + '">' + label + '</button>'; };
    root.innerHTML =
      '<div class="lq" role="group" aria-label="Quantisation lab">' +
      '<div class="lq-head"><div class="lq-title"><b>Quantisation lab</b><span>mlp.down_proj · 1,024 × 1,024 · synthetic, seeded</span></div><div class="lq-status" aria-live="polite"><i></i><span></span></div></div>' +
      '<div class="lq-ctrls">' +
        '<div class="lq-ctl"><span class="lq-lab" id="' + id + '-f">Format</span><div class="lq-seg lq-fmt" role="radiogroup" aria-labelledby="' + id + '-f">' +
          FMTS.map(function (f) { return segBtn(f, short(f, f === 'int4g' ? 'G' : 0).replace('gG', 'g128'), 'fmt'); }).join('') + '</div></div>' +
        '<div class="lq-ctl"><span class="lq-lab" id="' + id + '-g">INT4 group size</span><div class="lq-seg lq-grp" role="radiogroup" aria-labelledby="' + id + '-g">' +
          GROUPS.map(function (g) { return segBtn(g, g, 'g'); }).join('') + '</div></div>' +
        '<label class="lq-sw"><input type="checkbox" class="lq-prot"><span class="lq-sw-t" aria-hidden="true"></span><span>Protect outlier channels</span></label>' +
        (!LAB && HW ? '<div class="lq-ctl"><label class="lq-lab" for="' + id + '-gpu">GPU</label><select id="' + id + '-gpu" class="lq-gsel">' + Object.keys(HW.gpus).map(function (k) { return '<option value="' + k + '">' + esc(HW.gpus[k].name) + '</option>'; }).join('') + '</select></div>' : '') +
      '</div>' +
      '<p class="lq-desc"></p>' +
      '<div class="lq-body"><div class="lq-load">Generating the layer…</div></div>' +
      '<details class="lq-more"><summary>What this shows</summary><div>' +
        '<p>One linear layer of a transformer, generated here with a fixed seed: 1,024 input by 1,024 output channels, heavy-tailed like real checkpoints, with four input channels that carry outlier weights (118, 300, 640, 871) and eight that carry large activations in the 16-token calibration sample (37, 140, 262, 291, 455, 610, 777, 930). Every number is computed in your browser by quantising and dequantising the weights.</p>' +
        '<dl>' +
          '<dt>BF16</dt><dd>The usual checkpoint precision; the error is rounding noise.</dd>' +
          '<dt>FP8 E4M3</dt><dd>A floating-point grid, so small and large weights keep similar relative precision under one tensor scale.</dd>' +
          '<dt>INT8</dt><dd>An even grid per output channel; 255 levels absorb most outliers.</dd>' +
          '<dt>INT4</dt><dd>Sixteen levels. Per channel, one outlier coarsens the grid for 1,024 weights; with groups it only costs its own group, for a few hundredths of a bit in scales.</dd>' +
          '<dt>NVFP4</dt><dd>Sixteen floating-point levels per block of 16, with an FP8 scale for each block.</dd>' +
          '<dt>Protection</dt><dd>Activation-aware scaling as in AWQ: channels that see large activations are scaled up before quantisation, and the inverse is folded into the previous operation, so they land on finer steps at no memory cost. The exponent is grid-searched on the calibration sample.</dd>' +
        '</dl>' +
        (HW ? '<p>The "On this GPU" panel uses the catalogue\'s tensor-core rates only: a format is native when the GPU lists a rate for it; otherwise the weights are dequantised to the widest supported type at matmul time, which keeps the memory saving but not a compute speed-up. The per-token time is the 32B model\'s weights divided by ' + BW_EFF + ' of peak bandwidth, the same first-order, memory-bound model as the capacity planner.</p>' : '') +
        '<p>Weight error and SQNR measure the weights alone. Output error is what the next layer receives, which is why the heatmap can weight each error by its channel\'s activation. Neither is the real test: that is accuracy on your own eval set, which is what Optimize holds every candidate to with an accuracy floor.</p>' +
      '</div></details></div>';
    var $ = function (sel) { return root.querySelector(sel); };
    var lq = $('.lq'), body = $('.lq-body'), statusEl = $('.lq-status');
    var built = false, els = {};

    function fit() { var w = lq.clientWidth; lq.classList.toggle('lq-wide', w >= 1000); lq.classList.toggle('lq-mid', w >= 560 && w < 1000); }
    fit();
    if (window.ResizeObserver) new ResizeObserver(function () { fit(); redraw(); }).observe(lq);
    else window.addEventListener('resize', function () { fit(); redraw(); });
    var lastW = 0;
    function redraw() { if (!built || !cur) return; drawHeat(); var w = lq.clientWidth; if (w !== lastW) { lastW = w; drawHist(cur); drawInset(cur); } }

    function build() {
      body.innerHTML =
        '<div class="lq-metrics">' +
          '<div class="lq-m"><small>Bits per weight, incl. scales</small><b data-m="bits"></b><em data-m="bitsx"></em></div>' +
          '<div class="lq-m"><small>This layer</small><b data-m="layer"></b><em data-m="layerx"></em></div>' +
          '<div class="lq-m"><small>32B model, weights</small><b data-m="m32"></b><em data-m="m32x"></em></div>' +
          '<div class="lq-m"><small>70B model, weights</small><b data-m="m70"></b><em data-m="m70x"></em></div>' +
          '<div class="lq-m"><small>Weight error, RMSE / RMS</small><b data-m="werr"></b><em data-m="sqnr"></em></div>' +
          '<div class="lq-m"><small>Output error, ‖xW − xŴ‖ / ‖xW‖</small><b data-m="yerr"></b><em data-m="prot"></em></div>' +
        '</div>' +
        '<div class="lq-cols">' +
          '<div class="lq-col">' +
            '<div class="lq-panel"><div class="lq-ph"><b>Weight distribution</b><label class="lq-chk"><input type="checkbox" class="lq-log" checked>Log counts</label></div><svg class="lq-hist" viewBox="0 0 600 150" role="img" aria-label="Histogram of the layer\'s weights with the quantisation grid"></svg><p class="lq-cap lq-hsub"></p></div>' +
            (HW ? '<div class="lq-panel lq-gpu"><div class="lq-ph"><b class="lq-gname">On this GPU</b><span class="lq-gsub">from the datasheet</span></div><div class="lq-gbody"></div></div>' : '') +
          '</div>' +
          '<div class="lq-col">' +
            '<div class="lq-panel"><div class="lq-ph"><b>One group, as quantised</b><span class="lq-isub"></span></div><svg class="lq-inset" viewBox="0 0 300 150" role="img" aria-label="Weights of one group against the quantisation levels"></svg>' +
              '<div class="lq-key"><span><i class="lq-k-o"></i>weight</span><span><i class="lq-k-q"></i>quantised</span><span><i class="lq-k-g"></i>levels</span><span><i class="lq-k-s"></i>ch 291, 300</span></div></div>' +
          '</div>' +
          '<div class="lq-col">' +
            '<div class="lq-panel"><div class="lq-ph"><b>Error map</b><span class="lq-sp"></span><div class="lq-seg sm lq-hm" role="radiogroup" aria-label="Error map scale">' + segBtn('act', '× activation', 'hm') + segBtn('raw', 'Raw', 'hm') + '</div></div>' +
              '<div class="lq-heat"><div class="lq-marks"><i style="left:' + ((262 - TK0 + .5) / 64 * 100) + '%">262</i><i style="left:' + ((291 - TK0 + .5) / 64 * 100) + '%">291</i><i class="w" style="left:' + ((300 - TK0 + .5) / 64 * 100) + '%">300</i></div><canvas aria-hidden="true"></canvas></div>' +
              '<div class="lq-axes"><span>in 256 → 319</span><span>out 0 ↓ 63</span></div><div class="lq-legend"><span class="lq-lo"></span><i></i><span class="lq-hi"></span></div></div>' +
          '</div>' +
          '<div class="lq-col">' +
            '<div class="lq-panel"><div class="lq-ph"><b>All formats</b><span>this layer, current settings</span></div>' +
              '<div class="lq-cmp-h"><span>Format</span><span>Bits per weight</span><span>Output error, log</span></div><div class="lq-rows"></div>' +
              '<p class="lq-note">Pick a row to inspect it. Shorter bars are better.</p></div>' +
          '</div>' +
        '</div>';
      els.hist = $('.lq-hist'); els.inset = $('.lq-inset'); els.canvas = $('.lq-heat canvas'); els.rows = $('.lq-rows');
      els.hsub = $('.lq-hsub'); els.isub = $('.lq-isub'); els.lo = $('.lq-lo'); els.hi = $('.lq-hi'); els.leg = $('.lq-legend i'); els.gbody = $('.lq-gbody'); els.gname = $('.lq-gname'); els.gsub = $('.lq-gsub');
      $('.lq-log').addEventListener('change', function (e) { S.log = e.target.checked; drawHist(cur); });
      wireSeg($('.lq-hm'), 'hm', function (v) { S.heat = v; drawHeat(); });
      els.rows.addEventListener('click', function (e) { var r = e.target.closest('.lq-row'); if (r) setFmt(r.getAttribute('data-f')); });
      els.rows.addEventListener('keydown', function (e) { var r = e.target.closest('.lq-row'); if (r && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); setFmt(r.getAttribute('data-f')); } });
      built = true;
    }

    function wireSeg(seg, attr, fn) {
      var btns = [].slice.call(seg.querySelectorAll('button'));
      seg.addEventListener('click', function (e) { var b = e.target.closest('button'); if (b && !b.disabled) fn(b.getAttribute('data-' + attr)); });
      seg.addEventListener('keydown', function (e) {
        var i = btns.indexOf(document.activeElement); if (i < 0) return;
        var d = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0;
        if (!d) return; e.preventDefault();
        for (var j = 1; j <= btns.length; j++) { var b = btns[(i + d * j + btns.length * 2) % btns.length]; if (!b.disabled) { b.focus(); fn(b.getAttribute('data-' + attr)); break; } }
      });
    }
    function syncSeg(seg, attr, val, disabled) {
      [].forEach.call(seg.querySelectorAll('button'), function (b) {
        var on = String(b.getAttribute('data-' + attr)) === String(val);
        b.setAttribute('aria-checked', on ? 'true' : 'false'); b.tabIndex = on ? 0 : -1; b.disabled = !!disabled;
      });
    }
    wireSeg($('.lq-fmt'), 'fmt', function (v) { setFmt(v); });
    wireSeg($('.lq-grp'), 'g', function (v) { S.G = +v; update(); });
    $('.lq-prot').addEventListener('change', function (e) { S.prot = e.target.checked; update(); });
    function setFmt(f) { S.fmt = f; update(); }
    var gsel = $('.lq-gsel');
    if (gsel) gsel.addEventListener('change', function () { S.gpu = gsel.value; update(); });
    if (LAB) LAB.subscribe(function (m) { if (m.kind === 'gpu' && m.gpu !== S.gpu) { S.gpu = m.gpu; update(); } });
    function gpuSpec() { return HW ? HW.gpus[S.gpu] : null; }
    function tagFormats() {
      var g = gpuSpec(); if (!g) return;
      [].forEach.call($('.lq-fmt').querySelectorAll('button'), function (b) {
        var f = b.getAttribute('data-fmt'), sp = support(f, g);
        b.innerHTML = esc(short(f, S.G)) + (sp && !sp.native ? '<em>dequant</em>' : '');
        b.title = sp ? sp.how : '';
      });
    }
    function gpuPanel(r) {
      var g = gpuSpec(); if (!g || !els.gbody) return;
      var sp = support(S.fmt, g), f = g.flops || {};
      var rateT = f[sp.rate] || f.bf16, bytes32 = 32e9 * r.bits / 8, tMs = bytes32 / (g.bw * 1e12 * BW_EFF) * 1e3;
      els.gname.textContent = 'On ' + g.name;
      els.gsub.textContent = (HW.arch[g.arch] ? HW.arch[g.arch].name : g.arch) + ' · ' + g.mem + ' GB ' + g.memType + ' · ' + g.bw + ' TB/s';
      var rate = function (k) { return f[k] ? esc(fmtN(f[k])) : '<span class="dq">none</span>'; };
      var dl = document.createElement('dl'); dl.className = 'lq-on';
      dl.innerHTML = '<dt>BF16 · FP8 · FP4, TFLOPS</dt><dd>' + rate('bf16') + ' · ' + rate('fp8') + ' · ' + rate('fp4') + '</dd>' +
        '<dt>' + esc(short(S.fmt, S.G)) + ' here</dt><dd class="' + (sp.native ? 'ok' : 'dq') + '">' + (sp.native ? 'native' : 'dequantised → ' + sp.rate.toUpperCase()) + '</dd>' +
        '<dt>Matmul rate used</dt><dd>' + esc(fmtN(rateT) + ' TFLOPS ' + sp.rate) + '</dd>' +
        '<dt>32B weights to read</dt><dd>' + esc(gb(32 * r.bits / 8) + ' GB') + '</dd>' +
        '<dt>Per token, one stream</dt><dd>' + esc(tMs.toFixed(2) + ' ms · ≤ ' + Math.round(1000 / tMs) + ' tok/s') + '</dd>';
      var how = document.createElement('p'); how.className = 'lq-how'; how.textContent = sp.how + '. Read time = bytes ÷ (' + g.bw + ' TB/s × ' + BW_EFF + '); the matmul itself is not counted.'; how.title = how.textContent;
      els.gbody.innerHTML = ''; els.gbody.appendChild(dl); els.gbody.appendChild(how);
    }
    function fmtN(n) { return n == null ? '—' : Number(n).toLocaleString('en-GB'); }

    var cur = null;
    function update() {
      syncSeg($('.lq-fmt'), 'fmt', S.fmt);
      syncSeg($('.lq-grp'), 'g', S.G, S.fmt !== 'int4g');
      var gbtn = $('.lq-fmt [data-fmt="int4g"]'); if (!HW) gbtn.textContent = 'INT4 g' + S.G;
      $('.lq-desc').innerHTML = '<b>' + esc(name(S.fmt, S.G)) + '.</b> ' + esc(desc(S.fmt, S.G));
      if (!D) return;
      if (!built) build();
      syncSeg($('.lq-hm'), 'hm', S.heat);
      cur = result(S.fmt, S.G, S.prot);
      tagFormats(); metrics(cur); drawHist(cur); drawInset(cur); drawHeat(); bars(); gpuPanel(cur);
      var set = FMTS.map(function (f) { return [f, S.G, S.prot]; });
      enqueue(set, true);
      enqueue(FMTS.map(function (f) { return [f, S.G, !S.prot]; }).concat(GROUPS.map(function (g) { return ['int4g', g, S.prot]; })), false);
      status();
    }

    function status() {
      var busy = qBusy && queue.length > 0;
      statusEl.classList.toggle('busy', busy);
      statusEl.querySelector('span').textContent = !D ? 'Waiting' : busy ? 'Comparing formats…' : 'Computed in your browser';
    }

    function metrics(r) {
      var set = function (k, v, cls) { var e = root.querySelector('[data-m="' + k + '"]'); e.textContent = v; if (cls !== undefined) e.className = cls; };
      var ref = 16, mib = K * N * r.bits / 8 / 1048576;
      set('bits', r.bits.toFixed(r.bits % 1 ? 3 : 0));
      set('bitsx', r.fmt === 'bf16' ? 'reference' : (ref / r.bits).toFixed(2) + '× smaller', r.fmt === 'bf16' ? '' : 'ok');
      set('layer', mib.toFixed(2) + ' MiB'); set('layerx', 'BF16: 2.00 MiB', '');
      set('m32', gb(32 * r.bits / 8) + ' GB'); set('m32x', 'BF16: 64 GB', '');
      set('m70', gb(70 * r.bits / 8) + ' GB'); set('m70x', 'BF16: 140 GB', '');
      set('werr', pct(r.wErr)); set('sqnr', 'SQNR ' + r.sqnr.toFixed(1) + ' dB', '');
      set('yerr', pct(r.yErr));
      var p = '';
      if (S.prot) {
        if (r.fmt === 'bf16') p = 'protection not needed';
        else if (!r.alpha) p = 'no gain for this format';
        else {
          var off = result(r.fmt, r.G, false);
          p = 'α ' + r.alpha.toFixed(1) + ' · salient ×' + r.salMul.toFixed(1) + ' · was ' + pct(off.yErr);
        }
      } else p = 'calibration: 16 tokens';
      set('prot', p, S.prot && r.alpha ? 'ok' : '');
    }

    function bars() {
      if (!built) return;
      var maxB = 16, lo = Math.log10(1e-4), hi = Math.log10(1);
      els.rows.innerHTML = FMTS.map(function (f) {
        var r = cache[keyOf(f, S.G, S.prot)], b = bits(f, S.G);
        var e = r ? '<i style="width:' + Math.max(2, Math.min(100, (Math.log10(Math.max(r.yErr, 1e-4)) - lo) / (hi - lo) * 100)).toFixed(1) + '%"></i><span>' + pct(r.yErr) + '</span>' : '<span class="pend">computing…</span>';
        return '<div class="lq-row' + (f === S.fmt ? ' on' : '') + '" role="button" tabindex="0" aria-pressed="' + (f === S.fmt) + '" data-f="' + f + '">' +
          '<span class="lq-fn">' + esc(short(f, S.G)) + '</span>' +
          '<span class="lq-bar"><i style="width:' + (b / maxB * 100 * 0.78).toFixed(1) + '%"></i><span>' + b.toFixed(2) + '</span></span>' +
          '<span class="lq-bar">' + e + '</span></div>';
      }).join('');
    }

    function drawHist(r) {
      if (!r) return;
      var W = Math.max(300, Math.min(600, Math.round(els.hist.clientWidth || 600))), H = W < 450 ? 128 : 150, L = 34, R = 8, Tp = 8, B = 22, d = D, nb = d.hist.length;
      els.hist.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
      var max = 0; for (var i = 0; i < nb; i++) max = Math.max(max, d.hist[i]);
      var fy = function (c) {
        if (!c) return 0;
        return S.log ? Math.log10(c + 1) / Math.log10(max + 1) : c / max;
      };
      var X = function (v) { return L + (v + d.amax) / (2 * d.amax) * (W - L - R); };
      var Y = function (f) { return Tp + (1 - f) * (H - Tp - B); };
      var out = [], bw = (W - L - R) / nb;
      // y grid
      var yt = S.log ? [1, 10, 100, 1e3, 1e4, 1e5] : [0, .25, .5, .75, 1].map(function (f) { return Math.round(f * max); });
      yt.forEach(function (c) {
        if (c > max) return;
        var y = Y(fy(c));
        out.push('<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y.toFixed(1) + '" y2="' + y.toFixed(1) + '" stroke="var(--line2,#eef2f7)"/>');
        out.push('<text x="' + (L - 5) + '" y="' + (y + 3).toFixed(1) + '" text-anchor="end">' + (c >= 1000 ? (c / 1000) + 'k' : c) + '</text>');
      });
      // grid levels (scaled space, which equals original space for the unscaled channels)
      var lv = r.inset && r.inset.lv, nlv = 0;
      if (lv) {
        var vis = lv.filter(function (v) { return Math.abs(v) <= d.amax; });
        nlv = vis.length;
        var op = vis.length > 120 ? .22 : vis.length > 40 ? .35 : .6;
        vis.forEach(function (v) { var x = X(v).toFixed(1); out.push('<line x1="' + x + '" x2="' + x + '" y1="' + Tp + '" y2="' + (H - B) + '" stroke="var(--brand,#3f5cf6)" stroke-opacity="' + op + '" stroke-width=".8"/>'); });
      }
      // bars
      var p = '';
      for (i = 0; i < nb; i++) {
        var f = fy(d.hist[i]); if (!f) continue;
        var x = L + i * bw, y = Y(f);
        p += 'M' + x.toFixed(1) + ' ' + (H - B) + 'V' + y.toFixed(1) + 'H' + (x + bw - .6).toFixed(1) + 'V' + (H - B) + 'Z';
      }
      out.push('<path d="' + p + '" fill="var(--ink4,#94a3b8)" fill-opacity=".55"/>');
      out.push('<line x1="' + L + '" x2="' + (W - R) + '" y1="' + (H - B) + '" y2="' + (H - B) + '" stroke="var(--ink4,#94a3b8)"/>');
      [-d.amax, -d.amax / 2, 0, d.amax / 2, d.amax].forEach(function (v) {
        out.push('<text x="' + X(v).toFixed(1) + '" y="' + (H - 7) + '" text-anchor="middle">' + (v === 0 ? '0' : v.toFixed(2)) + '</text>');
      });
      els.hist.innerHTML = out.join('');
      els.hsub.textContent = !lv ? '1,048,576 weights · BF16 grid too fine to draw' : nlv + ' levels of the highlighted group';
    }

    function drawInset(r) {
      var I = r.inset, W = Math.max(260, Math.min(420, Math.round(els.inset.clientWidth || 300))), H = Math.round(W * (lq.classList.contains('lq-wide') ? 0.56 : 0.62)), L = 36, R = 6, Tp = 8, B = 16;
      els.inset.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
      var n = I.r1 - I.r0, m = 0, i;
      for (i = 0; i < n; i++) m = Math.max(m, Math.abs(I.a[i]), Math.abs(I.q[i]));
      m *= 1.08;
      var X = function (j) { return L + (j + .5) / n * (W - L - R); };
      var Y = function (v) { return Tp + (1 - (v + m) / (2 * m)) * (H - Tp - B); };
      var out = [];
      if (I.lv) {
        var vis = I.lv.filter(function (v) { return Math.abs(v) <= m; });
        var dense = vis.length > 60;
        vis.forEach(function (v) { var y = Y(v).toFixed(1); out.push('<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y + '" y2="' + y + '" stroke="var(--brand200,#bdcdff)" stroke-width="' + (dense ? .4 : .8) + '"/>'); });
      }
      out.push('<line x1="' + L + '" x2="' + (W - R) + '" y1="' + Y(0).toFixed(1) + '" y2="' + Y(0).toFixed(1) + '" stroke="var(--ink4,#94a3b8)" stroke-width=".6"/>');
      [m / 1.08, 0, -m / 1.08].forEach(function (v) { out.push('<text x="' + (L - 4) + '" y="' + (Y(v) + 3).toFixed(1) + '" text-anchor="end">' + (v === 0 ? '0' : v.toFixed(2)) + '</text>'); });
      var dw = Math.max(1.2, Math.min(4, (W - L - R) / n * .7));
      for (i = 0; i < n; i++) {
        var x = X(i), k = I.r0 + i, hl = k === 291 || k === 300;
        out.push('<line x1="' + (x - dw).toFixed(1) + '" x2="' + (x + dw).toFixed(1) + '" y1="' + Y(I.q[i]).toFixed(1) + '" y2="' + Y(I.q[i]).toFixed(1) + '" stroke="var(--brand,#3f5cf6)" stroke-width="1.6"/>');
        out.push('<circle cx="' + x.toFixed(1) + '" cy="' + Y(I.a[i]).toFixed(1) + '" r="' + (hl ? 3 : 1.5) + '" fill="' + (hl ? 'none' : 'var(--ink4,#94a3b8)') + '"' + (hl ? ' stroke="var(--brandD,#2737bd)" stroke-width="1.4"' : '') + '/>');
        if (hl) out.push('<text x="' + x.toFixed(1) + '" y="' + (Y(I.a[i]) + (I.a[i] >= 0 ? -6 : 13)).toFixed(1) + '" text-anchor="middle" style="fill:var(--brandD,#2737bd)">' + k + '</text>');
      }
      out.push('<text x="' + L + '" y="' + (H - 3) + '">in ' + I.r0 + '</text><text x="' + (W - R) + '" y="' + (H - 3) + '" text-anchor="end">' + (I.r1 - 1) + '</text>');
      els.inset.innerHTML = out.join('');
      var lvN = I.lv ? I.lv.filter(function (v, j, a) { return a.indexOf(v) === j; }).length : 0;
      els.isub.textContent = 'out ch ' + N0 + ' · ' + (I.glen >= K ? 'whole channel' : I.glen + ' weights') + (n < I.glen ? ', ' + n + ' shown' : '') + (I.lv ? ' · ' + lvN + ' levels' : '') + (S.prot && r.alpha ? ' · scaled' : '');
    }

    var ramp = null;
    function mkRamp() {
      var surf = getComputedStyle(lq).backgroundColor, dark = lum(surf) < 0.5, sm = surf.match(/\d+(\.\d+)?/g);
      var base = sm && sm.length >= 3 ? [+sm[0], +sm[1], +sm[2]] : (dark ? [17, 26, 48] : [255, 255, 255]);
      var stops = dark
        ? [[0, base], [.45, hex(css('--brand100', lq) || '#243576')], [.7, hex(css('--brand', lq) || '#3f5cf6')], [.88, [165, 180, 252]], [1, [238, 242, 255]]]
        : [[0, base], [.5, hex(css('--brand100', lq) || '#dbe5ff')], [.75, hex(css('--brand', lq) || '#3f5cf6')], [.9, hex(css('--brandD', lq) || '#2737bd')], [1, [30, 27, 75]]];
      ramp = new Uint8ClampedArray(256 * 3);
      for (var i = 0; i < 256; i++) {
        var t = i / 255, j = 0; while (j < stops.length - 2 && t > stops[j + 1][0]) j++;
        var a = stops[j], b = stops[j + 1], f = (t - a[0]) / (b[0] - a[0]);
        for (var c = 0; c < 3; c++) ramp[i * 3 + c] = a[1][c] + (b[1][c] - a[1][c]) * f;
      }
      els.leg.style.background = 'linear-gradient(90deg,' + [0, .5, .75, .9, 1].map(function (t) { var i = Math.round(t * 255) * 3; return 'rgb(' + ramp[i] + ',' + ramp[i + 1] + ',' + ramp[i + 2] + ')'; }).join(',') + ')';
    }
    function drawHeat() {
      if (!built || !cur) return;
      if (!ramp) mkRamp();
      var cv = els.canvas, w = cv.clientWidth; if (!w) return;
      var dpr = Math.min(window.devicePixelRatio || 1, 3), px = Math.round(w * dpr);
      if (cv.width !== px) { cv.width = px; cv.height = px; }
      var act = S.heat === 'act', lo = -5, hi = act ? 0 : -1.5;
      var off = document.createElement('canvas'); off.width = 64; off.height = TN;
      var ox = off.getContext('2d'), img = ox.createImageData(64, TN), tile = cur.tile;
      for (var n = 0; n < TN; n++) for (var k = 0; k < 64; k++) {
        var v = Math.abs(tile[n * 64 + k]) * (act ? D.xrms[TK0 + k] : 1);
        var t = v > 0 ? (Math.log10(v) - lo) / (hi - lo) : 0; t = t < 0 ? 0 : t > 1 ? 1 : t;
        var ri = Math.round(t * 255) * 3, p = (n * 64 + k) * 4;
        img.data[p] = ramp[ri]; img.data[p + 1] = ramp[ri + 1]; img.data[p + 2] = ramp[ri + 2]; img.data[p + 3] = 255;
      }
      ox.putImageData(img, 0, 0);
      var cx = cv.getContext('2d'); cx.imageSmoothingEnabled = false; cx.drawImage(off, 0, 0, px, px);
      els.lo.textContent = '1e−5'; els.hi.textContent = act ? '1' : '0.03';
    }

    insts.push({ bars: function () { if (cur) bars(); }, status: status });
    update();

    function start() {
      if (D) { update(); return; }
      statusEl.querySelector('span').textContent = 'Generating…';
      setTimeout(function () { gen(); update(); insts.forEach(function (i) { i.status(); }); }, 20);
    }
    if (D) start();
    else if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (es) { if (es.some(function (e) { return e.isIntersecting; })) { io.disconnect(); start(); } }, { rootMargin: '300px' });
      io.observe(root);
    } else start();
    // another instance may generate the data first
    root.__lqStart = start;
  }

  function init() {
    var els = document.querySelectorAll('[data-lab="quant"]');
    if (!els.length) return;
    injectCSS();
    [].forEach.call(els, mount);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
