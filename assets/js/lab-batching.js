/* Batching simulator: a discrete-event model of one LLM server, run live in the browser.
   Renders into every [data-lab="batching"]. No libraries, no network.
   The step-time constants are derived from a chosen model and GPU (window.VO_HW, assets/js/hw.js);
   nothing here is a measurement of any product. */
(function () {
  'use strict';

  /* ───────────── model ───────────── */
  var MAXB = 256;            // max concurrent sequences the scheduler will run (vLLM's max_num_seqs default)
  var STATIC_B = 32;         // batch size of the static batcher (a tuned parameter in that era; 32 is typical)
  var BUDGET = 2048;         // prompt tokens a step may prefill (vLLM's max_num_batched_tokens default with chunked prefill)
  var STATIC_WAIT = 2000;    // ms a static batcher waits to fill a batch
  var BW_EFF = 0.75;         // share of peak memory bandwidth a decode step achieves (assumption)
  var FLOPS_EFF = 0.6;       // share of peak dense tensor throughput a prefill achieves (assumption)
  var OVERHEAD = 1;          // ms per step for kernel launches and the scheduler (assumption)
  var RESERVE = 0.10;        // share of GPU memory kept for activations, CUDA context and fragmentation (assumption)
  var GiB = 1073741824;

  /* open-weight models: parameter count and the KV-cache shape (layers × KV heads × head dim). Weights and KV cache are fp8. */
  var MODELS = {
    llama8b:  { label: 'Llama 3.1 8B',  params: 8.03e9, layers: 32, kvHeads: 8, headDim: 128 },
    qwen32b:  { label: 'Qwen3 32B',     params: 32.8e9, layers: 64, kvHeads: 8, headDim: 128 },
    llama70b: { label: 'Llama 3.3 70B', params: 70.6e9, layers: 80, kvHeads: 8, headDim: 128 }
  };
  var GPU_KEYS = ['h100', 'h200', 'b200', 'a100', 'l40s', 'rtx5090', 'mi300x'];

  /* The physics of one replica on one GPU. Returns the constants the engine runs on. */
  function derive(m, g) {
    var weights = m.params;                                         // bytes, fp8
    var kvTok = 2 * m.layers * m.kvHeads * m.headDim;               // bytes per cached token, fp8 keys and values
    var bw = g.bw * 1e12 * BW_EFF;                                  // bytes per second
    var tflops = g.flops.fp8 || g.flops.bf16, fp8 = !!g.flops.fp8;
    var memB = g.mem * GiB, reserve = memB * RESERVE;
    var kvBytes = memB - weights - reserve;
    return {
      weights: weights, kvTok: kvTok, reserve: reserve, memB: memB, fp8: fp8, tflops: tflops,
      fits: kvBytes > 0,
      kvBudget: Math.max(0, Math.floor(kvBytes / kvTok)),
      base: weights / bw * 1000 + OVERHEAD,                         // ms per step before any KV or prompt work
      b: kvTok / bw * 1000,                                         // ms per KV token read in a decode step
      pf: 2 * m.params / (tflops * 1e12 * FLOPS_EFF) * 1000,        // ms per prompt token prefilled
      maxB: MAXB
    };
  }

  var PRESETS = {
    chat:   { label: 'Chat',   shared: 300,  uniq: [500, 0.6, 80, 2500],   out: [220, 0.5, 24, 600], turns: { share: 0.6, hist: [900, 0.6, 200, 4000] },
              hint: 'A 300-token system prompt on every request; 60% of requests are follow-up turns whose history (about 900 tokens) is already cached.' },
    rag:    { label: 'RAG',    shared: 1200, uniq: [4200, 0.3, 2000, 7000], out: [160, 0.4, 30, 400],
              hint: 'Long prompts from retrieved documents, a shared 1.2k-token system prompt.' },
    agents: { label: 'Agents', shared: 6000, uniq: [400, 0.5, 80, 1500],   out: [70, 0.5, 12, 200],
              hint: 'A 6k-token shared prefix of instructions and tools, short outputs.' }
  };
  var MODES = {
    static:     { label: 'Static',            note: 'Requests wait for a batch of 32 or 2 s, and finished slots sit idle until the longest answer in the batch ends.' },
    continuous: { label: 'Continuous',        note: 'Requests join and leave at every step, so slots stay full. A long prompt is prefilled whole, and every running stream waits for it.' },
    chunked:    { label: 'Chunked prefill',   note: 'Continuous batching with long prompts split into chunks that share a 2,048-token budget with the decode streams, so no single step runs long.' }
  };
  function lnMean(p) { return Math.min(p[3], Math.max(p[2], p[0] * Math.exp(p[1] * p[1] / 2))); }

  /* Steady-state capacity of the step model for a preset: the arrival rate at which step time diverges, and
     the rate that fills 70% of it (or 80% of the KV cache or batch limit, whichever binds first). */
  function histMean(p) { return p.turns ? p.turns.share * lnMean(p.turns.hist) : 0; }
  function capacity(ph, preset, prefix) {
    var p = PRESETS[preset], cached = prefix && p.shared > 0, H = histMean(p);
    var P = lnMean(p.uniq) + (cached ? 0 : p.shared + H);   // prompt tokens prefilled per request
    var O = lnMean(p.out);                                   // output tokens per request
    var C = lnMean(p.uniq) + H + (cached ? 0 : p.shared) + O / 2;   // KV tokens read per decode step, per stream
    var k = (ph.b * O * C + ph.pf * P) / 1000;           // seconds of step time each request adds per second of arrivals
    var lmax = 1 / k;
    // with prefill capped at BUDGET tokens per step, prompt throughput is BUDGET / step; find the rate where that binds
    var kd = ph.b * O * C / 1000, lc = lmax / 2, it;
    for (it = 0; it < 40; it++) { var dtc = ph.base / Math.max(1e-6, 1 - lc * kd) + ph.pf * BUDGET; lc = 0.5 * lc + 0.5 * Math.min(lmax, BUDGET / (P * dtc / 1000)); }
    lmax = Math.min(lmax, lc);
    var ncap = Math.min(ph.maxB, ph.kvBudget / (lnMean(p.uniq) + H + (cached ? 0 : p.shared) + O));
    var rate = 0.7 * lmax;
    var dt = ph.base / (1 - rate * k), n = rate * O * dt / 1000;
    if (n > 0.8 * ncap) rate = 0.8 * ncap / (O * ph.base / 1000 + 0.8 * ncap * k);
    return { lmax: lmax, rate: rate, ncap: Math.floor(ncap) };
  }

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

  function Engine(preset, mode, prefix, rate, seed, ph) {
    this.p = PRESETS[preset]; this.mode = mode; this.prefix = !!prefix && this.p.shared > 0; this.rate = rate; this.ph = ph;
    this.r = mulberry(seed || 7);
    this.t = 0; this.nextArr = this.gap(); this.id = 0;
    this.queue = []; this.running = []; this.slots = []; for (var i = 0; i < ph.maxB; i++) this.slots.push(null);
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
      var hist = p.turns && this.r() < p.turns.share ? lognorm(this.r, p.turns.hist) : 0;   // a follow-up turn carries its conversation so far
      this.queue.push({ id: this.id++, arr: this.nextArr, shared: p.shared, hist: hist, uniq: lognorm(this.r, p.uniq), out: lognorm(this.r, p.out),
        gen: 0, slot: -1, admit: null, pfEnd: null, first: null, fin: null, rel: null, hit: false, owner: false, kv: 0, pfLeft: 0 });
      this.nextArr += this.gap();
    }
  };
  Engine.prototype.sharedKv = function () { return this.prefix && this.warm ? this.p.shared : 0; };
  Engine.prototype.need = function (q) {
    var ctx = (this.prefix ? 0 : q.shared) + q.hist + q.uniq;   // the history is resident either way; with caching it was kept from the last turn
    var extra = this.prefix && !this.warm && !this.anyShared ? q.shared : 0;
    return { kv: ctx + q.out, extra: extra };
  };
  Engine.prototype.freeSlot = function () { for (var i = 0; i < this.ph.maxB; i++) if (!this.slots[i]) return i; return -1; };
  Engine.prototype.admitOne = function (q) {
    var n = this.need(q), s = this.freeSlot();
    if (s < 0) return false;
    var owner = this.prefix && !this.anyShared;   // the first request computes the shared prefix; later ones share its blocks
    var base = this.kvUsed + (owner ? q.shared : 0);
    if (base + n.kv > this.ph.kvBudget && this.running.length) return false;
    if (owner) { this.kvUsed += q.shared; this.anyShared = true; }
    this.queue.shift();
    q.slot = s; q.admit = this.t; q.kv = n.kv; this.kvUsed += n.kv;
    q.owner = owner; q.hit = this.prefix && (!owner || q.hist > 0);
    q.pfLeft = this.prefix ? (owner ? q.shared : 0) + q.uniq : q.shared + q.hist + q.uniq;
    this.slots[s] = q; this.running.push(q); this.reqs.push(q);
    if (this.kvUsed > this.kvPeak) this.kvPeak = this.kvUsed;
    return true;
  };
  Engine.prototype.plan = function () {
    var dec = [], pf = [], pfTok = 0, kvRead = this.sharedKv(), i, q;
    for (i = 0; i < this.running.length; i++) {
      q = this.running[i];
      if (q.fin !== null) continue;
      if (q.pfLeft > 0) { if (q.hit && !q.owner && !this.warm) continue; pf.push(q); }   // a hit waits until the shared prefix blocks exist
      else { dec.push(q); kvRead += (this.prefix ? 0 : q.shared) + q.hist + q.uniq + q.gen; }
    }
    var take = [];
    if (this.mode === 'chunked') {
      // the token budget is shared with the decode streams; a prompt is split across steps to fit what is left
      var budget = Math.max(512, BUDGET - dec.length);
      for (i = 0; i < pf.length && budget > 0; i++) { var k = Math.min(budget, pf[i].pfLeft); take.push([pf[i], k]); budget -= k; pfTok += k; }
    } else if (this.mode === 'continuous') {
      // whole prompts only, as many as fit the budget, and always at least one however long it is
      for (i = 0; i < pf.length; i++) { if (i && pfTok + pf[i].pfLeft > BUDGET) break; take.push([pf[i], pf[i].pfLeft]); pfTok += pf[i].pfLeft; }
    } else {
      for (i = 0; i < pf.length; i++) { take.push([pf[i], pf[i].pfLeft]); pfTok += pf[i].pfLeft; }
    }
    if (!dec.length && !take.length) return null;
    return { dec: dec, take: take, dt: this.ph.base + this.ph.b * kvRead + this.ph.pf * pfTok };
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
    var guard = 0, maxB = Math.min(this.ph.maxB, STATIC_B);
    while (guard++ < 5000) {
      this.arrive();
      if (this.mode === 'static') {
        if (!this.batch) {
          var ready = this.queue.length >= maxB || (this.queue.length && this.t - this.queue[0].arr >= STATIC_WAIT - 1e-6);
          if (ready) {
            this.batch = [];
            while (this.queue.length && this.batch.length < maxB) { var q0 = this.queue[0]; if (!this.admitOne(q0)) break; this.batch.push(q0); }
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
      tps: out / span * 1000, streams: busy / span,
      ttft50: pct(ft, 0.5), ttft99: pct(ft, 0.99), tpot: pct(tp, 0.5), itl99: itl99,
      queue: this.queue.length, kv: this.ph.kvBudget ? this.kvUsed / this.ph.kvBudget : 0, kvTokens: this.kvUsed, running: this.running.length
    };
  };

  if (typeof module !== 'undefined' && module.exports) { module.exports = { Engine: Engine, PRESETS: PRESETS, MODELS: MODELS, derive: derive, capacity: capacity }; }
  if (typeof document === 'undefined') return;

  /* ───────────── styles ───────────── */
  var CSS = [
    '.lb{--lb-pf:var(--brandD,#2737bd);--lb-dec:rgba(99,127,255,.55);--lb-hit:#0d9488;--lb-long:rgba(217,119,6,.13);--lb-longl:rgba(217,119,6,.55);--lb-wait:#d97706;--lb-lane:rgba(15,23,42,.035);background:var(--white,#fff);border:1px solid var(--line,#e2e8f0);border-radius:12px;box-shadow:0 1px 2px rgba(16,24,40,.05);font-family:var(--font,system-ui,sans-serif);color:var(--ink2,#334155);font-size:13px;line-height:1.45;overflow:hidden;min-width:0}',
    '.vlab .lb{--lb-pf:#637fff;--lb-dec:rgba(99,127,255,.35);--lb-hit:#2dd4bf;--lb-long:rgba(251,191,36,.12);--lb-longl:rgba(251,191,36,.45);--lb-wait:#fbbf24;--lb-lane:rgba(255,255,255,.04);--ok:#34d399;--warn:#fbbf24;--bad:#f87171;box-shadow:none}',
    '.lb *{box-sizing:border-box}',
    '.lb-bar{display:flex;flex-wrap:wrap;align-items:flex-end;gap:10px 14px;padding:12px 14px 10px;border-bottom:1px solid var(--line2,#eef2f7)}',
    '.lb-grp{display:flex;flex-direction:column;gap:5px;min-width:0}',
    '.lb-lab{font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--ink3,#5b687c)}',
    '.lb-lab output{font-family:var(--mono,monospace);font-variant-numeric:tabular-nums;text-transform:none;letter-spacing:0;color:var(--ink,#0f172a);font-weight:500;margin-left:6px}',
    '.lb-sel{font:inherit;font-size:12.5px;font-weight:500;color:var(--ink,#0f172a);background:var(--white,#fff);border:1px solid var(--line,#e2e8f0);border-radius:8px;padding:6px 28px 6px 10px;appearance:none;-webkit-appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 12 12%27%3E%3Cpath d=%27M2.5 4.5l3.5 3.5 3.5-3.5%27 fill=%27none%27 stroke=%27%235b687c%27 stroke-width=%271.4%27/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 9px center;background-size:11px;cursor:pointer;max-width:100%}',
    '.lb-sel:hover{border-color:var(--brand200,#bdcdff)}',
    '.lb-seg{display:inline-flex;border:1px solid var(--line,#e2e8f0);border-radius:8px;padding:2px;background:var(--bg,#f5f6fa);flex-wrap:wrap}',
    '.lb-seg button,.lb-btn{font:inherit;font-size:12.5px;font-weight:500;color:var(--ink2,#334155);background:transparent;border:0;border-radius:6px;padding:5px 10px;cursor:pointer;white-space:nowrap;line-height:1.3}',
    '.lb-seg button:hover{color:var(--ink,#0f172a)}',
    '.lb-seg button[aria-pressed="true"]{background:var(--white,#fff);color:var(--brand,#3f5cf6);box-shadow:0 0 0 1px var(--brand200,#bdcdff)}',
    '.vlab .lb-seg button[aria-pressed="true"]{color:var(--brandD,#8fa3ff)}',
    '.lb-btn{border:1px solid var(--line,#e2e8f0);background:var(--white,#fff);display:inline-flex;align-items:center;gap:6px;padding:6px 11px}',
    '.lb-btn:hover{border-color:var(--brand200,#bdcdff)}',
    '.lb-btn.lb-pri{background:var(--brand,#3f5cf6);border-color:var(--brand,#3f5cf6);color:#fff}',
    '.lb-btn.lb-pri:hover{background:var(--brandD,#2737bd)}',
    '.lb-btn:disabled{opacity:.45;cursor:not-allowed}',
    '.lb-btn svg{width:12px;height:12px;fill:currentColor}',
    '.lb button:focus-visible,.lb input:focus-visible,.lb select:focus-visible,.lb summary:focus-visible{outline:2px solid var(--brand,#3f5cf6);outline-offset:2px}',
    '.lb-sw{display:inline-flex;align-items:center;gap:8px;cursor:pointer;padding:5px 0;font-weight:500;color:var(--ink,#0f172a);font-size:12.5px;user-select:none}',
    '.lb-sw input{position:absolute;opacity:0;width:1px;height:1px}',
    '.lb-sw i{width:30px;height:18px;border-radius:9px;background:var(--line,#e2e8f0);position:relative;transition:background .15s;flex:none}',
    '.lb-sw i::after{content:"";position:absolute;left:2px;top:2px;width:14px;height:14px;border-radius:50%;background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.2);transition:transform .15s}',
    '.lb-sw input:checked+i{background:var(--brand,#3f5cf6)}.lb-sw input:checked+i::after{transform:translateX(12px)}',
    '.lb-sw input:focus-visible+i{outline:2px solid var(--brand,#3f5cf6);outline-offset:2px}',
    '.lb-sw input:disabled+i{background:var(--line2,#eef2f7)}.lb-sw input:disabled+i::after{transform:none;box-shadow:0 0 0 1px var(--line,#e2e8f0)}.lb-sw.lb-dis{color:var(--ink4,#94a3b8);cursor:not-allowed}',
    '.lb-rate input[type=range]{width:120px;accent-color:var(--brand,#3f5cf6);margin:3px 0}',
    '.lb-ctl{display:flex;gap:6px;align-items:center;margin-left:auto;flex-wrap:wrap}',
    '.lb-phys{margin:0;padding:8px 14px 0;font-family:var(--mono,monospace);font-size:11.5px;color:var(--ink3,#5b687c);font-variant-numeric:tabular-nums;line-height:1.5}',
    '.lb-phys b{font-weight:500;color:var(--ink,#0f172a)}',
    '.lb-note{margin:0;padding:8px 14px 0;color:var(--ink3,#5b687c);font-size:12.5px}',
    '.lb-note b{color:var(--ink,#0f172a);font-weight:600}',
    '.lb-note.lb-nofit{color:var(--bad,#be123c)}',
    '.lb-main{display:grid;grid-template-columns:minmax(0,1fr) 248px;gap:0 14px;padding:10px 14px 0;align-items:start}',
    '.lb-viz{position:relative;min-width:0}',
    '.lb-viz canvas{display:block;width:100%;height:260px}',
    '.lb-viz .lb-nf{position:absolute;inset:0;display:grid;place-items:center;text-align:center;padding:24px;color:var(--ink3,#5b687c);font-size:13px;background:var(--white,#fff);opacity:.88}',
    '.lb-viz .lb-nf[hidden]{display:none}',
    '.lb-hw .hwc-kv{row-gap:1px}.lb-hw .hwc-b{padding:9px 11px 10px}',
    '.lb-hw{min-width:0}',
    '.lb-hw .hwc{box-shadow:none}',
    '.lb-hw .hwc-kv dd.lb-dim{color:var(--ink3,#5b687c)}',
    '.lb-kvline{display:flex;justify-content:space-between;gap:8px;font-size:11px;color:var(--ink3,#5b687c);margin-top:6px;font-family:var(--mono,monospace);font-variant-numeric:tabular-nums}',
    '.lb-kvline b{white-space:nowrap}',
    '.lb-kvline b{color:var(--ink,#0f172a);font-weight:500}',
    '.lb-leg{display:flex;flex-wrap:wrap;gap:6px 14px;padding:8px 14px 10px;font-size:11.5px;color:var(--ink3,#5b687c)}',
    '.lb-leg span{display:inline-flex;align-items:center;gap:6px}',
    '.lb-leg i{display:inline-block;width:16px;height:8px;border-radius:2px}',
    '.lb-met{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));border-top:1px solid var(--line2,#eef2f7);background:var(--bg,#f5f6fa)}',
    '.lb-m{padding:8px 12px;border-right:1px solid var(--line2,#eef2f7);border-bottom:1px solid var(--line2,#eef2f7);min-width:0}',
    '.lb-m small{display:block;font-size:11px;color:var(--ink3,#5b687c);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.lb-m b{display:block;font-family:var(--mono,monospace);font-variant-numeric:tabular-nums;font-size:17px;font-weight:500;color:var(--ink,#0f172a);margin-top:2px;white-space:nowrap}',
    '.lb-m b em{font-style:normal;font-size:11.5px;color:var(--ink3,#5b687c);margin-left:3px}',
    '.lb-m b.lb-bad{color:var(--bad,#be123c)}.lb-m b.lb-warn{color:var(--warn,#b45309)}',
    '.lb-m svg{display:block;width:100%;height:16px;margin-top:4px;overflow:visible}',
    '.lb-det{border-top:1px solid var(--line2,#eef2f7);padding:10px 14px;font-size:12.5px}',
    '.lb-det summary{cursor:pointer;font-weight:600;color:var(--ink,#0f172a);list-style-position:inside}',
    '.lb-det ul{margin:8px 0 2px 18px;padding:0;color:var(--ink3,#5b687c)}.lb-det li{margin:3px 0}',
    '.lb-det code{font-family:var(--mono,monospace);font-size:12px;color:var(--ink,#0f172a)}',
    '@media(max-width:760px){.lb-main{grid-template-columns:1fr;gap:12px}.lb-hw .hwc{display:grid;grid-template-columns:minmax(0,160px) minmax(0,1fr)}.lb-hw .hwc-ph{aspect-ratio:auto;height:100%;min-height:150px}}',
    '@media(max-width:560px){.lb-bar{padding:12px}.lb-ctl{margin-left:0}.lb-main{padding:6px 10px 0}.lb-viz canvas{height:230px}.lb-hw .hwc{grid-template-columns:1fr}.lb-hw .hwc-ph{aspect-ratio:3/2;min-height:0}.lb-note,.lb-phys,.lb-leg,.lb-det{padding-left:12px;padding-right:12px}.lb-rate input[type=range]{width:120px}}'
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
  function fmtSmall(ms) {   // a per-token cost in ms, shown in the natural unit
    if (ms >= 1) return ms.toFixed(2) + ' ms';
    if (ms >= 1e-3) return (ms * 1e3).toFixed(ms * 1e3 >= 100 ? 0 : 1) + ' µs';
    return (ms * 1e6).toFixed(0) + ' ns';
  }
  function fmtRate(v) { return v >= 100 ? v.toFixed(0) : v >= 10 ? v.toFixed(1) : v.toFixed(2); }
  function fmtTok(n) { return n >= 1e6 ? (n / 1e6).toFixed(2) + 'M' : n >= 1000 ? (n / 1000).toFixed(n >= 100000 ? 0 : 1) + 'k' : String(n); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function tipAttr(t) { return t ? ' data-tip="' + esc(t) + '"' : ''; }
  function tipRows(card, tips) { var dts = card.querySelectorAll('.hwc-kv dt'); tips.forEach(function (t, i) { if (dts[i] && t) dts[i].setAttribute('data-tip', t); }); }
  var TIP = {
    model: 'Open-weight model. Its parameter count sets the weight bytes read every step; its layers, KV heads and head size set the bytes per cached token. Weights and KV cache are fp8.',
    gpu: 'The GPU one replica runs on: memory sets the KV budget, bandwidth the step time, the fp8 or bf16 rate the prefill cost.',
    traffic: 'Arrival shape: the prompt and output length distributions (log-normal, fixed seed) and any shared prefix.',
    sched: 'How requests share the GPU across engine steps.',
    cache: 'Keeps the shared prefix resident after the first request, so later requests skip prefilling it and share its KV entries; a follow-up chat turn also skips its own history, which is assumed to have stayed resident since the previous turn.',
    rate: 'Mean arrival rate, Poisson. Defaults to 70% of the estimated capacity for this model, GPU and traffic; the top of the range is about 1.6× that.',
    play: 'Runs or pauses the simulated clock.', reset: 'Restarts the run with a new random seed.', speed: 'Simulated time per real second.',
    spd1: 'Real time.', spd4: 'Four simulated seconds per real second.',
    lane: 'GPU batch slots over time, newest at the right: each bar is one request.',
    lgPf: 'The request\'s prompt is being processed (prefill), before its first token.', lgDec: 'The request is generating output, one token per engine step.',
    lgHit: 'Prefix-cache hit: the shared prefix, or this conversation\'s earlier turns, were already resident, so only the new part of the prompt was prefilled.',
    lgHeld: 'Static batching: the request has finished but its slot stays taken until the batch\'s longest answer ends.',
    lgLong: 'An engine step over three times the median step on screen, usually a large prefill. Every running stream waits for it.',
    lgWait: 'A queued request that has waited more than two seconds.',
    mTps: 'Output tokens per second over the last 5 s of simulated time.',
    mT50: 'Median time from arrival to first token over the last 20 s, counting requests still waiting with their wait so far.',
    mT99: '99th percentile time from arrival to first token over the last 20 s; the sparkline tracks the last 40 s.',
    mTpot: 'Median time per output token after the first, per completed request.',
    mItl: '99th percentile gap between consecutive tokens of a stream over the last 15 s. Long prefill steps show up here.',
    mStr: 'Average streams in the batch over the last 5 s.', mQ: 'Requests waiting for a slot or for KV-cache space.', mKv: 'Share of the KV-cache budget in use.',
    kvLine: 'Cached tokens in use against the KV-cache budget.',
    phys: 'The step-time formula derived from this model and GPU, the KV-cache budget and the estimated capacity for this traffic.'
  };
  var CARD_TIPS = ['Datasheet memory capacity and type.', 'Datasheet: HBM stacks or GDDR channels and the capacity of each.', 'Datasheet peak memory bandwidth; steps read at 75% of it.', 'Datasheet dense tensor-core rate the prefill runs at: fp8 where the GPU has it, otherwise bf16.', 'Parameters × 1 byte.', 'Weight bytes ÷ (bandwidth × 0.75): the fixed cost of every step, before the 1 ms launch overhead.', 'Bytes per cached token ÷ (bandwidth × 0.75): the cost each decoding stream adds per token of context.', '2 FLOPs per parameter ÷ (tensor rate × 0.6): the cost of each prompt token.', 'Cached tokens that fit: (memory − weights − 10% reserve) ÷ bytes per cached token.'];
  var MEM_TIPS = ['fp8 weights, resident for the whole run.', 'KV cache held by the running requests, updated as the simulation runs.', '10% of memory assumed for activations, CUDA context and fragmentation.', 'Memory not in use.'];

  /* ───────────── widget ───────────── */
  var uid = 0;
  function mount(root) {
    if (root.__lb) return; root.__lb = true;
    var HW = window.VO_HW;
    if (!HW) { root.innerHTML = '<p>This demo needs the hardware catalogue (hw.js) loaded first.</p>'; return; }
    var id = 'lb' + (++uid);
    var LAB = window.VO_LAB, shell = !!(LAB && root.closest('.vlab'));
    var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    var st = { model: 'qwen32b', gpu: shell && HW.gpus[LAB.gpu] ? LAB.gpu : 'h100', preset: 'chat', mode: 'continuous', prefix: true, rate: 1, speed: 1, playing: !reduce, seed: 11 };
    var ph, cap;

    function seg(name, label, opts, cur, tip) {
      return '<div class="lb-grp"><span class="lb-lab" id="' + id + name + '"' + tipAttr(tip) + '>' + label + '</span><div class="lb-seg" role="group" aria-labelledby="' + id + name + '" data-k="' + name + '">' +
        opts.map(function (o) { return '<button type="button" data-v="' + o[0] + '" aria-pressed="' + (o[0] === cur) + '"' + tipAttr(o[2]) + '>' + o[1] + '</button>'; }).join('') + '</div></div>';
    }
    function sel(name, label, opts, cur, tip) {
      return '<div class="lb-grp"><label class="lb-lab" for="' + id + name + '"' + tipAttr(tip) + '>' + label + '</label><select class="lb-sel" id="' + id + name + '" data-k="' + name + '">' +
        opts.map(function (o) { return '<option value="' + o[0] + '"' + (o[0] === cur ? ' selected' : '') + '>' + esc(o[1]) + '</option>'; }).join('') + '</select></div>';
    }
    root.innerHTML =
      '<div class="lb">' +
      '<div class="lb-bar">' +
      sel('model', 'Model · fp8', Object.keys(MODELS).map(function (k) { return [k, MODELS[k].label]; }), st.model, TIP.model) +
      (shell ? '' : sel('gpu', 'GPU · one replica', GPU_KEYS.map(function (k) { return [k, HW.gpus[k].name]; }), st.gpu, TIP.gpu)) +
      seg('preset', 'Traffic', Object.keys(PRESETS).map(function (k) { return [k, PRESETS[k].label, PRESETS[k].hint]; }), st.preset, TIP.traffic) +
      seg('mode', 'Scheduler', Object.keys(MODES).map(function (k) { return [k, MODES[k].label, MODES[k].note]; }), st.mode, TIP.sched) +
      '<div class="lb-grp"><span class="lb-lab"' + tipAttr(TIP.cache) + '>Cache</span><label class="lb-sw"' + tipAttr(TIP.cache) + '><input type="checkbox" data-k="prefix" checked><i></i><span>Prefix caching</span></label></div>' +
      '<div class="lb-grp lb-rate"><label class="lb-lab" for="' + id + 'r"' + tipAttr(TIP.rate) + '>Arrivals<output>—</output></label><input id="' + id + 'r" type="range" min="0.1" max="6" step="0.1" value="3" data-k="rate"></div>' +
      '<div class="lb-ctl"><button type="button" class="lb-btn lb-pri" data-a="play"' + tipAttr(TIP.play) + '></button><button type="button" class="lb-btn" data-a="reset"' + tipAttr(TIP.reset) + '>' + ICON_RESET + 'Reset</button>' +
      '<div class="lb-seg" role="group" aria-label="Playback speed" data-k="speed"' + tipAttr(TIP.speed) + '><button type="button" data-v="1" aria-pressed="true"' + tipAttr(TIP.spd1) + '>1×</button><button type="button" data-v="4" aria-pressed="false"' + tipAttr(TIP.spd4) + '>4×</button></div></div>' +
      '</div>' +
      '<div class="lb-main"><div class="lb-viz"><canvas role="img" aria-label="GPU batch slots over time: each bar is a request, darker while its prompt is prefilled, lighter while it generates."></canvas><div class="lb-nf" hidden></div></div><div class="lb-hw"></div></div>' +
      '<div class="lb-leg"><span' + tipAttr(TIP.lgPf) + '><i style="background:var(--lb-pf)"></i>Prefill</span><span' + tipAttr(TIP.lgDec) + '><i style="background:var(--lb-dec)"></i>Decode</span>' +
      '<span' + tipAttr(TIP.lgHit) + '><i style="background:var(--lb-hit)"></i>Prefix cache hit</span><span' + tipAttr(TIP.lgHeld) + '><i style="background:transparent;border-top:2px dashed var(--ink4,#94a3b8);height:0;border-radius:0"></i>Slot held, idle</span>' +
      '<span' + tipAttr(TIP.lgLong) + '><i style="background:var(--lb-long);border-left:2px solid var(--lb-longl)"></i>Long step: every stream stalls</span><span' + tipAttr(TIP.lgWait) + '><i style="background:var(--lb-wait);width:8px"></i>Waiting &gt; 2 s</span></div>' +
      '<div class="lb-met">' +
      '<div class="lb-m"' + tipAttr(TIP.mTps) + '><small>Output throughput</small><b data-m="tps">—</b></div>' +
      '<div class="lb-m"' + tipAttr(TIP.mT50) + '><small>TTFT p50</small><b data-m="ttft50">—</b></div>' +
      '<div class="lb-m"' + tipAttr(TIP.mT99) + '><small>TTFT p99</small><b data-m="ttft99">—</b><svg viewBox="0 0 200 16" preserveAspectRatio="none" aria-hidden="true"><polyline fill="none" stroke="var(--brand,#3f5cf6)" stroke-width="1.5" vector-effect="non-scaling-stroke" points=""/></svg></div>' +
      '<div class="lb-m"' + tipAttr(TIP.mTpot) + '><small>TPOT p50</small><b data-m="tpot">—</b></div>' +
      '<div class="lb-m"' + tipAttr(TIP.mItl) + '><small>Inter-token p99</small><b data-m="itl99">—</b></div>' +
      '<div class="lb-m"' + tipAttr(TIP.mStr) + '><small>Streams running</small><b data-m="streams">—</b></div>' +
      '<div class="lb-m"' + tipAttr(TIP.mQ) + '><small>Queue</small><b data-m="queue">0</b></div>' +
      '<div class="lb-m"' + tipAttr(TIP.mKv) + '><small>KV cache in use</small><b data-m="kv">0<em>%</em></b></div>' +
      '</div>' +
      '<p class="lb-note" aria-live="polite"></p>' +
      '<p class="lb-phys" aria-live="polite"' + tipAttr(TIP.phys) + '></p>' +
      '<details class="lb-det"><summary>What the simulation models</summary><ul data-det></ul></details></div>';

    var el = root.querySelector('.lb'), canvas = el.querySelector('canvas'), ctx = canvas.getContext('2d');
    var note = el.querySelector('.lb-note'), phys = el.querySelector('.lb-phys'), playBtn = el.querySelector('[data-a="play"]'), nf = el.querySelector('.lb-nf');
    var rateIn = el.querySelector('[data-k="rate"]'), rateOut = el.querySelector('.lb-rate output');
    var prefIn = el.querySelector('[data-k="prefix"]'), prefLab = prefIn.closest('.lb-sw');
    var hwBox = el.querySelector('.lb-hw'), det = el.querySelector('[data-det]');
    var M = {}; [].forEach.call(el.querySelectorAll('[data-m]'), function (b) { M[b.getAttribute('data-m')] = b; });
    var spark = el.querySelector('.lb-m polyline');
    var eng, clock, hist, lastHist, lastMet, lanes = 16, memBar = null, kvLine = null, lastMemTs = 0;

    function css(n, f) { var v = getComputedStyle(el).getPropertyValue(n).trim(); return v || f; }
    var C = {};
    function readColours() {
      C.brand = css('--brand', '#3f5cf6'); C.brand2 = css('--brand2', '#637fff'); C.brandD = css('--brandD', '#2737bd');
      C.brand200 = css('--brand200', '#bdcdff'); C.ink = css('--ink', '#0f172a'); C.ink3 = css('--ink3', '#5b687c'); C.ink4 = css('--ink4', '#94a3b8');
      C.line = css('--line', '#e2e8f0'); C.line2 = css('--line2', '#eef2f7'); C.mono = css('--mono', 'ui-monospace,monospace'); C.font = css('--font', 'system-ui,sans-serif');
      C.white = css('--white', '#fff'); C.pf = css('--lb-pf', '#2737bd'); C.dec = css('--lb-dec', 'rgba(99,127,255,.55)'); C.hit = css('--lb-hit', '#0d9488');
      C.long = css('--lb-long', 'rgba(217,119,6,.13)'); C.longl = css('--lb-longl', 'rgba(217,119,6,.55)'); C.wait = css('--lb-wait', '#d97706'); C.lane = css('--lb-lane', 'rgba(15,23,42,.035)');
    }

    /* the physics for the chosen model and GPU, and everything that depends on it */
    function rederive() {
      var m = MODELS[st.model], g = HW.gpus[st.gpu];
      ph = derive(m, g);
      cap = ph.fits ? capacity(ph, st.preset, st.prefix) : null;
      var p = PRESETS[st.preset];
      lanes = ph.fits ? Math.max(8, Math.min(32, cap.ncap)) : 8;
      // arrivals slider: default at 70% of the estimated capacity, range up to ~1.6× the default
      if (cap) {
        var mx = cap.rate * 1.6, step = mx >= 50 ? 1 : mx >= 10 ? 0.5 : mx >= 2 ? 0.1 : 0.02;
        rateIn.min = step; rateIn.max = (Math.ceil(mx / step) * step).toFixed(2); rateIn.step = step;
        st.rate = Math.max(step, Math.round(cap.rate / step) * step);
        rateIn.value = st.rate;
      }
      rateOut.textContent = cap ? fmtRate(st.rate) + ' req/s' : '—';
      rateIn.disabled = !ph.fits;
      prefIn.disabled = !p.shared; prefLab.classList.toggle('lb-dis', !p.shared);
      prefLab.setAttribute('data-tip', TIP.cache);
      playBtn.disabled = !ph.fits;
      // readout
      phys.hidden = !ph.fits;
      phys.innerHTML = ph.fits
        ? 'Step time = <b>' + ph.base.toFixed(1) + ' ms</b> + <b>' + fmtSmall(ph.b) + '</b> × KV tokens read + <b>' + fmtSmall(ph.pf) + '</b> × prompt tokens prefilled · KV cache <b>' + fmtTok(ph.kvBudget) + ' tokens</b>' +
          (cap ? ' · capacity ≈ <b>' + fmtRate(cap.lmax) + ' req/s</b> on this traffic' : '')
        : m.label + ' in fp8 is ' + HW.gb(ph.weights) + '; the ' + g.name + ' has ' + g.mem + ' GB and ' + HW.gb(ph.reserve) + ' is reserved, so it does not fit on one GPU.';
      nf.hidden = ph.fits;
      nf.textContent = ph.fits ? '' : 'Does not fit on one ' + g.name + '. A smaller model or a GPU with more memory would be needed; splitting across GPUs is not modelled.';
      buildCard(m, g);
      buildDetails(m, g);
    }
    function buildCard(m, g) {
      var rows = [
        ['Memory', g.mem + ' GB ' + g.memType],
        [g.memType.indexOf('GDDR') === 0 ? 'Channels' : 'Stacks', g.stacks + ' × ' + g.stackGB + ' GB'],
        ['Bandwidth', g.bw + ' TB/s'],
        ['Compute used', HW.fmt(ph.tflops) + ' TFLOPS ' + (ph.fp8 ? 'fp8' : 'bf16')],
        ['Weights, fp8', HW.gb(ph.weights)],
        ['Weight read / step', ph.fits ? (ph.base - OVERHEAD).toFixed(1) + ' ms' : '—'],
        ['KV read / token', fmtSmall(ph.b)],
        ['Prefill / token', fmtSmall(ph.pf)],
        ['KV cache budget', ph.fits ? fmtTok(ph.kvBudget) + ' tok' : '0']
      ];
      var card = HW.card(g, { photo: !shell, rows: rows, sub: g.arch === 'cdna3' ? g.cus + ' CUs · ' + HW.arch[g.arch].name : g.sms + ' SMs · ' + HW.arch[g.arch].name,
        note: (ph.fp8 ? '' : 'No fp8 tensor cores: weights stay fp8 in memory and are dequantised on the fly; prefill is priced at the bf16 rate. ') +
              (shell ? '' : 'Reads at ' + Math.round(BW_EFF * 100) + '% of peak bandwidth, prefill at ' + Math.round(FLOPS_EFF * 100) + '% of peak compute, ' + OVERHEAD + ' ms launch overhead per step, ' + Math.round(RESERVE * 100) + '% of memory reserved. All assumptions; see below.') });
      tipRows(card, CARD_TIPS);
      hwBox.innerHTML = ''; hwBox.appendChild(card);
      var slot = card.querySelector('.hwc-slot');
      kvLine = document.createElement('div'); kvLine.className = 'lb-kvline'; kvLine.setAttribute('data-tip', TIP.kvLine);
      slot.appendChild(kvLine);
      memBar = null; drawMem(0, true);
    }
    function drawMem(kvTokens, force) {
      if (!memBar || force) {
        var bar = HW.memoryBar(HW.gpus[st.gpu], memParts(kvTokens));
        if (memBar) memBar.parentNode.replaceChild(bar, memBar); else kvLine.parentNode.insertBefore(bar, kvLine);
        memBar = bar;
        [].forEach.call(bar.querySelectorAll('.hwm-lg span'), function (sp, i) { if (MEM_TIPS[i]) sp.setAttribute('data-tip', MEM_TIPS[i]); });
      } else {
        // update the stack fills in place
        var parts = memParts(kvTokens), capB = ph.memB;
        [].forEach.call(memBar.querySelectorAll('.hwm-st'), function (stk) {
          var x = 0;
          [].forEach.call(stk.children, function (seg, k) { var w = Math.max(0, parts[k].bytes) / capB * 100; seg.style.left = x + '%'; seg.style.width = w + '%'; x += w; });
        });
        var lg = memBar.querySelectorAll('.hwm-lg span');
        if (lg[1]) lg[1].textContent = 'KV cache in use ' + HW.gb(parts[1].bytes);
        if (lg[3]) lg[3].textContent = 'free ' + HW.gb(Math.max(0, capB - parts[0].bytes - parts[1].bytes - parts[2].bytes));
      }
      kvLine.innerHTML = '<span>KV in use</span><b>' + fmtTok(kvTokens) + ' / ' + fmtTok(ph.kvBudget) + ' tok</b>';
    }
    function memParts(kvTokens) {
      return [
        { label: 'Weights', bytes: ph.weights, color: C.pf || '#2737bd' },
        { label: 'KV cache in use', bytes: kvTokens * ph.kvTok, color: C.brand2 || '#637fff' },
        { label: 'Reserve', bytes: ph.reserve, color: C.ink4 || '#94a3b8' }
      ];
    }
    function buildDetails(m, g) {
      var p = PRESETS[st.preset];
      det.innerHTML = [
        'One replica of <code>' + esc(m.label) + '</code> on one <code>' + esc(g.name) + '</code>. Weights and KV cache are fp8: <code>' + HW.gb(ph.weights) + '</code> of weights and <code>' + fmtTok(ph.kvTok) + ' B</code> per cached token (2 × ' + m.layers + ' layers × ' + m.kvHeads + ' KV heads × ' + m.headDim + ' dims). ' + Math.round(RESERVE * 100) + '% of memory is reserved; the rest, <code>' + fmtTok(ph.kvBudget) + ' tokens</code>, is the KV cache. A request is admitted only if its prompt and full output fit, and at most ' + MAXB + ' run at once.',
        'Each engine step costs <code>' + ph.base.toFixed(1) + ' ms + ' + fmtSmall(ph.b) + ' × KV tokens read + ' + fmtSmall(ph.pf) + ' × prompt tokens prefilled</code>. The first term is the weights read once per step at ' + Math.round(BW_EFF * 100) + '% of ' + g.bw + ' TB/s plus ' + OVERHEAD + ' ms of launch overhead; the KV term is the same bandwidth applied to the cache read by decode attention; the prefill term is 2 FLOPs per parameter per token at ' + Math.round(FLOPS_EFF * 100) + '% of ' + HW.fmt(ph.tflops) + ' ' + (ph.fp8 ? 'fp8' : 'bf16') + ' TFLOPS. Decode is memory-bound and prefill compute-bound, which is the first-order picture of a transformer server. The efficiency factors are assumptions, not measurements.',
        'Arrivals are Poisson. Prompt and output lengths are log-normal, drawn from a fixed seed, so every scheduler sees the same requests. The slider defaults to 70% of the estimated capacity for the chosen traffic' + (cap ? ' (about ' + fmtRate(cap.lmax) + ' req/s here, where the step model or the prefill budget saturates)' : '') + ', or less if the KV cache or the batch limit would fill first.',
        'Static batching waits for ' + STATIC_B + ' requests or ' + (STATIC_WAIT / 1000) + ' s, prefills them in one step and runs the batch until its longest answer ends. Continuous batching admits and retires requests every step and prefills whole prompts, up to ' + fmtTok(BUDGET) + ' tokens per step or one prompt however long. Chunked prefill splits prompts so that prefill and decode together stay within the ' + fmtTok(BUDGET) + '-token step budget (vLLM\u2019s <code>max_num_batched_tokens</code>); a smaller budget smooths inter-token latency and lowers prompt throughput.',
        'Prefix caching keeps the shared prefix (a chat system prompt, a RAG system prompt, agent instructions and tools) in the cache after the first request, so later requests skip prefilling it and share its KV entries. Chat traffic is also multi-turn: 60% of its requests are follow-up turns that resend the conversation so far (about 900 tokens on average), and with caching on that history is treated as still resident from the previous turn, so only the new message is prefilled. Eviction between turns is not modelled; on a busy server some of those blocks would be gone.',
        'A step is shaded as long when it takes over three times the median step on screen. Not modelled: tensor parallelism, speculative decoding, CUDA graphs, paged-attention fragmentation, and the real kernels’ efficiency at small batch sizes. TTFT counts requests still waiting with their wait so far. Inter-token p99 is the 99th percentile gap between tokens of a stream. The lane chart shows up to ' + lanes + ' streams; any beyond that are counted, not drawn. Figures are from this model, not measurements of any product.'
      ].map(function (t) { return '<li>' + t + '</li>'; }).join('');
    }

    function reset() {
      eng = new Engine(st.preset, st.mode, st.prefix, st.rate, st.seed, ph);
      clock = 0; hist = []; lastHist = 0; lastMet = -1e9;
      updateNote(); updateMetrics(true); draw(); drawMem(0, false);
    }
    function updateNote() {
      var p = PRESETS[st.preset];
      if (!ph.fits) { note.className = 'lb-note lb-nofit'; note.innerHTML = '<b>Does not fit.</b> ' + esc(phys.textContent); return; }
      note.className = 'lb-note';
      var txt = '<b>' + MODES[st.mode].label + '.</b> ' + MODES[st.mode].note;
      var sh = p.shared >= 1000 ? (p.shared / 1000).toFixed(1) + 'k' : p.shared;
      if (p.shared) txt += st.prefix ? ' Prefix caching is on: the shared ' + sh + '-token prefix is prefilled once' + (p.turns ? ', and follow-up turns skip their history' : '') + '.' : ' Prefix caching is off: every request prefills the shared ' + sh + '-token prefix' + (p.turns ? ' and its whole history' : '') + ' again.';
      note.innerHTML = txt;
    }
    function setPlay(v) {
      st.playing = v && ph.fits;
      playBtn.innerHTML = st.playing ? ICON_PAUSE + 'Pause' : ICON_PLAY + (reduce && clock === 0 ? 'Run' : 'Play');
      playBtn.setAttribute('aria-label', st.playing ? 'Pause simulation' : 'Run simulation');
    }

    el.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      var g = b.parentNode.getAttribute('data-k');
      if (g) {
        [].forEach.call(b.parentNode.children, function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        var v = b.getAttribute('data-v');
        if (g === 'speed') { st.speed = +v; return; }
        st[g] = v;
        if (g === 'preset') rederive();
        reset(); return;
      }
      var a = b.getAttribute('data-a');
      if (a === 'play') setPlay(!st.playing);
      if (a === 'reset') { st.seed++; reset(); }
    });
    el.addEventListener('change', function (e) {
      var s = e.target.closest('select.lb-sel'); if (!s) return;
      st[s.getAttribute('data-k')] = s.value; rederive(); reset(); setPlay(st.playing || !reduce);
    });
    rateIn.addEventListener('input', function () { st.rate = +rateIn.value; rateOut.textContent = fmtRate(st.rate) + ' req/s'; });
    rateIn.addEventListener('change', reset);
    prefIn.addEventListener('change', function () { st.prefix = prefIn.checked; rederive(); reset(); });

    /* sizing */
    var W = 0, H = 0, dpr = 1, hatch = null;
    function resize() {
      // on desktop the lane chart is as tall as the hardware card beside it, so the two read as one panel
      var wide = el.clientWidth > 760, ch = wide ? Math.max(240, Math.min(shell ? 340 : 600, hwBox.offsetHeight)) : (el.clientWidth < 560 ? 230 : 260);
      if (Math.abs(parseFloat(canvas.style.height || '0') - ch) > 1) canvas.style.height = ch + 'px';
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
      var laneH = (H - top - axis) / lanes, span = (narrow ? 8 : 12) * 1000, pps = (R - G - 8) / span;
      function X(t) { return R - (clock - t) * pps; }
      ctx.font = '600 10px ' + C.font; ctx.textBaseline = 'alphabetic';
      ctx.fillStyle = C.ink3; ctx.fillText('QUEUE', 0, 11);
      ctx.fillText(narrow ? 'BATCH SLOTS' : 'GPU BATCH SLOTS', G + 8, 11);
      // lanes
      for (var i = 0; i < lanes; i++) {
        if (i % 2) continue;
        ctx.fillStyle = C.lane; ctx.fillRect(G + 8, top + i * laneH, R - G - 8, laneH);
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
      // long engine steps (a big prefill): every decoding stream waits for them. Long means over three times the median step in view.
      var dts = [], j;
      for (j = eng.steps.length - 1; j >= 0; j--) { if (eng.steps[j].t1 < clock - span) break; if (eng.steps[j].t1 <= clock) dts.push(eng.steps[j].dt); }
      dts.sort(function (a, b) { return a - b; });
      var longStep = Math.max(40, 3 * (dts.length ? dts[dts.length >> 1] : ph.base));
      for (j = eng.steps.length - 1; j >= 0; j--) {
        var sp = eng.steps[j]; if (sp.t1 < clock - span) break;
        if (sp.dt < longStep || sp.t1 > clock) continue;
        var sx0 = X(sp.t1 - sp.dt), sx1 = X(sp.t1);
        ctx.fillStyle = C.long; ctx.fillRect(sx0, top, Math.max(1, sx1 - sx0), H - top - axis);
        ctx.fillStyle = C.longl; ctx.fillRect(sx0, top, 1.5, H - top - axis);
      }
      var bh = Math.max(3, laneH - 3), rad = Math.min(3, bh / 2), hidden = 0;
      for (var k = 0; k < eng.reqs.length; k++) {
        var q = eng.reqs[k];
        if (q.admit > clock) continue;
        if (q.slot >= lanes) { if (q.rel === null || q.rel > clock) hidden++; continue; }
        var y = top + q.slot * laneH + (laneH - bh) / 2;
        var fin = q.fin !== null && q.fin <= clock ? q.fin : null;
        var fade = fin === null ? 1 : Math.max(.3, 1 - (clock - fin) / 5000);
        var pe = q.pfEnd !== null && q.pfEnd <= clock ? q.pfEnd : null;
        var x0 = X(q.admit), xp = X(pe === null ? clock : pe), xe = X(fin === null ? clock : fin);
        ctx.globalAlpha = fade;
        // prefill
        if (xp - x0 > .3) {
          ctx.fillStyle = C.pf; rr(x0, y, Math.max(1, xp - x0), bh, rad); ctx.fill();
          ctx.fillStyle = hatchPat(); ctx.fill();
        }
        // decode
        if (pe !== null && xe - xp > .3) {
          ctx.fillStyle = C.dec; rr(xp, y, Math.max(1, xe - xp), bh, rad); ctx.fill();
          ctx.fillStyle = C.brand2; ctx.fillRect(Math.max(xp, xe - 2), y, 2, bh);
        }
        if (q.hit) { ctx.globalAlpha = fade; ctx.fillStyle = C.hit; ctx.fillRect(x0, y, 3, bh); }
        // static batch: slot held after the request finished
        if (fin !== null && (q.rel === null || q.rel > fin)) {
          var xr = X(q.rel !== null && q.rel <= clock ? q.rel : clock);
          ctx.globalAlpha = 1; ctx.strokeStyle = C.ink4; ctx.setLineDash([3, 3]); ctx.beginPath();
          ctx.moveTo(xe + 2, y + bh / 2 + .5); ctx.lineTo(xr, y + bh / 2 + .5); ctx.stroke(); ctx.setLineDash([]);
        }
      }
      ctx.restore(); ctx.globalAlpha = 1;
      if (hidden) {
        ctx.font = '500 10.5px ' + C.mono; ctx.textAlign = 'right'; ctx.fillStyle = C.ink3;
        var lbl = '+' + hidden + ' more running, not drawn', tw = ctx.measureText(lbl).width;
        ctx.fillStyle = C.white; ctx.globalAlpha = .9; ctx.fillRect(R - tw - 10, H - axis - 16, tw + 8, 14); ctx.globalAlpha = 1;
        ctx.fillStyle = C.ink3; ctx.fillText(lbl, R - 6, H - axis - 5); ctx.textAlign = 'left';
      }
      // queue
      var waiting = eng.queue.filter(function (q) { return q.arr <= clock; });
      var cs = narrow ? 6 : 7, gap = 2, cols = Math.max(1, Math.floor((G - 4) / (cs + gap))), rows = Math.floor((H - top - axis - 14) / (cs + gap));
      var cap2 = cols * rows, shown = Math.min(waiting.length, waiting.length > cap2 ? cap2 - cols : cap2);
      for (var w = 0; w < shown; w++) {
        var cx = (w % cols) * (cs + gap), cy = top + Math.floor(w / cols) * (cs + gap);
        ctx.fillStyle = clock - waiting[w].arr > 2000 ? C.wait : C.brand200; rr(cx, cy, cs, cs, 1.5); ctx.fill();
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
      var itlWarn = Math.max(60, 3 * ph.base), itlBad = Math.max(150, 8 * ph.base);
      M.itl99.className = m.itl99 > itlBad ? 'lb-bad' : m.itl99 > itlWarn ? 'lb-warn' : '';
      M.streams.innerHTML = clock > 0 ? m.streams.toFixed(m.streams >= 10 ? 0 : 1) + '<em>avg</em>' : '—';
      M.queue.textContent = m.queue; M.queue.className = m.queue > 20 ? 'lb-bad' : m.queue > 6 ? 'lb-warn' : '';
      M.kv.innerHTML = Math.round(m.kv * 100) + '<em>%</em>'; M.kv.className = m.kv > 0.95 ? 'lb-warn' : '';
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
      if (ts - lastMemTs > 250) { lastMemTs = ts; drawMem(eng.kvUsed, false); }
    }

    readColours(); rederive(); reset(); setPlay(st.playing);
    if (shell) LAB.subscribe(function (msg) { if (msg.kind !== 'gpu' || msg.gpu === st.gpu || !HW.gpus[msg.gpu]) return; st.gpu = msg.gpu; rederive(); reset(); setPlay(st.playing || !reduce); resize(); });
    if ('ResizeObserver' in window) { var ro = new ResizeObserver(resize); ro.observe(canvas); ro.observe(hwBox); } else window.addEventListener('resize', resize);
    resize();
    if ('IntersectionObserver' in window) new IntersectionObserver(function (es) { visible = es[0].isIntersecting; last = 0; }, { threshold: 0.05 }).observe(el);
    document.addEventListener('visibilitychange', function () { last = 0; });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { readColours(); draw(); });
    requestAnimationFrame(tick);
  }

  function init() { injectCss(); [].forEach.call(document.querySelectorAll('[data-lab="batching"]'), mount); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
