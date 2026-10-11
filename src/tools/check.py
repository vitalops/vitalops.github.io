"""Sanity checks on the built page: no console errors and no horizontal overflow on desktop and phone.
Needs Playwright with Chromium."""
import os
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
url = "file://" + os.path.join(ROOT, "index.html")
ok = True
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, w in (("desktop", 1366), ("tablet", 768), ("phone", 390), ("small phone", 360)):
        pg = b.new_page(viewport={"width": w, "height": 900}); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
        pg.goto(url); pg.wait_for_timeout(1500)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        good = sw <= w and not errs; ok &= good
        print(f"{name:12} {w}px  scrollWidth={sw}  errors={errs or 'none'}  {'OK' if good else 'FAIL'}"); pg.close()
    b.close()
raise SystemExit(0 if ok else 1)
