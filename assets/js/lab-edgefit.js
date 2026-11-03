/* Edge fit: which model fits a device's memory, how fast it decodes, and whether an
   on-device QLoRA fine-tune fits too. Renders into every [data-lab="edgefit"].
   Device specifications and the hardware card come from assets/js/hw.js (window.VO_HW). */
(function () {
  'use strict';

  var HW = window.VO_HW;
  var DEV_ORDER = ['orin_nano', 'orin_nx', 'agx_orin', 'pi5', 'iphone16', 'pixel9', 's25u', 'mba'];
  var LADDER = [
    // Qwen2.5-class shapes: params (B), layers, KV heads, head dim, hidden, MLP width
    { id: '0.5', label: '0.5B', p: 0.49, L: 24, kvh: 2, hd: 64,  h: 896,  I: 4864 },
    { id: '1.5', label: '1.5B', p: 1.54, L: 28, kvh: 2, hd: 128, h: 1536, I: 8960 },
    { id: '3',   label: '3B',   p: 3.09, L: 36, kvh: 2, hd: 128, h: 2048, I: 11008 },
    { id: '7',   label: '7B',   p: 7.62, L: 28, kvh: 4, hd: 128, h: 3584, I: 18944 },
    { id: '14',  label: '14B',  p: 14.7, L: 48, kvh: 8, hd: 128, h: 5120, I: 13824 },
    { id: '32',  label: '32B',  p: 32.8, L: 64, kvh: 8, hd: 128, h: 5120, I: 27648 }
  ];
  var PREC = [['fp16', 'fp16'], ['int8', 'int8'], ['int4', 'int4'], ['int4p', 'int4 −2L']];
  var KVP = [['fp16', 2], ['int8', 1]];
  var CTX = [1024, 2048, 4096, 8192, 16384, 32768];
  var VISION_P = 0.6, IMAGE_TOK = 1024, VOCAB = 152064, TRAIN_SEQ = 512, RANK = 16;

  var CSS = [
    '.le{font-family:var(--font);color:var(--ink2);background:var(--white);border:1px solid var(--line);border-radius:12px;box-shadow:0 1px 2px rgba(16,24,40,.05);display:grid;grid-template-columns:320px minmax(0,1fr);overflow:hidden;text-align:left;line-height:1.45;font-size:14px}',
    '.le *{box-sizing:border-box}',
    '.le-ctl{padding:18px;border-right:1px solid var(--line);background:#fbfcfe;display:flex;flex-direction:column;gap:14px;min-width:0}',
    '.le-hd{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3)}',
    '.le-hd i{width:7px;height:7px;border-radius:50%;background:var(--brand)}',
    '.le-f{display:flex;flex-direction:column;gap:6px;min-width:0}',
    '.le-f>label,.le-f>.le-lab{font-size:12.5px;font-weight:600;color:var(--ink);display:flex;justify-content:space-between;gap:8px}',
    '.le-f output{font-family:var(--mono);font-weight:500;color:var(--brand);font-variant-numeric:tabular-nums}',
    '.le-sel{width:100%;font:inherit;font-size:13.5px;color:var(--ink);background:var(--white);border:1px solid var(--line);border-radius:8px;padding:8px 28px 8px 10px;min-width:0;appearance:none;-webkit-appearance:none;background-image:linear-gradient(45deg,transparent 50%,var(--ink3) 50%),linear-gradient(135deg,var(--ink3) 50%,transparent 50%);background-position:calc(100% - 15px) 52%,calc(100% - 10px) 52%;background-size:5px 5px;background-repeat:no-repeat}',
    '.le-sel:hover{border-color:var(--brand200)}',
    '.le-seg{display:flex;border:1px solid var(--line);border-radius:8px;background:var(--white);padding:2px;gap:2px}',
    '.le-seg button{flex:1;font:inherit;font-size:12px;font-weight:600;font-family:var(--mono);color:var(--ink3);background:none;border:0;border-radius:6px;padding:6px 2px;cursor:pointer;white-space:nowrap}',
    '.le-seg button:hover{color:var(--ink)}',
    '.le-seg button[aria-pressed="true"]{background:var(--brand);color:#fff}',
    '.le-lad{display:flex;flex-direction:column;border:1px solid var(--line);border-radius:8px;background:var(--white);overflow:hidden}',
    '.le-lad button{display:grid;grid-template-columns:44px minmax(0,1fr) auto;align-items:center;gap:8px;font:inherit;text-align:left;background:none;border:0;border-top:1px solid var(--line2);padding:7px 10px;cursor:pointer;color:var(--ink2)}',
    '.le-lad button:first-child{border-top:0}',
    '.le-lad button:hover{background:var(--line2)}',
    '.le-lad b{font-family:var(--mono);font-weight:500;color:var(--ink);font-size:13px}',
    '.le-lad span{font-family:var(--mono);font-size:11.5px;color:var(--ink3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-variant-numeric:tabular-nums}',
    '.le-lad em{font-style:normal;font-size:11px;font-weight:600;padding:1px 7px;border-radius:10px;white-space:nowrap}',
    '.le-lad em.le-y{color:var(--ok);background:#ecfdf5}.le-lad em.le-n{color:var(--ink4);background:var(--line2)}',
    '.le-lad em.le-best{color:#fff;background:var(--ok)}',
    '.le-lad button[aria-pressed="true"]{background:var(--brand50);box-shadow:inset 3px 0 0 var(--brand)}',
    '.le-lad button[aria-pressed="true"] b{color:var(--brand)}',
    '.le-chk{display:flex;align-items:flex-start;gap:9px;font-size:13px;color:var(--ink2);cursor:pointer}',
    '.le-chk input{appearance:none;-webkit-appearance:none;flex:none;width:16px;height:16px;border:1.5px solid var(--ink4);border-radius:4px;margin:2px 0 0;background:var(--white);display:grid;place-content:center;cursor:pointer}',
    '.le-chk input:checked{background:var(--brand);border-color:var(--brand)}',
    '.le-chk input:checked::after{content:"";width:8px;height:4px;border:2px solid #fff;border-top:0;border-right:0;transform:rotate(-45deg) translate(1px,-1px)}',
    '.le-chk b{display:block;color:var(--ink);font-weight:600;font-size:12.5px}',
    '.le input[type=range]{-webkit-appearance:none;appearance:none;width:100%;height:20px;background:none;margin:0;cursor:pointer}',
    '.le input[type=range]::-webkit-slider-runnable-track{height:4px;border-radius:2px;background:linear-gradient(var(--brand),var(--brand)) 0/var(--p,50%) 100% no-repeat,var(--line)}',
    '.le input[type=range]::-moz-range-track{height:4px;border-radius:2px;background:var(--line)}',
    '.le input[type=range]::-moz-range-progress{height:4px;border-radius:2px;background:var(--brand)}',
    '.le input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:16px;height:16px;border-radius:50%;background:var(--white);border:2px solid var(--brand);margin-top:-6px;box-shadow:0 1px 2px rgba(16,24,40,.15)}',
    '.le input[type=range]::-moz-range-thumb{width:12px;height:12px;border-radius:50%;background:var(--white);border:2px solid var(--brand)}',
    '.le button:focus-visible,.le select:focus-visible,.le input:focus-visible,.le summary:focus-visible{outline:2px solid var(--brand);outline-offset:2px}',
    '.le-out{padding:18px 20px;display:flex;flex-direction:column;gap:18px;min-width:0}',
    '.le-mid{display:grid;grid-template-columns:276px minmax(0,1fr);gap:16px;align-items:start}',
    '.le-r{display:flex;flex-direction:column;gap:18px;min-width:0}',
    '.le-card .hwc-slot .le-sec{margin-bottom:6px}',
    '.le-card .le-leg{font-size:11.5px;gap:4px 12px}',
    '.le-bb{display:flex;height:22px;border-radius:6px;overflow:hidden;border:1px solid var(--line);background:var(--line2)}',
    '.le-bb i{display:block;height:100%;transition:width .35s ease;min-width:0}',
    '.le-math{display:grid;grid-template-columns:auto minmax(0,1fr);column-gap:12px;row-gap:3px;font-size:12px;color:var(--ink3);margin-top:8px}',
    '.le-math dd{margin:0;font-family:var(--mono);color:var(--ink);font-variant-numeric:tabular-nums;overflow-wrap:anywhere}',
    '.le-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--line);border-radius:10px;overflow:hidden}',
    '.le-kpi{padding:10px 12px;border-left:1px solid var(--line);min-width:0}',
    '.le-kpi:first-child{border-left:0}',
    '.le-kpi small{display:block;font-size:11.5px;color:var(--ink3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.le-kpi b{display:block;font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:20px;font-weight:500;color:var(--ink);letter-spacing:-.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.le-kpi span{display:block;font-size:11.5px;color:var(--ink3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.le-kpi.le-ok{background:#ecfdf5}.le-kpi.le-ok b{color:var(--ok)}',
    '.le-kpi.le-no{background:#fff1f2}.le-kpi.le-no b{color:var(--bad)}',
    '.le-use{font:inherit;font-size:12px;font-weight:600;color:var(--brand);background:none;border:0;padding:0;cursor:pointer;text-decoration:underline;text-underline-offset:2px}',
    '.le-sec{display:flex;justify-content:space-between;align-items:baseline;gap:10px;font-size:12.5px;font-weight:600;color:var(--ink);margin-bottom:8px}',
    '.le-sec span{font-weight:400;color:var(--ink3);font-family:var(--mono);font-size:12px;font-variant-numeric:tabular-nums;text-align:right}',
    '.le-bw{position:relative;padding-top:16px}',
    '.le-bar{position:relative;display:flex;height:28px;border-radius:6px;overflow:hidden;background:var(--white);border:1px solid var(--line)}',
    '.le-bar i{display:block;height:100%;transition:width .35s ease;min-width:0}',
    '.le-c-w{background:var(--brand)}.le-c-v{background:#8b5cf6}.le-c-kv{background:var(--brand2);opacity:.55}.le-c-rt{background:var(--ink4)}',
    '.le-c-os{background:repeating-linear-gradient(135deg,#cbd5e1 0 4px,#e2e8f0 4px 8px)}.le-c-tr{background:#0d9488}.le-c-over{background:repeating-linear-gradient(135deg,#fecdd3 0 5px,#fff1f2 5px 10px)}',
    '.le-lim{position:absolute;top:0;bottom:0;width:0;border-left:2px solid var(--ink);transition:left .35s ease;pointer-events:none}',
    '.le-lim span{position:absolute;top:-1px;transform:translateX(-50%);font-family:var(--mono);font-size:10.5px;color:var(--ink);white-space:nowrap;background:var(--white);padding:0 3px}',
    '.le-lim.le-r span{transform:translateX(-100%)}.le-lim.le-l span{transform:none}',
    '.le-leg{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:8px;font-size:12px;color:var(--ink3)}',
    '.le-leg span{display:inline-flex;align-items:center;gap:6px}',
    '.le-leg em{font-style:normal;font-family:var(--mono);color:var(--ink);font-variant-numeric:tabular-nums}',
    '.le-leg i{width:10px;height:10px;border-radius:2px;display:inline-block}',
    '.le-leg [hidden]{display:none}',
    '.le-msg{font-size:13px;border-radius:8px;padding:9px 12px;background:var(--brand50);color:var(--brandD);border:1px solid var(--brand100)}',
    '.le-msg.le-bad{background:#fff1f2;color:var(--bad);border-color:#fecdd3}.le-msg.le-good{background:#ecfdf5;color:#047857;border-color:#a7f3d0}',
    '.le-how{font-size:13px;color:var(--ink2);border-top:1px solid var(--line);padding-top:12px}',
    '.le-how summary{cursor:pointer;font-weight:600;color:var(--ink);font-size:13px}',
    '.le-how ul{margin:10px 0 0;padding-left:18px;display:grid;gap:6px}',
    '.le-how code{font-family:var(--mono);font-size:12px;color:var(--ink);background:var(--line2);padding:1px 4px;border-radius:4px;overflow-wrap:anywhere}',
    '.le-note{font-size:12px;color:var(--ink3);margin:0}',
    '@media (max-width:1100px){.le-mid{grid-template-columns:minmax(0,1fr)}.le-card .hwc{grid-template-columns:minmax(150px,220px) minmax(0,1fr)}.le-card .hwc-ph{aspect-ratio:auto;min-height:100%}}',
    '@media (max-width:1040px){.le-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.le-kpi:nth-child(3){border-left:0}.le-kpi:nth-child(n+3){border-top:1px solid var(--line)}}',
    '@media (max-width:860px){.le{grid-template-columns:minmax(0,1fr)}.le-ctl{border-right:0;border-bottom:1px solid var(--line)}}',
    '@media (max-width:520px){.le-out,.le-ctl{padding:16px}.le-kpi b{font-size:18px}.le-card .hwc{grid-template-columns:minmax(0,1fr)}.le-card .hwc-ph{aspect-ratio:3/2;min-height:0}}',
    '@media (prefers-reduced-motion:reduce){.le-bar i,.le-lim,.le-bb i{transition:none}}'
  ].join('\n');

  function injectCSS() {
    if (document.getElementById('lab-edgefit-css')) return;
    var s = document.createElement('style'); s.id = 'lab-edgefit-css'; s.textContent = CSS;
    document.head.appendChild(s);
  }
  function gb(b) { var g = b / 1e9; return g >= 10 ? g.toFixed(1) + ' GB' : g >= 1 ? g.toFixed(2) + ' GB' : Math.round(g * 1000) + ' MB'; }
  function tok(n) { return n >= 1024 ? (n / 1024) + 'k' : String(n); }
  function byId(a, id) { for (var i = 0; i < a.length; i++) if (a[i].id === id) return a[i]; return a[0]; }
  function dev(id) { return HW.devices[id] || HW.devices[DEV_ORDER[0]]; }

  /* ---------- the model ---------- */
  function bytesPerParam(prec) { return prec === 'fp16' ? 2 : prec === 'int8' ? 1.0625 : 0.5625; }
  function calc(st, m) {
    var d = dev(st.device);
    var bpp = bytesPerParam(st.prec);
    var keep = st.prec === 'int4p' ? (m.L - 2) / m.L : 1;
    var layers = m.L * keep;
    var weights = m.p * 1e9 * keep * bpp;
    var vision = st.vlm ? VISION_P * 1e9 * (st.prec === 'fp16' ? 2 : 1.0625) : 0;
    var ctx = CTX[st.ctx] + (st.vlm ? IMAGE_TOK : 0);
    var kvTok = 2 * layers * m.kvh * m.hd * byId2(KVP, st.kv);
    var kv = kvTok * ctx;
    var rt = 0.3e9 + 0.05 * (weights + vision);           // compute buffers, scratch, runtime
    var need = weights + vision + kv + rt;
    var usable = d.usable * 1e9;
    var kvRead = kvTok * ctx / 2;                           // KV read per token, averaged over the generation
    var tps = d.bw * 1e9 * d.eff / (weights + kvRead);
    var tpsEnd = d.bw * 1e9 * d.eff / (weights + kvTok * ctx);
    // QLoRA: 4-bit base, rank-16 adapters on every linear layer, fp32 Adam, gradient checkpointing
    var adapter = RANK * layers * (8 * m.h + 3 * m.I);
    var tBase = m.p * 1e9 * keep * 0.5625;
    var tAdapt = adapter * 16;                           // fp16 weight + grad, fp32 master + two Adam moments
    var tAct = layers * TRAIN_SEQ * m.h * 2 + TRAIN_SEQ * (18 * m.h + 4 * m.I) * 2 + TRAIN_SEQ * VOCAB * 4;
    var tRt = 0.4e9;
    var train = tBase + vision + tAdapt + tAct + tRt;
    return { d: d, weights: weights, vision: vision, kv: kv, rt: rt, need: need, usable: usable, total: d.mem * 1e9, fits: need <= usable, tps: tps, tpsEnd: tpsEnd, kvRead: kvRead, kvTok: kvTok, ctx: ctx,
      adapter: adapter, tBase: tBase, tAdapt: tAdapt, tAct: tAct, tRt: tRt, train: train, trainFits: train <= usable };
  }
  function byId2(a, id) { for (var i = 0; i < a.length; i++) if (a[i][0] === id) return a[i][1]; return a[0][1]; }

  var uid = 0;
  function mount(root) {
    if (root.__le) return; root.__le = true;
    var u = 'le' + (++uid) + '-';
    if (!HW) { root.innerHTML = '<p class="le-note">The hardware catalogue (hw.js) did not load.</p>'; return; }
    var st = { device: 'orin_nano', model: '3', prec: 'int4', ctx: 2, kv: 'fp16', vlm: true, train: true };
    root.innerHTML =
      '<div class="le"><div class="le-ctl">' +
        '<div class="le-hd"><i></i>Edge fit</div>' +
        '<div class="le-f"><label for="' + u + 'd">Device</label><select class="le-sel" id="' + u + 'd" data-k="device">' +
          DEV_ORDER.map(function (k) { var d = HW.devices[k]; return '<option value="' + k + '"' + (k === st.device ? ' selected' : '') + '>' + d.name + '</option>'; }).join('') + '</select></div>' +
        '<div class="le-f"><span class="le-lab" id="' + u + 'pl">Weights</span><div class="le-seg" role="group" aria-labelledby="' + u + 'pl" data-seg="prec">' +
          PREC.map(function (p) { return '<button type="button" data-v="' + p[0] + '" aria-pressed="' + (p[0] === st.prec) + '"' + (p[0] === 'int4p' ? ' title="int4 with two transformer layers pruned"' : '') + '>' + p[1] + '</button>'; }).join('') + '</div></div>' +
        '<div class="le-f"><span class="le-lab" id="' + u + 'ml">Model size <output>Qwen2.5-class</output></span><div class="le-lad" role="group" aria-labelledby="' + u + 'ml" data-x="lad">' +
          LADDER.map(function (m) { return '<button type="button" data-m="' + m.id + '" aria-pressed="' + (m.id === st.model) + '"><b>' + m.label + '</b><span></span><em></em></button>'; }).join('') + '</div></div>' +
        '<div class="le-f"><label for="' + u + 'c">Context <output data-x="ctxo">' + tok(CTX[st.ctx]) + '</output></label><input type="range" id="' + u + 'c" data-k="ctx" min="0" max="' + (CTX.length - 1) + '" step="1" value="' + st.ctx + '"></div>' +
        '<div class="le-f"><span class="le-lab" id="' + u + 'kl">KV cache</span><div class="le-seg" role="group" aria-labelledby="' + u + 'kl" data-seg="kv">' +
          KVP.map(function (p) { return '<button type="button" data-v="' + p[0] + '" aria-pressed="' + (p[0] === st.kv) + '">' + p[0] + '</button>'; }).join('') + '</div></div>' +
        '<label class="le-chk"><input type="checkbox" data-k="vlm"' + (st.vlm ? ' checked' : '') + '><span><b>Vision-language model</b>Adds a 0.6B vision encoder and one image (~1k tokens) to the context.</span></label>' +
        '<label class="le-chk"><input type="checkbox" data-k="train"' + (st.train ? ' checked' : '') + '><span><b>Fine-tune on the device</b>QLoRA, rank 16, 512-token samples, gradient checkpointing.</span></label>' +
      '</div>' +
      '<div class="le-out" aria-live="polite">' +
        '<div class="le-kpis">' +
          '<div class="le-kpi" data-x="fitk"><small>Inference</small><b data-x="fit">—</b><span data-x="fits">—</span></div>' +
          '<div class="le-kpi"><small>Decode speed</small><b data-x="tps">—</b><span>tok/s, bandwidth bound</span></div>' +
          '<div class="le-kpi"><small>Memory needed</small><b data-x="need">—</b><span data-x="needs">—</span></div>' +
          '<div class="le-kpi"><small>Largest that fits</small><b data-x="best">—</b><span data-x="bests">—</span></div>' +
        '</div>' +
        '<div class="le-mid"><div class="le-card" data-x="card"></div><div class="le-r">' +
          '<div><div class="le-sec">Where the bandwidth goes, per token<span data-x="bwlab">—</span></div>' +
            '<div class="le-bb" role="img" data-x="bb"><i class="le-c-w"></i><i class="le-c-kv"></i></div>' +
            '<div class="le-leg"><span><i class="le-c-w"></i>Weights <em data-x="bw1"></em></span><span><i class="le-c-kv"></i>KV cache, average over the answer <em data-x="bw2"></em></span></div>' +
            '<dl class="le-math"><dt>Bytes read per token</dt><dd data-x="m1">—</dd><dt>Effective bandwidth</dt><dd data-x="m2">—</dd><dt>Decode speed</dt><dd data-x="m3">—</dd><dt>At the end of the context</dt><dd data-x="m4">—</dd></dl></div>' +
          '<div data-x="trs" hidden><div class="le-sec">Fine-tuning memory<span data-x="tcap">—</span></div>' +
            '<div class="le-bw"><div class="le-bar" role="img" data-x="tbar"><i class="le-c-w"></i><i class="le-c-v"></i><i class="le-c-tr"></i><i class="le-c-kv"></i><i class="le-c-rt"></i><i class="le-c-over"></i></div><div class="le-lim" data-x="tlim"><span>usable</span></div></div>' +
            '<div class="le-leg"><span><i class="le-c-w"></i>4-bit base <em data-x="tw"></em></span><span data-x="tvs"><i class="le-c-v"></i>Vision encoder <em data-x="tv"></em></span><span><i class="le-c-tr"></i>Adapter, gradients, optimiser <em data-x="ta"></em></span><span><i class="le-c-kv"></i>Activations <em data-x="tact"></em></span><span><i class="le-c-rt"></i>Runtime <em data-x="trt"></em></span></div></div>' +
        '</div></div>' +
        '<div data-x="msg"></div>' +
        '<details class="le-how"><summary>How this is calculated</summary><ul>' +
          '<li>Weights take <code>params × bytes</code>: fp16 2, int8 1.06, int4 0.56 (group-wise scales included). "int4 −2L" also drops two transformer layers, which is what pruning buys before accuracy is re-checked.</li>' +
          '<li>KV cache is <code>2 × layers × KV heads × head dim × bytes × context</code>, using Qwen2.5-class shapes. The vision encoder (0.6B) stays in fp16 for fp16 weights and int8 otherwise; one image adds ~1k tokens of context.</li>' +
          '<li>Runtime buffers are <code>0.3 GB + 5% of weights</code>. "Usable" is what the device leaves a single process after the OS and other apps; phones get much less than their RAM.</li>' +
          '<li>Decode speed is bandwidth bound: <code>bandwidth × efficiency ÷ (weight bytes + KV bytes read per token)</code>, at 60–70% of the datasheet bandwidth depending on the device (an assumption; the card shows the figure used). The KV read is averaged over the answer, so it is half the context; the figure for the end of the context is the worst case. The vision encoder runs once per image, not per token, so it is not in the per-token bytes.</li>' +
          '<li>QLoRA keeps the base in 4-bit and trains rank-16 adapters on every linear layer: 16 bytes per adapter parameter (weight, gradient, fp32 master copy, two Adam moments), checkpointed activations for 512-token samples, and fp32 logits over a 152k vocabulary.</li>' +
          '<li>"Usable" memory is an assumption per device, shown on the card with its reason. Devices without a licensed photo show a labelled outline.</li>' +
          '<li>Not modelled: accuracy loss from quantisation and pruning, thermals, NPU operator coverage, CPU-only compute limits on the Raspberry Pi. Edge measures all of these on the device before anything ships.</li>' +
        '</ul></details>' +
        '<p class="le-note">A first-order estimate from public device specs. Edge measures the real fit, speed and accuracy on your device.</p>' +
      '</div></div>';

    var X = {}; [].forEach.call(root.querySelectorAll('[data-x]'), function (e) { X[e.getAttribute('data-x')] = e; });
    var ctxIn = root.querySelector('[data-k="ctx"]');
    var cardDev = null;
    // the device card: photo, the specs the estimate uses, and the inference-memory bar in its slot
    function buildCard(d) {
      var rows = [['Memory', d.mem + ' GB'], ['Usable by the model', d.usable + ' GB'], ['Memory bandwidth', d.bw + ' GB/s'], ['Bandwidth efficiency', Math.round(d.eff * 100) + '% assumed']];
      var c = HW.card(d, { rows: rows, sub: d.kind, note: d.note || '' });
      c.querySelector('.hwc-slot').innerHTML =
        '<div class="le-sec">Inference memory<span data-x="cap">—</span></div>' +
        '<div class="le-bw"><div class="le-bar" role="img" data-x="bar"><i class="le-c-w"></i><i class="le-c-v"></i><i class="le-c-kv"></i><i class="le-c-rt"></i><i class="le-c-over"></i></div><div class="le-lim" data-x="lim"><span>usable</span></div></div>' +
        '<div class="le-leg"><span><i class="le-c-w"></i>Weights <em data-x="lw"></em></span><span data-x="lvs"><i class="le-c-v"></i>Vision encoder <em data-x="lv"></em></span><span><i class="le-c-kv"></i>KV cache <em data-x="lkv"></em></span><span><i class="le-c-rt"></i>Runtime buffers <em data-x="lrt"></em></span><span><i class="le-c-os"></i>OS and apps <em data-x="los"></em></span></div>';
      X.card.innerHTML = ''; X.card.appendChild(c);
      [].forEach.call(c.querySelectorAll('[data-x]'), function (e) { X[e.getAttribute('data-x')] = e; });
    }

    root.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b || !root.contains(b)) return;
      if (b.hasAttribute('data-m')) { st.model = b.getAttribute('data-m'); }
      else if (b.hasAttribute('data-use')) { st.model = b.getAttribute('data-use'); }
      else if (b.parentNode.hasAttribute('data-seg')) { st[b.parentNode.getAttribute('data-seg')] = b.getAttribute('data-v'); }
      else return;
      update();
    });
    root.addEventListener('input', function (e) {
      var t = e.target, k = t.getAttribute('data-k'); if (!k) return;
      if (t.type === 'checkbox') st[k] = t.checked; else if (k === 'ctx') st.ctx = +t.value; else st[k] = t.value;
      update();
    });

    function setBar(bar, lim, parts, usable, total) {
      var sum = parts.reduce(function (a, b) { return a + b; }, 0);
      var scale = Math.max(total, sum) ;
      var is = bar.querySelectorAll('i');
      var over = Math.max(0, sum - usable);
      // segments in order; overflow beyond usable is hatched red at the end
      for (var i = 0; i < parts.length; i++) is[i].style.width = (parts[i] / scale * 100).toFixed(2) + '%';
      is[parts.length].style.width = '0%';
      var lp = usable / scale * 100;
      lim.style.left = lp.toFixed(2) + '%';
      lim.className = 'le-lim' + (lp > 88 ? ' le-r' : lp < 12 ? ' le-l' : '');
      // OS share: shown as the background between usable and total
      bar.style.background = 'linear-gradient(90deg,var(--white) 0 ' + lp.toFixed(2) + '%,transparent ' + lp.toFixed(2) + '%),repeating-linear-gradient(135deg,#cbd5e1 0 4px,#e2e8f0 4px 8px)';
      if (over > 0) bar.style.borderColor = 'var(--bad)'; else bar.style.borderColor = '';
      return over;
    }

    function update() {
      var m = byId(LADDER, st.model);
      ctxIn.style.setProperty('--p', (st.ctx / (CTX.length - 1) * 100) + '%');
      X.ctxo.textContent = tok(CTX[st.ctx]);
      [].forEach.call(root.querySelectorAll('[data-seg] button'), function (b) { b.setAttribute('aria-pressed', st[b.parentNode.getAttribute('data-seg')] === b.getAttribute('data-v') ? 'true' : 'false'); });
      var best = null, all = {};
      LADDER.forEach(function (x) { var r = calc(st, x); all[x.id] = r; if (r.fits && (!st.train || r.trainFits)) best = x; });
      [].forEach.call(X.lad.children, function (b) {
        var id = b.getAttribute('data-m'), r = all[id];
        b.setAttribute('aria-pressed', id === st.model ? 'true' : 'false');
        b.querySelector('span').textContent = gb(r.need) + (r.fits ? ' · ' + Math.round(r.tps) + ' tok/s' : '');
        var em = b.querySelector('em'), ok = r.fits && (!st.train || r.trainFits);
        em.className = best && best.id === id ? 'le-best' : ok ? 'le-y' : 'le-n';
        em.textContent = best && best.id === id ? 'largest fit' : ok ? 'fits' : r.fits ? 'no training' : 'too big';
      });
      var r = all[m.id], d = r.d;
      if (cardDev !== st.device) { cardDev = st.device; buildCard(d); }
      X.fitk.className = 'le-kpi ' + (r.fits ? 'le-ok' : 'le-no');
      X.fit.textContent = r.fits ? 'Fits' : 'Too big';
      X.fits.textContent = r.fits ? gb(r.usable - r.need) + ' headroom' : gb(r.need - r.usable) + ' over';
      X.tps.textContent = r.fits ? (r.tps >= 100 ? Math.round(r.tps) : r.tps.toFixed(1)) : '—';
      X.need.textContent = gb(r.need);
      X.needs.textContent = 'of ' + d.usable + ' GB usable';
      X.best.textContent = best ? best.label : 'None';
      X.bests.innerHTML = best ? (best.id === m.id ? 'selected' : '<button type="button" class="le-use" data-use="' + best.id + '">Use ' + best.label + '</button>') : 'try int4 or a shorter context';
      X.cap.textContent = 'of ' + d.usable + ' GB';
      setBar(X.bar, X.lim, [r.weights, r.vision, r.kv, r.rt], r.usable, r.total);
      X.bar.setAttribute('aria-label', 'Needs ' + gb(r.need) + ' of ' + d.usable + ' GB usable');
      X.lw.textContent = gb(r.weights); X.lv.textContent = gb(r.vision); X.lvs.hidden = !st.vlm; X.lkv.textContent = gb(r.kv); X.lrt.textContent = gb(r.rt);
      X.los.textContent = gb(r.total - r.usable);
      var bytesTok = r.weights + r.kvRead, effBW = d.bw * 1e9 * d.eff;
      X.bb.querySelectorAll('i')[0].style.width = (r.weights / bytesTok * 100).toFixed(2) + '%';
      X.bb.querySelectorAll('i')[1].style.width = (r.kvRead / bytesTok * 100).toFixed(2) + '%';
      X.bb.setAttribute('aria-label', 'Per token: weights ' + gb(r.weights) + ', KV cache ' + gb(r.kvRead));
      X.bw1.textContent = gb(r.weights); X.bw2.textContent = gb(r.kvRead);
      X.bwlab.textContent = gb(bytesTok) + ' per token';
      X.m1.textContent = gb(r.weights) + ' + ' + gb(r.kvRead) + ' = ' + gb(bytesTok);
      X.m2.textContent = d.bw + ' GB/s × ' + d.eff.toFixed(2) + ' = ' + Math.round(effBW / 1e9) + ' GB/s';
      X.m3.textContent = Math.round(effBW / 1e9) + ' GB/s ÷ ' + gb(bytesTok) + ' = ' + (r.tps >= 100 ? Math.round(r.tps) : r.tps.toFixed(1)) + ' tok/s';
      X.m4.textContent = (r.tpsEnd >= 100 ? Math.round(r.tpsEnd) : r.tpsEnd.toFixed(1)) + ' tok/s at ' + tok(r.ctx) + ' tokens of KV';
      X.trs.hidden = !st.train;
      if (st.train) {
        X.tcap.textContent = gb(r.train) + ' of ' + d.usable + ' GB usable';
        setBar(X.tbar, X.tlim, [r.tBase, r.vision, r.tAdapt, r.tAct, r.tRt], r.usable, r.total);
        X.tbar.setAttribute('aria-label', 'Fine-tuning needs ' + gb(r.train) + ' of ' + d.usable + ' GB usable');
        X.tw.textContent = gb(r.tBase); X.tv.textContent = gb(r.vision); X.tvs.hidden = !st.vlm; X.ta.textContent = gb(r.tAdapt) + ' (' + (r.adapter / 1e6).toFixed(0) + 'M params)'; X.tact.textContent = gb(r.tAct); X.trt.textContent = gb(r.tRt);
      }
      var label = m.label + (st.vlm ? ' VLM' : '') + ' at ' + PREC.filter(function (p) { return p[0] === st.prec; })[0][1];
      var msg;
      if (!r.fits) msg = '<div class="le-msg le-bad">' + label + ' needs ' + gb(r.need) + ' but the ' + d.name + ' leaves ' + d.usable + ' GB for the model. ' + (best ? 'The largest that fits with these settings is ' + best.label + '.' : 'Nothing on the ladder fits with these settings.') + '</div>';
      else if (st.train && !r.trainFits) msg = '<div class="le-msg le-bad">Inference fits, but fine-tuning ' + label + ' needs ' + gb(r.train) + '. Train a smaller model on the device, or train elsewhere and push the adapter.</div>';
      else if (st.train) msg = '<div class="le-msg le-good">' + label + ' runs and fine-tunes on the ' + d.name + ': adapters are ' + gb(r.adapter * 2) + ' to push to every device on the same base.</div>';
      else msg = '<div class="le-msg">' + label + ' fits the ' + d.name + ' at ' + tok(CTX[st.ctx]) + ' context with ' + gb(r.usable - r.need) + ' to spare, at about ' + Math.round(r.tps) + ' tok/s.</div>';
      X.msg.innerHTML = msg;
    }
    update();
  }

  function init() { injectCSS(); [].forEach.call(document.querySelectorAll('[data-lab="edgefit"]'), mount); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
