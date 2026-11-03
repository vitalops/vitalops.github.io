# Site source

Every page (`index.html`, `products/`, `solutions/`, `lab/`, `platform/`, `services/`, `security/`, `company/`, `credits/`) and the shared files under `assets/css/` and `assets/js/site.js`, `assets/js/play.js` are generated. Edit the files here, then rebuild:

```sh
python3 src/build.py          # writes every page; needs only Python 3
```

| File | What it is |
|---|---|
| `site.py` | The page: copy, sections, site CSS, the playback and carousel scripts. |
| `app.py` | The mock app screens shown in the hero and walkthrough: fixed 1132×708 canvases, scaled by the page, never reflowed. |
| `app.css` | Styles for those screens. The app palette is scoped to `.mock` so it never leaks into the site. |
| `build.py` | Splices the three into one generated module (`_site_gen.py`, git-ignored), runs it, then hands its parts to `pages.py`. |
| `pages.py` | The company site: navigation, footer, the home page, product, solution and demo pages, and the Plan screen. Writes the shared CSS and JS with a content hash on each link. |
| `pages.css`, `pages.js` | Styles and the small nav and lifecycle script for those pages. |
| `photo_credits.json` | Source and licence of each photo under `assets/photos/`; the credits page is built from it. |
| `../assets/js/hw.js` | The hardware catalogue the demos share: public specs per GPU and device, the compute-capability rules for the occupancy calculator, the photo card and the memory drawing. Every figure is from a datasheet or is marked as an assumption. |
| `../assets/js/lab-shell.js` | The demo shell: a dark panel with the hardware carousel as the selector and one tab per demo (`<div data-lab-shell data-tabs="planner,kernel">`). Demos read the selection from `window.VO_LAB`. |
| `../assets/js/lab-*.js` | The six live demos (planner, batching, kernel, quant, specdec, edgefit). Hand-written; each mounts on `[data-lab="name"]` and reads `window.VO_HW`. |
| `icons/` | Lucide icons and brand marks, inlined as an SVG sprite that holds only the icons the page uses. See `icons/LICENSES.md`. |
| `og.html` | Source of the social card. |
| `tools/render_icons.py` | Renders the PNG favicons, the Apple touch icon and `assets/og.png` from `assets/vo-mark.svg` and `og.html`. |
| `tools/render_screens.mjs` | Renders each product's app screen to `assets/screens/` for the product tiles. Rerun after changing a screen. |
| `tools/check.py` | Console errors and horizontal overflow at four widths. |
| `tools/a11y.py` | axe-core, WCAG 2.2 AA, on desktop and phone. Exit code 1 on any violation. |

The tools need Playwright (`pip install playwright && playwright install chromium`); the build does not.

Conventions worth keeping:

- Site and app share no class names. A collision shows up as one side's styles bleeding into the other.
- Everything the mocks do on screen is scripted playback driven by `data-step` attributes; nothing is recorded.
- The photos under `assets/stock/` are from Pexels under the Pexels licence, which needs no attribution. The photos under `assets/photos/` are from Wikimedia Commons; several are CC BY or CC BY-SA, so keep the credits page linked from the footer.
- The live demos are estimators built on first-order physics. They never quote a VitalOps result.
