/* Speculative decoding race: the same answer generated on one clock, by plain decoding and by
   draft-then-verify. Renders into every [data-lab="specdec"]. No libraries, no network. */
(function () {
  'use strict';

  var TEXT = 'To size the KV cache, start from the per-token footprint: two tensors (keys and values) per layer, times the number of KV heads, times the head dimension, times bytes per element. For an 8B model with 32 layers, 8 KV heads of 128 dimensions and an fp16 cache, that is 128 KiB per token, so a 32k-token context needs 4 GiB per sequence. Quantising the cache to fp8 halves that, and paged allocation stops long requests from reserving memory they never use.';
  var TOKENS = TEXT.match(/\s*[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*|\s*[^\sA-Za-z0-9]/g);
  var WRONG = ['the', 'a', 'memory', 'cache', 'model', 'each', 'all', 'one', 'it', 'which', 'per', 'size', 'in', 'of', 'two', 'layer'];
  var BASE_TPS = 60;      // baseline tokens/s the counters are scaled to
  var UNIT_MS = 150;      // real milliseconds per target forward pass on screen (playback is slowed down)
  var SLOW = Math.round(UNIT_MS / (1000 / BASE_TPS));
  var PRESETS = [
    { id: 'generic', label: 'Generic draft', a: 0.6 },
    { id: 'trained', label: 'Draft trained on your traffic', a: 0.85 }
  ];

  function expected(a, k, c) { var e = a >= 0.999 ? k + 1 : (1 - Math.pow(a, k + 1)) / (1 - a); return e / (1 + k * c); }
  function bestK(a, c) { var b = 1, bv = 0; for (var k = 1; k <= 8; k++) { var v = expected(a, k, c); if (v > bv) { bv = v; b = k; } } return b; }

  /* ───────────── styles ───────────── */
  var CSS = [
    '.ls{background:var(--white,#fff);border:1px solid var(--line,#e2e8f0);border-radius:12px;box-shadow:0 1px 2px rgba(16,24,40,.05);font-family:var(--font,system-ui,sans-serif);color:var(--ink2,#334155);font-size:13px;line-height:1.45;overflow:hidden;min-width:0}',
    '.ls *{box-sizing:border-box}',
    '.ls-bar{display:flex;flex-wrap:wrap;align-items:flex-end;gap:12px 20px;padding:14px 16px 12px;border-bottom:1px solid var(--line2,#eef2f7)}',
    '.ls-grp{display:flex;flex-direction:column;gap:5px;min-width:0}',
    '.ls-lab{font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--ink3,#5b687c);white-space:nowrap}',
    '.ls-lab output{font-family:var(--mono,monospace);font-variant-numeric:tabular-nums;text-transform:none;letter-spacing:0;color:var(--ink,#0f172a);font-weight:500;margin-left:6px}',
    '.ls-sym{text-transform:none;font-family:var(--mono,monospace);letter-spacing:0}',
    '.ls-seg{display:inline-flex;border:1px solid var(--line,#e2e8f0);border-radius:8px;padding:2px;background:var(--bg,#f5f6fa);flex-wrap:wrap}',
    '.ls-seg button,.ls-btn{font:inherit;font-size:12.5px;font-weight:500;color:var(--ink2,#334155);background:transparent;border:0;border-radius:6px;padding:5px 10px;cursor:pointer;white-space:nowrap;line-height:1.3}',
    '.ls-seg button:hover{color:var(--ink,#0f172a)}',
    '.ls-seg button[aria-pressed="true"]{background:var(--white,#fff);color:var(--brand,#3f5cf6);box-shadow:0 0 0 1px var(--brand200,#bdcdff),0 1px 2px rgba(16,24,40,.06)}',
    '.ls-seg button em{font-style:normal;font-family:var(--mono,monospace);font-size:11.5px;color:var(--ink3,#5b687c);margin-left:5px}',
    '.ls-seg button[aria-pressed="true"] em{color:var(--brand,#3f5cf6)}',
    '.ls-btn{border:1px solid var(--brand,#3f5cf6);background:var(--brand,#3f5cf6);color:#fff;display:inline-flex;align-items:center;gap:6px;padding:6px 12px}',
    '.ls-btn:hover{background:var(--brandD,#2737bd)}',
    '.ls-btn svg{width:12px;height:12px;fill:currentColor}',
    '.ls button:focus-visible,.ls input:focus-visible,.ls summary:focus-visible{outline:2px solid var(--brand,#3f5cf6);outline-offset:2px}',
    '.ls input[type=range]{width:130px;accent-color:var(--brand,#3f5cf6);margin:3px 0}',
    '.ls-end{margin-left:auto}',
    '.ls-race{display:grid;grid-template-columns:1fr 1fr;gap:0}',
    '.ls-pane{min-width:0;padding:14px 16px 12px;display:flex;flex-direction:column}',
    '.ls-pane+.ls-pane{border-left:1px solid var(--line2,#eef2f7)}',
    '.ls-ph{display:flex;align-items:baseline;justify-content:space-between;gap:10px;flex-wrap:wrap}',
    '.ls-ph b{color:var(--ink,#0f172a);font-weight:600;font-size:13.5px}',
    '.ls-ph span{font-size:12px;color:var(--ink3,#5b687c)}',
    '.ls-tps{font-family:var(--mono,monospace);font-variant-numeric:tabular-nums;font-size:22px;color:var(--ink,#0f172a);font-weight:500;margin-top:6px;line-height:1.2}',
    '.ls-tps em{font-style:normal;font-size:12px;color:var(--ink3,#5b687c);margin-left:4px}',
    '.ls-pane.ls-spec .ls-tps{color:var(--brand,#3f5cf6)}',
    '.ls-prog{height:3px;background:var(--line2,#eef2f7);border-radius:2px;margin:8px 0 10px;overflow:hidden}',
    '.ls-prog i{display:block;height:100%;width:0;background:var(--ink4,#94a3b8)}',
    '.ls-spec .ls-prog i{background:var(--brand,#3f5cf6)}',
    '.ls-txt{height:188px;overflow:hidden;font-size:14px;line-height:1.65;color:var(--ink,#0f172a);background:var(--bg,#f5f6fa);border:1px solid var(--line2,#eef2f7);border-radius:8px;padding:10px 12px;white-space:pre-wrap;word-break:break-word}',
    '.ls-txt span{border-radius:3px;transition:background-color .6s,color .3s}',
    '.ls-txt .ls-new{animation:ls-in .18s ease-out}',
    '.ls-txt .ls-draft{color:var(--ink4,#94a3b8);text-decoration:underline dotted var(--ink4,#94a3b8);text-underline-offset:3px}',
    '.ls-txt .ls-ver{background:var(--brand50,#eff4ff);color:var(--ink3,#5b687c)}',
    '.ls-txt .ls-acc{background:rgba(5,150,105,.16)}',
    '.ls-txt .ls-rej{color:var(--bad,#be123c);text-decoration:line-through;background:rgba(190,18,60,.08)}',
    '.ls-txt .ls-fix{background:var(--brand100,#dbe5ff)}',
    '.ls-txt .ls-cool{background:transparent}',
    '.ls-txt i.ls-car{display:inline-block;width:2px;height:1.05em;background:var(--brand,#3f5cf6);vertical-align:-2px;margin-left:1px;animation:ls-blink 1s steps(1) infinite}',
    '@keyframes ls-in{from{opacity:0}to{opacity:1}}',
    '@keyframes ls-blink{50%{opacity:0}}',
    '.ls-pf{display:flex;gap:14px;flex-wrap:wrap;margin-top:9px;font-size:11.5px;color:var(--ink3,#5b687c)}',
    '.ls-pf b{font-family:var(--mono,monospace);font-variant-numeric:tabular-nums;color:var(--ink,#0f172a);font-weight:500}',
    '.ls-bot{display:grid;grid-template-columns:minmax(0,1fr) minmax(240px,340px);border-top:1px solid var(--line2,#eef2f7);background:var(--bg,#f5f6fa)}',
    '.ls-met{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));align-content:start}',
    '.ls-m{padding:10px 14px;border-right:1px solid var(--line2,#eef2f7);border-bottom:1px solid var(--line2,#eef2f7);min-width:0}',
    '.ls-m small{display:block;font-size:11px;color:var(--ink3,#5b687c);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.ls-m b{display:block;font-family:var(--mono,monospace);font-variant-numeric:tabular-nums;font-size:17px;font-weight:500;color:var(--ink,#0f172a);margin-top:2px;white-space:nowrap}',
    '.ls-m b em{font-style:normal;font-size:11.5px;color:var(--ink3,#5b687c);margin-left:3px}',
    '.ls-m b.ls-up{color:var(--ok,#059669)}',
    '.ls-chart{padding:10px 14px 8px;min-width:0}',
    '.ls-chart small{display:block;font-size:11px;color:var(--ink3,#5b687c)}',
    '.ls-chart svg{display:block;width:100%;height:auto;margin-top:2px;overflow:visible}',
    '.ls-note{margin:0;padding:8px 16px;font-size:11.5px;color:var(--ink3,#5b687c);border-top:1px solid var(--line2,#eef2f7)}',
    '.ls-det{border-top:1px solid var(--line2,#eef2f7);padding:10px 16px;font-size:12.5px}',
    '.ls-det summary{cursor:pointer;font-weight:600;color:var(--ink,#0f172a)}',
    '.ls-det ul{margin:8px 0 2px 18px;padding:0;color:var(--ink3,#5b687c)}.ls-det li{margin:3px 0}',
    '.ls-det code{font-family:var(--mono,monospace);font-size:12px;color:var(--ink,#0f172a)}',
    '@media(max-width:720px){.ls-race{grid-template-columns:1fr}.ls-pane+.ls-pane{border-left:0;border-top:1px solid var(--line2,#eef2f7)}.ls-txt{height:150px;font-size:13.5px}.ls-bot{grid-template-columns:1fr}.ls-end{margin-left:0}}',
    '@media(max-width:560px){.ls-bar{padding:12px}.ls-pane{padding:12px}.ls-note,.ls-det{padding-left:12px;padding-right:12px}.ls input[type=range]{width:120px}}'
  ].join('\n');
  function injectCss() {
    if (document.getElementById('lab-specdec-css')) return;
    var s = document.createElement('style'); s.id = 'lab-specdec-css'; s.textContent = CSS; document.head.appendChild(s);
  }
  var ICON_PLAY = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M3 1.5v9l7.5-4.5z"/></svg>';
  var ICON_REPLAY = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M6 1.5a4.5 4.5 0 1 0 4.4 5.4l-1.5-.3A3 3 0 1 1 6 3v1.6l2.6-2.3L6 0z"/></svg>';
  function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;'); }

  /* ───────────── widget ───────────── */
  var uid = 0;
  function mount(root) {
    if (root.__ls) return; root.__ls = true;
    var id = 'ls' + (++uid);
    var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    var st = { a: 0.85, k: 4, c: 0.06 };

    root.innerHTML =
      '<div class="ls">' +
      '<div class="ls-bar">' +
      '<div class="ls-grp"><span class="ls-lab" id="' + id + 'p">Draft model</span><div class="ls-seg" role="group" aria-labelledby="' + id + 'p">' +
      PRESETS.map(function (p) { return '<button type="button" data-a="' + p.a + '" aria-pressed="' + (p.a === st.a) + '">' + p.label + '<em>α≈' + p.a + '</em></button>'; }).join('') + '</div></div>' +
      '<div class="ls-grp"><label class="ls-lab" for="' + id + 'a">Acceptance <span class="ls-sym">α</span><output data-o="a"></output></label><input id="' + id + 'a" type="range" min="0.3" max="0.95" step="0.01" data-k="a"></div>' +
      '<div class="ls-grp"><label class="ls-lab" for="' + id + 'k">Draft length <span class="ls-sym">k</span><output data-o="k"></output></label><input id="' + id + 'k" type="range" min="1" max="8" step="1" data-k="k"></div>' +
      '<div class="ls-grp"><label class="ls-lab" for="' + id + 'c">Draft cost <span class="ls-sym">c</span><output data-o="c"></output></label><input id="' + id + 'c" type="range" min="0.02" max="0.3" step="0.01" data-k="c"></div>' +
      '<div class="ls-grp ls-end"><button type="button" class="ls-btn" data-act="run"></button></div>' +
      '</div>' +
      '<div class="ls-race">' +
      pane('base', 'Baseline', '1 token per forward pass') +
      pane('spec', 'Speculative', 'draft k tokens, verify in one pass') +
      '</div>' +
      '<div class="ls-bot"><div class="ls-met">' +
      '<div class="ls-m"><small>Measured speed-up</small><b data-m="up">—</b></div>' +
      '<div class="ls-m"><small>Tokens per verify pass</small><b data-m="tpp">—</b></div>' +
      '<div class="ls-m"><small>Draft tokens accepted</small><b data-m="acc">—</b></div>' +
      '<div class="ls-m"><small>Expected speed-up</small><b data-m="exp">—</b></div>' +
      '<div class="ls-m"><small>Best k at this α and c</small><b data-m="best">—</b></div>' +
      '</div><div class="ls-chart"><small>Expected speed-up against draft length k</small><svg viewBox="0 0 300 120" role="img" aria-label="Expected speed-up for draft lengths 1 to 8"></svg></div></div>' +
      '<p class="ls-note">Same text, same target model, one clock. Playback is slowed ' + SLOW + '× so each step can be followed; the counters show real-time rates for a ' + BASE_TPS + ' tok/s baseline.</p>' +
      '<details class="ls-det"><summary>What the simulation models</summary><ul>' +
      '<li>The baseline runs one target-model forward pass per token, scaled to ' + BASE_TPS + ' tokens per second.</li>' +
      '<li>Each speculative step runs the draft model k times, at <code>c</code> of a target pass each, then one target pass that checks all k drafts at once: <code>k·c + 1</code> target-pass units.</li>' +
      '<li>Each draft token is accepted with probability α, independently, until the first rejection. The verify pass always yields one token of its own: the correction for the rejected draft, or a bonus token when all k are accepted. The output is exactly what the target model would have written alone.</li>' +
      '<li>Expected speed-up: <code>(1 − α^(k+1)) / (1 − α) ÷ (1 + k·c)</code>. Longer drafts pay off only while α is high; drafts trained on your own traffic (EAGLE-style heads) usually accept more than a generic small model.</li>' +
      '<li>It ignores batching: at large batch sizes the verify pass stops being nearly free and the gain shrinks. Figures come from this model, not from measurements of any product.</li>' +
      '</ul></details></div>';

    function pane(kind, title, sub) {
      return '<div class="ls-pane ls-' + kind + '" data-p="' + kind + '"><div class="ls-ph"><b>' + title + '</b><span>' + sub + '</span></div>' +
        '<div class="ls-tps" data-v="tps">0<em>tok/s</em></div><div class="ls-prog"><i></i></div>' +
        '<div class="ls-txt" aria-hidden="true"></div>' +
        '<div class="ls-pf"><span>Tokens <b data-v="n">0</b></span><span>Target passes <b data-v="fp">0</b></span><span>Time <b data-v="t">0.00 s</b></span></div></div>';
    }

    var el = root.querySelector('.ls'), runBtn = el.querySelector('[data-act="run"]');
    var inputs = {}, outs = {};
    ['a', 'k', 'c'].forEach(function (k) { inputs[k] = el.querySelector('[data-k="' + k + '"]'); outs[k] = el.querySelector('[data-o="' + k + '"]'); });
    var M = {}; [].forEach.call(el.querySelectorAll('[data-m]'), function (b) { M[b.getAttribute('data-m')] = b; });
    var P = {};
    ['base', 'spec'].forEach(function (k) {
      var p = el.querySelector('[data-p="' + k + '"]');
      P[k] = { txt: p.querySelector('.ls-txt'), tps: p.querySelector('[data-v="tps"]'), n: p.querySelector('[data-v="n"]'), fp: p.querySelector('[data-v="fp"]'), t: p.querySelector('[data-v="t"]'), prog: p.querySelector('.ls-prog i') };
    });
    var svg = el.querySelector('.ls-chart svg');

    function syncInputs() {
      inputs.a.value = st.a; inputs.k.value = st.k; inputs.c.value = st.c;
      outs.a.textContent = (+st.a).toFixed(2); outs.k.textContent = st.k; outs.c.textContent = (+st.c).toFixed(2);
      [].forEach.call(el.querySelectorAll('.ls-seg button'), function (b) { b.setAttribute('aria-pressed', Math.abs(+b.getAttribute('data-a') - st.a) < 0.005 ? 'true' : 'false'); });
      chart(); M.exp.innerHTML = expected(st.a, st.k, st.c).toFixed(2) + '<em>×</em>'; M.best.textContent = bestK(st.a, st.c);
    }
    function chart() {
      var W = 300, H = 120, L = 30, R = 10, T = 12, B = 20, vals = [], k, mx = 1;
      for (k = 1; k <= 8; k++) { vals.push(expected(st.a, k, st.c)); }
      mx = Math.max(2, Math.ceil(Math.max.apply(null, vals) + 0.25));
      var X = function (k) { return L + (k - 1) / 7 * (W - L - R); }, Y = function (v) { return T + (1 - v / mx) * (H - T - B); };
      var g = [], bk = bestK(st.a, st.c);
      for (var v = 0; v <= mx; v++) g.push('<line x1="' + L + '" x2="' + (W - R) + '" y1="' + Y(v) + '" y2="' + Y(v) + '" stroke="var(--line,#e2e8f0)" stroke-width="1"' + (v === 1 ? ' stroke-dasharray="3 3" stroke="var(--ink4,#94a3b8)"' : '') + '/><text x="' + (L - 6) + '" y="' + (Y(v) + 3.5) + '" text-anchor="end" font-size="10" font-family="var(--mono,monospace)" fill="var(--ink3,#5b687c)">' + v + '×</text>');
      for (k = 1; k <= 8; k++) g.push('<text x="' + X(k) + '" y="' + (H - 5) + '" text-anchor="middle" font-size="10" font-family="var(--mono,monospace)" fill="' + (k === st.k ? 'var(--brand,#3f5cf6)' : 'var(--ink3,#5b687c)') + '"' + (k === st.k ? ' font-weight="600"' : '') + '>' + k + '</text>');
      g.push('<polyline fill="none" stroke="var(--brand,#3f5cf6)" stroke-width="1.75" stroke-linejoin="round" points="' + vals.map(function (v, i) { return X(i + 1).toFixed(1) + ',' + Y(v).toFixed(1); }).join(' ') + '"/>');
      for (k = 1; k <= 8; k++) {
        var cur = k === st.k;
        g.push('<circle cx="' + X(k).toFixed(1) + '" cy="' + Y(vals[k - 1]).toFixed(1) + '" r="' + (cur ? 4.5 : 2.5) + '" fill="' + (cur ? 'var(--brand,#3f5cf6)' : 'var(--white,#fff)') + '" stroke="var(--brand,#3f5cf6)" stroke-width="1.5"/>');
      }
      var by = Y(vals[bk - 1]) - 9;
      g.push('<text x="' + Math.min(W - R - 2, Math.max(L + 14, X(bk))).toFixed(1) + '" y="' + Math.max(9, by).toFixed(1) + '" text-anchor="middle" font-size="10" font-family="var(--font,sans-serif)" font-weight="600" fill="var(--ok,#059669)">best</text>');
      svg.innerHTML = g.join('');
    }

    /* race */
    var N = TOKENS.length, race = null, playing = false, visible = true, last = 0, doneAt = null;
    function build() {
      var ev = [], i, t = 0, pos = 0, steps = 0, drafted = 0, accepted = 0;
      for (i = 0; i < N; i++) ev.push({ t: i + 1, side: 'base', i: i });
      while (pos < N) {
        var ke = Math.min(st.k, N - pos), n = 0;
        while (n < ke && Math.random() < st.a) n++;
        for (i = 0; i < ke; i++) ev.push({ t: t + (i + 1) * st.c, side: 'spec', type: 'draft', j: i, pos: pos, ke: ke, n: n });
        t += ke * st.c;
        ev.push({ t: t + 0.0001, side: 'spec', type: 'verify', pos: pos, ke: ke });
        t += 1;
        var gain = Math.min(n + 1, N - pos);
        ev.push({ t: t, side: 'spec', type: 'resolve', pos: pos, ke: ke, n: n, gain: gain });
        steps++; drafted += ke; accepted += n; pos += gain;
      }
      ev.sort(function (x, y) { return x.t - y.t || (x.side === 'base' ? -1 : 1); });
      return { ev: ev, ei: 0, now: 0, base: { n: 0, fp: 0, end: N }, spec: { n: 0, fp: 0, end: t, acc: 0, dr: 0, steps: 0 }, drafts: [] };
    }
    function span(text, cls) { var s = document.createElement('span'); s.className = cls; s.textContent = text; return s; }
    function caret(p) { var c = p.txt.querySelector('.ls-car'); if (!c) { c = document.createElement('i'); c.className = 'ls-car'; } p.txt.appendChild(c); p.txt.scrollTop = p.txt.scrollHeight; }
    function wrongFor(tok) {
      var lead = tok.match(/^\s*/)[0], w = tok.trim(), pick;
      do { pick = WRONG[Math.floor(Math.random() * WRONG.length)]; } while (pick.toLowerCase() === w.toLowerCase());
      return (lead || ' ') + pick;
    }
    function cool(s, ms) { setTimeout(function () { s.classList.add('ls-cool'); }, ms); }
    function apply(e) {
      var S, p;
      if (e.side === 'base') {
        p = P.base; S = race.base; S.n++; S.fp++;
        p.txt.appendChild(span(TOKENS[e.i], 'ls-new')); caret(p); return;
      }
      p = P.spec; S = race.spec;
      if (e.type === 'draft') {
        var tok = e.j < e.n ? TOKENS[e.pos + e.j] : (e.j === e.n ? wrongFor(TOKENS[e.pos + e.j]) : TOKENS[e.pos + e.j]);
        var d = span(tok, 'ls-draft ls-new'); race.drafts.push(d); p.txt.appendChild(d); caret(p);
      } else if (e.type === 'verify') {
        race.drafts.forEach(function (d) { d.classList.add('ls-ver'); });
      } else {
        S.fp++; S.steps++; S.dr += e.ke; S.acc += e.n;
        race.drafts.forEach(function (d, j) {
          d.classList.remove('ls-draft', 'ls-ver', 'ls-new');
          if (j < e.n) { d.classList.add('ls-acc'); cool(d, 650); }
          else if (j === e.n) {
            d.classList.add('ls-rej');
            (function (dd) { setTimeout(function () { if (dd.parentNode) dd.parentNode.removeChild(dd); }, 420); })(d);
          } else d.parentNode && d.parentNode.removeChild(d);
        });
        race.drafts = [];
        if (e.gain > e.n) { var f = span(TOKENS[e.pos + e.n], 'ls-fix ls-new'); p.txt.appendChild(f); cool(f, 650); }
        S.n += e.gain; caret(p);
      }
    }
    function counters() {
      var now = race.now;
      ['base', 'spec'].forEach(function (k) {
        var S = race[k], p = P[k], tEnd = Math.min(now, S.end), tps = tEnd > 0 ? S.n / tEnd * BASE_TPS : 0;
        p.tps.innerHTML = Math.round(tps) + '<em>tok/s</em>';
        p.n.textContent = S.n + ' / ' + N; p.fp.textContent = S.fp; p.t.textContent = (tEnd / BASE_TPS).toFixed(2) + ' s';
        p.prog.style.width = (S.n / N * 100).toFixed(1) + '%';
      });
      var b = race.base, s = race.spec;
      var bt = b.n ? Math.min(now, b.end) / b.n : 0, stt = s.n ? Math.min(now, s.end) / s.n : 0;
      if (s.n > 8 && bt && stt) { var up = bt / stt; M.up.innerHTML = up.toFixed(2) + '<em>×</em>'; M.up.className = up > 1.05 ? 'ls-up' : ''; } else { M.up.innerHTML = '—'; M.up.className = ''; }
      M.tpp.textContent = s.steps ? (s.n / s.steps).toFixed(2) : '—';
      M.acc.innerHTML = s.dr ? Math.round(s.acc / s.dr * 100) + '<em>%</em>' : '—';
    }
    function start() {
      race = build(); doneAt = null;
      P.base.txt.textContent = ''; P.spec.txt.textContent = ''; caret(P.base); caret(P.spec);
      counters(); setPlaying(true);
    }
    function setPlaying(v) {
      playing = v; last = 0;
      runBtn.innerHTML = race && (v || race.ei > 0) ? ICON_REPLAY + 'Replay' : ICON_PLAY + 'Run';
    }
    function tick(ts) {
      requestAnimationFrame(tick);
      var dt = last ? Math.min(100, ts - last) : 0; last = ts;
      if (!race || !playing || !visible || document.hidden) return;
      if (doneAt !== null) {
        doneAt += dt;
        if (doneAt > 2600) { if (reduce) { setPlaying(false); doneAt = null; return; } start(); }
        return;
      }
      race.now += dt / UNIT_MS;
      while (race.ei < race.ev.length && race.ev[race.ei].t <= race.now) apply(race.ev[race.ei++]);
      counters();
      if (race.ei >= race.ev.length) { race.now = Math.max(race.base.end, race.spec.end); counters(); doneAt = 0; }
    }

    el.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      if (b.hasAttribute('data-a')) { st.a = +b.getAttribute('data-a'); syncInputs(); start(); }
      else if (b.getAttribute('data-act') === 'run') start();
    });
    ['a', 'k', 'c'].forEach(function (k) {
      inputs[k].addEventListener('input', function () { st[k] = +inputs[k].value; syncInputs(); });
      inputs[k].addEventListener('change', function () { if (!reduce || playing) start(); });
    });

    syncInputs();
    race = build(); counters(); caret(P.base); caret(P.spec);
    setPlaying(false);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) {
        visible = es[0].isIntersecting; last = 0;
        if (visible && !reduce && race.ei === 0 && !playing) start();
      }, { threshold: 0.2 }).observe(el);
    } else if (!reduce) start();
    document.addEventListener('visibilitychange', function () { last = 0; });
    requestAnimationFrame(tick);
  }

  function init() { injectCss(); [].forEach.call(document.querySelectorAll('[data-lab="specdec"]'), mount); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
