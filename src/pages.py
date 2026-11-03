"""Every page of the site, laid out from the parts site.py and app.py make.

build.py runs the spliced module (the screens, the site and app styles, the playback and carousel
scripts) and hands its globals to build(). Shared CSS and JS are written once under assets/ with a
content hash on the link, so a change reaches browsers instead of being served from cache.
Copy lives here; the content of each mock screen lives in app.py (and SCREEN_PLAN below)."""
import hashlib, html as H, json, os, re

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
BOOK = "https://calendly.com/abhijith-vitalops/30min"
MAIL = "hello@vitalops.ai"
G = {}

def ic(name, cls=""):
    return G["ic"](name, cls)

def lg(slug, cls=""):
    return G["lg"](slug, cls)

# ───────────────────────── catalogue ─────────────────────────
PRODUCTS = {
 "plan":     dict(name="Plan", icon="gauge", short="Capacity and hardware planning"),
 "optimize": dict(name="Optimize", icon="zap", short="Agentic inference optimisation"),
 "sim":      dict(name="Sim", icon="cpu", short="Kernel work without a GPU"),
 "serve":    dict(name="Serve", icon="server", short="Model serving and monitoring"),
 "edge":     dict(name="Edge", icon="smartphone", short="On-device models and training"),
 "fleet":    dict(name="Fleet", icon="bot", short="Agent fleets on your GPUs"),
}
SOLUTIONS = {
 "llm-apis":   dict(name="LLM products and APIs", icon="message-square", short="Chat, copilots and model APIs"),
 "agents":     dict(name="AI agents", icon="workflow", short="Long prefixes, sub-agents, tool calls"),
 "multimodal": dict(name="Vision and multimodal", icon="image", short="VLMs, documents, speech"),
 "robotics":   dict(name="Robotics and devices", icon="scan", short="Models that run in the field"),
 "gpu-clouds": dict(name="GPU clouds", icon="cloud", short="More tokens per GPU you rent out"),
 "on-prem":    dict(name="Regulated and on-prem", icon="shield-check", short="Air-gapped, in your data centre"),
}
DEMOS = {
 "planner":  ("Capacity planner", "How many GPUs, of which kind, and what each million tokens costs.", "gauge"),
 "batching": ("Batching simulator", "Why the scheduler decides your time to first token.", "layers"),
 "quant":    ("Quantisation lab", "What FP8, INT4 and NVFP4 do to real weight distributions.", "boxes"),
 "specdec":  ("Speculative decoding", "Draft, verify, and the speed-up you get per acceptance rate.", "zap"),
 "edgefit":  ("Edge fit", "The largest model that fits a Jetson, a phone or a Pi.", "smartphone"),
}

# ───────────────────────── shell ─────────────────────────
def asset(path):
    """Link to a file under the repo root with a content hash, so browsers refetch it when it changes."""
    h = hashlib.sha1(open(os.path.join(ROOT, path), "rb").read()).hexdigest()[:10]
    return f"{path}?v={h}"

def head(title, desc, root, url, jsonld=""):
    css = "".join(f'<link rel="stylesheet" href="{root}{asset(p)}">' for p in ("assets/css/vo.css", "assets/css/pages.css"))
    return f"""<!DOCTYPE html>
<html lang="en" style="color-scheme:light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light">
<title>{title}</title>
<meta name="description" content="{H.escape(desc)}">
<link rel="canonical" href="https://vitalops.ai/{url}">
<meta name="theme-color" content="#f5f6fa">
<link rel="icon" type="image/svg+xml" href="{root}assets/vo-mark.svg">
<link rel="icon" type="image/png" sizes="32x32" href="{root}assets/favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="{root}assets/icon-192.png">
<link rel="apple-touch-icon" sizes="180x180" href="{root}assets/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="VitalOps">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{H.escape(desc)}">
<meta property="og:url" content="https://vitalops.ai/{url}">
<meta property="og:image" content="https://vitalops.ai/assets/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@vitalopsai">
<meta name="twitter:image" content="https://vitalops.ai/assets/og.png">
{jsonld}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
{css}
</head>
<body>
"""

def drop(label, root, items, base, cur, foot=""):
    rows = []
    for k, it in items.items():
        on = ' class="is-current" aria-current="page"' if cur == f"{base}/{k}" else ""
        rows.append(f'<a href="{root}{base}/{k}/"{on}><span class="ni">{ic(it["icon"])}</span><b>{it["name"]}</b><span>{it["short"]}</span></a>')
    on = " is-current" if (cur or "").startswith(base + "/") else ""
    return (f'<div class="nav-drop"><button class="nav-drop-btn{on}" type="button" aria-expanded="false">{label}{ic("chevron-down", "chev")}</button>'
            f'<div class="nav-panel">{"".join(rows)}{foot}</div></div>')

def nav(root, cur):
    def link(href, text, key):
        on = ' class="is-current" aria-current="page"' if cur == key else ""
        return f'<a class="nav-a" href="{root}{href}"{on}>{text}</a>'
    pfoot = f'<a class="nav-foot" href="{root}platform/">{ic("layers")}How the products fit together<em>{ic("arrow-up-right")}</em></a>'
    sfoot = f'<a class="nav-foot" href="{root}lab/">{ic("play")}Try the live demos<em>{ic("arrow-up-right")}</em></a>'
    return f"""<header class="vnav" id="top"><a class="skip" href="#main">Skip to content</a><div class="wrap vnav-in">
  <a class="logo" href="{root or './'}" aria-label="VitalOps home"><svg aria-hidden="true"><use href="#vo-logo"/></svg>VitalOps</a>
  <nav class="nav-links" id="navLinks" aria-label="Main">
    {drop("Products", root, PRODUCTS, "products", cur, pfoot)}
    {drop("Solutions", root, SOLUTIONS, "solutions", cur, sfoot)}
    {link("lab/", "Live demos", "lab")}
    {link("services/", "Services", "services")}
    {link("security/", "Security", "security")}
    {link("company/", "Company", "company")}
  </nav>
  <div class="nav-act">
    <button class="nav-burger" id="navToggle" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="navLinks"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
    <a class="btn btn-p btn-sm" href="{BOOK}" target="_blank" rel="noopener">{ic("calendar")}<span>Book a review</span></a>
  </div>
</div></header>"""

def footer(root):
    col = lambda items, base: "".join(f'<a href="{root}{base}/{k}/">{v["name"]}</a>' for k, v in items.items())
    return f"""<footer class="vfoot"><div class="wrap">
  <div class="foot-grid">
    <div class="foot-brand"><a class="logo" href="{root or './'}"><svg aria-hidden="true"><use href="#vo-logo"/></svg>VitalOps</a>
      <p>Inference engineering: plan, optimise, serve and run open-weight models on the hardware you choose.</p>
      <p class="foot-soc"><a href="https://github.com/vitalops" target="_blank" rel="noopener" aria-label="GitHub">{lg("github")}</a><a href="https://x.com/vitalopsai" target="_blank" rel="noopener" aria-label="X">X</a><a href="mailto:{MAIL}">{MAIL}</a></p></div>
    <div><h4>Products</h4>{col(PRODUCTS, "products")}</div>
    <div><h4>Solutions</h4>{col(SOLUTIONS, "solutions")}</div>
    <div><h4>Resources</h4><a href="{root}lab/">Live demos</a><a href="{root}platform/">Platform</a><a href="{root}platform/#stack">Supported stack</a><a href="{root}services/">Services</a><a href="{root}services/#engage">How we engage</a></div>
    <div><h4>Company</h4><a href="{root}company/">About</a><a href="{root}security/">Security</a><a href="{BOOK}" target="_blank" rel="noopener">Book a review</a><a href="mailto:{MAIL}">Contact</a><a href="{root}credits/">Photo credits</a></div>
  </div>
  <p class="foot-legal">© <span id="yr">2026</span> VitalOps Inc · vitalops.ai</p>
</div></footer>"""

CTA_DEFAULT = ("What's the number you need to hit?",
               "Tokens per second, time to first token, a memory budget, a cost per million tokens. Bring it and the model. In 30 minutes we'll tell you whether it's reachable and what it would take.")
def cta(h2=None, lede=None):
    h2, lede = h2 or CTA_DEFAULT[0], lede or CTA_DEFAULT[1]
    return f"""<section class="cta2" id="contact"><div class="wrap cta2-in">
  <div class="cta2-copy"><span class="k">Get started</span><h2>{h2}</h2><p class="lede">{lede}</p>
    <div class="hero-cta"><a class="btn btn-p" href="{BOOK}" target="_blank" rel="noopener">{ic("calendar")}Book an inference review</a><a class="btn btn-s" href="mailto:{MAIL}">{ic("send")}{MAIL}</a></div></div>
  <ol class="cta2-steps">
    <li><b>{ic("calendar")}Review</b><span>Free, 30 minutes. Your model, your hardware and your target; an honest estimate back.</span></li>
    <li><b>{ic("flask-conical")}Sprint</b><span>Two weeks, fixed fee, on your hardware. If we don't beat your baseline, you don't pay.</span></li>
    <li><b>{ic("server")}Run</b><span>Serve, monitoring and continuous re-optimisation, with an SLO we sign.</span></li>
  </ol>
</div></section>"""

def jsonld(faqs=()):
    org = {"@type": "Organization", "@id": "https://vitalops.ai/#org", "name": "VitalOps", "legalName": "VitalOps Inc",
           "url": "https://vitalops.ai/", "logo": "https://vitalops.ai/assets/icon-512.png", "email": MAIL,
           "sameAs": ["https://github.com/vitalops", "https://x.com/vitalopsai"]}
    graph = [org]
    strip = lambda x: H.unescape(re.sub(r"<[^>]+>", "", x)).strip()
    if faqs:
        graph.append({"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": strip(q), "acceptedAnswer": {"@type": "Answer", "text": strip(a)}} for q, a in faqs]})
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False) + "</script>"

def faq(items, title="Questions", h2="What engineering teams ask us"):
    qs = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in items)
    return f'<section class="faq"><div class="wrap"><span class="k">{title}</span><h2 style="margin:12px 0 20px">{h2}</h2>{qs}</div></section>'

PAGES = []
def page(path, title, desc, cur, body, faqs=(), demos=(), cta_args=None, ctaband=True):
    root = "../" * path.count("/") if path else ""
    out = head(title, desc, root, path, jsonld(faqs)) + G["DEFS"] + "__SPRITE__" + nav(root, cur)
    out += '\n<main id="main" tabindex="-1">\n' + body.replace("{R}", root) + (faq(faqs) if faqs else "") + (cta(*(cta_args or ())) if ctaband else "") + "\n</main>\n" + footer(root)
    js = ["assets/js/site.js", "assets/js/play.js"] + [f"assets/js/lab-{d}.js" for d in demos]
    out += "".join(f'\n<script src="{root}{asset(j)}"{" defer" if "lab-" in j else ""}></script>' for j in js) + "\n</body>\n</html>\n"
    PAGES.append((path, out))

def write_all():
    sprite = G["sprite"]()
    for path, out in PAGES:
        d = os.path.join(ROOT, path)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w").write(out.replace("__SPRITE__", sprite))
    print("pages", len(PAGES))

# ───────────────────────── page parts ─────────────────────────
def sec_head(k, h2, lede="", cls=""):
    return f'<div class="sh-head {cls}"><span class="k">{k}</span><h2>{h2}</h2>{f"<p class=lede>{lede}</p>" if lede else ""}</div>'

def phero(photo, k, h1, lede, metrics, ctas=None, pos="center", shot=""):
    ctas = ctas if ctas is not None else [("btn-w", BOOK, "Book an inference review", "calendar", True)]
    cb = "".join(f'<a class="btn {c}" href="{h}"{" target=_blank rel=noopener" if ext else ""}>{ic(i) if i else ""}{t}</a>' for c, h, t, i, ext in ctas)
    ms = "".join(f'<div class="pm"><b>{v}</b><span>{l}</span></div>' for v, l in metrics)
    grid = " has-shot" if shot else ""
    return f"""<section class="phero{grid}"><div class="phero-bg" style="background-image:url('{{R}}assets/photos/{photo}.webp');background-position:{pos}"></div>
  <div class="wrap phero-in"><div class="phero-copy"><span class="k">{k}</span><h1>{h1}</h1><p class="lede">{lede}</p><div class="hero-cta">{cb}</div></div>{f'<div class="phero-shot">{shot}</div>' if shot else ""}</div>
  {f'<div class="wrap"><div class="pms">{ms}</div></div>' if metrics else ""}
</section>"""

_row_i = [0]
def row(no, title, para, fig, bullets, link=None, flip=None):
    if flip is None:
        flip = _row_i[0] % 2 == 1; _row_i[0] += 1
    li = "".join(f"<li>{ic(i)}<span>{t}</span></li>" for i, t in bullets)
    a = f'<a class="more" href="{link[0]}">{link[1]}{ic("arrow-up-right")}</a>' if link else ""
    return f"""<article class="step{" flip" if flip else ""}"><div class="wrap bleed{" l" if flip else ""}"><div class="split">
  <div class="step-copy"><div class="step-no">{no}</div><h3>{title}</h3><p>{para}</p><ul class="chg">{li}</ul>{a}</div>
  <div class="step-shot">{fig}</div></div></div></article>"""

def lab_block(key, k=None, h2=None, lede=None, id_=None):
    t, d, i = DEMOS[key]
    return f"""<section class="labsec" id="{id_ or 'demo-' + key}"><div class="wrap">
  <div class="labsec-head"><div><span class="k">{ic("play")}{k or "Live demo · runs in your browser"}</span><h2>{h2 or t}</h2><p class="lede">{lede or d}</p></div></div>
  <div class="lab" data-lab="{key}"><noscript><p class="lab-ns">This demo needs JavaScript.</p></noscript></div>
</div></section>"""

def cards(items, base, root="{R}", cls="pcards"):
    return f'<div class="{cls}">' + "".join(
        f'<a class="pcard" href="{root}{base}/{k}/"><span class="pc-i">{ic(v["icon"])}</span><b>{v["name"]}</b><span>{v.get("blurb", v["short"])}</span><em>{ic("arrow-up-right")}</em></a>'
        for k, v in items.items()) + "</div>"

def chips(items):
    return '<div class="chips2">' + "".join(f'<span>{lg(s) if s else ""}{t}</span>' for t, s in items) + "</div>"

LOGOS = [("NVIDIA", "nvidia"), ("AMD", "amd"), ("Apple silicon", "apple"), ("Qualcomm", "qualcomm"), ("Arm", "arm"), ("Raspberry Pi", "raspberrypi"),
         ("PyTorch", "pytorch"), ("Hugging Face", "huggingface"), ("Kubernetes", "kubernetes"), ("Llama", "meta"), ("Qwen", "qwen"), ("DeepSeek", "deepseek"), ("Mistral", "mistralai"), ("Gemma", "google")]
def logo_strip(title="Runs on the hardware and the stack you already have"):
    items = "".join(f"<span>{lg(s)}{t}</span>" for t, s in LOGOS)
    return f'<section class="logos"><div class="wrap"><p>{title}</p><div class="logo-row"><div class="logo-track">{items}{items.replace("<span>", "<span aria-hidden=\"true\">")}</div></div></div></section>'

# ───────────────────────── lifecycle ─────────────────────────
def vig(k):
    """A small animated picture of each stage's work, drawn to match its title."""
    if k == "plan":
        bars = "".join(f'<g class="pb pb{i}"><text x="14" y="{30 + i * 26}">{n}</text><rect class="tr" x="58" y="{21 + i * 26}" width="150" height="12" rx="3"/><rect class="fl" x="58" y="{21 + i * 26}" width="{w}" height="12" rx="3"/><text class="v" x="{66 + w}" y="{31 + i * 26}">{c}</text></g>'
                       for i, (n, w, c) in enumerate((("L40S", 132, "$0.61"), ("H100", 92, "$0.31"), ("H200", 70, "$0.24"), ("B200", 84, "$0.27"))))
        return f'<svg viewBox="0 0 260 130" class="vg vg-plan" aria-hidden="true">{bars}<path class="ck" d="M232 73l5 5 9-10"/><text class="cap" x="14" y="124">$ per 1M tokens at your peak · H200 wins</text></svg>'
    if k == "optimize":
        pts = [(18, 92), (64, 92), (64, 70), (108, 70), (108, 62), (156, 62), (156, 38), (206, 38), (206, 26), (246, 26)]
        d = "M" + " L".join(f"{x} {y}" for x, y in pts)
        dots = "".join(f'<circle class="od od{i}" cx="{x}" cy="{y}" r="3.5"/>' for i, (x, y) in enumerate(((64, 70), (108, 62), (156, 38), (206, 26))))
        return (f'<svg viewBox="0 0 260 130" class="vg vg-opt" aria-hidden="true"><line class="floor" x1="14" y1="106" x2="250" y2="106"/><text class="cap fl" x="250" y="102" text-anchor="end">accuracy floor</text>'
                f'<path class="ol" d="{d}"/>{dots}<g class="rej"><circle cx="132" cy="114" r="3.5"/><text x="140" y="118">int4 · below floor</text></g><text class="cap" x="14" y="16">tok/s · 1,840 → 6,120</text></svg>')
    if k == "deploy":
        return ('<svg viewBox="0 0 260 130" class="vg vg-dep" aria-hidden="true"><text class="cap" x="14" y="22">traffic · prod-a</text>'
                '<rect class="tr" x="14" y="34" width="232" height="22" rx="4"/><rect class="nw" x="14" y="34" width="232" height="22" rx="4"/>'
                '<g class="lbl"><text class="l1" x="20" y="49">canary 10%</text><text class="l2" x="20" y="49">50%</text><text class="l3" x="20" y="49">100% · promoted</text></g>'
                '<g class="ck3"><rect x="14" y="74" width="232" height="40" rx="6" class="box"/><text x="26" y="92">TTFT p99</text><text class="v" x="234" y="92" text-anchor="end">−41%</text><text x="26" y="106">error rate</text><text class="v" x="234" y="106" text-anchor="end">0.02% (=)</text></g></svg>')
    # operate
    return ('<svg viewBox="0 0 260 130" class="vg vg-run" aria-hidden="true"><text class="cap" x="14" y="16">TTFT p99 · ms</text><line class="slo" x1="14" y1="44" x2="250" y2="44"/><text class="cap fl" x="250" y="40" text-anchor="end">SLO 400</text>'
            '<g class="scroll"><path class="ln" d="M0 84 L20 80 L40 86 L60 78 L80 82 L100 76 L120 30 L140 26 L160 34 L180 80 L200 84 L220 78 L240 82 L260 80 L280 84 L300 80 L320 86 L340 78 L360 82 L380 76 L400 84 L420 80 L440 86 L460 78 L480 82 L500 80 L520 84"/></g>'
            '<g class="alert"><circle cx="140" cy="26" r="5"/><text x="150" y="22">alert · prefix hit 71% → 44%</text></g><g class="fix"><rect x="14" y="98" width="232" height="22" rx="5"/><text x="24" y="113">fix proposed · chunked prefill · canary 10%</text></g></svg>')

STAGES = [
 dict(k="plan", n="01", t="Plan", h="Size it before you buy it", photo="racks-art",
      d="Pick the hardware, the count and the contract from your traffic, not from a vendor's benchmark. Plan simulates your workload on every GPU in the catalogue and prices each option, so the purchase order is a decision you can defend.",
      dl=["GPU type and count per SLO", "Cost per million tokens by option", "Buy-versus-rent break-even", "Headroom for next year's traffic"],
      res=[("−38%", "hardware spend against the first quote"), ("±8%", "forecast against measured throughput")], prods=["plan", "sim"]),
 dict(k="optimize", n="02", t="Optimise", h="Make it fast, keep it right", photo="racks-teal",
      d="Optimize searches the serving engine, quantisation, scheduling, speculative decoding and kernels for your model on your target, and holds every candidate to your accuracy floor. The result is a reproducible bundle, not a tuning diary.",
      dl=["Verified configuration bundle", "Custom kernels, SASS-checked", "Eval report against your floor", "Draft model trained on your traffic"],
      res=[("3.3×", "throughput on the same GPUs"), ("0", "points below your accuracy floor")], prods=["optimize", "sim"]),
 dict(k="deploy", n="03", t="Deploy", h="Ship it as a canary", photo="gpu-cluster",
      d="The bundle goes to Serve, in your cloud or data centre, as a canary with instant rollback, or to Edge, exported and signed for every device in the fleet. What you optimised is exactly what runs.",
      dl=["OpenAI-compatible endpoints", "Canary rollouts and rollback", "Device exports: GGUF, MLX, ExecuTorch, TensorRT", "Signed over-the-air updates"],
      res=[("Seconds", "to roll back a release"), ("1", "endpoint for every model you run")], prods=["serve", "edge"]),
 dict(k="operate", n="04", t="Operate", h="Hold the SLO as traffic changes", photo="racks-dark",
      d="Monitoring reads inference in the numbers that decide the bill: time to first token, tokens per second, KV-cache hit rate, cost per million tokens and quality drift. When something moves, the fix comes back through Optimize; Fleet keeps agent swarms within budget.",
      dl=["Inference-native dashboards and alerts", "Alerts with a proposed fix", "Continuous re-optimisation", "Capacity checks before a launch"],
      res=[("< 1 h", "from a regression to a proposed fix"), ("−69%", "cost per million tokens over a year")], prods=["serve", "fleet"]),
]
def lifecycle():
    rail = "".join(f'<button class="lc-card{" on" if i == 0 else ""}" type="button" role="tab" aria-selected="{"true" if i == 0 else "false"}" aria-controls="lc-{s["k"]}" id="lct-{s["k"]}"><span class="lc-vig">{vig(s["k"])}</span><span class="lc-t"><i>{s["n"]}</i><b>{s["t"]}</b><em>{s["h"]}</em></span></button>' for i, s in enumerate(STAGES))
    panels = []
    for i, s in enumerate(STAGES):
        dl = "".join(f"<li>{x}</li>" for x in s["dl"])
        res = "".join(f"<li><b>{v}</b><span>{l}</span></li>" for v, l in s["res"])
        pr = "".join(f'<a href="{{R}}products/{p}/"><span class="pc-i">{ic(PRODUCTS[p]["icon"])}</span><b>{PRODUCTS[p]["name"]}</b><span>{PRODUCTS[p]["short"]}</span></a>' for p in s["prods"])
        panels.append(f"""<div class="lc-panel" id="lc-{s["k"]}" role="tabpanel" aria-labelledby="lct-{s["k"]}"{"" if i == 0 else " hidden"}>
  <div class="lc-a"><div class="lc-ph" style="background-image:url('{{R}}assets/photos/{s["photo"]}.webp')"></div><h3>{s["h"]}</h3><p>{s["d"]}</p></div>
  <div class="lc-b"><h4>Deliverables</h4><ul class="lc-dl">{dl}</ul></div>
  <div class="lc-b"><h4>Results</h4><ul class="lc-res">{res}</ul></div>
  <div class="lc-b"><h4>Products</h4><div class="lc-pr">{pr}</div></div>
</div>""")
    return f"""<section class="life" id="lifecycle"><div class="wrap">
  {sec_head("Across the model's life", "From GPU budget to production SLO.", "Pick a stage to see what you get from it, what changes, and which products do the work.")}
  <div class="lc"><div class="lc-rail" role="tablist" aria-label="Lifecycle stages">{rail}</div>{"".join(panels)}</div>
  <p class="lc-also">The same four stages apply wherever the model runs: <a href="{{R}}solutions/gpu-clouds/">GPU clouds and data centres {ic("arrow-up-right")}</a> <a href="{{R}}solutions/robotics/">devices in the field {ic("arrow-up-right")}</a></p>
</div></section>"""

# ───────────────────────── the Plan screen ─────────────────────────
def screen_plan():
    g = G
    g["NAV"]["plan"] = [("Plan", ["Scenarios*", "Traffic", "Catalogue", "Reports"]), ("Optimize", ["Runs", "Models", "Bundles"]), ("Serve", ["Pools", "Monitoring"]), ("Fleet", ["Agents", "GPUs"])]
    g["NAV_ICON"].update({"Scenarios": "git-branch", "Traffic": "activity", "Catalogue": "database", "Reports": "file-text"})
    g["NAV_COUNT"]["Scenarios"] = "7"
    stat, st, ab, mb, bh, evt, gpu_t, model = g["stat"], g["st"], g["ab"], g["mb"], g["bh"], g["evt"], g["gpu_t"], g["model"]
    tb, CBX, CBH, RA, RAH = g["toolbar"], g["CBX"], g["CBH"], g["RA"], g["RAH"]
    fc = g["line_chart"](640, 122, (0, 24), [dict(cls="brand", pts=[(0, 120), (3, 150), (6, 190), (9, 240), (12, 300), (15, 340), (18, 380), (21, 410), (24, 420)], area=True)], (0, 500),
                         [(0, "0"), (200, "200"), (400, "400")], [(0, "now"), (6, "+6 mo"), (12, "+12"), (18, "+18"), (24, "+24")],
                         markers=[dict(x=12, y=300, label="launch in EU · +40%", step=2, dy=-8), dict(x=24, y=420, label="peak 420 req/s", step=4, cls="hi", anchor="end", dy=-8)])
    E = H.escape
    main = f"""
<div class="ph"><div><div class="crumb">Plan {ic("chevron-right")} Scenarios</div><p class="t1">support-assistant · 2027 <span class="mu">Qwen3-32B · fp8 · TTFT p99 &lt; 400 ms</span></p></div><div class="actions">{ab("Compare","columns-3")}{ab("New scenario","plus","pri")}</div></div>
<div class="ptabs"><span class="on">Options</span><span>Traffic</span><span>What-ifs <em>4</em></span><span>Assumptions</span></div>
<div class="stats">{stat("Peak forecast","420 req/s","+250% in 24 months","up")}{stat("Recommended","12× H200","3 nodes · reserved 1 yr","ok",count=False)}{stat("Cost per 1M tokens","$0.24","was $0.39 on the quote","ok")}{stat("TTFT p99 at peak","310 ms","SLO 400 ms","ok")}</div>
<div class="pane">
  <div>
    <div class="blk">
      {tb(["All options*","Meets SLO","Within budget"],"GPU, cloud, region…")}
      <table class="tbl">
        <tr><th>Option</th><th class="n">GPUs</th><th class="n">tok/s/GPU</th><th class="n">TTFT p99</th><th class="n">$/month</th><th class="n">$/1M</th><th>Verdict</th>{RAH}</tr>
        <tr><td>{gpu_t("H100 · on-demand")}</td><td class="n">16</td><td class="n count">3,060</td><td class="n">355 ms</td><td class="n">$58,400</td><td class="n">$0.39</td><td>{st("warn","Over budget")}</td>{RA}</tr>
        <tr data-step="1"><td>{gpu_t("L40S · reserved")}</td><td class="n">40</td><td class="n count">1,180</td><td class="n">520 ms</td><td class="n">$41,800</td><td class="n">$0.61</td><td>{st("bad","Misses SLO")}</td>{RA}</tr>
        <tr data-step="2"><td>{gpu_t("MI300X · reserved", "amd")}</td><td class="n">10</td><td class="n count">4,410</td><td class="n">330 ms</td><td class="n">$39,900</td><td class="n">$0.27</td><td>{st("ok","Meets SLO")}</td>{RA}</tr>
        <tr data-step="3"><td>{gpu_t("B200 · buy, 3 yr")}</td><td class="n">8</td><td class="n count">6,900</td><td class="n">240 ms</td><td class="n">$44,100</td><td class="n">$0.27</td><td>{st("ok","Meets SLO")}</td>{RA}</tr>
        <tr data-step="4" class="sel"><td>{gpu_t("H200 · reserved")}</td><td class="n">12</td><td class="n count">4,980</td><td class="n">310 ms</td><td class="n">$36,200</td><td class="n">$0.24</td><td data-before='{E(st("ok","Meets SLO"))}'>{st("brand","Recommended")}</td>{RA}</tr>
      </table>
    </div>
    <div class="blk">{bh("Peak requests per second · forecast","24 months",("maximize-2",))}{fc}</div>
  </div>
  <aside class="side">
    <div class="sh"><b>12× H200 · reserved</b><span class="ibtn">{ic("external-link")}</span></div>
    <div class="kv"><b class="dt">Parallelism</b><span class="dd">TP 2 · 6 replicas</span><b class="dt">Bundle</b><span class="dd">run-8841 · fp8 + EAGLE-3</span><b class="dt">KV cache / GPU</b><span class="dd">96 GB · 71% at peak</span><b class="dt">Power</b><span class="dd">8.4 kW per node</span><b class="dt">Headroom</b><span class="dd">+22% at peak</span></div>
    <div class="sh2">Buy versus rent</div>
    <div class="hb"><span>Reserved 1-yr</span><i><b class="grow" style="width:62%"></b></i><em>$434k</em></div>
    <div class="hb"><span>Buy B200 · 3-yr</span><i><b class="grow" style="width:76%"></b></i><em>$529k</em></div>
    <div class="hb"><span>On-demand H100</span><i><b class="grow" style="width:100%"></b></i><em>$701k</em></div>
    <div class="ai" data-step="5"><b>{ic("sparkles")}Recommendation</b>Reserve 12× H200 for a year; buying only breaks even at month 19 at this growth. Re-plan after the EU launch.</div>
    <div class="acts" data-step="5">{mb("Export plan","download","pri",act=True)}{mb("Share","share-2")}</div>
  </aside>
</div>"""
    return g["screen"]("fig-plan", "localhost:8080/plan/scenarios/support-assistant-2027", "plan", "7 scenarios · catalogue 2026-10", main,
                       done="✓ Exported", toast="plan-support-assistant-2027.pdf · 12× H200 · $0.24 per 1M tokens",
                       label="Plan: hardware options for a traffic forecast, each simulated and priced, with a recommended configuration and buy-versus-rent costs", foot_icon="database")

# ───────────────────────── products ─────────────────────────
def P(key):
    return PRODUCTS[key]

def product_pages():
    g = G
    SP = screen_plan()
    data = {
     "plan": dict(photo="racks-art", k="Plan · capacity and hardware planning",
        h1="Know the GPU bill before you sign it.",
        lede="Plan simulates your traffic on every accelerator in the catalogue, with your model, your SLO and the configuration Optimize would ship, and prices each option. You choose the hardware, the count and the contract from numbers you can defend.",
        metrics=[("−38%", "hardware spend against the first quote"), ("±8%", "forecast against measured throughput"), ("40+", "accelerators and cloud SKUs modelled"), ("Minutes", "per scenario, not a month of benchmarking")],
        rows=[("01 · Scenarios", "Every option, simulated on your traffic", "Describe the workload once: model, prompt and output lengths, arrival pattern, growth and the SLO. Plan runs a discrete-event simulation of the serving engine on each GPU and cloud SKU and returns throughput, latency at the tail, power and cost side by side.", SP,
               [("check", "Options that miss the SLO are marked before anyone gets a quote."), ("check", "Cost per million tokens, not cost per GPU-hour."), ("check", "Buy, reserve or rent, with the break-even month.")])],
        demo=("planner", "Plan, in miniature", "Pick a model, a GPU and your traffic. The estimate uses the same first-order physics Plan starts from: decode is bound by memory bandwidth, prefill by compute."),
        feats=[("database", "A catalogue that knows the quirks", "H100 to B200, MI300X, L40S, consumer cards and edge modules, with the details that change answers: NVLink domains, HBM sizes, FP8 and FP4 support, and real interconnect bandwidth."),
               ("trending-up", "Traffic that grows", "Seasonality, launches and growth curves. Plan tells you when the cluster runs out of headroom, not just whether it fits today."),
               ("badge-check", "Calibrated against measurements", "Every forecast is checked against Optimize runs on real hardware; the error is reported with the plan.")],
        works="NVIDIA H100, H200, B200, GB200, L40S, L4 · AMD MI300X, MI325X · AWS, Google Cloud, Azure, CoreWeave, Lambda and on-prem price books · vLLM, SGLang and TensorRT-LLM performance models.",
        faq=[("Is Plan a spreadsheet?", "No. It runs a discrete-event simulation of the serving engine, scheduler and KV cache against your traffic, using performance models calibrated on measured runs. The spreadsheet view is an export."),
             ("Does it include the optimisation?", "Yes. Each option is simulated with the configuration Optimize would ship on that hardware, so you don't buy for an unoptimised baseline."),
             ("Can it plan for edge devices?", "Yes. Edge fits use the same models: memory, bandwidth and power per device, with the largest model that meets your accuracy floor.")]),
     "optimize": dict(photo="racks-teal", k="Optimize · agentic inference optimisation",
        h1="The same model, three times the tokens per second.",
        lede="Give Optimize a model, a GPU target, an SLO and your eval set. An agent searches the serving engine, quantisation, parallelism, scheduling, speculative decoding and custom kernels, and every candidate is held to your accuracy floor.",
        metrics=[("3.3×", "throughput on the sample run, same GPUs"), ("−55%", "time to first token at p99"), ("84.1", "accuracy held above the 83.5 floor"), ("2 h 14 m", "of search, not weeks of trial and error")],
        rows=[("01 · Runs", "Every run, ranked against the number you need", "The runs list shows each model and target with its best verified result, the speed-up against the baseline and whether it held the accuracy floor. Ship to Serve is one click.", g["SCREEN_HERO"],
               [("check", "Weeks of trial and error become one run with a report."), ("check", "Every speed-up is tied to an accuracy number."), ("check", "A reproducible bundle anyone on the team can rerun.")]),
              ("02 · Search", "A search you can read, candidate by candidate", "Each candidate is a concrete change: fp8 weights and KV cache, chunked prefill, an EAGLE-3 draft trained on your traffic, a fused kernel. Each is measured on the target GPU and evaluated with several seeds; anything below the floor is rejected, however fast.", g["SCREEN_OPT"],
               [("check", "INT4 tried and rejected when the eval says so."), ("check", "Kernels verified numerically and at SASS level."), ("check", "The best configuration exported as a bundle.")])],
        demo=("quant", "What quantisation does to the weights", "Real FP8, INT8, INT4 and NVFP4 rounding on a synthetic layer with outlier channels. Optimize makes the same trade on your weights, then checks it on your eval set."),
        demo2=("specdec", "Speculative decoding, on one clock", "A small draft model guesses tokens; the target verifies them in one pass. Optimize trains the draft on your traffic, which is what moves the acceptance rate."),
        feats=[("sliders-horizontal", "The whole stack, not just flags", "Engine choice and flags, weight and KV quantisation, tensor and pipeline parallelism, batching and prefill policy, speculative decoding, CUDA graphs, torch.compile and custom kernels."),
               ("flask-conical", "Your eval is the judge", "Bring lm-eval tasks or your own set. You set the floor; Optimize reports accuracy with every throughput number and never ships below it."),
               ("package", "Bundles, not tuning notes", "The winning configuration, kernels and draft model are packaged with the exact engine version, so Serve runs what was measured.")],
        works="vLLM, SGLang, TensorRT-LLM, llama.cpp, Hugging Face Transformers · lm-eval or your own evals · targets: tokens/s, TTFT, TPOT, p99, memory, cost per million tokens.",
        faq=[("Which models can it speed up?", "Open-weight models and your fine-tunes: Llama, Qwen, DeepSeek, Mistral, Gemma, GLM, Whisper, VLMs, embedding and reranker models."),
             ("How is the faster model still correct?", "You set an accuracy floor on your eval set. Every candidate is evaluated against it with several seeds, and anything below the floor is rejected. Custom kernels are checked numerically against the reference and inspected at SASS level."),
             ("Do our weights leave our environment?", "No. Optimize runs in your cloud account or data centre, and evals run where your data already lives.")]),
     "sim": dict(photo="racks-dark", k="Sim · a GPU simulator for kernel work",
        h1="Rank kernels without a GPU attached.",
        lede="A replacement libcuda.so takes your unchanged binary, loads the cubin into a SASS interpreter and executes the launches on CPU threads under a timing model. You get predicted time per target, a per-instruction stall breakdown and a ranking of candidates, on a laptop or in CI.",
        metrics=[("0", "GPUs needed to rank candidates"), ("ms → h", "three fidelities, static to cycle-level"), ("ρ 0.9+", "rank correlation reported on every run"), ("6", "NVIDIA architectures modelled")],
        rows=[("01 · Kernels", "The SASS listing, stall by stall", "Optimize's kernel page shows the SASS the compiler produced for each candidate, with stall shares per instruction, register pressure and occupancy, and the predicted time on each GPU you target.", g["SCREEN_SIM"],
               [("check", "Kernel work no longer waits for a GPU slot."), ("check", "Agents rank thousands of variants for the cost of CPU time."), ("check", "A performance regression fails CI before it reaches hardware.")]),
              ("02 · Kernel IDE", "An agent that rewrites the kernel and checks its work", "The agent edits the CUDA or Triton source, recompiles, reads the new SASS, simulates and then verifies the winner on a real GPU before opening a pull request.", g["SCREEN_IDE"],
               [("check", "Source, SASS and terminal side by side."), ("check", "Every accepted change verified on real hardware."), ("check", "A pull request with the numbers attached.")])],
        flow=True,
        feats=[("gauge", "Three fidelities", "Static analysis in milliseconds, sampled simulation in seconds, cycle-level in hours. Use the cheap one to prune and the expensive one to decide."),
               ("badge-check", "Honest about its error", "Rank correlation against real hardware is reported with every run, and the best candidates are verified on a real GPU before anything ships."),
               ("git-branch", "Built for CI", "Run on GitHub Actions or any CPU runner. Fail the build when a kernel gets slower on a GPU you don't have in the rack.")],
        works="CUDA C++, Triton, CUTLASS, PyTorch through a driver shim · KernelBench and TritonBench · GitHub Actions · targets: H100, H200, B200, L40S, RTX 4090 and 5090, Jetson Orin and Thor.",
        faq=[("What does 'down to the SASS' mean?", "We inspect what the compiler produced: register pressure, spills, occupancy, shared-memory bank conflicts and stall reasons in the SASS the GPU executes. We don't write SASS; ptxas does. We steer it through PTX intrinsics, launch bounds and compiler flags, and check the result."),
             ("How accurate is a CPU simulation?", "Good enough to rank, which is what it's for. Each run reports its rank correlation against measured hardware, and nothing ships without a real-GPU verification."),
             ("Does it model AMD GPUs?", "Not yet. Sim models NVIDIA architectures; AMD kernels are tuned on hardware.")]),
     "serve": dict(photo="gpu-cluster", k="Serve · model serving and monitoring",
        h1="Run the optimised model. Watch it in the numbers that decide the bill.",
        lede="An OpenAI-compatible server built around the bundles Optimize produces: multi-model pools, continuous batching, prefix caching, chunked prefill, speculative decoding and structured output, with canary rollouts and inference-native monitoring. In your cloud or your data centre.",
        metrics=[("Seconds", "to roll back a release"), ("71%", "prefix-cache hit rate on agent traffic"), ("1", "endpoint for every model you run"), ("Air-gapped", "deployments supported")],
        rows=[("01 · Pools", "Ship the bundle as a canary, promote when the numbers hold", "Deploy a bundle to a pool, send it ten per cent of the traffic, and compare TTFT, cost and errors against the release it replaces. Promote or roll back in one click.", g["SCREEN_SERVE"],
               [("check", "The optimised configuration is the one in production."), ("check", "Rollouts you can reverse in seconds."), ("check", "One endpoint for every model you run.")]),
              ("02 · Monitoring", "Alerts that arrive with the fix", "Generic APM shows CPU and memory. Serve shows TTFT, TPOT, tokens per second, KV-cache hit rate, queue depth, cost per million tokens and quality drift, per model, pool, tenant and prompt template, and hands the fix back to Optimize.", g["SCREEN_MON"],
               [("check", "The cost of a prompt change, the hour it ships."), ("check", "Sampled evals catch quality regressions."), ("check", "Attaches to existing vLLM, SGLang and TensorRT-LLM deployments.")])],
        demo=("batching", "Why the scheduler decides your latency", "A discrete-event simulation of a model server. Switch from static to continuous batching, add chunked prefill and prefix caching, and watch time to first token move."),
        feats=[("network", "OpenAI-compatible", "/v1/chat/completions, /v1/embeddings, tool calls, JSON-schema and grammar-constrained decoding. Point your SDK at a new base URL."),
               ("git-branch", "Rollouts built in", "Canaries, traffic splits, shadow traffic and instant rollback, with the comparison against the previous release on one screen."),
               ("chart-line", "Monitoring that knows inference", "Prometheus and OpenTelemetry out, Grafana dashboards included, PagerDuty and Slack alerts with the cause and a proposed fix.")],
        works="OpenAI SDKs, LangChain and LlamaIndex · Kubernetes and Slurm · NVIDIA and AMD GPUs · Prometheus, OpenTelemetry, Grafana, PagerDuty and Slack.",
        faq=[("Do we have to use Serve to use Optimize?", "No. Bundles export to stock vLLM, SGLang and TensorRT-LLM. Serve adds the rollouts, the monitoring and the loop back into Optimize."),
             ("Can it monitor our existing deployment?", "Yes. Monitoring attaches to existing vLLM, SGLang and TensorRT-LLM servers through their metrics endpoints and a lightweight sidecar."),
             ("Where does it run?", "In your cloud account or data centre, including air-gapped environments. We never see your prompts or completions.")]),
     "edge": dict(photo="jetson-board", k="Edge · on-device models and training", pos="center 40%",
        h1="The largest model that fits, on every device, kept up to date.",
        lede="Each device gets the largest model that meets your accuracy floor inside its memory and latency budget. Where data can't leave the device, fine-tuning runs on it, and the adapter is pushed to every device on the same base.",
        metrics=[("3B", "vision-language model on an 8 GB Jetson"), ("18 MB", "adapter pushed over the air"), ("+2.3 pts", "eval gain from on-device QLoRA"), ("0 bytes", "of training data leaving the device")],
        rows=[("01 · Devices", "A fleet of phones, Pis and Jetsons, each with its own fit", "Edge tracks every device with the model it serves, its tokens per second and its memory headroom, and runs fine-tunes where the data lives.", g["SCREEN_EDGE"],
               [("check", "A model that didn't fit now runs on a phone, a Pi or a Jetson."), ("check", "Accuracy is measured after every compression step."), ("check", "Signed, staged over-the-air updates.")])],
        demo=("edgefit", "Will it fit?", "Pick a device and a model. Weights, KV cache, the vision encoder and the runtime reserve, against the memory the device really has."),
        feats=[("boxes", "Compression with a guard", "Quantise weights, KV cache and the vision encoder, prune a couple of layers, and measure accuracy after every step; stop when the floor is reached."),
               ("brain", "Training on the device", "QLoRA within the memory budget, with gradient checkpointing, a live loss curve and the expected eval gain before the job starts."),
               ("upload", "Exports for every runtime", "GGUF, MLX, ExecuTorch, Core ML, QNN and TensorRT, signed and versioned, with staged rollouts across the fleet.")],
        works="NVIDIA Jetson Orin and Thor · iPhone and Apple silicon · Pixel and Android NPUs · Qualcomm Snapdragon and Dragonwing · Raspberry Pi 5 with Hailo · x86 and Arm CPUs.",
        faq=[("Can you really train on the edge device?", "For many devices, yes. QLoRA fine-tunes of 1–8B models fit within the memory of a Jetson Orin, an Apple M-series machine or a workstation GPU. Edge plans the job within the device's budget and tells you the time and the expected eval gain before it starts."),
             ("What about devices with an NPU?", "Exports target Qualcomm QNN, Apple's Neural Engine through Core ML, and Hailo on the Raspberry Pi, with the same accuracy check after conversion.")]),
     "fleet": dict(photo="racks-art", k="Fleet · agent fleets on your GPUs",
        h1="Run N agents on M GPUs, on your premises.",
        lede="Agent workloads don't look like chat: long shared prefixes, bursts of parallel sub-agents and long idle gaps while tools run. Fleet schedules a swarm of agents across your GPUs with KV-aware routing, prefix sharing between agents and preemption while an agent waits on a tool.",
        metrics=[("12×", "more agents per GPU than naive serving"), ("8 → 96", "agents with one command"), ("64%", "of prompt tokens served from shared prefixes"), ("Air-gapped", "by default")],
        rows=[("01 · Agents", "A GPU map you can schedule against", "Every GPU with its agents, utilisation and KV cache, the scheduler's decisions as they happen, and a capacity check that tells you where the SLO breaks before you scale.", g["SCREEN_FLEET"],
               [("check", "More agents per GPU, because the KV cache stops being thrown away."), ("check", "Scaling means changing one number."), ("check", "A straight answer to how many agents you can run.")])],
        demo=("batching", "Prefix caching, on agent traffic", "Choose the Agents traffic shape and switch prefix caching on: shared system prompts and tool schemas stop being recomputed for every call."),
        feats=[("network", "KV-aware routing", "Requests go to the GPU that already holds their prefix, so a sub-agent burst doesn't recompute the same 20k tokens sixteen times."),
               ("pause", "Preemption while tools run", "An agent waiting on a tool call yields its slot; its KV cache is kept warm or offloaded, not thrown away."),
               ("gauge-circle", "Budgets and policies", "Per-team GPU budgets, priorities and quotas, enforced by the scheduler rather than by a spreadsheet.")],
        works="Claude Agent SDK, OpenAI Agents, LangGraph, or your own loop · Kubernetes and Slurm · air-gapped by default.",
        faq=[("Does Fleet replace our agent framework?", "No. Your agents keep their framework and call an OpenAI-compatible endpoint; Fleet schedules the inference underneath them."),
             ("Which models can the agents use?", "Any open-weight model Serve runs, including several at once with per-model pools.")]),
    }
    related = {"plan": ["optimize", "serve", "sim"], "optimize": ["sim", "serve", "plan"], "sim": ["optimize", "plan", "serve"], "serve": ["optimize", "fleet", "edge"], "edge": ["optimize", "plan", "serve"], "fleet": ["serve", "optimize", "plan"]}
    for key, d in data.items():
        _row_i[0] = 0
        p = P(key)
        body = phero(d["photo"], d["k"], d["h1"], d["lede"], d["metrics"],
                     [("btn-w", BOOK, "Book an inference review", "calendar", True)] + ([("btn-g", "#demo-" + d["demo"][0], "Try the live demo", "play", False)] if d.get("demo") else []), d.get("pos", "center"))
        body += '<section class="prows">' + "".join(row(*r) for r in d["rows"]) + "</section>"
        if d.get("flow"):
            body += f'<section class="flowband"><div class="wrap"><div class="flow-head"><span class="k">How Sim works</span><h2>Python to SASS, then a CPU pretending to be an H100</h2><p class="lede">The kernel compiles exactly as it would for the GPU. Sim interprets the SASS on CPU threads and reports the CPU wall time beside the predicted GPU time.</p></div>{g["FLOW"]}</div></section>'
        if d.get("demo"):
            body += lab_block(d["demo"][0], h2=d["demo"][1], lede=d["demo"][2])
        feats = "".join(f'<div class="feat"><span class="pc-i">{ic(i)}</span><h3>{t}</h3><p>{x}</p></div>' for i, t, x in d["feats"])
        body += f'<section class="feats"><div class="wrap">{sec_head("What you get", "Built for the people who carry the pager.")}<div class="feat-grid">{feats}</div><div class="works"><h4>Works with</h4><p>{d["works"]}</p></div></div></section>'
        if d.get("demo2"):
            body += lab_block(d["demo2"][0], h2=d["demo2"][1], lede=d["demo2"][2])
        rel = {k: PRODUCTS[k] for k in related[key]}
        body += f'<section class="related"><div class="wrap">{sec_head("Across the platform", "Works with the rest of VitalOps.")}{cards(rel, "products")}</div></section>'
        demos = [x[0] for x in (d.get("demo"), d.get("demo2")) if x]
        page(f"products/{key}/", f"{p['name']} · {p['short']} | VitalOps", d["lede"], f"products/{key}", body, faqs=d["faq"], demos=demos)

# ───────────────────────── solutions ─────────────────────────
def solution_pages():
    g = G
    data = {
     "llm-apis": dict(photo="gpu-cluster", k="Solutions · LLM products and APIs",
        h1="Serve more users from the GPUs you already pay for.",
        lede="Chat assistants, copilots and model APIs live or die on time to first token and cost per million tokens. We take the model you trust and make it fast and cheap enough to price your product the way you want.",
        metrics=[("3.3×", "tokens per second on the same GPUs"), ("−69%", "cost per million tokens"), ("< 400 ms", "TTFT at p99, held at peak")],
        pains=[("Latency spikes at peak", "Long prompts block short ones and TTFT blows through the SLO exactly when traffic is highest."),
               ("A bill that scales with success", "Every new customer is another GPU, because the serving stack was never tuned past its defaults."),
               ("Fear of touching it", "Nobody wants to quantise the model that passed evaluation, so it runs in bf16 forever.")],
        how=[("plan", "Size the cluster for next year's peak and price every option."), ("optimize", "Search quantisation, scheduling, speculative decoding and kernels under your accuracy floor."), ("serve", "Ship the bundle as a canary and watch TTFT and cost per tenant.")],
        fig=g["SCREEN_OPT"], fig_t="Every candidate measured and evaluated", demo="batching"),
     "agents": dict(photo="racks-teal", k="Solutions · AI agents",
        h1="Agents that share the GPU instead of fighting over it.",
        lede="Agent traffic has long shared prefixes, bursts of parallel sub-agents and idle gaps while tools run. Chat-shaped serving throws the KV cache away between calls. We schedule for the shape your agents actually have.",
        metrics=[("12×", "more agents per GPU"), ("64%", "of prompt tokens from shared prefixes"), ("8 → 96", "agents with one command")],
        pains=[("The same 20k tokens, recomputed", "System prompts and tool schemas are prefilled again for every step of every agent."),
               ("Sub-agent bursts", "A planner fans out sixteen workers and the queue explodes for everyone else."),
               ("Unknown capacity", "Nobody can say how many agents the cluster can run before the SLO breaks.")],
        how=[("fleet", "Schedule agents across GPUs with KV-aware routing and prefix sharing."), ("serve", "Pool the models your agents call behind one endpoint, with prefix caching on."), ("plan", "Run the capacity check before the launch, not after the incident.")],
        fig=g["SCREEN_FLEET"], fig_t="Agents per GPU, live", demo="batching"),
     "multimodal": dict(photo="racks-dark", k="Solutions · vision and multimodal",
        h1="Vision-language models at the speed of a text model.",
        lede="Document understanding, visual inspection and speech pipelines carry image and audio encoders that most serving stacks treat as an afterthought. We optimise the encoder, the prefill and the decode together.",
        metrics=[("2.4×", "throughput on a 7B VLM on one L40S"), ("−60%", "image-encoder latency"), ("3.1×", "Whisper requests per second")],
        pains=[("Encoders on the critical path", "Each image adds thousands of tokens of prefill and an encoder pass before the first word."),
               ("Memory that disappears", "High-resolution images blow up the KV cache and the batch size collapses."),
               ("Pipelines, not models", "OCR, layout, VLM and speech are tuned one at a time, never as a system.")],
        how=[("optimize", "Quantise the vision tower and the language model separately, each under the eval."), ("serve", "Batch encoders and decoders independently, with image-token caching."), ("edge", "Fit the same VLM onto cameras and inspection devices.")],
        fig=g["SCREEN_HERO"], fig_t="VLMs and speech models among the runs", demo="quant"),
     "robotics": dict(photo="robot-plant", k="Solutions · robotics and devices", pos="center 60%",
        h1="Models that think on the robot, not in the cloud.",
        lede="Inspection robots, drones, cameras and handhelds need answers without a round trip and without sending data off the device. We fit the largest model that meets your accuracy floor onto the hardware you ship, and keep it learning there.",
        metrics=[("3B", "VLM on an 8 GB Jetson Orin Nano"), ("< 120 ms", "per decision on device"), ("0 bytes", "of field data leaving the device")],
        pains=[("Doesn't fit", "The model that passed evaluation needs 16 GB and the module has 8."),
               ("No connectivity", "Sites with no network can't call a cloud model, and latency budgets are measured in milliseconds."),
               ("Data you can't move", "Field data is sensitive or simply too large to upload for training.")],
        how=[("edge", "Compress with an accuracy guard and export for Jetson, Snapdragon, Apple or Hailo."), ("optimize", "Tune the kernels for the module's GPU and memory bandwidth."), ("plan", "Choose the module: the cheapest device that runs the model you need.")],
        fig=g["SCREEN_EDGE"], fig_t="A fleet of devices, each with its own fit", demo="edgefit"),
     "gpu-clouds": dict(photo="aisle-white", k="Solutions · GPU clouds and data centres",
        h1="More tokens from every GPU you rent out.",
        lede="Neoclouds, inference providers and enterprise data centres sell throughput. We raise the tokens per second each GPU delivers, help you plan what to buy next, and give your customers serving that's tuned from day one.",
        metrics=[("+2.6×", "median tokens per second per GPU"), ("−38%", "capex against the first quote"), ("40+", "accelerators modelled")],
        pains=[("Utilisation you can't sell", "GPUs sit at 30% because the serving stack can't keep them busy."),
               ("Buying blind", "Next quarter's order is placed on vendor benchmarks, not your customers' traffic."),
               ("Customers who churn on latency", "Tenants move to whoever serves their model fastest.")],
        how=[("plan", "Model next year's fleet against real tenant traffic, per accelerator."), ("optimize", "Ship tuned bundles for the models your customers run most."), ("serve", "Multi-tenant pools with per-tenant monitoring and cost.")],
        fig=SCREEN_PLAN_CACHE, fig_t="Hardware options, simulated and priced", demo="planner"),
     "on-prem": dict(photo="technician", k="Solutions · regulated and on-prem",
        h1="Your models, your data centre, no data leaving it.",
        lede="Banks, hospitals, governments and manufacturers run open-weight models where the data lives. Everything we ship installs inside your environment, air-gapped if you need it, and our engineers work there too.",
        metrics=[("0", "prompts or weights leaving your network"), ("Air-gapped", "installs and updates"), ("SSO", "and audit logs on every action")],
        pains=[("No cloud APIs allowed", "Policy rules out hosted models, so the team inherits the whole serving stack."),
               ("Hardware that's already bought", "The GPUs are fixed for three years; the models are not."),
               ("Auditors", "Every model change needs to be traceable to an evaluation and an approval.")],
        how=[("serve", "Install in your cluster, with SSO, role-based access and audit logs."), ("optimize", "Get the most out of the GPUs you already own, with every change evaluated."), ("fleet", "Run internal agents on premises with budgets per team.")],
        fig=g["SCREEN_SERVE"], fig_t="A pool in your own data centre", demo="planner"),
    }
    for key, d in data.items():
        s = SOLUTIONS[key]
        body = phero(d["photo"], d["k"], d["h1"], d["lede"], d["metrics"], None, d.get("pos", "center"))
        pains = "".join(f'<div class="pain"><span class="pn">{i + 1:02d}</span><h3>{t}</h3><p>{x}</p></div>' for i, (t, x) in enumerate(d["pains"]))
        body += f'<section class="pains"><div class="wrap">{sec_head("The problem", "What gets in the way.")}<div class="pain-grid">{pains}</div></div></section>'
        how = "".join(f'<a class="hw" href="{{R}}products/{p}/"><span class="pc-i">{ic(PRODUCTS[p]["icon"])}</span><div><b>{PRODUCTS[p]["name"]}</b><p>{t}</p></div>{ic("arrow-up-right")}</a>' for p, t in d["how"])
        body += f'<section class="howsec"><div class="wrap bleed"><div class="split"><div class="step-copy">{sec_head("How VitalOps helps", "Three products, one bundle.")}<div class="hws">{how}</div></div><div class="step-shot">{d["fig"]}<p class="fig-cap">{d["fig_t"]}</p></div></div></div></section>'
        body += lab_block(d["demo"], h2=DEMOS[d["demo"]][0])
        others = {k: v for k, v in SOLUTIONS.items() if k != key}
        body += f'<section class="related"><div class="wrap">{sec_head("Other solutions", "Where else we work.")}{cards(others, "solutions")}</div></section>'
        page(f"solutions/{key}/", f"{s['name']} | VitalOps", d["lede"], f"solutions/{key}", body, demos=[d["demo"]])

SCREEN_PLAN_CACHE = ""

# ───────────────────────── home ─────────────────────────
FAQ_HOME = [
 ("Do we have to send you our weights or data?", "No. Everything runs in your cloud account or data centre. Evals run on your data where it already lives. For sprints, our engineers work inside your environment."),
 ("Which models can you speed up?", "Open-weight models and your own fine-tunes: Llama, Qwen, DeepSeek, Mistral, Gemma, GLM, Whisper, VLMs, embedding and reranker models. We can't make a closed API model faster, but we can route, cache and batch around it."),
 ("How do you make sure the faster model is still correct?", "You set an accuracy floor on your eval set. Every candidate configuration is evaluated against it, with several seeds, and anything below the floor is rejected however fast it is. Custom kernels are checked numerically against the reference and inspected at SASS level."),
 ("Can we start with one product?", "Yes. Most teams start with an Optimize sprint on one model, or with Plan before a hardware purchase. Bundles also export to stock vLLM, SGLang and TensorRT-LLM."),
 ("Do you support AMD or non-NVIDIA hardware?", "AMD MI300-class GPUs through ROCm, with kernels written in Triton where possible. Edge covers Apple, Qualcomm, Arm and Hailo targets. Sim currently models NVIDIA GPUs."),
]

def home():
    g = G
    hero = phero("racks-teal", "AI inference engineering",
                 "Make every model <em>fast, small and cheap</em> enough to ship.",
                 "VitalOps plans, optimises, serves and runs open-weight models on the hardware you choose, from a rack of H100s to a Jetson in the field, with an accuracy floor on every change.",
                 [("3.3×", "more tokens per second from the same GPUs"), ("−69%", "cost per million tokens"), ("−55%", "time to first token at p99"), ("0 pts", "accuracy lost below your floor")],
                 [("btn-w", BOOK, "Book an inference review", "calendar", True), ("btn-g", "lab/", "Try the live demos", "play", False)],
                 shot=g["carousel"]([g["SCREEN_HERO"], g["SCREEN_IDE"]], "Optimize · the runs list · a run ships to production as the clip plays"))
    prods = {k: dict(v) for k, v in PRODUCTS.items()}
    blurbs = {"plan": "Simulate your traffic on every GPU in the catalogue and price each option before you buy.",
              "optimize": "An agent searches the stack from engine flags to kernels, held to your accuracy floor.",
              "sim": "A CPU-side GPU simulator that ranks kernels in CI, no GPU attached.",
              "serve": "OpenAI-compatible serving with canary rollouts and inference-native monitoring.",
              "edge": "The largest model that fits each device, fine-tuned where the data lives.",
              "fleet": "Schedule agent swarms across your GPUs with KV-aware routing."}
    for k in prods:
        prods[k]["blurb"] = blurbs[k]
    labs = "".join(f'<a class="lcard" href="lab/#{k}"><span class="pc-i">{ic(i)}</span><b>{t}</b><span>{d}</span><em>{ic("play")}Open</em></a>' for k, (t, d, i) in DEMOS.items())
    sols = "".join(f'<a class="scard" href="solutions/{k}/"><span class="sc-ph" style="background-image:url(\'assets/photos/{ph}.webp\')"></span><span class="sc-b"><span class="pc-i">{ic(v["icon"])}</span><b>{v["name"]}</b><span>{v["short"]}</span></span></a>'
                   for (k, v), ph in zip(SOLUTIONS.items(), ("gpu-cluster", "racks-teal", "racks-dark", "robot-plant", "aisle-white", "technician")))
    html = g["HTML"]
    def cut(start, end):
        i = html.index(start); j = html.index(end, i) + len(end)
        return html[i:j]
    ladder = cut('<section class="ladder"', "</section>")
    tour = cut('<section class="tour"', '<span id="usecases"></span>').replace('<span id="usecases"></span>', "")
    svc = cut('<section class="svc"', "</section>").replace("</div>\n</div></section>", f'</div>\n<p class="svc-more"><a class="more" href="services/">All services and how we engage{ic("arrow-up-right")}</a></p></div></section>')
    clients = cut('<section class="clients"', "</section>")
    body = (hero + logo_strip() + lifecycle()
            + f'<section class="prods" id="products"><div class="wrap">{sec_head("Products", "Six products, one bundle format.", "Each product works alone. Together, what Plan sizes, Optimize tunes and Serve runs is the same configuration, measured once.")}{cards(prods, "products", root="")}</div></section>'
            + ladder + tour
            + f'<section class="labs" id="lab"><div class="wrap">{sec_head("Live demos", "Try the maths in your browser.", "Five interactive tools built on the same first-order physics our products start from. No sign-up, nothing leaves the page.")}<div class="lcards">{labs}</div></div></section>'
            + f'<section class="sols" id="solutions"><div class="wrap">{sec_head("Solutions", "Wherever the model has to run.")}<div class="scards">{sols}</div></div></section>'
            + svc + clients)
    page("", "VitalOps · AI inference engineering: plan, optimise, serve, run", "VitalOps makes open-weight models fast, small and cheap enough to ship: capacity planning, agentic inference optimisation, a GPU simulator for kernels, serving with monitoring, edge deployment and agent fleets.", "home", body, faqs=FAQ_HOME)

# ───────────────────────── other pages ─────────────────────────
def lab_page():
    order = ["planner", "batching", "quant", "specdec", "edgefit"]
    sub = "".join(f'<a href="#{k}">{ic(DEMOS[k][2])}{DEMOS[k][0]}</a>' for k in order)
    intro = {"planner": "How many GPUs, of which kind, and what each million tokens costs. Decode is bound by memory bandwidth and prefill by compute; this is the first-order model Plan starts from before it simulates your traffic.",
             "batching": "A discrete-event simulation of a model server. Static batching, continuous batching, chunked prefill and prefix caching, on chat, RAG and agent traffic.",
             "quant": "Real FP8, INT8, INT4 and NVFP4 rounding on a synthetic layer with outlier channels, the way LLM weights really look. See what grouping and outlier protection buy.",
             "specdec": "A draft model guesses several tokens; the target verifies them in one pass. Move the acceptance rate and the draft length and find the best k.",
             "edgefit": "Weights, KV cache, the vision encoder and the runtime reserve, against what a Jetson, a phone or a Pi really has free. Add an on-device fine-tune and see if it still fits."}
    body = f"""<section class="lhero"><div class="wrap"><span class="k">Live demos</span><h1>The physics of inference, in your browser.</h1><p class="lede">Five tools our engineers use to reason about a workload before measuring it. They run entirely on this page: no sign-up, no server, nothing sent anywhere. When you want the real number for your model on your hardware, that's what the products are for.</p><nav class="lsub" aria-label="Demos">{sub}</nav></div></section>"""
    for k in order:
        body += lab_block(k, k=f"{DEMOS[k][0]}", h2={"planner": "How many GPUs do you need?", "batching": "Why the scheduler decides your latency", "quant": "What quantisation does to the weights", "specdec": "Speculative decoding, on one clock", "edgefit": "Will it fit on the device?"}[k], lede=intro[k], id_=k)
    page("lab/", "Live demos · the physics of inference | VitalOps", "Interactive inference tools that run in your browser: a GPU capacity planner, a batching simulator, a quantisation lab, a speculative decoding race and an edge memory fit.", "lab", body, demos=order,
         cta_args=("Want the measured number?", "These are first-order estimates. Book a review and we'll tell you what your model will really do on your hardware, and what it would take to hit your target."))

def platform_page():
    g = G
    html = g["HTML"]
    i = html.index('<section class="stack"'); j = html.index("</section>", i) + 10
    stack = html[i:j].replace('<span class="k">Stack</span>', '<span class="k">Supported stack</span>')
    layers = [("Your traffic, models and evals", "Prompts, weights and eval sets stay where they are. VitalOps reads them in place.", "database"),
              ("Plan", "Sizes hardware against the traffic and the SLO.", "gauge"),
              ("Optimize and Sim", "Search and verify the configuration; rank kernels on CPU.", "zap"),
              ("The bundle", "Engine version, flags, quantised weights, kernels and draft model, measured together.", "package"),
              ("Serve, Edge and Fleet", "Run the bundle on GPUs, devices or agent swarms.", "server"),
              ("Monitoring", "Reads production and hands regressions back to Optimize.", "chart-line")]
    ls = "".join(f'<li><span class="pc-i">{ic(i)}</span><div><b>{t}</b><p>{d}</p></div></li>' for t, d, i in layers)
    deploy = [("Your cloud account", "AWS, Google Cloud, Azure, CoreWeave, Lambda or any Kubernetes cluster. Installed with Helm or Terraform; we never hold your keys.", "cloud"),
              ("Your data centre", "Bare metal or Kubernetes, Slurm for batch work. NVIDIA and AMD GPUs, InfiniBand or Ethernet.", "server"),
              ("Air-gapped", "Offline installs and signed update bundles, with no call home. Licence checks work offline.", "lock"),
              ("Devices", "Jetson, Apple, Android, Qualcomm, Raspberry Pi and x86. Signed exports and staged over-the-air updates.", "smartphone")]
    ds = "".join(f'<div class="feat"><span class="pc-i">{ic(i)}</span><h3>{t}</h3><p>{d}</p></div>' for t, d, i in deploy)
    body = phero("aisle-white", "Platform", "One bundle, from plan to production.",
                 "Every VitalOps product speaks the same unit: a bundle that pins the engine, the configuration, the quantised weights, the kernels and the draft model that were measured together. What Plan sizes and Optimize verifies is exactly what Serve, Edge and Fleet run.",
                 [("1", "unit of deployment across every product"), ("0", "weights or prompts leaving your environment"), ("4", "ways to deploy: cloud, data centre, air-gapped, device")], None)
    body += f'<section class="arch"><div class="wrap"><div class="arch-grid"><div>{sec_head("Architecture", "How the products fit together.", "Each layer works on its own. Together they close the loop: production regressions become optimisation runs, and optimisation runs become plans.")}</div><ol class="arch-l">{ls}</ol></div></div></section>'
    body += f'<section class="feats"><div class="wrap">{sec_head("Deployment", "Runs where your models already live.")}<div class="feat-grid four">{ds}</div></div></section>'
    body += stack.replace('class="stack"', 'class="stack" id="stack"', 1)
    body += f'<section class="related"><div class="wrap">{sec_head("Products", "The pieces.")}{cards(PRODUCTS, "products")}</div></section>'
    page("platform/", "Platform · one bundle, from plan to production | VitalOps", "How VitalOps products fit together, where they deploy and the stack they support.", "platform", body)

def services_page():
    g = G
    html = g["HTML"]
    def cut(start):
        i = html.index(start); j = html.index("</section>", i) + 10
        return html[i:j]
    svc = cut('<section class="svc"')
    eng = cut('<section class="engage"')
    clients = cut('<section class="clients"').replace('src="assets/', 'src="{R}assets/')
    body = phero("technician", "Services", "Engineers on your problem, fixed scope.",
                 "The products came out of this work, and we still do it: two-week sprints, custom kernels, speculative decoding, quantisation, edge deployment and capacity planning, delivered inside your environment.",
                 [("2 weeks", "from model and target to a verified configuration"), ("Fixed fee", "agreed before we start"), ("No win, no fee", "if we don't beat your baseline")], None)
    body += svc + eng + clients
    page("services/", "Services · inference engineering, fixed scope | VitalOps", "Inference optimisation sprints, custom kernels, speculative decoding, quantisation, edge deployment and capacity planning, delivered fixed-scope.", "services", body, faqs=FAQ_HOME[:3])

def security_page():
    items = [("lock", "Your data stays put", "Products install in your cloud account, data centre or air-gapped network. Prompts, completions, weights and eval sets never leave it, and nothing calls home."),
             ("users", "Access you control", "Single sign-on through SAML or OIDC, SCIM provisioning, and role-based access down to the pool, model and run."),
             ("history", "Every change traceable", "Each bundle records the run, the eval and the person who approved it. Audit logs export to your SIEM."),
             ("shield-check", "Signed artefacts", "Bundles, kernels and device exports are signed and verified before they load, and over-the-air updates are staged."),
             ("key", "Secrets in your vault", "Model registry, cloud and API credentials stay in your secrets manager; we read them at runtime and never store them."),
             ("user", "Engineers inside your boundary", "On sprints, our engineers work in your environment under your access policies, with no copies of anything on our side.")]
    feats = "".join(f'<div class="feat"><span class="pc-i">{ic(i)}</span><h3>{t}</h3><p>{d}</p></div>' for i, t, d in items)
    body = phero("racks-dark", "Security", "Built to run inside your boundary.",
                 "VitalOps is software you run, not a service you send data to. Everything installs in your environment, air-gapped if you need it, and every model change is traceable to an evaluation and an approval.",
                 [("0", "prompts or weights leaving your network"), ("Air-gapped", "installs and signed updates"), ("SSO", "SAML and OIDC, with SCIM")], None)
    body += f'<section class="feats"><div class="wrap">{sec_head("Controls", "What we do, and what we never do.")}<div class="feat-grid">{feats}</div></div></section>'
    page("security/", "Security | VitalOps", "VitalOps installs in your environment: no data leaves it, SSO and role-based access, audit logs, signed artefacts and air-gapped installs.", "security", body,
         faqs=[("Do you ever see our prompts or weights?", "No. The products run in your environment and don't send telemetry about your data. On sprints our engineers work inside your environment under your access controls."),
               ("Can it run with no internet access?", "Yes. Air-gapped installs use offline bundles and signed updates, and licence checks work offline."),
               ("How do you handle a security report?", f"Email {MAIL} with the details. We acknowledge within one working day.")])

def company_page():
    vals = [("badge-check", "Measured, not promised", "Every number we quote a customer is measured on their model and their hardware, with the eval beside it."),
            ("flask-conical", "Accuracy first", "A faster model that answers worse is not faster. The floor is set by you and enforced by the software."),
            ("lock", "Your environment", "We build software you run, so your data never has to come to us."),
            ("code", "Down to the metal", "We go below the framework when the bottleneck is there: kernels, compilers and the SASS the GPU executes.")]
    vs = "".join(f'<div class="feat"><span class="pc-i">{ic(i)}</span><h3>{t}</h3><p>{d}</p></div>' for i, t, d in vals)
    body = phero("racks-art", "Company", "We make AI fast, small and cheap enough to ship.",
                 "VitalOps is an inference engineering company. We spent years making models run faster for clients, one engagement at a time. The products are those years, written down, so every team can get the result.",
                 [], None)
    body += f'<section class="feats"><div class="wrap">{sec_head("How we work", "Four things we don't compromise on.")}<div class="feat-grid four">{vs}</div></div></section>'
    body += f'<section class="feats alt"><div class="wrap"><div class="split2"><div>{sec_head("Talk to us", "Bring the model and the number.", "Book a 30-minute review, or write to us. We reply within one working day.")}<div class="hero-cta" style="margin-top:20px"><a class="btn btn-p" href="{BOOK}" target="_blank" rel="noopener">{ic("calendar")}Book a review</a><a class="btn btn-s" href="mailto:{MAIL}">{ic("send")}{MAIL}</a></div></div><div class="co-ph" style="background-image:url(\'{{R}}assets/stock/pair-review.jpg\')"></div></div></div></section>'
    page("company/", "Company | VitalOps", "VitalOps is an inference engineering company: software and engineers that make open-weight models fast, small and cheap enough to ship.", "company", body, ctaband=False)

def credits_page():
    cr = json.load(open(os.path.join(HERE, "photo_credits.json")))
    rows = "".join(f'<li><img src="{{R}}assets/photos/{c["file"]}" alt="" loading="lazy"><div><b>{H.escape(c["title"])}</b><span>{H.escape(c["author"])} · {c["license"]} · <a href="{c["page"]}" target="_blank" rel="noopener">source</a></span></div></li>' for c in cr)
    body = f'<section class="lhero"><div class="wrap"><span class="k">Credits</span><h1>Photo credits</h1><p class="lede">Photographs from Wikimedia Commons, used under the licences listed and resized for the web. The office photographs are from Pexels under the Pexels licence. Product screens are illustrations; numbers on them are examples.</p><ul class="credits">{rows}</ul></div></section>'
    page("credits/", "Photo credits | VitalOps", "Photo credits for vitalops.ai.", "credits", body, ctaband=False)

# ───────────────────────── assets ─────────────────────────
def write_assets():
    g = G
    os.makedirs(os.path.join(ROOT, "assets/css"), exist_ok=True)
    css = g["CSS"].replace('url("assets/', 'url("../')
    open(os.path.join(ROOT, "assets/css/vo.css"), "w").write(css)
    open(os.path.join(ROOT, "assets/css/pages.css"), "w").write(open(os.path.join(HERE, "pages.css")).read())
    html = g["HTML"]
    i = html.index("</footer>") + len("</footer>"); j = html.index("</body>")
    scripts = re.findall(r"<script>(.*?)</script>", html[i:j], re.S)
    site_js, play_js = scripts[0], scripts[1]
    open(os.path.join(ROOT, "assets/js/site.js"), "w").write("/* generated by src/pages.py from site.py */\n" + site_js.strip() + "\n" + open(os.path.join(HERE, "pages.js")).read())
    open(os.path.join(ROOT, "assets/js/play.js"), "w").write("/* generated by src/pages.py from site.py */\n" + play_js.strip() + "\n")
    k = html.index('<svg width="0" height="0"'); G["DEFS"] = html[k:html.index("</svg>", k) + 6] + "\n"

def build(g):
    global SCREEN_PLAN_CACHE
    G.update(g)
    write_assets()
    SCREEN_PLAN_CACHE = screen_plan().replace('id="fig-plan"', 'id="fig-plan-s"')
    home(); product_pages(); solution_pages(); lab_page(); platform_page(); services_page(); security_page(); company_page(); credits_page()
    write_all()
    urls = [p for p, _ in PAGES]
    sm = "".join(f"<url><loc>https://vitalops.ai/{u}</loc></url>" for u in urls)
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
