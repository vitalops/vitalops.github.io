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
 "planner":  ("Capacity planner", "Estimate GPU count and cost per million tokens for a model and traffic level.", "gauge"),
 "batching": ("Batching simulator", "See how the batching strategy changes time to first token.", "layers"),
 "quant":    ("Quantisation lab", "Compare FP8, INT4 and NVFP4 error on a layer with outlier weights.", "boxes"),
 "specdec":  ("Speculative decoding", "See how acceptance rate and draft length affect the speed-up.", "zap"),
 "edgefit":  ("Edge fit", "Check whether a model fits on a Jetson, a phone or a Raspberry Pi.", "smartphone"),
 "kernel":   ("Kernel lab", "Occupancy, register pressure and achievable bandwidth, per GPU architecture.", "cpu"),
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
      <p>We make open-weight models run faster and cheaper, on GPU clusters and on devices.</p>
      <p class="foot-soc"><a href="https://github.com/vitalops" target="_blank" rel="noopener" aria-label="GitHub">{lg("github")}</a><a href="https://x.com/vitalopsai" target="_blank" rel="noopener" aria-label="X">X</a><a href="mailto:{MAIL}">{MAIL}</a></p></div>
    <div><h4>Products</h4>{col(PRODUCTS, "products")}</div>
    <div><h4>Solutions</h4>{col(SOLUTIONS, "solutions")}</div>
    <div><h4>Resources</h4><a href="{root}lab/">Live demos</a><a href="{root}platform/">Platform</a><a href="{root}platform/#stack">Supported stack</a><a href="{root}services/">Services</a><a href="{root}services/#engage">How we engage</a></div>
    <div><h4>Company</h4><a href="{root}company/">About</a><a href="{root}security/">Security</a><a href="{BOOK}" target="_blank" rel="noopener">Book a review</a><a href="mailto:{MAIL}">Contact</a><a href="{root}credits/">Photo credits</a></div>
  </div>
  <p class="foot-legal">© <span id="yr">2026</span> VitalOps Inc · vitalops.ai</p>
</div></footer>"""

CTA_DEFAULT = ("Tell us what you need the model to do",
               "Send us the model, the hardware and your target, whether that's tokens per second, latency, memory or cost. In a 30-minute call we'll tell you whether we think it's doable and roughly what it would take.")
def cta(h2=None, lede=None):
    h2, lede = h2 or CTA_DEFAULT[0], lede or CTA_DEFAULT[1]
    return f"""<section class="cta2" id="contact"><div class="wrap cta2-in">
  <div class="cta2-copy"><span class="k">Get started</span><h2>{h2}</h2><p class="lede">{lede}</p>
    <div class="hero-cta"><a class="btn btn-p" href="{BOOK}" target="_blank" rel="noopener">{ic("calendar")}Book an inference review</a><a class="btn btn-s" href="mailto:{MAIL}">{ic("send")}{MAIL}</a></div></div>
  <ol class="cta2-steps">
    <li><b>{ic("calendar")}Review</b><span>A free 30-minute call. We look at your model, hardware and target and give you an honest estimate.</span></li>
    <li><b>{ic("flask-conical")}Sprint</b><span>Two weeks at a fixed fee, on your hardware. If we can't beat your current setup, you don't pay.</span></li>
    <li><b>{ic("server")}Run</b><span>We run Serve and monitoring for you and keep re-tuning as traffic changes, under an agreed SLO.</span></li>
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
    js = ["assets/js/site.js", "assets/js/play.js"] + (["assets/js/hw.js", "assets/js/lab-shell.js"] if demos else []) + [f"assets/js/lab-{d}.js" for d in demos]
    out += "".join(f'\n<script src="{root}{asset(j)}"{" defer" if "lab-" in j or "hw.js" in j else ""}></script>' for j in js) + "\n</body>\n</html>\n"
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

def lab_block(keys, k=None, h2=None, lede=None, id_=None, gpu="h100"):
    """One demo shell with a tab per key (a string or a list); the hardware carousel is the selector."""
    keys = [keys] if isinstance(keys, str) else list(keys)
    t, d, i = DEMOS[keys[0]]
    return f"""<section class="labsec" id="{id_ or 'demo-' + keys[0]}"><div class="wrap">
  <div class="labsec-head"><div><span class="k">{ic("play")}{k or "Live demo"}</span><h2>{h2 or t}</h2><p class="lede">{lede or d}</p></div></div>
  <div class="lab" data-lab-shell data-tabs="{','.join(keys)}" data-gpu="{gpu}"><noscript><p class="lab-ns">This demo needs JavaScript.</p></noscript></div>
</div></section>"""

PRODUCT_PHOTO = {"plan": "racks-art", "optimize": "racks-teal", "sim": "racks-dark", "serve": "gpu-cluster", "edge": "jetson-board", "fleet": "aisle-white"}
def cards(items, base, root="{R}", cls="pcards"):
    def pic(k):
        if base != "products":
            return ""
        return (f'<span class="pc-pic"><span class="pc-ph" style="background-image:url(\'{root}assets/photos/{PRODUCT_PHOTO[k]}.webp\')"></span>'
                f'<img src="{root}assets/screens/{k}.webp" alt="" loading="lazy" width="1132" height="708"></span>')
    return f'<div class="{cls}">' + "".join(
        f'<a class="pcard{" has-pic" if base == "products" else ""}" href="{root}{base}/{k}/">{pic(k)}<span class="pc-body"><span class="pc-i">{ic(v["icon"])}</span><b>{v["name"]}</b><span>{v.get("blurb", v["short"])}</span></span><em>{ic("arrow-up-right")}</em></a>'
        for k, v in items.items()) + "</div>"

def chips(items):
    return '<div class="chips2">' + "".join(f'<span>{lg(s) if s else ""}{t}</span>' for t, s in items) + "</div>"

LOGOS = [("NVIDIA", "nvidia"), ("AMD", "amd"), ("Apple silicon", "apple"), ("Qualcomm", "qualcomm"), ("Arm", "arm"), ("Raspberry Pi", "raspberrypi"),
         ("PyTorch", "pytorch"), ("Hugging Face", "huggingface"), ("Kubernetes", "kubernetes"), ("Llama", "meta"), ("Qwen", "qwen"), ("DeepSeek", "deepseek"), ("Mistral", "mistralai"), ("Gemma", "google")]
def logo_strip(title="Hardware and software we support"):
    items = "".join(f"<span>{lg(s)}{t}</span>" for t, s in LOGOS)
    return f'<section class="logos"><div class="wrap"><p>{title}</p><div class="logo-row"><div class="logo-track">{items}{items.replace("<span>", "<span aria-hidden=\"true\">")}</div></div></div></section>'

# ───────────────────────── lifecycle ─────────────────────────
def vig(k):
    """A small animated picture of each stage's work, drawn to match its title."""
    if k == "plan":
        bars = "".join(f'<g class="pb pb{i}"><text x="14" y="{30 + i * 26}">{n}</text><rect class="tr" x="58" y="{21 + i * 26}" width="150" height="12" rx="3"/><rect class="fl" x="58" y="{21 + i * 26}" width="{w}" height="12" rx="3"/><text class="v" x="{66 + w}" y="{31 + i * 26}">{c}</text></g>'
                       for i, (n, w, c) in enumerate((("L40S", 132, "$0.61"), ("H100", 92, "$0.31"), ("H200", 70, "$0.24"), ("B200", 84, "$0.27"))))
        return f'<svg viewBox="0 0 260 130" class="vg vg-plan" aria-hidden="true">{bars}<path class="ck" d="M232 73l5 5 9-10"/><text class="cap" x="14" y="124">$ per 1M tokens at peak traffic</text></svg>'
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
 dict(k="plan", n="01", t="Plan", h="Choose the hardware", photo="racks-art",
      d="Plan simulates your traffic on each GPU type you're considering and prices the result. You can compare options on latency and cost per million tokens before committing to a purchase or a cloud contract.",
      dl=["GPU type and count per SLO", "Cost per million tokens by option", "Buy-versus-rent break-even", "Headroom for next year's traffic"],
      res=[("−38%", "hardware spend against the first quote"), ("±8%", "forecast against measured throughput")], prods=["plan", "sim"]),
 dict(k="optimize", n="02", t="Optimise", h="Tune the model and server", photo="racks-teal",
      d="Optimize tries changes to the serving engine, quantisation, scheduling, speculative decoding and kernels on your target GPU. Each change is checked against your eval set, and the best configuration is saved as a bundle that can be rerun.",
      dl=["Verified configuration bundle", "Custom kernels, SASS-checked", "Eval report against your floor", "Draft model trained on your traffic"],
      res=[("3.3×", "throughput on the same GPUs"), ("0", "points below your accuracy floor")], prods=["optimize", "sim"]),
 dict(k="deploy", n="03", t="Deploy", h="Roll it out", photo="gpu-cluster",
      d="Serve deploys the bundle to your cloud or data centre as a canary, with one-click rollback. For devices, Edge exports and signs the model for each target. Production runs the same configuration that was benchmarked.",
      dl=["OpenAI-compatible endpoints", "Canary rollouts and rollback", "Device exports: GGUF, MLX, ExecuTorch, TensorRT", "Signed over-the-air updates"],
      res=[("Seconds", "to roll back a release"), ("1", "endpoint for every model you run")], prods=["serve", "edge"]),
 dict(k="operate", n="04", t="Operate", h="Monitor and adjust", photo="racks-dark",
      d="Monitoring tracks time to first token, tokens per second, KV-cache hit rate, cost per million tokens and output quality. When something gets worse it suggests a fix, which can go back through Optimize. Fleet handles scheduling for agent workloads.",
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
  {sec_head("How it fits together", "From buying hardware to running in production", "Click a stage to see what it produces and which products are involved.")}
  <div class="lc"><div class="lc-rail" role="tablist" aria-label="Lifecycle stages">{rail}</div>{"".join(panels)}</div>
  <p class="lc-also">This works the same way for data-centre GPUs and for edge devices: <a href="{{R}}solutions/gpu-clouds/">GPU clouds and data centres {ic("arrow-up-right")}</a> <a href="{{R}}solutions/robotics/">devices in the field {ic("arrow-up-right")}</a></p>
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
        h1="Compare GPU options against your own traffic",
        lede="Plan models how your workload would run on each GPU and cloud instance you're considering, using your model, your latency target and the settings Optimize would use. You get throughput, latency and cost for each option, so the hardware decision is based on numbers.",
        metrics=[("−38%", "hardware spend compared with the first quote"), ("±8%", "forecast error against measured throughput"), ("40+", "GPUs and cloud instance types"), ("Minutes", "to run a scenario")],
        rows=[("01 · Scenarios", "Compare options side by side", "You describe the workload once: the model, prompt and output lengths, arrival rate, expected growth and latency target. Plan simulates the serving engine on each GPU and cloud instance and shows throughput, tail latency, power and cost in one table.", SP,
               [("check", "Options that miss the latency target are flagged."), ("check", "Costs are shown per million tokens as well as per GPU-hour."), ("check", "Buying, reserving and renting are compared, including when buying pays off.")])],
        demo=("planner", "Try a simplified version", "Choose a model, a GPU and a traffic level. This demo uses rough estimates, where decode speed is limited by memory bandwidth and prefill by compute. Plan itself runs a full simulation."),
        feats=[("database", "Detailed hardware catalogue", "Covers H100 to B200, MI300X, L40S, consumer cards and edge modules, including the details that affect results, such as NVLink, memory size, FP8 and FP4 support and interconnect bandwidth."),
               ("trending-up", "Traffic growth", "Add seasonality, launches and growth, and Plan shows when you would run out of capacity."),
               ("badge-check", "Checked against real runs", "Forecasts are compared with Optimize runs on real hardware, and the error is included in the report.")],
        works="NVIDIA H100, H200, B200, GB200, L40S, L4 · AMD MI300X, MI325X · AWS, Google Cloud, Azure, CoreWeave, Lambda and on-prem price books · vLLM, SGLang and TensorRT-LLM performance models.",
        faq=[("Is Plan a spreadsheet?", "No. It simulates the serving engine, scheduler and KV cache against your traffic, using performance models calibrated on measured runs. You can export the results to a spreadsheet."),
             ("Does it account for optimisation?", "Yes. Each option is simulated with the settings Optimize would use on that hardware, so you aren't sizing for an untuned setup."),
             ("Can it plan for edge devices?", "Yes. Edge uses the same performance models, with memory, bandwidth and power per device, to find the largest model that meets your accuracy threshold.")]),
     "optimize": dict(photo="racks-teal", k="Optimize · agentic inference optimisation",
        h1="Get more throughput from the same model and GPUs",
        lede="You give Optimize a model, a target GPU, a latency target and an eval set. It tries changes to the serving engine, quantisation, parallelism, scheduling, speculative decoding and kernels, and only keeps the ones that stay above your accuracy threshold.",
        metrics=[("3.3×", "throughput in a sample run, same GPUs"), ("−55%", "lower p99 time to first token"), ("84.1", "accuracy, above an 83.5 threshold"), ("2 h 14 m", "search time on two H100s")],
        rows=[("01 · Runs", "All runs in one list", "The runs list shows each model and GPU with its best verified result, the speed-up over the baseline and whether it stayed above the accuracy threshold. You can send a result to Serve from here.", g["SCREEN_HERO"],
               [("check", "One run and a report instead of weeks of manual tuning."), ("check", "Each speed-up is reported with its accuracy score."), ("check", "Results are saved as bundles anyone on the team can rerun.")]),
              ("02 · Search", "See what was tried", "Each candidate is a specific change, such as fp8 weights and KV cache, chunked prefill, an EAGLE-3 draft model trained on your traffic, or a fused kernel. Each one is benchmarked on the target GPU and evaluated over several seeds. Anything below the accuracy threshold is rejected.", g["SCREEN_OPT"],
               [("check", "In this run, INT4 was tried and rejected by the eval."), ("check", "Custom kernels are checked numerically and at the SASS level."), ("check", "The best configuration is exported as a bundle.")])],
        demo=("quant", "Quantisation, up close", "This applies real FP8, INT8, INT4 and NVFP4 rounding to a synthetic layer with outlier channels. Optimize does the same with your weights and then checks the result on your eval set."),
        demo2=("specdec", "Speculative decoding", "A small draft model proposes several tokens and the main model checks them in one pass. Optimize trains the draft model on your traffic, which raises the acceptance rate."),
        feats=[("sliders-horizontal", "Covers the whole stack", "Engine choice and settings, weight and KV-cache quantisation, tensor and pipeline parallelism, batching and prefill settings, speculative decoding, CUDA graphs, torch.compile and custom kernels."),
               ("flask-conical", "Your evals decide", "Use lm-eval tasks or your own test set and set a minimum score. Accuracy is reported next to every throughput number, and nothing below the minimum ships."),
               ("package", "Reproducible results", "The winning settings, kernels and draft model are packaged with the exact engine version, so Serve runs what was benchmarked.")],
        works="vLLM, SGLang, TensorRT-LLM, llama.cpp, Hugging Face Transformers · lm-eval or your own evals · targets: tokens/s, TTFT, TPOT, p99, memory, cost per million tokens.",
        faq=[("Which models can it speed up?", "Open-weight models and your own fine-tunes, including Llama, Qwen, DeepSeek, Mistral, Gemma, GLM, Whisper, vision-language models, and embedding and reranker models."),
             ("How do you know the faster model is still correct?", "You set a minimum score on your eval set. Every candidate is tested against it over several seeds and rejected if it falls short. Custom kernels are compared numerically with the reference and inspected at the SASS level."),
             ("Do our weights leave our environment?", "No. Optimize runs in your cloud account or data centre, and evals run where your data already is.")]),
     "sim": dict(photo="racks-dark", k="Sim · a GPU simulator for kernel work",
        h1="Benchmark CUDA kernels without a GPU",
        lede="Sim replaces libcuda.so, so your binary runs unchanged. It loads the compiled kernel into a SASS interpreter, runs it on CPU threads with a timing model, and reports the estimated time on each GPU and where each instruction stalls. It runs on a laptop or in CI.",
        metrics=[("0", "GPUs needed to compare candidates"), ("3", "levels of detail, from milliseconds to hours"), ("0.9+", "rank correlation with real hardware"), ("6", "NVIDIA architectures supported")],
        rows=[("01 · Kernels", "Kernel analysis", "The kernel page shows the SASS produced for each candidate, with the stall percentage for each instruction, register use, occupancy and the estimated time on each target GPU.", g["SCREEN_SIM"],
               [("check", "Kernel work doesn't have to wait for a free GPU."), ("check", "Agents can compare thousands of variants on ordinary CPUs."), ("check", "A slower kernel can fail CI before it reaches real hardware.")]),
              ("02 · Kernel IDE", "Kernel editor with an agent", "The agent edits the CUDA or Triton source, recompiles, reads the new SASS and simulates it. The best version is tested on a real GPU before a pull request is opened.", g["SCREEN_IDE"],
               [("check", "Source, SASS and terminal in one window."), ("check", "Accepted changes are always tested on real hardware."), ("check", "Pull requests include the benchmark numbers.")])],
        flow=True,
        demo=("kernel", "Register pressure, per architecture", "Pick a GPU and a kernel. The occupancy comes from the CUDA occupancy-calculator rules for that architecture, the achievable bandwidth from Little's law, and the bound from a roofline. Sim goes further by interpreting the SASS; this shows the mechanics."),
        feats=[("gauge", "Three levels of detail", "Static analysis takes milliseconds, sampled simulation takes seconds and cycle-level simulation takes hours. Use the fast ones to narrow the candidates down and the slow one to choose between the last few."),
               ("badge-check", "Reports its own error", "Each run reports how closely its ranking matches real hardware, and the top candidates are tested on a real GPU before anything ships."),
               ("git-branch", "Works in CI", "Runs on GitHub Actions or any CPU runner, so a build can fail when a kernel gets slower on a GPU you don't own.")],
        works="CUDA C++, Triton, CUTLASS, PyTorch through a driver shim · KernelBench and TritonBench · GitHub Actions · targets: H100, H200, B200, L40S, RTX 4090 and 5090, Jetson Orin and Thor.",
        faq=[("What do you mean by working at the SASS level?", "We look at what the compiler actually produced: register use, spills, occupancy, shared-memory bank conflicts and stall reasons in the SASS. We don't write SASS by hand; ptxas does. We influence it with PTX intrinsics, launch bounds and compiler flags, then check the output."),
             ("How accurate is a CPU simulation?", "Accurate enough to rank candidates, which is what it's for. Each run reports its rank correlation with real hardware, and nothing ships without a test on a real GPU."),
             ("Does it model AMD GPUs?", "Not yet. Sim only models NVIDIA architectures for now, so we tune AMD kernels on real hardware.")]),
     "serve": dict(photo="gpu-cluster", k="Serve · model serving and monitoring",
        h1="Serve tuned models and monitor them in production",
        lede="Serve is an OpenAI-compatible model server that runs Optimize bundles. It supports several models per pool, continuous batching, prefix caching, chunked prefill, speculative decoding and structured output, along with canary rollouts and monitoring. It runs in your cloud account or data centre.",
        metrics=[("Seconds", "to roll back a release"), ("71%", "prefix-cache hit rate on agent traffic"), ("1", "endpoint for all your models"), ("Air-gapped", "installs supported")],
        rows=[("01 · Pools", "Canary rollouts", "Deploy a bundle to a pool, send it 10% of traffic, and compare latency, cost and errors with the current release. Then promote it or roll it back.", g["SCREEN_SERVE"],
               [("check", "Production runs the configuration that was benchmarked."), ("check", "A rollback takes seconds."), ("check", "All models are served from one endpoint.")]),
              ("02 · Monitoring", "Monitoring", "Serve tracks time to first token, time per output token, tokens per second, KV-cache hit rate, queue depth, cost per million tokens and output quality. You can break these down by model, pool, tenant and prompt template. When a metric gets worse, Serve suggests a fix and can pass it to Optimize.", g["SCREEN_MON"],
               [("check", "See what a prompt change costs within an hour."), ("check", "Sampled evals flag drops in output quality."), ("check", "Also works with existing vLLM, SGLang and TensorRT-LLM deployments.")])],
        demo=("batching", "How batching affects latency", "This simulates a model server. Switch between static and continuous batching, then turn on chunked prefill and prefix caching to see how time to first token changes."),
        feats=[("network", "OpenAI-compatible API", "Supports /v1/chat/completions, /v1/embeddings, tool calls, and JSON-schema and grammar-constrained output. Existing SDKs only need a new base URL."),
               ("git-branch", "Rollouts", "Canaries, traffic splits, shadow traffic and rollback, with a side-by-side comparison against the previous release."),
               ("chart-line", "Inference metrics", "Exports to Prometheus and OpenTelemetry, comes with Grafana dashboards, and sends alerts to PagerDuty and Slack.")],
        works="OpenAI SDKs, LangChain and LlamaIndex · Kubernetes and Slurm · NVIDIA and AMD GPUs · Prometheus, OpenTelemetry, Grafana, PagerDuty and Slack.",
        faq=[("Do we have to use Serve to use Optimize?", "No. Bundles can be exported to standard vLLM, SGLang and TensorRT-LLM. Serve adds rollouts, monitoring and the link back to Optimize."),
             ("Can it monitor our existing deployment?", "Yes. It connects to existing vLLM, SGLang and TensorRT-LLM servers through their metrics endpoints and a small sidecar."),
             ("Where does it run?", "In your cloud account or data centre, including air-gapped environments. We don't see your prompts or outputs.")]),
     "edge": dict(photo="jetson-board", k="Edge · on-device models and training", pos="center 40%",
        h1="Run larger models on phones, Jetsons and Raspberry Pis",
        lede="Edge finds the largest model that stays above your accuracy threshold within each device's memory and latency limits. If data can't leave the device, it can fine-tune there and push the resulting adapter to every device running the same base model.",
        metrics=[("3B", "vision-language model on an 8 GB Jetson"), ("18 MB", "adapter update sent over the air"), ("+2.3 pts", "eval improvement from on-device QLoRA"), ("0 bytes", "of training data sent off the device")],
        rows=[("01 · Devices", "Device fleet", "Edge lists every device with the model it runs, its tokens per second and its free memory, and can run fine-tuning jobs on the devices that hold the data.", g["SCREEN_EDGE"],
               [("check", "Models that didn't fit before can run on a phone, a Pi or a Jetson."), ("check", "Accuracy is checked after each compression step."), ("check", "Updates are signed and rolled out in stages.")])],
        demo=("edgefit", "Check whether a model fits", "Choose a device and a model to see how the weights, KV cache, vision encoder and runtime overhead compare with the memory actually available."),
        feats=[("boxes", "Compression with accuracy checks", "Quantise the weights, KV cache and vision encoder, prune layers if needed, and check accuracy after each step. Edge stops before the model drops below your threshold."),
               ("brain", "On-device training", "QLoRA fine-tuning within the device's memory using gradient checkpointing, with a live loss curve and an estimate of the improvement before you start."),
               ("upload", "Export formats", "GGUF, MLX, ExecuTorch, Core ML, QNN and TensorRT, signed and versioned, with staged rollouts.")],
        works="NVIDIA Jetson Orin and Thor · iPhone and Apple silicon · Pixel and Android NPUs · Qualcomm Snapdragon and Dragonwing · Raspberry Pi 5 with Hailo · x86 and Arm CPUs.",
        faq=[("Can you really train on the edge device?", "On many devices, yes. QLoRA fine-tunes of 1–8B models fit in the memory of a Jetson Orin, an Apple M-series machine or a workstation GPU. Edge plans the job to fit the device and estimates the time and the improvement before it starts."),
             ("What about devices with an NPU?", "Edge exports to Qualcomm QNN, to Apple's Neural Engine through Core ML, and to Hailo on the Raspberry Pi, and checks accuracy again after conversion.")]),
     "fleet": dict(photo="racks-art", k="Fleet · agent fleets on your GPUs",
        h1="Run more AI agents on your own GPUs",
        lede="Agent workloads behave differently from chat. Agents share long prompts, start sub-agents in bursts and sit idle while tools run. Fleet schedules agents across your GPUs, sends requests to GPUs that already have their prompt cached, and frees an agent's slot while it waits on a tool.",
        metrics=[("12×", "more agents per GPU than a default setup"), ("8 → 96", "agents, scaled with one command"), ("64%", "of prompt tokens served from shared prefixes"), ("Air-gapped", "by default")],
        rows=[("01 · Agents", "GPU and agent overview", "See each GPU with its agents, utilisation and KV-cache use, the scheduler's decisions as they happen, and a capacity check that estimates when you would miss the latency target.", g["SCREEN_FLEET"],
               [("check", "More agents per GPU, because cached prompts are reused."), ("check", "Scaling is a single setting."), ("check", "A clear estimate of how many agents your cluster can handle.")])],
        demo=("batching", "Prefix caching with agent traffic", "Select the Agents traffic preset and turn on prefix caching. Shared system prompts and tool definitions are then no longer recomputed on every call."),
        feats=[("network", "Prefix-aware routing", "Requests go to the GPU that already has their prompt prefix cached, so a burst of sub-agents doesn't recompute the same 20k tokens sixteen times."),
               ("pause", "Pausing during tool calls", "While an agent waits on a tool, its slot is given to another agent and its KV cache is kept in memory or offloaded."),
               ("gauge-circle", "Budgets and policies", "Set GPU budgets, priorities and quotas per team. The scheduler enforces them.")],
        works="Claude Agent SDK, OpenAI Agents, LangGraph, or your own loop · Kubernetes and Slurm · air-gapped by default.",
        faq=[("Does Fleet replace our agent framework?", "No. Your agents keep using their framework and call an OpenAI-compatible endpoint. Fleet schedules the inference behind it."),
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
            body += f'<section class="flowband"><div class="wrap"><div class="flow-head"><span class="k">How Sim works</span><h2>From Python to SASS, then simulated on a CPU</h2><p class="lede">The kernel is compiled exactly as it would be for the GPU. Sim then runs the SASS on CPU threads and shows how long that took next to the estimated GPU time.</p></div>{g["FLOW"]}</div></section>'
        if d.get("demo"):
            body += lab_block([d["demo"][0]] + ([d["demo2"][0]] if d.get("demo2") else []), h2=d["demo"][1], lede=d["demo"][2])
        feats = "".join(f'<div class="feat"><span class="pc-i">{ic(i)}</span><h3>{t}</h3><p>{x}</p></div>' for i, t, x in d["feats"])
        body += f'<section class="feats"><div class="wrap">{sec_head("Features", "What's included")}<div class="feat-grid">{feats}</div><div class="works"><h4>Works with</h4><p>{d["works"]}</p></div></div></section>'
        rel = {k: PRODUCTS[k] for k in related[key]}
        body += f'<section class="related"><div class="wrap">{sec_head("Related", "Other products")}{cards(rel, "products")}</div></section>'
        demos = [x[0] for x in (d.get("demo"), d.get("demo2")) if x]
        page(f"products/{key}/", f"{p['name']} · {p['short']} | VitalOps", d["lede"], f"products/{key}", body, faqs=d["faq"], demos=demos)

# ───────────────────────── solutions ─────────────────────────
def solution_pages():
    g = G
    data = {
     "llm-apis": dict(photo="gpu-cluster", k="Solutions · LLM products and APIs",
        h1="Serve more users on the GPUs you have",
        lede="For chat assistants, copilots and model APIs, latency and cost per token decide your margins. We take the model you've already validated and make it faster and cheaper to run.",
        metrics=[("3.3×", "tokens per second on the same GPUs"), ("−69%", "lower cost per million tokens"), ("< 400 ms", "p99 time to first token at peak")],
        pains=[("Latency spikes at peak", "Long prompts hold up short ones, and time to first token goes over the target when traffic is highest."),
               ("Costs grow with usage", "Each new customer means another GPU, because the serving setup still uses its default settings."),
               ("Nobody wants to touch the model", "Teams avoid quantising a model that has passed evaluation, so it stays in bf16.")],
        how=[("plan", "Size the cluster for next year's peak and compare the cost of each option."), ("optimize", "Test quantisation, scheduling, speculative decoding and kernels against your accuracy threshold."), ("serve", "Roll out the result as a canary and track latency and cost per tenant.")],
        fig=g["SCREEN_OPT"], fig_t="Each candidate is benchmarked and evaluated", demo="batching"),
     "agents": dict(photo="racks-teal", k="Solutions · AI agents",
        h1="Run more agents on the same hardware",
        lede="Agent traffic has long shared prompts, bursts of parallel sub-agents and gaps while tools run. Servers built for chat discard the KV cache between calls. We schedule around how agents actually behave.",
        metrics=[("12×", "more agents per GPU"), ("64%", "of prompt tokens from shared prefixes"), ("8 → 96", "agents with one command")],
        pains=[("The same prompt, processed again", "System prompts and tool definitions are processed again on every step of every agent."),
               ("Sub-agent bursts", "When a planner starts sixteen workers at once, everyone else's requests queue up."),
               ("Unknown capacity", "It's unclear how many agents the cluster can run before latency suffers.")],
        how=[("fleet", "Schedule agents across GPUs, routing requests to where their prompt is already cached."), ("serve", "Serve the models your agents use from one endpoint, with prefix caching."), ("plan", "Check capacity before a launch.")],
        fig=g["SCREEN_FLEET"], fig_t="Agents per GPU, live", demo="batching"),
     "multimodal": dict(photo="racks-dark", k="Solutions · vision and multimodal",
        h1="Faster vision-language and speech models",
        lede="Document understanding, visual inspection and speech pipelines include image and audio encoders that most serving setups don't optimise. We tune the encoder, prefill and decode together.",
        metrics=[("2.4×", "throughput on a 7B VLM on one L40S"), ("−60%", "image-encoder latency"), ("3.1×", "Whisper requests per second")],
        pains=[("Encoders add latency", "Each image adds thousands of prefill tokens and an encoder pass before the first output token."),
               ("Memory runs out", "High-resolution images inflate the KV cache, so batch sizes drop."),
               ("Components tuned separately", "OCR, layout, VLM and speech models are each tuned on their own rather than as one pipeline.")],
        how=[("optimize", "Quantise the vision encoder and the language model separately, each checked against the eval."), ("serve", "Batch encoders and decoders separately and cache image tokens."), ("edge", "Run the same VLM on cameras and inspection devices.")],
        fig=g["SCREEN_HERO"], fig_t="VLM and speech model runs in Optimize", demo="quant"),
     "robotics": dict(photo="robot-plant", k="Solutions · robotics and devices", pos="center 60%",
        h1="Run models on the robot instead of in the cloud",
        lede="Inspection robots, drones, cameras and handheld devices often can't wait for a round trip to the cloud or send data off the device. We fit the largest model that meets your accuracy threshold onto the hardware you ship, and it can keep training there.",
        metrics=[("3B", "VLM on an 8 GB Jetson Orin Nano"), ("< 120 ms", "per decision on device"), ("0 bytes", "of field data leaving the device")],
        pains=[("The model is too big", "The model that passed evaluation needs 16 GB and the module has 8."),
               ("No network", "Some sites have no connection, and latency budgets are measured in milliseconds."),
               ("Data can't be moved", "Field data is sensitive or too large to upload for training.")],
        how=[("edge", "Compress with accuracy checks and export for Jetson, Snapdragon, Apple or Hailo."), ("optimize", "Tune kernels for the module's GPU and memory bandwidth."), ("plan", "Find the cheapest device that can run the model you need.")],
        fig=g["SCREEN_EDGE"], fig_t="Devices and the models running on them", demo="edgefit"),
     "gpu-clouds": dict(photo="aisle-white", k="Solutions · GPU clouds and data centres",
        h1="Get more tokens out of every GPU you rent out",
        lede="GPU clouds, inference providers and enterprise data centres sell throughput. We increase tokens per second per GPU, help plan future purchases, and give your customers serving that is already tuned.",
        metrics=[("+2.6×", "median tokens per second per GPU"), ("−38%", "capex against the first quote"), ("40+", "accelerators modelled")],
        pains=[("Low utilisation", "GPUs sit at around 30% because the serving stack can't keep them busy."),
               ("Buying without data", "Hardware orders are based on vendor benchmarks rather than your customers' traffic."),
               ("Customers leave over latency", "Tenants move to whichever provider serves their model fastest.")],
        how=[("plan", "Model next year's fleet against real tenant traffic for each GPU type."), ("optimize", "Provide tuned bundles for the models your customers use most."), ("serve", "Run multi-tenant pools with monitoring and cost per tenant.")],
        fig=SCREEN_PLAN_CACHE, fig_t="Hardware options, simulated and priced", demo="planner"),
     "on-prem": dict(photo="technician", k="Solutions · regulated and on-prem",
        h1="Run models in your own data centre",
        lede="Banks, hospitals, government agencies and manufacturers often need to run open-weight models where their data is. All our software installs inside your environment, including air-gapped networks, and our engineers work there too.",
        metrics=[("0", "prompts or weights leaving your network"), ("Air-gapped", "installs and updates"), ("SSO", "and audit logs on every action")],
        pains=[("Cloud APIs aren't allowed", "Policy rules out hosted models, so the team has to run the whole serving stack itself."),
               ("The hardware is fixed", "The GPUs were bought for three years, but the models keep changing."),
               ("Audit requirements", "Every model change has to be traceable to an evaluation and an approval.")],
        how=[("serve", "Install in your cluster with SSO, role-based access and audit logs."), ("optimize", "Get more out of the GPUs you own, with every change evaluated."), ("fleet", "Run internal agents on-premises with per-team budgets.")],
        fig=g["SCREEN_SERVE"], fig_t="A pool in your own data centre", demo="planner"),
    }
    for key, d in data.items():
        s = SOLUTIONS[key]
        body = phero(d["photo"], d["k"], d["h1"], d["lede"], d["metrics"], None, d.get("pos", "center"))
        pains = "".join(f'<div class="pain"><span class="pn">{i + 1:02d}</span><h3>{t}</h3><p>{x}</p></div>' for i, (t, x) in enumerate(d["pains"]))
        body += f'<section class="pains"><div class="wrap">{sec_head("Common problems", "What usually goes wrong")}<div class="pain-grid">{pains}</div></div></section>'
        how = "".join(f'<a class="hw" href="{{R}}products/{p}/"><span class="pc-i">{ic(PRODUCTS[p]["icon"])}</span><div><b>{PRODUCTS[p]["name"]}</b><p>{t}</p></div>{ic("arrow-up-right")}</a>' for p, t in d["how"])
        body += f'<section class="howsec"><div class="wrap bleed"><div class="split"><div class="step-copy">{sec_head("How we help", "Products involved")}<div class="hws">{how}</div></div><div class="step-shot">{d["fig"]}<p class="fig-cap">{d["fig_t"]}</p></div></div></div></section>'
        body += lab_block(d["demo"], h2=DEMOS[d["demo"]][0])
        others = {k: v for k, v in SOLUTIONS.items() if k != key}
        body += f'<section class="related"><div class="wrap">{sec_head("More solutions", "Other use cases")}{cards(others, "solutions")}</div></section>'
        page(f"solutions/{key}/", f"{s['name']} | VitalOps", d["lede"], f"solutions/{key}", body, demos=[d["demo"]])

SCREEN_PLAN_CACHE = ""

# ───────────────────────── home ─────────────────────────
FAQ_HOME = [
 ("Do we have to send you our weights or data?", "No. Everything runs in your cloud account or data centre, and evals run on your data where it is. During sprints our engineers work inside your environment."),
 ("Which models can you speed up?", "Open-weight models and your own fine-tunes, including Llama, Qwen, DeepSeek, Mistral, Gemma, GLM, Whisper, vision-language models, and embedding and reranker models. We can't speed up closed API models, but we can help with routing, caching and batching around them."),
 ("How do you make sure the faster model is still correct?", "You set a minimum score on your eval set. Every candidate configuration is tested against it over several seeds and rejected if it falls short, however fast it is. Custom kernels are compared numerically with the reference and inspected at the SASS level."),
 ("Can we start with one product?", "Yes. Most teams start with an Optimize sprint on one model, or use Plan before buying hardware. Bundles can also be exported to standard vLLM, SGLang and TensorRT-LLM."),
 ("Do you support AMD or non-NVIDIA hardware?", "We support AMD MI300-class GPUs through ROCm, writing kernels in Triton where we can. Edge supports Apple, Qualcomm, Arm and Hailo devices. Sim only models NVIDIA GPUs for now."),
]

def home():
    g = G
    hero = phero("racks-teal", "AI inference engineering",
                 "Faster, cheaper inference for <em>open-weight models</em>",
                 "We help teams plan, tune and run open-weight models on their own hardware, from GPU clusters to Jetson boards. Every change is tested against your evals before it ships.",
                 [("3.3×", "throughput on the same GPUs in a sample run"), ("−69%", "lower cost per million tokens"), ("−55%", "lower p99 time to first token"), ("84.1", "accuracy, kept above an 83.5 threshold")],
                 [("btn-w", BOOK, "Book an inference review", "calendar", True), ("btn-g", "lab/", "Try the live demos", "play", False)],
                 shot=g["carousel"]([g["SCREEN_HERO"], g["SCREEN_IDE"]], "Optimize · the runs list · a run ships to production as the clip plays"))
    prods = {k: dict(v) for k, v in PRODUCTS.items()}
    blurbs = {"plan": "Estimates throughput, latency and cost for each GPU option, using your traffic.",
              "optimize": "Finds the fastest engine settings, quantisation and kernels that still pass your evals.",
              "sim": "Simulates NVIDIA GPUs on a CPU, so you can benchmark kernels in CI without a GPU.",
              "serve": "An OpenAI-compatible model server with canary rollouts and inference metrics.",
              "edge": "Compresses models to fit phones, Jetsons and Pis, and fine-tunes them on the device.",
              "fleet": "Schedules agent workloads across your GPUs and reuses shared prompt prefixes."}
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
    svc = cut('<section class="svc"', "</section>").replace("</div>\n</div></section>", f'</div>\n<p class="svc-more"><a class="more" href="services/">All services{ic("arrow-up-right")}</a></p></div></section>')
    clients = cut('<section class="clients"', "</section>")
    body = (hero + logo_strip() + lifecycle()
            + f'<section class="prods" id="products"><div class="wrap">{sec_head("Products", "What we build", "Each product can be used on its own. Used together, they share one configuration format, so the setup Plan sizes for is the one Optimize tunes and Serve runs.")}{cards(prods, "products", root="")}</div></section>'
            + ladder + tour
            + f'<section class="labs" id="lab"><div class="wrap">{sec_head("Live demos", "Interactive demos", "Five small tools that run in your browser with no sign-up. They use rough first-order estimates, the same starting point our products use before measuring on real hardware.")}<div class="lcards">{labs}</div></div></section>'
            + f'<section class="sols" id="solutions"><div class="wrap">{sec_head("Solutions", "Where we work")}<div class="scards">{sols}</div></div></section>'
            + svc + clients)
    page("", "VitalOps · Inference optimisation for open-weight models", "VitalOps helps teams plan, tune and run open-weight models on their own hardware: capacity planning, inference optimisation, a GPU simulator for kernels, serving and monitoring, edge deployment and agent scheduling.", "home", body, faqs=FAQ_HOME)

# ───────────────────────── other pages ─────────────────────────
def lab_page():
    order = ["planner", "batching", "kernel", "quant", "specdec", "edgefit"]
    sub = ""
    intro = {"planner": "Estimates how many GPUs you need and the cost per million tokens. It assumes decode is limited by memory bandwidth and prefill by compute, which is where Plan starts before running a full simulation.",
             "batching": "Simulates a model server using static batching, continuous batching, chunked prefill and prefix caching on chat, RAG and agent traffic.",
             "quant": "Applies real FP8, INT8, INT4 and NVFP4 rounding to a synthetic layer with outlier channels, similar to real LLM weights. You can see the effect of group size and outlier protection.",
             "specdec": "A draft model proposes several tokens and the main model checks them in one pass. Adjust the acceptance rate and draft length to find the best setting.",
             "kernel": "Occupancy from the CUDA occupancy-calculator rules for each architecture, the register file and shared memory drawn to scale, spills under a register cap, achievable bandwidth from Little's law and a roofline for the chosen kernel.",
             "edgefit": "Adds up the weights, KV cache, vision encoder and runtime overhead and compares them with the free memory on a Jetson, a phone or a Raspberry Pi. You can also check whether on-device fine-tuning would fit."}
    body = f"""<section class="lhero"><div class="wrap"><span class="k">Live demos</span><h1>Interactive inference demos</h1><p class="lede">Our engineers use tools like these to estimate how a workload will behave before measuring it. Everything runs in your browser and nothing is sent to a server. Pick the hardware at the top of the panel; every tab follows it.</p></div></section>"""
    items = "".join(f'<li><a href="#{k}">{ic(DEMOS[k][2])}<b>{DEMOS[k][0]}</b></a><p>{intro[k]}</p></li>' for k in order)
    body += f'<section class="labsec" id="demos"><div class="wrap"><div class="lab" data-lab-shell data-tabs="{",".join(order)}" data-gpu="h100"><noscript><p class="lab-ns">These demos need JavaScript.</p></noscript></div><ul class="lab-list">{items}</ul></div></section>'

    page("lab/", "Live demos | VitalOps", "Interactive inference tools that run in your browser: a GPU capacity planner, a batching simulator, a kernel occupancy lab, a quantisation lab, a speculative decoding race and an edge memory fit.", "lab", body, demos=order,
         cta_args=("Want real numbers?", "These demos give rough estimates. On a review call we'll look at your actual model and hardware and tell you what's realistic."))

def platform_page():
    g = G
    html = g["HTML"]
    i = html.index('<section class="stack"'); j = html.index("</section>", i) + 10
    stack = html[i:j].replace('<span class="k">Stack</span>', '<span class="k">Supported stack</span>')
    layers = [("Your traffic, models and evals", "Prompts, weights and eval sets stay where they are, and VitalOps reads them there.", "database"),
              ("Plan", "Sizes the hardware for your traffic and latency target.", "gauge"),
              ("Optimize and Sim", "Find and test the best configuration, and compare kernels on CPU.", "zap"),
              ("The bundle", "Engine version, flags, quantised weights, kernels and draft model, measured together.", "package"),
              ("Serve, Edge and Fleet", "Run the bundle on GPUs, devices or agent swarms.", "server"),
              ("Monitoring", "Watches production and sends regressions back to Optimize.", "chart-line")]
    ls = "".join(f'<li><span class="pc-i">{ic(i)}</span><div><b>{t}</b><p>{d}</p></div></li>' for t, d, i in layers)
    deploy = [("Your cloud account", "AWS, Google Cloud, Azure, CoreWeave, Lambda or any Kubernetes cluster. Installed with Helm or Terraform. We don't hold your keys.", "cloud"),
              ("Your data centre", "Bare metal or Kubernetes, Slurm for batch work. NVIDIA and AMD GPUs, InfiniBand or Ethernet.", "server"),
              ("Air-gapped", "Offline installs and signed updates. Nothing connects back to us, and licence checks work offline.", "lock"),
              ("Devices", "Jetson, Apple, Android, Qualcomm, Raspberry Pi and x86. Signed exports and staged over-the-air updates.", "smartphone")]
    ds = "".join(f'<div class="feat"><span class="pc-i">{ic(i)}</span><h3>{t}</h3><p>{d}</p></div>' for t, d, i in deploy)
    body = phero("aisle-white", "Platform", "How the products work together",
                 "All VitalOps products use the same unit, called a bundle. It records the engine version, settings, quantised weights, kernels and draft model that were tested together. The configuration Plan sizes for and Optimize tests is the one Serve, Edge and Fleet run.",
                 [("1", "deployment format across all products"), ("0", "weights or prompts sent outside your environment"), ("4", "deployment options: cloud, data centre, air-gapped, devices")], None)
    body += f'<section class="arch"><div class="wrap"><div class="arch-grid"><div>{sec_head("Architecture", "Architecture", "Each part can be used on its own. Used together, problems found in production can start new Optimize runs, and those results feed back into Plan.")}</div><ol class="arch-l">{ls}</ol></div></div></section>'
    body += f'<section class="feats"><div class="wrap">{sec_head("Deployment", "Where it runs")}<div class="feat-grid four">{ds}</div></div></section>'
    body += stack.replace('class="stack"', 'class="stack" id="stack"', 1)
    body += f'<section class="related"><div class="wrap">{sec_head("Products", "Products")}{cards(PRODUCTS, "products")}</div></section>'
    page("platform/", "Platform | VitalOps", "How VitalOps products fit together, where they deploy and the stack they support.", "platform", body)

def services_page():
    g = G
    html = g["HTML"]
    def cut(start):
        i = html.index(start); j = html.index("</section>", i) + 10
        return html[i:j]
    svc = cut('<section class="svc"')
    eng = cut('<section class="engage"')
    clients = cut('<section class="clients"').replace('src="assets/', 'src="{R}assets/')
    body = phero("technician", "Services", "Fixed-scope engineering work",
                 "We did this work by hand before we built the products, and we still do: two-week tuning sprints, custom kernels, speculative decoding, quantisation, edge deployment and capacity planning, all inside your environment.",
                 [("2 weeks", "for a typical tuning sprint"), ("Fixed fee", "agreed before we start"), ("No fee", "if we can't beat your current setup")], None)
    body += svc + eng + clients
    page("services/", "Services | VitalOps", "Inference optimisation sprints, custom kernels, speculative decoding, quantisation, edge deployment and capacity planning, delivered fixed-scope.", "services", body, faqs=FAQ_HOME[:3])

def security_page():
    items = [("lock", "Data stays in your environment", "The software installs in your cloud account, data centre or air-gapped network. Prompts, outputs, weights and eval sets stay there, and nothing is sent back to us."),
             ("users", "Access control", "Single sign-on with SAML or OIDC, SCIM provisioning, and role-based access for pools, models and runs."),
             ("history", "Audit trail", "Each bundle records the run, the eval and who approved it. Audit logs can be exported to your SIEM."),
             ("shield-check", "Signed artefacts", "Bundles, kernels and device exports are signed and checked before they load. Over-the-air updates roll out in stages."),
             ("key", "Secrets", "Credentials for model registries, clouds and APIs stay in your secrets manager. We read them at runtime and don't store them."),
             ("user", "Our engineers", "During sprints our engineers work in your environment under your access policies, and we keep no copies of your data.")]
    feats = "".join(f'<div class="feat"><span class="pc-i">{ic(i)}</span><h3>{t}</h3><p>{d}</p></div>' for i, t, d in items)
    body = phero("racks-dark", "Security", "Runs inside your environment",
                 "VitalOps is software you install and run yourself, rather than a hosted service. It can run fully air-gapped, and every model change is linked to an evaluation and an approval.",
                 [("0", "prompts or weights leaving your network"), ("Air-gapped", "installs and signed updates"), ("SSO", "SAML and OIDC, with SCIM")], None)
    body += f'<section class="feats"><div class="wrap">{sec_head("Controls", "Security controls")}<div class="feat-grid">{feats}</div></div></section>'
    page("security/", "Security | VitalOps", "VitalOps installs in your environment: no data leaves it, SSO and role-based access, audit logs, signed artefacts and air-gapped installs.", "security", body,
         faqs=[("Do you ever see our prompts or weights?", "No. The products run in your environment and don't send any data about your usage to us. During sprints our engineers work inside your environment under your access controls."),
               ("Can it run with no internet access?", "Yes. Air-gapped installs use offline bundles and signed updates, and licence checks work offline."),
               ("How do you handle a security report?", f"Email {MAIL} with the details. We acknowledge within one working day.")])

def company_page():
    vals = [("badge-check", "We measure", "Any number we give a customer is measured on their model and hardware, with the eval result next to it."),
            ("flask-conical", "Accuracy comes first", "A faster model that gives worse answers isn't an improvement. You set the accuracy threshold and the software enforces it."),
            ("lock", "We don't take your data", "Our software runs in your environment, so your data doesn't need to come to us."),
            ("code", "We go low-level when needed", "If the bottleneck is in a kernel or in the compiler output, that's where we work.")]
    vs = "".join(f'<div class="feat"><span class="pc-i">{ic(i)}</span><h3>{t}</h3><p>{d}</p></div>' for i, t, d in vals)
    body = phero("racks-art", "Company", "About VitalOps",
                 "VitalOps works on inference: making open-weight models run faster and cheaper. We spent several years doing this for clients one project at a time, and built the products from what we learned.",
                 [], None)
    body += f'<section class="feats"><div class="wrap">{sec_head("How we work", "How we work")}<div class="feat-grid four">{vs}</div></div></section>'
    body += f'<section class="feats alt"><div class="wrap"><div class="split2"><div>{sec_head("Contact", "Get in touch", "Book a 30-minute call or email us. We usually reply within a working day.")}<div class="hero-cta" style="margin-top:20px"><a class="btn btn-p" href="{BOOK}" target="_blank" rel="noopener">{ic("calendar")}Book a review</a><a class="btn btn-s" href="mailto:{MAIL}">{ic("send")}{MAIL}</a></div></div><div class="co-ph" style="background-image:url(\'{{R}}assets/stock/pair-review.jpg\')"></div></div></div></section>'
    page("company/", "Company | VitalOps", "VitalOps makes open-weight models run faster and cheaper, with software and engineering services.", "company", body, ctaband=False)

def credits_page():
    cr = json.load(open(os.path.join(HERE, "photo_credits.json")))
    rows = "".join(f'<li><img src="{{R}}assets/photos/{c["file"]}" alt="" loading="lazy"><div><b>{H.escape(c["title"])}</b><span>{H.escape(c["author"])} · {c["license"]} · <a href="{c["page"]}" target="_blank" rel="noopener">source</a></span></div></li>' for c in cr)
    body = f'<section class="lhero"><div class="wrap"><span class="k">Credits</span><h1>Photo credits</h1><p class="lede">Photographs from Wikimedia Commons, used under the licences listed, cropped and resized for the web. The office photographs are from Pexels under the Pexels licence. Product screens are illustrations; numbers on them are examples. The hardware photographs in the live demos are listed here too; where no licensed photo of a part exists, the demo shows a labelled outline instead.</p><ul class="credits">{rows}</ul></div></section>'
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
