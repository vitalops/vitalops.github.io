// The home hero's top right corner peels back to show the other side of VitalOps: AI agents for
// operations, with a link to /e2e. Adapted from the scramjit and cimo sites' Prompt for Agents.
(function () {
  var ROBOT = '<svg class="i-robot" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v4"/><circle cx="12" cy="3" r=".6"/><rect x="4" y="7" width="16" height="13" rx="3"/><path d="M1.5 12.5v3M22.5 12.5v3M9 16h6"/><circle class="eye" cx="9" cy="11.5" r="1.2"/><circle class="eye eye-r" cx="15" cy="11.5" r="1.2"/></svg>';
  var LABEL = '<span class="peel-label">AI agents for operations</span>';
  var banner = document.querySelector('.banner');

  var phone = matchMedia('(max-width:600px)');
  var REST = phone.matches ? 32 : 42, HOVER = REST + 10, TIP = 96;
  var SHARE = 0.4, ROLL = phone.matches ? 44 : 70;  // how much of the banner peels, and how wide the fold rolls up
  var base = new URL('../peel/', document.currentScript.src).href;
  var TILES = [['manufacturing', 'Manufacturing'], ['supply-chain', 'Supply chain'], ['logistics', 'Logistics'],
    ['healthcare', 'Healthcare'], ['insurance', 'Insurance'], ['finance', 'Finance']].map(function (t) {
    return '<a href="e2e/#' + t[0] + '"><img src="' + base + t[0] + '.webp" alt="" loading="lazy"><span>' + t[1] + '</span></a>';
  }).join('');
  var front = banner && banner.querySelector('.banner-front');
  if (!banner) return;

  var back = document.createElement('div');
  back.className = 'rip-back';
  back.id = 'agents';
  back.inert = true;
  back.innerHTML = '<div class="rip-in"><div class="rip-bar"><span class="rip-k">The other side of VitalOps</span>' +
    '<button type="button" class="rip-close">Close</button></div>' +
    '<h2>AI agents for operations</h2>' +
    '<p class="rip-about">We also build agents that do routine operations work in manufacturing, supply chain, logistics, healthcare, insurance and finance. They work inside your systems and hand anything unclear to a person.</p>' +
    '<div class="rip-tiles">' + TILES + '</div>' +
    '<a class="rip-go" href="e2e/">See the agents at work<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7M8 7h9v9"/></svg></a></div>';
  banner.insertBefore(back, front || null);

  var flap = document.createElement('div');
  flap.className = 'rip-flap';
  flap.innerHTML = '<i></i>';
  banner.appendChild(flap);
  var paper = flap.firstChild;

  var peel = document.createElement('button');
  peel.type = 'button';
  peel.className = 'peel';
  peel.setAttribute('aria-label', 'AI agents for operations');
  peel.setAttribute('aria-expanded', 'false');
  peel.setAttribute('aria-controls', 'agents');
  peel.innerHTML = '<span class="peel-under"></span><i class="peel-hit"></i>' + LABEL;
  banner.appendChild(peel);

  // One robot, in the corner the whole time: always inside the part that has peeled.
  var robot = document.createElement('span');
  robot.className = 'rip-robot';
  robot.innerHTML = ROBOT;
  banner.appendChild(robot);

  var go = back.querySelector('.rip-go');

  // Folding the corner to (W - q, q) creases the banner along y = x - W + q. The part above the
  // crease is gone from the front and shows, reflected across the crease, as the flap.
  var q = REST, isOpen = false, raf = 0, drag = null;
  var points = function (ps) { return ps.length ? 'polygon(' + ps.map(function (p) { return p[0] + 'px ' + p[1] + 'px'; }).join(',') + ')' : 'polygon(0 0)'; };
  function cut(poly, d) {
    var out = [];
    poly.forEach(function (a, i) {
      var b = poly[(i + 1) % poly.length], da = d(a), db = d(b);
      if (da >= 0) out.push(a);
      if (da * db < 0) { var t = da / (da - db); out.push([a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])]); }
    });
    return out;
  }
  function draw(v) {
    q = v;
    var W = banner.clientWidth, H = banner.clientHeight, rect = [[0, 0], [W, 0], [W, H], [0, H]];
    var below = function (p) { return p[1] - p[0] + W - q; };
    var gone = cut(rect, function (p) { return -below(p); });
    // Without a banner nothing is cut from the page: the prompt covers that part of it instead, so
    // the page can go on scrolling under a crease that stays put.
    if (front) front.style.clipPath = points(cut(rect, below)); else back.style.clipPath = points(gone);
    var flipped = gone.map(function (p) { return [p[1] + W - q, p[0] - W + q]; });
    paper.style.clipPath = points(cut(flipped, function (p) { return ROLL * Math.SQRT2 - below(p); }));
    paper.style.setProperty('--crease', q / Math.SQRT2 + 'px');
    var size = Math.min(q, TIP);
    peel.style.width = peel.style.height = size + 'px';
  }
  // Open, the crease stops where SHARE of the banner has peeled or just short of the headline and
  // lede, whichever comes first, unless the prompt's panel needs more room, as on a phone. The
  // panel fits exactly above the crease.
  var panel = back.querySelector('.rip-in'), TOP = 16, EDGE = 14;
  function peeled(v, W, H) {
    var d = function (p) { return p[0] - p[1] - W + v; };
    var ps = cut([[0, 0], [W, 0], [W, H], [0, H]], d), area = 0;
    ps.forEach(function (a, i) { var b = ps[(i + 1) % ps.length]; area += a[0] * b[1] - b[0] * a[1]; });
    return Math.abs(area) / 2 / (W * H);
  }
  function clearOfCopy(W) {
    var box = banner.getBoundingClientRect(), range = document.createRange(), limit = Infinity;
    banner.querySelectorAll('.phero-copy h1, .phero-copy .lede').forEach(function (el) {
      range.selectNodeContents(el);
      [].forEach.call(range.getClientRects(), function (r) {
        limit = Math.min(limit, r.top - box.top + W - (r.right - box.left) - ROLL * Math.SQRT2 - 8);
      });
    });
    return limit;
  }
  function full() {
    var W = banner.clientWidth, H = banner.clientHeight, lo = 0, hi = W + H, side = phone.matches ? 16 : 24;
    for (var i = 0; i < 24; i++) { var m = (lo + hi) / 2; if (peeled(m, W, H) < SHARE) lo = m; else hi = m; }
    var gaps = side + TOP + EDGE, maxW = W - 2 * side, maxH = H - 2 * TOP;
    var v = Math.max(Math.min(lo, clearOfCopy(W)), Math.min(maxW, 340) + Math.min(maxH, 420) + gaps);
    var pw = Math.min(maxW, Math.round((v - gaps) * 0.5)), ph = Math.min(maxH, v - gaps - pw);
    panel.style.cssText = 'top:' + TOP + 'px;right:' + side + 'px;width:' + pw + 'px;height:' + ph + 'px';
    return v;
  }
  var still = matchMedia('(prefers-reduced-motion:reduce)');
  function move(to, ms, done) {
    cancelAnimationFrame(raf);
    if (still.matches) { draw(to); if (done) done(); return; }
    var from = q, t0 = performance.now();
    (function step(now) {
      var t = Math.min(1, (now - t0) / ms), e = 1 - Math.pow(1 - t, 3);
      draw(from + (to - from) * e);
      if (t < 1) raf = requestAnimationFrame(step); else if (done) done();
    })(t0);
  }

  function open(instant) {
    isOpen = true;
    back.inert = false;
    peel.setAttribute('aria-expanded', 'true');
    var end = function () { peel.hidden = true; banner.classList.add('is-open'); if (!instant) go.focus({ preventScroll: true }); };
    if (instant) { draw(full()); end(); } else move(full(), 650, end);
  }
  function close() {
    isOpen = false;
    back.inert = true;
    banner.classList.remove('is-open');
    peel.hidden = false;
    peel.setAttribute('aria-expanded', 'false');
    move(REST, 550, function () { peel.focus({ preventScroll: true }); });
  }

  // Opens on a click, or when let go past about a third of the way. Letting go any sooner, dragging
  // back, or Esc cancels: the corner falls back.
  peel.addEventListener('pointerdown', function (e) {
    if (e.button || isOpen) return;
    cancelAnimationFrame(raf);
    drag = { x: e.clientX, y: e.clientY, q: q, moved: 0, most: 0, id: e.pointerId };
    peel.setPointerCapture(e.pointerId);
    peel.classList.add('pulling');
  });
  peel.addEventListener('pointermove', function (e) {
    if (!drag) return;
    drag.moved = Math.max(0, (drag.x - e.clientX + e.clientY - drag.y) / 2);
    drag.most = Math.max(drag.most, Math.abs(drag.x - e.clientX) + Math.abs(e.clientY - drag.y));
    draw(Math.min(drag.q + drag.moved, full()));
  });
  peel.addEventListener('pointerup', function () {
    if (!drag) return;
    var clicked = drag.most < 6, far = q >= full() / 3;
    drag = null;
    peel.classList.remove('pulling');
    if (clicked || far) open(); else move(REST, 300);
  });
  function cancel() {
    if (!drag) return;
    if (peel.hasPointerCapture(drag.id)) peel.releasePointerCapture(drag.id);
    drag = null;
    peel.classList.remove('pulling');
    move(REST, 300);
  }
  peel.addEventListener('pointercancel', cancel);
  peel.addEventListener('click', function (e) { if (e.detail === 0 && !isOpen) open(); });  // keyboard
  peel.addEventListener('pointerenter', function (e) { if (e.pointerType === 'mouse' && !drag && !isOpen) move(HOVER, 150); });
  peel.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse' && !drag && !isOpen) move(REST, 150); });
  peel.addEventListener('focus', function () { if (peel.matches(':focus-visible') && !isOpen) move(HOVER, 150); });
  peel.addEventListener('blur', function () { if (!drag && !isOpen) move(REST, 150); });

  back.querySelector('.rip-close').addEventListener('click', close);
  // A click on what's left of the banner puts it back, unless it's on a link or button, or selects text.
  (front || document).addEventListener('click', function (e) {
    if (isOpen && !back.contains(e.target) && !e.target.closest('a, button') && !String(getSelection())) close();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (drag) cancel(); else if (isOpen) close();
  });
  if ('ResizeObserver' in window) new ResizeObserver(function () { if (!drag) draw(isOpen ? full() : q); }).observe(banner);
  full();
  draw(REST);
  if (location.hash === '#agents') open(true);
})();
