"""Render the PNG favicons, the Apple touch icon and the social card from assets/vo-mark.svg and src/og.html.
Needs Playwright with Chromium:  pip install playwright && playwright install chromium"""
import os, tempfile
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = os.path.join(ROOT, "assets")
mark = open(os.path.join(A, "vo-mark.svg")).read()
with sync_playwright() as p, tempfile.TemporaryDirectory() as tmp:
    b = p.chromium.launch()
    open(os.path.join(tmp, "round.svg"), "w").write(mark)
    open(os.path.join(tmp, "square.svg"), "w").write(mark.replace('rx="30"', 'rx="0"'))  # iOS applies its own corner mask
    for size, name, svg, bg in ((32, "favicon-32.png", "round", "transparent"), (192, "icon-192.png", "round", "transparent"),
                                (512, "icon-512.png", "round", "transparent"), (180, "apple-touch-icon.png", "square", "#3f5cf6")):
        pg = b.new_page(viewport={"width": size, "height": size})
        pg.set_content(f'<body style="margin:0;background:{bg}"><img src="file://{tmp}/{svg}.svg" width="{size}" height="{size}" style="display:block"></body>')
        pg.wait_for_timeout(200); pg.screenshot(path=os.path.join(A, name), omit_background=(bg == "transparent")); pg.close()
    pg = b.new_page(viewport={"width": 1200, "height": 630}); pg.goto("file://" + os.path.join(ROOT, "src", "og.html")); pg.wait_for_timeout(1500)
    pg.screenshot(path=os.path.join(A, "og.png")); b.close()
print("icons and social card written to assets/")
