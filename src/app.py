
# ───────────────────────── Icons (Lucide, ISC) and brand marks (Simple Icons, CC0; zhipu from LobeHub icons, MIT) ─────────────────────────
import os, re
ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
_used_ic, _used_lg = {}, {}
def _lucide(name):
    s = open(f"{ICON_DIR}/lucide/{name}.svg").read()
    inner = s[s.index(">", s.index("<svg")) + 1 : s.rindex("</svg>")]
    return re.sub(r"\s+", " ", inner).strip()
def _brand(slug):  # (path data, extra attrs): a mark drawn with even-odd filling keeps that rule
    s = open(f"{ICON_DIR}/brands/{slug}.svg").read()
    return re.search(r'<path d="([^"]+)"', s).group(1), (' fill-rule="evenodd"' if 'fill-rule="evenodd"' in s else "")
def ic(name, cls=""):
    _used_ic[name] = 1
    return f'<svg class="ic{(" " + cls) if cls else ""}"><use href="#i-{name}"/></svg>'
BRAND_HEX = {"nvidia":"#76B900","amd":"#ED1C24","qualcomm":"#3253DC","apple":"#000000","intel":"#0071C5","arm":"#0091BD",
 "huggingface":"#FF9D00","github":"#181717","slack":"#4A154B","pagerduty":"#06AC38","grafana":"#F46800","kubernetes":"#326CE5",
 "docker":"#2496ED","pytorch":"#EE4C2C","meta":"#0467DF","mistralai":"#FA520F","alibabacloud":"#FF6A00","qwen":"#615CED",
 "deepseek":"#4D6BFE","google":"#4285F4","microsoft":"#5E5E5E","openai":"#000000","amazonwebservices":"#232F3E","ollama":"#000000",
 "onnx":"#005CED","zhipu":"#3859FF","kimi":"#000000","sentry":"#362D59","cloudflare":"#F38020","datadog":"#632CA6","prometheus":"#E6522C","python":"#3776AB","vercel":"#000000"}
def lg(slug, cls="", mono=False):
    _used_lg[slug] = 1
    style = "" if mono else f' style="color:{BRAND_HEX.get(slug, "#334155")}"'
    return f'<svg class="lg{(" " + cls) if cls else ""}"{style}><use href="#l-{slug}"/></svg>'
def lm(text, bg, fg="#fff"):  # lettermark for a company without a public mark
    return f'<span class="lm" style="background:{bg};color:{fg}">{text}</span>'
def sprite():
    out = ['<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>']
    for n in sorted(_used_ic):
        out.append(f'<symbol id="i-{n}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{_lucide(n)}</symbol>')
    for s in sorted(_used_lg):
        d, extra = _brand(s)
        out.append(f'<symbol id="l-{s}" viewBox="0 0 24 24"><path fill="currentColor"{extra} d="{d}"/></symbol>')
    out.append("</defs></svg>")
    return "".join(out)

# ───────────────────────── App shell pieces ─────────────────────────
def chrome(url):
    return (f'<div class="chrome" aria-hidden="true"><span class="tl"><i></i><i></i><i></i></span>'
            f'<span class="nav-ar">{ic("chevron-left")}{ic("chevron-right")}{ic("rotate-cw")}</span>'
            f'<span class="url">{ic("sliders-horizontal")}<span>{url}</span></span>'
            f'<span class="chrome-r">{ic("star")}{ic("ellipsis")}</span></div>')

def appbar(ws="acme-ml", env="prod"):
    return (f'<div class="appbar"><span class="brand"><svg class="vmark" aria-hidden="true"><use href="#vo-logo"/></svg><b>VitalOps</b></span>'
            f'<span class="ws">{lm("A", "#0ea5e9")}<span>{ws}</span><em class="env">{env}</em>{ic("chevrons-up-down")}</span>'
            f'<span class="search">{ic("search")}<span>Search runs, models, kernels…</span><kbd>⌘K</kbd></span>'
            f'<span class="ibtn">{ic("circle-help")}</span><span class="ibtn bell">{ic("bell")}<i>3</i></span><span class="ibtn">{ic("settings")}</span><span class="av">AK</span></div>')

NAV_ICON = {"Runs":"activity","Models":"box","Targets":"cpu","Evals":"flask-conical","Kernels":"square-terminal","Bundles":"package",
 "Pools":"server","Monitoring":"chart-line","Edge":"smartphone","Fleet":"layers","Endpoints":"network","Rollouts":"git-branch",
 "API keys":"key","Devices":"monitor","Fits":"boxes","Training":"brain","Exports":"upload","Agents":"bot","GPUs":"cpu","Queues":"list-checks",
 "Policies":"shield","Budgets":"gauge-circle","Candidates":"bar-chart-3","Gym":"workflow","Optimize":"sparkles","Serve":"server","Source":"file-code"}
NAV = {
 "runs": [("Optimize", ["Runs*", "Models", "Targets", "Evals", "Kernels", "Bundles"]), ("Serve", ["Pools", "Monitoring"]), ("Edge", ["Devices", "Fits"]), ("Fleet", ["Agents", "GPUs"])],
 "opt":  [("Optimize", ["Runs*", "Models", "Targets", "Evals", "Kernels", "Bundles"]), ("Serve", ["Pools", "Monitoring"]), ("Edge", ["Devices", "Fits"]), ("Fleet", ["Agents", "GPUs"])],
 "kern": [("Optimize", ["Runs", "Models", "Targets", "Evals", "Kernels*", "Bundles"]), ("Serve", ["Pools", "Monitoring"]), ("Edge", ["Devices", "Fits"]), ("Fleet", ["Agents", "GPUs"])],
 "serve":[("Optimize", ["Runs", "Models", "Bundles"]), ("Serve", ["Pools*", "Models", "Endpoints", "Rollouts", "Monitoring", "API keys"]), ("Edge", ["Devices", "Fits"]), ("Fleet", ["Agents", "GPUs"])],
 "mon":  [("Optimize", ["Runs", "Models", "Bundles"]), ("Serve", ["Pools", "Models", "Endpoints", "Rollouts", "Monitoring*", "API keys"]), ("Edge", ["Devices", "Fits"]), ("Fleet", ["Agents", "GPUs"])],
 "edge": [("Optimize", ["Runs", "Models"]), ("Serve", ["Pools", "Monitoring"]), ("Edge", ["Devices*", "Models", "Fits", "Training", "Exports"]), ("Fleet", ["Agents", "GPUs"])],
 "fleet":[("Optimize", ["Runs", "Models"]), ("Serve", ["Pools", "Monitoring"]), ("Edge", ["Devices", "Fits"]), ("Fleet", ["Agents*", "GPUs", "Queues", "Policies", "Budgets"])],
}
NAV_COUNT = {"Runs": "23", "Agents": "48", "Pools": "2", "Fits": "6", "Kernels": "12", "Devices": "6"}
def nav(key, foot, foot_icon="circle-dot"):
    out = ['<nav class="anav">']
    for sec, items in NAV[key]:
        out.append(f'<div class="sec">{sec}</div>')
        for it in items:
            on = it.endswith("*"); it = it.rstrip("*")
            cnt = f"<em>{NAV_COUNT[it]}</em>" if on and it in NAV_COUNT else ""
            out.append(f'<a class="{"on" if on else ""}">{ic(NAV_ICON.get(it, "circle-dot"))}{it}{cnt}</a>')
    out.append(f'<span class="grow-sp"></span><a class="dim">{ic("book-open")}Docs</a><a class="dim">{ic("settings")}Settings</a>')
    out.append(f'<div class="nfoot">{ic(foot_icon, "fi")}{foot}</div></nav>')
    return "".join(out)

STAT_ICON = {"ok": "check", "warn": "triangle-alert", "up": "trending-up", "down": "trending-down"}
def stat(label, value, delta="", cls="", count=True, before=None, icon=None):
    b = f' data-before="{H.escape(before)}"' if before else ""
    i = ic(icon) if icon else (ic(STAT_ICON[cls]) if cls in STAT_ICON else "")
    return f'<div class="stat"><small>{label}</small><b class="{"count" if count else ""}"{b}>{value}</b><span class="{cls}">{i}{delta}</span></div>'

def st(kind, text):  # status: dot + text
    return f'<span class="st {kind}">{text}</span>'

def ab(label, icon=None, kind=""):  # page-header button
    return f'<span class="ab {kind}">{(ic(icon) if icon else "")}{label}</span>'
def ab_logo(label, slug):
    return f'<span class="ab">{lg(slug)}{label}</span>'
def mb(label, icon=None, kind="", act=False):  # pane button; act = the one the cursor presses
    return f'<span class="mb {kind}{" act" if act else ""}">{(ic(icon) if icon else "")}{label}</span>'

def toolbar(chips, q, extra=""):
    c = "".join(f'<span class="{"on" if ch.endswith("*") else ""}">{ch.rstrip("*")}</span>' for ch in chips)
    return (f'<div class="tb"><span class="chips">{c}</span><span class="q">{ic("search")}{q}</span>'
            f'<span class="ibtn">{ic("list-filter")}</span><span class="ibtn">{ic("columns-3")}</span><span class="ibtn">{ic("download")}</span>{extra}</div>')
def pager(text):
    return f'<div class="pg"><span>{text}</span><span class="ibtn">{ic("chevron-left")}</span><span class="ibtn">{ic("chevron-right")}</span></div>'
def bh(title, right="", icons=()):
    r = "".join(f'<span class="ibtn">{ic(i)}</span>' for i in icons)
    return f'<div class="bh">{title}<span class="r"><span class="mu">{right}</span>{r}</span></div>'

def ent(name, slug=None, mark=None):  # entity with a vendor mark
    m = lg(slug) if slug else (mark or "")
    return f'<span class="ent">{m}{name}</span>'
VENDOR = {"Qwen": "qwen", "Llama": "meta", "DeepSeek": "deepseek", "Mistral": "mistralai", "Whisper": "openai", "qwen": "qwen", "llama": "meta"}
def model(name):
    for k, v in VENDOR.items():
        if name.startswith(k):
            return ent(name, v)
    return ent(name, mark=lm("B", "#64748b"))
def gpu_t(name, vendor="nvidia"):
    return ent(name, vendor)

CBX = '<td class="cbx"><i></i></td>'
CBH = '<th class="cbx"><i></i></th>'
RA = f'<td class="ra">{ic("ellipsis")}</td>'
RAH = '<th class="ra"></th>'

def evt(time, icon, text, cls="", step=None):
    s = f' data-step="{step}"' if step else ""
    return f'<div class="evt"{s}><time>{time}</time><span class="ei {cls}">{ic(icon)}</span><span>{text}</span></div>'

def screen(id_, url, navkey, navfoot, main, done=None, toast=None, label="", foot_icon="circle-dot", rail=False, main_cls="", title="", dark=False, accept=False):
    d = f' data-done="{H.escape(done)}"' if done else ""
    t = f' data-toast="{H.escape(toast)}"' if toast else ""
    t += ' data-accept' if accept else ""
    side = globals()["rail"]() if rail else nav(navkey, navfoot, foot_icon)
    return f'<div class="frame" data-title="{H.escape(title)}"><figure class="mock{" dark" if dark else ""}" id="{id_}" role="img" aria-label="{H.escape(label)}"{d}{t}>{chrome(url)}<div class="app" aria-hidden="true">{appbar()}<div class="abody{" has-rail" if rail else ""}">{side}<div class="amain {main_cls}">{main}</div></div></div></figure></div>'

# ───────────────────────── Screens ─────────────────────────
# throughput-over-search data (minutes, tok/s)
SEARCH = [(0,1840),(19,3120),(63,3780),(98,5460),(129,6120)]
search_chart = line_chart(640, 122, (0,134), [dict(cls="brand", pts=SEARCH, step=True, area=True)], (0,7000),
    [(0,"0"),(2000,"2k"),(4000,"4k"),(6000,"6k")], [(0,"00:00"),(30,"00:30"),(60,"01:00"),(90,"01:30"),(120,"02:00")],
    markers=[dict(x=19,y=3120,label="fp8 W8A8 + fp8 KV",step=1,dy=14), dict(x=41,y=3900,label="int4 AWQ · below floor",step=2,cls="bad",dy=-8),
             dict(x=63,y=3780,label="prefix cache + chunked prefill",step=3,dy=14), dict(x=98,y=5460,label="EAGLE-3 draft",step=4,dy=-8),
             dict(x=129,y=6120,label="fused kernel · SASS-verified",step=5,cls="hi",anchor="end",dy=-8)])

RUNS_MAIN = f"""
<div class="ph"><div><div class="crumb">Optimize {ic("chevron-right")} Runs</div><p class="t1">Runs</p></div><div class="actions">{ab("Import model","upload")}{ab("New run","plus","pri")}</div></div>
<div class="stats">{stat("Runs this month","23","+6 vs September","up")}{stat("GPU-hours used","61 / 120","budget","mu")}{stat("Median speed-up","2.6×","across verified runs","ok")}{stat("Bundles shipped","9","+3 this week","up")}</div>
<div class="pane narrow">
  <div>
  <div class="blk">
    {toolbar(["All*","Running","Verified","Shipped"],"model, target, run id…")}
    <table class="tbl">
      <tr>{CBH}<th>Run</th><th>Model</th><th>Target</th><th class="n">Best</th><th class="n">vs base</th><th>Status</th>{RAH}</tr>
      <tr class="sel">{CBX}<td class="mono">run-8841</td><td>{model("Qwen3-32B")}</td><td>{gpu_t("2×H100 SXM")}</td><td class="n count">6,120 tok/s</td><td class="n">3.3×</td><td data-before='{H.escape(st("ok","Verified"))}'>{st("brand","Shipped")}</td>{RA}</tr>
      <tr data-step="1">{CBX}<td class="mono">run-8852</td><td>{model("Llama-3.3-70B")}</td><td>{gpu_t("4×H100 SXM")}</td><td class="n count">2,980 tok/s</td><td class="n">2.1×</td><td>{st("run","Searching · 41%")}</td>{RA}</tr>
      <tr data-step="2">{CBX}<td class="mono">run-8849</td><td>{model("Qwen2.5-VL-7B")}</td><td>{gpu_t("L40S")}</td><td class="n count">1,410 tok/s</td><td class="n">2.4×</td><td>{st("ok","Verified")}</td>{RA}</tr>
      <tr data-step="3">{CBX}<td class="mono">run-8846</td><td>{model("DeepSeek-R1-32B")}</td><td>{gpu_t("2×H100 SXM")}</td><td class="n count">4,870 tok/s</td><td class="n">2.9×</td><td>{st("brand","Shipped")}</td>{RA}</tr>
      <tr data-step="4">{CBX}<td class="mono">run-8840</td><td>{model("Mistral-Small-24B")}</td><td>{gpu_t("RTX 5090")}</td><td class="n count">1,120 tok/s</td><td class="n">1.8×</td><td>{st("warn","Below floor")}</td>{RA}</tr>
      <tr data-step="5">{CBX}<td class="mono">run-8833</td><td>{model("Whisper-large-v3")}</td><td>{gpu_t("A100 40GB")}</td><td class="n count">38 req/s</td><td class="n">3.1×</td><td>{st("brand","Shipped")}</td>{RA}</tr>
      <tr data-step="5">{CBX}<td class="mono">run-8829</td><td>{model("bge-m3")}</td><td>{gpu_t("L4")}</td><td class="n count">2,650 emb/s</td><td class="n">2.2×</td><td>{st("ok","Verified")}</td>{RA}</tr>
    </table>
    {pager("1–7 of 23")}
  </div>
  <div class="blk">{bh("Activity","today",("maximize-2",))}
    <div class="evts">
      {evt("10:14","rocket","run-8841 shipped to prod-a as a 10% canary · by AK","go",6)}
      {evt("10:02","play","run-8852 started · Llama-3.3-70B on 4×H100 · budget 6 GPU-hours","pri",3)}
      {evt("09:48","check","kernel fused_rmsnorm_quant verified on H100 · 18.4 µs · max err 3.1e-4","go",2)}
      {evt("09:31","flask-conical","eval support-qa-v3 updated · 1,200 samples · 3 seeds","",1)}
    </div>
  </div>
  </div>
  <aside class="side">
    <div class="sh"><b>run-8841</b><span class="ibtn">{ic("external-link")}</span></div>
    <div class="kv"><b class="dt">Model</b><span class="dd">{lg("huggingface")}Qwen/Qwen3-32B</span><b class="dt">Target</b><span class="dd">{lg("nvidia")}2×H100 SXM</span><b class="dt">SLO</b><span class="dd">TTFT p99 &lt; 400 ms</span><b class="dt">Eval</b><span class="dd">support-qa-v3 · ≥ 83.5</span><b class="dt">Candidates</b><span class="dd">14 tried · 6 kept</span><b class="dt">Search time</b><span class="dd">2 h 14 m · 2 GPUs</span></div>
    <div class="sh2">Throughput during the search</div>
    {line_chart(300, 112, (0,134), [dict(cls="brand", pts=SEARCH, step=True, area=True)], (0,7000), [(0,"0"),(3000,"3k"),(6000,"6k")], [(0,"0h"),(60,"1h"),(120,"2h")])}
    <div class="kv"><b class="dt">Best candidate</b><span class="dd">#14 · rmsnorm+quant</span><b class="dt">Throughput</b><span class="dd">6,120 tok/s · 3.3×</span><b class="dt">TTFT p99</b><span class="dd">275 ms</span><b class="dt">Accuracy</b><span class="dd">84.1 · floor held</span></div>
    <div class="acts" data-step="6">{mb("Ship to Serve","rocket","go",act=True)}{mb("Open run","arrow-up-right")}</div>
  </aside>
</div>"""
SCREEN_HERO = screen("hero-run","localhost:8080/optimize/runs","runs","2 GPUs busy · 23 runs",RUNS_MAIN,done="✓ Shipped",toast="run-8841 deployed to prod-a · canary 10%",label="Optimize runs list with a selected run's throughput chart and a Ship to Serve action",title="Optimize · the runs list · a run ships to production as the clip plays")

OPT_MAIN = f"""
<div class="ph"><div><div class="crumb">Optimize {ic("chevron-right")} Runs {ic("chevron-right")} run-8841</div><p class="t1">{lg("qwen")}Qwen3-32B → 2×H100 SXM <span class="mu">run-8841</span></p></div><div class="actions">{ab("Report","file-text")}{ab("Export bundle","download")}{ab("Ship to Serve","rocket","go")}</div></div>
<div class="ptabs"><span class="on">Overview</span><span>Candidates <em>14</em></span><span>Kernels <em>2</em></span><span>Evals</span><span>Log</span></div>
<div class="stats">{stat("Throughput","6,120 tok/s","baseline 1,840","up")}{stat("TTFT p99","275 ms","SLO 400 ms","ok")}{stat("Accuracy · support-qa-v3","84.1%","floor 83.5 · base 84.3","mu")}{stat("Cost per 1M tokens","$0.31","was $1.02","down")}</div>
<div class="pane">
  <div>
    <div class="blk">{bh("Tokens/s during the search","2 h 14 m · 2×H100",("maximize-2",))}{search_chart}</div>
    <div class="blk">
      {bh("Candidates","14 tried · 6 kept · 1 rejected by eval",("list-filter","download"))}
      <table class="tbl">
        <tr><th>#</th><th>Change</th><th class="n">tok/s</th><th class="n">TTFT p99</th><th class="n">Acc</th><th>Result</th>{RAH}</tr>
        <tr><td>1</td><td>baseline · vLLM 0.11 · bf16 · TP2</td><td class="n">1,840</td><td class="n">612 ms</td><td class="n">84.3</td><td>{st("mu","reference")}</td>{RA}</tr>
        <tr data-step="1"><td>3</td><td>fp8 W8A8 weights + fp8 KV cache</td><td class="n">3,120</td><td class="n">410 ms</td><td class="n">84.1</td><td>{st("ok","kept")}</td>{RA}</tr>
        <tr data-step="2"><td>5</td><td>int4 AWQ (g128)</td><td class="n">3,900</td><td class="n">352 ms</td><td class="n">82.9</td><td>{st("bad","below floor")}</td>{RA}</tr>
        <tr data-step="3"><td>8</td><td>chunked prefill 2k + prefix cache</td><td class="n">3,780</td><td class="n">288 ms</td><td class="n">84.1</td><td>{st("ok","kept")}</td>{RA}</tr>
        <tr data-step="4"><td>11</td><td>EAGLE-3 draft (k=3), trained on your traffic</td><td class="n">5,460</td><td class="n">291 ms</td><td class="n">84.1</td><td>{st("ok","kept")}</td>{RA}</tr>
        <tr data-step="5" class="sel"><td>14</td><td>fused rmsnorm+quant kernel · SASS-verified</td><td class="n">6,120</td><td class="n">275 ms</td><td class="n">84.1</td><td>{st("brand","best")}</td>{RA}</tr>
      </table>
    </div>
  </div>
  <aside class="side">
    <div class="sh"><b>Best configuration</b><span class="mu ent">{lg("github")}PR #412</span></div>
    <div class="kv"><b class="dt">Engine</b><span class="dd">vLLM 0.11</span><b class="dt">Weights / KV</b><span class="dd">fp8 W8A8 / fp8</span><b class="dt">Parallelism</b><span class="dd">TP=2</span><b class="dt">Spec decode</b><span class="dd" data-before="—">EAGLE-3 · k=3</span><b class="dt">Prefill</b><span class="dd" data-before="default">chunked 2k · prefix</span><b class="dt">Custom kernels</b><span class="dd" data-before="0">2 · SASS-verified</span></div>
    <div class="sh2" data-step="5">Kernel check · fused_rmsnorm_quant · sm_90a</div>
    <div class="kv" data-step="5"><b class="dt">Registers</b><span class="dd">72 / 255</span><b class="dt">Occupancy</b><span class="dd">62%</span><b class="dt">Smem bank conflicts</b><span class="dd">0</span><b class="dt">Top stall</b><span class="dd">long scoreboard 11%</span><b class="dt">Max err vs bf16</b><span class="dd">3.1e-4</span></div>
    <div class="ai" data-step="6"><b>{ic("sparkles")}Agent recommendation</b>Ship #14: 3.3× throughput at accuracy parity. int4 stays rejected under this floor.</div>
    <div class="acts" data-step="6">{mb("Ship to Serve","rocket","go",act=True)}{mb("Re-run · 8 h","refresh-cw")}</div>
  </aside>
</div>"""
SCREEN_OPT = screen("fig-opt","localhost:8080/optimize/runs/run-8841","opt","run-8841 · 2 GPUs busy",OPT_MAIN,done="✓ Shipped",toast="run-8841 deployed to prod-a · canary 10%",label="Optimize run detail: throughput chart, candidates table, best configuration and a SASS-level kernel check")

SERVE_MAIN = f"""
<div class="ph"><div><div class="crumb">Serve {ic("chevron-right")} Pools {ic("chevron-right")} prod-a</div><p class="t1">prod-a <span class="mu">{lg("amazonwebservices")} us-east-1 · {lg("kubernetes")} eks-prod · 8×H100</span></p></div><div class="actions">{ab("Keys","key")}{ab("Scale","sliders-horizontal")}{ab("Deploy bundle","rocket","go")}</div></div>
<div class="ptabs"><span class="on">Overview</span><span>Models <em>3</em></span><span>Requests</span><span>Rollouts <em>1</em></span><span>Logs</span></div>
<div class="stats">{stat("Requests / s","412","peak 590 today","mu")}{stat("Tokens / s","38,900","generation","mu")}{stat("TTFT p99","318 ms","SLO 400 ms","ok")}{stat("Prefix cache hit","71%","KV 84% used","mu")}</div>
<div class="pane">
  <div>
    <div class="blk">
      {bh("Live requests","streaming · last 30 s",("pause","list-filter"))}
      <table class="tbl">
        <tr><th>Request</th><th>Model</th><th class="n">In / out tokens</th><th class="n">TTFT</th><th>Status</th>{RAH}</tr>
        <tr><td class="mono">req-9f21</td><td>{model("qwen3-32b-fp8")}</td><td class="n">3,120 / 212</td><td class="n">141 ms</td><td>{st("ok","done")}</td>{RA}</tr>
        <tr data-step="1"><td class="mono">req-9f22</td><td>{model("qwen3-32b-fp8")}</td><td class="n">18,400 / 64</td><td class="n">296 ms</td><td data-before='{H.escape(st("run","streaming"))}'>{st("ok","done")}</td>{RA}</tr>
        <tr data-step="2"><td class="mono">req-9f23</td><td>{model("llama-3.3-70b-int4")}</td><td class="n">980 / 410</td><td class="n">188 ms</td><td data-before='{H.escape(st("run","streaming"))}'>{st("ok","done")}</td>{RA}</tr>
        <tr data-step="3"><td class="mono">req-9f24</td><td>{model("bge-m3")}</td><td class="n">512 / —</td><td class="n">9 ms</td><td>{st("ok","done")}</td>{RA}</tr>
        <tr data-step="4"><td class="mono">req-9f25</td><td>{model("qwen3-32b-fp8")}</td><td class="n">2,040 / 1,300</td><td class="n">122 ms</td><td>{st("run","streaming")}</td>{RA}</tr>
        <tr data-step="5"><td class="mono">req-9f26</td><td>{model("qwen3-32b-fp8")}</td><td class="n">prefix hit 16k</td><td class="n">48 ms</td><td>{st("run","streaming")}</td>{RA}</tr>
      </table>
    </div>
    <div class="blk">{bh("Tokens/s","last 60 min",("maximize-2",))}{bars([52,58,61,55,70,76,72,81,88,84,95,100],labels=["−60 min","−30","now"])}</div>
  </div>
  <aside class="side">
    <div class="sh"><b>Models in pool</b><span class="mu">9 replicas</span></div>
    <table class="tbl"><tr><th>Model</th><th class="n">Rep.</th><th>Bundle</th></tr>
      <tr><td>{model("qwen3-32b-fp8")}</td><td class="n">6</td><td class="mono">run-8841</td></tr>
      <tr><td>{model("llama-3.3-70b-int4")}</td><td class="n">2</td><td class="mono">run-8702</td></tr>
      <tr><td>{model("bge-m3")}</td><td class="n">1</td><td class="mu">stock</td></tr></table>
    <div class="sh2">Rollout · run-8841 replaces run-8790</div>
    <div class="prog"><span>Canary 10%</span><i><b class="grow" style="width:100%"></b></i><em>passed</em></div>
    <div class="prog" data-step="2"><span>50%</span><i><b class="grow" style="width:100%"></b></i><em>passed</em></div>
    <div class="prog" data-step="4"><span>100%</span><i><b class="grow" style="width:100%"></b></i><em data-before="pending">now</em></div>
    <div class="kv" data-step="3"><b class="dt">TTFT p99 vs previous</b><span class="dd">−41%</span><b class="dt">Cost per 1M tokens</b><span class="dd">−69%</span><b class="dt">Error rate</b><span class="dd">0.02% (=)</span></div>
    <div class="acts" data-step="5">{mb("Promote to 100%","check","go",act=True)}{mb("Rollback","rotate-ccw")}</div>
  </aside>
</div>"""
SCREEN_SERVE = screen("serve-pools","localhost:8080/serve/pools/prod-a","serve","9 replicas healthy",SERVE_MAIN,done="✓ Promoted",toast="run-8841 at 100% · previous bundle kept warm",label="Serve pool overview with live requests, models and a canary rollout being promoted")

ttft_chart = line_chart(640, 150, (0,24), [dict(cls="amber", pts=[(0,330),(3,325),(6,335),(9,330),(9.7,480),(12,560),(15,600),(18,612),(21,610),(24,612)]), dict(cls="brand", pts=[(0,150),(6,148),(12,160),(18,172),(24,175)])],
    (0,700), [(0,"0"),(200,"200"),(400,"400"),(600,"600")], [(0,"−24 h"),(6,"−18"),(12,"−12"),(18,"−6"),(24,"now")],
    markers=[dict(x=9.7,y=480,label="template v12 deployed 09:35",step=1,cls="bad",dy=-8)],
    extra='<line class="slo" x1="28" y1="{y}" x2="634" y2="{y}"/>'.replace("{y}", f"{8 + (1-400/700)*(150-8-18):.1f}"))
MON_MAIN = f"""
<div class="ph"><div><div class="crumb">Serve {ic("chevron-right")} Monitoring</div><p class="t1">Production <span class="mu">all pools · 12 GPUs</span></p></div><div class="actions"><span class="seg small"><span>1h</span><span class="on">24h</span><span>7d</span></span>{ab_logo("Grafana","grafana")}{ab("Export","download")}</div></div>
<div class="ptabs"><span class="on">Overview</span><span>Latency</span><span>Throughput</span><span>Cost</span><span>Quality</span><span>Alerts <em>1</em></span></div>
<div class="stats">{stat("Tokens served · 24 h","1.9B","+12% vs yesterday","up")}{stat("TTFT p99 · all pools","318 ms","prod-b 612 ms","warn")}{stat("Cost per 1M tokens","$0.31","$590 / day","mu")}{stat("Quality drift · sampled eval","−0.2 pts","alert at −1.0","mu",count=False)}</div>
<div class="pane">
  <div>
    <div class="blk">{bh("TTFT p50 / p99 · prod-b · ms","SLO 400 ms (dashed)",("maximize-2",))}{ttft_chart}</div>
    <div class="blk">{bh("Tokens/s by pool","prod-a 31k · prod-b 8k",("maximize-2",))}{bars([48,52,50,58,66,72,70,78,84,90,96,100],labels=["00:00","12:00","now"])}</div>
  </div>
  <aside class="side">
    <div class="sh"><b>{ic("triangle-alert")}Alerts</b><span class="mu">1 open</span></div>
    {evt("09:41","triangle-alert",f"p99 612 ms on prod-b · SLO 400 ms · paged {lg('pagerduty')}","bad")}
    {evt("09:42","trending-down","KV prefix hit on prod-b fell 71% → 44% after prompt template v12","warn",1)}
    {evt("09:43","sparkles","Cause: system prompt v12 breaks the shared prefix · " + lg("slack") + " #inference-oncall","pri",2)}
    <div class="sh2" data-step="4">Cost by model · today</div>
    <div class="hb" data-step="4"><span>{model("qwen3-32b-fp8")}</span><i><b class="grow" style="width:100%"></b></i><em>$412</em></div>
    <div class="hb" data-step="4"><span>{model("llama-3.3-70b-int4")}</span><i><b class="grow" style="width:38%"></b></i><em>$156</em></div>
    <div class="hb" data-step="4"><span>{model("bge-m3")}</span><i><b class="grow" style="width:5%"></b></i><em>$22</em></div>
    <div class="ai" data-step="5"><b>{ic("sparkles")}Agent suggestion</b>Static prefix first in v12; chunked prefill on prod-b. Predicted p99: 290 ms.</div>
    <div class="acts" data-step="5">{mb("Apply via Optimize","sparkles","pri",act=True)}{mb("Snooze 1 h","clock")}</div>
  </aside>
</div>"""
SCREEN_MON = screen("serve-monitor","localhost:8080/serve/monitoring","mon","12 GPUs reporting",MON_MAIN,done="✓ Applied",toast="chunked prefill rolled to prod-b · canary 10% · watching p99",label="Serve monitoring: latency chart against the SLO, cost by model, an alert traced to a prompt-template change, and a suggested fix")

loss_chart = line_chart(640, 122, (0,1000), [dict(cls="brand", pts=[(0,1.42),(100,1.1),(200,.9),(300,.72),(400,.6),(500,.52),(620,.47),(800,.44),(1000,.42)], area=True)], (0,1.6),
    [(0,"0"),(0.5,"0.5"),(1,"1.0"),(1.5,"1.5")], [(0,"step 0"),(250,"250"),(500,"500"),(750,"750"),(1000,"1k")],
    markers=[dict(x=400,y=.6,label="eval +1.1 pts",step=2,dy=-8), dict(x=1000,y=.42,label="eval +2.3 pts · plateau",step=4,cls="hi",anchor="end",dy=-8)])
EDGE_MAIN = f"""
<div class="ph"><div><div class="crumb">Edge {ic("chevron-right")} Devices</div><p class="t1">Field devices <span class="mu">6 online · 2 fine-tuning · 4 serving</span></p></div><div class="actions">{ab("Add device","plus")}{ab("Push adapter","upload","go")}</div></div>
<div class="ptabs"><span class="on">Devices <em>6</em></span><span>Models</span><span>Fits</span><span>Training <em>2</em></span><span>Exports</span></div>
<div class="stats">{stat("Devices online","6 / 6","all reporting","ok")}{stat("Fine-tuning now","2","QLoRA · on device","mu")}{stat("Adapter v3 · eval","+2.3 pts","doc-qa-field · 240 held out","ok",count=False,before="running…")}{stat("Data left the device","0 bytes","samples stay local","ok",count=False)}</div>
<div class="pane">
  <div>
    <div class="blk">{bh("Devices","live · refreshed 5 s ago",("list-filter","refresh-cw"))}
      <table class="tbl"><tr><th>Device</th><th>SoC</th><th>Model</th><th class="n">Decode</th><th>Status</th>{RAH}</tr>
        <tr><td>{gpu_t("Jetson Orin Nano","nvidia")}</td><td class="mu">Orin 8 GB</td><td>{model("Qwen2.5-VL-3B int4")}</td><td class="n">28 tok/s</td><td>{st("ok","serving")}</td>{RA}</tr>
        <tr class="sel"><td>{gpu_t("Pixel 9 Pro","google")}</td><td class="mu">G4 12 GB</td><td>{model("Qwen2.5-1.5B int4")}</td><td class="n">11 tok/s</td><td data-before='{H.escape(st("run","fine-tuning 41%"))}'>{st("run","fine-tuning 62%")}</td>{RA}</tr>
        <tr data-step="1"><td>{gpu_t("iPhone 16 Pro","apple")}</td><td class="mu">A18 8 GB</td><td>{model("Qwen2.5-1.5B int4")}</td><td class="n">14 tok/s</td><td data-before='{H.escape(st("run","fine-tuning 18%"))}'>{st("run","fine-tuning 35%")}</td>{RA}</tr>
        <tr data-step="2"><td>{gpu_t("Raspberry Pi 5","raspberrypi")}</td><td class="mu">A76 8 GB</td><td>{model("Qwen2.5-1.5B int4")}</td><td class="n">9 tok/s</td><td>{st("ok","serving")}</td>{RA}</tr>
        <tr data-step="3"><td>{gpu_t("Dragonwing RB3","qualcomm")}</td><td class="mu">QCS6490 8 GB</td><td>{model("Qwen2.5-VL-3B int4")}</td><td class="n">9 tok/s</td><td data-before='{H.escape(st("warn","flashing 80%"))}'>{st("ok","serving")}</td>{RA}</tr>
        <tr data-step="3"><td>{gpu_t("Jetson AGX Thor","nvidia")}</td><td class="mu">Thor 128 GB</td><td>{model("Qwen2.5-VL-7B fp8")}</td><td class="n">38 tok/s</td><td>{st("ok","serving")}</td>{RA}</tr>
      </table>
    </div>
    <div class="blk">{bh("Live fine-tune · Pixel 9 Pro · QLoRA r=16","training loss · 1,200 samples on device",("maximize-2",))}{loss_chart}</div>
  </div>
  <aside class="side">
    <div class="sh"><b>{ic("brain")}Training job</b><span class="mu">pixel-9-pro-02</span></div>
    <div class="kv"><b class="dt">Base</b><span class="dd">{lg("qwen")}Qwen2.5-1.5B · int4</span><b class="dt">Method</b><span class="dd">QLoRA r=16 · 4-bit base</span><b class="dt">Data</b><span class="dd">1,200 samples · on device</span><b class="dt">Step</b><span class="dd" data-before="620 / 1,000">1,000 / 1,000</span><b class="dt">Loss</b><span class="dd" data-before="0.47">0.42</span><b class="dt">Peak memory</b><span class="dd">2.8 GB / 12 GB</span><b class="dt">Elapsed</b><span class="dd" data-before="14 min">22 min</span><b class="dt">Thermal</b><span class="dd">41 °C · no throttling</span></div>
    <div class="sh2" data-step="4">After training</div>
    <div class="kv" data-step="4"><b class="dt">Eval · doc-qa-field</b><span class="dd">+2.3 pts</span><b class="dt">Adapter size</b><span class="dd">18 MB</span><b class="dt">Signed</b><span class="dd">yes · OTA field-v3</span></div>
    <div class="ai" data-step="5"><b>{ic("sparkles")}Result</b>Loss plateaued at 0.42; eval +2.3 pts on 240 held-out samples. Push v3 to the fleet.</div>
    <div class="acts" data-step="5">{mb("Push adapter v3","upload","go",act=True)}{mb("Pause","pause")}</div>
  </aside>
</div>"""
SCREEN_EDGE = screen("fig-edge","localhost:8080/edge/devices","edge","6 devices · 2 training",EDGE_MAIN,done="✓ Pushed",toast="adapter v3 pushed to 4 devices · 18 MB · signed · OTA",label="Edge devices: a fleet of phones, Pis and Jetsons serving small models, two of them fine-tuning on device with a live loss curve, and an adapter pushed to the fleet",foot_icon="wifi")

def gpu(name, util, agents, kv, cls="", step=None, before=None):
    s = f' data-step="{step}"' if step else ""
    return f'<div class="gpu"{s}><b>{lg("nvidia")}{name}<span>{util}%</span></b><i><em class="grow {cls}" style="width:{util}%"></em></i><small>{agents} agents · KV {kv} GB</small></div>'
FLEET_MAIN = f"""
<div class="ph"><div><div class="crumb">Fleet {ic("chevron-right")} Agents</div><p class="t1">On-prem cluster <span class="mu">8×H100 · air-gapped</span></p></div><div class="actions">{ab("Policies","shield")}{ab("Scale","sliders-horizontal","pri")}</div></div>
<div class="ptabs"><span class="on">Agents <em>48</em></span><span>GPUs <em>8</em></span><span>Queues</span><span>Budgets</span></div>
<div class="stats">{stat("Agents running","96","scaling · 96 scheduled","ok",before="48")}{stat("GPU utilisation","91%","8 × H100","mu")}{stat("Prefix shared across agents","64%","of prompt tokens","mu")}{stat("Step latency p99","1.9 s","SLO 3.0 s","ok")}</div>
<div class="pane">
  <div>
    <div class="blk">{bh("GPU map","agents per GPU · KV resident",("refresh-cw",))}
      <div class="gpus">{gpu("gpu-0",94,7,71)}{gpu("gpu-1",92,6,68)}{gpu("gpu-2",96,8,77,"warn")}{gpu("gpu-3",88,6,62)}{gpu("gpu-4",90,6,66)}{gpu("gpu-5",93,6,70)}{gpu("gpu-6",89,5,61)}{gpu("gpu-7",71,4,48,step=3)}</div>
    </div>
    <div class="blk">{bh("Agent steps / s","last 10 min",("maximize-2",))}{bars([60,64,70,66,78,82,80,88,92,100],labels=["−10 min","−5","now"])}</div>
  </div>
  <aside class="side">
    <div class="sh"><b>{ic("workflow")}Scheduler events</b><span class="mu">KV-aware</span></div>
    {evt("14:02","clock","agent-17 waiting on tool (browser) → KV offloaded to CPU","")}
    {evt("14:02","zap","agent-22 prefix hit: 18k tokens shared from agent-09","go",1)}
    {evt("14:03","flame","gpu-2 hot (96%) → next 3 steps routed to gpu-7","warn",2)}
    {evt("14:03","arrow-right-left","4 agents migrated to gpu-7 with KV","pri",3)}
    {evt("14:04","check","agent-17 tool returned → KV restored, 0.3 s","go",4)}
    {evt("14:05","users","scale request from team research: 48 → 96 agents","",5)}
    <div class="sh2" data-step="5">Capacity check</div>
    <div class="kv" data-step="5"><b class="dt">Max agents at SLO</b><span class="dd">112</span><b class="dt">After scaling</b><span class="dd">96 · 86% of capacity</span><b class="dt">Predicted p99 step</b><span class="dd">2.6 s</span></div>
    <div class="acts" data-step="5">{mb("Scale to 96","sliders-horizontal","pri",act=True)}{mb("Pause pool","pause")}</div>
  </aside>
</div>"""
SCREEN_FLEET = screen("fig-fleet","localhost:8080/fleet/agents","fleet","air-gapped · healthy",FLEET_MAIN,done="✓ Scaling",toast="96 agents scheduled across 8 GPUs · p99 within SLO",label="Fleet: GPU map with agents per GPU, scheduler events and a scale-up action",foot_icon="shield-check")

def sass(addr, instr, pct, cls="", step=None):
    s = f' data-step="{step}"' if step else ""
    return f'<div class="sl"{s}><span class="a">{addr}</span><span class="i">{instr}</span><span class="h"><i class="grow {cls}" style="width:{pct*4}%"></i></span><span class="c">{pct:.1f}%</span></div>'
SIM_MAIN = f"""
<div class="ph"><div><div class="crumb">Optimize {ic("chevron-right")} Kernels {ic("chevron-right")} fused_rmsnorm_quant</div><p class="t1">{ic("file-code")}fused_rmsnorm_quant.py <span class="mu">sm_90a · no GPU attached</span></p></div><div class="actions">{ab("Diff vs v3","git-branch")}{ab("Run","play","pri")}</div></div>
<div class="ptabs"><span>Source</span><span class="on">SASS</span><span>Targets <em>4</em></span><span>Candidates <em>212</em></span><span>Gym</span></div>
<div class="stats">{stat("Predicted · H100","18.4 µs","stock path 41.2 µs","ok")}{stat("Occupancy","62%","4 blocks / SM","mu")}{stat("Registers · smem","72 · 16 KB","no spills","mu",count=False)}{stat("Rank correlation","0.93","vs last H100 run","ok")}</div>
<div class="pane">
  <div>
    <div class="blk code">{bh("SASS · hottest basic block","stall share · sampled mode",("copy","maximize-2"))}
      {sass("0120",'<b>LDG.E.128</b> R4, [R2.64]',22.0,"bad")}{sass("0130",'<b>LDG.E.128</b> R8, [R2.64+0x10]',15.5,"bad",1)}{sass("0140",'<b>FMUL</b> R12, R4, R16',2.0,"ok",1)}{sass("0150",'<b>FFMA</b> R12, R5, R5, R12',2.5,"ok",2)}{sass("0160",'<b>SHFL.BFLY</b> PT, R13, R12, 0x10, 0x1f',7.5,"warn",2)}{sass("0170",'<b>MUFU.RSQ</b> R14, R13',6.5,"warn",3)}{sass("0180",'<b>F2FP.E4M3.PACK_AB</b> R20, R19, R18',3.0,"ok",3)}{sass("0190",'<b>STG.E.64</b> [R6.64], R20',8.5,"warn",4)}{sass("01a0",'<b>BAR.SYNC.DEFER_BLOCKING</b> 0x0',11.0,"bad",4)}
      <div class="sl mu" data-step="4"><span class="a">…</span><span class="i">31 more instructions · long scoreboard dominates · loads 100% coalesced</span><span></span><span></span></div>
    </div>
    <div class="blk">{bh("Candidate ranking","212 variants · static mode 0.4 s",("list-filter",))}
      <table class="tbl"><tr><th>#</th><th>Variant</th><th class="n">H100</th><th class="n">B200</th><th>Status</th>{RAH}</tr>
        <tr class="sel"><td>1</td><td>vec4 loads · 2 rows / warp</td><td class="n">18.4 µs</td><td class="n">9.7 µs</td><td>{st("brand","best")}</td>{RA}</tr>
        <tr data-step="4"><td>2</td><td>vec4 · 1 row / warp</td><td class="n">19.1 µs</td><td class="n">10.2 µs</td><td>{st("mu","within 4%")}</td>{RA}</tr>
        <tr data-step="4"><td>3</td><td>vec2 · smem reduce</td><td class="n">21.8 µs</td><td class="n">11.9 µs</td><td>{st("mu","within 20%")}</td>{RA}</tr>
        <tr data-step="5"><td>4</td><td>cp.async pipeline, 2 stages</td><td class="n">22.6 µs</td><td class="n">12.4 µs</td><td>{st("mu","")}</td>{RA}</tr></table>
    </div>
  </div>
  <aside class="side">
    <div class="sh"><b>Predicted across targets</b><span class="mu">sampled</span></div>
    <table class="tbl"><tr><th>Target</th><th class="n">Predicted</th><th class="n">Stock</th></tr>
      <tr><td>{gpu_t("H100 SXM")}</td><td class="n">18.4 µs</td><td class="n">41.2 µs</td></tr>
      <tr data-step="2"><td>{gpu_t("B200")}</td><td class="n">9.7 µs</td><td class="n">22.8 µs</td></tr>
      <tr data-step="3"><td>{gpu_t("L40S")}</td><td class="n">44.1 µs</td><td class="n">96.0 µs</td></tr>
      <tr data-step="3"><td>{gpu_t("RTX 5090")}</td><td class="n">21.3 µs</td><td class="n mu">static</td></tr></table>
    <div class="sh2" data-step="4">This run</div>
    <div class="kv" data-step="4"><b class="dt">Static</b><span class="dd">212 variants · 0.4 s</span><b class="dt">Sampled</b><span class="dd">top 20 · 38 s</span><b class="dt">Functional check</b><span class="dd">PTX oracle · pass</span><b class="dt">Determinism</b><span class="dd">bit-exact replay</span></div>
    <div class="ai" data-step="5"><b>{ic("sparkles")}Next</b>Top 3 within 20%: verify on a real H100 before shipping. ~1 GPU-minute.</div>
    <div class="acts" data-step="5">{mb("Verify on H100","play","pri",act=True)}{mb("Add to gym","plus")}</div>
  </aside>
</div>"""
SCREEN_SIM = screen("fig-sim","localhost:8080/optimize/kernels/fused_rmsnorm_quant","kern","CPU sim · nvcc 13.x",SIM_MAIN,done="✓ Queued",toast="verification queued on a real H100 · ~1 GPU-minute",label="Optimize kernels page: SASS listing with stall shares, candidate ranking and predicted times per GPU, simulated with no GPU attached",foot_icon="cpu",title="Kernels · the SASS listing, candidate ranking and predicted times per GPU")

# ───────────────────────── Kernel IDE screen (hero slide 2) ─────────────────────────
KW = {"template","__global__","__launch_bounds__","const","int","float","for","if","return","void","__restrict__","reinterpret_cast","unroll","pragma"}
TY = {"bf16","bf16x8","fp8_e4m3","uint4","float4"}
def hl(line):
    code, cm = (line.split("//", 1) + [""])[:2] if "//" in line else (line, "")
    out = []
    if code.lstrip().startswith("#"):
        out.append(f'<span class="pp">{H.escape(code)}</span>')
    else:
        for tok in re.split(r'([A-Za-z_][A-Za-z0-9_]*(?=\()|[A-Za-z_][A-Za-z0-9_]*|\b\d[\d.]*f?\b)', code):
            if not tok: continue
            e = H.escape(tok)
            if tok in KW: out.append(f'<span class="kw">{e}</span>')
            elif tok in TY: out.append(f'<span class="ty">{e}</span>')
            elif re.fullmatch(r'\d[\d.]*f?', tok): out.append(f'<span class="nu">{e}</span>')
            elif re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', tok) and code[code.find(tok)+len(tok):code.find(tok)+len(tok)+1] == "(" and tok not in KW: out.append(f'<span class="fn">{e}</span>')
            else: out.append(e)
    if cm: out.append(f'<span class="cm">//{H.escape(cm)}</span>')
    return "".join(out)
def cl(n, new, old=None, step=None, cur=False):
    inner = lambda src, add: f'<i class="ln">{n}</i><i class="g">{"+" if add else ""}</i><span>{hl(src)}</span>'
    attrs = (f' data-step="{step}"' if step else "") + (f" data-before='{H.escape(inner(old, False))}'" if old is not None else "")
    return f'<div class="cl{" add" if old is not None else ""}{" cur" if cur else ""}"{attrs}>{inner(new, old is not None)}</div>'
CODE = [
 (1, '#include "vo/warp.cuh"  // bf16x8, fp8x8, shuffles', None, None),
 (2, 'template <int kRowsPerWarp>', 'template <int kBlock>', 3),
 (3, '__global__ void __launch_bounds__(256)', None, None),
 (4, 'fused_rmsnorm_quant(const bf16* __restrict__ x,', None, None),
 (5, '    const bf16* __restrict__ w,', None, None),
 (6, '    fp8_e4m3* __restrict__ out,', None, None),
 (7, '    float* __restrict__ scale, int n, float eps) {', None, None),
 (8, '  const int lane = threadIdx.x & 31;', None, None),
 (9, '  const int row = blockIdx.x * kRowsPerWarp + warp();', '  const int row = blockIdx.x;', 3),
 (10,'  const uint4* xv = (const uint4*)(x + row * n);', '  const bf16* xr = x + row * n;', 3),
 (11,'  float ss = 0.f;', None, None),
 (12,'  #pragma unroll 4', '', 3),
 (13,'  for (int i = lane; i < n / 8; i += 32) {', '  for (int i = threadIdx.x; i < n; i += 256) {', 3),
 (14,'    bf16x8 v = unpack(__ldg(xv + i));      // LDG.E.128', '    float v = __bfloat162float(xr[i]);    // LDG.E.U16', 3),
 (15,'    ss += dot8(v, v);', '    ss += v * v;', 3),
 (16,'  }', None, None),
 (17,'  ss = warp_reduce_sum(ss);              // SHFL.BFLY', '  ss = block_reduce_sum(ss);             // BAR.SYNC', 4),
 (18,'  const float rstd = rsqrtf(ss / n + eps);  // MUFU.RSQ', None, None),
 (19,'  const float s = warp_max(absmax8(xv, rstd)) / 448.f;', '  const float s = block_max(absmax(xr, rstd)) / 448.f;', 4),
 (20,'  if (lane == 0) scale[row] = s;', '  if (threadIdx.x == 0) scale[row] = s;', 4),
 (21,'  for (int i = lane; i < n / 8; i += 32)', '  for (int i = threadIdx.x; i < n; i += 256)', 4),
 (22,'    store_fp8x8(out + row * n + i * 8,     // F2FP.E4M3', '    out[row*n+i] = to_fp8(xr[i]*rstd*w[i], 1.f/s);', 4),
 (23,'      unpack(__ldg(xv + i)) * rstd * wv(w, i), 1.f / s);', '', 4),
 (24,'}', None, None),
]
CODE_HTML = "".join(cl(n, new, old, step, cur=(n == 14)) for n, new, old, step in CODE)

def sr(addr, instr, pct, cls="", step=None, before=None, mapped=False):
    s = f' data-step="{step}"' if step else ""
    b = f" data-before='{H.escape(before)}'" if before else ""
    return f'<div class="sr {cls}{" map" if mapped else ""}"{s}{b}><span class="a">{addr}</span><span class="i">{instr}</span><span class="c">{pct}</span></div>'
SASS_ROWS = (
    sr("0120", "<b>LDG.E.128</b> R4, [R2.64]", "22.0%", "bad", step=3, before='<span class="a">0120</span><span class="i"><b>LDG.E.U16</b> R4, [R2.64]</span><span class="c">31.0%</span>', mapped=True) +
    sr("0130", "<b>LDG.E.128</b> R8, [R2+0x10]", "15.5%", "bad", step=3, before='<span class="a">0130</span><span class="i"><b>LDG.E.U16</b> R5, [R2+0x2]</span><span class="c">19.5%</span>', mapped=True) +
    sr("0140", "<b>PRMT</b> R12, R4, 0x5410, RZ", "1.0%") +
    sr("0150", "<b>FMUL</b> R12, R12, R12", "2.0%", "ok") +
    sr("0160", "<b>FFMA</b> R12, R13, R13, R12", "2.5%", "ok") +
    sr("0170", "<b>FFMA</b> R12, R14, R14, R12", "2.0%", "ok") +
    sr("0180", "<b>SHFL.BFLY</b> R13, R12, 0x10", "7.5%", "warn", step=4, before='<span class="a">0180</span><span class="i"><b>BAR.SYNC.DEFER_BLOCKING</b></span><span class="c">11.0%</span>') +
    sr("0190", "<b>FADD</b> R12, R12, R13", "1.5%", "ok") +
    sr("01a0", "<b>SHFL.BFLY</b> R13, R12, 0x8", "6.0%", "warn", step=4, before='<span class="a">01a0</span><span class="i"><b>LDS</b> R13, [R1]</span><span class="c">4.0%</span>') +
    sr("01b0", "<b>MUFU.RSQ</b> R14, R13", "6.5%", "warn") +
    sr("01c0", "<b>FMUL</b> R20, R4, R14", "1.0%", "ok") +
    sr("01d0", "<b>F2FP.E4M3.PACK_AB</b> R20", "3.0%", "ok") +
    sr("01e0", "<b>STG.E.64</b> [R6.64], R20", "8.5%", "warn") +
    sr("01f0", "<b>EXIT</b>", "0.0%") +
    sr("…", "26 more · 0 spills", "", "mu", step=4))

def tl(text, cls="", step=None):
    s = f' data-step="{step}"' if step else ""
    return f'<div class="tl {cls}"{s}>{text}</div>'
def am(icon, html, cls="", step=None):
    s = f' data-step="{step}"' if step else ""
    return f'<div class="am"{s}><span class="ei {cls}">{ic(icon)}</span><span>{html}</span></div>'

def rail(active="Optimize"):
    items = [("Optimize", "sparkles"), ("Serve", "server"), ("Edge", "smartphone"), ("Fleet", "layers")]
    out = ['<nav class="anav rail">'] + [f'<a class="{"on" if n == active else ""}" title="{n}">{ic(i)}</a>' for n, i in items]
    out.append(f'<span class="grow-sp"></span><a class="dim">{ic("book-open")}</a><a class="dim">{ic("settings")}</a><div class="nfoot">{ic("circle-dot", "fi")}</div></nav>')
    return "".join(out)

IDE_MAIN = f"""
<div class="ide">
  <div class="xp">
    <div class="xh">Explorer</div>
    <a>{ic("chevron-down")}acme-ml/serving</a>
    <a class="d1">{ic("chevron-down")}kernels</a>
    <a class="d2 on">{ic("file-code")}rmsnorm_quant.cu<i class="mod"></i></a>
    <a class="d2">{ic("file-code")}rmsnorm_quant.ptx</a>
    <a class="d2">{ic("file-code")}rmsnorm_quant.sass</a>
    <a class="d2">{ic("file-code")}rope_fp8.cu</a>
    <a class="d2">{ic("file-code")}paged_attn.cu</a>
    <a class="d1">{ic("chevron-down")}bench</a>
    <a class="d2">{ic("file-code")}bench_rmsnorm.py</a>
    <a class="d2">{ic("file-text")}targets.yaml</a>
    <a class="d1">{ic("chevron-right")}evals</a>
    <a class="d1">{ic("file-text")}README.md</a>
    <div class="xh" style="margin-top:10px">Sim targets</div>
    <div class="tg"><span>{lg("nvidia")}H100 SXM</span><em data-before="41.2 µs">18.4 µs</em></div>
    <div class="tg" data-step="5"><span>{lg("nvidia")}B200</span><em>9.7 µs</em></div>
    <div class="tg" data-step="5"><span>{lg("nvidia")}L40S</span><em>44.1 µs</em></div>
    <div class="tg" data-step="5"><span>{lg("nvidia")}RTX 5090</span><em>21.3 µs</em></div>
  </div>
  <div class="ed">
    <div class="etabs"><span class="on">{ic("file-code")}rmsnorm_quant.cu<i class="mod"></i></span><span class="sp"></span><span class="ibtn">{ic("git-branch")}</span><span class="ibtn">{ic("play")}</span></div>
    <div class="code-area">{CODE_HTML}</div>
  </div>
  <div class="sv">
    <div class="etabs"><span>PTX</span><span class="on">SASS</span><span class="sp"></span><span class="ibtn">{ic("copy")}</span></div>
    <div class="sh3"><span>sm_90a · stall share</span><span>line 14</span></div>
    {SASS_ROWS}
  </div>
  <div class="term">
    <div class="etabs"><span class="on">{ic("square-terminal")}Terminal</span><span>Problems</span><span>Output</span><span>Sim</span><span class="sp"></span><span class="ibtn">{ic("plus")}</span><span class="ibtn">{ic("trash-2")}</span></div>
    <div class="tls">
      {tl("vo profile k.cu --gpu h100-0  →  41.2 µs · 71% long-scoreboard stalls · LDG.E.U16 ×8", "cmd")}
      {tl("nvcc -arch=sm_90a -O3 -Xptxas -v rmsnorm_quant.cu -o k.cubin", "cmd", 4)}
      {tl("ptxas info    : Used <span class='hi'>72 registers</span>, 16384 bytes smem, <span class='hi'>0 bytes spill</span> stores", "", 4)}
      {tl("vo sim k.cubin --target h100 --mode sampled", "cmd", 5)}
      {tl("predicted <span class='hi'>18.4 µs</span>  (stock 41.2 µs · 2.24×)  ·  rank 1 / 212  ·  rank-corr 0.93", "", 5)}
      {tl("vo verify k.cubin --gpu h100-0 --oracle ptx", "cmd", 6)}
      {tl("h100-0: <span class='hi'>18.6 µs</span>  ·  max_err 3.1e-4  ·  <span class='ok'>PASS</span>", "", 6)}
    </div>
  </div>
  <div class="ag">
    <div class="agh">{ic("sparkles")}Kernel agent<span class="mu">H100 · 20 min budget</span></div>
    <div class="ams">
      {am("gauge", "<b>Goal</b> · fused_rmsnorm_quant under 20 µs on H100, bit-exact vs the bf16 reference.")}
      {am("activity", "<b>Profiled</b> · 41.2 µs. 71% of stalls: long scoreboard. 16-bit loads, BAR.SYNC reduce.", "", 1)}
      {am("list-checks", "<b>Plan</b> · 128-bit loads, two rows per warp, warp-level reductions; fp8 epilogue stays fused.", "pri", 2)}
      {am("pencil", "<b>Edited</b> rmsnorm_quant.cu <span class='diff'><span class='p'>+11</span> <span class='m'>−9</span></span> · vectorised the load path.<span class='chips2'>" + mb("Accept","check","go",act=True) + mb("Reject","x") + "<span class='acc-note'>" + ic("check") + "Accepted · saved</span></span>", "pri", 3)}
      {am("check", "<b>Compiled</b> sm_90a · 72 registers, no spills, 0 bank conflicts.", "go", 4)}
      {am("gauge", "<b>Sim</b> · 18.4 µs predicted, rank 1 of 212 variants. B200 9.7 µs.", "pri", 5)}
      {am("badge-check", "<b>Verified on h100-0</b> · 18.6 µs, max error 3.1e-4, 2.2× over stock. Opened PR #413.", "go", 6)}
    </div>
    <div class="agf">
      <div class="ask">{ic("sparkles")}<span>Ask the agent or add a constraint…</span>{ic("send-horizontal")}</div>
    </div>
  </div>
  <div class="sb"><span>{ic("git-branch")}main*</span><span>CUDA C++</span><span>sm_90a</span><span>nvcc 13.0 · PTX 8.8</span><span>Ln 14, Col 5</span><span class="r">{ic("cpu")}h100-0 idle</span><span>{ic("check")}Sim ready</span></div>
</div>"""
SCREEN_IDE = screen("hero-ide","localhost:8080/optimize/kernels/fused_rmsnorm_quant/ide","opt","",IDE_MAIN,done="✓ Accepted",toast="rmsnorm_quant.cu accepted · PR #413 opened on acme-ml/serving · 18.6 µs on H100",label="Kernel IDE: the agent rewrites a CUDA kernel, the SASS pane updates, the terminal shows compile, simulate and verify, and the kernel ships",rail=True,main_cls="ide-main",dark=True,accept=True,title="Kernel IDE · the agent rewrites a CUDA kernel, checks the SASS, and verifies it on an H100")

