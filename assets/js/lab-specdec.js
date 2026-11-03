/* Speculative decoding race: the same answer generated on one clock, by plain decoding and by
   draft-then-verify. Renders into every [data-lab="specdec"]. No libraries, no network.
   The baseline rate comes from the selected GPU (window.VO_LAB, or a local select) with the same
   first-order model the capacity planner uses: single-stream decode is bound by reading the weights. */
(function () {
  'use strict';

  var TEXT = 'To size the KV cache, start from the per-token footprint: two tensors (keys and values) per layer, times the number of KV heads, times the head dimension, times bytes per element. For an 8B model with 32 layers, 8 KV heads of 128 dimensions and an fp16 cache, that is 128 KiB per token, so a 32k-token context needs 4 GiB per sequence. Quantising the cache to fp8 halves that, and paged allocation stops long requests from reserving memory they never use.';
  var TOKENS = TEXT.match(/\s*[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*|\s*[^\sA-Za-z0-9]/g);
  var WRONG = ['the', 'a', 'memory', 'cache', 'model', 'each', 'all', 'one', 'it', 'which', 'per', 'size', 'in', 'of', 'two', 'layer'];
  var UNIT_MS = 150;      // real milliseconds per target forward pass on screen (playback is slowed down)
  var BW_EFF = 0.75;      // share of peak bandwidth a decode step reaches (assumption, same as the planner)
  var DRAFT_BYTES = 1.0e9; // a 1B-class draft model in fp8
  var MODELS = [
    { id: 'llama8b', name: 'Llama 3.1 8B', bytes: 8.03e9 },
    { id: 'qwen32b', name: 'Qwen3 32B', bytes: 32.8e9 }
  ];
  var PRESETS = [
    { id: 'generic', label: 'Generic draft', a: 0.6 },
    { id: 'trained', label: 'Draft trained on your traffic', a: 0.85 }
  ];
  var HW = window.VO_HW || null;

  function expected(a, k, c) { var e = a >= 0.999 ? k + 1 : (1 - Math.pow(a, k + 1)) / (1 - a); return e / (1 + k * c); }
  function bestK(a, c) { var b = 1, bv = 0; for (var k = 1; k <= 8; k++) { var v = expected(a, k, c); if (v > bv) { bv = v; b = k; } } return b; }
  function fmt(n, d) { return Number(n).toLocaleString('en-GB', { maximumFractionDigits: d == null ? 0 : d, minimumFractionDigits: d == null ? 0 : d }); }
  function gbs(bytes) { return (bytes / 1e9).toFixed(bytes >= 1e10 ? 1 : 2) + ' GB'; }
  /* a surface's luminance decides the tints: the shell's dark scope and the page's light one use the same classes */
  function lum(c) {
    var m = (c || '').match(/\d+(\.\d+)?/g); if (!m || m.length < 3) return 1;
    return (0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]) / 255;
  }

  /* ───────────── styles ───────────── */
  var CSS = [
    '.ls{--ls-acc:rgba(5,150,105,.16);--ls-accT:inherit;--ls-rej:var(--bad,#be123c);--ls-rejB:rgba(190,18,60,.08);--ls-draft:var(--ink4,#94a3b8);',
    '  background:var(--white,#fff);border:1px solid var(--line,#e2e8f0);border-radius:12px;box-shadow:0 1px 2px rgba(16,24,40,.05);font-family:var(--font,system-ui,sans-serif);color:var(--ink2,#334155);font-size:13px;line-height:1.45;overflow:hidden;min-width:0}',
    '.ls.ls-dark{--ls-acc:rgba(52,211,153,.25);--ls-accT:#34d399;--ls-rej:#f87171;--ls-rejB:rgba(248,113,113,.14);--ls-draft:#8e9ab3}',
    '.ls *{box-sizing:border-box}',
    '.ls-bar{display:flex;flex-wrap:wrap;align-items:flex-end;gap:10px 18px;padding:12px 16px 10px;border-bottom:1px solid var(--line2,#eef2f7)}',
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
    '.ls select{font:inherit;font-size:12.5px;color:var(--ink,#0f172a);background:var(--white,#fff);border:1px solid var(--line,#e2e8f0);border-radius:7px;padding:5px 8px;max-width:100%}',
    '.ls-btn{border:1px solid var(--brand,#3f5cf6);background:var(--brand,#3f5cf6);color:#fff;display:inline-flex;align-items:center;gap:6px;padding:6px 12px}',
    '.ls-btn:hover{background:var(--brandD,#2737bd)}',
    '.ls-btn:disabled{opacity:.5;cursor:default}',
    '.ls-btn svg{width:12px;height:12px;fill:currentColor}',
    '.ls button:focus-visible,.ls input:focus-visible,.ls select:focus-visible,.ls summary:focus-visible{outline:2px solid var(--brand,#3f5cf6);outline-offset:2px}',
    '.ls input[type=range]{width:120px;accent-color:var(--brand,#3f5cf6);margin:3px 0}',
    '.ls-end{margin-left:auto}',
    '.ls-race{display:grid;grid-template-columns:1fr 1fr;gap:0}',
    '.ls-pane{min-width:0;padding:10px 16px 10px;display:flex;flex-direction:column}',
    '.ls-pane+.ls-pane{border-left:1px solid var(--line2,#eef2f7)}',
    '.ls-ph{display:flex;align-items:baseline;justify-content:space-between;gap:10px;flex-wrap:wrap}',
    '.ls-ph b{color:var(--ink,#0f172a);font-weight:600;font-size:13.5px}',
    '.ls-ph span{font-size:12px;color:var(--ink3,#5b687c)}',
    '.ls-tps{font-family:var(--mono,monospace);font-variant-numeric:tabular-nums;font-size:21px;color:var(--ink,#0f172a);font-weight:500;margin-top:4px;line-height:1.2;display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}',
    '.ls-tps em{font-style:normal;font-size:12px;color:var(--ink3,#5b687c)}',
    '.ls-tps small{font-family:var(--mono,monospace);font-size:11px;color:var(--ink3,#5b687c);font-weight:400}',
    '.ls-pane.ls-spec .ls-tps{color:var(--brand,#3f5cf6)}',
    '.ls-prog{height:3px;background:var(--line2,#eef2f7);border-radius:2px;margin:6px 0 8px;overflow:hidden}',
    '.ls-prog i{display:block;height:100%;width:0;background:var(--ink4,#94a3b8)}',
    '.ls-spec .ls-prog i{background:var(--brand,#3f5cf6)}',
    '.ls-txt{height:176px;overflow:hidden;font-size:13.5px;line-height:1.6;color:var(--ink,#0f172a);background:var(--bg,#f5f6fa);border:1px solid var(--line2,#eef2f7);border-radius:8px;padding:9px 12px;white-space:pre-wrap;word-break:break-word}',
    '.ls-txt span{border-radius:3px;transition:background-color .6s,color .3s}',
    '.ls-txt .ls-new{animation:ls-in .18s ease-out}',
    '.ls-txt .ls-draft{color:var(--ls-draft);text-decoration:underline dotted var(--ls-draft);text-underline-offset:3px}',
    '.ls-txt .ls-ver{background:var(--brand50,#eff4ff);color:var(--ink3,#5b687c)}',
    '.ls-txt .ls-acc{background:var(--ls-acc);color:var(--ls-accT)}',
    '.ls-txt .ls-rej{color:var(--ls-rej);text-decoration:line-through;background:var(--ls-rejB)}',
    '.ls-txt .ls-fix{background:var(--brand100,#dbe5ff)}',
    '.ls-txt .ls-cool{background:transparent;color:inherit}',
    '.ls-txt i.ls-car{display:inline-block;width:2px;height:1.05em;background:var(--brand,#3f5cf6);vertical-align:-2px;margin-left:1px;animation:ls-blink 1s steps(1) infinite}',
    '@keyframes ls-in{from{opacity:0}to{opacity:1}}',
    '@keyframes ls-blink{50%{opacity:0}}',
    '.ls-pf{display:flex;gap:14px;flex-wrap:wrap;margin-top:8px;font-size:11.5px;color:var(--ink3,#5b687c)}',
    '.ls-pf b{font-family:var(--mono,monospace);font-variant-numeric:tabular-nums;color:var(--ink,#0f172a);font-weight:500}',
    '.ls-bot{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);border-top:1px solid var(--line2,#eef2f7);background:var(--bg,#f5f6fa)}',
    '.ls-met{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));align-content:start}',
    '.ls-m{padding:8px 14px;border-right:1px solid var(--line2,#eef2f7);border-bottom:1px solid var(--line2,#eef2f7);min-width:0}',
    '.ls-m small{display:block;font-size:11px;color:var(--ink3,#5b687c);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.ls-m b{display:block;font-family:var(--mono,monospace);font-variant-numeric:tabular-nums;font-size:16px;font-weight:500;color:var(--ink,#0f172a);margin-top:2px;white-space:nowrap}',
    '.ls-m b em{font-style:normal;font-size:11.5px;color:var(--ink3,#5b687c);margin-left:3px}',
    '.ls-m b.ls-up{color:var(--ok,#059669)}',
    '.ls-chart{padding:8px 14px 6px;min-width:0;border-bottom:1px solid var(--line2,#eef2f7)}',
    '.ls-chart small{display:block;font-size:11px;color:var(--ink3,#5b687c)}',
    '.ls-chart svg{display:block;width:100%;max-height:104px;height:auto;margin:2px auto 0;overflow:visible}',
    '.ls-note{margin:0;padding:7px 16px;font-size:11.5px;color:var(--ink3,#5b687c)}',
    '.ls-note.ls-warn{color:var(--warn,#b45309)}',
    '.ls-det{border-top:1px solid var(--line2,#eef2f7);padding:9px 16px;font-size:12.5px}',
    '.ls-det summary{cursor:pointer;font-weight:600;color:var(--ink,#0f172a)}',
    '.ls-det ul{margin:8px 0 2px 18px;padding:0;color:var(--ink3,#5b687c)}.ls-det li{margin:3px 0}',
    '.ls-det code{font-family:var(--mono,monospace);font-size:12px;color:var(--ink,#0f172a)}',
    '@media(max-width:720px){.ls-race{grid-template-columns:1fr}.ls-pane+.ls-pane{border-left:0;border-top:1px solid var(--line2,#eef2f7)}.ls-txt{height:140px;font-size:13px}.ls-bot{grid-template-columns:1fr}.ls-end{margin-left:0}.ls-met{grid-template-columns:repeat(auto-fit,minmax(120px,1fr))}}',
    '@media(max-width:560px){.ls-bar{padding:12px}.ls-pane{padding:12px}.ls-note,.ls-det{padding-left:12px;padding-right:12px}.ls input[type=range]{width:110px}}',
    '@media (prefers-reduced-motion:reduce){.ls-txt span{transition:none}.ls-txt .ls-new{animation:none}.ls-txt i.ls-car{animation:none}}'
  ].join('\n');
  function injectCss() {
    if (document.getElementById('lab-specdec-css')) return;
    var s = document.createElement('style'); s.id = 'lab-specdec-css'; s.textContent = CSS; document.head.appendChild(s);
  }
  var ICON_PLAY = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M3 1.5v9l7.5-4.5z"/></svg>';
  var ICON_REPLAY = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M6 1.5a4.5 4.5 0 1 0 4.4 5.4l-1.5-.3A3 3 0 1 1 6 3v1.6l2.6-2.3L6 0z"/></svg>';
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }

  /* ───────────── widget ───────────── */
  var uid = 0;
  function mount(root) {
    if (root.__ls) return; root.__ls = true;
    var id = 'ls' + (++uid);
    var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    var LAB = window.VO_LAB || null;
    var st = { a: 0.85, k: 4, c: 0.12, model: 'llama8b', gpu: LAB ? LAB.gpu : 'h100' };
    var BASE_TPS = 60, SLOW = 9, fits = true;   // overwritten by derive()

    var gpuCtl = !LAB && HW ? '<div class="ls-grp"><label class="ls-lab" for="' + id + 'g" data-tip="The GPU whose datasheet bandwidth and memory set the baseline rate.">GPU</label><select id="' + id + 'g" data-sel="gpu">' +
      Object.keys(HW.gpus).map(function (k) { return '<option value="' + k + '">' + esc(HW.gpus[k].name) + '</option>'; }).join('') + '</select></div>' : '';

    root.innerHTML =
      '<div class="ls">' +
      '<div class="ls-bar">' +
      '<div class="ls-grp"><label class="ls-lab" for="' + id + 'm" data-tip="The model that produces the final answer, with fp8 weights. Its weight bytes set the baseline rate: one stream reads every weight once per token.">Target model · fp8</label><select id="' + id + 'm" data-sel="model">' +
      MODELS.map(function (m) { return '<option value="' + m.id + '">' + esc(m.name) + ' · ' + gbs(m.bytes) + '</option>'; }).join('') + '</select></div>' +
      gpuCtl +
      '<div class="ls-grp"><span class="ls-lab" id="' + id + 'p" data-tip="The small model that proposes tokens. The presets set the acceptance rate α; the draft cost c comes from its size against the target.">Draft model</span><div class="ls-seg" role="group" aria-labelledby="' + id + 'p">' +
      PRESETS.map(function (p) { return '<button type="button" data-a="' + p.a + '" aria-pressed="' + (p.a === st.a) + '" data-tip="' + (p.id === 'generic' ? 'A small off-the-shelf model as the draft: about 60% of its tokens match the target, a typical figure for unrelated drafts.' : 'A draft head trained on the deployment\'s own traffic, EAGLE-style: about 85% of its tokens match the target.') + '">' + p.label + '<em>α≈' + p.a + '</em></button>'; }).join('') + '</div></div>' +
      '<div class="ls-grp"><label class="ls-lab" for="' + id + 'a" data-tip="Probability that each draft token matches what the target would have produced, treated as independent per token. Drafting stops at the first mismatch.">Acceptance <span class="ls-sym">α</span><output data-o="a"></output></label><input id="' + id + 'a" type="range" min="0.3" max="0.95" step="0.01" data-k="a"></div>' +
      '<div class="ls-grp"><label class="ls-lab" for="' + id + 'k" data-tip="Tokens the draft proposes before one verify pass. A longer draft can yield more tokens per pass but costs k draft passes, and later tokens are less likely to be reached.">Draft length <span class="ls-sym">k</span><output data-o="k"></output></label><input id="' + id + 'k" type="range" min="1" max="8" step="1" data-k="k"></div>' +
      '<div class="ls-grp"><label class="ls-lab" for="' + id + 'c" data-tip="Cost of one draft pass as a fraction of a target pass. The default is the draft\'s weight bytes over the target\'s (a 1 GB fp8 draft), since both passes are bound by reading weights. Editable.">Draft cost <span class="ls-sym">c</span><output data-o="c"></output></label><input id="' + id + 'c" type="range" min="0.02" max="0.3" step="0.01" data-k="c"></div>' +
      '<div class="ls-grp ls-end"><button type="button" class="ls-btn" data-act="run" data-tip="Restarts both panes on one clock with a fresh random draw of accepted and rejected draft tokens."></button></div>' +
      '</div>' +
      '<div class="ls-race">' +
      pane('base', 'Baseline', '1 token per forward pass', 'Plain decoding: one forward pass of the target model per token, each pass reading all the weights.', 'Tokens per second = bandwidth × 0.75 ÷ target weight bytes: the same memory-bound, batch-1 model as the capacity planner.') +
      pane('spec', 'Speculative', 'draft k tokens, verify in one pass', 'Draft-then-verify: the draft proposes k tokens, then one target pass checks them all and adds a token of its own. The output is identical to plain decoding.', 'Tokens per second from the same clock: accepted draft tokens plus one per verify pass, divided by the time spent in draft and target passes.') +
      '</div>' +
      '<div class="ls-bot"><div class="ls-met">' +
      '<div class="ls-m" data-tip="Baseline time per token divided by speculative time per token, from the run so far. It converges on the expected value as the text goes on."><small>Measured speed-up</small><b data-m="up">—</b></div>' +
      '<div class="ls-m" data-tip="Tokens produced per verify pass in this run: accepted draft tokens plus the target\'s own token."><small>Tokens per verify pass</small><b data-m="tpp">—</b></div>' +
      '<div class="ls-m" data-tip="Share of all proposed draft tokens that were accepted in this run."><small>Draft tokens accepted</small><b data-m="acc">—</b></div>' +
      '<div class="ls-m" data-tip="Closed form: (1 − α^(k+1)) ÷ (1 − α) expected tokens per step, divided by the step cost 1 + k·c."><small>Expected speed-up</small><b data-m="exp">—</b></div>' +
      '<div class="ls-m" data-tip="The draft length from 1 to 8 that maximises the expected speed-up at the current α and c."><small>Best k at this α and c</small><b data-m="best">—</b></div>' +
      '<div class="ls-m" data-tip="Baseline tokens per second × expected speed-up, for one stream on the selected GPU."><small>Expected tok/s, one stream</small><b data-m="etps">—</b></div>' +
      '</div><div class="ls-chart"><small data-tip="The expected speed-up formula evaluated for k = 1 to 8 at the current α and c; the dashed line is 1×, the marked point the chosen k.">Expected speed-up against draft length k</small><svg viewBox="0 0 300 104" role="img" aria-label="Expected speed-up for draft lengths 1 to 8"></svg></div></div>' +
      '<p class="ls-note" data-note></p>' +
      '<details class="ls-det"><summary>What the simulation models</summary><ul>' +
      '<li>The baseline runs one target-model forward pass per token. One stream reads every weight once per token, so its rate is <code>peak bandwidth × ' + BW_EFF + ' ÷ weight bytes</code>: the same first-order, memory-bound model as the capacity planner, batch 1, no attention or communication cost. Peak bandwidth comes from the GPU\'s datasheet.</li>' +
      '<li>Each speculative step runs the draft model k times, at <code>c</code> of a target pass each, then one target pass that checks all k drafts at once: <code>k·c + 1</code> target-pass units. The default <code>c</code> is the draft\'s weight bytes over the target\'s (a 1B-class fp8 draft, ' + gbs(DRAFT_BYTES) + '), since both passes are bound by reading weights.</li>' +
      '<li>Each draft token is accepted with probability α, independently, until the first rejection. The verify pass always yields one token of its own: the correction for the rejected draft, or a bonus token when all k are accepted. The output is exactly what the target model would have written alone.</li>' +
      '<li>Expected speed-up: <code>(1 − α^(k+1)) / (1 − α) ÷ (1 + k·c)</code>. Longer drafts pay off only while α is high; drafts trained on your own traffic (EAGLE-style heads) usually accept more than a generic small model.</li>' +
      '<li>Playback is slowed so each step can be followed; the counters are scaled to the derived baseline. It ignores batching: at large batch sizes the verify pass stops being nearly free and the gain shrinks. Figures come from this model, not from measurements of any product.</li>' +
      '</ul></details></div>';

    function pane(kind, title, sub, tipT, tipR) {
      return '<div class="ls-pane ls-' + kind + '" data-p="' + kind + '"><div class="ls-ph"><b data-tip="' + tipT + '">' + title + '</b><span>' + sub + '</span></div>' +
        '<div class="ls-tps" data-tip="' + tipR + '"><span><span data-v="tps">0</span><em>tok/s</em></span><small data-v="sub"></small></div><div class="ls-prog"><i></i></div>' +
        '<div class="ls-txt" aria-hidden="true"></div>' +
        '<div class="ls-pf"><span data-tip="Tokens of the answer produced so far, out of the total.">Tokens <b data-v="n">0</b></span><span data-tip="Forward passes of the target model so far. The baseline needs one per token; speculative decoding needs one per verify step.">Target passes <b data-v="fp">0</b></span><span data-tip="Elapsed time in model time, at the derived baseline rate (playback on screen is slowed).">Time <b data-v="t">0.00 s</b></span></div></div>';
    }

    var el = root.querySelector('.ls'), runBtn = el.querySelector('[data-act="run"]'), noteEl = el.querySelector('[data-note]');
    if (lum(getComputedStyle(el).backgroundColor) < 0.5) el.classList.add('ls-dark');
    var inputs = {}, outs = {};
    ['a', 'k', 'c'].forEach(function (k) { inputs[k] = el.querySelector('[data-k="' + k + '"]'); outs[k] = el.querySelector('[data-o="' + k + '"]'); });
    var M = {}; [].forEach.call(el.querySelectorAll('[data-m]'), function (b) { M[b.getAttribute('data-m')] = b; });
    var P = {};
    ['base', 'spec'].forEach(function (k) {
      var p = el.querySelector('[data-p="' + k + '"]');
      P[k] = { txt: p.querySelector('.ls-txt'), tps: p.querySelector('[data-v="tps"]'), sub: p.querySelector('[data-v="sub"]'), n: p.querySelector('[data-v="n"]'), fp: p.querySelector('[data-v="fp"]'), t: p.querySelector('[data-v="t"]'), prog: p.querySelector('.ls-prog i') };
    });
    var svg = el.querySelector('.ls-chart svg');
    var modelSel = el.querySelector('[data-sel="model"]'), gpuSel = el.querySelector('[data-sel="gpu"]');

    function model() { for (var i = 0; i < MODELS.length; i++) if (MODELS[i].id === st.model) return MODELS[i]; return MODELS[0]; }
    function gpu() { return HW ? HW.gpus[st.gpu] : null; }
    /* the physics: baseline tokens/s and the draft cost from the catalogue */
    function derive() {
      var m = model(), g = gpu();
      if (!g) { BASE_TPS = 60; fits = true; SLOW = Math.round(UNIT_MS / (1000 / BASE_TPS)); return; }
      fits = m.bytes <= g.mem * 1e9;
      BASE_TPS = g.bw * 1e12 * BW_EFF / m.bytes;
      SLOW = Math.max(1, Math.round(UNIT_MS / (1000 / BASE_TPS)));
      P.base.sub.textContent = fits ? fmt(g.bw, 2) + ' TB/s × ' + BW_EFF + ' ÷ ' + gbs(m.bytes) : 'weights do not fit';
      P.spec.sub.textContent = fits ? 'draft ' + gbs(DRAFT_BYTES) + ' · c = ' + st.c.toFixed(2) : '';
      noteEl.className = 'ls-note' + (fits ? '' : ' ls-warn');
      noteEl.textContent = fits
        ? m.name + ' in fp8 on ' + g.name + ': ' + Math.round(BASE_TPS) + ' tok/s baseline, memory-bound at batch 1. Same text, same target model, one clock; playback is slowed ' + SLOW + '× so each step can be followed.'
        : m.name + ' in fp8 is ' + gbs(m.bytes) + '; ' + g.name + ' has ' + g.mem + ' GB. The weights do not fit on one GPU, so there is no single-GPU baseline to race.';
      runBtn.disabled = !fits;
    }
    function defaultC() { return Math.min(0.3, Math.max(0.02, DRAFT_BYTES / model().bytes)); }

    function syncInputs() {
      inputs.a.value = st.a; inputs.k.value = st.k; inputs.c.value = st.c;
      outs.a.textContent = (+st.a).toFixed(2); outs.k.textContent = st.k; outs.c.textContent = (+st.c).toFixed(2);
      if (modelSel) modelSel.value = st.model; if (gpuSel) gpuSel.value = st.gpu;
      [].forEach.call(el.querySelectorAll('.ls-seg button'), function (b) { b.setAttribute('aria-pressed', Math.abs(+b.getAttribute('data-a') - st.a) < 0.005 ? 'true' : 'false'); });
      derive(); chart();
      var ex = expected(st.a, st.k, st.c);
      M.exp.innerHTML = ex.toFixed(2) + '<em>×</em>'; M.best.textContent = bestK(st.a, st.c);
      M.etps.innerHTML = fits ? fmt(BASE_TPS * ex) + '<em>vs ' + fmt(BASE_TPS) + '</em>' : '—';
    }
    function chart() {
      var W = 300, H = 104, L = 30, R = 10, T = 10, B = 18, vals = [], k, mx = 1;
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
        p.tps.textContent = fmt(tps);
        p.n.textContent = S.n + ' / ' + N; p.fp.textContent = S.fp; p.t.textContent = (tEnd / BASE_TPS).toFixed(2) + ' s';
        p.prog.style.width = (S.n / N * 100).toFixed(1) + '%';
      });
      var b = race.base, s = race.spec;
      var bt = b.n ? Math.min(now, b.end) / b.n : 0, stt = s.n ? Math.min(now, s.end) / s.n : 0;
      if (s.n > 8 && bt && stt) { var up = bt / stt; M.up.innerHTML = up.toFixed(2) + '<em>×</em>'; M.up.className = up > 1.05 ? 'ls-up' : ''; } else { M.up.innerHTML = '—'; M.up.className = ''; }
      M.tpp.textContent = s.steps ? (s.n / s.steps).toFixed(2) : '—';
      M.acc.innerHTML = s.dr ? Math.round(s.acc / s.dr * 100) + '<em>%</em>' : '—';
    }
    function reset() {
      race = build(); doneAt = null;
      P.base.txt.textContent = ''; P.spec.txt.textContent = ''; caret(P.base); caret(P.spec);
      counters();
    }
    function start() {
      if (!fits) { reset(); setPlaying(false); return; }
      reset(); setPlaying(true);
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
    function hwChanged() { syncInputs(); if (fits && (!reduce || playing)) start(); else { reset(); setPlaying(false); } }
    if (modelSel) modelSel.addEventListener('change', function () { st.model = modelSel.value; st.c = defaultC(); hwChanged(); });
    if (gpuSel) gpuSel.addEventListener('change', function () { st.gpu = gpuSel.value; hwChanged(); });
    if (LAB) LAB.subscribe(function (m) { if (m.kind === 'gpu' && m.gpu !== st.gpu) { st.gpu = m.gpu; hwChanged(); } });

    st.c = defaultC();
    syncInputs();
    race = build(); counters(); caret(P.base); caret(P.spec);
    setPlaying(false);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) {
        visible = es[0].isIntersecting; last = 0;
        if (visible && !reduce && race.ei === 0 && !playing && fits) start();
      }, { threshold: 0.2 }).observe(el);
    } else if (!reduce) start();
    document.addEventListener('visibilitychange', function () { last = 0; });
    requestAnimationFrame(tick);
  }

  function init() { injectCss(); [].forEach.call(document.querySelectorAll('[data-lab="specdec"]'), mount); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
