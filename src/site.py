"""The site source: an editorial marketing page wrapping dense, product-grade app
screens (16:10 windows). Site and app share no components. Built by build.py,
which splices app.py and app.css in and writes ../index.html."""
import html as H
import os
import re

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")

# ───────────────────────── SVG helpers for app charts ─────────────────────────
def line_chart(w, h, xs, series, ylim, ylabels, xlabels, markers=(), extra="", pad=(28, 8, 18, 6)):
    """series: list of dict(cls, pts=[(x,y)], step=bool). markers: list of dict(x,y,label,step,cls,anchor)."""
    L, R, B, T = pad
    def X(x): return L + (x - xs[0]) / (xs[1] - xs[0]) * (w - L - R)
    def Y(y): return T + (1 - (y - ylim[0]) / (ylim[1] - ylim[0])) * (h - T - B)
    g = [f'<svg viewBox="0 0 {w} {h}" aria-hidden="true" class="ch">']
    for yv, lab in ylabels:
        g.append(f'<line class="grid" x1="{L}" y1="{Y(yv):.1f}" x2="{w-R}" y2="{Y(yv):.1f}"/><text class="ax" x="{L-4}" y="{Y(yv)+3:.1f}" text-anchor="end">{lab}</text>')
    for xv, lab in xlabels:
        g.append(f'<text class="ax" x="{X(xv):.1f}" y="{h-4}" text-anchor="middle">{lab}</text>')
    g.append(extra)
    for s in series:
        pts = s["pts"]
        if s.get("step"):
            d = f"M{X(pts[0][0]):.1f} {Y(pts[0][1]):.1f}"
            for i in range(1, len(pts)):
                d += f" L{X(pts[i][0]):.1f} {Y(pts[i-1][1]):.1f} L{X(pts[i][0]):.1f} {Y(pts[i][1]):.1f}"
        else:
            d = "M" + " L".join(f"{X(x):.1f} {Y(y):.1f}" for x, y in pts)
        if s.get("area"):
            g.append(f'<path class="area grow-area" d="{d} L{X(pts[-1][0]):.1f} {h-B} L{X(pts[0][0]):.1f} {h-B} Z"/>')
        g.append(f'<path class="ln {s["cls"]} grow-path" d="{d}"/>')
    for m in markers:
        st = f' data-step="{m["step"]}"' if "step" in m else ""
        anc = m.get("anchor", "start")
        tx = X(m["x"]) + (6 if anc == "start" else -6)
        g.append(f'<g class="mk {m.get("cls","")}"{st}><circle cx="{X(m["x"]):.1f}" cy="{Y(m["y"]):.1f}" r="3.5"/><text x="{tx:.1f}" y="{Y(m["y"]) + m.get("dy",-7):.1f}" text-anchor="{anc}">{m["label"]}</text></g>')
    g.append("</svg>")
    return "".join(g)

def bars(vals, cls=None, labels=None):
    out = ['<div class="bars">']
    for i, v in enumerate(vals):
        c = (cls[i] if cls else "") or ""
        out.append(f'<i class="grow {c}" style="height:{v}%"></i>')
    out.append("</div>")
    if labels:
        out.append('<div class="bars-x">' + "".join(f"<span>{l}</span>" for l in labels) + "</div>")
    return "".join(out)

# ───────────────────────── App shell pieces ─────────────────────────
def chrome(url):
    return f'<div class="chrome"><span class="dots"><i></i><i></i><i></i></span><span class="url">{url}</span></div>'

def appbar(ws="acme-ml · prod"):
    return f'<div class="appbar"><span class="mark"></span><b>VitalOps</b><span class="ws">{ws}</span><span class="search">Search runs, models, kernels…</span><span class="bell"></span><span class="av">FR</span></div>'

NAV = {
 "opt":  [("Optimize", ["Runs*", "Models", "Targets", "Evals", "Kernels", "Bundles"]), ("Serve", ["Pools", "Monitoring"]), ("More", ["Edge", "Fleet", "Sim"])],
 "runs": [("Optimize", ["Runs*", "Models", "Targets", "Evals", "Kernels", "Bundles"]), ("Serve", ["Pools", "Monitoring"]), ("More", ["Edge", "Fleet", "Sim"])],
 "serve":[("Optimize", ["Runs", "Models", "Bundles"]), ("Serve", ["Pools*", "Models", "Endpoints", "Rollouts", "Monitoring", "API keys"]), ("More", ["Edge", "Fleet", "Sim"])],
 "mon":  [("Optimize", ["Runs", "Models", "Bundles"]), ("Serve", ["Pools", "Models", "Endpoints", "Rollouts", "Monitoring*", "API keys"]), ("More", ["Edge", "Fleet", "Sim"])],
 "edge": [("Optimize", ["Runs", "Models"]), ("Edge", ["Devices", "Models", "Fits*", "Training", "Exports"]), ("More", ["Serve", "Fleet", "Sim"])],
 "fleet":[("Fleet", ["Agents*", "GPUs", "Queues", "Policies", "Budgets"]), ("Serve", ["Pools", "Monitoring"]), ("More", ["Optimize", "Edge", "Sim"])],
 "sim":  [("Sim", ["Kernels*", "Targets", "Runs", "Candidates", "Gym"]), ("Optimize", ["Runs", "Kernels"]), ("More", ["Serve", "Edge", "Fleet"])],
}
def nav(key, foot):
    out = ['<nav class="anav">']
    for sec, items in NAV[key]:
        out.append(f'<div class="sec">{sec}</div>')
        for it in items:
            on = it.endswith("*"); it = it.rstrip("*")
            out.append(f'<a class="{"on" if on else ""}"><i></i>{it}</a>')
    out.append(f'<div class="nfoot">{foot}</div></nav>')
    return "".join(out)

def stat(label, value, delta="", cls="", count=True, before=None):
    b = f' data-before="{H.escape(before)}"' if before else ""
    return f'<div class="stat"><small>{label}</small><b class="{"count" if count else ""}"{b}>{value}</b><span class="{cls}">{delta}</span></div>'

def st(kind, text):  # status: dot + text
    return f'<span class="st {kind}">{text}</span>'

def screen(id_, url, navkey, navfoot, main, done=None, toast=None, label=""):
    d = f' data-done="{H.escape(done)}"' if done else ""
    t = f' data-toast="{H.escape(toast)}"' if toast else ""
    return f'<div class="frame"><figure class="mock" id="{id_}" aria-label="{H.escape(label)}"{d}{t}>{chrome(url)}<div class="app">{appbar()}<div class="abody">{nav(navkey, navfoot)}<div class="amain">{main}</div></div></div></figure></div>'

# ───────────────────────── Screens ─────────────────────────
# throughput-over-search data (minutes, tok/s)
SEARCH = [(0,1840),(19,3120),(63,3780),(98,5460),(129,6120)]
search_chart = line_chart(640, 122, (0,134), [dict(cls="brand", pts=SEARCH, step=True, area=True)], (0,7000),
    [(0,"0"),(2000,"2k"),(4000,"4k"),(6000,"6k")], [(0,"00:00"),(30,"00:30"),(60,"01:00"),(90,"01:30"),(120,"02:00")],
    markers=[dict(x=19,y=3120,label="fp8 W8A8 + fp8 KV",step=1,dy=14), dict(x=41,y=3900,label="int4 AWQ · below floor",step=2,cls="bad",dy=-8),
             dict(x=63,y=3780,label="prefix cache + chunked prefill",step=3,dy=14), dict(x=98,y=5460,label="EAGLE-3 draft",step=4,dy=-8),
             dict(x=129,y=6120,label="fused kernel · SASS-verified",step=5,cls="hi",anchor="end",dy=-8)])

RUNS_MAIN = f"""
<div class="ph"><div><div class="crumb">Optimize / Runs</div><h1>Runs</h1></div><div class="actions"><span class="ab">Filters</span><span class="ab pri">New run</span></div></div>
<div class="stats">{stat("Runs this month","23")}{stat("GPU-hours used","61 / 120","budget","mu")}{stat("Median speed-up","2.6×","across verified runs","ok")}{stat("Bundles shipped","9","+3 this week","ok")}</div>
<div class="seg"><span class="on">All</span><span>Running</span><span>Verified</span><span>Shipped</span><span class="sp"></span><span class="q">model, target, run id…</span></div>
<div class="pane narrow">
  <div>
  <div class="blk">
    <table class="tbl">
      <tr><th>Run</th><th>Model</th><th>Target</th><th class="n">Best</th><th class="n">vs base</th><th>Status</th><th class="hide-md">Updated</th></tr>
      <tr class="sel"><td class="mono">run-8841</td><td>Qwen3-32B</td><td>2×H100 SXM</td><td class="n count">6,120 tok/s</td><td class="n">3.3×</td><td data-before='{H.escape(st("ok","Verified"))}'>{st("brand","Shipped")}</td><td class="hide-md mu">2 min ago</td></tr>
      <tr data-step="1"><td class="mono">run-8852</td><td>Llama-3.3-70B</td><td>4×H100 SXM</td><td class="n count">2,980 tok/s</td><td class="n">2.1×</td><td>{st("run","Searching · 41%")}</td><td class="hide-md mu">live</td></tr>
      <tr data-step="2"><td class="mono">run-8849</td><td>Qwen2.5-VL-7B</td><td>L40S</td><td class="n count">1,410 tok/s</td><td class="n">2.4×</td><td>{st("ok","Verified")}</td><td class="hide-md mu">1 h ago</td></tr>
      <tr data-step="3"><td class="mono">run-8846</td><td>DeepSeek-R1-32B</td><td>2×H100 SXM</td><td class="n count">4,870 tok/s</td><td class="n">2.9×</td><td>{st("brand","Shipped")}</td><td class="hide-md mu">yesterday</td></tr>
      <tr data-step="4"><td class="mono">run-8840</td><td>Mistral-Small-24B</td><td>RTX 5090</td><td class="n count">1,120 tok/s</td><td class="n">1.8×</td><td>{st("warn","Below floor")}</td><td class="hide-md mu">yesterday</td></tr>
      <tr data-step="5"><td class="mono">run-8833</td><td>Whisper-large-v3</td><td>A100 40GB</td><td class="n count">38 req/s</td><td class="n">3.1×</td><td>{st("brand","Shipped")}</td><td class="hide-md mu">3 d ago</td></tr>
      <tr data-step="5"><td class="mono">run-8829</td><td>bge-m3</td><td>L4</td><td class="n count">2,650 emb/s</td><td class="n">2.2×</td><td>{st("ok","Verified")}</td><td class="hide-md mu">4 d ago</td></tr>
    </table>
  </div>
  <div class="blk"><div class="bh">Activity<span class="mu">today</span></div>
    <div class="evts">
      <div class="evt" data-step="6"><time>10:14</time><span>run-8841 shipped to prod-a as a 10% canary · by FR</span></div>
      <div class="evt" data-step="3"><time>10:02</time><span>run-8852 started · Llama-3.3-70B on 4×H100 · budget 6 GPU-hours</span></div>
      <div class="evt" data-step="2"><time>09:48</time><span>kernel fused_rmsnorm_quant verified on H100 · 18.4 µs · max err 3.1e-4</span></div>
      <div class="evt" data-step="1"><time>09:31</time><span>eval support-qa-v3 updated · 1,200 samples · 3 seeds</span></div>
    </div>
  </div>
  </div>
  <aside class="side">
    <div class="sh"><b>run-8841</b><span class="mu">Qwen3-32B → 2×H100 SXM</span></div>
    <div class="kv"><dt>SLO</dt><dd>TTFT p99 &lt; 400 ms</dd><dt>Eval</dt><dd>support-qa-v3 · floor 83.5</dd><dt>Candidates</dt><dd>14 tried · 6 kept</dd><dt>Search time</dt><dd>2 h 14 m · 2 GPUs</dd></div>
    <div class="sh2">Throughput during the search</div>
    {line_chart(300, 120, (0,134), [dict(cls="brand", pts=SEARCH, step=True, area=True)], (0,7000), [(0,"0"),(3000,"3k"),(6000,"6k")], [(0,"0h"),(60,"1h"),(120,"2h")])}
    <div class="kv"><dt>Best candidate</dt><dd>#14 · fused rmsnorm+quant</dd><dt>Throughput</dt><dd>6,120 tok/s · 3.3×</dd><dt>TTFT p99</dt><dd>275 ms</dd><dt>Accuracy</dt><dd>84.1 · floor held</dd></div>
    <div class="acts" data-step="6"><span class="mb pri">Ship to Serve</span><span class="mb">Open run</span></div>
  </aside>
</div>"""
SCREEN_HERO = screen("hero-run","app.vitalops.ai/optimize/runs","runs","23 runs · 2 GPUs busy",RUNS_MAIN,done="✓ Shipped",toast="run-8841 deployed to prod-a · canary 10%",label="Optimize runs list with a selected run's throughput chart and a Ship to Serve action")

OPT_MAIN = f"""
<div class="ph"><div><div class="crumb">Optimize / Runs / run-8841</div><h1>Qwen3-32B → 2×H100 SXM <span class="mu">run-8841</span></h1></div><div class="actions"><span class="ab">Export bundle</span><span class="ab">Report</span></div></div>
<div class="ptabs"><span class="on">Overview</span><span>Candidates <em>14</em></span><span>Kernels <em>2</em></span><span>Evals</span><span>Log</span></div>
<div class="stats">{stat("Throughput","6,120 tok/s","baseline 1,840","ok")}{stat("TTFT p99","275 ms","SLO 400 ms","ok")}{stat("Accuracy · support-qa-v3","84.1%","floor 83.5 · base 84.3","mu")}{stat("Cost per 1M tokens","$0.31","was $1.02","ok")}</div>
<div class="pane">
  <div>
    <div class="blk"><div class="bh">Tokens/s during the search<span class="mu">2 h 14 m · 2×H100</span></div>{search_chart}</div>
    <div class="blk">
      <div class="bh">Candidates<span class="mu">14 tried · 6 kept · 1 rejected by eval</span></div>
      <table class="tbl">
        <tr><th>#</th><th>Change</th><th class="n">tok/s</th><th class="n">TTFT p99</th><th class="n">Acc</th><th>Result</th></tr>
        <tr><td>1</td><td>baseline · vLLM 0.11 · bf16 · TP2</td><td class="n">1,840</td><td class="n">612 ms</td><td class="n">84.3</td><td>{st("mu","reference")}</td></tr>
        <tr data-step="1"><td>3</td><td>fp8 W8A8 weights + fp8 KV cache</td><td class="n">3,120</td><td class="n">410 ms</td><td class="n">84.1</td><td>{st("ok","kept")}</td></tr>
        <tr data-step="2"><td>5</td><td>int4 AWQ (g128)</td><td class="n">3,900</td><td class="n">352 ms</td><td class="n">82.9</td><td>{st("bad","below floor")}</td></tr>
        <tr data-step="3"><td>8</td><td>chunked prefill 2k + prefix cache</td><td class="n">3,780</td><td class="n">288 ms</td><td class="n">84.1</td><td>{st("ok","kept")}</td></tr>
        <tr data-step="4"><td>11</td><td>EAGLE-3 draft (k=3), trained on your traffic</td><td class="n">5,460</td><td class="n">291 ms</td><td class="n">84.1</td><td>{st("ok","kept")}</td></tr>
        <tr data-step="5" class="sel"><td>14</td><td>fused rmsnorm+quant kernel · SASS-verified</td><td class="n">6,120</td><td class="n">275 ms</td><td class="n">84.1</td><td>{st("brand","best")}</td></tr>
      </table>
    </div>
  </div>
  <aside class="side">
    <div class="sh"><b>Best configuration</b><span class="mu">#14</span></div>
    <div class="kv"><dt>Engine</dt><dd>vLLM 0.11</dd><dt>Weights / KV</dt><dd>fp8 W8A8 / fp8</dd><dt>Parallelism</dt><dd>TP=2</dd><dt>Spec decode</dt><dd data-before="—">EAGLE-3 · k=3</dd><dt>Prefill</dt><dd data-before="default">chunked 2k + prefix cache</dd><dt>Custom kernels</dt><dd data-before="0">2 · SASS-verified</dd></div>
    <div class="sh2" data-step="5">Kernel check · fused_rmsnorm_quant · sm_90a</div>
    <div class="kv" data-step="5"><dt>Registers</dt><dd>72 / 255</dd><dt>Occupancy</dt><dd>62%</dd><dt>Smem bank conflicts</dt><dd>0</dd><dt>Top stall</dt><dd>long scoreboard 11%</dd><dt>Max err vs bf16</dt><dd>3.1e-4</dd></div>
    <div class="ai" data-step="6"><b>Agent recommendation</b>Ship #14: 3.3× throughput at accuracy parity. int4 stays rejected under this floor.</div>
    <div class="acts" data-step="6"><span class="mb pri">Ship to Serve</span><span class="mb">Re-run · 8 h budget</span></div>
  </aside>
</div>"""
SCREEN_OPT = screen("fig-opt","app.vitalops.ai/optimize/runs/run-8841","opt","run-8841 · 2 GPUs busy",OPT_MAIN,done="✓ Shipped",toast="run-8841 deployed to prod-a · canary 10%",label="Optimize run detail: throughput chart, candidates table, best configuration and a SASS-level kernel check")

SERVE_MAIN = f"""
<div class="ph"><div><div class="crumb">Serve / Pools / prod-a</div><h1>prod-a <span class="mu">8×H100 · us-east · your VPC</span></h1></div><div class="actions"><span class="ab">Scale</span><span class="ab">Keys</span><span class="ab pri">Deploy bundle</span></div></div>
<div class="ptabs"><span class="on">Overview</span><span>Models <em>3</em></span><span>Requests</span><span>Rollouts <em>1</em></span><span>Logs</span></div>
<div class="stats">{stat("Requests / s","412","peak 590 today","mu")}{stat("Tokens / s","38,900","generation","mu")}{stat("TTFT p99","318 ms","SLO 400 ms","ok")}{stat("Prefix cache hit","71%","KV 84% used","mu")}</div>
<div class="pane">
  <div>
    <div class="blk">
      <div class="bh">Live requests<span class="mu">streaming · last 30 s</span></div>
      <table class="tbl">
        <tr><th>Request</th><th>Model</th><th class="n hide-md">In / out tokens</th><th class="n">TTFT</th><th>Status</th></tr>
        <tr><td class="mono">req-9f21</td><td>qwen3-32b-fp8</td><td class="n hide-md">3,120 / 212</td><td class="n">141 ms</td><td>{st("ok","done")}</td></tr>
        <tr data-step="1"><td class="mono">req-9f22</td><td>qwen3-32b-fp8</td><td class="n hide-md">18,400 / 64</td><td class="n">296 ms</td><td data-before='{H.escape(st("run","streaming"))}'>{st("ok","done")}</td></tr>
        <tr data-step="2"><td class="mono">req-9f23</td><td>llama-3.3-70b-int4</td><td class="n hide-md">980 / 410</td><td class="n">188 ms</td><td data-before='{H.escape(st("run","streaming"))}'>{st("ok","done")}</td></tr>
        <tr data-step="3"><td class="mono">req-9f24</td><td>bge-m3</td><td class="n hide-md">512 / —</td><td class="n">9 ms</td><td>{st("ok","done")}</td></tr>
        <tr data-step="4"><td class="mono">req-9f25</td><td>qwen3-32b-fp8</td><td class="n hide-md">2,040 / 1,300</td><td class="n">122 ms</td><td>{st("run","streaming")}</td></tr>
        <tr data-step="5"><td class="mono">req-9f26</td><td>qwen3-32b-fp8</td><td class="n hide-md">prefix hit 16k</td><td class="n">48 ms</td><td>{st("run","streaming")}</td></tr>
      </table>
    </div>
    <div class="blk"><div class="bh">Tokens/s<span class="mu">last 60 min</span></div>{bars([52,58,61,55,70,76,72,81,88,84,95,100],labels=["−60 min","−30","now"])}</div>
  </div>
  <aside class="side">
    <div class="sh"><b>Models in pool</b><span class="mu">9 replicas</span></div>
    <table class="tbl"><tr><th>Model</th><th class="n">Rep.</th><th>Bundle</th></tr>
      <tr><td>qwen3-32b-fp8</td><td class="n">6</td><td class="mono">run-8841</td></tr>
      <tr><td>llama-3.3-70b-int4</td><td class="n">2</td><td class="mono">run-8702</td></tr>
      <tr><td>bge-m3</td><td class="n">1</td><td class="mu">stock</td></tr></table>
    <div class="sh2">Rollout · run-8841 replaces run-8790</div>
    <div class="prog"><span>Canary 10%</span><i><b class="grow" style="width:100%"></b></i><em>passed</em></div>
    <div class="prog" data-step="2"><span>50%</span><i><b class="grow" style="width:100%"></b></i><em>passed</em></div>
    <div class="prog" data-step="4"><span>100%</span><i><b class="grow" style="width:100%"></b></i><em data-before="pending">now</em></div>
    <div class="kv" data-step="3"><dt>TTFT p99 vs previous</dt><dd>−41%</dd><dt>Cost per 1M tokens</dt><dd>−69%</dd><dt>Error rate</dt><dd>0.02% (=)</dd></div>
    <div class="acts" data-step="5"><span class="mb pri">Promote to 100%</span><span class="mb">Rollback</span></div>
  </aside>
</div>"""
SCREEN_SERVE = screen("serve-pools","app.vitalops.ai/serve/pools/prod-a","serve","prod-a · 9 replicas healthy",SERVE_MAIN,done="✓ Promoted",toast="run-8841 at 100% · previous bundle kept warm",label="Serve pool overview with live requests, models and a canary rollout being promoted")

ttft_chart = line_chart(640, 150, (0,24), [dict(cls="amber", pts=[(0,330),(3,325),(6,335),(9,330),(9.7,480),(12,560),(15,600),(18,612),(21,610),(24,612)]), dict(cls="brand", pts=[(0,150),(6,148),(12,160),(18,172),(24,175)])],
    (0,700), [(0,"0"),(200,"200"),(400,"400"),(600,"600")], [(0,"−24 h"),(6,"−18"),(12,"−12"),(18,"−6"),(24,"now")],
    markers=[dict(x=9.7,y=480,label="template v12 deployed 09:35",step=1,cls="bad",dy=-8)],
    extra='<line class="slo" x1="28" y1="{y}" x2="634" y2="{y}"/>'.replace("{y}", f"{8 + (1-400/700)*(150-8-18):.1f}"))
MON_MAIN = f"""
<div class="ph"><div><div class="crumb">Serve / Monitoring</div><h1>Production <span class="mu">all pools · 12 GPUs</span></h1></div><div class="actions"><span class="seg small"><span>1h</span><span class="on">24h</span><span>7d</span></span><span class="ab">Export</span></div></div>
<div class="ptabs"><span class="on">Overview</span><span>Latency</span><span>Throughput</span><span>Cost</span><span>Quality</span><span>Alerts <em>1</em></span></div>
<div class="stats">{stat("Tokens served · 24 h","1.9B","+12% vs yesterday","ok")}{stat("TTFT p99 · all pools","318 ms","prod-b 612 ms","warn")}{stat("Cost per 1M tokens","$0.31","$590 / day","mu")}{stat("Quality drift · sampled eval","−0.2 pts","alert at −1.0","mu",count=False)}</div>
<div class="pane">
  <div>
    <div class="blk"><div class="bh">TTFT p50 / p99 · prod-b · ms<span class="mu">SLO 400 ms (dashed)</span></div>{ttft_chart}</div>
    <div class="blk"><div class="bh">Tokens/s by pool<span class="mu">prod-a 31k · prod-b 8k</span></div>{bars([48,52,50,58,66,72,70,78,84,90,96,100],labels=["00:00","12:00","now"])}</div>
  </div>
  <aside class="side">
    <div class="sh"><b>Alerts</b><span class="mu">1 open</span></div>
    <div class="evt"><time>09:41</time><span>{st("bad","p99")} TTFT 612 ms on prod-b, SLO 400 ms</span></div>
    <div class="evt" data-step="1"><time>09:42</time><span>KV prefix hit on prod-b fell 71% → 44% after prompt template v12</span></div>
    <div class="evt" data-step="2"><time>09:43</time><span>Cause: new system prompt breaks the shared prefix</span></div>
    <div class="sh2" data-step="4">Cost by model · today</div>
    <div class="hb" data-step="4"><span>qwen3-32b-fp8</span><i><b class="grow" style="width:100%"></b></i><em>$412</em></div>
    <div class="hb" data-step="4"><span>llama-3.3-70b-int4</span><i><b class="grow" style="width:38%"></b></i><em>$156</em></div>
    <div class="hb" data-step="4"><span>bge-m3</span><i><b class="grow" style="width:5%"></b></i><em>$22</em></div>
    <div class="ai" data-step="5"><b>Agent suggestion</b>Move the variable part of template v12 after the static prefix; enable chunked prefill on prod-b. Predicted p99: 290 ms.</div>
    <div class="acts" data-step="5"><span class="mb pri">Apply via Optimize</span><span class="mb">Snooze 1 h</span></div>
  </aside>
</div>"""
SCREEN_MON = screen("serve-monitor","app.vitalops.ai/serve/monitoring","mon","12 GPUs reporting",MON_MAIN,done="✓ Applied",toast="chunked prefill rolled to prod-b · canary 10% · watching p99",label="Serve monitoring: latency chart against the SLO, cost by model, an alert traced to a prompt-template change, and a suggested fix")

EDGE_MAIN = f"""
<div class="ph"><div><div class="crumb">Edge / Fits / qwen2.5-vl-3b</div><h1>Qwen2.5-VL-3B → Jetson Orin Nano 8 GB <span class="mu">fit-2291</span></h1></div><div class="actions"><span class="ab">Change device</span><span class="ab pri">Export</span></div></div>
<div class="ptabs"><span class="on">Fit</span><span>Accuracy</span><span>Training</span><span>Exports <em>1</em></span></div>
<div class="stats">{stat("Device memory","8.0 GB","budget for model 6.5 GB","mu",count=False)}{stat("Model footprint","3.1 GB","fits · 3.4 GB headroom","ok",count=False,before="7.4 GB")}{stat("Decode","28 tok/s","target 20","ok")}{stat("Accuracy · doc-vqa-internal","91.4%","floor 90.0","ok")}</div>
<div class="pane">
  <div>
    <div class="blk"><div class="bh">Fit steps<span class="mu">memory after each</span></div>
      <div class="hb"><span>bf16 weights + fp16 KV</span><i><b class="grow bad" style="width:100%"></b></i><em>7.4 GB</em></div>
      <div class="hb" data-step="1"><span>INT4 AWQ weights (g128)</span><i><b class="grow warn" style="width:55%"></b></i><em>4.1 GB</em></div>
      <div class="hb" data-step="2"><span>INT8 KV cache · 4k ctx</span><i><b class="grow" style="width:47%"></b></i><em>3.5 GB</em></div>
      <div class="hb" data-step="3"><span>vision encoder fp8</span><i><b class="grow" style="width:43%"></b></i><em>3.2 GB</em></div>
      <div class="hb" data-step="4"><span>prune 2 of 36 layers (kd)</span><i><b class="grow" style="width:42%"></b></i><em>3.1 GB</em></div>
    </div>
    <div class="blk"><div class="bh">Accuracy guard<span class="mu">doc-vqa-internal · 1,200 samples</span></div>
      <table class="tbl"><tr><th>Step</th><th class="n">Accuracy</th><th class="n">Δ</th><th>Result</th></tr>
        <tr><td>baseline bf16</td><td class="n">92.0%</td><td class="n">—</td><td>{st("mu","reference")}</td></tr>
        <tr data-step="1"><td>INT4 AWQ</td><td class="n">91.6%</td><td class="n">−0.4</td><td>{st("ok","kept")}</td></tr>
        <tr data-step="2"><td>INT8 KV</td><td class="n">91.6%</td><td class="n">0.0</td><td>{st("ok","kept")}</td></tr>
        <tr data-step="3"><td>encoder fp8</td><td class="n">91.5%</td><td class="n">−0.1</td><td>{st("ok","kept")}</td></tr>
        <tr data-step="4"><td>prune 2 layers</td><td class="n">91.4%</td><td class="n">−0.1</td><td>{st("ok","kept")}</td></tr>
        <tr data-step="4"><td class="mu">prune 4 layers</td><td class="n mu">89.2%</td><td class="n mu">−2.2</td><td>{st("bad","rejected")}</td></tr></table>
    </div>
  </div>
  <aside class="side">
    <div class="sh"><b>On-device training</b><span class="mu">QLoRA</span></div>
    <div class="kv"><dt>Method</dt><dd>QLoRA r=16 · int4 base</dd><dt>Data</dt><dd>1,200 samples · stays on device</dd><dt>Peak memory</dt><dd>5.9 GB</dd><dt>Time</dt><dd>1 h 48 m</dd><dt>Eval after</dt><dd data-before="running…">+2.3 pts</dd></div>
    <div class="sh2" data-step="5">Export</div>
    <div class="kv" data-step="5"><dt>Format</dt><dd>ExecuTorch .pte</dd><dt>Runtime</dt><dd>CUDA delegate</dd><dt>Size</dt><dd>3.1 GB</dd><dt>Signed</dt><dd>yes · OTA field-v2</dd></div>
    <div class="ai" data-step="5"><b>Result</b>3.1 GB, 28 tok/s, 91.4% accuracy. Fits with headroom for a 4k context.</div>
    <div class="acts" data-step="5"><span class="mb pri">Export .pte</span><span class="mb">Flash device</span></div>
  </aside>
</div>"""
SCREEN_EDGE = screen("fig-edge","app.vitalops.ai/edge/fits/qwen2.5-vl-3b","edge","Orin Nano 8 GB · online",EDGE_MAIN,done="✓ Exported",toast="qwen2.5-vl-3b-int4.pte · 3.1 GB · signed · ready to flash",label="Edge fit: memory reduced step by step with an accuracy guard, on-device training and export")

def gpu(name, util, agents, kv, cls="", step=None, before=None):
    s = f' data-step="{step}"' if step else ""
    return f'<div class="gpu"{s}><b>{name}<span>{util}%</span></b><i><em class="grow {cls}" style="width:{util}%"></em></i><small>{agents} agents · KV {kv} GB</small></div>'
FLEET_MAIN = f"""
<div class="ph"><div><div class="crumb">Fleet / Agents</div><h1>On-prem cluster <span class="mu">8×H100 · air-gapped</span></h1></div><div class="actions"><span class="ab">Policies</span><span class="ab pri">Scale</span></div></div>
<div class="ptabs"><span class="on">Agents <em>48</em></span><span>GPUs <em>8</em></span><span>Queues</span><span>Budgets</span></div>
<div class="stats">{stat("Agents running","96","scaling · 96 scheduled","ok",before="48")}{stat("GPU utilisation","91%","8 × H100","mu")}{stat("Prefix shared across agents","64%","of prompt tokens","mu")}{stat("Step latency p99","1.9 s","SLO 3.0 s","ok")}</div>
<div class="pane">
  <div>
    <div class="blk"><div class="bh">GPU map<span class="mu">agents per GPU · KV resident</span></div>
      <div class="gpus">{gpu("gpu-0",94,7,71)}{gpu("gpu-1",92,6,68)}{gpu("gpu-2",96,8,77,"warn")}{gpu("gpu-3",88,6,62)}{gpu("gpu-4",90,6,66)}{gpu("gpu-5",93,6,70)}{gpu("gpu-6",89,5,61)}{gpu("gpu-7",71,4,48,step=3)}</div>
    </div>
    <div class="blk"><div class="bh">Agent steps / s<span class="mu">last 10 min</span></div>{bars([60,64,70,66,78,82,80,88,92,100],labels=["−10 min","−5","now"])}</div>
  </div>
  <aside class="side">
    <div class="sh"><b>Scheduler events</b><span class="mu">KV-aware</span></div>
    <div class="evt"><time>14:02</time><span>agent-17 waiting on tool (browser) → KV offloaded to CPU</span></div>
    <div class="evt" data-step="1"><time>14:02</time><span>agent-22 prefix hit: 18k tokens shared from agent-09</span></div>
    <div class="evt" data-step="2"><time>14:03</time><span>gpu-2 hot (96%) → next 3 steps routed to gpu-7</span></div>
    <div class="evt" data-step="3"><time>14:03</time><span>4 agents migrated to gpu-7 with KV</span></div>
    <div class="evt" data-step="4"><time>14:04</time><span>agent-17 tool returned → KV restored, 0.3 s</span></div>
    <div class="evt" data-step="5"><time>14:05</time><span>scale request from team research: 48 → 96 agents</span></div>
    <div class="sh2" data-step="5">Capacity check</div>
    <div class="kv" data-step="5"><dt>Max agents at SLO</dt><dd>112</dd><dt>After scaling</dt><dd>96 · 86% of capacity</dd><dt>Predicted p99 step</dt><dd>2.6 s</dd></div>
    <div class="acts" data-step="5"><span class="mb pri">Scale to 96</span><span class="mb">Pause pool</span></div>
  </aside>
</div>"""
SCREEN_FLEET = screen("fig-fleet","fleet.internal.example/agents","fleet","scheduler healthy · no data leaves",FLEET_MAIN,done="✓ Scaling",toast="96 agents scheduled across 8 GPUs · p99 within SLO",label="Fleet: GPU map with agents per GPU, scheduler events and a scale-up action")

def sass(addr, instr, pct, cls="", step=None):
    s = f' data-step="{step}"' if step else ""
    return f'<div class="sl"{s}><span class="a">{addr}</span><span class="i">{instr}</span><span class="h"><i class="grow {cls}" style="width:{pct*4}%"></i></span><span class="c">{pct:.1f}%</span></div>'
SIM_MAIN = f"""
<div class="ph"><div><div class="crumb">Sim / Kernels / fused_rmsnorm_quant</div><h1>fused_rmsnorm_quant.py <span class="mu">sm_90a · no GPU attached</span></h1></div><div class="actions"><span class="ab">Diff vs v3</span><span class="ab pri">Run</span></div></div>
<div class="ptabs"><span>Source</span><span class="on">SASS</span><span>Targets <em>4</em></span><span>Candidates <em>212</em></span><span>Gym</span></div>
<div class="stats">{stat("Predicted · H100","18.4 µs","stock path 41.2 µs","ok")}{stat("Occupancy","62%","4 blocks / SM","mu")}{stat("Registers · smem","72 · 16 KB","no spills","mu",count=False)}{stat("Rank correlation","0.93","vs last H100 run","ok")}</div>
<div class="pane">
  <div>
    <div class="blk code"><div class="bh">SASS · hottest basic block<span class="mu">stall share · sampled mode</span></div>
      {sass("0120",'<b>LDG.E.128</b> R4, [R2.64]',22.0,"bad")}{sass("0130",'<b>LDG.E.128</b> R8, [R2.64+0x10]',15.5,"bad",1)}{sass("0140",'<b>FMUL</b> R12, R4, R16',2.0,"ok",1)}{sass("0150",'<b>FFMA</b> R12, R5, R5, R12',2.5,"ok",2)}{sass("0160",'<b>SHFL.BFLY</b> PT, R13, R12, 0x10, 0x1f',7.5,"warn",2)}{sass("0170",'<b>MUFU.RSQ</b> R14, R13',6.5,"warn",3)}{sass("0180",'<b>F2FP.E4M3.PACK_AB</b> R20, R19, R18',3.0,"ok",3)}{sass("0190",'<b>STG.E.64</b> [R6.64], R20',8.5,"warn",4)}{sass("01a0",'<b>BAR.SYNC.DEFER_BLOCKING</b> 0x0',11.0,"bad",4)}
      <div class="sl mu" data-step="4"><span class="a">…</span><span class="i">31 more instructions · long scoreboard dominates · loads 100% coalesced</span><span></span><span></span></div>
    </div>
    <div class="blk"><div class="bh">Candidate ranking<span class="mu">212 variants · static mode 0.4 s</span></div>
      <table class="tbl"><tr><th>#</th><th>Variant</th><th class="n">H100</th><th class="n hide-md">B200</th><th>Status</th></tr>
        <tr class="sel"><td>1</td><td>vec4 loads · 2 rows / warp</td><td class="n">18.4 µs</td><td class="n hide-md">9.7 µs</td><td>{st("brand","best")}</td></tr>
        <tr data-step="4"><td>2</td><td>vec4 · 1 row / warp</td><td class="n">19.1 µs</td><td class="n hide-md">10.2 µs</td><td>{st("mu","within 4%")}</td></tr>
        <tr data-step="4"><td>3</td><td>vec2 · smem reduce</td><td class="n">21.8 µs</td><td class="n hide-md">11.9 µs</td><td>{st("mu","within 20%")}</td></tr>
        <tr data-step="5"><td>4</td><td>cp.async pipeline, 2 stages</td><td class="n">22.6 µs</td><td class="n hide-md">12.4 µs</td><td>{st("mu","")}</td></tr></table>
    </div>
  </div>
  <aside class="side">
    <div class="sh"><b>Predicted across targets</b><span class="mu">sampled</span></div>
    <table class="tbl"><tr><th>Target</th><th class="n">Predicted</th><th class="n">Stock</th></tr>
      <tr><td>H100 SXM</td><td class="n">18.4 µs</td><td class="n">41.2 µs</td></tr>
      <tr data-step="2"><td>B200</td><td class="n">9.7 µs</td><td class="n">22.8 µs</td></tr>
      <tr data-step="3"><td>L40S</td><td class="n">44.1 µs</td><td class="n">96.0 µs</td></tr>
      <tr data-step="3"><td>RTX 5090</td><td class="n">21.3 µs</td><td class="n mu">static</td></tr></table>
    <div class="sh2" data-step="4">This run</div>
    <div class="kv" data-step="4"><dt>Static</dt><dd>212 variants · 0.4 s</dd><dt>Sampled</dt><dd>top 20 · 38 s</dd><dt>Functional check</dt><dd>PTX oracle · pass</dd><dt>Determinism</dt><dd>bit-exact replay</dd></div>
    <div class="ai" data-step="5"><b>Next</b>Top 3 are within 20%: verify them on a real H100 before shipping. Estimated 1 GPU-minute.</div>
    <div class="acts" data-step="5"><span class="mb pri">Verify on real H100</span><span class="mb">Add to gym</span></div>
  </aside>
</div>"""
SCREEN_SIM = screen("fig-sim","app.vitalops.ai/sim/kernels/fused_rmsnorm_quant","sim","16 CPU threads · nvcc 13.x",SIM_MAIN,done="✓ Queued",toast="verification queued on a real H100 · ~1 GPU-minute",label="Sim: SASS listing with stall shares, candidate ranking and predicted times per GPU, with no GPU attached")

# ───────────────────────── CSS ─────────────────────────
CSS = r"""
:root{--bg:#f5f6fa;--white:#fff;--ink:#0f172a;--ink2:#334155;--ink3:#5b687c;--ink4:#94a3b8;--line:#e2e8f0;--line2:#eef2f7;--brand:#3f5cf6;--brand2:#637fff;--brandD:#2737bd;--brand50:#eff4ff;--brand100:#dbe5ff;--brand200:#bdcdff;--ok:#059669;--warn:#b45309;--bad:#be123c;--ai:#6d28d9;--font:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;--mono:'DM Mono',ui-monospace,monospace;color-scheme:light}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{background:var(--bg);color:var(--ink2);font-family:var(--font);font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased;overflow-x:hidden;font-feature-settings:"ss01","cv11"}
img{max-width:100%;display:block}
a{color:inherit;text-decoration:none}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
@media(max-width:600px){.wrap{padding:0 16px}}
h1,h2,h3{color:var(--ink);letter-spacing:-.025em;line-height:1.15;font-weight:700}
h1{font-size:clamp(34px,4.4vw,52px);font-weight:800;letter-spacing:-.035em;line-height:1.06}
h2{font-size:clamp(26px,3vw,34px);font-weight:800;letter-spacing:-.03em}
h3{font-size:19px}
.k{font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--brand)}
.lede{font-size:18px;color:var(--ink2);max-width:62ch}
.mono{font-family:var(--mono)}
code{font-family:var(--mono);font-size:.9em;color:var(--ink)}
.btn{display:inline-flex;align-items:center;gap:8px;padding:11px 18px;border-radius:8px;font-weight:600;font-size:14px;border:1px solid transparent;cursor:pointer;font-family:var(--font);white-space:nowrap;transition:.15s}
.btn-p{background:var(--brand);color:#fff}.btn-p:hover{background:var(--brandD)}
.btn-s{background:var(--white);color:var(--ink);border-color:var(--line)}.btn-s:hover{border-color:var(--brand200)}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.skip{position:absolute;left:12px;top:-60px;z-index:100;background:var(--brand);color:#fff;padding:8px 12px;border-radius:8px;font-weight:600}.skip:focus{top:12px}
a:focus-visible,button:focus-visible,[tabindex]:focus-visible{outline:2px solid var(--brand);outline-offset:2px}
.btn:focus-visible,summary:focus-visible,.tour-bar a:focus-visible,.topnav a:focus-visible{outline:2px solid var(--brand);outline-offset:2px}
/* top nav */
.top{position:sticky;top:0;z-index:50;background:rgba(245,246,250,.9);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.top-in{display:flex;align-items:center;justify-content:space-between;height:62px;gap:16px}
.logo{display:flex;align-items:center;gap:8px;font-weight:700;font-size:15px;color:var(--ink)}
.logo svg{width:28px;height:28px;color:var(--brand);transform:rotate(var(--spin,0deg));will-change:transform}
.topnav{display:flex;gap:4px;list-style:none;align-items:center}
.topnav a{display:block;padding:7px 11px;border-radius:7px;font-size:14px;font-weight:500;color:var(--ink2)}
.topnav a:hover{color:var(--ink);background:var(--white)}
.topnav .navcta{margin-left:8px}
.topnav a.btn-p{color:#fff;padding:9px 14px}
.topnav a.btn-p:hover{background:var(--brandD);color:#fff}
.menu-btn{display:none;background:var(--white);border:1px solid var(--line);border-radius:7px;padding:7px 10px;color:var(--ink);font:inherit;font-size:13px;font-weight:600;cursor:pointer}
@media(max-width:920px){.menu-btn{display:block}.topnav{display:none;position:absolute;top:62px;left:0;right:0;flex-direction:column;align-items:stretch;background:var(--white);border-bottom:1px solid var(--line);padding:10px 16px 16px;gap:2px}.topnav.open{display:flex}.topnav a{padding:12px 10px;font-size:16px;border-bottom:1px solid var(--line2);border-radius:0}.topnav .navcta{margin:10px 0 0}.topnav .navcta .btn{width:100%;justify-content:center;border-bottom:0}}
/* hero */
.hero{padding:44px 0 36px;overflow-x:clip}
.hero .wrap{max-width:none;padding-left:max(24px,calc((100vw - var(--sbw,0px) - 1132px)/2));padding-right:24px}
.hero-grid{display:grid;grid-template-columns:minmax(320px,440px) minmax(0,1fr);gap:48px;align-items:center}
.hero .k{display:block;margin-bottom:14px}
.hero h1{font-size:clamp(32px,3.1vw,44px);letter-spacing:-.03em;line-height:1.08}
.hero h1 em{font-style:normal;color:var(--brand)}
.hero .lede{margin-top:18px;font-size:17px}
.hero-cta{display:flex;gap:10px;margin-top:24px;flex-wrap:wrap}
.hero-note{margin-top:14px;font-size:13px;color:var(--ink3)}
.hero-shot{min-width:0}
.carousel{min-width:0}
.car-clip{overflow:hidden;padding:18px 14px 48px;margin:-18px -14px -48px}
/* flow strip under the Kernels window: transpile, then emulate */
@property --n{syntax:'<integer>';inherits:true;initial-value:0}
.flow{margin-top:14px;display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:12px;background:#0b1020;border:1px solid #1f2740;border-radius:12px;padding:12px;color:#c9d1d9;font-family:var(--font)}
.flow .cw{background:#0f1117;border:1px solid #262b38;border-radius:8px;overflow:hidden;min-width:0;display:flex;flex-direction:column}
.flow .cwt{height:26px;display:flex;align-items:center;padding:0 10px;border-bottom:1px solid #262b38;background:#161922;font-family:var(--mono);font-size:10.5px;color:#8e94a3;position:relative}
.flow .tab,.flow .xstep{position:absolute;top:0;line-height:26px;opacity:0;animation:fshow .25s forwards var(--a),fhide .25s forwards var(--b)}
.flow .tab{left:10px;color:#c9d1d9}.flow .tab::before{content:"";display:inline-block;width:6px;height:6px;border-radius:50%;background:#f59e0b;margin-right:6px;vertical-align:1px}
.flow .xstep{right:10px;color:#a5b4fc}
.flow .cwb{position:relative;flex:1;min-height:128px}
.flow .stage{position:absolute;inset:0;margin:0;padding:8px 10px;font-family:var(--mono);font-size:10.5px;line-height:16px;color:#c9d1d9;white-space:pre;overflow:hidden;opacity:0;animation:fshow .01s forwards var(--a),fout .3s ease-in forwards var(--b)}
.flow .stage b{font-weight:400}.flow .t-kw{color:#ff7b72}.flow .t-ty{color:#ffa657}.flow .t-fn,.flow .t-dec{color:#d2a8ff}.flow .t-str{color:#a5d6ff}.flow .t-num{color:#79c0ff}.flow .t-cm{color:#6e7681}
.flow .t-op{color:#c084fc;font-weight:500}.flow .t-mod{color:#a5b4fc}.flow .t-reg{color:#5eead4}.flow .t-pred{color:#ffa657}
.flow .stage .ln{display:block;opacity:0;transform:translateX(-10px);animation:ln-in .28s ease-out forwards;animation-delay:calc(var(--a) + var(--i) * .07s)}
.flow .pc{position:absolute;left:0;right:0;top:8px;height:16px;background:rgba(99,127,255,.2);border-left:2px solid #8aa0ff;opacity:0;animation:pc-run .7s steps(7,jump-none) 4 forwards,pc-vis 2.9s linear forwards;animation-delay:var(--t),var(--t)}
@keyframes ln-in{to{opacity:1;transform:none}}
@keyframes fout{to{opacity:0;transform:translateY(-8px)}}
@keyframes pc-run{from{top:8px}to{top:104px}}
@keyframes pc-vis{0%{opacity:0}3%{opacity:1}96%{opacity:1}100%{opacity:0}}
.flow .cpu{display:flex;flex-direction:column;gap:8px;min-width:0;overflow:hidden}
.flow .cph{display:block;font-size:11.5px;position:relative;height:32px;padding:0}
.flow .cph b{display:block;color:#fff;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.flow .cph span{position:absolute;left:0;top:17px;font-size:10.5px;color:#9aa3b8;white-space:nowrap;opacity:0;animation:fshow .3s forwards var(--a),fhide .3s forwards var(--b)}
.flow .cph .st1{color:#a5b4fc}.flow .cph .st2{color:#4ade80}
.flow .cb{display:grid;grid-template-columns:74px minmax(0,1fr);gap:12px;align-items:center}
.flow .cores{display:grid;grid-template-columns:repeat(4,15px);gap:4px}
.flow .cores i{display:block;width:15px;height:15px;border-radius:3px;background:#1b2340;border:1px solid #2f3b63;animation:core-on 1.3s ease-in-out infinite;animation-delay:var(--t)}
.flow .meters{display:grid;gap:4px}
.flow .m{display:flex;align-items:baseline;gap:6px;font-size:11px;color:#9aa3b8}.flow .m small{flex:1;font-size:10.5px}.flow .m b{font-family:var(--mono);font-size:12px;color:#fff;font-weight:600}.flow .m i{font-style:normal;font-size:10.5px}
.flow .ctr::after{content:counter(n);counter-reset:n var(--n)}
.no-prop .flow .ctr.w::after{content:"212"}.no-prop .flow .ctr.k::after{content:"1342"}.no-prop .flow .ctr.s::after{content:"38"}
.flow .ctr.w{animation:cnt-w 3s linear forwards;animation-delay:7.2s}.flow .ctr.k{animation:cnt-k 3s linear forwards;animation-delay:7.2s}.flow .ctr.s{animation:cnt-s 3s linear forwards;animation-delay:7.2s}
@keyframes cnt-w{to{--n:212}}@keyframes cnt-k{to{--n:1342}}@keyframes cnt-s{to{--n:38}}
.flow .bar{height:4px;background:#1b2340;border-radius:2px;overflow:hidden}.flow .bar em{display:block;height:100%;width:0;background:#637fff;animation:fbar 3s linear forwards;animation-delay:7.2s}
@keyframes fbar{to{width:100%}}
.flow .out{display:grid;grid-template-columns:auto minmax(0,1fr);gap:16px;align-items:baseline;min-width:0;opacity:0;animation:fshow .4s forwards var(--a)}
.flow .out small{display:block;font-size:10px;color:#9aa3b8;text-transform:uppercase;letter-spacing:.05em}.flow .out b{display:block;font-family:var(--mono);font-size:16px;color:#4ade80;font-weight:700;white-space:nowrap}.flow .out b.mu{font-size:11px;color:#c9d1d9;font-weight:500;white-space:normal}
.flow .trade{font-size:10.5px;color:#9aa3b8;line-height:1.4;opacity:0;animation:fshow .4s forwards var(--a)}
@keyframes fshow{to{opacity:1}}@keyframes fhide{to{opacity:0}}
@keyframes core-on{0%,100%{background:#1b2340}50%{background:#637fff}}
@media(max-width:700px){.flow{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){.flow *{animation-duration:0s!important;animation-delay:0s!important}}
.car{position:relative;aspect-ratio:16/10;max-width:1132px;cursor:grab;touch-action:pan-y;user-select:none;-webkit-user-select:none;perspective:1600px}
.car.dragging{cursor:grabbing}
.car .mock,.car .mock *{cursor:grab}.car.dragging .mock,.car.dragging .mock *{cursor:grabbing}
.car .frame{position:absolute;left:0;top:0;width:100%;z-index:2;transform-origin:50% 50%;will-change:transform,opacity;transition:transform .72s cubic-bezier(.3,.7,.2,1),opacity .72s ease}
.car .frame.active{z-index:1}.car .frame.leaving{z-index:0}
.car .frame[data-off]{opacity:.45;transform:translateX(104%) scale(.86)}
.car-bar{display:flex;justify-content:space-between;align-items:center;gap:12px;font-size:13px;color:var(--ink3);margin-top:12px}
.car-title b{color:var(--ink);font-weight:600}
.car-count{font-family:var(--mono);font-size:12px;color:var(--ink3);flex-shrink:0}
@media (prefers-reduced-motion:reduce){.car .frame{transition:opacity .3s ease}}
@media(max-width:600px){.car-title{font-size:12px}}
@media(max-width:1280px){.hero-grid{grid-template-columns:minmax(300px,400px) minmax(0,1fr);gap:32px}.hero h1{font-size:clamp(30px,3vw,38px)}.hero .lede{font-size:16px;line-height:1.55}.hero-cta .btn{padding:10px 14px;font-size:13.5px}}
@media(max-width:1100px){.hero .wrap{padding-left:24px}.hero-grid{grid-template-columns:minmax(0,1fr);gap:28px}.hero h1{font-size:clamp(32px,5vw,46px);max-width:18ch}.hero .lede{max-width:62ch;font-size:17px}}
@media(max-width:800px){.hero{padding:40px 0 20px}}
@media(max-width:600px){.hero .wrap{padding-left:16px;padding-right:16px}}
/* fact row */
.facts{padding:48px 0 8px}
.facts-row{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.fact{padding:22px 24px 22px 0}
.fact+.fact{border-left:1px solid var(--line);padding-left:24px}
.fact b{display:block;font-size:34px;font-weight:800;letter-spacing:-.03em;color:var(--ink);line-height:1.1}
.fact span{display:block;font-size:13.5px;color:var(--ink3);margin-top:6px}
.facts-note{font-size:13px;color:var(--ink3);margin-top:12px}
@media(max-width:860px){.facts-row{grid-template-columns:1fr 1fr}.fact:nth-child(3){border-left:0;padding-left:0}.fact:nth-child(n+3){border-top:1px solid var(--line)}}
@media(max-width:480px){.facts-row{grid-template-columns:1fr}.fact{border-left:0!important;padding-left:0!important;border-top:1px solid var(--line)}.fact:first-child{border-top:0}}
/* ladder: the stack */
.ladder{padding:56px 0 24px}
.lad-intro{margin-top:12px;color:var(--ink2);font-size:17px;max-width:62ch}
.lad{--cw:140px;--ch:236px;margin-top:18px;display:flex;align-items:flex-start;justify-content:center;flex-wrap:wrap;row-gap:14px}
.layer{width:var(--cw);max-width:var(--cw);height:var(--ch);flex:none;background:var(--white);border:1px solid var(--line);border-radius:10px;overflow:hidden;transition:max-width .7s cubic-bezier(.3,.7,.2,1),opacity .5s ease,border-width 0s linear .7s}
.layer .inner{width:var(--cw);display:flex;flex-direction:column;height:100%}
.layer .g{height:88px;background:#fafbff;border-bottom:1px solid var(--line2);display:flex;align-items:center;justify-content:center;overflow:hidden;position:relative;width:100%;flex:none}
.layer.cap .g{background:#f3f4f8}
.layer.cap{background:#fbfbfd;margin-top:22px}
.layer h3{font-size:13.5px;margin:10px 12px 3px;display:flex;align-items:baseline;gap:6px;letter-spacing:-.01em;line-height:1.2;min-height:32.5px}
.layer h3 i{font-style:normal;font-family:var(--mono);font-size:10.5px;color:var(--brand)}
.layer p{font-size:12.5px;color:var(--ink3);margin:0 12px 12px;line-height:1.4}
.lk{width:18px;max-width:18px;height:calc(var(--ch) + 22px);flex:none;display:flex;align-items:center;justify-content:center;position:relative;transition:max-width .7s cubic-bezier(.3,.7,.2,1),opacity .5s ease;overflow:hidden}
.layers-box .lk{height:var(--ch)}
.lk i{display:block;width:18px;height:1px;background:var(--ink4);position:relative;flex:none}
.lk i::after{content:"";position:absolute;right:0;top:-3px;width:5px;height:5px;border-right:1px solid var(--ink4);border-top:1px solid var(--ink4);transform:rotate(45deg)}
.layers-box{display:flex;align-items:stretch;position:relative;border:1px solid var(--brand100);background:linear-gradient(180deg,#f6f8ff,#fbfcff);border-radius:14px;padding:22px 10px 10px;max-width:900px;transition:max-width .9s cubic-bezier(.3,.7,.2,1),opacity .6s ease,padding .9s cubic-bezier(.3,.7,.2,1);overflow:hidden;flex:none}
.layers-box .lbl{position:absolute;top:-1px;left:12px;background:var(--brand);color:#fff;font-size:10.5px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;padding:3px 9px;border-radius:0 0 8px 8px;white-space:nowrap}
.layers-box .layer{transition-delay:var(--d,0s),var(--d,0s),var(--d,0s),0s,0s,0s}
/* collapsed: only the ends are visible until the chain opens in view */
.lad:not(.open) .layers-box{max-width:0;padding-left:0;padding-right:0;border-left-width:0;border-right-width:0;opacity:0}
.lad:not(.open) .lk2{max-width:0;opacity:0}
.lad:not(.open) .layers-box .layer,.lad:not(.open) .layers-box .lk{opacity:0;transition-delay:0s}
.layers-box .lk{transition-delay:var(--d,0s)}
.lad-out{max-width:62ch;margin:22px auto 0;color:var(--ink2);text-align:center}
.layer{transition:max-width .7s cubic-bezier(.3,.7,.2,1),opacity .5s ease,border-width 0s linear .7s,border-color .12s ease-out,transform .12s ease-out,box-shadow .12s ease-out}
@media(hover:hover){.lad.open .layer:hover{transform:translateY(-3px);border-color:var(--brand200);border-color:color-mix(in srgb,var(--brand) 40%,var(--line));box-shadow:0 10px 22px -12px rgba(16,24,40,.28)}}
@media(max-width:1040px){.lad{justify-content:center}.layer.cap{margin-top:0}.layers-box{flex:1 1 100%;max-width:100%!important;flex-wrap:wrap;gap:12px;justify-content:center;padding:26px 10px 10px!important;border-width:1px!important;opacity:1!important}.lad .lk{display:none}.layers-box .layer{opacity:1!important}}
@media(max-width:640px){.lad{--cw:150px}}
@media (prefers-reduced-motion:reduce){.layer *{animation:none!important}.g-sched .req{opacity:1}.ed2 .op .a,.ed2 .pct .a,.ed2 .bar,.ed2 .f2{opacity:1}.layer,.lk,.layers-box{transition:none}}
/* application: streamed answer */
.g-app .chat{width:128px;font-size:9px;line-height:1.3}
.g-app .u{background:var(--brand);color:#fff;border-radius:10px 10px 2px 10px;padding:3px 7px;margin:0 0 4px 22px}
.g-app .a{background:#fff;border:1px solid var(--line);border-radius:10px 10px 10px 2px;padding:3px 7px;margin-right:14px;color:var(--ink2);min-height:26px}
.g-app .a span{opacity:0;animation:tok 6.5s infinite}
.g-app .caret{display:inline-block;width:1px;height:10px;background:var(--brand);vertical-align:-1px;animation:blink 1s steps(2) infinite}
@keyframes tok{0%{opacity:0}4%,78%{opacity:1}88%,100%{opacity:0}}
@keyframes blink{to{visibility:hidden}}
/* silicon: a GPU board */
.g-gpu{width:132px;height:81px}
.g-gpu .bracket{fill:#9ca3af}.g-gpu .board{fill:#1f2937}.g-gpu .fingers rect{fill:#d4a017}
.g-gpu .hbm{fill:#4b5563;animation:hbm 2.8s ease-in-out infinite}
.g-gpu .die{fill:#0b1220;stroke:#374151;stroke-width:1}
.g-gpu .core{fill:var(--brand2);opacity:.25;animation:core 1.9s ease-in-out infinite}
.g-gpu text{font-size:7px;font-family:var(--mono);fill:#9ca3af;text-anchor:middle}
@keyframes hbm{0%,100%{fill:#4b5563}50%{fill:#6b7280}}
@keyframes core{0%,100%{opacity:.2}50%{opacity:1}}
/* 01 serving engine (one 8 s loop, teal) */
.g-engine,.layer .g-engine{--eng:#0f766e;--eng2:#14b8a6;--eng50:#ccfbf1;flex-direction:column;align-items:stretch;justify-content:flex-start;padding:6px 6px 5px;gap:4px}
.g-engine .tabs{display:flex;gap:3px}
.g-engine .tabs span{font-size:7px;font-weight:600;padding:1px 6px;border-radius:999px;border:1px solid var(--line);color:var(--ink3);background:#fff;line-height:11px}
.g-engine .tabs span.on{background:#0f766e;border-color:#0f766e;color:#fff}
.g-engine .mid{display:grid;grid-template-columns:minmax(0,1fr) 42px;gap:5px;align-items:start}
.g-engine .tgs{display:flex;flex-direction:column;gap:3px}
.tg{display:flex;align-items:center;gap:4px;font-size:7.5px;line-height:11px;color:var(--ink2);font-family:var(--mono);white-space:nowrap}
.tg i{position:relative;width:16px;height:10px;border-radius:6px;background:var(--line);animation:tg-bg 8s infinite;animation-delay:var(--d,0s);flex-shrink:0}
.tg i::after{content:"";position:absolute;top:1.5px;left:1.5px;width:7px;height:7px;border-radius:50%;background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.25);animation:tg-knob 8s infinite;animation-delay:var(--d,0s)}
@keyframes tg-bg{0%,12%{background:var(--line)}15%,84%{background:var(--eng)}90%,100%{background:var(--line)}}
@keyframes tg-knob{0%,12%{left:1.5px}15%,84%{left:7.5px}90%,100%{left:1.5px}}
.g-engine .tps{text-align:right}
.g-engine .tps small{display:block;font-size:6px;color:var(--ink3);letter-spacing:.04em;text-transform:uppercase}
.g-engine .vals{display:block;position:relative;height:16px;font-family:var(--mono);font-size:12px;font-weight:600;color:var(--eng);line-height:16px}
.g-engine .vals b{position:absolute;right:0;top:0;opacity:0}
.g-engine .v1{animation:ev1 8s infinite}.g-engine .v2{animation:ev2 8s infinite}.g-engine .v3{animation:ev3 8s infinite}.g-engine .v4{animation:ev4 8s infinite}
@keyframes ev1{0%,14%{opacity:1}16%,88%{opacity:0}92%,100%{opacity:1}}
@keyframes ev2{0%,15%{opacity:0}17%,29%{opacity:1}31%,100%{opacity:0}}
@keyframes ev3{0%,30%{opacity:0}32%,44%{opacity:1}46%,100%{opacity:0}}
@keyframes ev4{0%,45%{opacity:0}47%,88%{opacity:1}92%,100%{opacity:0}}
.g-engine .bar{display:block;height:4px;border-radius:2px;background:var(--line2);margin-top:3px;overflow:hidden}
.g-engine .bar em{display:block;height:100%;border-radius:2px;background:var(--eng2);width:30%;animation:ebar 8s infinite}
@keyframes ebar{0%,12%{width:30%}17%,27%{width:50%}32%,42%{width:85%}47%,88%{width:100%}92%,100%{width:30%}}
.g-engine .chips{display:flex;gap:4px}
.g-engine .chips span{font-size:6.5px;font-family:var(--mono);color:var(--ink3);background:#fff;border:1px solid var(--line);border-radius:4px;padding:0 5px;line-height:11px;position:relative;min-width:26px;text-align:center}
.g-engine .dt b{position:absolute;left:0;right:0;top:0;font-weight:500;opacity:0}
.g-engine .dt .a{animation:ev1 8s infinite;color:var(--ink3)}.g-engine .dt .b{animation:ev4b 8s infinite;color:var(--eng)}
@keyframes ev4b{0%,15%{opacity:0}17%,88%{opacity:1}92%,100%{opacity:0}}
/* 02 batching */
.g-sched{width:100%;height:100%;padding:8px 10px}
.g-sched .slot{fill:var(--line2)}
.g-sched .req{fill:var(--brand2);opacity:0;animation:req-in 5.2s infinite}
.g-sched .req.c1{fill:#14b8a6}.g-sched .req.c2{fill:#f59e0b}.g-sched .req.c3{fill:#a78bfa}.g-sched .req.c4{fill:#f472b6}
.g-sched .ax{font-size:8px;fill:var(--ink4);font-family:var(--mono)}
@keyframes req-in{0%{transform:translateX(110px);opacity:0}10%{transform:none;opacity:1}78%{transform:none;opacity:1}88%,100%{transform:none;opacity:0}}
/* 03 fusion: zoom in, fuse, zoom out (one 11 s loop) */
.g-graph{width:100%;height:100%;padding:4px 4px 2px}
.g-graph .scene{transform-origin:0 0;animation:zoom 11s cubic-bezier(.45,.05,.3,1) infinite}
.g-graph .e{stroke:var(--ink4);stroke-width:.8;fill:none}
.g-graph .er{stroke-dasharray:2 2;stroke:var(--ink4)}
.g-graph .ei{animation:fuse-edge 11s infinite}
.g-graph .n rect{fill:#fff;stroke:var(--ink4);stroke-width:.8}
.g-graph .n text{font-size:4.6px;font-family:var(--mono);fill:var(--ink2);text-anchor:middle}
.g-graph .f1,.g-graph .f2,.g-graph .f3{animation:fuse-node 11s infinite}
.g-graph .f1{--dy:24px}.g-graph .f2{--dy:0px}.g-graph .f3{--dy:-24px}
.g-graph .fused{opacity:0;transform-box:fill-box;transform-origin:center;animation:fuse-in 11s infinite}
.g-graph .fused rect{fill:var(--brand50);stroke:var(--brand);stroke-width:1.2}
.g-graph .fused text{font-size:4.8px;font-family:var(--mono);fill:var(--brandD);text-anchor:middle;font-weight:500}
.g-graph .cap{font-size:6.5px;font-family:var(--mono);fill:var(--ink4);animation:cap1 11s infinite}
.g-graph .cap.c2{fill:var(--brandD);animation:cap2 11s infinite}
@keyframes zoom{0%,14%{transform:translate(0px,0px) scale(1) translate(0px,0px)}26%,50%{transform:translate(90px,45px) scale(1.55) translate(-52px,-44px)}62%,100%{transform:translate(0px,0px) scale(1) translate(0px,0px)}}
@keyframes fuse-node{0%,33%{transform:translateY(0);opacity:1}44%,92%{transform:translateY(var(--dy));opacity:0}97%,100%{transform:translateY(0);opacity:1}}
@keyframes fuse-edge{0%,33%{opacity:1}42%,92%{opacity:0}97%,100%{opacity:1}}
@keyframes fuse-in{0%,36%{opacity:0;transform:scale(.6)}48%,92%{opacity:1;transform:scale(1)}97%,100%{opacity:0;transform:scale(.6)}}
@keyframes cap1{0%,40%{opacity:1}48%,92%{opacity:0}97%,100%{opacity:1}}
@keyframes cap2{0%,44%{opacity:0}52%,92%{opacity:1}97%,100%{opacity:0}}
/* 04 thread tiles */
.g-kern .grid{display:grid;grid-template-columns:repeat(9,11px);gap:3px}
.g-kern i{display:block;width:11px;height:11px;border-radius:2px;background:var(--line2);animation:wave 3.4s infinite}
@keyframes wave{0%{background:var(--line2)}7%{background:#16a34a}22%,78%{background:#bbf7d0}90%,100%{background:var(--line2)}}
/* 05 ptx → sass → steered sass, inside a miniature editor (one 9 s loop) */
.g-sass{padding:5px;align-items:stretch}
.ed2{width:100%;height:100%;background:#0f1117;border:1px solid #262b38;border-radius:6px;overflow:hidden;font-family:var(--mono);font-size:7px;color:#c9d1d9;display:flex;flex-direction:column;text-align:left}
.ed2 .tb{height:15px;flex:none;display:flex;align-items:center;padding:0 7px;background:#161922;border-bottom:1px solid #262b38;font-size:7px;color:#8e94a3;position:relative}
.ed2 .tb i{width:5px;height:5px;border-radius:50%;background:#f59e0b;flex:none}
.ed2 .tb span{position:absolute;left:17px;top:0;line-height:15px;opacity:0;white-space:nowrap}
.ed2 .f1{animation:ph1 9s infinite}.ed2 .f2{animation:ph23 9s infinite}
.ed2 .tb em{position:absolute;right:5px;top:3px;font-style:normal;font-size:6px;line-height:9px;padding:0 4px;border-radius:3px;background:#2b2352;color:#c4b5fd;opacity:0;animation:ph3 9s infinite}
.ed2 .body{flex:1;padding:5px 5px 0 3px;display:grid;grid-template-columns:8px minmax(0,1fr);column-gap:4px;row-gap:3px;align-content:start}
.ed2 .n{color:#5c6373;text-align:right;line-height:12px}
.ed2 .row{position:relative;height:12px;display:grid;grid-template-columns:46px minmax(0,1fr) 22px;gap:4px;align-items:center;min-width:0}
.ed2 .p{position:absolute;left:0;top:0;line-height:12px;white-space:nowrap;opacity:0;animation:ph1 9s infinite;color:#c9d1d9}
.ed2 .kop{color:#c084fc;font-weight:500}.ed2 .reg{color:#5eead4;font-weight:400}
.ed2 .op,.ed2 .pct{position:relative;height:12px}
.ed2 .pct{text-align:right}
.ed2 .a,.ed2 .b{position:absolute;left:0;right:0;top:0;line-height:12px;font-weight:500;opacity:0}
.ed2 .op .a{animation:ph2 9s infinite;color:#c084fc}.ed2 .op .b{animation:ph3 9s infinite;color:#c4b5fd}
.ed2 .pct .a{animation:ph2 9s infinite;color:#c9d1d9}.ed2 .pct .b{animation:ph3 9s infinite;color:#c9d1d9}
.ed2 .bar{height:5px;background:#262b38;border-radius:3px;overflow:hidden;opacity:0;animation:ph23 9s infinite}
.ed2 .bar i{display:block;height:100%;border-radius:3px;width:var(--w0);background:#f87171;animation:sw-bar 9s infinite}
@keyframes ph1{0%,26%{opacity:1}29%,100%{opacity:0}}
@keyframes ph2{0%,27%{opacity:0}30%,60%{opacity:1}63%,100%{opacity:0}}
@keyframes ph3{0%,61%{opacity:0}64%,94%{opacity:1}97%,100%{opacity:0}}
@keyframes ph23{0%,27%{opacity:0}30%,94%{opacity:1}97%,100%{opacity:0}}
@keyframes sw-bar{0%,60%{width:var(--w0);background:#f87171}66%,100%{width:var(--w1);background:#8b5cf6}}
/* tour */
.tour{padding:28px 0 20px}
.tour-k{display:block;margin-bottom:8px}
.tour-bar{position:sticky;top:62px;z-index:40;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 0;margin-bottom:8px}
.tour-bar nav{display:flex;gap:4px;overflow-x:auto;scrollbar-width:none}
.tour-bar nav::-webkit-scrollbar{display:none}
.tour-bar a{display:inline-flex;gap:8px;align-items:center;padding:7px 12px;border-radius:7px;font-size:13.5px;font-weight:500;color:var(--ink3);white-space:nowrap}
.tour-bar a i{font-style:normal;font-family:var(--mono);font-size:11px;color:var(--ink3)}
.tour-bar a.on{color:var(--ink);background:var(--white);box-shadow:0 1px 2px rgba(15,23,42,.06);font-weight:600}
.tour-bar a.on i{color:var(--brand)}
/* steps: copy on one side, the screen on the other, alternating; screens bleed to the viewport edge like the hero so every screen is the same size */
.bleed{max-width:none;padding-left:max(24px,calc((100vw - var(--sbw,0px) - 1132px)/2));padding-right:24px}
.bleed.l{padding-left:24px;padding-right:max(24px,calc((100vw - var(--sbw,0px) - 1132px)/2))}
.step{padding:48px 0 16px;scroll-margin-top:118px}
.step:first-of-type{padding-top:24px}
.split{display:grid;grid-template-columns:minmax(320px,440px) minmax(0,1fr);gap:48px;align-items:center}
.step.flip .split{grid-template-columns:minmax(0,1fr) minmax(320px,440px)}
.step.flip .step-copy{order:2}.step.flip .step-shot{order:1}
.step-shot{min-width:0}
.step-no{font-family:var(--mono);font-size:12px;color:var(--brand);margin-bottom:10px}
.step h3{font-size:clamp(22px,2.1vw,27px);font-weight:800;letter-spacing:-.03em;line-height:1.15}
.step-copy>p{font-size:15.5px;color:var(--ink2);margin-top:12px}
.step-copy h4{font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3);margin-top:18px}
.step-copy .chg{list-style:none;padding:0;margin-top:10px;color:var(--ink2);font-size:14.5px}
.step-copy .chg li{display:flex;gap:10px;align-items:flex-start;margin-bottom:8px}
.step-copy .chg .ic{width:17px;height:17px;color:var(--brand);flex:none;margin-top:2px}
.step-copy .with{font-size:13.5px;color:var(--ink3);margin-top:8px}
@media(max-width:1280px){.split{grid-template-columns:minmax(300px,400px) minmax(0,1fr);gap:32px}.step.flip .split{grid-template-columns:minmax(0,1fr) minmax(300px,400px)}.step-copy>p{font-size:15px}}
@media(max-width:1100px){.bleed,.bleed.l{padding:0 24px}.split{grid-template-columns:minmax(0,1fr);gap:24px}.step.flip .split{grid-template-columns:minmax(0,1fr)}.step.flip .step-copy{order:1}.step.flip .step-shot{order:2}.step{padding:48px 0 8px}}
@media(max-width:600px){.bleed,.bleed.l{padding:0 16px}}
/* services: a photo band with glass cards */
.svc{position:relative;padding:72px 0 56px;border-top:1px solid var(--line);overflow:hidden;isolation:isolate}
.svc-bg{position:absolute;inset:0;z-index:-1;background-image:linear-gradient(90deg,rgba(245,246,250,.97) 0%,rgba(245,246,250,.9) 38%,rgba(245,246,250,.62) 100%),url("assets/stock/office-laptop.jpg");background-size:cover;background-position:center 45%}
.svc-head{max-width:640px}
.svc-head .k{display:block;margin-bottom:12px}
.svc-head .lede{margin-top:12px}
.svc-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:32px}
.svc-item{background:rgba(255,255,255,.86);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.9);box-shadow:0 1px 2px rgba(15,23,42,.05),0 12px 30px -16px rgba(15,23,42,.18);border-radius:12px;padding:18px 18px 16px}
.svc-i{width:38px;height:38px;border-radius:10px;background:var(--brand50);color:var(--brand);display:grid;place-items:center;margin-bottom:14px}
.svc-i .ic{width:19px;height:19px}
.svc-item h3{font-size:15.5px;margin-bottom:6px;letter-spacing:-.01em}
.svc-item p{font-size:14px;color:var(--ink2)}
.svc-item small{display:block;font-family:var(--mono);font-size:11px;color:var(--ink3);margin-top:10px;line-height:1.5}
@media(max-width:1000px){.svc-grid{grid-template-columns:1fr 1fr}}
@media(max-width:560px){.svc-grid{grid-template-columns:1fr}}
/* engagement: photo beside a three-step path */
.engage{padding:72px 0 48px;border-top:1px solid var(--line)}
.eng-grid{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:56px;align-items:stretch}
.eng-photo{position:relative;min-height:420px;border-radius:16px;background-image:linear-gradient(180deg,rgba(15,23,42,0) 55%,rgba(15,23,42,.45)),url("assets/stock/pair-review.jpg");background-size:cover;background-position:center 30%}
.eng-steps .k{display:block;margin-bottom:12px}
.eng-steps h2{margin-bottom:8px}
.steps{list-style:none;margin:20px 0 0;padding:0;position:relative}
.steps::before{content:"";position:absolute;left:21px;top:22px;bottom:22px;width:2px;background:var(--line)}
.steps li{display:grid;grid-template-columns:44px minmax(0,1fr);gap:18px;padding:16px 0;position:relative}
.sp-i{width:44px;height:44px;border-radius:50%;background:var(--white);border:2px solid var(--line);color:var(--ink3);display:grid;place-items:center;position:relative;z-index:1}
.sp-i .ic{width:20px;height:20px}
.steps li.hl .sp-i{border-color:var(--brand);background:var(--brand);color:#fff}
.steps small{display:block;font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--brand);margin:6px 0 4px}
.steps h3{font-size:19px;display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.steps h3 i{font-style:normal;font-family:var(--mono);font-size:12px;color:var(--ink3);font-weight:500}
.steps p{font-size:15px;color:var(--ink2);margin-top:6px;max-width:56ch}
.steps .btn{margin-top:12px}
.guar{display:inline-flex;align-items:center;gap:8px;margin-top:12px;font-size:14px;font-weight:600;color:var(--ink);background:var(--brand50);border:1px solid var(--brand100);border-radius:8px;padding:8px 12px}
.guar .ic{width:16px;height:16px;color:var(--brand)}
@media(max-width:900px){.eng-grid{grid-template-columns:1fr;gap:28px}.eng-photo{min-height:260px}}
/* stack: four typographic lists */
.stack{padding:56px 0 48px;border-top:1px solid var(--line)}
.stack-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:40px;margin-top:28px}
.sg{border-top:2px solid var(--ink);padding-top:14px;min-width:0}
.sg h3{font-size:14px;letter-spacing:-.01em;display:flex;align-items:center;gap:8px;margin-bottom:10px}
.sg h3 .ic{width:16px;height:16px;color:var(--brand)}
.stk{list-style:none;margin:0;padding:0}
.stk li{display:flex;align-items:center;gap:9px;font-size:14px;color:var(--ink2);padding:6px 0;border-bottom:1px solid var(--line2);line-height:1.35}
.stk li:last-child{border-bottom:0}
.stk a{color:inherit;text-decoration:none;border-bottom:1px solid var(--line);transition:color .12s,border-color .12s}.stk a:hover{color:var(--brand);border-color:var(--brand)}
.stk .lg{width:14px;height:14px;flex:none}.stk .nolg{width:14px;height:14px;flex:none;display:inline-block}
@media(max-width:1000px){.stack-grid{grid-template-columns:1fr 1fr;gap:32px}}
@media(max-width:560px){.stack-grid{grid-template-columns:1fr;gap:24px}}
/* clients */
.clients{padding:64px 0 32px;border-top:1px solid var(--line)}
.quotes{display:grid;grid-template-columns:1fr 1fr;gap:48px;margin-top:28px}
.quote p{font-size:19px;line-height:1.5;color:var(--ink);font-weight:500;letter-spacing:-.01em}
.quote footer{display:flex;align-items:center;gap:10px;margin-top:16px;font-size:13px;color:var(--ink3)}
.quote footer img{height:22px;width:auto}
@media(max-width:800px){.quotes{grid-template-columns:1fr;gap:28px}}
/* team */
.team{padding:64px 0 24px;border-top:1px solid var(--line)}
.people{display:grid;grid-template-columns:1fr 1fr;gap:40px;margin-top:28px}
.person{display:flex;gap:18px;align-items:flex-start}
.person img{width:72px;height:72px;border-radius:50%;object-fit:cover;flex-shrink:0}
.person h3{font-size:17px}
.person i{display:block;font-style:normal;font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--brand);margin:2px 0 8px}
.person p{font-size:14.5px;color:var(--ink2)}
.person a{color:var(--brand)}
.person small{display:block;margin-top:8px;font-size:13px;color:var(--ink3)}
.oss{margin-top:36px;border-top:1px solid var(--line)}
.oss a{display:grid;grid-template-columns:160px 1fr;gap:16px;padding:12px 0;border-bottom:1px solid var(--line);font-size:14.5px;color:var(--ink2)}
.oss a b{font-family:var(--mono);color:var(--ink);font-weight:500}
.oss a:hover b{color:var(--brand)}
@media(max-width:700px){.people{grid-template-columns:1fr}.oss a{grid-template-columns:1fr;gap:2px}}
/* faq */
.faq{padding:64px 0 32px;border-top:1px solid var(--line)}
.faq details{border-bottom:1px solid var(--line)}
.faq summary{cursor:pointer;list-style:none;padding:18px 40px 18px 0;font-weight:600;font-size:16px;color:var(--ink);position:relative}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";position:absolute;right:4px;top:14px;font-size:22px;font-weight:300;color:var(--brand);transition:.2s}
.faq details[open] summary::after{transform:rotate(45deg)}
.faq details p{padding:0 0 20px;max-width:70ch;color:var(--ink2);font-size:15.5px}
/* cta */
.cta{background:var(--brand50);border-top:1px solid var(--brand100);border-bottom:1px solid var(--brand100);padding:64px 0;margin-top:40px}
.cta .k{display:block;margin-bottom:12px}
.cta h2{max-width:22ch}
.cta .lede{margin-top:12px}
.cta .hero-cta{margin-top:24px}
footer.site{padding:28px 0 40px;font-size:13px;color:var(--ink3)}
.foot{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;align-items:center}
.foot-links{display:flex;gap:18px;flex-wrap:wrap}.foot-links a{padding:4px 0}
.foot-links a:hover{color:var(--ink)}
.foot-legal{flex-basis:100%;font-style:normal;font-size:12.5px;line-height:1.6;color:var(--ink3);margin-top:8px}
.foot-legal .flag{display:inline-block;width:16px;height:11px;vertical-align:-1px;margin-left:3px;border-radius:1.5px;box-shadow:0 0 0 1px var(--line2)}

/* ════════ App screens (product UI, self-contained) ════════ */
.mock{position:relative;aspect-ratio:16/10;display:flex;flex-direction:column;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--bg);box-shadow:0 1px 2px rgba(15,23,42,.06),0 16px 40px -12px rgba(15,23,42,.14);font-size:12px;line-height:1.4;color:var(--ink);font-family:var(--font);user-select:none;-webkit-user-select:none;-webkit-touch-callout:none;cursor:default;font-variant-numeric:tabular-nums}
.mock *{cursor:default}
.chrome{display:flex;align-items:center;gap:12px;height:38px;padding:0 12px;background:#fff;border-bottom:1px solid var(--line);flex-shrink:0}
.chrome .dots{display:flex;gap:6px}.chrome .dots i{width:10px;height:10px;border-radius:50%;background:var(--line)}
.chrome .url{flex:1;max-width:420px;margin:0 auto;font-family:var(--mono);font-size:11px;color:var(--ink3);background:var(--bg);border:1px solid var(--line2);border-radius:6px;padding:4px 12px;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.app{flex:1;min-height:0;display:flex;flex-direction:column}
.appbar{display:flex;align-items:center;gap:10px;height:40px;padding:0 14px;background:#fff;border-bottom:1px solid var(--line);flex-shrink:0}
.appbar .mark{width:18px;height:18px;border-radius:5px;background:var(--brand)}
.appbar b{font-size:13px;font-weight:700;color:var(--ink)}
.appbar .ws{font-size:11.5px;color:var(--ink3);padding:3px 8px;border:1px solid var(--line);border-radius:6px;margin-left:4px}
.appbar .search{margin-left:auto;width:220px;font-size:11px;color:var(--ink4);background:var(--bg);border:1px solid var(--line2);border-radius:6px;padding:4px 10px}
.appbar .bell{width:14px;height:14px;border-radius:4px;border:1.5px solid var(--ink4)}
.appbar .av{width:22px;height:22px;border-radius:50%;background:var(--brand100);color:var(--brandD);font-size:10px;font-weight:700;display:grid;place-items:center}
.abody{flex:1;min-height:0;display:grid;grid-template-columns:168px minmax(0,1fr)}
.anav{background:#fff;border-right:1px solid var(--line);padding:10px 8px;display:flex;flex-direction:column;gap:1px;overflow:hidden}
.anav .sec{font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--ink4);padding:8px 10px 4px}
.anav a{display:flex;align-items:center;gap:8px;padding:5px 10px;border-radius:6px;font-size:12px;color:var(--ink2)}
.anav a i{width:12px;height:12px;border-radius:3px;background:var(--line);flex-shrink:0}
.anav a.on{background:var(--brand50);color:var(--brandD);font-weight:600}
.anav a.on i{background:var(--brand2)}
.anav .nfoot{margin-top:auto;font-size:10.5px;color:var(--ink3);padding:8px 10px;border-top:1px solid var(--line2)}
.amain{padding:12px 16px;overflow:hidden;min-width:0}
.ph{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;margin-bottom:8px}
.crumb{font-size:11px;color:var(--ink3);margin-bottom:2px}
.ph h1{font-size:16px;font-weight:700;letter-spacing:-.01em;line-height:1.2}
.ph h1 .mu{font-weight:400;font-size:12px;margin-left:6px}
.actions{display:flex;gap:6px;align-items:center}
.ab{font-size:11.5px;font-weight:600;padding:5px 10px;border-radius:6px;border:1px solid var(--line);background:#fff;color:var(--ink2);white-space:nowrap}
.ab.pri{background:var(--brand);border-color:var(--brand);color:#fff}
.ptabs{display:flex;gap:2px;border-bottom:1px solid var(--line);margin-bottom:10px}
.ptabs span{padding:6px 10px;font-size:12px;color:var(--ink3);border-bottom:2px solid transparent;margin-bottom:-1px}
.ptabs span.on{color:var(--ink);font-weight:600;border-bottom-color:var(--brand)}
.ptabs em{font-style:normal;font-size:10.5px;color:var(--ink4);margin-left:4px}
.stats{display:flex;margin-bottom:10px;border:1px solid var(--line);border-radius:8px;background:#fff;overflow:hidden}
.stat{flex:1;min-width:0;padding:7px 12px;border-right:1px solid var(--line2)}
.stat:last-child{border-right:0}
.stat small{display:block;font-size:10.5px;color:var(--ink3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.stat b{display:block;font-size:17px;font-weight:700;color:var(--ink);letter-spacing:-.01em;margin-top:1px;line-height:1.2}
.stat span{font-size:10.5px;color:var(--ink3)}
.stat span.ok{color:var(--ok)}.stat span.warn{color:var(--warn)}
.seg{display:flex;align-items:center;gap:2px;margin-bottom:10px;font-size:11.5px}
.seg span{padding:4px 10px;border-radius:6px;color:var(--ink3)}
.seg span.on{background:#fff;color:var(--ink);font-weight:600;box-shadow:0 1px 2px rgba(15,23,42,.08)}
.seg .sp{flex:1}
.seg .q{color:var(--ink3);background:#fff;border:1px solid var(--line);border-radius:6px;padding:4px 10px;width:220px}
.seg.small{margin:0;border:1px solid var(--line);border-radius:6px;background:#fff;padding:1px}
.seg.small span{padding:3px 8px;font-size:11px}
.pane{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:10px;align-items:start}
.pane.narrow{grid-template-columns:minmax(0,1fr) 268px}
.blk{background:#fff;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.blk+.blk{margin-top:10px}
.bh{display:flex;justify-content:space-between;align-items:baseline;gap:10px;padding:7px 12px;font-size:12px;font-weight:600;color:var(--ink);border-bottom:1px solid var(--line2)}
.bh .mu{font-weight:400}
.mu{color:var(--ink3);font-size:11px}
.tbl{width:100%;border-collapse:collapse}
.tbl th{text-align:left;font-weight:500;font-size:11px;color:var(--ink3);padding:6px 10px;border-bottom:1px solid var(--line2);white-space:nowrap}
.tbl td{padding:6px 10px;border-bottom:1px solid var(--line2);white-space:nowrap;font-size:11.5px;color:var(--ink)}
.tbl tr:last-child td{border-bottom:0}
.tbl .n{text-align:right;font-family:var(--mono);font-size:11.5px}
.tbl th.n{font-family:var(--font)}
.tbl tr.sel td{background:var(--brand50)}
.tbl .mono{font-family:var(--mono);font-size:11.5px}
.tbl td.mu{font-size:11px}
.st{display:inline-flex;align-items:center;gap:6px;font-size:11.5px;color:var(--ink2);white-space:nowrap}
.st::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--ink4);flex-shrink:0}
.st.ok::before{background:#10b981}.st.bad::before{background:#e11d48}.st.warn::before{background:#f59e0b}.st.brand::before{background:var(--brand2)}.st.run::before{background:#0ea5e9;box-shadow:0 0 0 3px rgba(14,165,233,.18)}.st.mu{color:var(--ink3)}
.side{background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px 14px;align-self:start}
.sh{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:8px}
.sh b{font-size:13px;font-weight:700;color:var(--ink)}
.sh2{font-size:11px;font-weight:600;color:var(--ink);margin:10px 0 6px;padding-top:8px;border-top:1px solid var(--line2)}
.side .tbl{margin:0 -14px;width:calc(100% + 28px)}
.side .tbl th,.side .tbl td{padding:5px 14px}
.kv{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;font-size:11.5px;margin-bottom:4px}
.kv dt{color:var(--ink3)}
.kv dd{text-align:right;color:var(--ink);font-family:var(--mono);font-size:11px}
.ai{margin-top:10px;padding:8px 10px;border-left:3px solid var(--ai);background:#f5f3ff;border-radius:0 6px 6px 0;font-size:11.5px;color:var(--ink2)}
.ai b{display:block;font-size:10.5px;color:var(--ai);font-weight:600;margin-bottom:2px}
.acts{display:flex;gap:6px;margin-top:12px;flex-wrap:wrap}
.mb{font-size:11.5px;font-weight:600;padding:6px 11px;border-radius:6px;border:1px solid var(--line);background:#fff;color:var(--ink2);white-space:nowrap;transition:transform .12s ease,background .25s ease,color .25s ease}
.mb.pri{background:var(--brand);border-color:var(--brand);color:#fff}
.mb.pressed{transform:scale(.94)}
.mb.done{background:#ecfdf5;color:var(--ok);border-color:#a7f3d0}
.ch{display:block;width:100%;height:auto;padding:6px 10px 2px}
.ch .grid{stroke:var(--line2);stroke-width:1}
.ch .ax{font-size:9px;fill:var(--ink4);font-family:var(--mono)}
.ch .ln{fill:none;stroke-width:1.8;stroke-linejoin:round}
.ch .ln.brand{stroke:var(--brand2)}.ch .ln.amber{stroke:#f59e0b}
.ch .area{fill:var(--brand2);opacity:.08}
.ch .slo{stroke:#e11d48;stroke-width:1;stroke-dasharray:4 3}
.ch .mk circle{fill:#fff;stroke:var(--brand2);stroke-width:1.8}
.ch .mk.bad circle{stroke:#e11d48}.ch .mk.hi circle{fill:var(--brand2)}
.ch .mk text{font-size:9.5px;fill:var(--ink2)}
.ch .mk.bad text{fill:var(--bad)}
.bars{display:flex;align-items:flex-end;gap:5px;height:50px;padding:8px 12px 0}
.bars i{flex:1;background:var(--brand2);border-radius:2px 2px 0 0;transition:height .9s cubic-bezier(.2,.8,.2,1);opacity:.85}
.bars-x{display:flex;justify-content:space-between;font-size:9.5px;color:var(--ink4);padding:4px 12px 8px;font-family:var(--mono)}
.prog{display:grid;grid-template-columns:70px 1fr 48px;gap:8px;align-items:center;font-size:11px;color:var(--ink2);padding:3px 0}
.prog i{display:block;height:6px;border-radius:3px;background:var(--line2);overflow:hidden}
.prog b{display:block;height:100%;background:var(--brand2);transition:width .9s ease}
.prog em{font-style:normal;text-align:right;font-family:var(--mono);font-size:10.5px;color:var(--ink)}
.hb{display:grid;grid-template-columns:150px 1fr 56px;gap:10px;align-items:center;font-size:11.5px;color:var(--ink2);padding:4px 12px}
.side .hb{grid-template-columns:110px 1fr 44px;padding:3px 0}
.hb i{display:block;height:7px;border-radius:3px;background:var(--line2);overflow:hidden}
.hb b{display:block;height:100%;background:var(--brand2);transition:width .9s cubic-bezier(.2,.8,.2,1)}
.hb b.bad{background:#fb7185}.hb b.warn{background:#fbbf24}
.hb em{font-style:normal;text-align:right;font-family:var(--mono);font-size:11px;color:var(--ink)}
.blk .hb:first-of-type{padding-top:10px}.blk .hb:last-child{padding-bottom:10px}
.evts{padding:4px 12px 6px}
.evt{display:flex;gap:8px;padding:4px 0;border-bottom:1px solid var(--line2);font-size:11.5px;color:var(--ink2)}
.evt:last-of-type{border-bottom:0}
.evt time{font-family:var(--mono);font-size:10px;color:var(--ink3);flex-shrink:0;padding-top:2px}
.gpus{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding:10px 12px}
.gpu{border:1px solid var(--line2);border-radius:6px;padding:7px 9px;background:var(--bg)}
.gpu b{font-family:var(--mono);font-size:10.5px;font-weight:500;display:flex;justify-content:space-between;color:var(--ink2)}
.gpu i{display:block;height:6px;border-radius:3px;background:var(--line);margin:5px 0 4px;overflow:hidden}
.gpu em{display:block;height:100%;background:var(--brand2);transition:width .9s ease}
.gpu em.warn{background:#fbbf24}
.gpu small{font-size:10px;color:var(--ink3)}
.code{padding-bottom:6px}
.sl{display:grid;grid-template-columns:38px 1fr 90px 44px;gap:8px;align-items:center;padding:1.5px 12px;font-family:var(--mono);font-size:11px}
.sl .a{color:var(--ink4)}.sl .i{color:var(--ink)}.sl .i b{color:var(--brand);font-weight:500}
.sl .h{height:6px;border-radius:3px;background:var(--line2);overflow:hidden}
.sl .h i{display:block;height:100%;background:#fb7185;transition:width .8s ease}.sl .h i.warn{background:#fbbf24}.sl .h i.ok{background:#34d399}
.sl .c{text-align:right;color:var(--ink3)}
.sl.mu .i{color:var(--ink3);font-size:10.5px}
.code .sl:first-of-type{padding-top:8px}
.hide-md{}
/* playback */
.mock [data-a="0"]{opacity:0;transform:translateY(4px)}
.mock [data-a]{transition:opacity .4s ease,transform .4s ease}
.live{position:absolute;right:12px;top:9px;display:inline-flex;align-items:center;gap:6px;font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3)}
.live i{width:7px;height:7px;border-radius:50%;background:#10b981;animation:vo-pulse 1.6s ease-in-out infinite}
@keyframes vo-pulse{0%,100%{opacity:1}50%{opacity:.3}}
.vo-cursor{position:absolute;left:0;top:0;width:20px;height:20px;z-index:6;pointer-events:none;opacity:0;transition:transform .95s cubic-bezier(.3,.7,.2,1),opacity .3s ease;filter:drop-shadow(0 2px 3px rgba(15,23,42,.3))}
.vo-cursor.on{opacity:1}
.vo-ripple{position:absolute;width:30px;height:30px;margin:-15px 0 0 -15px;border-radius:50%;border:2px solid var(--brand2);pointer-events:none;z-index:5;animation:vo-rip .55s ease-out forwards}
@keyframes vo-rip{from{transform:scale(.3);opacity:.9}to{transform:scale(1.4);opacity:0}}
.vo-toast{position:absolute;right:16px;bottom:16px;z-index:7;max-width:calc(100% - 32px);display:flex;gap:8px;align-items:center;background:var(--ink);color:#fff;font-size:11.5px;padding:9px 13px;border-radius:8px;box-shadow:0 16px 40px rgba(15,23,42,.2);opacity:0;transform:translateY(8px);transition:opacity .35s ease,transform .35s ease}
.vo-toast.on{opacity:1;transform:none}
.vo-toast b{color:#34d399;font-weight:700}
@media (prefers-reduced-motion:reduce){.live i{animation:none}}
/* a recording: fixed 1132×708 canvas, scaled as one piece, ratio locked */
.frame{position:relative;width:100%;max-width:1132px;aspect-ratio:16/10}
.frame .mock{position:absolute;left:0;top:0;width:1132px;transform-origin:0 0;transform:scale(var(--s,1))}
"""

# ───────────────────────── Site sections ─────────────────────────
def svc(icon, title, text, tags):
    return f'<div class="svc-item"><div class="svc-i">{ic(icon)}</div><h3>{title}</h3><p>{text}</p><small>{tags}</small></div>'
def stackgroup(icon, title, items):
    """items: (label, brand slug or None). A label may carry [text](url) links; an external link opens in a new tab."""
    def link(m):
        text, url = m.group(1), m.group(2)
        ext = "" if url.startswith("#") else ' target="_blank" rel="noopener"'
        return f'<a href="{url}"{ext}>{text}</a>'
    rows = "".join(f'<li>{lg(slug) if slug else "<i class=\"nolg\"></i>"}<span>{re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, name)}</span></li>' for name, slug in items)
    return f'<div class="sg"><h3>{ic(icon)}{title}</h3><ul class="stk">{rows}</ul></div>'
def layers_html():
    # 01 serving engine: engine tabs, flags switching on one by one, throughput climbing, dtype chip flipping
    engine = ('<div class="g g-engine"><div class="tabs"><span class="on">vLLM</span><span>SGLang</span><span>TRT-LLM</span></div>'
              '<div class="mid"><div class="tgs">' + "".join(f'<div class="tg" style="--d:{k * 1.2:.1f}s"><i></i><span>{t}</span></div>' for k, t in enumerate(("fp8 kv cache", "spec decode", "prefix cache"))) + '</div>'
              '<div class="tps"><small>tok/s</small><span class="vals"><b class="v1">1,840</b><b class="v2">3,120</b><b class="v3">5,460</b><b class="v4">6,120</b></span><i class="bar"><em></em></i></div></div>'
              '<div class="chips"><span class="dt"><b class="a">bf16</b><b class="b">fp8</b></span><span>TP 2</span><span>2×H100</span></div></div>')
    # 02 scheduling: requests packing into GPU slots
    lanes = [[(8, 60), (72, 40), (116, 56)], [(8, 44), (56, 72), (132, 40)], [(8, 80), (92, 36), (132, 40)]]
    sch = ['<svg class="g g-sched" viewBox="0 0 180 80" aria-hidden="true">']
    k = 0
    for r, lane in enumerate(lanes):
        y = 14 + r * 20
        sch.append(f'<rect class="slot" x="8" y="{y}" width="164" height="14" rx="3"/>')
        for x, w in lane:
            sch.append(f'<rect class="req c{k % 5}" x="{x}" y="{y}" width="{w}" height="14" rx="3" style="animation-delay:{k*.28:.2f}s"/>'); k += 1
    sch.append('<text class="ax" x="8" y="76">batch</text><text class="ax" x="172" y="76" text-anchor="end">t →</text></svg>')
    # 03 graph: a transformer block with its real branches (q/k/v, gate/up, residuals); zoom into q·k·v, fuse them into one qkv gemm, zoom out
    w, h = 18, 9; T, M, B = 20, 44, 68
    col = lambda k: 3 + k * 19.5
    N = {"x": (col(0), M), "norm1": (col(1), M), "q": (col(2), T), "k": (col(2), M), "v": (col(2), B), "attn": (col(3), M), "add1": (col(4), M),
         "norm2": (col(5), M), "gate": (col(6), T), "up": (col(6), B), "down": (col(7), M), "add2": (col(8), M)}
    label = {"x": "x", "norm1": "norm", "q": "q", "k": "k", "v": "v", "attn": "attn", "add1": "add", "norm2": "norm", "gate": "gate", "up": "up", "down": "down", "add2": "add"}
    def node(key):
        x, y = N[key]; cls = {"q": " f1", "k": " f2", "v": " f3"}.get(key, "")
        return f'<g class="n{cls}"><rect x="{x:g}" y="{y:g}" width="{w}" height="{h}" rx="2"/><text x="{x + w / 2:g}" y="{y + 6.4:g}">{label[key]}</text></g>'
    def edge(a, b, cls=""):
        ax, ay = N[a]; bx, by = N[b]
        return f'<path class="e{(" " + cls) if cls else ""}" d="M{ax + w:g} {ay + h / 2:g}L{bx:g} {by + h / 2:g}"/>'
    edges = (edge("x", "norm1") + edge("norm1", "q", "ei") + edge("norm1", "k") + edge("norm1", "v", "ei") + edge("q", "attn", "ei") + edge("k", "attn") + edge("v", "attn", "ei")
             + edge("attn", "add1") + edge("add1", "norm2") + edge("norm2", "gate") + edge("norm2", "up") + edge("gate", "down") + edge("up", "down") + edge("down", "add2"))
    xa, add1x, add2x = N["x"][0] + w / 2, N["add1"][0] + w / 2, N["add2"][0] + w / 2
    resid = f'<path class="e er" d="M{xa:g} {M}C{xa:g} 2,{add1x:g} 2,{add1x:g} {M}"/><path class="e er" d="M{add1x:g} {M}C{add1x:g} 2,{add2x:g} 2,{add2x:g} {M}"/>'
    nodes = "".join(node(k) for k in N)
    fx, fy = N["k"]
    fused = f'<g class="fused"><rect x="{fx - 2:g}" y="{fy - 1:g}" width="{w + 4}" height="{h + 2}" rx="2.5"/><text x="{fx + w / 2:g}" y="{fy + 6.4:g}">qkv</text></g>'
    graph = f'<svg class="g g-graph" viewBox="0 0 180 90" aria-hidden="true"><g class="scene">{resid}{edges}{nodes}{fused}</g><text class="cap" x="4" y="87">1 block · 12 ops</text><text class="cap c2" x="4" y="87">q·k·v → 1 fused gemm</text></svg>'
    # 04 kernels: a tile wave across the thread grid
    cells = "".join(f'<i style="animation-delay:{(c + r) * .07:.2f}s"></i>' for r in range(4) for c in range(9))
    kern = f'<div class="g g-kern"><div class="grid">{cells}</div></div>'
    # 05 ptx → sass → steered, shown inside a miniature editor
    def ptx(line):  # opcode purple, registers teal
        op, rest = line.split(" ", 1)
        rest = re.sub(r"\b(rd?\d+)\b", r'<b class="reg">\1</b>', rest)
        return f'<b class="kop">{op}</b> {rest}'
    rows = [("ld.global.u16 r4,[rd2]", "LDG.E.U16", "LDG.E.128", 31, 22, 82, 58), ("bar.sync 0", "BAR.SYNC", "SHFL.BFLY", 11, 7.5, 40, 26), ("st.global.b32 [rd6],r20", "STG.E.32", "STG.E.64", 14, 8.5, 48, 30)]
    sass = ('<div class="g g-sass"><div class="ed2"><div class="tb"><i></i><span class="f1">rmsnorm.ptx</span><span class="f2">rmsnorm.sass</span><em>steered</em></div><div class="body">' + "".join(
        f'<span class="n">{i + 1}</span><div class="row"><span class="p">{ptx(line)}</span><span class="op"><b class="a">{a}</b><b class="b">{b}</b></span><span class="bar"><i style="--w0:{w0}%;--w1:{w1}%"></i></span><span class="pct"><b class="a">{p0:g}%</b><b class="b">{p1:g}%</b></span></div>'
        for i, (line, a, b, p0, p1, w0, w1) in enumerate(rows)) + "</div></div></div>")
    # application: a prompt and a streamed answer
    words = "Supplier may raise prices yearly, capped at 4%…".split()
    app = ('<div class="g g-app"><div class="chat"><div class="u">Summarise this contract.</div><div class="a">'
           + " ".join(f'<span style="animation-delay:{.6 + k * .16:.2f}s">{w}</span>' for k, w in enumerate(words)) + ' <i class="caret"></i></div></div></div>')
    # silicon: a GPU board with HBM stacks and a busy die
    hbm = "".join(f'<rect class="hbm" x="{x}" y="{y}" width="12" height="11" rx="1" style="animation-delay:{(i*.35):.2f}s"/>' for i, (x, y) in enumerate([(38, 22), (38, 36), (38, 50), (100, 22), (100, 36), (100, 50)]))
    cores = "".join(f'<rect class="core" x="{62 + c * 6}" y="{27 + r * 7}" width="4" height="5" style="animation-delay:{((c * 3 + r * 5) % 11) * .17:.2f}s"/>' for r in range(5) for c in range(4))
    fingers = "".join(f'<rect x="{40 + i * 5}" y="74" width="3" height="8"/>' for i in range(14))
    sil = (f'<svg class="g g-gpu" viewBox="0 0 150 92" aria-hidden="true"><rect class="bracket" x="5" y="6" width="7" height="74" rx="1.5"/>'
           f'<rect class="board" x="12" y="8" width="132" height="66" rx="4"/><g class="fingers">{fingers}</g>{hbm}'
           f'<rect class="die" x="58" y="22" width="34" height="40" rx="2"/><g class="cores">{cores}</g>'
           '<text x="78" y="70">H100 · 80 GB HBM3</text></svg>')
    layers = [
        ("", "Application", app, "Capture the real traffic shape, the eval set and the SLO we optimise to.", "cap",
         "Where the number comes from. A support assistant needs its first token under 400 ms for every user; a document pipeline wants the most tokens per dollar; a robot needs 20 Hz on a 15 W board. The target is set here, and every layer below is judged against it.",
         ["Support assistant: p99 TTFT < 400 ms, 30 tok/s per user", "Batch pipeline: cost per million tokens", "Robot VLA policy: 20 Hz on Jetson Orin"]),
        ("01", "Serving engine", engine, "Configure the engine: quantised weights and KV cache, TP/PP, scheduler flags.", "mid",
         "Which engine, which dtype, which parallelism, which flags. The same model on the same GPUs can differ by 3× between a default launch and a tuned one, before anyone writes a line of CUDA.",
         ["vLLM: --kv-cache-dtype fp8 --enable-prefix-caching", "TensorRT-LLM: fp8 engine build, paged KV", "SGLang: RadixAttention, chunked prefill"]),
        ("02", "Scheduling", "".join(sch), "Tune how requests share the GPU: batching, chunked prefill, prefix caching.", "mid",
         "How requests share a GPU. Continuous batching keeps the GPU full, chunked prefill stops long prompts from stalling decode, prefix caching reuses shared system prompts, and KV placement decides how many sequences fit at once.",
         ["Prefix cache: 71% hit rate on a shared system prompt", "Chunked prefill: p99 TTFT 612 → 275 ms", "fp8 KV cache: 2× concurrent sequences"]),
        ("03", "Compile and fuse", graph, "Fuse ops, remove copies, capture CUDA graphs, compile the decode step.", "mid",
         "Fewer kernel launches, fewer bytes moved. Fuse q, k and v into one GEMM, fold the norm and quantisation into the GEMM prologue, capture the decode step in a CUDA graph, let a small draft model propose tokens for the big one to verify.",
         ["QKV fusion: 3 GEMMs → 1", "CUDA graphs: launch overhead −80% at batch 1", "EAGLE-3 draft: 2.1× decode on your traffic"]),
        ("04", "Kernels", kern, "Profile, then rewrite the hot kernels for your shapes; verify vs the stock path.", "mid",
         "When the stock path leaves throughput on the table, write the kernel for your shapes: tile sizes, pipelining depth, the right instructions for the GPU generation. Checked numerically against the reference before it ships.",
         ["Triton fused rmsnorm+quant: 41.2 → 18.4 µs", "CUTLASS wgmma GEMM for an odd head dim", "Paged-attention decode kernel for 128k contexts"]),
        ("05", "SASS verification", sass, "Inspect the SASS ptxas emits: registers, spills, stalls. Steer the compiler.", "mid",
         "ptxas writes the SASS; we read it. Register count and spills, occupancy per SM, shared-memory bank conflicts and stall reasons. Then steer the compiler with inline PTX, launch bounds, unroll pragmas and flags until the code the GPU runs is what we meant.",
         ["LDG.E.U16 ×8 → LDG.E.128 ×1: vectorised loads", "BAR.SYNC → SHFL.BFLY: warp-level reduce", "72 registers, 0 spills, occupancy 62%"]),
        ("", "Silicon", sil, "Measure every candidate on the target GPU and report what it did.", "cap",
         "Every number is measured on the target, never estimated from a spec sheet. H100 and B200 in the data centre, L40S and consumer cards for cheaper decode, Jetson Orin and Thor at the edge, Apple and Qualcomm on devices.",
         ["H100 SXM 80 GB: 6,120 tok/s on Qwen3-32B", "Jetson Orin Nano 8 GB: 28 tok/s in 3.1 GB", "B200: 9.7 µs for the same kernel"]),
    ]
    lk = '<span class="lk" aria-hidden="true"><i></i></span>'
    def card(k, num, name, g, d, cls, *_):
        return f'<div class="layer {cls}"><div class="inner">{g}<h3>{f"<i>{num}</i>" if num else ""}{name}</h3><p>{d}</p></div></div>'
    mids = [(k, l) for k, l in enumerate(layers) if l[4] == "mid"]
    box = ('<div class="layers-box"><span class="lbl">VitalOps works here</span>'
           + ''.join((lk.replace('class="lk"', f'class="lk" style="--d:{.25 + j * .12:.2f}s"') if j else '') + card(k, *l).replace('<div class="layer mid"', f'<div class="layer mid" style="--d:{.25 + j * .12:.2f}s"', 1) for j, (k, l) in enumerate(mids)) + '</div>')
    return '<div class="lad" id="lad">' + card(0, *layers[0]) + lk + box + lk.replace('class="lk"', 'class="lk lk2"') + card(6, *layers[6]) + '</div>'

def carousel(slides, first_title):
    n = len(slides)
    return (f'<div class="carousel" tabindex="0" role="group" aria-roledescription="carousel" aria-label="Product screens; use the left and right arrow keys to move between them"><div class="car-clip"><div class="car">{faces(slides)}</div></div>'
            f'<div class="car-bar"><span class="car-title">{first_title}</span><span class="car-count">01 / {n:02d}</span></div></div>')

def flow_html():
    """Under the Kernels window: the kernel's code transpiles in place (Python → CUDA → PTX → SASS), then a CPU
    interprets the SASS while emulating an H100, and reports the real CPU wall time beside the predicted GPU time."""
    # tiny per-language tokenizers: (regex, token class); first alternative wins at a position
    RULES = {
        "py": [(r"#.*", "cm"), (r"@[\w.]+", "dec"), (r"\"[^\"]*\"|'[^']*'", "str"),
               (r"\b(def|return|for|in|if|else|import|from|with|as|lambda|and|or|not|None|True|False)\b", "kw"),
               (r"\b\d+(?:\.\d+)?(?:e-?\d+)?\b", "num"), (r"\b[A-Za-z_]\w*(?=\()", "fn")],
        "cu": [(r"//.*", "cm"), (r"\b(__global__|__device__|__shared__|const|for|if|else|return)\b", "kw"),
               (r"\b(void|int|float|bf16|fp8|half|bool|unsigned)\b", "ty"),
               (r"\b\d+(?:\.\d*)?f?\b", "num"), (r"\b[A-Za-z_]\w*(?=\()", "fn")],
        "ptx": [(r"//.*", "cm"), (r"^\.[a-z]+", "kw"), (r"^[a-z]+", "op"), (r"\.[a-z0-9]+", "mod"),
                (r"%[a-z]+\d*", "reg"), (r"(?<![\w.%])-?\d+\b", "num"), (r"\b[A-Za-z_]\w*(?=\()", "fn")],
        "sass": [(r"/\*[0-9a-f]+\*/", "cm"), (r"(?<=\*/ )[A-Z][A-Z0-9_]*", "op"), (r"\.[A-Z0-9_]+\b", "mod"),
                 (r"!?\bPT\b", "pred"), (r"\bR\d+\b|\bRZ\b", "reg"), (r"\b0x[0-9a-f]+\b", "num")],
    }
    PATS = {k: re.compile("|".join(f"(?P<{c}>{r})" for r, c in v), re.M) for k, v in RULES.items()}
    def hl(lang, line):
        out, pos = [], 0
        for m in PATS[lang].finditer(line):
            out.append(H.escape(line[pos:m.start()]))
            out.append(f'<b class="t-{m.lastgroup}">{H.escape(m.group())}</b>')
            pos = m.end()
        out.append(H.escape(line[pos:]))
        return "".join(out)
    def code(lang, lines):
        return "".join(f'<span class="ln" style="--i:{k}">{hl(lang, l)}</span>' for k, l in enumerate(lines))
    py = ["@torch.compile", "def rmsnorm_q(x, w, eps=1e-6):", "    v = x.float().pow(2).mean(-1, keepdim=True)", "    y = x * torch.rsqrt(v + eps) * w", "    s = y.abs().amax(-1, keepdim=True) / 448.0", "    return (y / s).to(torch.float8_e4m3fn), s"]
    cu = ["__global__ void rmsnorm_q(const bf16* x,", "    const bf16* w, fp8* out, int n, float eps) {", "  float ss = 0.f;", "  for (int i = lane; i < n / 8; i += 32)", "    ss += dot8(ld128(x + i));", "  ss = warp_reduce_sum(ss);", "  float r = rsqrtf(ss / n + eps);"]
    ptx = [".visible .entry rmsnorm_q(.param .u64 x, ...)", "ld.global.v4.u32 {%r4, %r5, %r6, %r7}, [%rd2];", "fma.rn.f32 %f12, %f5, %f5, %f12;", "shfl.sync.bfly.b32 %f13, %f12, 16, 31, -1;", "rsqrt.approx.f32 %f14, %f13;", "max.f32 %f15, %f15, %f16;", "st.global.v2.b32 [%rd6], {%r20, %r21};"]
    sass = ["/*0120*/ LDG.E.128 R4, [R2.64]", "/*0150*/ FFMA R12, R5, R5, R12", "/*0180*/ SHFL.BFLY PT, R13, R12, 0x10, 0x1f", "/*01b0*/ MUFU.RSQ R14, R13", "/*0210*/ FMNMX R15, R15, R16, !PT", "/*0240*/ F2FP.E4M3.PACK_AB R20, R19, R18", "/*0270*/ STG.E.64 [R6.64], R20"]
    stages = [("rmsnorm.py", py, .3, 2.5), ("rmsnorm.cu", cu, 2.7, 4.7), ("rmsnorm.ptx", ptx, 4.9, 6.7), ("rmsnorm.sass", sass, 6.9, 99)]
    panes = "".join(f'<pre class="stage" style="--a:{a}s;--b:{b}s">{"<i class=\"pc\" style=\"--t:7.2s\"></i>" if name.endswith(".sass") else ""}{code(name.rsplit(".", 1)[1], lines)}</pre>' for name, lines, a, b in stages)
    tabs = "".join(f'<span class="tab" style="--a:{a}s;--b:{b}s">{name}</span>' for name, lines, a, b in stages)
    steps = ('<span class="xstep" style="--a:2.3s;--b:3.1s">PyTorch dispatches the kernel →</span>'
             '<span class="xstep" style="--a:4.5s;--b:5.3s">nvcc → PTX →</span>'
             '<span class="xstep" style="--a:6.5s;--b:7.3s">ptxas → SASS →</span>')
    cores = "".join(f'<i style="--t:{7.3 + k * .13:.2f}s"></i>' for k in range(16))
    cpu = ('<div class="cpu" aria-hidden="true"><div class="cph"><b>CPU · emulating an H100</b><span class="st0" style="--a:0s;--b:7.0s">waiting for SASS</span><span class="st1" style="--a:7.0s;--b:10.4s">interpreting SASS on 16 threads</span><span class="st2" style="--a:10.4s;--b:99s">done</span></div>'
           f'<div class="cb"><div class="cores">{cores}</div>'
           '<div class="meters"><div class="m"><small>warps</small><b class="ctr w"></b><i>/ 212</i></div><div class="m"><small>instructions</small><b class="ctr k"></b><i>k</i></div><div class="m"><small>wall time on this CPU</small><b class="ctr s"></b><i>s</i></div></div></div>'
           '<div class="bar"><em></em></div>'
           '<div class="out" style="--a:10.5s;--b:99s"><div><small>predicted on H100</small><b>18.4 µs</b></div><div><small>stock kernel</small><b class="mu">41.2 µs · 2.2× faster</b></div></div><div class="trade" style="--a:10.9s;--b:99s">The trade: 38 s of CPU for 18 µs of GPU, per candidate. Sim ranks; a real GPU verifies.</div></div>')
    return (f'<div class="flow" role="img" aria-label="The kernel transpiles from Python to CUDA to PTX to SASS; a CPU interprets the SASS while emulating an H100 and reports the real CPU wall time beside the predicted GPU time">'
            f'<div class="cw" aria-hidden="true"><div class="cwt">{tabs}{steps}</div><div class="cwb">{panes}</div></div>{cpu}</div>')
FLOW = flow_html()

def faces(slides):
    return "".join(sl.replace('<div class="frame"', '<div class="frame"' + ('' if k == 0 else ' data-off'), 1) for k, sl in enumerate(slides))
_step_i = [0]
def tour_step(n, id_, title, para, fig, works, changes, label="What changes"):
    ch = "".join(f"<li>{ic(c[0])}<span>{c[1]}</span></li>" if isinstance(c, tuple) else f"<li><span>{c}</span></li>" for c in changes)
    flip = _step_i[0] % 2 == 0; _step_i[0] += 1   # the hero has copy left; step 01 puts the screen left, then alternate
    return f"""
    <article class="step{" flip" if flip else ""}" id="{id_}">
      <div class="wrap bleed{" l" if flip else ""}"><div class="split">
        <div class="step-copy"><div class="step-no">{n}</div><h3>{title}</h3><p>{para}</p><h4>{label}</h4><ul class="chg">{ch}</ul><h4>Works with</h4><p class="with">{works}</p></div>
        <div class="step-shot">{fig}</div>
      </div></div>
    </article>"""

STEPS = [
 tour_step("01 · Optimize","w-opt","Point it at the model, the hardware and the number you need",
   "Give the optimizer a model, a GPU target, an SLO and your eval set. The agent searches the serving engine's knobs, quantisation, parallelism, scheduling, speculative decoding and custom kernels, ranks candidates in the built-in simulator, verifies the best on real GPUs and ships a reproducible bundle. Every candidate is held to your accuracy floor; kernels are checked at PTX and SASS level and numerically verified.",
   SCREEN_OPT,"vLLM, SGLang, TensorRT-LLM, llama.cpp, Hugging Face Transformers; lm-eval or your own evals. Targets: tokens/s, TTFT, TPOT, p99, memory, cost per million tokens.",
   [("timer","Weeks of trial and error become one run with a report."),("badge-check","Every speed-up is tied to an accuracy number."),("history","The result is a reproducible bundle anyone on the team can rerun.")]),
 tour_step("02 · Optimize · Kernels","w-sim","Rank kernels without a GPU attached",
   "Optimize's kernel page runs your candidates on real GPUs when you have them. When you don't, it runs them on Sim: an optional GPU simulator. A replacement <code>libcuda.so</code> takes the same binary, loads the cubin into a SASS interpreter and executes the launches on CPU threads under a timing model, so you get a predicted time per target, a per-instruction stall breakdown and a ranking of candidates on a laptop or in CI. Three fidelities: static in milliseconds, sampled in seconds, cycle-level in hours. Rank correlation against real hardware is reported on every run, and the best candidates are verified on a real GPU before anything ships.",
   SCREEN_SIM + FLOW,"CUDA C++, Triton, CUTLASS, PyTorch through a driver shim; KernelBench and TritonBench; GitHub Actions. Targets: H100, H200, B200, L40S, RTX 4090 and 5090, Jetson Orin and Thor.",
   [("cpu","Kernel work no longer waits for a GPU slot."),("bot","Agents rank thousands of variants for the cost of CPU time."),("git-branch","A performance regression fails CI before it reaches hardware.")], label="What it unlocks"),
 tour_step("03 · Serve","w-serve","Ship the bundle as a canary, promote when the numbers hold",
   "An OpenAI-compatible server built around the bundles Optimize produces: multi-model pools, continuous batching, prefix caching, chunked prefill, speculative decoding, structured output, and canary rollouts with instant rollback. Runs in your cloud account or data centre; air-gapped supported.",
   SCREEN_SERVE,"OpenAI SDKs, LangChain and LlamaIndex, Kubernetes, NVIDIA and AMD GPUs. <code>/v1/chat/completions</code>, <code>/v1/embeddings</code>, tool calls, JSON-schema and grammar-constrained decoding.",
   [("rocket","The optimised configuration is the one actually in production."),("rotate-ccw","Rollouts you can reverse in seconds."),("network","One endpoint for every model you run.")], label="What you get"),
 tour_step("04 · Serve · Monitoring","w-mon","Watch it in production, in the numbers that decide your bill",
   "Generic APM shows CPU and memory. Serve's monitoring shows TTFT, TPOT, tokens per second, KV-cache hit rate, queue depth, cost per million tokens, and whether model quality is drifting, per model, pool, tenant and prompt template. When something moves, the fix is handed back to Optimize. It also attaches to an existing vLLM, SGLang or TensorRT-LLM deployment.",
   SCREEN_MON,"Prometheus, OpenTelemetry, Grafana, PagerDuty and Slack; existing vLLM, SGLang and TensorRT-LLM deployments.",
   [("chart-line","You see the cost of a prompt change the hour it ships."),("shield-check","Evals catch quality regressions before they reach users."),("bell-ring","Every alert arrives with a proposed fix.")], label="What you catch"),
 tour_step("05 · Edge","w-edge","Fit it on the device, and train it there",
   "Each device gets the largest model that meets your accuracy floor inside its memory and latency budget. A Jetson or a flagship phone takes a 3B vision-language model once the weights, KV cache and encoder are quantised and a couple of layers pruned; a Raspberry Pi gets a 0.5 to 1.5B model and the same accuracy guard. Where the data can't leave the device, fine-tuning runs on it: QLoRA inside the memory budget, a live loss curve, and the adapter pushed to every device on the same base.",
   SCREEN_EDGE,"NVIDIA Jetson, iPhone and Apple silicon, Pixel and Android NPUs, Qualcomm Snapdragon and Dragonwing, Raspberry Pi 5, x86 CPUs. Exports to GGUF, MLX, ExecuTorch, CoreML, QNN and TensorRT.",
   [("smartphone","A model that didn't fit now runs on a phone, a Pi or a Jetson."),("badge-check","Accuracy is measured after every step."),("lock","Fine-tuning runs on the device, so the data never leaves it.")], label="What becomes possible"),
 tour_step("06 · Fleet","w-fleet","Run N agents on M GPUs, on your premises",
   "Agent workloads don't look like chat: long shared prefixes, bursts of parallel sub-agents, and long idle gaps while tools run. Fleet schedules a swarm of agents across your GPUs with KV-aware routing, prefix sharing between agents, and preemption while an agent waits on a tool. Scaling from 8 agents to 96 is one command, and the capacity check tells you where the SLO breaks.",
   SCREEN_FLEET,"Claude Agent SDK, OpenAI Agents, LangGraph, or your own loop; Kubernetes and Slurm; air-gapped by default.",
   [("layers","More agents per GPU, because the KV cache stops being thrown away."),("sliders-horizontal","Scaling means changing one number."),("users","A straight answer to how many agents you can run.")], label="What it buys you"),
]

PLAY = r"""
<script>
/* Screen playback: each screen replays a scripted session from data attributes.
   [data-step] elements appear in order (an element with data-before shows that
   earlier value first), .count numbers count up, .grow bars grow, lines draw,
   then a cursor presses the primary button and a toast confirms. The finished
   state is the static HTML, so no-JS and reduced-motion visitors see the result. */
(function(){
  if(!('IntersectionObserver' in window))return;
  var reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  var CURSOR='<svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><path d="M3 2l12.5 7.2-5.6 1.3-2.7 5.3z" fill="#0f172a" stroke="#ffffff" stroke-width="1.4" stroke-linejoin="round"/></svg>';
  var runs={};
  function Stop(){}
  function sleep(ms,tok){return new Promise(function(res,rej){setTimeout(function(){tok.x?rej(new Stop()):res();},ms);});}
  function $$(root,sel){return [].slice.call(root.querySelectorAll(sel));}
  function counter(el,dur,tok){
    var m=el.textContent.match(/^([^\d]*)([\d,]*\.?\d+)(.*)$/);
    if(!m)return;
    var pre=m[1],num=m[2],suf=m[3],commas=num.indexOf(',')>=0,dec=(num.split('.')[1]||'').length,target=parseFloat(num.replace(/,/g,'')),t0=null;
    function fmt(v){var s=v.toFixed(dec);if(commas){var p=s.split('.');p[0]=p[0].replace(/\B(?=(\d{3})+(?!\d))/g,',');s=p.join('.');}return pre+s+suf;}
    el.textContent=fmt(0);
    (function step(t){if(tok.x)return;if(t0===null)t0=t;var k=Math.min(1,(t-t0)/dur),e=1-Math.pow(1-k,3);el.textContent=fmt(target*e);if(k<1)requestAnimationFrame(step);else el.textContent=fmt(target);})(performance.now());
  }
  function zeroGrow(g){if(g.style.width){g._w=g.style.width;g.style.width='0%';}if(g.style.height){g._h=g.style.height;g.style.height='0%';}}
  function doGrow(g){if(g._w!==undefined)g.style.width=g._w;if(g._h!==undefined)g.style.height=g._h;}
  function place(cur,x,y,instant){if(instant){cur.style.transition='none';cur.style.transform='translate('+x+'px,'+y+'px)';cur.offsetWidth;cur.style.transition='';}else cur.style.transform='translate('+x+'px,'+y+'px)';}
  async function play(mock,tok){
    while(!tok.x){
      mock.dispatchEvent(new CustomEvent('vo:loop'));
      mock.innerHTML=mock._orig;mock.classList.remove('accepted');
      var dur=+mock.getAttribute('data-dur');if(dur){await sleep(dur,tok);mock.dispatchEvent(new CustomEvent('vo:done'));continue;}
      $$(mock,'[data-before]').forEach(function(e){e._final=e.innerHTML;e.innerHTML=e.getAttribute('data-before');});
      var stepped=$$(mock,'[data-step]'),steps={};
      stepped.forEach(function(e){var s=+e.getAttribute('data-step');(steps[s]=steps[s]||[]).push(e);if(e.getAttribute('data-before')===null)e.setAttribute('data-a','0');});
      var paths=$$(mock,'.grow-path');paths.forEach(function(p){var L=p.getTotalLength();p.style.strokeDasharray=L;p.style.strokeDashoffset=L;p.style.transition='none';});
      $$(mock,'.grow-area').forEach(function(a){a.style.opacity='0';});
      $$(mock,'.grow').forEach(zeroGrow);
      $$(mock,'.count').forEach(function(c){if(!c.closest('[data-step]'))counter(c,1500,tok);});
      await sleep(450,tok);
      $$(mock,'.grow').forEach(function(g){if(!g.closest('[data-step]'))doGrow(g);});
      paths.forEach(function(p){p.offsetWidth;p.style.transition='stroke-dashoffset 2.2s ease';p.style.strokeDashoffset='0';});
      $$(mock,'.grow-area').forEach(function(a){a.style.transition='opacity 1.2s ease .8s';a.style.opacity='';});
      var keys=Object.keys(steps).map(Number).sort(function(a,b){return a-b;});
      for(var i=0;i<keys.length;i++){
        var group=steps[keys[i]],wait=+(group[0].getAttribute('data-wait')||560);
        await sleep(wait,tok);
        group.forEach(function(e){
          if(e.getAttribute('data-before')!==null){e.innerHTML=e._final;}else{e.setAttribute('data-a','1');}
          if(e.classList.contains('grow'))doGrow(e);$$(e,'.grow').forEach(doGrow);
          if(e.classList.contains('count'))counter(e,900,tok);$$(e,'.count').forEach(function(c){counter(c,900,tok);});
        });
      }
      var btn=mock.querySelector('.mb.pri'),done=mock.getAttribute('data-done'),toastTxt=mock.getAttribute('data-toast'),toast=null;
      if(btn&&done){
        await sleep(600,tok);
        var cur=document.createElement('div');cur.className='vo-cursor';cur.innerHTML=CURSOR;mock.appendChild(cur);
        var mr=mock.getBoundingClientRect(),sc=(mr.width/mock.offsetWidth)||1;
        place(cur,mock.offsetWidth*.9,mock.offsetHeight*.92,true);cur.classList.add('on');
        await sleep(60,tok);
        var br=btn.getBoundingClientRect(),bx=(br.left-mr.left+br.width*.55)/sc,by=(br.top-mr.top+br.height*.55)/sc;
        place(cur,bx,by,false);
        await sleep(1050,tok);
        var rip=document.createElement('div');rip.className='vo-ripple';rip.style.left=bx+'px';rip.style.top=by+'px';mock.appendChild(rip);
        btn.classList.add('pressed');await sleep(140,tok);
        btn.classList.remove('pressed');
        if(mock.hasAttribute('data-accept')){mock.classList.add('accepted');}else{btn.classList.add('done');btn.textContent=done;}
        await sleep(350,tok);cur.classList.remove('on');
      } else { await sleep(900,tok); }
      $$(mock,'[data-before]:not([data-step])').forEach(function(e){e.innerHTML=e._final;});
      if(toastTxt){toast=document.createElement('div');toast.className='vo-toast';toast.innerHTML='<b>✓</b><span>'+toastTxt+' · recorded</span>';mock.appendChild(toast);toast.offsetWidth;toast.classList.add('on');}
      await sleep(3600,tok);
      if(toast)toast.classList.remove('on');
      await sleep(500,tok);
      mock.dispatchEvent(new CustomEvent('vo:done'));
    }
  }
  function start(mock){var id=mock._id;if(runs[id])return;var tok={x:false};runs[id]=tok;play(mock,tok).catch(function(e){if(!(e instanceof Stop))throw e;});}
  function stop(mock){var id=mock._id,tok=runs[id];if(!tok)return;tok.x=true;delete runs[id];mock.innerHTML=mock._orig;mock.classList.remove('accepted');}
  var mocks=[].slice.call(document.querySelectorAll('.mock'));
  mocks.forEach(function(m,i){m._orig=m.innerHTML;m._id='m'+i;m._play=function(){if(!reduce)start(m);};m._stop=function(){stop(m);};m.addEventListener('dragstart',function(e){e.preventDefault();});});
  if(reduce)return;
  var io=new IntersectionObserver(function(entries){entries.forEach(function(en){if(en.target.hasAttribute('data-rec'))return;if(en.isIntersecting&&en.intersectionRatio>=.3&&!en.target.closest('[data-off]'))start(en.target);else stop(en.target);});},{threshold:[0,.3]});
  mocks.forEach(function(m){io.observe(m);});
})();
</script>"""

SHOW_COMPANY = False  # hidden for now; flip to True to bring the team and open-source section back
COMPANY = f"""<section class="team" id="company"><div class="wrap">
  <span class="k">Company</span>
  <h2 style="margin-top:12px">Built by people who've been inside the frameworks</h2>
  <p class="lede" style="margin-top:12px">We've contributed to the libraries this industry runs on and spent the last years making models run faster for clients. The products are those years, written down.</p>
  <div class="people">
    <div class="person"><img loading="lazy" decoding="async" src="assets/fariz_profile.png" alt="Fariz Rahman"><div><h3>Fariz Rahman</h3><i>Co-founder</i><p>Machine learning engineer and long-time core contributor to Keras. Builds the runtimes, sandboxes and tooling behind VitalOps.</p><small><a href="https://github.com/farizrahman4u" target="_blank" rel="noopener">GitHub</a> · <a href="https://linkedin.com/in/fariz-rahman" target="_blank" rel="noopener">LinkedIn</a></small></div></div>
    <div class="person"><img loading="lazy" decoding="async" src="assets/abhijith.jpeg" alt="Abhijith Neil Abraham"><div><h3>Abhijith Neil Abraham</h3><i>Co-founder</i><p>Engineer and AI researcher, creator of TableQA, published author and speaker. Leads inference optimisation work and wrote our <a href="https://medium.com/@abhijithneilabraham/a-simple-practical-mental-model-for-llm-inference-optimization-ca3ea989da25" target="_blank" rel="noopener">mental model for LLM inference optimisation</a>.</p><small><a href="https://github.com/abhijithneilabraham" target="_blank" rel="noopener">GitHub</a> · <a href="https://www.linkedin.com/in/abhijith-neil-abraham-765165141/" target="_blank" rel="noopener">LinkedIn</a></small></div></div>
  </div>
  <div class="oss">
    <a href="https://github.com/vitalops/temenos" target="_blank" rel="noopener"><b>temenos</b><span>Sandboxed execution runtime for AI agents and untrusted code.</span></a>
    <a href="https://github.com/vitalops/datatune" target="_blank" rel="noopener"><b>datatune</b><span>LLM transformations over datasets of any size. Peer-reviewed at DATA 2026.</span></a>
    <a href="https://github.com/vitalops/coherence" target="_blank" rel="noopener"><b>coherence</b><span>Readable, versionable memory for long-running agents.</span></a>
    <a href="https://github.com/vitalops/opendesk" target="_blank" rel="noopener"><b>opendesk</b><span>Desktop automation for software with no API.</span></a>
  </div>
</div></section>"""

HTML = f"""<!DOCTYPE html>
<html lang="en" style="color-scheme:light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light">
<title>VitalOps · Inference optimisation, serving, edge and GPU sim</title>
<meta name="description" content="Inference optimisation, model serving, edge deployment and GPU simulation: VitalOps makes the model you already trust fast, small and cheap enough to ship.">
<link rel="canonical" href="https://vitalops.ai/">
<meta name="theme-color" content="#f5f6fa">
<link rel="icon" type="image/svg+xml" href="assets/vo-mark.svg">
<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="assets/icon-192.png">
<link rel="apple-touch-icon" sizes="180x180" href="assets/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="VitalOps">
<meta property="og:title" content="VitalOps · inference optimisation, serving, edge and GPU sim">
<meta property="og:description" content="The model you already trust, made fast enough, small enough and cheap enough to ship: an agentic inference optimizer with a CPU-side GPU simulator, a model server with inference-native monitoring, edge deployment with on-device training, and agent-fleet scheduling.">
<meta property="og:url" content="https://vitalops.ai/">
<meta property="og:image" content="https://vitalops.ai/assets/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@vitalopsai">
<meta name="twitter:image" content="https://vitalops.ai/assets/og.png">
__JSONLD__
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
  <mask id="ptm"><path fill="white" d="M50,8 C57,8 63,11 67,16 L85,46 C89,52 89,59 86,65 C83,71 77,74 71,74 L29,74 C23,74 17,71 14,65 C11,59 11,52 15,46 L33,16 C37,11 43,8 50,8 Z"/><circle cx="50" cy="46" r="20" fill="black"/></mask>
  <symbol id="vo-logo" viewBox="-8 -8 116 116"><g transform="rotate(180 50 50)"><rect width="100" height="100" fill="currentColor" mask="url(#ptm)"/></g></symbol>
</defs></svg>

<header class="top"><a class="skip" href="#main">Skip to content</a><div class="wrap top-in">
  <a class="logo" href="#top" aria-label="VitalOps home"><svg aria-hidden="true"><use href="#vo-logo"/></svg>VitalOps</a>
  <button class="menu-btn" id="navToggle" aria-expanded="false" aria-controls="navLinks">Menu</button>
  <ul class="topnav" id="navLinks">
    <li><a href="#tour">Walkthrough</a></li><li><a href="#services">Services</a></li><li><a href="#stack">Stack</a></li>{'<li><a href="#company">Company</a></li>' if SHOW_COMPANY else ""}
    <li class="navcta"><a class="btn btn-p" href="https://calendly.com/abhijith-vitalops/30min" target="_blank" rel="noopener">Book an inference review</a></li>
  </ul>
</div></header>

<main id="main" tabindex="-1">
<section class="hero"><div class="wrap hero-grid">
  <div class="hero-copy">
    <span class="k">Inference optimisation · serving · edge · GPU sim</span>
    <h1>The model is right. Now make it <em>fast, small and cheap</em> enough to ship.</h1>
    <p class="lede">You've found the LLM or VLM that answers correctly. Getting it to the tokens per second you need, into the memory you have, or onto the device in the field is a different job. That's ours: an agentic optimizer that searches the stack from the serving engine down and verifies at the SASS, a server that runs the result, and the engineers behind both.</p>
    <div class="hero-cta"><a class="btn btn-p" href="https://calendly.com/abhijith-vitalops/30min" target="_blank" rel="noopener">Book an inference review</a><a class="btn btn-s" href="#tour">Take the walkthrough</a></div>
    <p class="hero-note">Open-weight LLMs and VLMs · H100, B200, Jetson, Apple, Qualcomm · accuracy floor enforced · runs in your environment</p>
  </div>
  <div class="hero-shot">
    {carousel([SCREEN_HERO, SCREEN_IDE], "Optimize · the runs list · a run ships to production as the clip plays")}
  </div>
</div></section>

<div class="facts"><div class="wrap">
  <div class="facts-row">
    <div class="fact"><b>3.3×</b><span>throughput on the sample run · 1,840 → 6,120 tok/s</span></div>
    <div class="fact"><b>−55%</b><span>time to first token at p99 · 612 → 275 ms, under the 400 ms SLO</span></div>
    <div class="fact"><b>84.1%</b><span>accuracy held above the 83.5 floor · int4 rejected by the eval</span></div>
    <div class="fact"><b>−69%</b><span>cost per million tokens · $1.02 → $0.31</span></div>
  </div>
  <p class="facts-note">What one Optimize run produced for Qwen3-32B on two H100s against a support-QA eval, in 2 h 14 m of search.</p>
</div></div>

<section class="ladder" aria-labelledby="h-ladder"><div class="wrap">
  <h2 class="sr-only" id="h-ladder">Where the work happens</h2><span class="k" aria-hidden="true">Where the work happens</span>
  {layers_html()}
  <p class="lad-out">Most teams stop at the first layer. We work all five and verify at the bottom, in the SASS the GPU actually executes.</p>
</div></section>

<section class="tour" id="tour" aria-labelledby="h-tour">
  <div class="wrap"><h2 class="sr-only" id="h-tour">Walkthrough</h2><span class="k tour-k" aria-hidden="true">Walkthrough</span></div>
  <div class="tour-bar"><nav class="wrap" aria-label="Walkthrough steps">
    <a href="#w-opt" class="on"><i>01</i>Optimize</a><a href="#w-sim"><i>02</i>Kernels</a><a href="#w-serve"><i>03</i>Serve</a><a href="#w-mon"><i>04</i>Monitoring</a><a href="#w-edge"><i>05</i>Edge</a><a href="#w-fleet"><i>06</i>Fleet</a>
  </nav></div>
  {''.join(STEPS)}
</section>

<span id="usecases"></span>
<section class="svc" id="services">
  <div class="svc-bg" aria-hidden="true"></div>
  <div class="wrap">
  <div class="svc-head"><span class="k">Services</span><h2>Engineers on your problem, fixed scope</h2><p class="lede">The products came out of this work. We still do it, fixed-scope, for teams who want the result delivered.</p></div>
  <div class="svc-grid">
    {svc("timer","Inference optimisation sprint","Model, hardware and SLO in; verified configuration and report out. Two weeks, fixed fee.","vLLM · SGLang · TensorRT-LLM · FP8 · INT4 · NVFP4 · speculative decoding · prefix caching")}
    {svc("cpu","Custom kernels","Fused and specialised kernels where the stock path leaves throughput on the table, tuned down to the SASS.","Triton · CUDA · CUTLASS · wgmma · TMA · cp.async · Hopper · Blackwell · Ada")}
    {svc("zap","Speculative decoding","Draft models trained on your traffic, so the speed-up holds on your prompts.","EAGLE-3 · Medusa · n-gram and prompt-lookup drafts · acceptance tuning")}
    {svc("boxes","Quantisation and distillation","Smaller models that keep the accuracy you signed off on, with the eval to prove it.","AWQ · GPTQ · SmoothQuant · KV-cache quantisation · distillation · pruning")}
    {svc("smartphone","Edge deployment and on-device training","From a model that doesn't fit to one that runs, updates and fine-tunes in the field.","Jetson · Apple silicon · Qualcomm · Raspberry Pi · ExecuTorch · GGUF · MLX · QLoRA on device")}
    {svc("bot","Serving for agent workloads","Design and tuning of the serving layer for long prefixes, sub-agent bursts and tool-call gaps.","KV-aware routing · prefix sharing · capacity planning")}
    {svc("bar-chart-3","Benchmarking and capacity planning","Tokens per second per dollar across GPUs and clouds, measured on your workload.","H100 · H200 · B200 · MI300X · L40S · consumer cards · buy-versus-rent models")}
    {svc("trending-up","Training throughput","When the bottleneck is the training run: data loading, parallelism, kernels and memory.","FSDP · DeepSpeed · Megatron · torch.compile · fused optimisers · MFU audits")}
  </div>
</div></section>

<section class="engage" id="engage"><div class="wrap">
  <div class="eng-grid">
    <div class="eng-photo" aria-hidden="true"></div>
    <div class="eng-steps">
      <span class="k">How we work together</span>
      <h2>Start small, prove it on your hardware, then run it</h2>
      <ol class="steps">
        <li><div class="sp-i">{ic("calendar")}</div><div><small>Start here</small><h3>Inference review <i>Free · 30 minutes</i></h3><p>Bring the model, the hardware you have or plan to buy, and the number you need to hit. You leave with an honest estimate of what's achievable and how.</p><a class="btn btn-s" href="https://calendly.com/abhijith-vitalops/30min" target="_blank" rel="noopener">Book the review</a></div></li>
        <li class="hl"><div class="sp-i">{ic("flask-conical")}</div><div><small>Prove it</small><h3>Optimisation sprint <i>Fixed fee · 2 weeks</i></h3><p>We run Optimize and our engineers on your model and hardware. You get the verified configuration, the kernels, the eval numbers and a report.</p><b class="guar">{ic("shield-check")}If we don't beat your baseline, you don't pay.</b></div></li>
        <li><div class="sp-i">{ic("server")}</div><div><small>Run it</small><h3>Managed inference <i>Monthly</i></h3><p>Serve with its monitoring, and continuous re-optimisation as your models and traffic change, in your environment, with an SLO we sign.</p></div></li>
      </ol>
    </div>
  </div>
</div></section>

<section class="stack" id="stack"><div class="wrap">
  <span class="k">Stack</span>
  <h2 style="margin-top:12px">Everything we work with</h2>
  <div class="stack-grid">
    {stackgroup("server","Serving and compilers",[
      ("[vLLM](https://docs.vllm.ai/)",None),("[SGLang](https://docs.sglang.ai/)",None),("[TensorRT-LLM](https://nvidia.github.io/TensorRT-LLM/)","nvidia"),("[llama.cpp](https://github.com/ggml-org/llama.cpp)",None),
      ("[ExecuTorch](https://pytorch.org/executorch/)","pytorch"),("[MLX](https://ml-explore.github.io/mlx/)","apple"),("[torch.compile](https://pytorch.org/docs/stable/torch.compiler.html)","pytorch"),
      ("[CUDA graphs](https://developer.nvidia.com/blog/cuda-graphs/)","nvidia"),("[Triton](https://triton-lang.org/)",None),("[CUTLASS](https://github.com/NVIDIA/cutlass)","nvidia"),
      ("[PTX](https://docs.nvidia.com/cuda/parallel-thread-execution/) and [SASS](https://docs.nvidia.com/cuda/cuda-binary-utilities/)","nvidia"),("[ROCm](https://rocm.docs.amd.com/) and [HIP](https://rocm.docs.amd.com/projects/HIP/en/latest/)","amd")])}
    {stackgroup("cpu","Hardware",[
      ("[H100](https://www.nvidia.com/en-us/data-center/h100/) · [H200](https://www.nvidia.com/en-us/data-center/h200/)","nvidia"),("[B200](https://www.nvidia.com/en-us/data-center/dgx-b200/) · [GB200](https://www.nvidia.com/en-us/data-center/gb200-nvl72/)","nvidia"),
      ("[A100](https://www.nvidia.com/en-us/data-center/a100/)","nvidia"),("[L40S](https://www.nvidia.com/en-us/data-center/l40s/) · [L4](https://www.nvidia.com/en-us/data-center/l4/)","nvidia"),
      ("[RTX 4090](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/) · [5090](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/)","nvidia"),("[MI300X](https://www.amd.com/en/products/accelerators/instinct/mi300/mi300x.html)","amd"),
      ("[Jetson Orin](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/) · [Thor](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-thor/)","nvidia"),("[Apple M-series](https://developer.apple.com/documentation/apple-silicon)","apple"),
      ("[Snapdragon](https://www.qualcomm.com/snapdragon) · [Dragonwing](https://www.qualcomm.com/dragonwing)","qualcomm"),("[Raspberry Pi 5](https://www.raspberrypi.com/products/raspberry-pi-5/)","raspberrypi"),("x86 and [ARM](https://www.arm.com/) CPUs","arm")])}
    {stackgroup("sliders-horizontal","Techniques",[
      ("[FP8](https://arxiv.org/abs/2209.05433) · [INT8](https://arxiv.org/abs/2208.07339) · [INT4](https://arxiv.org/abs/2212.09720) · [NVFP4](https://developer.nvidia.com/blog/introducing-nvfp4-for-efficient-and-accurate-low-precision-inference/)",None),
      ("[AWQ](https://arxiv.org/abs/2306.00978) · [GPTQ](https://arxiv.org/abs/2210.17323) · [SmoothQuant](https://arxiv.org/abs/2211.10438)",None),("[Paged attention](https://arxiv.org/abs/2309.06180)",None),
      ("[Prefix caching](https://arxiv.org/abs/2312.07104)",None),("[Chunked prefill](https://arxiv.org/abs/2403.02310)",None),("[Disaggregated prefill / decode](https://arxiv.org/abs/2401.09670)",None),
      ("[EAGLE-3](https://arxiv.org/abs/2503.01840) · [Medusa](https://arxiv.org/abs/2401.10774)",None),("[KV-cache quantisation](https://arxiv.org/abs/2402.02750) and [offload](https://arxiv.org/abs/2303.06865)",None),
      ("[Tensor](https://arxiv.org/abs/1909.08053) · [pipeline](https://arxiv.org/abs/1811.06965) · [expert](https://arxiv.org/abs/2006.16668) parallelism",None),("[QLoRA](https://arxiv.org/abs/2305.14314)",None)])}
    {stackgroup("box","Models",[
      ("[Llama](https://www.llama.com/)","meta"),("[Qwen](https://qwenlm.github.io/) · [Qwen-VL](https://github.com/QwenLM/Qwen3-VL)","qwen"),("[DeepSeek](https://github.com/deepseek-ai)","deepseek"),
      ("[Mistral](https://mistral.ai/) · [Pixtral](https://mistral.ai/news/pixtral-12b)","mistralai"),("[Gemma](https://ai.google.dev/gemma)","google"),("[GLM](https://github.com/zai-org)","zhipu"),("[Kimi](https://github.com/MoonshotAI)","kimi"),
      ("[Whisper](https://github.com/openai/whisper)","openai"),("[Embedding and reranker models](https://huggingface.co/spaces/mteb/leaderboard)",None),("[Your fine-tunes](#w-edge)",None)])}
  </div>
</div></section>

<section class="clients" aria-labelledby="h-clients"><div class="wrap">
  <h2 class="sr-only" id="h-clients">Clients</h2><span class="k" aria-hidden="true">Clients</span>
  <div class="quotes">
    <figure class="quote"><p>“VitalOps helped us optimise our data pipelines for the finance databases, which directly translated into a smoother and more intuitive experience for our users.”</p><footer><img src="assets/chatfin-logo.png" alt="Chatfin"><span>CEO, Chatfin · AI for finance teams</span></footer></figure>
    <figure class="quote"><p>“The team is highly responsive, pragmatic, and product-minded, and the best part is that they understand what it takes to operationalize data, not just analyze it.”</p><footer><img src="assets/straightops-logo.jpg" alt="Straightops"><span>CEO, Straightops · Source-to-Pay automation</span></footer></figure>
  </div>
</div></section>

{COMPANY if SHOW_COMPANY else ""}

<section class="faq"><div class="wrap">
  <span class="k">Questions</span>
  <h2 style="margin:12px 0 20px">What engineering teams ask us</h2>
  <details><summary>Do we have to send you our weights or data?</summary><p>No. Optimize, Serve, Edge and Fleet run in your cloud account or data centre. Evals run on your data where it already lives. For sprints, our engineers work inside your environment.</p></details>
  <details><summary>Which models can you speed up?</summary><p>Open-weight models and your own fine-tunes: Llama, Qwen, DeepSeek, Mistral, Gemma, GLM, Whisper, VLMs, embedding and reranker models. We can't make a closed API model faster, but we can route, cache and batch around it.</p></details>
  <details><summary>How do you make sure the faster model is still correct?</summary><p>You set an accuracy floor on your eval set. Every candidate configuration is evaluated against it, with several seeds, and anything below the floor is rejected no matter how fast it is. Custom kernels are checked numerically against the reference implementation and inspected at SASS level.</p></details>
  <details><summary>What does "down to the SASS" actually mean?</summary><p>Most optimisation stops at the serving engine's flags. When the remaining bottleneck is a kernel, we write or tune it in Triton or CUDA and then inspect what the compiler produced: register pressure, spills, occupancy, shared-memory bank conflicts and stall reasons in the SASS the GPU executes. We don't write SASS; NVIDIA's ptxas does. We steer it through PTX intrinsics, launch bounds and compiler flags, and check the result. Optimize's simulator lets us do that without a GPU in the loop.</p></details>
  <details><summary>Can you really train on the edge device?</summary><p>For many devices, yes. QLoRA fine-tunes of 1–8B models fit within the memory of a Jetson Orin, an Apple M-series machine or a workstation GPU. Edge plans the job within the device's memory budget and tells you the time and the expected eval gain before it starts.</p></details>
  <details><summary>Do you support AMD or non-NVIDIA hardware?</summary><p>AMD MI300-class GPUs through ROCm, with kernels written in Triton where possible. Edge covers Apple, Qualcomm and ARM targets. The kernel simulator currently models NVIDIA GPUs.</p></details>
</div></section>

<section class="cta" id="contact"><div class="wrap">
  <span class="k">Get started</span>
  <h2>What's the number you need to hit?</h2>
  <p class="lede">Tokens per second, time to first token, a memory budget, a cost per million tokens. Bring it and the model. We'll tell you in 30 minutes whether it's reachable and what it would take.</p>
  <div class="hero-cta"><a class="btn btn-p" href="https://calendly.com/abhijith-vitalops/30min" target="_blank" rel="noopener">Book an inference review</a><a class="btn btn-s" href="mailto:hello@vitalops.ai">hello@vitalops.ai</a></div>
</div></section>
</main>

<footer class="site"><div class="wrap foot">
  <a class="logo" href="#top"><svg aria-hidden="true"><use href="#vo-logo"/></svg>VitalOps</a>
  <div class="foot-links"><a href="#tour">Walkthrough</a><a href="#services">Services</a><a href="#stack">Stack</a><a href="https://github.com/vitalops" target="_blank" rel="noopener">GitHub</a><a href="https://x.com/vitalopsai" target="_blank" rel="noopener">X</a><a href="mailto:hello@vitalops.ai">Contact</a></div>
  <span>© <span id="yr">2026</span> VitalOps Technologies Pvt Ltd</span>
  <address class="foot-legal">VitalOps Technologies Pvt Ltd<br>Asset Greenford, 9B, Metro Gardens Road<br>Aluva 683106, Ernakulam, Kerala, India <svg class="flag" viewBox="0 0 18 12" aria-label="India" role="img"><rect width="18" height="4" fill="#ff9933"/><rect y="4" width="18" height="4" fill="#fff"/><rect y="8" width="18" height="4" fill="#138808"/><circle cx="9" cy="6" r="1.6" fill="none" stroke="#000080" stroke-width=".55"/><circle cx="9" cy="6" r=".35" fill="#000080"/></svg></address>
</div></footer>

<script>
if(!(window.CSS&&CSS.registerProperty))document.documentElement.classList.add('no-prop');
// the mark spins with scroll: a quarter degree per pixel. Past the ends, Safari reports the bounce as scrollY itself;
// Chrome and Firefox keep the position clamped and only show the bounce in the compositor, so wheel and touch input at a
// bound feeds a virtual overscroll. It holds until a release signal: a zero-delta wheel event (macOS trackpads at gesture
// end; Edge on Windows sends it too), scrollend, touchend, the page moving, or 6 s of silence; then it springs back.
(function(){{var ms=document.querySelectorAll('.logo svg');if(!ms.length||matchMedia('(prefers-reduced-motion:reduce)').matches)return;
var over=0,held=false,last=0,t=false,ty=null,lastY=window.scrollY;
function maxY(){{return Math.max(0,document.documentElement.scrollHeight-innerHeight);}}
function queue(){{if(!t){{t=true;requestAnimationFrame(apply);}}}}
function release(){{held=false;last=0;queue();}}
function apply(){{t=false;var y=window.scrollY,m=maxY(),now=performance.now();
  if(y<0||y>m+1)over=0;
  else if(over){{if(y!==lastY)held=false;
    if(held&&ty==null&&now-last>6000)held=false;
    if(!held&&ty==null&&now-last>60){{over*=0.85;if(Math.abs(over)<0.5)over=0;}}}}
  lastY=y;var d=((y+over)*0.25)%360+'deg';for(var i=0;i<ms.length;i++)ms[i].style.setProperty('--spin',d);if(over)queue();}}
function push(dy){{var y=window.scrollY,m=maxY();if(y<0||y>m+1)return;
  if((y<=0&&dy<0)||(y>=m-1&&dy>0)){{over=Math.max(-320,Math.min(320,over+dy*0.5));held=true;last=performance.now();queue();}}}}
addEventListener('scroll',queue,{{passive:true}});
addEventListener('scrollend',release,{{passive:true}});
addEventListener('wheel',function(e){{if(e.deltaY===0&&e.deltaX===0){{release();return;}}push(e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?innerHeight:1));}},{{passive:true}});
addEventListener('touchstart',function(e){{ty=e.touches[0].clientY;}},{{passive:true}});
addEventListener('touchmove',function(e){{if(ty==null)return;var y=e.touches[0].clientY;push(ty-y);ty=y;}},{{passive:true}});
addEventListener('touchend',function(){{ty=null;release();}},{{passive:true}});
addEventListener('touchcancel',function(){{ty=null;release();}},{{passive:true}});
apply();}})();
(function(){{
  var toggle=document.getElementById('navToggle'),links=document.getElementById('navLinks');
  toggle.addEventListener('click',function(){{var open=links.classList.toggle('open');toggle.setAttribute('aria-expanded',open?'true':'false');}});
  links.addEventListener('click',function(e){{if(e.target.closest('a')){{links.classList.remove('open');toggle.setAttribute('aria-expanded','false');}}}});
  document.getElementById('yr').textContent=new Date().getFullYear();
  var bar=[].slice.call(document.querySelectorAll('.tour-bar a')),steps=[].slice.call(document.querySelectorAll('.step'));
  if('IntersectionObserver' in window){{
    var io=new IntersectionObserver(function(es){{es.forEach(function(en){{if(!en.isIntersecting)return;bar.forEach(function(a){{a.classList.toggle('on',a.getAttribute('href')==='#'+en.target.id);}});}});}},{{rootMargin:'-30% 0px -60% 0px',threshold:0}});
    steps.forEach(function(s){{io.observe(s);}});
  }}
}})();
(function(){{
  var fr=[].slice.call(document.querySelectorAll('.frame'));if(!fr.length)return;
  function fit(){{
    document.documentElement.style.setProperty('--sbw',(window.innerWidth-document.documentElement.clientWidth)+'px');
    fr.forEach(function(f){{var m=f.querySelector('.mock');if(!m)return;var w=f.clientWidth||f.parentElement.clientWidth;m.style.setProperty('--s',Math.min(1,w/1132).toFixed(4));}});

  }}
  fit();window.addEventListener('resize',fit);
  if('ResizeObserver' in window){{var ro=new ResizeObserver(fit);fr.forEach(function(f){{ro.observe(f);}});}}
}})();
(function(){{
  if(window.__norotate)return;
  [].slice.call(document.querySelectorAll('.carousel')).forEach(function(wrap){{
  var car=wrap.querySelector('.car');if(!car)return;
  var slides=[].slice.call(car.querySelectorAll('.frame')),N=slides.length,i=0,busy=false,W=car.clientWidth,GAP=1.04;
  var title=wrap.querySelector('.car-title'),count=wrap.querySelector('.car-count');
  var dragX=null,dragT=0,dragging=false,side=1,pendingAuto=false,tmr=null,paused=false,holdUntil=0,holdTmr=null,d0={{ry:0,tz:0,peek:0,s:.86,o:.45}};
  function pad(n){{return (n<10?'0':'')+n;}}
  function inView(){{var r=car.getBoundingClientRect();return r.bottom>0&&r.top<innerHeight;}}
  function pose(el,x,sc,op,instant,ry,tz){{el.style.transition=instant===true?'none':instant==='fast'?'transform .45s ease,opacity .45s ease':'';el.style.transform='translateX('+x.toFixed(1)+'px) translateZ('+(tz||0)+'px) rotateY('+(ry||0)+'deg) scale('+sc.toFixed(3)+')';el.style.opacity=op.toFixed(3);if(instant===true){{el.offsetWidth;el.style.transition='';}}}}
  function park(k,s){{slides[k]._side=s;pose(slides[k],s*W*GAP,.86,.45,true);}}
  function retract(){{slides.forEach(function(s,k){{if(k!==i)pose(s,(s._side||1)*W*GAP,.86,.45,'fast');}});}}
  function layout(){{W=car.clientWidth;slides.forEach(function(s,k){{s.classList.toggle('active',k===i);if(k===i)pose(s,0,1,1,true);else park(k,1);}});}}
  /* hover: lift the screen a little; near an edge, tilt and peek the neighbour */
  var hov=null;
  function setHover(z){{
    if(z===hov)return;hov=z;car.classList.toggle('hover',z!==null);var a=slides[i];
    if(z===null){{pose(a,0,1,1,'fast');retract();return;}}
    pose(a,0,1.004,1,'fast',z*5,12);
    if(z===0){{retract();return;}}
    var nb=(i+z+N)%N;slides.forEach(function(s,k){{if(k!==i&&k!==nb)pose(s,(s._side||1)*W*GAP,.86,.45,'fast');}});
    if(slides[nb]._side!==z)park(nb,z);pose(slides[nb],z*W*(GAP-.16),.9,.7,'fast');
  }}
  car.addEventListener('pointermove',function(e){{if(e.pointerType!=='mouse'||dragX!==null||busy)return;var r=car.getBoundingClientRect(),px=(e.clientX-r.left)/r.width;setHover(px<.18?-1:px>.82?1:0);}});
  car.addEventListener('pointerenter',function(e){{if(e.pointerType!=='mouse')return;paused=true;clearTimeout(tmr);}});
  car.addEventListener('pointerleave',function(e){{if(dragX!==null)return;setHover(null);if(e.pointerType==='mouse'){{paused=false;pendingAuto=false;holdUntil=Date.now()+5000;arm();}}}});
  var RM=matchMedia('(prefers-reduced-motion:reduce)').matches;
  function arm(){{clearTimeout(tmr);if(RM)return;tmr=setTimeout(function(){{if(!inView()){{arm();return;}}auto();}},14000);}}
  function auto(){{if(dragX!==null||paused){{pendingAuto=true;return;}}var left=holdUntil-Date.now();if(left>0){{clearTimeout(holdTmr);holdTmr=setTimeout(auto,left);return;}}go(1,false);}}
  function go(dir,fromDrag){{
    if(busy||N<2)return;busy=true;clearTimeout(tmr);
    var from=slides[i],j=(i+dir+N)%N,to=slides[j];hov=null;car.classList.remove('hover');
    if(!fromDrag)park(j,dir);
    from.classList.remove('active');from.classList.add('leaving');to.classList.add('active');
    to.removeAttribute('data-off');var tm=to.querySelector('.mock');if(tm&&tm._play&&inView())tm._play();
    from._side=-dir;pose(to,0,1,1,false);pose(from,-dir*W*GAP,.86,.45,false);
    i=j;pendingAuto=false;title.textContent=to.getAttribute('data-title')||'';count.textContent=pad(i+1)+' / '+pad(N);
    setTimeout(function(){{from.setAttribute('data-off','');from.classList.remove('leaving');var fm=from.querySelector('.mock');if(fm&&fm._stop)fm._stop();busy=false;arm();}},740);
  }}
  slides.forEach(function(s,k){{var m=s.querySelector('.mock');if(m)m.addEventListener('vo:done',function(){{if(k===i&&!RM)auto();}});}});
  wrap.addEventListener('keydown',function(e){{if(e.key==='ArrowRight'){{go(1,false);e.preventDefault();}}else if(e.key==='ArrowLeft'){{go(-1,false);e.preventDefault();}}}});
  wrap.addEventListener('focusin',function(){{paused=true;clearTimeout(tmr);}});wrap.addEventListener('focusout',function(e){{if(!wrap.contains(e.relatedTarget)){{paused=false;arm();}}}});
  layout();arm();window.addEventListener('resize',function(){{if(!busy&&dragX===null)layout();}});
  /* drag or swipe: the neighbour peeks in from the side as you pull */
  car.addEventListener('pointerdown',function(e){{if(busy||e.button)return;dragX=e.clientX;dragT=e.timeStamp;dragging=false;clearTimeout(tmr);try{{car.setPointerCapture(e.pointerId);}}catch(x){{}}}});
  car.addEventListener('pointermove',function(e){{
    if(dragX===null)return;var dx=e.clientX-dragX;
    if(!dragging){{if(Math.abs(dx)<=6)return;dragging=true;car.classList.add('dragging');side=dx<0?1:-1;
      var peeking=(hov===side);d0={{ry:hov?hov*5:0,tz:hov!==null?12:0,peek:peeking?.16:0,s:peeking?.9:.86,o:peeking?.7:.45}};
      if(!peeking){{if(hov&&N>2)pose(slides[(i+hov+N)%N],hov*W*GAP,.86,.45,'fast');park((i+side+N)%N,side);}}
      hov=null;}}
    var ns=dx<0?1:-1;if(ns!==side){{side=ns;d0.peek=0;d0.s=.86;d0.o=.45;park((i+side+N)%N,side);}}
    var p=Math.max(-1,Math.min(1,dx/W)),a=Math.abs(p),f=Math.max(0,1-a/.2),nb=slides[(i+side+N)%N];
    pose(slides[i],dx,1-.14*a,1-.55*a,true,d0.ry*f,d0.tz*f);pose(nb,side*W*(GAP-d0.peek)+dx,d0.s+(1-d0.s)*a,d0.o+(1-d0.o)*a,true);
  }});
  function endDrag(e){{
    if(dragX===null)return;var dx=e.clientX-dragX,dt=Math.max(1,e.timeStamp-dragT),v=Math.abs(dx)/dt;dragX=null;car.classList.remove('dragging');
    if(dragging){{dragging=false;var nb=(i+side+N)%N;
      if(Math.abs(dx)/W>.18||v>.6){{go(side,true);return;}}
      pose(slides[i],0,1,1,false);pose(slides[nb],side*W*GAP,.86,.45,false);}}
    if(pendingAuto){{pendingAuto=false;setTimeout(auto,700);}}else arm();
  }}
  car.addEventListener('pointerup',endDrag);car.addEventListener('pointercancel',endDrag);
  }});
}})();
(function(){{
  var lad=document.getElementById('lad');if(!lad)return;
  if(!('IntersectionObserver' in window)||(matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)){{lad.classList.add('open');return;}}
  var tmr=null;
  var io=new IntersectionObserver(function(es){{es.forEach(function(en){{
    if(en.isIntersecting&&en.intersectionRatio>=.35){{if(!lad.classList.contains('open')&&tmr===null)tmr=setTimeout(function(){{tmr=null;lad.classList.add('open');}},450);}}
    else if(!en.isIntersecting||en.intersectionRatio<.3){{if(tmr!==null){{clearTimeout(tmr);tmr=null;}}lad.classList.remove('open');}}
  }});}},{{threshold:[0,.3,.35]}});
  io.observe(lad);
}})();
(function(){{
  var fl=[].slice.call(document.querySelectorAll('.flow'));if(!fl.length||!('IntersectionObserver' in window))return;
  if(matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  fl.forEach(function(f){{f._orig=f.innerHTML;var tmr=null;function run(){{f.innerHTML=f._orig;}}
    var io=new IntersectionObserver(function(es){{es.forEach(function(en){{if(en.isIntersecting&&en.intersectionRatio>=.3){{if(tmr===null){{run();tmr=setInterval(run,14000);}}}}else if(tmr!==null){{clearInterval(tmr);tmr=null;}}}});}},{{threshold:[0,.3]}});
    io.observe(f);}});
}})();
</script>
{PLAY}
</body>
</html>
"""
def jsonld(page):
    import json, html as _h
    strip = lambda x: _h.unescape(re.sub(r"<[^>]+>", "", x)).strip()
    faqs = [{"@type": "Question", "name": strip(q), "acceptedAnswer": {"@type": "Answer", "text": strip(a)}}
            for q, a in re.findall(r"<details><summary>(.*?)</summary><p>(.*?)</p></details>", page, re.S)]
    org = {"@type": "Organization", "@id": "https://vitalops.ai/#org", "name": "VitalOps", "legalName": "VitalOps Technologies Pvt Ltd",
           "url": "https://vitalops.ai/", "logo": "https://vitalops.ai/assets/icon-512.png", "email": "hello@vitalops.ai",
           "sameAs": ["https://github.com/vitalops", "https://x.com/vitalopsai"],
           "address": {"@type": "PostalAddress", "streetAddress": "Asset Greenford, 9B, Metro Gardens Road", "addressLocality": "Aluva",
                       "addressRegion": "Kerala", "postalCode": "683106", "addressCountry": "IN"}}
    site = {"@type": "WebSite", "@id": "https://vitalops.ai/#site", "url": "https://vitalops.ai/", "name": "VitalOps", "publisher": {"@id": "https://vitalops.ai/#org"}}
    graph = [org, site] + ([{"@type": "FAQPage", "mainEntity": faqs}] if faqs else [])
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False) + '</script>'
open(OUT, "w").write(HTML.replace("__JSONLD__", jsonld(HTML)))
print("written", len(HTML))
