"""Build the /e2e pitch page: python3 src/e2e/build.py

Edit page.html, industries.py and e2e.css here, then run this. It writes e2e/index.html and e2e/e2e.css, inlines
the Lucide icons the page uses (<i data-i="name"></i>) as one SVG sprite, and runs the copy checker.
This page is separate from the main site's generator (src/build.py) and shares nothing with it.
"""
import hashlib, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
ICONS = os.path.join(HERE, "..", "icons", "lucide")

page = open(os.path.join(HERE, "page.html"), encoding="utf-8").read()
css = open(os.path.join(HERE, "e2e.css"), encoding="utf-8").read()
sys.path.insert(0, HERE)
import industries  # noqa: E402
page = page.replace("__INDUSTRIES__", industries.render())
hero_bg, hero_car = industries.hero()
page = page.replace("__HERO_BG__", hero_bg).replace("__HERO_CAR__", hero_car)

used = sorted(set(re.findall(r'<i data-i="([a-z0-9-]+)"></i>', page)))
symbols = []
for name in used:
    path = os.path.join(ICONS, name + ".svg")
    if not os.path.exists(path):
        sys.exit(f"unknown icon: {name}")
    svg = open(path, encoding="utf-8").read()
    inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    inner = re.sub(r"\s+", " ", inner).strip()
    symbols.append(f'<symbol id="i-{name}" viewBox="0 0 24 24">{inner}</symbol>')
sprite = f'<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>{"".join(symbols)}</defs></svg>'

page = re.sub(r'<i data-i="([a-z0-9-]+)"></i>', r'<svg class="ic" aria-hidden="true"><use href="#i-\1"/></svg>', page)
page = page.replace("__SPRITE__", sprite).replace("__CSSV__", hashlib.sha1(css.encode()).hexdigest()[:10])

out = os.path.join(ROOT, "e2e")
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page)
open(os.path.join(out, "e2e.css"), "w", encoding="utf-8").write(css)
print(f"e2e: {len(used)} icons")
sys.exit(subprocess.call([sys.executable, os.path.join(ROOT, "src", "tools", "copy_tells.py"), os.path.join(out, "index.html")]))
