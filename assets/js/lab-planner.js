/* Capacity planner: a first-order roofline estimate of what a model needs to serve
   a given load. Renders into every [data-lab="planner"]. No libraries, no network. */
(function () {
  'use strict';

  var MODELS = [
    // total / active params (B), layers, KV heads, head dim; kvPerLayer overrides (MLA)
    { id: 'llama8',   name: 'Llama-3.1-8B',        total: 8.03,  active: 8.03,  layers: 32, kvh: 8,  hd: 128 },
    { id: 'mistral24',name: 'Mistral-Small-24B',   total: 23.6,  active: 23.6,  layers: 40, kvh: 8,  hd: 128 },
    { id: 'gemma27',  name: 'Gemma-3-27B',         total: 27.4,  active: 27.4,  layers: 62, kvh: 16, hd: 128 },
    { id: 'qwen32',   name: 'Qwen3-32B',           total: 32.8,  active: 32.8,  layers: 64, kvh: 8,  hd: 128 },
    { id: 'llama70',  name: 'Llama-3.3-70B',       total: 70.6,  active: 70.6,  layers: 80, kvh: 8,  hd: 128 },
    { id: 'qwen235',  name: 'Qwen3-235B-A22B (MoE)', total: 235, active: 22,    layers: 94, kvh: 4,  hd: 128 },
    { id: 'dsv3',     name: 'DeepSeek-V3 (MoE, MLA)', total: 671, active: 37,   layers: 61, kvPerLayer: 576 }
  ];
  var GPUS = [
    // memory GB, bandwidth TB/s, dense TFLOPS bf16 / fp8, $/GPU-hour default
    { id: 'h100',  name: 'H100 SXM 80 GB',  mem: 80,  bw: 3.35,  bf16: 989,  fp8: 1979, price: 2.50 },
    { id: 'h200',  name: 'H200 141 GB',     mem: 141, bw: 4.8,   bf16: 989,  fp8: 1979, price: 3.50 },
    { id: 'b200',  name: 'B200 180 GB',     mem: 180, bw: 8.0,   bf16: 2250, fp8: 4500, price: 5.50 },
    { id: 'mi300', name: 'MI300X 192 GB',   mem: 192, bw: 5.3,   bf16: 1307, fp8: 2615, price: 2.50 },
    { id: 'a100',  name: 'A100 80 GB',      mem: 80,  bw: 2.039, bf16: 312,  fp8: 0,    price: 1.60 },
    { id: 'l40s',  name: 'L40S 48 GB',      mem: 48,  bw: 0.864, bf16: 362,  fp8: 733,  price: 1.00 },
    { id: 'r5090', name: 'RTX 5090 32 GB',  mem: 32,  bw: 1.79,  bf16: 209,  fp8: 419,  price: 0.70 }
  ];
  var WPREC = [['bf16', 2], ['fp8', 1], ['int4', 0.5625]];
  var KVPREC = [['bf16', 2], ['fp8', 1]];
  var USERS = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024];
  var PROMPT = [256, 512, 1024, 2048, 4096, 8192, 16384, 32768];
  var OUTPUT = [100, 200, 300, 500, 1000, 2000, 4000];
  var SLO = [200, 300, 500, 800, 1200, 2000, 3000];
  var TPS = [1, 2, 4, 8];
  var BW_EFF = 0.75, FLOP_EFF = 0.5, PREFILL_EFF = 0.6, MAX_BATCH = 512;

  var CSS = [
    '.lp{font-family:var(--font);color:var(--ink2);background:var(--white);border:1px solid var(--line);border-radius:12px;box-shadow:0 1px 2px rgba(16,24,40,.05);display:grid;grid-template-columns:320px minmax(0,1fr);overflow:hidden;text-align:left;line-height:1.45;font-size:14px}',
    '.lp *{box-sizing:border-box}',
    '.lp-ctl{padding:18px;border-right:1px solid var(--line);background:#fbfcfe;display:flex;flex-direction:column;gap:14px;min-width:0}',
    '.lp-hd{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3)}',
    '.lp-hd i{width:7px;height:7px;border-radius:50%;background:var(--brand)}',
    '.lp-f{display:flex;flex-direction:column;gap:6px;min-width:0}',
    '.lp-f>label,.lp-f>.lp-lab{font-size:12.5px;font-weight:600;color:var(--ink);display:flex;justify-content:space-between;gap:8px}',
    '.lp-f>label output,.lp-f>.lp-lab output{font-family:var(--mono);font-weight:500;color:var(--brand);font-variant-numeric:tabular-nums}',
    '.lp-sel,.lp-num{width:100%;font:inherit;font-size:13.5px;color:var(--ink);background:var(--white);border:1px solid var(--line);border-radius:8px;padding:8px 10px;min-width:0}',
    '.lp-sel{appearance:none;-webkit-appearance:none;background-image:linear-gradient(45deg,transparent 50%,var(--ink3) 50%),linear-gradient(135deg,var(--ink3) 50%,transparent 50%);background-position:calc(100% - 15px) 52%,calc(100% - 10px) 52%;background-size:5px 5px;background-repeat:no-repeat;padding-right:28px}',
    '.lp-inl{flex-direction:row;align-items:center;justify-content:space-between;gap:10px}',
    '.lp-inl>label{font-weight:500!important;color:var(--ink2)!important}',
    '.lp-usd{position:relative;width:104px;flex:none}.lp-usd::before{content:"$";position:absolute;left:10px;top:50%;transform:translateY(-50%);font-family:var(--mono);font-size:13px;color:var(--ink3)}.lp-usd .lp-num{padding-left:22px}',
    '.lp-num{font-family:var(--mono);font-variant-numeric:tabular-nums}',
    '.lp-sel:hover,.lp-num:hover{border-color:var(--brand200)}',
    '.lp-seg{display:flex;border:1px solid var(--line);border-radius:8px;background:var(--white);padding:2px;gap:2px}',
    '.lp-seg button{flex:1;font:inherit;font-size:12.5px;font-weight:600;font-family:var(--mono);color:var(--ink3);background:none;border:0;border-radius:6px;padding:6px 4px;cursor:pointer}',
    '.lp-seg button:hover{color:var(--ink)}',
    '.lp-seg button[aria-pressed="true"]{background:var(--brand);color:#fff}',
    '.lp-row2{display:grid;grid-template-columns:1fr 1fr;gap:10px}',
    '.lp input[type=range]{-webkit-appearance:none;appearance:none;width:100%;height:20px;background:none;margin:0;cursor:pointer}',
    '.lp input[type=range]::-webkit-slider-runnable-track{height:4px;border-radius:2px;background:linear-gradient(var(--brand),var(--brand)) 0/var(--p,50%) 100% no-repeat,var(--line)}',
    '.lp input[type=range]::-moz-range-track{height:4px;border-radius:2px;background:var(--line)}',
    '.lp input[type=range]::-moz-range-progress{height:4px;border-radius:2px;background:var(--brand)}',
    '.lp input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:16px;height:16px;border-radius:50%;background:var(--white);border:2px solid var(--brand);margin-top:-6px;box-shadow:0 1px 2px rgba(16,24,40,.15)}',
    '.lp input[type=range]::-moz-range-thumb{width:12px;height:12px;border-radius:50%;background:var(--white);border:2px solid var(--brand)}',
    '.lp button:focus-visible,.lp select:focus-visible,.lp input:focus-visible,.lp summary:focus-visible{outline:2px solid var(--brand);outline-offset:2px}',
    '.lp-out{padding:18px 20px;display:flex;flex-direction:column;gap:16px;min-width:0}',
    '.lp-kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));border:1px solid var(--line);border-radius:10px;overflow:hidden}',
    '.lp-kpi{padding:10px 12px;border-left:1px solid var(--line);min-width:0}',
    '.lp-kpi:first-child{border-left:0;background:var(--brand50)}',
    '.lp-kpi small{display:block;font-size:11.5px;color:var(--ink3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.lp-kpi b{display:block;font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:20px;font-weight:500;color:var(--ink);letter-spacing:-.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.lp-kpi:first-child b{color:var(--brand)}',
    '.lp-kpi span{display:block;font-size:11.5px;color:var(--ink3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.lp-kpi span.lp-ok{color:var(--ok)}.lp-kpi span.lp-bad{color:var(--bad)}',
    '.lp-alert{font-size:13px;border-radius:8px;padding:9px 12px;background:#fff7ed;color:var(--warn);border:1px solid #fed7aa}',
    '.lp-alert.lp-err{background:#fff1f2;color:var(--bad);border-color:#fecdd3}',
    '.lp-sec{display:flex;justify-content:space-between;align-items:baseline;gap:10px;font-size:12.5px;font-weight:600;color:var(--ink);margin-bottom:8px}',
    '.lp-sec span{font-weight:400;color:var(--ink3);font-family:var(--mono);font-size:12px;font-variant-numeric:tabular-nums;text-align:right}',
    '.lp-bar{display:flex;height:26px;border-radius:6px;overflow:hidden;background:repeating-linear-gradient(135deg,var(--line2) 0 6px,var(--white) 6px 12px);border:1px solid var(--line)}',
    '.lp-bar i{display:block;height:100%;transition:width .35s ease;min-width:0}',
    '.lp-c-w{background:var(--brand)}.lp-c-kv{background:var(--brand2);opacity:.55}.lp-c-act{background:var(--ink4)}',
    '.lp-leg{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:8px;font-size:12px;color:var(--ink3)}',
    '.lp-leg span{display:inline-flex;align-items:center;gap:6px}',
    '.lp-leg em{font-style:normal;font-family:var(--mono);color:var(--ink);font-variant-numeric:tabular-nums}',
    '.lp-leg i{width:10px;height:10px;border-radius:2px;display:inline-block}',
    '.lp-leg i.lp-c-free{background:repeating-linear-gradient(135deg,var(--line) 0 3px,var(--white) 3px 6px);border:1px solid var(--line)}',
    '.lp-chart svg{display:block;width:100%;height:auto}',
    '.lp-chart .lp-grid{stroke:var(--line2)}',
    '.lp-chart text{font-family:var(--mono);font-size:10px;fill:var(--ink4)}',
    '.lp-chart .lp-agg{fill:none;stroke:var(--brand);stroke-width:2}',
    '.lp-chart .lp-usr{fill:none;stroke:var(--ink3);stroke-width:1.5;stroke-dasharray:4 3}',
    '.lp-chart .lp-area{fill:var(--brand);opacity:.07}',
    '.lp-chart .lp-op{stroke:var(--brand);stroke-dasharray:2 3}',
    '.lp-chart .lp-dot{fill:var(--white);stroke:var(--brand);stroke-width:2}',
    '.lp-chart .lp-dot2{fill:var(--white);stroke:var(--ink3);stroke-width:1.5}',
    '.lp-chart .lp-oplab{fill:var(--brand);font-weight:500}',
    '.lp-tbl{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0;border-top:1px solid var(--line)}',
    '.lp-tbl div{padding:8px 0;border-bottom:1px solid var(--line2);min-width:0;padding-right:10px}',
    '.lp-tbl dt{font-size:11.5px;color:var(--ink3)}',
    '.lp-tbl dd{margin:0;font-family:var(--mono);font-size:13px;color:var(--ink);font-variant-numeric:tabular-nums;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.lp-how{font-size:13px;color:var(--ink2);border-top:1px solid var(--line);padding-top:12px}',
    '.lp-how summary{cursor:pointer;font-weight:600;color:var(--ink);font-size:13px}',
    '.lp-how ul{margin:10px 0 0;padding-left:18px;display:grid;gap:6px}',
    '.lp-how code{font-family:var(--mono);font-size:12px;color:var(--ink);background:var(--line2);padding:1px 4px;border-radius:4px;overflow-wrap:anywhere}',
    '.lp-note{font-size:12px;color:var(--ink3);margin-top:8px}',
    '@media (max-width:1040px){.lp-kpis{grid-template-columns:repeat(3,minmax(0,1fr))}.lp-kpi:nth-child(4){border-left:0}.lp-kpi:nth-child(n+4){border-top:1px solid var(--line)}}',
    '@media (max-width:860px){.lp{grid-template-columns:minmax(0,1fr)}.lp-ctl{border-right:0;border-bottom:1px solid var(--line)}}',
    '@media (max-width:520px){.lp-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.lp-kpi{border-left:1px solid var(--line)!important;border-top:1px solid var(--line)}.lp-kpi:nth-child(odd){border-left:0!important}.lp-kpi:nth-child(-n+2){border-top:0}.lp-kpi:first-child{grid-column:1/-1;border-left:0!important}.lp-kpi:nth-child(2){border-left:0!important;border-top:1px solid var(--line)}.lp-kpi:nth-child(3){border-top:1px solid var(--line)}.lp-tbl{grid-template-columns:repeat(2,minmax(0,1fr))}.lp-out{padding:16px}.lp-ctl{padding:16px}}',
    '@media (prefers-reduced-motion:reduce){.lp-bar i{transition:none}}'
  ].join('\n');

  function injectCSS() {
    if (document.getElementById('lab-planner-css')) return;
    var s = document.createElement('style'); s.id = 'lab-planner-css'; s.textContent = CSS;
    document.head.appendChild(s);
  }

  function fmtN(v) {
    if (!isFinite(v)) return '—';
    if (v >= 100) return Math.round(v).toLocaleString('en-GB');
    if (v >= 10) return v.toFixed(1);
    return v.toFixed(2);
  }
  function fmtTok(n) { return n >= 1024 ? (n / 1024) + 'k' : String(n); }
  function fmtGB(b) { var g = b / 1e9; return g >= 100 ? Math.round(g) + ' GB' : g >= 10 ? g.toFixed(1) + ' GB' : g >= 1 ? g.toFixed(2) + ' GB' : Math.round(g * 1000) + ' MB'; }
  function fmtMs(s) { return s >= 1 ? s.toFixed(2) + ' s' : Math.round(s * 1000) + ' ms'; }
  function fmtUSD(v) { return v >= 1000 ? '$' + Math.round(v).toLocaleString('en-GB') : v >= 10 ? '$' + v.toFixed(0) : '$' + v.toFixed(2); }
  function byId(arr, id) { for (var i = 0; i < arr.length; i++) if (arr[i].id === id) return arr[i]; return arr[0]; }

  /* ---------- the model ---------- */
  function kvBytesPerToken(m, kvb) {
    var perLayer = m.kvPerLayer ? m.kvPerLayer : 2 * m.kvh * m.hd;
    return m.layers * perLayer * kvb;
  }
  // weight bytes a decode step reads: dense = all; MoE = the experts the batch touches
  function weightsRead(m, wb, b) {
    if (m.active >= m.total) return m.total * 1e9 * wb;
    var p = m.active / m.total;
    return m.total * 1e9 * wb * (1 - Math.pow(1 - p, b));
  }
  function flops(g, wname) { return (wname !== 'bf16' && g.fp8 ? g.fp8 : g.bf16) * 1e12; }

  // per-replica figures at batch b, tensor-parallel tp
  function perf(s, tp, b) {
    var m = s.m, g = s.g, wb = s.wb, kvTok = s.kvTok;
    var ctxAvg = s.inTok + s.outTok / 2;
    var bw = g.bw * 1e12 * BW_EFF * tp;
    var F = flops(g, s.wname) * tp;
    var comm = tp > 1 ? 1 + 0.06 * Math.log2(tp) : 1;
    var tMem = (weightsRead(m, wb, b) + b * ctxAvg * kvTok) / bw;
    var tCmp = 2 * m.active * 1e9 * b / (F * FLOP_EFF);
    var tStep = Math.max(tMem, tCmp) * comm;
    var r = 1 / tStep;                                  // tok/s per stream, decode only
    var tPre = 2 * m.active * 1e9 / (F * PREFILL_EFF) * comm; // s per prompt token
    var k = b * s.inTok * tPre / s.outTok;              // prefill share couples to decode rate
    var rEff = r / (1 + k * r);
    var ttft = s.inTok * tPre + tStep;
    return { tStep: tStep, user: rEff, agg: rEff * b, ttft: ttft, memBound: tMem >= tCmp };
  }

  function plan(s) {
    var g = s.g, m = s.m;
    var memB = g.mem * 1e9;
    var act = (0.08 * g.mem + 1.5) * 1e9;               // activations, CUDA graphs, allocator slack
    var weights = m.total * 1e9 * s.wb;
    var perReq = s.kvTok * (s.inTok + s.outTok);
    var opts = [];
    for (var i = 0; i < TPS.length; i++) {
      var tp = TPS[i];
      var wPer = weights / tp;
      var kvCap = (memB - act - wPer) * tp;
      if (kvCap <= 0) continue;
      var maxB = Math.min(MAX_BATCH, Math.floor(kvCap / perReq));
      if (maxB < 1) continue;
      var replicas = Math.ceil(s.users / maxB);
      var b = Math.ceil(s.users / replicas);
      var p = perf(s, tp, b);
      opts.push({ tp: tp, replicas: replicas, gpus: tp * replicas, b: b, maxB: maxB, p: p, wPer: wPer, act: act, kvPer: b * perReq / tp, kvCap: kvCap, sloOk: p.ttft * 1000 <= s.slo });
    }
    if (!opts.length) return { fail: true, weights: weights, act: act, memB: memB };
    var ok = opts.filter(function (o) { return o.sloOk; });
    var best;
    if (ok.length) {
      best = ok.reduce(function (a, o) { return o.gpus < a.gpus || (o.gpus === a.gpus && o.tp < a.tp) ? o : a; });
    } else {
      best = opts.reduce(function (a, o) { return o.p.ttft < a.p.ttft ? o : a; });
    }
    best.memB = memB; best.perReq = perReq; best.weights = weights;
    return best;
  }

  /* ---------- rendering ---------- */
  function seg(name, opts, sel, label) {
    return '<div class="lp-f"><span class="lp-lab" id="' + name + '-l">' + label + '</span><div class="lp-seg" role="group" aria-labelledby="' + name + '-l" data-seg="' + name + '">' +
      opts.map(function (o) { return '<button type="button" data-v="' + o[0] + '" aria-pressed="' + (o[0] === sel) + '">' + o[0] + '</button>'; }).join('') + '</div></div>';
  }
  function range(name, label, arr, idx, fmt) {
    return '<div class="lp-f"><label for="' + name + '">' + label + ' <output data-o="' + name + '">' + fmt(arr[idx]) + '</output></label>' +
      '<input type="range" id="' + name + '" data-r="' + name + '" min="0" max="' + (arr.length - 1) + '" step="1" value="' + idx + '"></div>';
  }

  var uid = 0;
  function mount(root) {
    if (root.__lp) return; root.__lp = true;
    var u = 'lp' + (++uid) + '-';
    var st = { model: 'qwen32', w: 'fp8', kv: 'fp8', gpu: 'h100', price: 2.5, users: 6, inp: 3, out: 2, slo: 2 };
    root.innerHTML =
      '<div class="lp">' +
      '<div class="lp-ctl">' +
        '<div class="lp-hd"><i></i>Capacity planner</div>' +
        '<div class="lp-f"><label for="' + u + 'm">Model</label><select class="lp-sel" id="' + u + 'm" data-k="model">' +
          MODELS.map(function (m) { return '<option value="' + m.id + '"' + (m.id === st.model ? ' selected' : '') + '>' + m.name + '</option>'; }).join('') + '</select></div>' +
        '<div class="lp-row2">' + seg(u + 'w', WPREC, st.w, 'Weights') + seg(u + 'kv', KVPREC, st.kv, 'KV cache') + '</div>' +
        '<div class="lp-f"><label for="' + u + 'g">GPU</label><select class="lp-sel" id="' + u + 'g" data-k="gpu">' +
          GPUS.map(function (g) { return '<option value="' + g.id + '"' + (g.id === st.gpu ? ' selected' : '') + '>' + g.name + '</option>'; }).join('') + '</select></div>' +
        '<div class="lp-f lp-inl"><label for="' + u + 'p">Price per GPU-hour</label><span class="lp-usd"><input class="lp-num" id="' + u + 'p" data-k="price" type="number" min="0" step="0.05" value="2.50" inputmode="decimal"></span></div>' +
        range(u + 'users', 'Concurrent requests', USERS, st.users, String) +
        range(u + 'inp', 'Prompt tokens', PROMPT, st.inp, fmtTok) +
        range(u + 'out', 'Output tokens', OUTPUT, st.out, String) +
        range(u + 'slo', 'TTFT target', SLO, st.slo, function (v) { return v + ' ms'; }) +
      '</div>' +
      '<div class="lp-out" aria-live="polite">' +
        '<div class="lp-kpis">' +
          '<div class="lp-kpi"><small>GPUs needed</small><b data-x="gpus">—</b><span data-x="layout">—</span></div>' +
          '<div class="lp-kpi"><small>Per-user decode</small><b data-x="user">—</b><span>tok/s per stream</span></div>' +
          '<div class="lp-kpi"><small>Aggregate output</small><b data-x="agg">—</b><span>tok/s, all GPUs</span></div>' +
          '<div class="lp-kpi"><small>Time to first token</small><b data-x="ttft">—</b><span data-x="slo">—</span></div>' +
          '<div class="lp-kpi"><small>Per 1M output tokens</small><b data-x="cpm">—</b><span data-x="month">—</span></div>' +
        '</div>' +
        '<div data-x="alert"></div>' +
        '<div><div class="lp-sec">Memory per GPU<span data-x="memcap">—</span></div>' +
          '<div class="lp-bar" role="img" data-x="bar"><i class="lp-c-w"></i><i class="lp-c-kv"></i><i class="lp-c-act"></i></div>' +
          '<div class="lp-leg"><span><i class="lp-c-w"></i>Weights <em data-x="lw">—</em></span><span><i class="lp-c-kv"></i>KV cache <em data-x="lkv">—</em></span><span><i class="lp-c-act"></i>Activations and runtime <em data-x="lact">—</em></span><span><i class="lp-c-free"></i>Free <em data-x="lfree">—</em></span></div></div>' +
        '<div class="lp-chart"><div class="lp-sec">Throughput against batch size, one replica<span data-x="regime">—</span></div><div data-x="chart"></div>' +
          '<div class="lp-leg"><span><i class="lp-c-w"></i>Aggregate tok/s (left axis)</span><span><i style="background:none;border-top:2px dashed var(--ink3);height:0;width:14px"></i>Per-user tok/s (right axis)</span></div></div>' +
        '<dl class="lp-tbl" style="margin:0">' +
          '<div><dt>Tensor parallel × replicas</dt><dd data-x="tp">—</dd></div>' +
          '<div><dt>Batch per replica</dt><dd data-x="batch">—</dd></div>' +
          '<div><dt>Requests per second</dt><dd data-x="rps">—</dd></div>' +
          '<div><dt>KV cache per request</dt><dd data-x="kvreq">—</dd></div>' +
          '<div><dt>KV cache, all requests</dt><dd data-x="kvall">—</dd></div>' +
          '<div><dt>Decode step</dt><dd data-x="step">—</dd></div>' +
        '</dl>' +
        '<details class="lp-how"><summary>How this is calculated</summary><ul>' +
          '<li>Weights take <code>params × bytes</code> (bf16 2, fp8 1, int4 0.56 with group scales), split across the tensor-parallel group. Each GPU also holds <code>8% of memory + 1.5 GB</code> for activations, CUDA graphs and allocator slack; what is left holds the KV cache.</li>' +
          '<li>KV cache per token is <code>2 × layers × KV heads × head dim × bytes</code> (DeepSeek-V3 caches a 576-wide latent per layer). Each request reserves room for prompt plus output.</li>' +
          '<li>A decode step is memory bound: <code>(weight bytes read + batch × avg context × KV bytes) ÷ (bandwidth × 0.75)</code>, with a compute floor of <code>2 × active params × batch ÷ (FLOPS × 0.5)</code>. For MoE models, the weight bytes read grow with the experts the batch touches.</li>' +
          '<li>Prefill is compute bound at 60% of dense FLOPS (fp8 rate for fp8 and int4 weights where the GPU has it). Prefill time is taken out of decode time, so long prompts lower per-user speed. TTFT is one prompt\'s prefill plus one decode step, with no queueing.</li>' +
          '<li>Tensor parallelism adds <code>6% × log2(TP)</code> for communication. The planner picks the layout that meets the TTFT target with the fewest GPUs.</li>' +
          '<li>Not modelled: prefix caching, speculative decoding, chunked-prefill scheduling, quantisation accuracy, queueing under bursty traffic. That is what an Optimize run measures.</li>' +
        '</ul></details>' +
        '<p class="lp-note" style="margin:0">A first-order estimate from public hardware specs. Optimize measures the real number on your model, traffic and hardware.</p>' +
      '</div></div>';

    var $ = function (sel) { return root.querySelector(sel); };
    var X = {}; [].forEach.call(root.querySelectorAll('[data-x]'), function (e) { X[e.getAttribute('data-x')] = e; });
    var barI = X.bar.querySelectorAll('i');

    root.addEventListener('click', function (e) {
      var b = e.target.closest('.lp-seg button'); if (!b || !root.contains(b)) return;
      var grp = b.parentNode, name = grp.getAttribute('data-seg');
      [].forEach.call(grp.children, function (c) { c.setAttribute('aria-pressed', c === b ? 'true' : 'false'); });
      if (name === u + 'w') st.w = b.getAttribute('data-v'); else st.kv = b.getAttribute('data-v');
      update();
    });
    root.addEventListener('input', function (e) {
      var t = e.target, k = t.getAttribute('data-k'), r = t.getAttribute('data-r');
      if (k === 'model') st.model = t.value;
      else if (k === 'gpu') { st.gpu = t.value; st.price = byId(GPUS, st.gpu).price; $('#' + u + 'p').value = st.price.toFixed(2); }
      else if (k === 'price') { var v = parseFloat(t.value); st.price = isFinite(v) && v >= 0 ? v : 0; }
      else if (r) { st[r.slice(u.length)] = +t.value; }
      update();
    });

    function update() {
      [['users', USERS, String], ['inp', PROMPT, fmtTok], ['out', OUTPUT, String], ['slo', SLO, function (v) { return v + ' ms'; }]].forEach(function (a) {
        var inp = $('#' + u + a[0]); inp.style.setProperty('--p', (st[a[0]] / (a[1].length - 1) * 100) + '%');
        root.querySelector('[data-o="' + u + a[0] + '"]').textContent = a[2](a[1][st[a[0]]]);
      });
      var m = byId(MODELS, st.model), g = byId(GPUS, st.gpu);
      var wb = WPREC.filter(function (x) { return x[0] === st.w; })[0][1];
      var kvb = KVPREC.filter(function (x) { return x[0] === st.kv; })[0][1];
      var s = { m: m, g: g, wb: wb, wname: st.w, kvTok: kvBytesPerToken(m, kvb), users: USERS[st.users], inTok: PROMPT[st.inp], outTok: OUTPUT[st.out], slo: SLO[st.slo] };
      var r = plan(s);
      var alert = '';
      if (r.fail) {
        X.gpus.textContent = '> 8'; X.layout.textContent = 'does not fit one node';
        ['user', 'agg', 'ttft', 'cpm', 'tp', 'batch', 'rps', 'kvall', 'step'].forEach(function (k) { X[k].textContent = '—'; });
        X.slo.textContent = ''; X.month.textContent = ''; X.slo.className = '';
        X.kvreq.textContent = fmtGB(s.kvTok * (s.inTok + s.outTok));
        X.alert.innerHTML = '<div class="lp-alert lp-err">' + fmtGB(r.weights) + ' of weights plus the KV cache don\'t fit on 8 × ' + g.name + '. Choose lower-precision weights, a larger GPU, or shorter contexts.</div>';
        var wPer8 = r.weights / 8;
        setBar(Math.min(wPer8, r.memB), 0, Math.min(r.act, Math.max(0, r.memB - wPer8)), r.memB, 8);
        X.lw.textContent = fmtGB(wPer8) + ' needed';
        X.chart.innerHTML = ''; X.regime.textContent = '';
        return;
      }
      var p = r.p;
      X.gpus.textContent = r.gpus;
      X.layout.textContent = r.replicas > 1 ? r.replicas + ' replicas × TP' + r.tp : 'TP' + r.tp + ', one replica';
      X.user.textContent = fmtN(p.user);
      X.agg.textContent = fmtN(p.agg * r.replicas);
      X.ttft.textContent = fmtMs(p.ttft);
      X.slo.textContent = r.sloOk ? 'within ' + s.slo + ' ms' : 'misses ' + s.slo + ' ms';
      X.slo.className = r.sloOk ? 'lp-ok' : 'lp-bad';
      var hourly = r.gpus * st.price;
      var cpm = hourly / (p.agg * r.replicas * 3600) * 1e6;
      X.cpm.textContent = st.price > 0 ? fmtUSD(cpm) : '—';
      X.month.textContent = st.price > 0 ? fmtUSD(hourly * 730) + ' a month' : 'set a GPU price';
      X.tp.textContent = 'TP' + r.tp + ' × ' + r.replicas;
      X.batch.textContent = r.b + ' (max ' + r.maxB + ')';
      X.rps.textContent = fmtN(p.agg * r.replicas / s.outTok);
      X.kvreq.textContent = fmtGB(r.perReq);
      X.kvall.textContent = fmtGB(r.perReq * s.users);
      X.step.textContent = (p.tStep * 1000).toFixed(1) + ' ms';
      if (!r.sloOk) alert = '<div class="lp-alert">No layout up to TP8 prefills a ' + fmtTok(s.inTok) + '-token prompt within ' + s.slo + ' ms on ' + g.name + '. Shown: the fastest layout. Prefix caching or a faster GPU would close the gap.</div>';
      X.alert.innerHTML = alert;
      setBar(r.wPer, r.kvPer, r.act, r.memB, r.tp);
      X.regime.textContent = p.memBound ? 'memory-bandwidth bound' : 'compute bound';
      chart(s, r);
    }

    function setBar(w, kv, act, mem, tp) {
      var free = Math.max(0, mem - w - kv - act);
      var pct = function (v) { return (Math.max(0, v) / mem * 100).toFixed(2) + '%'; };
      barI[0].style.width = pct(w); barI[1].style.width = pct(kv); barI[2].style.width = pct(act);
      X.lw.textContent = fmtGB(w); X.lkv.textContent = fmtGB(kv); X.lact.textContent = fmtGB(act); X.lfree.textContent = fmtGB(free);
      X.memcap.textContent = fmtGB(mem) + ' per GPU' + (tp > 1 ? ', TP' + tp : '');
      X.bar.setAttribute('aria-label', 'Weights ' + fmtGB(w) + ', KV cache ' + fmtGB(kv) + ', activations ' + fmtGB(act) + ', free ' + fmtGB(free) + ' of ' + fmtGB(mem));
    }

    function nice(v) { var e = Math.pow(10, Math.floor(Math.log10(v))), f = v / e; return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * e; }
    function chart(s, r) {
      var W = Math.round(Math.max(300, Math.min(640, X.chart.clientWidth || 600))), H = Math.round(Math.max(180, W * 0.34)), L = 40, R = 34, T = 12, B = 26;
      var maxB = Math.max(2, r.maxB), n = 48, pts = [];
      for (var i = 0; i <= n; i++) { var b = Math.max(1, Math.round(Math.exp(Math.log(maxB) * i / n))); if (!pts.length || pts[pts.length - 1].b !== b) pts.push({ b: b, p: perf(s, r.tp, b) }); }
      var aMax = nice(Math.max.apply(null, pts.map(function (q) { return q.p.agg; })) * 1.08);
      var uMax = nice(Math.max.apply(null, pts.map(function (q) { return q.p.user; })) * 1.08);
      var x = function (b) { return L + Math.log(b) / Math.log(maxB) * (W - L - R); };
      var ya = function (v) { return T + (1 - v / aMax) * (H - T - B); };
      var yu = function (v) { return T + (1 - v / uMax) * (H - T - B); };
      var o = ['<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Aggregate and per-user tokens per second against batch size">'];
      for (var k = 0; k <= 4; k++) {
        var yy = T + k / 4 * (H - T - B);
        o.push('<line class="lp-grid" x1="' + L + '" x2="' + (W - R) + '" y1="' + yy.toFixed(1) + '" y2="' + yy.toFixed(1) + '"/>');
        o.push('<text x="' + (L - 6) + '" y="' + (yy + 3).toFixed(1) + '" text-anchor="end">' + short(aMax * (1 - k / 4)) + '</text>');
        o.push('<text x="' + (W - R + 6) + '" y="' + (yy + 3).toFixed(1) + '">' + short(uMax * (1 - k / 4)) + '</text>');
      }
      for (var t = 1; t <= maxB; t *= 4) o.push('<text x="' + x(t).toFixed(1) + '" y="' + (H - 8) + '" text-anchor="middle">' + t + '</text>');
      o.push('<text x="' + (W - R) + '" y="' + (H - 8) + '" text-anchor="end">batch</text>');
      var da = pts.map(function (q, j) { return (j ? 'L' : 'M') + x(q.b).toFixed(1) + ' ' + ya(q.p.agg).toFixed(1); }).join('');
      var du = pts.map(function (q, j) { return (j ? 'L' : 'M') + x(q.b).toFixed(1) + ' ' + yu(q.p.user).toFixed(1); }).join('');
      o.push('<path class="lp-area" d="' + da + 'L' + x(pts[pts.length - 1].b).toFixed(1) + ' ' + (H - B) + 'L' + x(1).toFixed(1) + ' ' + (H - B) + 'Z"/>');
      o.push('<path class="lp-agg" d="' + da + '"/><path class="lp-usr" d="' + du + '"/>');
      var ob = Math.min(r.b, maxB), ox = x(ob), op = r.p;
      o.push('<line class="lp-op" x1="' + ox.toFixed(1) + '" x2="' + ox.toFixed(1) + '" y1="' + T + '" y2="' + (H - B) + '"/>');
      o.push('<circle class="lp-dot" cx="' + ox.toFixed(1) + '" cy="' + ya(op.agg).toFixed(1) + '" r="4"/><circle class="lp-dot2" cx="' + ox.toFixed(1) + '" cy="' + yu(op.user).toFixed(1) + '" r="3.5"/>');
      var right = ox > W - R - 110;
      o.push('<text class="lp-oplab" x="' + (ox + (right ? -6 : 6)).toFixed(1) + '" y="' + (T + 10) + '" text-anchor="' + (right ? 'end' : 'start') + '">batch ' + r.b + '</text>');
      o.push('</svg>');
      X.chart.innerHTML = o.join('');
    }
    function short(v) { return v >= 1e4 ? Math.round(v / 1e3) + 'k' : v >= 1e3 ? (v / 1e3).toFixed(1).replace(/\.0$/, '') + 'k' : String(Math.round(v)); }

    update();
    if ('ResizeObserver' in window) {
      var lastW = 0;
      new ResizeObserver(function () { var w = X.chart.clientWidth; if (Math.abs(w - lastW) > 24) { lastW = w; update(); } }).observe(X.chart);
    }
  }

  function init() { injectCSS(); [].forEach.call(document.querySelectorAll('[data-lab="planner"]'), mount); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
