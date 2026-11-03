// Renders each product's app screen to assets/screens/<product>.webp for the product tiles.
// The screens are captured in their finished state (reduced motion skips the playback).
// Needs playwright-core and a running static server over the repo's parent:
//   python3 -m http.server 4190 --directory ..   then   node src/tools/render_screens.mjs [base-url] [chromium]
import { chromium } from 'playwright-core';
const base = process.argv[2] || 'http://localhost:4190/vitalops.github.io/';
const exe = process.argv[3];
const SHOTS = { plan: '#fig-plan', optimize: '#fig-opt', sim: '#fig-sim', serve: '#serve-pools', edge: '#fig-edge', fleet: '#fig-fleet' };
const b = await chromium.launch(exe ? { executablePath: exe } : {});
const p = await b.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1, reducedMotion: 'reduce' });
for (const [k, sel] of Object.entries(SHOTS)) {
  await p.goto(base + 'products/' + k + '/', { waitUntil: 'load' });
  await p.evaluate(s => { const m = document.querySelector(s), f = m.closest('.frame'); f.style.width = '1132px'; f.style.maxWidth = 'none'; m.style.setProperty('--s', '1'); m.style.boxShadow = 'none'; }, sel);
  await p.waitForTimeout(300);
  await p.locator(sel).screenshot({ path: `assets/screens/${k}.png` });
}
await b.close();
