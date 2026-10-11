"""Run axe-core (WCAG 2.2 AA + best practices) against the built page on desktop and phone.
Needs Playwright with Chromium and network access for axe-core itself."""
import os, urllib.request
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
url = "file://" + os.path.join(ROOT, "index.html")
axe = urllib.request.urlopen("https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js").read().decode()
total = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, vp in (("desktop", {"width": 1366, "height": 900}), ("phone", {"width": 390, "height": 844})):
        pg = b.new_page(viewport=vp); pg.goto(url); pg.wait_for_timeout(800); pg.add_script_tag(content=axe)
        r = pg.evaluate("axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']}})")
        print(f"== {name}: {len(r['violations'])} violation types"); total += len(r["violations"])
        for v in r["violations"]:
            print(f"  [{v['impact']}] {v['id']}: {v['help']} ({len(v['nodes'])} nodes)")
            for n in v["nodes"][:3]: print("      -", n["target"][0][:100])
        pg.close()
    b.close()
raise SystemExit(0 if total == 0 else 1)
