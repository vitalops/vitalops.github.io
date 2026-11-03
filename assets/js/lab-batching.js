/* Batching simulator: a discrete-event model of one LLM server, run live in the browser.
   Renders into every [data-lab="batching"]. No libraries, no network. */
(function () {
  'use strict';

  /* ───────────── model ───────────── */
  var SLOTS = 16;            // max concurrent sequences (batch slots)
  var KV_BUDGET = 48000;     // KV-cache capacity in tokens
  var STEP_BASE = 10;        // ms per engine step: weights read, launch overheads
  var STEP_KV = 0.00035;     // ms per KV-cache token read during decode attention
  var STEP_PF = 0.03;        // ms per prompt token prefilled
  var CHUNK = 512;           // prefill tokens per step with chunked prefill
  var STATIC_WAIT = 2000;    // ms a static batcher waits to fill a batch

  var PRESETS = {
    chat:   { label: 'Chat',   rate: 2.4, rmax: 6,  shared: 0,    uniq: [700, 0.6, 120, 3000],  out: [220, 0.5, 24, 600],
              hint: 'Short prompts, medium answers.' },
    rag:    { label: 'RAG',    rate: 1.1, rmax: 3,  shared: 1200, uniq: [4200, 0.3, 2000, 7000], out: [160, 0.4, 30, 400],
              hint: 'Long prompts from retrieved documents, a shared 1.2k-token system prompt.' },
    agents: { label: 'Agents', rate: 4,   rmax: 10, shared: 6000, uniq: [400, 0.5, 80, 1500],   out: [70, 0.5, 12, 200],
              hint: 'A 6k-token shared prefix of instructions and tools, short outputs.' }
  };
  var MODES = {
    static:     { label: 'Static',            note: 'Requests wait for a full batch, and finished slots sit idle until the longest answer in the batch ends.' },
    continuous: { label: 'Continuous',        note: 'Requests join and leave at every step, so slots stay full. A long prompt still stalls every running stream while it prefills.' },
    chunked:    { label: 'Chunked prefill',   note: 'Continuous batching with prefill split into 512-token chunks between decode steps, so long prompts no longer stall the streams.' }
  };

  function mulberry(seed) {
    return function () {
      seed = (seed + 0x6D2B79F5) | 0;
      var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function lognorm(r, p) {
    var u = r() || 1e-9, v = r();
    var z = Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
    return Math.round(Math.max(p[2], Math.min(p[3], p[0] * Math.exp(p[1] * z))));
  }

  function Engine(preset, mode, prefix, rate, seed) {
    this.p = PRESETS[preset]; this.mode = mode; this.prefix = !!prefix && this.p.shared > 0; this.rate = rate;
    this.r = mulberry(seed || 7);
    this.t = 0; this.nextArr = this.gap(); this.id = 0;
    this.queue = []; this.running = []; this.slots = []; for (var i = 0; i < SLOTS; i++) this.slots.push(null);
    this.kvUsed = 0; this.warm = false; this.batch = null;
    this.reqs = [];       // everything that holds or held a slot, for drawing
    this.steps = [];      // committed steps {t1, dt, out, n}
    this.firsts = [];     // {t, ttft}
    this.tpots = [];      // {t, v}
    this.kvPeak = 0;
  }
  Engine.prototype.gap = function () { return -Math.log(1 - this.r()) / this.rate * 1000; };
  Engine.prototype.arrive = function () {
    while (this.nextArr <= this.t) {
      var p = this.p;
      this.queue.push({ id: this.id++, arr: this.nextArr, shared: p.shared, uniq: lognorm(this.r, p.uniq), out: lognorm(this.r, p.out),
        gen: 0, slot: -1, admit: null, pfEnd: null, first: null, fin: null, rel: null, hit: false, kv: 0, pfLeft: 0 });
      this.nextArr += this.gap();
    }
  };
  Engine.prototype.sharedKv = function () { return this.prefix && this.warm ? this.p.shared : 0; };
  Engine.prototype.need = function (q) {
    var ctx = this.prefix ? q.uniq : q.shared + q.uniq;
    var extra = this.prefix && !this.warm && !this.anyShared ? q.shared : 0;
    return { kv: ctx + q.out, extra: extra };
  };
  Engine.prototype.freeSlot = function () { for (var i = 0; i < SLOTS; i++) if (!this.slots[i]) return i; return -1; };
  Engine.prototype.admitOne = function (q) {
    var n = this.need(q), s = this.freeSlot();
    if (s < 0) return false;
    var base = this.kvUsed + (this.prefix && !this.anyShared ? q.shared : 0);
    if (base + n.kv > KV_BUDGET && this.running.length) return false;
    if (this.prefix && !this.anyShared) { this.kvUsed += q.shared; this.anyShared = true; }
    this.queue.shift();
    q.slot = s; q.admit = this.t; q.kv = n.kv; this.kvUsed += n.kv;
    q.hit = this.prefix && this.warm;
    q.pfLeft = q.hit ? q.uniq : q.shared + q.uniq;
    this.slots[s] = q; this.running.push(q); this.reqs.push(q);
    if (this.kvUsed > this.kvPeak) this.kvPeak = this.kvUsed;
    return true;
  };
  Engine.prototype.plan = function () {
    var dec = [], pf = [], pfTok = 0, kvRead = this.sharedKv(), i, q;
    for (i = 0; i < this.running.length; i++) {
      q = this.running[i];
      if (q.fin !== null) continue;
      if (q.pfLeft > 0) pf.push(q);
      else { dec.push(q); kvRead += (this.prefix ? 0 : q.shared) + q.uniq + q.gen; }
    }
    var take = [];
    if (this.mode === 'chunked') {
      var budget = CHUNK;
      for (i = 0; i < pf.length && budget > 0; i++) { var k = Math.min(budget, pf[i].pfLeft); take.push([pf[i], k]); budget -= k; pfTok += k; }
    } else {
      for (i = 0; i < pf.length; i++) { take.push([pf[i], pf[i].pfLeft]); pfTok += pf[i].pfLeft; }
    }
    if (!dec.length && !take.length) return null;
    return { dec: dec, take: take, dt: STEP_BASE + STEP_KV * kvRead + STEP_PF * pfTok };
  };
  Engine.prototype.commit = function (st) {
    var t1 = this.t + st.dt, out = 0, i, q;
    for (i = 0; i < st.take.length; i++) {
      q = st.take[i][0]; q.pfLeft -= st.take[i][1];
      if (q.pfLeft <= 0) {
        q.pfEnd = t1; q.first = t1; q.gen = 1; out++;
        this.firsts.push({ t: t1, v: t1 - q.arr });
        if (this.prefix && q.shared) this.warm = true;
        if (q.gen >= q.out) this.finish(q, t1);
      }
    }
    for (i = 0; i < st.dec.length; i++) { q = st.dec[i]; q.gen++; out++; if (q.gen >= q.out) this.finish(q, t1); }
    this.steps.push({ t1: t1, dt: st.dt, out: out, n: st.dec.length, a: st.dec.length + st.take.length });
    this.t = t1;
  };
  Engine.prototype.finish = function (q, t1) {
    q.fin = t1;
    if (q.out > 1) this.tpots.push({ t: t1, v: (t1 - q.first) / (q.out - 1) });
    if (this.mode !== 'static') this.release(q, t1);
  };
  Engine.prototype.release = function (q, t1) {
    q.rel = t1; this.slots[q.slot] = null; this.kvUsed -= q.kv;
    var i = this.running.indexOf(q); if (i >= 0) this.running.splice(i, 1);
    if (!this.running.length && this.prefix && !this.warm) { this.kvUsed -= this.p.shared; this.anyShared = false; }
  };
  Engine.prototype.advance = function (to) {
    var guard = 0;
    while (guard++ < 5000) {
      this.arrive();
      if (this.mode === 'static') {
        if (!this.batch) {
          var ready = this.queue.length >= SLOTS || (this.queue.length && this.t - this.queue[0].arr >= STATIC_WAIT - 1e-6);
          if (ready) {
            this.batch = [];
            while (this.queue.length && this.batch.length < SLOTS) { var q0 = this.queue[0]; if (!this.admitOne(q0)) break; this.batch.push(q0); }
          } else {
            var nx = Math.min(this.nextArr, this.queue.length ? this.queue[0].arr + STATIC_WAIT : Infinity);
            if (nx > to) { this.t = Math.max(this.t, to); return; }
            this.t = nx; continue;
          }
        }
      } else {
        while (this.queue.length && this.admitOne(this.queue[0])) {}
      }
      var st = this.plan();
      if (!st) {
        if (this.mode === 'static' && this.batch) {
          for (var b = 0; b < this.batch.length; b++) this.release(this.batch[b], this.t);
          this.batch = null; continue;
        }
        if (this.nextArr > to) { this.t = Math.max(this.t, to); return; }
        this.t = this.nextArr; continue;
      }
      if (this.t + st.dt > to) return;   // the step is in flight; commit it when the clock reaches its end
      this.commit(st);
    }
  };
  Engine.prototype.prune = function (before) {
    this.reqs = this.reqs.filter(function (q) { return q.rel === null || q.rel > before; });
    var cut = function (a, t) { var i = 0; while (i < a.length && a[i].t < t) i++; if (i) a.splice(0, i); };
    var i = 0; while (i < this.steps.length && this.steps[i].t1 < before) i++; if (i) this.steps.splice(0, i);
    cut(this.firsts, before); cut(this.tpots, before);
  };

  function pct(arr, p) {
    if (!arr.length) return null;
    var a = arr.slice().sort(function (x, y) { return x - y; });
    return a[Math.min(a.length - 1, Math.floor(p * a.length))];
  }
  Engine.prototype.metrics = function (now) {
    var W = 5000, from = now - W, out = 0, busy = 0, i, s, itl = [], tot = 0;
    for (i = 0; i < this.steps.length; i++) {
      s = this.steps[i];
      if (s.t1 > now) continue;
      if (s.t1 >= from) { out += s.out; busy += s.dt * s.a; }
      if (s.t1 >= now - 15000 && s.n) { itl.push([s.dt, s.n]); tot += s.n; }
    }
    var span = Math.min(W, Math.max(1, now));
    itl.sort(function (a, b) { return a[0] - b[0]; });
    var itl99 = null, acc = 0;
    for (i = 0; i < itl.length; i++) { acc += itl[i][1]; if (acc >= 0.99 * tot) { itl99 = itl[i][0]; break; } }
    var ft = [], tp = [];
    for (i = 0; i < this.firsts.length; i++) if (this.firsts[i].t >= now - 20000 && this.firsts[i].t <= now) ft.push(this.firsts[i].v);
    for (i = 0; i < this.tpots.length; i++) if (this.tpots[i].t >= now - 20000 && this.tpots[i].t <= now) tp.push(this.tpots[i].v);
    // a request still waiting counts toward TTFT with its wait so far, so a stalled queue shows up straight away
    for (i = 0; i < this.queue.length; i++) if (now - this.queue[i].arr > 0) ft.push(now - this.queue[i].arr);
    for (i = 0; i < this.running.length; i++) if (this.running[i].first === null) ft.push(now - this.running[i].arr);
    return {
      tps: out / span * 1000, busy: Math.min(1, busy / span / SLOTS),
      ttft50: pct(ft, 0.5), ttft99: pct(ft, 0.99), tpot: pct(tp, 0.5), itl99: itl99,
      queue: this.queue.length, kv: this.kvUsed / KV_BUDGET
    };
  };

  if (typeof module !== 'undefined' && module.exports) { module.exports = { Engine: Engine, PRESETS: PRESETS }; }
  if (typeof document === 'undefined') return;

  /* ───────────── styles ───────────── */
  var CSS = [
    '.lb{background:var(--white,#fff);border:1px solid var(--line,#e2e8f0);border-radius:12px;box-shadow:0 1px 2px rgba(16,24,40,.05);font-family:var(--font,system-ui,sans-serif);color:var(--ink2,#334155);font-size:13px;line-height:1.45;overflow:hidden;min-width:0}',
    '.lb *{box-sizing:border-box}',
    '.lb-bar{display:flex;flex-wrap:wrap;align-items:flex-end;gap:12px 18px;padding:14px 16px 12px;border-bottom:1px solid var(--line2,#eef2f7)}',
    '.lb-grp{display:flex;flex-direction:column;gap:5px;min-width:0}',
    '.lb-lab{font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--ink3,#5b687c)}',
    '.lb-lab output{font-family:var(--mono,monospace);font-variant-numeric:tabular-nums;text-transform:none;letter-spacing:0;color:var(--ink,#0f172a);font-weight:500;margin-left:6px}',
    '.lb-seg{display:inline-flex;border:1px solid var(--line,#e2e8f0);border-radius:8px;padding:2px;background:var(--bg,#f5f6fa);flex-wrap:wrap}',
    '.lb-seg button,.lb-btn{font:inherit;font-size:12.5px;font-weight:500;color:var(--ink2,#334155);background:transparent;border:0;border-radius:6px;padding:5px 10px;cursor:pointer;white-space:nowrap;line-height:1.3}',
    '.lb-seg button:hover{color:var(--ink,#0f172a)}',
    '.lb-seg button[aria-pressed="true"]{background:var(--white,#fff);color:var(--brand,#3f5cf6);box-shadow:0 0 0 1px var(--brand200,#bdcdff),0 1px 2px rgba(16,24,40,.06)}',
    '.lb-btn{border:1px solid var(--line,#e2e8f0);background:var(--white,#fff);display:inline-flex;align-items:center;gap:6px;padding:6px 11px}',
    '.lb-btn:hover{border-color:var(--brand200,#bdcdff)}',
    '.lb-btn.lb-pri{background:var(--brand,#3f5cf6);border-color:var(--brand,#3f5cf6);color:#fff}',
    '.lb-btn.lb-pri:hover{background:var(--brandD,#2737bd)}',
    '.lb-btn svg{width:12px;height:12px;fill:currentColor}',
    '.lb button:focus-visible,.lb input:focus-visible,.lb summary:focus-visible{outline:2px solid var(--brand,#3f5cf6);outline-offset:2px}',
    '.lb-sw{display:inline-flex;align-items:center;gap:8px;cursor:pointer;padding:5px 0;font-weight:500;color:var(--ink,#0f172a);font-size:12.5px;user-select:none}',
    '.lb-sw input{position:absolute;opacity:0;width:1px;height:1px}',
    '.lb-sw i{width:30px;height:18px;border-radius:9px;background:var(--line,#e2e8f0);position:relative;transition:background .15s;flex:none}',
    '.lb-sw i::after{content:"";position:absolute;left:2px;top:2px;width:14px;height:14px;border-radius:50%;background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.2);transition:transform .15s}',
    '.lb-sw input:checked+i{background:var(--brand,#3f5cf6)}.lb-sw input:checked+i::after{transform:translateX(12px)}',
    '.lb-sw input:focus-visible+i{outline:2px solid var(--brand,#3f5cf6);outline-offset:2px}',
    '.lb-sw input:disabled+i{background:var(--line2,#eef2f7)}.lb-sw input:disabled+i::after{transform:none;box-shadow:0 0 0 1px var(--line,#e2e8f0)}.lb-sw.lb-dis{color:var(--ink4,#94a3b8);cursor:not-allowed}',
    '.lb-rate input[type=range]{width:150px;accent-color:var(--brand,#3f5cf6);margin:3px 0}',
    '.lb-ctl{display:flex;gap:6px;align-items:center;margin-left:auto;flex-wrap:wrap}',
    '.lb-note{margin:0;padding:10px 16px 0;color:var(--ink3,#5b687c);font-size:12.5px;min-height:2.9em}',
    '.lb-note b{color:var(--ink,#0f172a);font-weight:600}',
    '.lb-viz{position:relative;padding:6px 16px 0}',
    '.lb-viz canvas{display:block;width:100%;height:270px}',
    '.lb-leg{display:flex;flex-wrap:wrap;gap:6px 16px;padding:8px 16px 12px;font-size:11.5px;color:var(--ink3,#5b687c)}',
    '.lb-leg span{display:inline-flex;align-items:center;gap:6px}',
    '.lb-leg i{display:inline-block;width:16px;height:8px;border-radius:2px}',
    '.lb-met{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));border-top:1px solid var(--line2,#eef2f7);background:var(--bg,#f5f6fa)}',
    '.lb-m{padding:10px 14px;border-right:1px solid var(--line2,#eef2f7);border-bottom:1px solid var(--line2,#eef2f7);min-width:0}',
    '.lb-m small{display:block;font-size:11px;color:var(--ink3,#5b687c);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.lb-m b{display:block;font-family:var(--mono,monospace);font-variant-numeric:tabular-nums;font-size:17px;font-weight:500;color:var(--ink,#0f172a);margin-top:2px;white-space:nowrap}',
    '.lb-m b em{font-style:normal;font-size:11.5px;color:var(--ink3,#5b687c);margin-left:3px}',
    '.lb-m b.lb-bad{color:var(--bad,#be123c)}.lb-m b.lb-warn{color:var(--warn,#b45309)}',
    '.lb-kv{height:6px;border-radius:3px;background:var(--line,#e2e8f0);margin-top:7px;overflow:hidden}',
    '.lb-kv i{display:block;height:100%;width:0;background:var(--brand,#3f5cf6);transition:width .25s}',
    '.lb-m svg{display:block;width:100%;height:16px;margin-top:4px;overflow:visible}',
    '.lb-det{border-top:1px solid var(--line2,#eef2f7);padding:10px 16px;font-size:12.5px}',
    '.lb-det summary{cursor:pointer;font-weight:600;color:var(--ink,#0f172a);list-style-position:inside}',
    '.lb-det ul{margin:8px 0 2px 18px;padding:0;color:var(--ink3,#5b687c)}.lb-det li{margin:3px 0}',
    '.lb-det code{font-family:var(--mono,monospace);font-size:12px;color:var(--ink,#0f172a)}',
    '@media(max-width:560px){.lb-bar{padding:12px}.lb-ctl{margin-left:0}.lb-viz{padding:6px 10px 0}.lb-viz canvas{height:220px}.lb-note,.lb-leg,.lb-det{padding-left:12px;padding-right:12px}.lb-rate input[type=range]{width:130px}}'
  ].join('\n');
  function injectCss() {
    if (document.getElementById('lab-batching-css')) return;
    var s = document.createElement('style'); s.id = 'lab-batching-css'; s.textContent = CSS; document.head.appendChild(s);
  }

  var ICON_PLAY = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M3 1.5v9l7.5-4.5z"/></svg>';
  var ICON_PAUSE = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 1.5h2.6v9H2.5zM6.9 1.5h2.6v9H6.9z"/></svg>';
  var ICON_RESET = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M6 1.5a4.5 4.5 0 1 0 4.4 5.4l-1.5-.3A3 3 0 1 1 6 3v1.6l2.6-2.3L6 0z"/></svg>';

  function fmtMs(v) {
    if (v === null || v === undefined || !isFinite(v)) return '—';
    if (v >= 10000) return (v / 1000).toFixed(0) + '<em>s</em>';
    if (v >= 1000) return (v / 1000).toFixed(1) + '<em>s</em>';
    return Math.round(v) + '<em>ms</em>';
  }

  /* ───────────── widget ───────────── */
  var uid = 0;
  function mount(root) {
    if (root.__lb) return; root.__lb = true;
    var id = 'lb' + (++uid);
    var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    var st = { preset: 'chat', mode: 'continuous', prefix: true, rate: PRESETS.chat.rate, speed: 1, playing: !reduce, seed: 11 };

    function seg(name, label, opts, cur) {
      return '<div class="lb-grp"><span class="lb-lab" id="' + id + name + '">' + label + '</span><div class="lb-seg" role="group" aria-labelledby="' + id + name + '" data-k="' + name + '">' +
        opts.map(function (o) { return '<button type="button" data-v="' + o[0] + '" aria-pressed="' + (o[0] === cur) + '">' + o[1] + '</button>'; }).join('') + '</div></div>';
    }
    root.innerHTML =
      '<div class="lb">' +
      '<div class="lb-bar">' +
      seg('preset', 'Traffic', Object.keys(PRESETS).map(function (k) { return [k, PRESETS[k].label]; }), st.preset) +
      seg('mode', 'Scheduler', Object.keys(MODES).map(function (k) { return [k, MODES[k].label]; }), st.mode) +
      '<div class="lb-grp"><span class="lb-lab">Cache</span><label class="lb-sw"><input type="checkbox" data-k="prefix" checked><i></i><span>Prefix caching</span></label></div>' +
      '<div class="lb-grp lb-rate"><label class="lb-lab" for="' + id + 'r">Arrivals<output>3.0 req/s</output></label><input id="' + id + 'r" type="range" min="0.5" max="6" step="0.1" value="3" data-k="rate"></div>' +
      '<div class="lb-ctl"><button type="button" class="lb-btn lb-pri" data-a="play"></button><button type="button" class="lb-btn" data-a="reset">' + ICON_RESET + 'Reset</button>' +
      '<div class="lb-seg" role="group" aria-label="Playback speed" data-k="speed"><button type="button" data-v="1" aria-pressed="true">1×</button><button type="button" data-v="4" aria-pressed="false">4×</button></div></div>' +
      '</div>' +
      '<p class="lb-note" aria-live="polite"></p>' +
      '<div class="lb-viz"><canvas role="img" aria-label="GPU batch slots over time: each bar is a request, darker while its prompt is prefilled, lighter while it generates."></canvas></div>' +
      '<div class="lb-leg"><span><i style="background:var(--brandD,#2737bd)"></i>Prefill</span><span><i style="background:var(--brand2,#637fff);opacity:.6"></i>Decode</span>' +
      '<span><i style="background:#0d9488"></i>Prefix cache hit</span><span><i style="background:transparent;border-top:2px dashed var(--ink4,#94a3b8);height:0;border-radius:0"></i>Slot held, idle</span>' +
      '<span><i style="background:rgba(217,119,6,.18);border-left:2px solid rgba(217,119,6,.6)"></i>Long step: every stream stalls</span><span><i style="background:#d97706;width:8px"></i>Waiting &gt; 2 s</span></div>' +
      '<div class="lb-met">' +
      '<div class="lb-m"><small>Output throughput</small><b data-m="tps">—</b></div>' +
      '<div class="lb-m"><small>TTFT p50</small><b data-m="ttft50">—</b></div>' +
      '<div class="lb-m" title="TTFT p99 over the last 40 s"><small>TTFT p99</small><b data-m="ttft99">—</b><svg viewBox="0 0 200 16" preserveAspectRatio="none" aria-hidden="true"><polyline fill="none" stroke="var(--brand,#3f5cf6)" stroke-width="1.5" vector-effect="non-scaling-stroke" points=""/></svg></div>' +
      '<div class="lb-m"><small>TPOT p50</small><b data-m="tpot">—</b></div>' +
      '<div class="lb-m"><small>Inter-token p99</small><b data-m="itl99">—</b></div>' +
      '<div class="lb-m"><small>Slots in use</small><b data-m="busy">—</b></div>' +
      '<div class="lb-m"><small>Queue</small><b data-m="queue">0</b></div>' +
      '<div class="lb-m"><small>KV cache</small><b data-m="kv">0<em>%</em></b><div class="lb-kv"><i></i></div></div>' +
      '</div>' +
      '<details class="lb-det"><summary>What the simulation models</summary><ul>' +
      '<li>One GPU with ' + SLOTS + ' batch slots and a KV cache of ' + (KV_BUDGET / 1000) + 'k tokens. A request is admitted only if its prompt and full output fit in the cache.</li>' +
      '<li>Each engine step costs <code>' + STEP_BASE + ' ms + ' + STEP_KV + ' ms × KV tokens read + ' + STEP_PF + ' ms × prompt tokens prefilled</code>: decode is bound by memory reads, prefill by compute. The constants are illustrative, in the range of a 7–8B model on one data-centre GPU.</li>' +
      '<li>Arrivals are Poisson. Prompt and output lengths are log-normal, drawn from a fixed seed, so every scheduler sees the same requests.</li>' +
      '<li>Static batching waits for ' + SLOTS + ' requests or ' + (STATIC_WAIT / 1000) + ' s, then runs the batch until its longest answer ends. Continuous batching admits and retires requests every step. Chunked prefill caps prompt work at ' + CHUNK + ' tokens per step.</li>' +
      '<li>Prefix caching keeps the shared prefix (RAG system prompt, agent instructions and tools) in the cache after the first request, so later requests skip prefilling it and share its KV entries.</li>' +
      '<li>TTFT counts requests still waiting with their wait so far. Inter-token p99 is the 99th percentile gap between tokens of a stream. Figures are from this model, not measurements of any product.</li>' +
      '</ul></details></div>';

    var el = root.querySelector('.lb'), canvas = el.querySelector('canvas'), ctx = canvas.getContext('2d');
    var note = el.querySelector('.lb-note'), playBtn = el.querySelector('[data-a="play"]');
    var rateIn = el.querySelector('[data-k="rate"]'), rateOut = el.querySelector('.lb-rate output');
    var prefIn = el.querySelector('[data-k="prefix"]'), prefLab = prefIn.closest('.lb-sw');
    var M = {}; [].forEach.call(el.querySelectorAll('[data-m]'), function (b) { M[b.getAttribute('data-m')] = b; });
    var kvBar = el.querySelector('.lb-kv i'), spark = el.querySelector('.lb-m polyline');
    var eng, clock, hist, lastHist, lastMet;

    function css(n, f) { var v = getComputedStyle(el).getPropertyValue(n).trim(); return v || f; }
    var C = {};
    function readColours() {
      C.brand = css('--brand', '#3f5cf6'); C.brand2 = css('--brand2', '#637fff'); C.brandD = css('--brandD', '#2737bd');
      C.brand200 = css('--brand200', '#bdcdff'); C.ink = css('--ink', '#0f172a'); C.ink3 = css('--ink3', '#5b687c'); C.ink4 = css('--ink4', '#94a3b8');
      C.line = css('--line', '#e2e8f0'); C.line2 = css('--line2', '#eef2f7'); C.mono = css('--mono', 'ui-monospace,monospace'); C.font = css('--font', 'system-ui,sans-serif');
    }

    function reset() {
      eng = new Engine(st.preset, st.mode, st.prefix, st.rate, st.seed);
      clock = 0; hist = []; lastHist = 0; lastMet = -1e9;
      updateNote(); updateMetrics(true); draw();
    }
    function updateNote() {
      var p = PRESETS[st.preset], txt = '<b>' + MODES[st.mode].label + '.</b> ' + MODES[st.mode].note;
      if (p.shared) txt += st.prefix ? ' Prefix caching is on: the shared ' + (p.shared / 1000).toFixed(1) + 'k-token prefix is prefilled once.' : ' Prefix caching is off: every request prefills the shared ' + (p.shared / 1000).toFixed(1) + 'k-token prefix again.';
      note.innerHTML = txt;
    }
    function setPlay(v) {
      st.playing = v;
      playBtn.innerHTML = v ? ICON_PAUSE + 'Pause' : ICON_PLAY + (reduce && clock === 0 ? 'Run' : 'Play');
      playBtn.setAttribute('aria-label', v ? 'Pause simulation' : 'Run simulation');
    }
    function syncRate() {
      var p = PRESETS[st.preset];
      rateIn.max = p.rmax; rateIn.value = st.rate; rateOut.textContent = (+st.rate).toFixed(1) + ' req/s';
      prefIn.disabled = !p.shared; prefLab.classList.toggle('lb-dis', !p.shared);
      prefLab.title = p.shared ? '' : 'Chat traffic here has no shared prefix';
    }

    el.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      var g = b.parentNode.getAttribute('data-k');
      if (g) {
        [].forEach.call(b.parentNode.children, function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        var v = b.getAttribute('data-v');
        if (g === 'speed') { st.speed = +v; return; }
        st[g] = v;
        if (g === 'preset') { st.rate = PRESETS[v].rate; syncRate(); }
        reset(); return;
      }
      var a = b.getAttribute('data-a');
      if (a === 'play') setPlay(!st.playing);
      if (a === 'reset') { st.seed++; reset(); }
    });
    rateIn.addEventListener('input', function () { st.rate = +rateIn.value; rateOut.textContent = st.rate.toFixed(1) + ' req/s'; });
    rateIn.addEventListener('change', reset);
    prefIn.addEventListener('change', function () { st.prefix = prefIn.checked; reset(); });

    /* sizing */
    var W = 0, H = 0, dpr = 1, hatch = null;
    function resize() {
      var r = canvas.getBoundingClientRect(); dpr = Math.min(2, window.devicePixelRatio || 1);
      W = Math.max(200, r.width); H = Math.max(120, r.height);
      canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
      hatch = null; draw();
    }
    function hatchPat() {
      if (hatch) return hatch;
      var c = document.createElement('canvas'), s = Math.round(6 * dpr); c.width = c.height = s;
      var g = c.getContext('2d'); g.strokeStyle = 'rgba(255,255,255,.28)'; g.lineWidth = 1.2 * dpr;
      g.beginPath(); g.moveTo(0, s); g.lineTo(s, 0); g.moveTo(-s / 2, s / 2); g.lineTo(s / 2, -s / 2); g.moveTo(s / 2, s * 1.5); g.lineTo(s * 1.5, s / 2); g.stroke();
      hatch = ctx.createPattern(c, 'repeat'); return hatch;
    }
    function rr(x, y, w, h, r) {
      r = Math.min(r, w / 2, h / 2);
      ctx.beginPath(); ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r); ctx.lineTo(x + w, y + h - r);
      ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h); ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r); ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath();
    }

    function draw() {
      if (!W || !eng) return;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
      var narrow = W < 520, G = narrow ? 50 : 82, top = 18, axis = 18, R = W - 2;
      var laneH = (H - top - axis) / SLOTS, span = (narrow ? 8 : 12) * 1000, pps = (R - G - 8) / span;
      function X(t) { return R - (clock - t) * pps; }
      ctx.font = '600 10px ' + C.font; ctx.textBaseline = 'alphabetic';
      ctx.fillStyle = C.ink3; ctx.fillText('QUEUE', 0, 11);
      ctx.fillText(narrow ? 'BATCH SLOTS' : 'GPU BATCH SLOTS', G + 8, 11);
      // lanes
      for (var i = 0; i < SLOTS; i++) {
        ctx.fillStyle = i % 2 ? '#ffffff' : C.line2; ctx.globalAlpha = i % 2 ? 1 : .55;
        ctx.fillRect(G + 8, top + i * laneH, R - G - 8, laneH);
      }
      ctx.globalAlpha = 1;
      // grid + axis
      ctx.strokeStyle = C.line; ctx.lineWidth = 1; ctx.font = '10px ' + C.mono; ctx.fillStyle = C.ink4; ctx.textAlign = 'center';
      for (var s = 0; s <= span / 1000; s += 2) {
        var gx = Math.round(R - s * 1000 * pps) + .5;
        if (gx < G + 8) break;
        ctx.beginPath(); ctx.moveTo(gx, top); ctx.lineTo(gx, H - axis + 3); ctx.stroke();
        ctx.fillText(s === 0 ? 'now' : '−' + s + ' s', Math.min(R - 12, Math.max(G + 22, gx)), H - 4);
      }
      ctx.textAlign = 'left';
      // requests
      ctx.save(); ctx.beginPath(); ctx.rect(G + 8, top, R - G - 8, H - top - axis); ctx.clip();
      // long engine steps (a big prefill): every decoding stream waits for them
      for (var j = eng.steps.length - 1; j >= 0; j--) {
        var sp = eng.steps[j]; if (sp.t1 < clock - span) break;
        if (sp.dt < 60 || sp.t1 > clock) continue;
        var sx0 = X(sp.t1 - sp.dt), sx1 = X(sp.t1);
        ctx.fillStyle = 'rgba(217,119,6,.13)'; ctx.fillRect(sx0, top, Math.max(1, sx1 - sx0), H - top - axis);
        ctx.fillStyle = 'rgba(217,119,6,.55)'; ctx.fillRect(sx0, top, 1.5, H - top - axis);
      }
      var bh = Math.max(3, laneH - 3), rad = Math.min(3, bh / 2);
      for (var k = 0; k < eng.reqs.length; k++) {
        var q = eng.reqs[k];
        if (q.admit > clock) continue;
        var y = top + q.slot * laneH + (laneH - bh) / 2;
        var fin = q.fin !== null && q.fin <= clock ? q.fin : null;
        var fade = fin === null ? 1 : Math.max(.3, 1 - (clock - fin) / 5000);
        var pe = q.pfEnd !== null && q.pfEnd <= clock ? q.pfEnd : null;
        var x0 = X(q.admit), xp = X(pe === null ? clock : pe), xe = X(fin === null ? clock : fin);
        if (xe < G) { /* off-screen, but its held slot may still show */ }
        ctx.globalAlpha = fade;
        // prefill
        if (xp - x0 > .3) {
          ctx.fillStyle = C.brandD; rr(x0, y, Math.max(1, xp - x0), bh, rad); ctx.fill();
          ctx.fillStyle = hatchPat(); ctx.fill();
        }
        // decode
        if (pe !== null && xe - xp > .3) {
          ctx.fillStyle = C.brand2; ctx.globalAlpha = fade * .55; rr(xp, y, Math.max(1, xe - xp), bh, rad); ctx.fill();
          ctx.globalAlpha = fade; ctx.fillStyle = C.brand; ctx.fillRect(Math.max(xp, xe - 2), y, 2, bh);
        }
        if (q.hit) { ctx.globalAlpha = fade; ctx.fillStyle = '#0d9488'; ctx.fillRect(x0, y, 3, bh); }
        // static batch: slot held after the request finished
        if (fin !== null && (q.rel === null || q.rel > fin)) {
          var xr = X(q.rel !== null && q.rel <= clock ? q.rel : clock);
          ctx.globalAlpha = 1; ctx.strokeStyle = C.ink4; ctx.setLineDash([3, 3]); ctx.beginPath();
          ctx.moveTo(xe + 2, y + bh / 2 + .5); ctx.lineTo(xr, y + bh / 2 + .5); ctx.stroke(); ctx.setLineDash([]);
        }
      }
      ctx.restore(); ctx.globalAlpha = 1;
      // queue
      var waiting = eng.queue.filter(function (q) { return q.arr <= clock; });
      var cs = narrow ? 6 : 7, gap = 2, cols = Math.max(1, Math.floor((G - 4) / (cs + gap))), rows = Math.floor((H - top - axis - 14) / (cs + gap));
      var cap = cols * rows, shown = Math.min(waiting.length, waiting.length > cap ? cap - cols : cap);
      for (var w = 0; w < shown; w++) {
        var cx = (w % cols) * (cs + gap), cy = top + Math.floor(w / cols) * (cs + gap);
        ctx.fillStyle = clock - waiting[w].arr > 2000 ? '#d97706' : C.brand200; rr(cx, cy, cs, cs, 1.5); ctx.fill();
      }
      ctx.fillStyle = C.ink; ctx.font = '500 11px ' + C.mono;
      var qy = top + Math.ceil(Math.max(shown, 1) / cols) * (cs + gap) + 12;
      ctx.fillText(waiting.length > shown ? '+' + (waiting.length - shown) + ' more' : waiting.length ? waiting.length + ' waiting' : 'empty', 0, Math.min(qy, H - axis - 2));
      // separator
      ctx.strokeStyle = C.line; ctx.beginPath(); ctx.moveTo(G + .5, top); ctx.lineTo(G + .5, H - axis); ctx.stroke();
    }

    function updateMetrics(force) {
      var m = eng.metrics(clock);
      M.tps.innerHTML = Math.round(m.tps).toLocaleString('en-GB') + '<em>tok/s</em>';
      M.ttft50.innerHTML = fmtMs(m.ttft50); M.ttft99.innerHTML = fmtMs(m.ttft99);
      M.ttft99.className = m.ttft99 > 3000 ? 'lb-bad' : m.ttft99 > 1000 ? 'lb-warn' : '';
      M.tpot.innerHTML = fmtMs(m.tpot); M.itl99.innerHTML = fmtMs(m.itl99);
      M.itl99.className = m.itl99 > 150 ? 'lb-bad' : m.itl99 > 60 ? 'lb-warn' : '';
      M.busy.innerHTML = clock > 0 ? Math.round(m.busy * 100) + '<em>%</em>' : '—';
      M.queue.textContent = m.queue; M.queue.className = m.queue > 20 ? 'lb-bad' : m.queue > 6 ? 'lb-warn' : '';
      M.kv.innerHTML = Math.round(m.kv * 100) + '<em>%</em>'; kvBar.style.width = Math.min(100, m.kv * 100) + '%';
      if (force || clock - lastHist >= 1000) {
        if (!force && m.ttft99 !== null) hist.push(m.ttft99);
        lastHist = clock;
        if (hist.length > 40) hist.shift();
        var mx = Math.max.apply(null, hist.concat([200]));
        spark.setAttribute('points', hist.map(function (v, i) { return (i / 39 * 200).toFixed(1) + ',' + (15 - v / mx * 14).toFixed(1); }).join(' '));
      }
    }

    /* loop */
    var visible = true, last = 0, frame = 0;
    function tick(ts) {
      requestAnimationFrame(tick);
      var dt = last ? Math.min(100, ts - last) : 16; last = ts;
      if (!st.playing || !visible || document.hidden) return;
      clock += dt * st.speed; eng.advance(clock);
      if (++frame % 600 === 0) eng.prune(clock - 60000);
      if (reduce && frame % 6) return;
      draw();
      if (clock - lastMet > 250 * st.speed || clock < lastMet) { lastMet = clock; updateMetrics(false); }
    }

    readColours(); syncRate(); reset(); setPlay(st.playing);
    if ('ResizeObserver' in window) new ResizeObserver(resize).observe(canvas); else window.addEventListener('resize', resize);
    resize();
    if ('IntersectionObserver' in window) new IntersectionObserver(function (es) { visible = es[0].isIntersecting; last = 0; }, { threshold: 0.05 }).observe(el);
    document.addEventListener('visibilitychange', function () { last = 0; });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { readColours(); draw(); });
    requestAnimationFrame(tick);
  }

  function init() { injectCss(); [].forEach.call(document.querySelectorAll('[data-lab="batching"]'), mount); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
