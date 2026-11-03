/* Kernel lab: occupancy, register pressure, achievable bandwidth and a roofline for one kernel
   on one GPU, computed from the public compute-capability rules in hw.js (window.VO_HW).
   Renders into every [data-lab="kernel"]. No libraries, no network.

   Every figure comes from a stated rule or a visible assumption:
   - occupancy: the CUDA occupancy calculator's rules (register and shared-memory allocation
     granularity, warps/blocks/threads per SM), per architecture; a simplified wave64 model for CDNA 3;
   - spills: the per-thread register cap nvcc derives from __launch_bounds__ / maxrregcount;
   - achievable bandwidth: Little's law with an assumed DRAM latency;
   - time: max(bytes / achievable bandwidth, FLOPs / peak rate).
   ptxas decides the real register count; -Xptxas -v prints it. These are estimates of the mechanics. */
(function () {
  'use strict';
  var HW = window.VO_HW;
  if (!HW) { return; }

  /* vector FP32 TFLOPS from the datasheets, for kernels that do not use the tensor cores
     (the catalogue only carries tensor rates). AGX Orin: 2048 cores × 1.3 GHz × 2. */
  var FP32 = { h100: 67, h200: 67, b200: 80, a100: 19.5, l40s: 91.6, rtx5090: 104.8, mi300x: 163.4, agx_orin: 5.3 };
  var GPU_ORDER = ['h100', 'h200', 'b200', 'a100', 'l40s', 'rtx5090', 'mi300x', 'agx_orin'];

  /* ───────────────────────────── occupancy calculator ───────────────────────────── */
  function roundUp(x, u) { return Math.ceil(x / u) * u; }
  function roundDown(x, u) { return Math.floor(x / u) * u; }

  /* nvcc's per-thread register cap from __launch_bounds__(threads, minBlocksPerSM):
     regs = floor(regsPerSM / (minBlocks × threads rounded up to a warp)), rounded down to 8, at most the ISA maximum. */
  function regCap(A, threads, minBlocks) {
    if (A.amd) {
      var wpb = Math.ceil(threads / A.warpSize);
      var wavesPerSIMD = Math.ceil(minBlocks * wpb / A.simdsPerCU);
      return Math.min(A.maxVgprPerWave, roundDown(Math.floor(A.vgprPerSIMD / wavesPerSIMD), A.vgprAllocUnit));
    }
    var warpThreads = roundUp(threads, A.warpSize);
    return Math.max(8, Math.min(A.maxRegsPerThread, roundDown(Math.floor(A.regsPerSM / (minBlocks * warpThreads)), 8)));
  }

  /* p: {threads, regs, smem} with regs already capped. Returns the resident warps per SM and what limits them. */
  function occupancy(A, p) {
    var r = { threads: p.threads };
    if (A.amd) {
      var wpb = Math.ceil(p.threads / A.warpSize);
      var vg = roundUp(Math.max(p.regs, A.vgprAllocUnit), A.vgprAllocUnit);
      var wavesPerSIMD = Math.min(A.maxWavesPerSIMD, Math.floor(A.vgprPerSIMD / vg));
      var wavesByRegs = wavesPerSIMD * A.simdsPerCU;
      var blocksByRegs = Math.floor(wavesByRegs / wpb);
      var ldsAlloc = p.smem > 0 ? roundUp(p.smem, A.ldsAllocUnit) : 0;
      var blocksBySmem = ldsAlloc > 0 ? Math.floor(A.ldsPerCU / ldsAlloc) : A.maxWorkgroupsPerCU;
      var maxWaves = A.maxWavesPerSIMD * A.simdsPerCU;
      var blocksByWaves = Math.floor(maxWaves / wpb);
      var blocks = Math.max(0, Math.min(blocksByRegs, blocksBySmem, blocksByWaves, A.maxWorkgroupsPerCU));
      var lim = blocks * wpb >= maxWaves ? 'CU full' : blocks === blocksByRegs ? 'registers' : blocks === blocksBySmem ? 'LDS' : blocks === blocksByWaves ? 'waves per CU' : 'workgroups per CU';
      if (p.threads > 1024) { blocks = 0; lim = 'block too large'; }
      r.warpsPerBlock = wpb; r.regsPerWarpAlloc = vg * A.warpSize; r.regsAlloc = vg; r.blocks = blocks; r.warps = blocks * wpb;
      r.maxWarps = maxWaves; r.occ = r.warps / maxWaves; r.limiter = lim; r.smemAlloc = ldsAlloc; r.smemTotal = A.ldsPerCU;
      r.regsFile = A.vgprPerSIMD * A.simdsPerCU; r.regsUsed = r.warps * vg; r.regsWaste = r.warps * (vg - p.regs);
      r.limits = { registers: blocksByRegs, smem: blocksBySmem, warps: blocksByWaves, blocks: A.maxWorkgroupsPerCU };
      r.unit = 'wave'; return r;
    }
    var warpsPerBlock = Math.ceil(p.threads / A.warpSize);
    var regsPerWarp = roundUp(Math.max(p.regs, 1) * A.warpSize, A.regAllocUnit);
    var warpsByRegs = roundDown(Math.floor(A.regsPerSM / regsPerWarp), A.warpAllocGran);
    var blocksByRegs = Math.floor(warpsByRegs / warpsPerBlock);
    var smemAlloc = roundUp(p.smem + A.smemReservedPerBlock, A.smemAllocUnit);
    var blocksBySmem = Math.floor(A.smemPerSM / smemAlloc);
    var blocksByWarps = Math.floor(A.maxWarpsPerSM / warpsPerBlock);
    var blocks = Math.max(0, Math.min(blocksByRegs, blocksBySmem, blocksByWarps, A.maxBlocksPerSM));
    var limiter = blocks * warpsPerBlock >= A.maxWarpsPerSM ? 'SM full' : blocks === blocksByRegs ? 'registers' : blocks === blocksBySmem ? 'shared memory' : blocks === blocksByWarps ? 'warps per SM' : 'blocks per SM';
    if (p.threads > 1024) { blocks = 0; limiter = 'block too large'; }
    if (p.smem > A.smemPerBlockMax) { blocks = 0; limiter = 'shared memory per block'; }
    r.warpsPerBlock = warpsPerBlock; r.regsPerWarpAlloc = regsPerWarp; r.blocks = blocks; r.warps = blocks * warpsPerBlock;
    r.maxWarps = A.maxWarpsPerSM; r.occ = r.warps / A.maxWarpsPerSM; r.limiter = limiter; r.smemAlloc = smemAlloc; r.smemTotal = A.smemPerSM;
    r.regsFile = A.regsPerSM; r.regsUsed = r.warps * regsPerWarp; r.regsWaste = r.warps * (regsPerWarp - p.regs * A.warpSize);
    r.limits = { registers: blocksByRegs, smem: blocksBySmem, warps: blocksByWarps, blocks: A.maxBlocksPerSM };
    r.unit = 'warp'; return r;
  }

  /* ───────────────────────────── kernels ───────────────────────────── */
  var KERNELS = {
    rmsnorm: {
      name: 'RMSNorm + FP8 quant', rate: 'fp32', dtypeNote: 'vector FP32 (no tensor cores)',
      params: [['tokens', 'Tokens', 8192, 256, 65536], ['hidden', 'Hidden size', 4096, 1024, 16384], ['ept', 'Elements per thread', 8, 2, 32]],
      defaults: { threads: 256, ilp: 2, bpl: 16 },
      est: function (k, s) { return { regs: 20 + Math.ceil(k.ept / 2) + s.ilp * s.bpl / 4, smem: 0 }; },
      work: function (k, s) {
        var n = k.tokens * k.hidden;
        return { bytes: n * 3 + k.tokens * 4, flops: 6 * n, threads: Math.ceil(n / k.ept), iters: 1,
          text: 'bytes = tokens × hidden × (2 read + 1 write) + tokens × 4 (scale); FLOPs = 6 × tokens × hidden; threads = tokens × hidden / elements per thread' };
      },
      regsText: 'registers ≈ 20 (addresses, loop, reduction) + elements per thread ÷ 2 (bf16 packed in pairs) + loads in flight × bytes per load ÷ 4'
    },
    attn: {
      name: 'Decode attention (GQA)', rate: 'bf16', dtypeNote: 'BF16 tensor rate (flash-decoding style)',
      params: [['batch', 'Sequences', 16, 1, 256], ['heads', 'Query heads', 32, 8, 128], ['kvh', 'KV heads', 8, 1, 64], ['hd', 'Head dim', 128, 64, 256], ['kvlen', 'KV length', 8192, 512, 131072], ['kvb', 'KV bytes per value', 2, 1, 2]],
      defaults: { threads: 128, ilp: 4, bpl: 16 },
      est: function (k, s) {
        var g = Math.max(1, Math.round(k.heads / k.kvh));
        return { regs: 24 + Math.ceil(g * k.hd / 32 / 2) + 8 + s.ilp * s.bpl / 4, smem: g * k.hd * 4 * Math.ceil(s.threads / 32) };
      },
      work: function (k, s) {
        var splits = Math.ceil(k.kvlen / 2048);
        return { bytes: k.batch * 2 * k.kvh * k.hd * k.kvlen * k.kvb, flops: k.batch * 4 * k.heads * k.hd * k.kvlen, threads: k.batch * k.kvh * splits * s.threads, iters: Math.ceil(2048 / Math.ceil(s.threads / 32)),
          text: 'bytes = sequences × 2 (K and V) × KV heads × head dim × KV length × bytes per value; FLOPs = sequences × 4 × query heads × head dim × KV length; one block per (sequence, KV head, 2k-token split); each warp sweeps its share of the split' };
      },
      regsText: 'registers ≈ 24 + (query heads per KV head × head dim ÷ 32 lanes ÷ 2, the group\'s bf16 query packed) + 8 (running max, sum, partial output) + loads in flight × bytes per load ÷ 4; shared memory = group × head dim × 4 B per warp for the partial outputs'
    },
    gemm: {
      name: 'GEMM tile (bf16)', rate: 'bf16', dtypeNote: 'BF16 tensor rate',
      params: [['M', 'M', 8192, 256, 65536], ['N', 'N', 8192, 256, 65536], ['K', 'K', 8192, 256, 65536], ['bm', 'Block tile M', 128, 32, 256], ['bn', 'Block tile N', 128, 32, 256], ['bk', 'Block tile K', 64, 16, 128], ['stages', 'Pipeline stages', 3, 1, 6]],
      defaults: { threads: 256, ilp: 2, bpl: 16 },
      est: function (k, s) {
        var acc = Math.ceil(k.bm * k.bn / s.threads), tm = Math.ceil(Math.sqrt(acc)), tn = Math.ceil(acc / tm);
        return { regs: 24 + acc + tm + tn, smem: (k.bm * k.bk + k.bk * k.bn) * 2 * k.stages };
      },
      work: function (k, s) {
        return { bytes: (k.M * k.K + k.K * k.N + k.M * k.N) * 2, flops: 2 * k.M * k.N * k.K, threads: Math.ceil(k.M / k.bm) * Math.ceil(k.N / k.bn) * s.threads, iters: Math.ceil(k.K / k.bk),
          text: 'DRAM bytes = (M×K + K×N + M×N) × 2, the read-once ideal (tiles re-read from L2 are not counted); FLOPs = 2 × M × N × K; one block per output tile; iterations = K ÷ block tile K' };
      },
      regsText: 'registers ≈ 24 + accumulators (block tile M × N ÷ threads, fp32) + fragment rows + fragment columns; shared memory = (tile M × tile K + tile K × tile N) × 2 B × pipeline stages'
    },
    silu: {
      name: 'SiLU × up (elementwise)', rate: 'fp32', dtypeNote: 'vector FP32 (no tensor cores)',
      params: [['tokens', 'Tokens', 8192, 256, 65536], ['inter', 'Intermediate size', 14336, 1024, 65536], ['ept', 'Elements per thread', 8, 2, 32]],
      defaults: { threads: 256, ilp: 2, bpl: 16 },
      est: function (k, s) { return { regs: 20 + k.ept + s.ilp * s.bpl / 4, smem: 0 }; },
      work: function (k, s) {
        var n = k.tokens * k.inter;
        return { bytes: n * 6, flops: 8 * n, threads: Math.ceil(n / k.ept), iters: 1,
          text: 'bytes = tokens × intermediate × (2 + 2 read + 2 write); FLOPs ≈ 8 per element (exp, add, divide, two multiplies); threads = elements ÷ elements per thread' };
      },
      regsText: 'registers ≈ 20 + elements per thread (two bf16 inputs unpacked to fp32 pairs) + loads in flight × bytes per load ÷ 4'
    }
  };

  /* ───────────────────────────── the full estimate for one GPU ───────────────────────────── */
  function estimate(gpuKey, st) {
    var G = HW.gpus[gpuKey], A = HW.arch[G.arch], K = KERNELS[st.kernel];
    var cap = st.lb ? regCap(A, st.threads, st.minBlocks) : (A.amd ? A.maxVgprPerWave : A.maxRegsPerThread);
    var regs = Math.min(st.regs, cap), spilled = Math.max(0, st.regs - cap);
    var occ = occupancy(A, { threads: st.threads, regs: regs, smem: st.smem });
    var lanes = A.warpSize, units = G.sms || G.cus;
    var latency = st.latency != null ? st.latency : G.latency;
    var inFlightPerSM = occ.warps * lanes * st.ilp * st.bpl;
    var little = inFlightPerSM * units / (latency * 1e-9);               // bytes per second
    var peakBW = G.bw * 1e12;
    var achBW = Math.min(peakBW, little);
    var w = K.work(st.k, st);
    var spillBytes = spilled * 4 * 2 * w.threads * w.iters;
    var bytes = w.bytes + spillBytes;
    var rate = K.rate === 'fp32' ? (G.flops.fp32 || FP32[gpuKey]) : (G.flops[K.rate] || G.flops.bf16);
    var peakF = rate * 1e12;
    var tMem = bytes / achBW, tComp = w.flops / peakF;
    var launchable = occ.warps > 0;
    var bound = !launchable ? 'does not launch' : tComp > tMem ? 'compute' : (little < peakBW ? 'latency' : 'memory');
    if (!launchable) { achBW = 0; tMem = Infinity; }
    return { G: G, A: A, K: K, cap: cap, regs: regs, spilled: spilled, occ: occ, latency: latency, inFlightPerSM: inFlightPerSM, little: little, peakBW: peakBW, achBW: achBW,
      work: w, spillBytes: spillBytes, bytes: bytes, flops: w.flops, rate: rate, peakF: peakF, tMem: tMem, tComp: tComp, t: Math.max(tMem, tComp), bound: bound,
      ai: w.flops / bytes, units: units, lanes: lanes, launchable: launchable };
  }

  /* ───────────────────────────── formatting ───────────────────────────── */
  var fmt = HW.fmt, esc = HW.esc;
  function si(v, unit, d) {
    var a = Math.abs(v);
    if (a >= 1e12) return fmt(v / 1e12, d == null ? 2 : d) + ' T' + unit;
    if (a >= 1e9) return fmt(v / 1e9, d == null ? 2 : d) + ' G' + unit;
    if (a >= 1e6) return fmt(v / 1e6, d == null ? 1 : d) + ' M' + unit;
    if (a >= 1e3) return fmt(v / 1e3, d == null ? 1 : d) + ' k' + unit;
    return fmt(v, d == null ? 0 : d) + ' ' + unit;
  }
  function tm(s) { return !isFinite(s) ? 'n/a' : s >= 1 ? fmt(s, 2) + ' s' : s >= 1e-3 ? fmt(s * 1e3, 2) + ' ms' : fmt(s * 1e6, 1) + ' µs'; }
  function kb(b) { return b >= 1024 ? fmt(b / 1024, b % 1024 ? 1 : 0) + ' KB' : fmt(b) + ' B'; }
  function pct(x) { return fmt(x * 100, x * 100 < 10 && x > 0 ? 1 : 0) + '%'; }

  /* ───────────────────────────── drawings ───────────────────────────── */
  /* register file: one cell per allocation unit; resident warps fill cells in turn (two shades so
     they can be told apart), the rounding waste inside a warp's allocation is drawn in a lighter tint,
     and what no warp can use is hatched. */
  function regFileSVG(E) {
    var A = E.A, o = E.occ, unit = A.amd ? A.vgprAllocUnit * A.warpSize : A.regAllocUnit;
    var total = o.regsFile * (A.amd ? A.warpSize : 1); // registers counted per lane for AMD → scale to 32-bit entries
    var cells = Math.round(total / unit), cols = A.amd ? 32 : 16, rows = Math.ceil(cells / cols);
    var cw = 100 / cols, ch = cw * (A.amd ? 1.6 : 1);
    var H = rows * ch, out = ['<svg class="lk-rf" viewBox="0 0 100 ' + H.toFixed(2) + '" preserveAspectRatio="none" role="img" aria-label="Register file: ' + fmt(o.regsUsed) + ' of ' + fmt(total) + ' registers allocated by ' + o.warps + ' resident ' + o.unit + 's">'];
    out.push('<defs><pattern id="lk-h" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="4" style="stroke:var(--line)" stroke-width="1.2"/></pattern></defs>');
    var perWarp = (A.amd ? o.regsAlloc * A.warpSize : o.regsPerWarpAlloc), usedPerWarp = (A.amd ? E.regs * A.warpSize : E.regs * A.warpSize);
    var cellsPerWarp = perWarp / unit, c = 0;
    for (var wi = 0; wi < o.warps; wi++) {
      var fill = wi % 2 ? 'var(--brand2)' : 'var(--brand)';
      for (var j = 0; j < cellsPerWarp; j++, c++) {
        var x = (c % cols) * cw, y = Math.floor(c / cols) * ch;
        out.push('<rect x="' + x.toFixed(2) + '" y="' + y.toFixed(2) + '" width="' + (cw - 0.35).toFixed(2) + '" height="' + (ch - 0.35).toFixed(2) + '" style="fill:' + fill + '"/>');
      }
      var waste = perWarp - usedPerWarp;
      if (waste > 0) { // the tail of this warp's allocation that holds nothing
        var wc = waste / unit, k = c - 1, px = (k % cols) * cw, py = Math.floor(k / cols) * ch, fw = Math.min(1, wc) * (cw - 0.35);
        out.push('<rect x="' + (px + (cw - 0.35) - fw).toFixed(2) + '" y="' + py.toFixed(2) + '" width="' + fw.toFixed(2) + '" height="' + (ch - 0.35).toFixed(2) + '" style="fill:var(--brand200)"/>');
      }
    }
    for (; c < cells; c++) {
      var x2 = (c % cols) * cw, y2 = Math.floor(c / cols) * ch;
      out.push('<rect x="' + x2.toFixed(2) + '" y="' + y2.toFixed(2) + '" width="' + (cw - 0.35).toFixed(2) + '" height="' + (ch - 0.35).toFixed(2) + '" fill="url(#lk-h)"/>');
    }
    out.push('</svg>');
    return out.join('');
  }

  function smemSVG(E) {
    var o = E.occ, total = o.smemTotal, out = ['<svg class="lk-sm" viewBox="0 0 100 6" preserveAspectRatio="none" role="img" aria-label="Shared memory: ' + o.blocks + ' blocks of ' + kb(o.smemAlloc) + ' in ' + kb(total) + '">'];
    var x = 0, resv = E.A.amd ? 0 : E.A.smemReservedPerBlock;
    for (var b = 0; b < o.blocks; b++) {
      var w = o.smemAlloc / total * 100, rw = resv / total * 100;
      out.push('<rect x="' + x.toFixed(2) + '" y="0" width="' + Math.max(0, w - 0.3).toFixed(2) + '" height="6" style="fill:' + (b % 2 ? 'var(--brand2)' : 'var(--brand)') + '"/>');
      if (rw > 0) out.push('<rect x="' + x.toFixed(2) + '" y="0" width="' + rw.toFixed(2) + '" height="6" style="fill:var(--ink3)" opacity=".55"/>');
      x += w;
    }
    out.push('<rect x="' + x.toFixed(2) + '" y="0" width="' + Math.max(0, 100 - x).toFixed(2) + '" height="6" style="fill:var(--line2)"/></svg>');
    return out.join('');
  }

  /* occupancy against registers per thread, from the same calculator, for every architecture */
  function occCurveSVG(E, st) {
    var W = 320, H = 150, L = 34, R = 10, T = 12, B = 26, maxX = 255;
    var X = function (r) { return L + (r - 8) / (maxX - 8) * (W - L - R); };
    var Y = function (o) { return T + (1 - o) * (H - T - B); };
    var out = ['<svg class="lk-ch" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Occupancy against registers per thread on ' + esc(E.A.name) + '">'];
    [0, .25, .5, .75, 1].forEach(function (g) { out.push('<line class="lk-grid" x1="' + L + '" x2="' + (W - R) + '" y1="' + Y(g) + '" y2="' + Y(g) + '"/><text class="lk-ax" x="' + (L - 4) + '" y="' + (Y(g) + 3) + '" text-anchor="end">' + Math.round(g * 100) + '%</text>'); });
    [32, 64, 96, 128, 160, 192, 224, 255].forEach(function (r) { out.push('<text class="lk-ax" x="' + X(r) + '" y="' + (H - 8) + '" text-anchor="middle">' + r + '</text>'); });
    var archs = Object.keys(HW.arch);
    function path(A) {
      var d = '', prev = null;
      for (var r = 8; r <= maxX; r++) {
        var o = occupancy(A, { threads: st.threads, regs: r, smem: st.smem }).occ;
        if (prev === null) d += 'M' + X(r).toFixed(1) + ' ' + Y(o).toFixed(1);
        else if (o !== prev) d += 'L' + X(r).toFixed(1) + ' ' + Y(prev).toFixed(1) + 'L' + X(r).toFixed(1) + ' ' + Y(o).toFixed(1);
        prev = o;
      }
      return d + 'L' + X(maxX).toFixed(1) + ' ' + Y(prev).toFixed(1);
    }
    archs.forEach(function (k) { if (HW.arch[k] !== E.A) out.push('<path class="lk-ln ghost" d="' + path(HW.arch[k]) + '"/>'); });
    if (E.cap < maxX) out.push('<rect x="' + X(E.cap) + '" y="' + T + '" width="' + (X(maxX) - X(E.cap)) + '" height="' + (H - T - B) + '" style="fill:var(--warn)" opacity=".14"/><line class="lk-cap" x1="' + X(E.cap) + '" x2="' + X(E.cap) + '" y1="' + T + '" y2="' + (H - B) + '"/><text class="lk-ax warn" x="' + (X(E.cap) + 3) + '" y="' + (T + 9) + '">cap ' + E.cap + ' · spills</text>');
    out.push('<path class="lk-ln" d="' + path(E.A) + '"/>');
    out.push('<circle class="lk-pt" cx="' + X(Math.min(st.regs, maxX)) + '" cy="' + Y(E.occ.occ) + '" r="4"/>');
    out.push('<text class="lk-ax" x="' + (W - R) + '" y="' + (H - 8) + '" text-anchor="end" style="display:none">regs</text></svg>');
    return out.join('');
  }

  /* roofline, log-log: peak bandwidth roof, achievable (Little's law) roof, compute roof, and the kernel */
  function rooflineSVG(E) {
    var W = 320, H = 170, L = 40, R = 10, T = 12, B = 26;
    var x0 = Math.log10(0.1), x1 = Math.log10(10000), y0 = Math.log10(0.5), y1 = Math.log10(20000);
    var X = function (ai) { return L + (Math.log10(ai) - x0) / (x1 - x0) * (W - L - R); };
    var Y = function (tf) { return T + (1 - (Math.log10(tf) - y0) / (y1 - y0)) * (H - T - B); };
    var clampY = function (v) { return Math.max(T, Math.min(H - B, v)); };
    var out = ['<svg class="lk-ch" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Roofline for ' + esc(E.G.name) + '">'];
    [1, 10, 100, 1000, 10000].forEach(function (g) { out.push('<line class="lk-grid" x1="' + L + '" x2="' + (W - R) + '" y1="' + Y(g) + '" y2="' + Y(g) + '"/><text class="lk-ax" x="' + (L - 4) + '" y="' + (Y(g) + 3) + '" text-anchor="end">' + (g >= 1000 ? g / 1000 + 'P' : g + 'T') + '</text>'); });
    [0.1, 1, 10, 100, 1000, 10000].forEach(function (g) { out.push('<text class="lk-ax" x="' + X(g) + '" y="' + (H - 8) + '" text-anchor="middle">' + (g >= 1000 ? g / 1000 + 'k' : g) + '</text>'); });
    out.push('<text class="lk-ax" x="' + (W - R) + '" y="' + (H - 16) + '" text-anchor="end">FLOP / byte</text>');
    function roof(bwTB, cls, label) {
      var peakT = E.rate, knee = peakT / bwTB;
      var d = 'M' + X(0.1) + ' ' + clampY(Y(0.1 * bwTB)) + 'L' + X(Math.min(knee, 10000)) + ' ' + clampY(Y(Math.min(knee, 10000) * bwTB));
      if (knee < 10000) d += 'L' + X(10000) + ' ' + Y(peakT);
      out.push('<path class="lk-ln ' + cls + '" d="' + d + '"/>');
      if (label) out.push('<text class="lk-ax" x="' + (X(0.1) + 3) + '" y="' + (clampY(Y(0.1 * bwTB)) - 4) + '">' + label + '</text>');
    }
    roof(E.peakBW / 1e12, 'ghost', 'peak ' + fmt(E.G.bw, 2) + ' TB/s');
    if (E.achBW < E.peakBW) roof(E.achBW / 1e12, 'warn', 'achievable ' + fmt(E.achBW / 1e12, 2) + ' TB/s');
    else roof(E.achBW / 1e12, '', '');
    out.push('<text class="lk-ax" x="' + (W - R - 2) + '" y="' + (Y(E.rate) - 4) + '" text-anchor="end">' + fmt(E.rate) + ' TFLOPS ' + E.K.rate + '</text>');
    if (E.launchable) {
      var attained = E.flops / E.t / 1e12, px = X(Math.max(0.1, Math.min(10000, E.ai))), py = clampY(Y(attained)), left = px > (W - R) * 0.6;
      out.push('<line class="lk-cap" x1="' + px + '" x2="' + px + '" y1="' + py + '" y2="' + (H - B) + '"/>');
      out.push('<circle class="lk-pt" cx="' + px + '" cy="' + py + '" r="4.5"/>');
      out.push('<text class="lk-ax pt" x="' + (left ? px - 7 : px + 7) + '" y="' + (py + (left ? 14 : 3)) + '"' + (left ? ' text-anchor="end"' : '') + '>' + fmt(E.ai, E.ai < 10 ? 2 : 0) + ' FLOP/B · ' + fmt(attained, attained < 10 ? 1 : 0) + ' TFLOPS</text>');
    }
    out.push('</svg>');
    return out.join('');
  }

  /* ───────────────────────────── CSS ───────────────────────────── */
  function css() {
    if (document.getElementById('lab-kernel-css')) return;
    var s = document.createElement('style'); s.id = 'lab-kernel-css';
    s.textContent = [
      '.lk-root{font-family:var(--font);color:var(--ink);background:var(--white);border:1px solid var(--line);border-radius:12px;box-shadow:0 1px 2px rgba(16,24,40,.05);display:grid;grid-template-columns:280px minmax(0,1fr);overflow:hidden;font-size:13px;line-height:1.45}',
      '.vlab .lk-root{--ok:#34d399;--warn:#fbbf24;--bad:#f87171;box-shadow:none}',
      '.lk-root *{box-sizing:border-box}',
      '.lk-ctl{padding:12px 14px 14px;border-right:1px solid var(--line);background:var(--bg);display:grid;gap:9px;align-content:start}',
      '.lk-res{padding:12px 14px 14px;min-width:0;display:grid;gap:12px;align-content:start}.lk-res>*,.lk-charts>*,.lk-hw>*{min-width:0}',
      '.lk-h{display:flex;align-items:center;gap:8px;font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--brand)}',
      '.lk-h::before{content:"";width:6px;height:6px;border-radius:50%;background:var(--brand)}',
      '.lk-f{display:grid;gap:5px}.lk-f>label,.lk-lab{font-size:12px;font-weight:600;color:var(--ink2);display:flex;justify-content:space-between;gap:8px}',
      '.lk-f>label output,.lk-lab output{font-family:var(--mono);font-weight:500;color:var(--brand)}',
      '.lk-root select,.lk-root input[type=number]{width:100%;font:inherit;font-size:13px;padding:7px 9px;border:1px solid var(--line);border-radius:7px;background:var(--white);color:var(--ink)}',
      '.lk-root input[type=number]{font-family:var(--mono)}',
      '.lk-root input[type=range]{width:100%;accent-color:var(--brand);margin:2px 0}',
      '.lk-seg{display:flex;flex-wrap:wrap;gap:4px}.lk-seg button{font:inherit;font-size:12px;font-weight:600;padding:6px 9px;border:1px solid var(--line);border-radius:7px;background:var(--white);color:var(--ink2);cursor:pointer;flex:1 1 auto;min-width:0}',
      '.lk-seg button[aria-pressed=true]{background:var(--brand);border-color:var(--brand);color:#fff}',
      '.lk-seg.mono button{font-family:var(--mono);font-weight:500}',
      '.lk-kp{display:grid;grid-template-columns:1fr 1fr;gap:8px}.lk-kp label{font-size:11.5px;color:var(--ink3);display:grid;gap:3px}.lk-kp input{padding:5px 7px;font-size:12px}',
      '.lk-chk{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--ink2);cursor:pointer}.lk-chk input{accent-color:var(--brand);width:15px;height:15px;margin:0}',
      '.lk-est{font-size:11.5px;color:var(--ink3)}.lk-est button{font:inherit;font-size:11.5px;color:var(--brand);background:none;border:0;padding:0;cursor:pointer;text-decoration:underline}',
      '.lk-root :focus-visible{outline:2px solid var(--brand);outline-offset:2px}',
      '.lk-stats{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));border:1px solid var(--line);border-radius:10px;overflow:hidden}',
      '.lk-st{padding:8px 10px;border-left:1px solid var(--line);min-width:0}.lk-st:first-child{border-left:0}',
      '.lk-st small{display:block;font-size:11px;color:var(--ink3);line-height:1.3}',
      '.lk-st b{display:block;font-family:var(--mono);font-weight:500;font-size:16px;margin-top:2px;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}',
      '.lk-st span{display:block;font-size:11px;color:var(--ink3);margin-top:2px;line-height:1.3}',
      '.lk-st.ok b{color:var(--ok)}.lk-st.warn b{color:var(--warn)}.lk-st.bad b{color:var(--bad)}',
      '.lk-hw{display:grid;grid-template-columns:272px minmax(0,1fr);gap:12px;align-items:start}',
      '.lk-hw .hwc{border-radius:10px}',
      '.lk-sub{font-size:11.5px;font-weight:600;color:var(--ink2);margin:0 0 4px;display:flex;justify-content:space-between;gap:8px}.lk-sub i{font-style:normal;font-family:var(--mono);font-weight:500;color:var(--ink3)}',
      '.lk-rf{display:block;width:100%;height:auto;max-height:120px;border:1px solid var(--line);border-radius:4px;background:var(--white)}',
      '.lk-sm{display:block;width:100%;height:14px;border:1px solid var(--line);border-radius:4px;margin-top:2px}',
      '.lk-lg{display:flex;flex-wrap:wrap;gap:3px 10px;font-size:10.5px;color:var(--ink3);margin-top:5px}.lk-lg span::before{content:"";display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:4px;vertical-align:-1px;background:var(--c)}',
      '.lk-charts{display:grid;gap:8px;align-content:start}',
      '.lk-ctabs{display:flex;gap:4px}.lk-ctabs button{font:inherit;font-size:12px;font-weight:600;padding:5px 10px;border:1px solid var(--line);border-radius:7px;background:var(--white);color:var(--ink2);cursor:pointer}.lk-ctabs button[aria-pressed=true]{background:var(--brand50);border-color:var(--brand200);color:var(--ink)}',
      '.lk-card{border:1px solid var(--line);border-radius:10px;padding:10px 12px 8px;background:var(--bg)}',
      '.lk-ch{display:block;width:100%;max-width:620px;height:auto}',
      '.lk-grid{stroke:var(--line2);stroke-width:1}.lk-ax{fill:var(--ink3);font-size:8.5px;font-family:var(--mono)}.lk-ax.warn{fill:var(--warn)}.lk-ax.pt{fill:var(--ink);font-weight:500}',
      '.lk-ln{fill:none;stroke:var(--brand);stroke-width:1.8;stroke-linejoin:round}.lk-ln.ghost{stroke:var(--line);stroke-width:1.2}.lk-ln.warn{stroke:var(--warn);stroke-dasharray:4 3}',
      '.lk-cap{stroke:var(--warn);stroke-width:1;stroke-dasharray:3 3}.lk-pt{fill:var(--white);stroke:var(--brand);stroke-width:2.2}',
      '.lk-tbl{width:100%;border-collapse:collapse;font-size:12px}.lk-tbl th{text-align:left;font-size:10.5px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--ink3);padding:6px 8px;border-bottom:1px solid var(--line);white-space:nowrap}',
      '.lk-tbl td{padding:7px 8px;border-bottom:1px solid var(--line2);font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}.lk-tbl td:first-child{font-family:var(--font);font-weight:600;color:var(--ink)}',
      '.lk-tbl tr.on td{background:var(--brand50)}.lk-tbl tr[tabindex]{cursor:pointer}.lk-tbl tr[tabindex]:hover td{background:var(--bg)}.lk-tbl .n{text-align:right}',
      '.lk-tw{overflow-x:auto}',
      '.lk-note{font-size:12px;color:var(--ink2);margin:0}.lk-note code{font-family:var(--mono);font-size:11.5px;background:var(--bg);padding:1px 4px;border-radius:4px}',
      '.lk-root details{border-top:1px solid var(--line);padding-top:10px}.lk-root summary{cursor:pointer;font-weight:600;font-size:13px;color:var(--ink)}',
      '.lk-root details ul{margin:8px 0 0;padding-left:18px;color:var(--ink2);font-size:12.5px}.lk-root details li{margin:4px 0}',
      '.lk-foot{font-size:11.5px;color:var(--ink3);border-top:1px solid var(--line);padding-top:10px}',
      '@media(max-width:1100px){.lk-stats{grid-template-columns:repeat(3,minmax(0,1fr))}.lk-st:nth-child(4){border-left:0}.lk-st:nth-child(n+4){border-top:1px solid var(--line)}}',
      '@media(max-width:900px){.lk-root{grid-template-columns:minmax(0,1fr)}.lk-ctl{border-right:0;border-bottom:1px solid var(--line)}.lk-hw{grid-template-columns:minmax(0,1fr)}}',
      '@media(max-width:480px){.lk-stats{grid-template-columns:1fr 1fr}.lk-st:nth-child(odd){border-left:0}.lk-st:nth-child(n+3){border-top:1px solid var(--line)}.lk-st:nth-child(4){border-left:1px solid var(--line)}.lk-kp{grid-template-columns:1fr}}',
      '@media (prefers-reduced-motion:no-preference){.lk-rf rect,.lk-sm rect{transition:fill .2s}}'
    ].join('\n');
    document.head.appendChild(s);
  }

  /* ───────────────────────────── widget ───────────────────────────── */
  var uid = 0;
  function mount(root) {
    css();
    var id = 'lk' + (++uid), L = window.VO_LAB;   // the demo shell, when there is one: it owns the GPU choice
    var st = { chart: 'occ', gpu: L ? L.gpu : 'h100', kernel: 'rmsnorm', threads: 256, regs: 32, smem: 0, ilp: 2, bpl: 16, lb: false, minBlocks: 2, latency: null, k: {}, over: {} };
    function applyPreset() {
      var K = KERNELS[st.kernel]; st.k = {}; K.params.forEach(function (p) { st.k[p[0]] = p[2]; });
      st.threads = K.defaults.threads; st.ilp = K.defaults.ilp; st.bpl = K.defaults.bpl; st.over = {};
      reEstimate();
    }
    function reEstimate() {
      var e = KERNELS[st.kernel].est(st.k, st);
      if (!st.over.regs) st.regs = Math.min(255, Math.max(8, Math.round(e.regs)));
      if (!st.over.smem) st.smem = Math.round(e.smem);
    }
    applyPreset();

    root.innerHTML = '<div class="lk-root"><form class="lk-ctl" autocomplete="off"></form><div class="lk-res"></div></div>';
    var ctl = root.querySelector('.lk-ctl'), res = root.querySelector('.lk-res');
    ctl.addEventListener('submit', function (e) { e.preventDefault(); });

    function seg(name, opts, cur, fmtf) {
      return '<div class="lk-seg mono" role="group" aria-label="' + esc(name) + '">' + opts.map(function (o) { return '<button type="button" data-seg="' + esc(name) + '" data-v="' + o + '" aria-pressed="' + (o === cur) + '">' + (fmtf ? fmtf(o) : o) + '</button>'; }).join('') + '</div>';
    }
    function buildControls() {
      var K = KERNELS[st.kernel], G = HW.gpus[st.gpu], A = HW.arch[G.arch];
      var maxRegs = A.amd ? 255 : A.maxRegsPerThread, maxSmem = A.amd ? A.ldsPerCU : A.smemPerBlockMax;
      var e = K.est(st.k, st);
      ctl.innerHTML =
        '<div class="lk-h">Kernel lab</div>' +
        (L ? '' : '<div class="lk-f"><label for="' + id + '-gpu">GPU</label><select id="' + id + '-gpu" name="gpu">' + GPU_ORDER.map(function (k) { return '<option value="' + k + '"' + (k === st.gpu ? ' selected' : '') + '>' + esc(HW.gpus[k].name) + '</option>'; }).join('') + '</select></div>') +
        '<div class="lk-f"><span class="lk-lab">Kernel</span><div class="lk-seg" role="group" aria-label="Kernel">' + Object.keys(KERNELS).map(function (k) { return '<button type="button" data-kernel="' + k + '" aria-pressed="' + (k === st.kernel) + '">' + esc(KERNELS[k].name) + '</button>'; }).join('') + '</div></div>' +
        '<div class="lk-f"><span class="lk-lab">Problem</span><div class="lk-kp">' + K.params.map(function (p) { return '<label>' + esc(p[1]) + '<input type="number" name="k:' + p[0] + '" value="' + st.k[p[0]] + '" min="' + p[3] + '" max="' + p[4] + '" step="1"></label>'; }).join('') + '</div></div>' +
        '<div class="lk-f"><span class="lk-lab">Threads per block</span>' + seg('threads', [64, 128, 256, 512, 1024], st.threads) + '</div>' +
        '<div class="lk-f"><label for="' + id + '-regs">Registers per thread <output>' + st.regs + '</output></label><input id="' + id + '-regs" type="range" name="regs" min="8" max="' + maxRegs + '" step="1" value="' + Math.min(st.regs, maxRegs) + '"><div class="lk-est">estimate for this kernel: ' + Math.round(e.regs) + (st.over.regs ? ' · <button type="button" data-reset="regs">use estimate</button>' : '') + '</div></div>' +
        '<div class="lk-f"><label for="' + id + '-smem">Shared memory per block <output>' + kb(st.smem) + '</output></label><input id="' + id + '-smem" type="range" name="smem" min="0" max="' + maxSmem + '" step="1024" value="' + Math.min(st.smem, maxSmem) + '"><div class="lk-est">estimate: ' + kb(Math.round(e.smem)) + (st.over.smem ? ' · <button type="button" data-reset="smem">use estimate</button>' : '') + '</div></div>' +
        '<div class="lk-f"><label for="' + id + '-ilp">Loads in flight per thread <output>' + st.ilp + '</output></label><input id="' + id + '-ilp" type="range" name="ilp" min="1" max="8" step="1" value="' + st.ilp + '"><div class="lk-est">independent loads issued before the first is used (unrolling)</div></div>' +
        '<div class="lk-f"><span class="lk-lab">Bytes per load</span>' + seg('bpl', [4, 8, 16], st.bpl, function (o) { return o + ' B'; }) + '</div>' +
        '<div class="lk-f"><label class="lk-chk"><input type="checkbox" name="lb"' + (st.lb ? ' checked' : '') + '> <span>Cap registers with <code>__launch_bounds__</code></span></label>' + (st.lb ? '<label for="' + id + '-mb">Minimum blocks per SM <output>' + st.minBlocks + '</output></label><input id="' + id + '-mb" type="range" name="minBlocks" min="1" max="8" step="1" value="' + st.minBlocks + '">' : '') + '</div>' +
        '<div class="lk-f"><label for="' + id + '-lat">DRAM latency, ns (assumption)</label><input id="' + id + '-lat" type="number" name="latency" min="100" max="2000" step="10" value="' + (st.latency != null ? st.latency : G.latency) + '"></div>';
    }
    buildControls();

    ctl.addEventListener('input', function (ev) {
      var t = ev.target, n = t.name; if (!n) return;
      if (n === 'gpu') { st.gpu = t.value; st.latency = null; buildControls(); render(); return; }
      if (n.indexOf('k:') === 0) { var v = parseFloat(t.value); if (isFinite(v) && v > 0) { st.k[n.slice(2)] = v; reEstimate(); syncOut(); render(); } return; }
      if (n === 'regs') { st.regs = +t.value; st.over.regs = true; }
      else if (n === 'smem') { st.smem = +t.value; st.over.smem = true; }
      else if (n === 'ilp') { st.ilp = +t.value; reEstimate(); }
      else if (n === 'minBlocks') { st.minBlocks = +t.value; }
      else if (n === 'latency') { var l = parseFloat(t.value); st.latency = isFinite(l) && l > 0 ? l : null; }
      else if (n === 'lb') { st.lb = t.checked; buildControls(); render(); return; }
      syncOut(); render();
    });
    ctl.addEventListener('click', function (ev) {
      var b = ev.target.closest('button'); if (!b) return;
      if (b.dataset.kernel) { st.kernel = b.dataset.kernel; applyPreset(); buildControls(); render(); }
      else if (b.dataset.seg) { var v = +b.dataset.v; st[b.dataset.seg] = v; if (b.dataset.seg === 'threads' || b.dataset.seg === 'bpl') reEstimate(); buildControls(); render(); }
      else if (b.dataset.reset) { st.over[b.dataset.reset] = false; reEstimate(); buildControls(); render(); }
    });
    function syncOut() {
      var r = ctl.querySelector('[name=regs]'); if (r) { r.value = st.regs; r.parentNode.querySelector('output').textContent = st.regs; }
      var s = ctl.querySelector('[name=smem]'); if (s) { s.value = st.smem; s.parentNode.querySelector('output').textContent = kb(st.smem); }
      var i = ctl.querySelector('[name=ilp]'); if (i) i.parentNode.querySelector('output').textContent = st.ilp;
      var m = ctl.querySelector('[name=minBlocks]'); if (m) m.parentNode.querySelector('output').textContent = st.minBlocks;
      var est = KERNELS[st.kernel].est(st.k, st), e1 = ctl.querySelectorAll('.lk-est');
      if (e1[0]) e1[0].innerHTML = 'estimate for this kernel: ' + Math.round(est.regs) + (st.over.regs ? ' · <button type="button" data-reset="regs">use estimate</button>' : '');
      if (e1[1]) e1[1].innerHTML = 'estimate: ' + kb(Math.round(est.smem)) + (st.over.smem ? ' · <button type="button" data-reset="smem">use estimate</button>' : '');
    }

    function render() {
      var E = estimate(st.gpu, st), G = E.G, A = E.A, o = E.occ, K = E.K;
      var unitName = G.sms ? 'SM' : 'CU', U = o.unit;
      var stats =
        '<div class="lk-stats">' +
        tile('Resident ' + U + 's / ' + unitName, o.warps + ' / ' + o.maxWarps, o.blocks + ' block' + (o.blocks === 1 ? '' : 's') + ' × ' + o.warpsPerBlock, o.warps === 0 ? 'bad' : '') +
        tile('Occupancy', pct(o.occ), /full$/.test(o.limiter) ? o.limiter : 'limited by ' + o.limiter, o.occ >= .5 ? 'ok' : o.occ >= .25 ? 'warn' : 'bad') +
        tile('Spilled registers', E.spilled ? E.spilled + ' / thread' : 'none', E.spilled ? '+' + (E.spilled * 8) + ' B local traffic per thread per iteration' : 'cap ' + E.cap + ' per thread', E.spilled ? 'warn' : '') +
        tile('Achievable bandwidth', E.launchable ? fmt(E.achBW / 1e12, 2) + ' TB/s' : 'n/a', E.launchable ? pct(E.achBW / E.peakBW) + ' of peak · ' + si(E.inFlightPerSM, 'B') + ' in flight / ' + unitName : 'no block fits on the ' + unitName, E.achBW / E.peakBW >= .9 ? 'ok' : E.achBW / E.peakBW >= .5 ? 'warn' : 'bad') +
        tile('Bound', E.bound, E.launchable ? fmt(E.ai, E.ai < 10 ? 2 : 0) + ' FLOP/B · ridge at ' + fmt(E.rate / (E.achBW / 1e12), 0) : 'reduce threads, registers or shared memory', E.bound === 'latency' ? 'warn' : E.launchable ? '' : 'bad') +
        tile('Estimated time', tm(E.t), E.launchable ? 'memory ' + tm(E.tMem) + ' · compute ' + tm(E.tComp) : 'kernel cannot run with this launch', '') +
        '</div>';

      var card = HW.card(G, {
        photo: !L,
        sub: A.name + ' · ' + E.units + ' ' + unitName + 's',
        rows: A.amd ? [
          ['VGPR file per CU', fmt(A.vgprPerSIMD * A.simdsPerCU) + ' × 64 lanes'],
          ['Alloc unit', A.vgprAllocUnit + ' VGPRs'],
          ['LDS per CU', kb(A.ldsPerCU)],
          ['Max waves per CU', fmt(A.maxWavesPerSIMD * A.simdsPerCU)],
          ['Max workgroups', A.maxWorkgroupsPerCU],
          ['Peak bandwidth', fmt(G.bw, 2) + ' TB/s'],
          ['Rate used', fmt(E.rate) + ' TFLOPS ' + K.rate],
          ['Latency (assumed)', fmt(E.latency) + ' ns']
        ] : [
          ['Registers per SM', fmt(A.regsPerSM)],
          ['Alloc unit', A.regAllocUnit + ' regs / warp · ' + A.warpAllocGran + ' warps'],
          ['Shared memory per SM', kb(A.smemPerSM) + ' (' + kb(A.smemPerBlockMax) + ' / block)'],
          ['Max warps · blocks', A.maxWarpsPerSM + ' · ' + A.maxBlocksPerSM],
          ['Max registers / thread', A.maxRegsPerThread],
          ['Peak bandwidth', fmt(G.bw, 2) + ' TB/s'],
          ['Rate used', fmt(E.rate) + ' TFLOPS ' + K.rate],
          ['Latency (assumed)', fmt(E.latency) + ' ns']
        ],
        note: A.amd ? 'Simplified CDNA 3 model: VGPR file per SIMD, waves per SIMD, LDS per CU. The compiler also places registers in AGPRs.' : null
      });
      var slot = card.querySelector('.hwc-slot');
      var regsFile = A.amd ? A.vgprPerSIMD * A.simdsPerCU * A.warpSize : A.regsPerSM;
      slot.innerHTML =
        '<p class="lk-sub">Register file <i>' + fmt(o.regsUsed * (A.amd ? A.warpSize : 1)) + ' / ' + fmt(regsFile) + '</i></p>' + regFileSVG(E) +
        '<div class="lk-lg"><span style="--c:var(--brand)">' + o.warps + ' ' + U + 's × ' + fmt(A.amd ? o.regsAlloc : o.regsPerWarpAlloc) + (A.amd ? ' VGPRs' : ' regs') + '</span><span style="--c:var(--brand200)">rounding waste ' + fmt(o.regsWaste * (A.amd ? A.warpSize : 1)) + '</span><span style="--c:var(--line2)">idle ' + fmt(regsFile - o.regsUsed * (A.amd ? A.warpSize : 1)) + (o.limiter === 'registers' ? ' (too few for another ' + U + ')' : /full$/.test(o.limiter) ? '' : ' (' + o.limiter + ' limit)') + '</span></div>' +
        '<p class="lk-sub" style="margin-top:10px">' + (A.amd ? 'LDS per CU' : 'Shared memory per SM') + ' <i>' + o.blocks + ' × ' + kb(o.smemAlloc) + ' / ' + kb(o.smemTotal) + '</i></p>' + smemSVG(E) +
        '<div class="lk-lg"><span style="--c:var(--brand)">block allocation</span>' + (A.amd ? '' : '<span style="--c:var(--ink3)">1 KB reserved per block</span>') + '<span style="--c:var(--line2)">free</span></div>';

      var charts =
        '<div class="lk-charts">' +
        '<div class="lk-ctabs" role="group" aria-label="Chart"><button type="button" data-chart="occ" aria-pressed="' + (st.chart === 'occ') + '">Occupancy against registers</button><button type="button" data-chart="roof" aria-pressed="' + (st.chart === 'roof') + '">Roofline</button></div>' +
        (st.chart === 'occ'
          ? '<div class="lk-card"><p class="lk-sub">Occupancy against registers per thread <i>' + esc(A.name) + ' · ' + st.threads + ' threads · ' + kb(st.smem) + ' smem</i></p>' + occCurveSVG(E, st) + '<div class="lk-lg"><span style="--c:var(--brand)">this architecture</span><span style="--c:var(--line)">the others</span>' + (E.cap < 255 ? '<span style="--c:var(--warn)">above the cap: spilled</span>' : '') + '</div></div>'
          : '<div class="lk-card"><p class="lk-sub">Roofline <i>' + esc(K.name) + ' on ' + esc(G.name) + '</i></p>' + rooflineSVG(E) + '<div class="lk-lg"><span style="--c:var(--line)">peak bandwidth roof</span><span style="--c:var(--warn)">achievable (Little\'s law)</span><span style="--c:var(--brand)">this kernel</span></div></div>') +
        '</div>';

      var rows = GPU_ORDER.map(function (k) {
        var e = estimate(k, st), g = HW.gpus[k];
        return '<tr tabindex="0" data-gpu="' + k + '" class="' + (k === st.gpu ? 'on' : '') + '" aria-selected="' + (k === st.gpu) + '"><td>' + esc(g.name) + '</td><td class="n">' + e.occ.warps + '/' + e.occ.maxWarps + '</td><td class="n">' + pct(e.occ.occ) + '</td><td>' + e.occ.limiter + '</td><td class="n">' + (e.spilled || '–') + '</td><td class="n">' + (e.launchable ? fmt(e.achBW / 1e12, 2) : '–') + ' / ' + fmt(g.bw, 2) + '</td><td>' + e.bound + '</td><td class="n">' + tm(e.t) + '</td></tr>';
      }).join('');
      var table = '<div class="lk-card"><p class="lk-sub">All GPUs, same kernel and launch <i>select a row</i></p><div class="lk-tw"><table class="lk-tbl"><thead><tr><th>GPU</th><th class="n">Resident</th><th class="n">Occupancy</th><th>Limit</th><th class="n">Spills</th><th class="n">Achievable / peak TB/s</th><th>Bound</th><th class="n">Time</th></tr></thead><tbody>' + rows + '</tbody></table></div></div>';

      var w = E.work;
      var details = '<details><summary>How this is calculated</summary><ul>' +
        '<li><b>Occupancy</b> (the CUDA occupancy calculator\'s rules, per compute capability): registers per warp = regs × 32 rounded up to ' + (A.amd ? A.vgprAllocUnit + ' VGPRs per lane' : A.regAllocUnit) + '; warps per SM limited by registers = ⌊' + fmt(A.amd ? A.vgprPerSIMD : A.regsPerSM) + ' ÷ regs per warp⌋' + (A.amd ? ' per SIMD, × 4 SIMDs' : ' rounded down to ' + A.warpAllocGran) + '; shared memory per block = requested + ' + (A.amd ? '0' : A.smemReservedPerBlock + ' B reserved') + ' rounded up to ' + (A.amd ? A.ldsAllocUnit : A.smemAllocUnit) + ' B; blocks per SM = min(by registers, by shared memory, by warps, ' + (A.amd ? A.maxWorkgroupsPerCU : A.maxBlocksPerSM) + '). Resident warps = blocks × ⌈threads ÷ ' + A.warpSize + '⌉.</li>' +
        '<li><b>Register cap</b>: with <code>__launch_bounds__(' + st.threads + ', ' + st.minBlocks + ')</code>, regs ≤ ⌊' + fmt(A.amd ? A.vgprPerSIMD * A.simdsPerCU : A.regsPerSM) + ' ÷ (' + st.minBlocks + ' × ' + roundUp(st.threads, A.warpSize) + ')⌋ rounded down to 8 = ' + regCap(A, st.threads, st.minBlocks) + '. Registers requested above the cap are spilled to local memory: ' + (E.spilled || 0) + ' × 4 B × 2 (store and reload) per thread per iteration, counted as DRAM traffic here, which is a pessimistic upper bound (spills usually hit L1 or L2).</li>' +
        '<li><b>Achievable bandwidth</b> (Little\'s law): bytes in flight per ' + unitName + ' = resident ' + U + 's × ' + A.warpSize + ' lanes × loads in flight × bytes per load = ' + o.warps + ' × ' + A.warpSize + ' × ' + st.ilp + ' × ' + st.bpl + ' = ' + si(E.inFlightPerSM, 'B') + '; achievable = min(peak, in flight × ' + E.units + ' ' + unitName + 's ÷ ' + fmt(E.latency) + ' ns) = ' + fmt(E.achBW / 1e12, 2) + ' TB/s. The latency is an assumption from published microbenchmarks; edit it.</li>' +
        '<li><b>Kernel work</b>: ' + esc(w.text) + '. Here ' + si(w.bytes, 'B') + ' and ' + si(w.flops, 'FLOP') + ' over ' + si(w.threads, 'threads') + ', ' + w.iters + ' iteration' + (w.iters === 1 ? '' : 's') + ' each' + (E.spillBytes ? '; spills add ' + si(E.spillBytes, 'B') : '') + '.</li>' +
        '<li><b>Register estimate</b>: ' + esc(K.regsText) + '. This is an estimate to show the mechanics; <code>ptxas</code> decides the real count. Compile with <code>-Xptxas -v</code> and type the number in.</li>' +
        '<li><b>Time</b> = max(bytes ÷ achievable bandwidth, FLOPs ÷ peak rate) = max(' + tm(E.tMem) + ', ' + tm(E.tComp) + '). Rate used: ' + fmt(E.rate) + ' TFLOPS, ' + esc(K.dtypeNote) + ' (vector FP32 rates are from the datasheets and are not in the catalogue). Bound: compute if the FLOP term is larger; otherwise memory when the achievable bandwidth reaches the peak, latency when it does not. Launch overhead, tail effects, L2 hits and tensor-core pipeline stalls are not modelled.</li>' +
        (A.amd ? '<li><b>CDNA 3</b>: a CU has 4 SIMDs, each with a 512-entry VGPR file per lane and at most 8 waves of 64 lanes; LDS is 64 KB per CU. AGPRs, the unified register file split and wave32 modes are not modelled.</li>' : '') +
        '</ul></details>';

      res.innerHTML = stats + '<div class="lk-hw"><div class="lk-hwcard"></div>' + charts + '</div>' + table + details +
        '<p class="lk-foot">Sim measures the real stall breakdown by interpreting the kernel\'s SASS instruction by instruction, which this estimate does not do.</p>';
      res.querySelector('.lk-hwcard').appendChild(card);
    }
    res.addEventListener('click', function (ev) { var cb = ev.target.closest('[data-chart]'); if (cb) { st.chart = cb.dataset.chart; render(); return; } var tr = ev.target.closest('tr[data-gpu]'); if (tr) choose(tr.dataset.gpu); });
    res.addEventListener('keydown', function (ev) { var tr = ev.target.closest('tr[data-gpu]'); if (tr && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); choose(tr.dataset.gpu); } });
    function choose(k) { if (L) L.select('gpu', k); else pickGpu(k); }   // through the shell, so the carousel follows
    function pickGpu(k) { if (!HW.gpus[k]) return; st.gpu = k; st.latency = null; buildControls(); render(); }
    if (L) L.subscribe(function (m) { if (m.kind === 'gpu' && m.gpu !== st.gpu) pickGpu(m.gpu); });
    function tile(label, value, sub, cls) { return '<div class="lk-st ' + cls + '"><small>' + esc(label) + '</small><b>' + esc(value) + '</b><span>' + esc(sub) + '</span></div>'; }
    render();
  }

  function init() { [].slice.call(document.querySelectorAll('[data-lab="kernel"]')).forEach(function (el) { if (!el.dataset.lkMounted) { el.dataset.lkMounted = '1'; mount(el); } }); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
  /* for tests */
  window.VO_KERNEL_LAB = { occupancy: occupancy, regCap: regCap, estimate: estimate, KERNELS: KERNELS };
})();
