"""Build ../index.html.

site.py is the page; app.py and app.css are the mock app screens. The two are
kept apart so site and app styles never collide, and spliced into one generated
module here (_site_gen.py, ignored by git) so that app.py's icon lookups resolve
against src/icons. Run:  python3 src/build.py
"""
import os, re, runpy
HERE = os.path.dirname(os.path.abspath(__file__))
rd = lambda n: open(os.path.join(HERE, n)).read()
g, parts, css = rd("site.py"), rd("app.py"), rd("app.css")
A = g[:g.index("# ───────────────────────── App shell pieces")]
SITE_CSS = g[g.index("# ───────────────────────── CSS ─"):g.index("/* ════════ App screens")]
E = g[g.index("/* playback */"):]
# the page's live badge belongs to the recorder, not the site; the mocks press their "act" button
E = re.sub(r"\.live\{position:absolute[^\n]*\n", "", E); E = re.sub(r"\.live i\{width:7px[^\n]*\n", "", E); E = re.sub(r"@keyframes vo-pulse\{[^\n]*\n", "", E)
E = E.replace("border:2px solid var(--brand2);pointer-events:none;z-index:5", "border:2px solid var(--pri);pointer-events:none;z-index:5")
E = E.replace("var btn=mock.querySelector('.mb.pri')", "var btn=mock.querySelector('.mb.act')")
E = E.replace('<span class="live"><i></i>Live</span>', '<span class="live"><i></i>REC</span>')
# the icon sprite is built after the page renders, so it holds exactly the icons used
E = E.replace('</defs></svg>\n', '</defs></svg>\n__SPRITE__\n', 1)
E = E.replace('open(OUT, "w").write(HTML.replace("__JSONLD__", jsonld(HTML)))',
              'open(OUT, "w").write(HTML.replace("__SPRITE__", sprite()).replace("__JSONLD__", jsonld(HTML)))')
gen = os.path.join(HERE, "_site_gen.py")
open(gen, "w").write(A + parts + "\n" + SITE_CSS + css + E)
runpy.run_path(gen, run_name="__main__")
