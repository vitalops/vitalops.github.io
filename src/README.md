# Site source

`index.html` is generated. Edit the files here, then rebuild:

```sh
python3 src/build.py          # writes ../index.html; needs only Python 3
```

| File | What it is |
|---|---|
| `site.py` | The page: copy, sections, site CSS, the playback and carousel scripts. |
| `app.py` | The mock app screens shown in the hero and walkthrough: fixed 1132×708 canvases, scaled by the page, never reflowed. |
| `app.css` | Styles for those screens. The app palette is scoped to `.mock` so it never leaks into the site. |
| `build.py` | Splices the three into one generated module (`_site_gen.py`, git-ignored) and runs it. |
| `icons/` | Lucide icons and brand marks, inlined as an SVG sprite that holds only the icons the page uses. See `icons/LICENSES.md`. |
| `og.html` | Source of the social card. |
| `tools/render_icons.py` | Renders the PNG favicons, the Apple touch icon and `assets/og.png` from `assets/vo-mark.svg` and `og.html`. |
| `tools/check.py` | Console errors and horizontal overflow at four widths. |
| `tools/a11y.py` | axe-core, WCAG 2.2 AA, on desktop and phone. Exit code 1 on any violation. |

The tools need Playwright (`pip install playwright && playwright install chromium`); the build does not.

Conventions worth keeping:

- Site and app share no class names. A collision shows up as one side's styles bleeding into the other.
- Everything the mocks do on screen is scripted playback driven by `data-step` attributes; nothing is recorded.
- The photos under `assets/stock/` are from Pexels under the Pexels licence, which needs no attribution.
