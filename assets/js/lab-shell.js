/* The demo shell (assets/js/lab-shell.js): a dark panel with the hardware carousel as the selector and one tab per demo.

   <div class="lab" data-lab-shell data-tabs="planner,batching,kernel" data-gpu="h100" data-device="orin_nano"></div>

   It builds a mount <div data-lab="name"> for each tab; the demo scripts (loaded after this one) render into them.
   Demos read the selection from window.VO_LAB and subscribe to changes; a demo running without a shell keeps its own selector.

   window.VO_LAB = { gpu, device, select(kind, key), subscribe(fn) -> unsubscribe }   fn({ kind, gpu, device, spec })
*/
(function () {
  'use strict';
  var HW = window.VO_HW; if (!HW) return;
  var TABS = {
    planner:  { label: 'Capacity planner', kind: 'gpu' },
    batching: { label: 'Batching simulator', kind: 'gpu' },
    kernel:   { label: 'Kernel lab', kind: 'gpu' },
    quant:    { label: 'Quantisation lab', kind: 'gpu' },
    specdec:  { label: 'Speculative decoding', kind: 'gpu' },
    edgefit:  { label: 'Edge fit', kind: 'device' }
  };
  var state = { gpu: 'h100', device: 'orin_nano' }, subs = [];
  function notify(kind) {
    var msg = { kind: kind, gpu: state.gpu, device: state.device, spec: kind === 'device' ? HW.devices[state.device] : HW.gpus[state.gpu] };
    subs.slice().forEach(function (f) { try { f(msg); } catch (e) { if (window.console) console.error(e); } });
    document.dispatchEvent(new CustomEvent('vo:hw', { detail: msg }));
  }
  window.VO_LAB = {
    get gpu() { return state.gpu; }, get device() { return state.device; },
    select: function (kind, key) {
      if (kind === 'device' ? !HW.devices[key] : !HW.gpus[key]) return;
      state[kind] = key; shells.forEach(function (sh) { if (sh.car.current().kind === kind) sh.car.select(key, true); }); notify(kind);
    },
    subscribe: function (f) { subs.push(f); return function () { var i = subs.indexOf(f); if (i >= 0) subs.splice(i, 1); }; }
  };

  var css = document.createElement('style'); css.id = 'lab-shell-css';
  css.textContent = [
    /* the dark scope: the demos read these variables, so they recolour without their own dark styles */
    '.vlab{--bg:#0b1020;--white:#111a30;--ink:#e8ecf5;--ink2:#c3cbdc;--ink3:#8e9ab3;--ink4:#5f6b85;--line:#263252;--line2:#1b2440;--brand50:#1a2452;--brand100:#243576;--brand200:#3b50a8;--brandD:#8fa3ff;color-scheme:dark;',
    '  background:#0b1020;color:var(--ink2);border:1px solid #1f2a44;border-radius:16px;overflow:hidden;font-family:var(--font);scroll-margin-top:78px}',
    '.vlab-head{padding:8px 12px 4px;border-bottom:1px solid #1f2a44;background:#0d1428}',
    '.vlab-head .hwcar-it{background:#0f1730;border-color:#263252;flex-basis:156px;padding:5px 5px 6px}',
    '.vlab-head .hwcar-it .hwc-ph{aspect-ratio:2/1}',
    '.vlab-head .hwcar-track{padding:4px 4px}',
    '.vlab-head .hwcar-ar{background:#0f1730;border-color:#263252;color:#c3cbdc}',
    '.vlab-tabs{display:flex;gap:2px;padding:8px 14px 0;overflow-x:auto;scrollbar-width:none;border-bottom:1px solid #1f2a44;background:#0d1428}',
    '.vlab-tabs::-webkit-scrollbar{display:none}',
    '.vlab-tab{appearance:none;background:none;border:0;border-bottom:2px solid transparent;padding:9px 12px 10px;font:600 13.5px/1 var(--font);color:#8e9ab3;cursor:pointer;white-space:nowrap;margin-bottom:-1px}',
    '.vlab-tab:hover{color:#e8ecf5}.vlab-tab[aria-selected=true]{color:#fff;border-bottom-color:var(--brand)}',
    '.vlab-tab:focus-visible{outline:2px solid var(--brand);outline-offset:-2px;border-radius:6px}',
    '.vlab-body{position:relative;height:var(--lab-h,640px);overflow:auto;overscroll-behavior:contain;scrollbar-width:thin;scrollbar-color:#2a365a #0b1020}',
    '.vlab-panel{padding:12px}',
    '.vlab-panel[hidden]{display:none}',
    '.vlab-note{padding:5px 14px 7px;font-size:11px;color:#5f6b85;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;border-top:1px solid #1f2a44}',
    '.vlab-note b{font-weight:500;color:#8e9ab3}',
    '.vlab .hwc{background:#111a30}',
    '.vlab input,.vlab select,.vlab button{color-scheme:dark}',
    '@media(max-width:600px){.vlab-head{padding:8px 8px 4px}.vlab-panel{padding:8px}.vlab-note span+span{display:none}}'
  ].join('\n');
  document.head.appendChild(css);

  var shells = [];
  function build(root) {
    var tabs = (root.getAttribute('data-tabs') || Object.keys(TABS).join(',')).split(',').map(function (s) { return s.trim(); }).filter(function (t) { return TABS[t]; });
    if (!tabs.length) return;
    if (root.getAttribute('data-gpu') && HW.gpus[root.getAttribute('data-gpu')]) state.gpu = root.getAttribute('data-gpu');
    if (root.getAttribute('data-device') && HW.devices[root.getAttribute('data-device')]) state.device = root.getAttribute('data-device');
    root.classList.add('vlab'); root.innerHTML = '';
    var head = document.createElement('div'); head.className = 'vlab-head';
    var first = tabs[0], kind0 = TABS[first].kind;
    var car = HW.carousel(kind0, kind0 === 'device' ? state.device : state.gpu, function (kind, key) { state[kind] = key; shells.forEach(function (sh) { if (sh.car !== car && sh.car.current().kind === kind) sh.car.select(key, true); }); notify(kind); });
    head.appendChild(car); root.appendChild(head);
    var bar = document.createElement('div'); bar.className = 'vlab-tabs'; bar.setAttribute('role', 'tablist');
    var body = document.createElement('div'); body.className = 'vlab-body';
    var panels = {};
    tabs.forEach(function (t, i) {
      var b = document.createElement('button'); b.className = 'vlab-tab'; b.type = 'button'; b.setAttribute('role', 'tab'); b.id = 'vlab-t-' + t + '-' + shells.length;
      b.setAttribute('aria-selected', i === 0 ? 'true' : 'false'); b.tabIndex = i === 0 ? 0 : -1; b.textContent = TABS[t].label; b.setAttribute('data-tab', t);
      bar.appendChild(b);
      var p = document.createElement('div'); p.className = 'vlab-panel'; p.setAttribute('role', 'tabpanel'); p.setAttribute('aria-labelledby', b.id); p.id = 'vlab-p-' + t + '-' + shells.length;
      b.setAttribute('aria-controls', p.id);
      if (i) p.hidden = true;
      var m = document.createElement('div'); m.setAttribute('data-lab', t); p.appendChild(m); body.appendChild(p); panels[t] = { btn: b, panel: p };
    });
    if (tabs.length > 1) root.appendChild(bar);
    root.appendChild(body);
    var note = document.createElement('div'); note.className = 'vlab-note';
    note.innerHTML = '<span><b>Estimates from public specifications.</b> Every formula is under "How this is calculated" in each demo; nothing here is a measurement of a VitalOps product.</span><span>Pick the hardware above; the demo follows.</span>';
    root.appendChild(note);
    var active = first;
    function show(t, focus) {
      if (!panels[t]) return;
      active = t;
      tabs.forEach(function (k) { var on = k === t; panels[k].btn.setAttribute('aria-selected', on); panels[k].btn.tabIndex = on ? 0 : -1; panels[k].panel.hidden = !on; });
      var kind = TABS[t].kind; car.setKind(kind, kind === 'device' ? state.device : state.gpu);
      body.scrollTop = 0;
      if (focus) panels[t].btn.focus();
      window.dispatchEvent(new Event('resize'));
    }
    bar.addEventListener('click', function (e) { var b = e.target.closest('.vlab-tab'); if (b) show(b.getAttribute('data-tab')); });
    bar.addEventListener('keydown', function (e) { var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0; if (!d) return; e.preventDefault(); var i = tabs.indexOf(active); show(tabs[(i + d + tabs.length) % tabs.length], true); });
    /* deep link: /lab/#kernel opens that tab */
    function fromHash() { var h = location.hash.replace('#', ''); if (panels[h]) { show(h); setTimeout(function () { root.scrollIntoView({ block: 'start', behavior: 'auto' }); }, 0); } }
    addEventListener('hashchange', fromHash); fromHash();
    /* height: the panel fits the window under the site header; the demo scrolls inside if it is taller */
    function fit() { var h = Math.max(520, Math.min(900, innerHeight - 62 - head.offsetHeight - (tabs.length > 1 ? bar.offsetHeight : 0) - note.offsetHeight - 16)); root.style.setProperty('--lab-h', h + 'px'); }
    fit(); addEventListener('resize', fit);
    shells.push({ root: root, car: car, show: show });
  }
  function init() { [].forEach.call(document.querySelectorAll('[data-lab-shell]'), build); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
