"""App screens for the industry tabs on /e2e. Each one is a mock of the VitalOps review app for one job,
showing a real case the agent has worked through. Names, numbers and companies are made up.

Rendered at a fixed 1072px layout and scaled as a whole on the page (like a screen recording).
"""

NAV_ICONS = ["inbox", "circle-check", "triangle-alert", "list-checks", "users", "history", "bar-chart-3", "settings"]


def pill(kind, text):
    return f'<span class="pl {kind}">{text}</span>'


def app(url, org, section, nav, kpis, cols, rows, detail, agent_note):
    """A compact app window (860px wide): icon rail, header, figures, work queue and the open item.
    nav: [(label, count)], the first three with counts become the queue tabs. kpis: [(label, value, kind)].
    rows: [(id, title, [middle...], right, status_html, selected)] given as a flat tuple."""
    rail = "".join(f'<li class="{"on" if i == 0 else ""}"><i data-i="{NAV_ICONS[i % len(NAV_ICONS)]}"></i></li>' for i in range(len(nav)))
    tabs = "".join(f'<span class="{"on" if i == 0 else ""}">{l} <em>{c}</em></span>' for i, (l, c) in enumerate([n for n in nav if n[1]][:3]))
    kp = "".join(f'<div class="{k}"><span>{l}</span><b>{v}</b></div>' for l, v, k in kpis)
    trs = []
    for r in rows:
        *cells, st, sel = r
        mid = " · ".join(cells[2:-1]) if len(cells) > 3 else ""
        right = cells[-1] if len(cells) > 2 else ""
        trs.append(f'<div class="qr{" on" if sel else ""}"><div class="q1"><span class="mono">{cells[0]}</span><span>{right}</span></div>'
                   f'<div class="q2"><b>{cells[1]}</b>{st}</div>{f'<div class="q3">{mid}</div>' if mid else ""}</div>')
    return f'''<div class="vw">
<div class="vw-bar"><span class="dots"><i></i><i></i><i></i></span><span class="vw-url"><i data-i="lock"></i>{url}</span><span class="vw-sp"></span></div>
<div class="a-app">
 <nav class="a-rail"><img src="../assets/vo-mark.svg" alt=""><ul>{rail}</ul><span class="a-live" title="{agent_note}"></span></nav>
 <div class="a-main">
  <div class="a-head"><div><span class="a-crumb">{org} / {section}</span><b class="a-title">{section}</b></div><div class="a-tools"><span class="a-run"><i></i>{agent_note}</span><span class="a-search"><i data-i="search"></i>Search</span></div></div>
  <div class="a-kpis">{kp}</div>
  <div class="a-split">
   <div class="a-list"><div class="ql-h">{tabs}</div>{"".join(trs)}</div>
   <div class="a-det">{detail}</div>
  </div>
 </div>
</div></div>'''


def dh(title, sub, kind, label):
    return f'<div class="d-h"><div><b>{title}</b><span>{sub}</span></div>{pill(kind, label)}</div>'


def box(k, body, cls=""):
    return f'<div class="d-box {cls}"><span class="d-k">{k}</span>{body}</div>'


def table(cols, rows, cls="d-t"):
    """rows: list of lists; a cell given as ("text", "dif") gets that class; a row ending with "@bad" gets class bad."""
    out = []
    for r in rows:
        rc = ""
        if r and r[-1] in ("@bad", "@tot", "@ok"):
            rc, r = r[-1][1:], r[:-1]
        tds = "".join(f'<td class="{c[1]}">{c[0]}</td>' if isinstance(c, tuple) else f"<td>{c}</td>" for c in r)
        out.append(f'<tr class="{rc}">{tds}</tr>')
    return f'<table class="{cls}"><thead><tr>{"".join(f"<th>{c}</th>" for c in cols)}</tr></thead><tbody>{"".join(out)}</tbody></table>'


def draft(to, right, text):
    return f'<div class="d-draft"><div class="dr-h"><span>To: {to}</span><span>{right}</span></div><p>{text}</p></div>'


def acts(*labels):
    return '<div class="d-acts">' + "".join(f'<span class="{"b1" if i == 0 else ""}">{l}</span>' for i, l in enumerate(labels)) + "</div>"


def meter(label, value, lo, hi, pos, ok, unit_note):
    """pos: marker position 0..100 on the bar; lo/hi: spec band as 0..100."""
    return (f'<div class="mtr {"ok" if ok else "bad"}"><div class="mtr-l"><b>{label}</b><span>{unit_note}</span></div>'
            f'<div class="mtr-v">{value}</div><div class="mtr-b"><i class="band" style="left:{lo}%;width:{hi - lo}%"></i><i class="mk" style="left:{pos}%"></i></div></div>')


def mfg_certs():
    rows = [
        ("2291", "XR-40 resin", "Calder Polymers", "08:52", pill("bad", "Held · viscosity"), True),
        ("2290", "PP copolymer", "Brightwater Chem", "08:40", pill("ok", "Released"), False),
        ("2288", "Glass fibre GF-13", "Ostrava Fibre", "08:31", pill("warn", "Certificate chased"), False),
        ("2287", "Black masterbatch", "Lumen Colour", "08:12", pill("ok", "Released"), False),
        ("2285", "XR-40 resin", "Calder Polymers", "07:58", pill("ok", "Released"), False),
        ("2284", "UV stabiliser", "Brightwater Chem", "07:40", pill("warn", "Old spec revision"), False),
        ("2281", "PA66 natural", "Ferro Nord", "07:22", pill("ok", "Released"), False),
        ("2279", "Talc filler T5", "Mineral Norte", "07:05", pill("ok", "Released"), False),
    ]
    spark = '''<svg class="spark" viewBox="0 0 220 64" aria-hidden="true"><rect x="0" y="14" width="220" height="30" class="sb"/><polyline points="4,38 26,36 48,39 70,34 92,33 114,30 136,26 158,22 180,17 202,8" class="sl"/><circle cx="202" cy="8" r="3.5" class="sd"/><text x="0" y="11">400</text><text x="0" y="58">350</text></svg>'''
    detail = f'''<div class="d-h"><div><b>Lot 2291 · XR-40 resin · 20 t</b><span>Calder Polymers · PO-48213 · receipt GR-5521 · spec RS-40 rev C</span></div>{pill("bad", "Held for QA")}</div>
<div class="d-g2">
 <div class="d-doc"><div class="dd-h"><b>CERTIFICATE OF ANALYSIS</b><span>Calder Polymers GmbH · Lot 2291</span></div>
  <div class="dd-r"><span>Viscosity (cP)</span><b class="hl">412</b></div><div class="dd-r"><span>Moisture (%)</span><b>0.08</b></div><div class="dd-r"><span>Density (g/cm³)</span><b>1.21</b></div><div class="dd-r"><span>Melt flow (g/10 min)</span><b>12.4</b></div><div class="dd-r"><span>Ash (%)</span><b>0.4</b></div>
  <div class="dd-sig">Approved: K. Brandt, QC</div><div class="dd-stamp">QC</div></div>
 <div class="d-col"><span class="d-k">Against spec RS-40 rev C</span>
  {meter("Viscosity", "412 cP", 20, 70, 82, False, "350–400")}
  {meter("Moisture", "0.08%", 0, 70, 56, True, "max 0.10")}
  {meter("Density", "1.21", 20, 80, 52, True, "1.18–1.24")}
  {meter("Melt flow", "12.4", 20, 80, 56, True, "10–14")}
 </div>
</div>
<div class="d-g2 mt">
 <div class="d-box"><span class="d-k">Viscosity, last 10 lots from Calder</span>{spark}<p>Rising on each of the last 5 lots. Lot 2291 is the first one over the limit.</p></div>
 <div class="d-box"><span class="d-k">Effect on production</span><p><b>WO-7731</b> needs 12 t of XR-40 on Thursday. Lot 2285 (18 t, released) covers it, so nothing is late.</p><p class="d-m">Lot 2291 is on quality hold Q2 in the ERP.</p></div>
</div>
<div class="d-acts"><span class="b1">Hold and raise NCR</span><span>Release under deviation</span><span>Ask supplier to retest</span></div>'''
    return app("app.vitalops.ai/northfield/incoming-inspection", "Northfield Plastics", "Incoming inspection",
               [("Inspection queue", "12"), ("Released today", "48"), ("Held lots", "3"), ("Specs", "214"), ("Suppliers", ""), ("Audit log", ""), ("Reports", ""), ("Settings", "")],
               [("Certificates read today", "61", ""), ("Released without review", "48", "ok"), ("Held for QA", "3", "bad"), ("Waiting on supplier", "2", "warn")],
               ["Lot", "Material", "Supplier", "Received"], rows, detail, "Last certificate 2 min ago")


def sc_acks():
    rows = [
        ("PO-48213", "Arlo Bearings", "Price +6%, date +7 d", pill("bad", "WO-7731 late"), True),
        ("PO-48190", "Mertz Castings", "Qty 400 → 380", pill("warn", "To buyer"), False),
        ("PO-48177", "Sato Seals", "No change", pill("ok", "Confirmed"), False),
        ("PO-48166", "Kord Electric", "Date +21 d", pill("bad", "SO-2290 at risk"), False),
        ("PO-48152", "Arlo Bearings", "No reply, 4 days", pill("warn", "Chased twice"), False),
        ("PO-48140", "Vela Steel", "2 of 5 lines", pill("warn", "Partial"), False),
        ("PO-48133", "Sato Seals", "No change", pill("ok", "Confirmed"), False),
        ("PO-48129", "Hollis Fasteners", "No change", pill("ok", "Confirmed"), False),
    ]
    lines = [("10", "Bearing 6205-2RS", "500", "500", "$2.40", "$2.55", "5 Dec", "5 Dec", (0, 1, 0)),
             ("20", "Bearing 6206-2RS", "300", "300", "$2.95", "$2.95", "5 Dec", "5 Dec", (0, 0, 0)),
             ("30", "Bearing 6305-ZZ", "200", "200", "$4.10", "$4.10", "3 Dec", "10 Dec", (0, 0, 1)),
             ("40", "Seal kit SK-14", "120", "120", "$1.12", "$1.12", "3 Dec", "3 Dec", (0, 0, 0))]
    lt = "".join(
        f'<tr><td>{n}</td><td>{it}</td><td>{q1}</td><td class="{"dif" if d[0] else ""}">{q2}</td><td>{p1}</td><td class="{"dif" if d[1] else ""}">{p2}</td><td>{s1}</td><td class="{"dif" if d[2] else ""}">{s2}</td></tr>'
        for n, it, q1, q2, p1, p2, s1, s2, d in lines)
    detail = f'''<div class="d-h"><div><b>PO-48213 · Arlo Bearings</b><span>Reply received 08:14 by email · 4 of 6 lines shown · buyer: M. Lund</span></div>{pill("bad", "2 changes")}</div>
<table class="d-t"><thead><tr><th>Line</th><th>Item</th><th>Qty ours</th><th>Theirs</th><th>Price ours</th><th>Theirs</th><th>Ship ours</th><th>Theirs</th></tr></thead><tbody>{lt}</tbody></table>
<div class="d-g2 mt">
 <div class="d-box"><span class="d-k">Line 30, ship to arrival</span>
  <div class="gt2"><div class="gt2-r"><span>Our order</span><div class="tr"><i style="left:14%;width:29%"></i><b style="left:50%"></b></div></div><div class="gt2-r bad"><span>Supplier</span><div class="tr"><i style="left:64%;width:29%"></i><b style="left:50%"></b></div></div><div class="gt2-x"><span>1 Dec</span><span class="nd">8 Dec · WO-7731</span><span>15 Dec</span></div></div>
  <p>Arrives 13 Dec with transit. Work order WO-7731 starts 8 Dec and feeds customer order SO-2281, due 19 Dec.</p></div>
 <div class="d-box"><span class="d-k">Line 10 price</span><p>Agreement <b>PA-112</b> fixes $2.40 until 31 Mar. The new price adds $75 to this order and $1,900 a year at current volume.</p></div>
</div>
<div class="d-draft"><div class="dr-h"><span>To: t.nowak@arlo-bearings.example</span><span>Drafted by the agent</span></div><p>Hi Tomas, thanks for confirming PO-48213. Two lines differ from our order. Line 10 is at $2.55, but agreement PA-112 fixes $2.40 until 31 March. Line 30 now ships 10 Dec, and we need it on site by 8 Dec. Please confirm the agreed price and an earlier date for line 30.</p></div>
<div class="d-acts"><span class="b1">Send reply</span><span>Accept changes</span><span>Edit draft</span></div>'''
    return app("app.vitalops.ai/halden/order-confirmations", "Halden Pumps", "Order confirmations",
               [("Changes to review", "17"), ("Confirmed", "121"), ("No reply", "9"), ("Agreements", "38"), ("Suppliers", ""), ("Audit log", ""), ("Reports", ""), ("Settings", "")],
               [("Replies today", "143", ""), ("Matched the PO", "121", "ok"), ("Changes to review", "17", "bad"), ("No reply after 3 days", "9", "warn")],
               ["PO", "Supplier", "Change"], rows, detail, "Checked purchasing inbox 1 min ago")


def lg_audit():
    rows = [
        ("88120", "Redline Freight", "L-30417", "$2,762", pill("bad", "Disputed $320"), True),
        ("88117", "Ostrow Trucking", "L-30402", "$1,410", pill("ok", "Approved"), False),
        ("88114", "Redline Freight", "L-30399", "$3,050", pill("warn", "Fuel above index"), False),
        ("88109", "Pine State", "L-30391", "$980", pill("warn", "Redelivery not on POD"), False),
        ("88101", "Ostrow Trucking", "L-30388", "$1,655", pill("ok", "Approved"), False),
        ("88097", "Halvard Logistics", "L-30380", "$2,210", pill("bad", "Duplicate of 88021"), False),
        ("88093", "Pine State", "L-30376", "$1,120", pill("ok", "Approved"), False),
        ("88090", "Redline Freight", "L-30371", "$2,405", pill("ok", "Approved"), False),
    ]
    detail = f'''<div class="d-h"><div><b>Invoice 88120 · Redline Freight</b><span>Load L-30417 · Dallas TX to Memphis TN · delivered 21 Nov · rate confirmation RC-9921</span></div>{pill("bad", "$320 disputed")}</div>
<table class="d-t"><thead><tr><th>Charge</th><th>Billed</th><th>Contract</th><th>Evidence</th><th></th></tr></thead><tbody>
<tr><td>Linehaul</td><td>$1,850</td><td>$1,850</td><td>Rate confirmation RC-9921</td><td>{pill("ok", "OK")}</td></tr>
<tr><td>Fuel surcharge 32%</td><td>$592</td><td>$592</td><td>DOE diesel index, week 47</td><td>{pill("ok", "OK")}</td></tr>
<tr class="bad"><td>Detention, 3 h</td><td>$225</td><td>$0</td><td>Gate log: on site 1 h 40 min, 2 h free</td><td>{pill("bad", "Dispute")}</td></tr>
<tr class="bad"><td>Liftgate</td><td>$95</td><td>$0</td><td>Dock delivery, door 12. Not ordered</td><td>{pill("bad", "Dispute")}</td></tr>
</tbody></table>
<div class="d-g2 mt">
 <div class="d-box"><span class="d-k">Time on site at DC-4, from the gate log</span>
  <div class="gl"><div class="gl-free" style="left:4%;width:84%"><span>Free time until 12:05</span></div><div class="gl-on" style="left:4%;width:70%"></div><b style="left:4%">In 10:05</b><b class="r" style="left:74%">Out 11:45</b></div>
  <p>The truck left 20 minutes before free time ended, so no detention is owed.</p></div>
 <div class="d-box"><span class="d-k">Payment</span><div class="pay"><div><span>Billed</span><b>$2,762</b></div><div><span>Approved to pay</span><b class="ok">$2,442</b></div><div><span>Held</span><b class="bad">$320</b></div></div><p class="d-m">Carrier has 14 days to respond under the contract.</p></div>
</div>
<div class="d-draft"><div class="dr-h"><span>To: billing@redline-freight.example</span><span class="att"><i data-i="file-text"></i>gate-log-L30417.pdf <i data-i="file-text"></i>RC-9921.pdf</span></div><p>Invoice 88120 for load L-30417: we are paying $2,442 and disputing $320. The gate log shows the truck on site from 10:05 to 11:45, inside the 2 hours of free time, and the delivery was to a dock door with no liftgate ordered. Both documents are attached.</p></div>
<div class="d-acts"><span class="b1">Send dispute</span><span>Pay in full</span><span>Edit draft</span></div>'''
    return app("app.vitalops.ai/corvel/freight-audit", "Corvel Distribution", "Freight audit",
               [("To check", "46"), ("Approved", "1,704"), ("Disputed", "131"), ("Carrier contracts", "22"), ("Carriers", ""), ("Audit log", ""), ("Reports", ""), ("Settings", "")],
               [("Invoices this week", "1,912", ""), ("Paid as billed", "1,704", "ok"), ("Disputed", "131", "bad"), ("Recovered this month", "$18,640", "ok")],
               ["Invoice", "Carrier", "Load", "Billed"], rows, detail, "Read carrier portal 4 min ago")


def hc_auth():
    rows = [
        ("J. Alvarez", "MRI lumbar spine", "Northstar Health", "2 Dec", pill("ok", "Submitted"), True),
        ("R. Chen", "Knee arthroscopy", "Cobalt Mutual", "4 Dec", pill("warn", "PT notes missing"), False),
        ("D. Hughes", "MRI shoulder", "Northstar Health", "3 Dec", pill("gray", "No auth needed"), False),
        ("P. Moreau", "Lumbar fusion", "Unity Plan", "9 Dec", pill("bad", "Peer review asked"), False),
        ("S. Patel", "CT abdomen", "Cobalt Mutual", "1 Dec", pill("ok", "Approved"), False),
        ("L. Brooks", "Hip injection", "Unity Plan", "5 Dec", pill("warn", "Form updated by insurer"), False),
        ("A. Novak", "MRI knee", "Northstar Health", "8 Dec", pill("ok", "Approved"), False),
    ]
    detail = f'''<div class="d-h"><div><b>J. Alvarez · MRN 204118 · MRI lumbar spine (CPT 72148)</b><span>Ordered by Dr. K. Imani · scheduled 2 Dec · Northstar Health PPO</span></div>{pill("ok", "Submitted")}</div>
<div class="steps"><div class="on"><i></i><b>Order seen</b><span>25 Nov 16:40</span></div><div class="on"><i></i><b>Insurer rules checked</b><span>Auth required</span></div><div class="on"><i></i><b>Notes attached</b><span>3 documents</span></div><div class="on"><i></i><b>Submitted</b><span>26 Nov 09:15 · PA-55120</span></div><div class="nx"><i></i><b>Decision</b><span>expected by 29 Nov</span></div></div>
<div class="crit">
 <div class="cr"><span class="cr-n">{pill("ok", "Met")}<b>Six weeks of conservative treatment</b></span><q>Physical therapy twice weekly since 12 Sep. No improvement in radicular pain.</q><em>Physio note, 30 Oct</em></div>
 <div class="cr"><span class="cr-n">{pill("ok", "Met")}<b>Neurological finding on exam</b></span><q>Decreased sensation in left L5 dermatome, EHL weakness 4/5.</q><em>Clinic note, Dr. Imani, 4 Nov</em></div>
 <div class="cr"><span class="cr-n">{pill("ok", "Met")}<b>Plain X-ray in the last 6 months</b></span><q>Mild disc space narrowing at L4-5, no fracture.</q><em>Lumbar X-ray report, 18 Sep</em></div>
</div>
<div class="d-g2 mt">
 <div class="d-box"><span class="d-k">Submission</span><p>Northstar provider portal, reference <b>PA-55120</b>. Form NS-IMG-2 with the 3 notes above. The agent checks the status each morning.</p></div>
 <div class="d-box"><span class="d-k">If the insurer asks for more</span><p>Clinical questions go to Dr. Imani's inbox. A denial goes to the appeals queue with this record attached.</p></div>
</div>
<div class="d-acts"><span class="b1">Open in EHR</span><span>View submission</span><span>Notify scheduler</span></div>'''
    return app("app.vitalops.ai/riverside/prior-auth", "Riverside Orthopaedics", "Prior authorisations",
               [("Worklist", "38"), ("Approved", "212"), ("Waiting on insurer", "41"), ("Insurer rules", "64"), ("Providers", ""), ("Audit log", ""), ("Reports", ""), ("Settings", "")],
               [("Orders needing auth", "38", ""), ("Submitted today", "22", "ok"), ("Waiting on insurer", "41", "warn"), ("Due within 48 h", "6", "bad")],
               ["Patient", "Procedure", "Insurer", "Date"], rows, detail, "Checked EHR work queue 3 min ago")


def in_subs():
    rows = [
        ("Kestrel Foods", "Harlow &amp; Pike", "$48.2M", pill("warn", "1 item asked"), True),
        ("Ardent Storage", "Mayfield Risk", "$12.6M", pill("bad", "Out of appetite"), False),
        ("Lyle Hotels", "Harlow &amp; Pike", "$91.0M", pill("ok", "Ready"), False),
        ("Brook Dental", "Ostin Brokers", "$4.1M", pill("warn", "Loss runs too old"), False),
        ("Corran Plastics", "Mayfield Risk", "$22.7M", pill("gray", "Duplicate"), False),
        ("Tessel Logistics", "Ostin Brokers", "$31.4M", pill("ok", "Ready"), False),
        ("Penrose Schools", "Harlow &amp; Pike", "$56.0M", pill("ok", "Ready"), False),
    ]
    sov = [("1", "Fresno", "Masonry", "1998", "Yes", "$11.4M", 0), ("2", "Modesto", "Steel frame", "2006", "Yes", "$8.9M", 0),
           ("4", "Tulare", "Steel frame", "2011", "not given", "$4.2M", 1), ("7", "Salinas", "Masonry", "1987", "Yes", "$3.6M", 0),
           ("9", "Visalia", "Tilt-up", "2015", "not given", "$2.8M", 1), ("12", "Merced", "Steel frame", "2003", "not given", "$2.1M", 1)]
    st = "".join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td><td class="{"dif" if m else ""}">{e}</td><td>{f}</td></tr>' for a, b, c, d, e, f, m in sov)
    detail = (dh("Kestrel Foods · commercial property", "From Harlow &amp; Pike, 08:31 · 6 attachments · 14 locations · draft quote Q-77812", "warn", "Waiting on broker")
        + '<span class="d-k">Locations from SOV_Kestrel_2026.xlsx, 6 of 14</span>'
        + f'<table class="d-t"><thead><tr><th>Loc</th><th>City</th><th>Construction</th><th>Built</th><th>Sprinklers</th><th>Value</th></tr></thead><tbody>{st}</tbody></table>'
        + '<div class="cks"><div class="ck ok"><i data-i="check"></i><span>Food processing, in appetite</span></div><div class="ck ok"><i data-i="check"></i><span>Largest site $11.4M, limit $15M</span></div>'
        + '<div class="ck ok"><i data-i="check"></i><span>2 claims in 5 years, $310k</span></div><div class="ck warn"><i data-i="triangle-alert"></i><span>Sprinklers missing for 3 sites</span></div></div>'
        + draft("a.pike@harlowpike.example", "Sent 08:36", "Thanks for the Kestrel Foods submission. Please send sprinkler details for locations 4, 9 and 12 so we can quote all 14 sites.")
        + acts("Send to underwriter", "Decline", "Open draft quote"))
    return app("app.vitalops.ai/westmark/submissions", "Westmark Specialty", "Submission intake",
               [("New submissions", "34"), ("Quote ready", "18"), ("Out of appetite", "9"), ("Appetite guide", ""), ("Brokers", ""), ("Audit log", ""), ("Reports", ""), ("Settings", "")],
               [("Submissions today", "34", ""), ("Ready for underwriter", "18", "ok"), ("Waiting on broker", "7", "warn"), ("Out of appetite", "9", "bad")],
               ["Insured", "Broker", "Value"], rows, detail, "Read submissions inbox 2 min ago")


def fi_cash():
    rows = [
        ("ACH 77120", "Arden Steel", "$12,480.00", pill("warn", "Posted · $150 deduction"), True),
        ("Wire 5512", "Pell Builders", "$48,000.00", pill("ok", "Posted"), False),
        ("ACH 77131", "Norra Fabrication", "$9,312.40", pill("warn", "Remittance asked"), False),
        ("Lockbox 2290", "Quay Marine", "$3,880.00", pill("ok", "Posted"), False),
        ("ACH 77140", "Coyle Metals", "$15,200.00", pill("bad", "Overpaid $200"), False),
        ("ACH 77142", "Pell Builders", "$6,115.75", pill("ok", "Posted"), False),
        ("Wire 5519", "Stanmore Rail", "$71,940.00", pill("ok", "Posted"), False),
        ("ACH 77150", "Quay Marine", "$2,250.00", pill("ok", "Posted"), False),
    ]
    detail = f'''<div class="d-h"><div><b>ACH 77120 · Arden Steel · $12,480.00</b><span>Bank line 24 Nov · remittance by email from ap@ardensteel.example, 23 Nov 17:02</span></div>{pill("warn", "Deduction routed")}</div>
<div class="d-g2">
 <div class="d-mail"><div class="dm-h"><b>Payment advice</b><span>Arden Steel accounts payable</span></div><p>Paid 24 Nov by ACH, total 12,480.00</p><p class="mono">INV-3310 &nbsp; 5,200.00<br>INV-3318 &nbsp; 4,880.00<br>INV-3325 &nbsp; <mark>2,400.00 PRICE ADJ</mark></p></div>
 <div><span class="d-k">Match</span><table class="d-t"><thead><tr><th>Invoice</th><th>Open</th><th>Paid</th><th>Difference</th></tr></thead><tbody>
 <tr><td>INV-3310</td><td>$5,200.00</td><td>$5,200.00</td><td>$0</td></tr><tr><td>INV-3318</td><td>$4,880.00</td><td>$4,880.00</td><td>$0</td></tr><tr><td>INV-3325</td><td>$2,550.00</td><td>$2,400.00</td><td class="dif">$150.00</td></tr>
 <tr class="tot"><td>Total</td><td>$12,630.00</td><td>$12,480.00</td><td>$150.00</td></tr></tbody></table></div>
</div>
<div class="d-g2 mt">
 <div class="d-box"><span class="d-k">Deduction</span><p>Reason PRICE ADJ. Sales opened price dispute <b>case 4471</b> on 2 Nov for INV-3325, for $150. Routed to collections with the case attached.</p></div>
 <div class="d-box"><span class="d-k">Entry posted</span><table class="je"><tr><td>Dr Cash, operating</td><td>12,480.00</td><td></td></tr><tr><td>Dr Customer deductions</td><td>150.00</td><td></td></tr><tr><td>Cr Receivables, Arden</td><td></td><td>12,630.00</td></tr></table></div>
</div>
<div class="d-acts"><span class="b1">Open case 4471</span><span>Reverse posting</span><span>View remittance</span></div>'''
    return app("app.vitalops.ai/tremont/cash-application", "Tremont Supply", "Cash application",
               [("Bank lines", "412"), ("Posted", "371"), ("Deductions", "26"), ("Unapplied", "15"), ("Customers", ""), ("Audit log", ""), ("Reports", ""), ("Settings", "")],
               [("Payments today", "412", ""), ("Matched and posted", "371", "ok"), ("Deductions", "26", "warn"), ("Unapplied cash", "$41,880", "bad")],
               ["Bank line", "Customer", "Amount"], rows, detail, "Read bank file 6 min ago")



# ── manufacturing ──
def mfg_orders():
    rows = [
        ("CPO-55102", "Brenner AG", "8 lines", pill("warn", "2 to check"), True),
        ("CPO-55101", "Ostfield Motors", "3 lines", pill("ok", "Entered"), False),
        ("CPO-55098", "Lakeview Pumps", "12 lines", pill("ok", "Entered"), False),
        ("CPO-55097", "Brenner AG", "1 line", pill("bad", "Unknown part"), False),
        ("CPO-55095", "Kessel Tools", "5 lines", pill("ok", "Entered"), False),
        ("CPO-55094", "Ostfield Motors", "2 lines", pill("ok", "Entered"), False),
        ("CPO-55090", "Arcon Fluid", "4 lines", pill("warn", "Date we can't meet"), False),
    ]
    lines = [["10", "BR-7781", "HSG-220-B", "400", "$18.40", "$18.40", "12 Jan", "OK"],
             ["20", "BR-7790", "CVR-118", "1,200", ("$2.10", "dif"), "$2.35", "12 Jan", ("Price", "dif")],
             ["30", "BR-7712", "SHF-40-S", "250", "$9.80", "$9.80", ("5 Jan", "dif"), ("Date", "dif")],
             ["40", "BR-7795", "GSK-61", "3,000", "$0.42", "$0.42", "12 Jan", "OK"]]
    detail = (dh("CPO-55102 · Brenner AG", "PDF from orders@brenner.example, 07:48 · 8 lines · 4 shown · contract BR-2026", "warn", "2 lines to check")
        + table(["Line", "Their part", "Our part", "Qty", "PO price", "Contract", "Wanted", ""], lines)
        + '<div class="d-g2">'
        + box("Line 20 price", "<p>Brenner's PO has $2.10. Contract BR-2026 has $2.35 since 1 Oct. The order total is $300 lower than it should be.</p>")
        + box("Line 30 date", "<p>250 of SHF-40-S by 5 Jan. Stock is 60 and the next run finishes 11 Jan. Earliest full delivery is 12 Jan.</p>")
        + "</div>"
        + draft("orders@brenner.example", "Drafted by the agent", "Thanks for order CPO-55102. Lines 10, 40 and the four not shown are confirmed for 12 Jan. Line 20 is priced at $2.35 under contract BR-2026. For line 30 we can ship 60 now and 190 on 12 Jan.")
        + acts("Send confirmation", "Accept as sent", "Edit draft"))
    return app("app.vitalops.ai/northfield/order-entry", "Northfield Plastics", "Order entry",
               [("To check", "4"), ("Entered", "112"), ("Unknown parts", "1"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Orders today", "117", ""), ("Entered without a person", "112", "ok"), ("To check", "4", "warn"), ("Average time to confirm", "6 min", "")],
               [], rows, detail, "Read orders inbox 1 min ago")


def mfg_maint():
    rows = [
        ("WO-90412", "Extruder 3, drive motor", "Closed 14:20", pill("bad", "4th in 60 days"), True),
        ("WO-90409", "Chiller 1", "Closed 13:05", pill("ok", "Coded"), False),
        ("WO-90407", "Press 12, hydraulics", "Closed 11:40", pill("ok", "Coded"), False),
        ("WO-90401", "Conveyor C4", "Closed 10:15", pill("warn", "Asset unclear"), False),
        ("WO-90398", "Extruder 1, heater band", "Closed 09:30", pill("ok", "Coded"), False),
        ("WO-90392", "Dryer D2", "Closed 08:10", pill("ok", "Coded"), False),
    ]
    detail = (dh("WO-90412 · Extruder 3, drive motor", "Closed by R. Okafor, 14:20 · 2.5 h · line down 1 h 10 min", "bad", "Repeat failure")
        + '<div class="note"><span class="d-k">Technician note</span><p><mark>replaced brg</mark> on <mark>drive end</mark>, motor <mark>running hot again</mark> and smelled burning, checked <mark>alignment</mark> ok and greased, <mark>same as last month</mark></p></div>'
        + '<div class="d-g2">'
        + box("Codes assigned", '<div class="codes"><div><span>Asset</span><b>EXT-03-M1</b></div><div><span>Failure</span><b>Bearing, drive end</b></div><div><span>Symptom</span><b>Overheating</b></div><div><span>Cause</span><b>Lubrication, suspected</b></div><div><span>Action</span><b>Replaced bearing</b></div></div>')
        + box("EXT-03-M1, last 90 days", '<div class="dots90"><i style="left:12%"></i><i style="left:44%"></i><i style="left:71%"></i><i class="now" style="left:96%"></i><span>Sep</span><span>Oct</span><span>Nov</span></div><p>4 bearing replacements in 60 days. Other extruder motors average one a year. Grease interval on the PM plan is 2,000 h.</p>')
        + "</div>"
        + acts("Send to reliability engineer", "Edit codes", "Open in CMMS"))
    return app("app.vitalops.ai/northfield/maintenance", "Northfield Plastics", "Maintenance records",
               [("Closed today", "23"), ("Repeat failures", "3"), ("Asset unclear", "1"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Work orders coded this month", "612", ""), ("Coded without a person", "588", "ok"), ("Repeat failures found", "7", "bad"), ("Downtime from repeats", "19 h", "warn")],
               [], rows, detail, "Read CMMS 5 min ago")


# ── supply chain ──
def sc_late():
    rows = [
        ("PO-48166 / 10", "Kord Electric", "Due 2 Dec", pill("bad", "21 days late"), True),
        ("PO-48201 / 30", "Mertz Castings", "Due 4 Dec", pill("warn", "Split offered"), False),
        ("PO-48155 / 20", "Vela Steel", "Due 5 Dec", pill("ok", "Date confirmed"), False),
        ("PO-48190 / 10", "Sato Seals", "Due 6 Dec", pill("warn", "No reply yet"), False),
        ("PO-48177 / 40", "Hollis Fasteners", "Due 9 Dec", pill("ok", "On time"), False),
        ("PO-48162 / 20", "Arlo Bearings", "Due 9 Dec", pill("ok", "On time"), False),
    ]
    thread = ('<div class="thread"><div class="msg out"><span>Agent · 08:00</span><p>PO-48166 line 10, 80 control boards due 2 Dec. Please confirm the ship date.</p></div>'
              '<div class="msg in"><span>Kord Electric · 10:12</span><p>Chip shortage on our side. We can ship 30 on 4 Dec and the other 50 on 23 Dec.</p></div></div>')
    detail = (dh("PO-48166 line 10 · Kord Electric", "Control board CB-220 · 80 pcs · planner: S. Iyer", "bad", "Affects 2 customer orders")
        + '<div class="d-g2">' + box("Supplier reply", thread)
        + box("What it affects", table(["Order", "Needs", "With split"], [["WO-7802", "30 on 5 Dec", ("On time", "okc")], ["WO-7815", "50 on 9 Dec", ("14 days late", "dif")], ["SO-2290 Kessel", "ships 16 Dec", ("30 Dec", "dif")]]))
        + "</div>"
        + box("Options the agent found", '<div class="opts"><div><b>Take the split</b><span>SO-2290 ships 30 Dec. Kessel has a late penalty of 2% per week.</span></div><div><b>Buy 50 from Pell Components</b><span>Approved supplier, $4.10 more per board, ships 6 Dec.</span></div><div><b>Air freight the 50</b><span>Kord quotes 16 Dec by air, $640.</span></div></div>')
        + acts("Buy 50 from Pell", "Accept the split", "Reschedule WO-7815"))
    return app("app.vitalops.ai/halden/expediting", "Halden Pumps", "Late deliveries",
               [("At risk", "23"), ("Confirmed", "64"), ("No reply", "6"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Open lines due in 14 days", "412", ""), ("Dates confirmed", "383", "ok"), ("At risk", "23", "bad"), ("Chased today", "48", "")],
               [], rows, detail, "Chased 48 suppliers today")


def sc_onboard():
    rows = [
        ("SUP-1182", "Pell Components", "7 of 9 documents", pill("warn", "Bank check"), True),
        ("SUP-1181", "Ravel Plastics", "9 of 9", pill("ok", "Ready"), False),
        ("SUP-1179", "Norra Metalworks", "4 of 9", pill("warn", "Chased twice"), False),
        ("SUP-1176", "Gant Logistics", "9 of 9", pill("bad", "Sanctions match"), False),
        ("SUP-1175", "Ilex Coatings", "8 of 9", pill("warn", "Certificate expired"), False),
    ]
    docs = [("Tax registration", "ok", "Matches legal name Pell Components Ltd"), ("Bank letter", "bad", "Account name is Pell Holdings Ltd"),
            ("Insurance certificate", "warn", "Expires 6 Dec, renewal asked"), ("ISO 9001 certificate", "ok", "Valid to Mar 2028, checked on the registry"),
            ("Sanctions screening", "ok", "No match on 4 lists"), ("Signed code of conduct", "ok", "Received 20 Nov"), ("Quality questionnaire", "gray", "Waiting, sent 21 Nov")]
    dl = "".join(f'<div class="ck2 {k}"><i data-i="{"check" if k == "ok" else "triangle-alert" if k in ("bad", "warn") else "clock"}"></i><b>{n}</b><span>{t}</span></div>' for n, k, t in docs)
    detail = (dh("Pell Components Ltd", "Requested by S. Iyer for control boards · started 18 Nov", "warn", "Waiting on 2 items")
        + f'<div class="cklist">{dl}</div>'
        + '<div class="d-g2">'
        + box("Bank details", "<p>The account name on the bank letter is Pell Holdings Ltd, a different company from the one you are paying. The agent has asked Pell to explain, and the bank details stay locked until two people approve them.</p>", "warnb")
        + draft("vendors@pell.example", "Sent 09:40", "Thanks for the documents. The bank letter is in the name of Pell Holdings Ltd. Please send a letter for an account in the name of Pell Components Ltd, or a note on company letterhead explaining the link.")
        + "</div>" + acts("Approve bank details", "Reject", "Call supplier"))
    return app("app.vitalops.ai/halden/supplier-onboarding", "Halden Pumps", "Supplier onboarding",
               [("In progress", "11"), ("Ready", "3"), ("Blocked", "2"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("New suppliers this quarter", "38", ""), ("Average days to set up", "6", "ok"), ("Waiting on supplier", "9", "warn"), ("Blocked", "2", "bad")],
               [], rows, detail, "Checked registries 12 min ago")


# ── logistics ──
def lg_pod():
    rows = [
        ("L-30417", "DC-4 Memphis", "Driver photo 15:02", pill("warn", "Short 2 cartons"), True),
        ("L-30415", "Brook Retail #12", "Driver photo 14:40", pill("ok", "Released"), False),
        ("L-30411", "Quay Marine", "Scan 14:05", pill("ok", "Released"), False),
        ("L-30409", "Pell Builders", "Driver photo 13:30", pill("bad", "No signature"), False),
        ("L-30406", "DC-2 Dallas", "Driver photo 12:55", pill("ok", "Released"), False),
        ("L-30402", "Norra Fab", "Driver photo 12:10", pill("warn", "Damage noted"), False),
    ]
    pod = ('<div class="podp"><div class="pp-h"><b>DELIVERY RECEIPT</b><span>Redline Freight · Pro 88120</span></div>'
           '<div class="dd-r"><span>Consignee</span><b>Corvel DC-4</b></div><div class="dd-r"><span>Pieces</span><b>24 plt / 960 ctn</b></div>'
           '<div class="dd-r"><span>Seal</span><b>RL 551208</b></div><div class="pp-hand">short 2 ctn SKU 44120<br>rcvd 958 · door 12</div><div class="pp-sig">J. Mendes 21/11</div></div>')
    detail = (dh("Load L-30417 · DC-4 Memphis", "Delivery receipt photo from the driver app, 15:02 · invoice waiting on proof of delivery", "warn", "Exception")
        + '<div class="d-g2">' + f'<div>{pod}</div>'
        + '<div class="d-col"><span class="d-k">Read from the receipt</span>'
        + table(["Field", "Value", ""], [["Signed by", "J. Mendes", ("OK", "okc")], ["Date", "21 Nov", ("OK", "okc")], ["Seal", "RL 551208, matches BOL", ("OK", "okc")], ["Received", ("958 of 960 ctn", "dif"), ("Check", "dif")], ["Note", ("short 2 ctn SKU 44120", "dif"), ""]])
        + "</div></div>"
        + '<div class="d-g2">' + box("Billing", "<p>Load released for invoicing at 958 cartons. Customer invoice INV-77120 drafted for $2,118.40, 2 cartons less than ordered.</p>")
        + box("Shortage claim", "<p>Claim OSD-3391 opened against Redline Freight for 2 cartons of SKU 44120, $86.20, with the photo and seal number attached.</p>") + "</div>"
        + acts("Send claim to carrier", "Release in full", "Open load"))
    return app("app.vitalops.ai/corvel/delivery-closeout", "Corvel Distribution", "Delivery close-out",
               [("Exceptions", "9"), ("Released", "214"), ("Missing receipt", "12"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Loads delivered today", "236", ""), ("Released for billing", "214", "ok"), ("Exceptions", "9", "warn"), ("Average days to invoice", "0.4", "ok")],
               [], rows, detail, "Read driver app 1 min ago")


def lg_quote():
    rows = [
        ("RFQ-6120", "Brook Retail", "Dallas to Atlanta", pill("ok", "Quoted"), True),
        ("RFQ-6119", "Pell Builders", "Houston to Denver", pill("ok", "Quoted"), False),
        ("RFQ-6118", "Quay Marine", "Mobile to Chicago", pill("warn", "Hazmat"), False),
        ("RFQ-6117", "Lakeview Pumps", "Tulsa to Omaha", pill("ok", "Quoted"), False),
        ("RFQ-6115", "Norra Fab", "Austin to El Paso", pill("warn", "Below margin floor"), False),
        ("RFQ-6114", "Brook Retail", "Dallas to Miami", pill("ok", "Won"), False),
    ]
    mail = ('<div class="d-mail"><div class="dm-h"><b>Rate request</b><span>logistics@brookretail.example · 09:41</span></div>'
            '<p>hi, need a price for <mark>14 pallets</mark>, about <mark>16,800 lbs</mark>, <mark>Dallas DC to our Atlanta store</mark>, pickup <mark>Thursday</mark>, needs <mark>liftgate</mark> at delivery. standard 48x40. thanks</p></div>')
    calc = table(["Item", "Amount"], [["Linehaul, DAL to ATL, 781 mi", "$1,640.00"], ["Fuel 32%, week 47 index", "$524.80"], ["Liftgate at delivery", "$95.00"], ["Total to customer", "$2,259.80", "@tot"]])
    detail = (dh("RFQ-6120 · Brook Retail", "Email, 09:41 · quoted 09:42 · rep: A. Lin", "ok", "Quoted in 1 min")
        + '<div class="d-g2">' + mail
        + '<div class="d-col"><span class="d-k">Read</span><div class="codes"><div><span>Lane</span><b>Dallas TX to Atlanta GA</b></div><div><span>Freight</span><b>14 plt, 16,800 lb</b></div><div><span>Pickup</span><b>Thu 27 Nov</b></div><div><span>Extras</span><b>Liftgate</b></div></div></div>'
        + "</div>"
        + '<div class="d-g2">' + box("Price from your rate table", calc) + box("Margin", '<div class="pay"><div><span>Carrier cost</span><b>$1,872</b></div><div><span>Margin</span><b class="ok">17.2%</b></div><div><span>Floor</span><b>12%</b></div></div><p class="d-m">Above the floor, so the agent sent the quote.</p>') + "</div>"
        + draft("logistics@brookretail.example", "Sent 09:42", "Thanks for the request. 14 pallets Dallas DC to Atlanta, pickup Thursday 27 Nov with liftgate delivery: $2,259.80 all in. Reply to book and we will confirm the pickup window.")
        + acts("Open in TMS", "Revise quote"))
    return app("app.vitalops.ai/corvel/quotes", "Corvel Distribution", "Quote requests",
               [("New", "6"), ("Quoted", "88"), ("For a rep", "5"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Requests today", "99", ""), ("Quoted by the agent", "88", "ok"), ("Sent to a rep", "11", "warn"), ("Median time to quote", "2 min", "ok")],
               [], rows, detail, "Read quotes inbox 30 s ago")


# ── healthcare ──
def hc_denials():
    rows = [
        ("CLM-88412", "M. Torres", "CO-16 · $1,240", pill("ok", "Corrected, resent"), True),
        ("CLM-88409", "K. Wu", "CO-197 · $3,880", pill("warn", "Appeal drafted"), False),
        ("CLM-88401", "B. Grant", "CO-50 · $6,420", pill("bad", "Needs clinician"), False),
        ("CLM-88398", "L. Brooks", "CO-29 · $410", pill("gray", "Past deadline"), False),
        ("CLM-88392", "A. Novak", "CO-16 · $980", pill("ok", "Corrected, resent"), False),
        ("CLM-88390", "S. Patel", "CO-97 · $220", pill("warn", "To coder"), False),
    ]
    bars = [("CO-16 missing or wrong info", 41), ("CO-197 no authorisation", 22), ("CO-50 medical necessity", 14), ("CO-97 bundled", 11), ("CO-29 filed late", 6)]
    bh = "".join(f'<div class="hb"><span>{l}</span><i style="width:{v * 2}%"></i><b>{v}</b></div>' for l, v in bars)
    detail = (dh("CLM-88412 · M. Torres · knee arthroscopy", "Cobalt Mutual · billed $1,240 · denied 20 Nov · appeal deadline 19 Jan", "ok", "Resubmitted")
        + table(["Field", "On the claim", "Insurer's records", ""], [["Member ID", ("CBM 4471 2209", "dif"), "CBM 4471 2290", ("Fixed", "okc")], ["Date of birth", "14 Mar 1979", "14 Mar 1979", ""], ["Plan", "Cobalt PPO", "Cobalt PPO", ""]])
        + '<p class="d-p">Denial CO-16: the claim has missing or wrong information. The agent checked eligibility with the insurer, found the member ID typed with two digits swapped, corrected it and resubmitted the claim at 09:12.</p>'
        + '<div class="d-g2">' + box("Denials this month by reason", f'<div class="hbars">{bh}</div>') + box("Where they went", "<p><b>58</b> clerical, corrected and resubmitted<br><b>27</b> appeals drafted for the appeals team<br><b>9</b> sent to coders<br><b>6</b> past the filing deadline</p>") + "</div>"
        + acts("Open claim", "Undo correction"))
    return app("app.vitalops.ai/riverside/denials", "Riverside Orthopaedics", "Denied claims",
               [("Open", "31"), ("Resubmitted", "58"), ("Appeals", "27"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Denials this month", "94", ""), ("Fixed and resubmitted", "58", "ok"), ("Appeals drafted", "27", "warn"), ("Value recovered", "$212,400", "ok")],
               [], rows, detail, "Read remittance file 20 min ago")


def hc_referral():
    rows = [
        ("FAX 11:02", "From Lakeside Family Med.", "3 pages", pill("warn", "MRI report asked"), True),
        ("FAX 10:47", "From Dr. Haines", "2 pages", pill("ok", "On scheduling list"), False),
        ("FAX 10:30", "From Northgate Clinic", "5 pages", pill("ok", "On scheduling list"), False),
        ("FAX 10:12", "Unknown sender", "1 page", pill("bad", "Unreadable"), False),
        ("FAX 09:55", "From Lakeside Family Med.", "2 pages", pill("ok", "On scheduling list"), False),
    ]
    fax = ('<div class="faxp"><div class="fx-h">FAX · LAKESIDE FAMILY MEDICINE · 24 NOV 11:01 · P 1/3</div><b>REFERRAL TO ORTHOPAEDICS</b>'
           '<div class="dd-r"><span>Patient</span><b>Tomas Reyes</b></div><div class="dd-r"><span>DOB</span><b>02/07/1986</b></div>'
           '<div class="dd-r"><span>Insurance</span><b>Northstar PPO NS-55871</b></div><div class="fx-t">Reason: L knee pain 6 wks after fall, locking. MRI done 18 Nov, suspect meniscal tear. Please see at your earliest slot.</div><div class="pp-sig">Dr. A. Cole</div></div>')
    detail = (dh("Referral · Tomas Reyes", "Fax from Lakeside Family Medicine, 3 pages · received 11:02", "warn", "Waiting on MRI report")
        + '<div class="d-g2">' + f'<div>{fax}</div>'
        + '<div class="d-col"><span class="d-k">Done by the agent</span>'
        + '<div class="ck2 ok"><i data-i="check"></i><b>Patient</b><span>New record MRN 205530 created in the EHR</span></div>'
        + '<div class="ck2 ok"><i data-i="check"></i><b>Insurance</b><span>Active, specialist visit $40 copay, no referral number needed</span></div>'
        + '<div class="ck2 ok"><i data-i="check"></i><b>Urgency</b><span>Routine, seen within 2 weeks by your rule for knee injuries</span></div>'
        + '<div class="ck2 warn"><i data-i="triangle-alert"></i><b>MRI report</b><span>Mentioned but not attached, asked for by fax at 11:04</span></div>'
        + '<div class="ck2 ok"><i data-i="check"></i><b>Scheduling list</b><span>Added for Dr. Imani, sports knee clinic</span></div>'
        + "</div></div>" + acts("Open in EHR", "Call referring office", "Mark urgent"))
    return app("app.vitalops.ai/riverside/referrals", "Riverside Orthopaedics", "Referral intake",
               [("New", "8"), ("On scheduling list", "46"), ("Missing info", "5"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Referrals today", "59", ""), ("Ready for scheduling", "46", "ok"), ("Waiting on referrer", "5", "warn"), ("Average time to list", "4 min", "ok")],
               [], rows, detail, "Read e-fax 1 min ago")


# ── insurance ──
def in_fnol():
    rows = [
        ("CLM-20931", "Lyle Hotels", "Water damage · $40k to $80k", pill("ok", "With adjuster"), True),
        ("CLM-20930", "Penrose Schools", "Theft · under $10k", pill("ok", "Fast track"), False),
        ("CLM-20928", "Tessel Logistics", "Fire · over $250k", pill("bad", "Large loss team"), False),
        ("CLM-20925", "Brook Dental", "Water damage", pill("warn", "Policy lapsed"), False),
        ("CLM-20922", "Kestrel Foods", "Equipment breakdown", pill("ok", "With adjuster"), False),
    ]
    photos = '<div class="phs"><i class="p1"></i><i class="p2"></i><i class="p3"></i><i class="p4"></i></div>'
    detail = (dh("CLM-20931 · Lyle Hotels, Fresno", "Email from the broker, 07:12 · 9 photos, plumber's report · loss date 22 Nov", "ok", "Assigned to J. Park")
        + '<div class="d-g2">' + box("What arrived", photos + "<p>Burst pipe on the 3rd floor, water through 6 guest rooms below. The plumber's report says a fitting failed.</p>")
        + '<div class="d-col"><span class="d-k">Checked against policy PR-55120</span>'
        + '<div class="ck2 ok"><i data-i="check"></i><b>In force</b><span>1 Jan to 31 Dec, premium paid</span></div>'
        + '<div class="ck2 ok"><i data-i="check"></i><b>Cause covered</b><span>Sudden water discharge, form CP 10 30</span></div>'
        + '<div class="ck2 ok"><i data-i="check"></i><b>Deductible</b><span>$10,000 per occurrence</span></div>'
        + '<div class="ck2 warn"><i data-i="triangle-alert"></i><b>Business income</b><span>6 rooms closed, BI cover applies after 72 h</span></div>'
        + "</div></div>"
        + '<div class="d-g2">' + box("Sized and routed", "<p>Estimated $40k to $80k from rooms affected and your water damage history. Routed to J. Park, property adjuster for the Central Valley, who has 14 open claims.</p>")
        + draft("claims@harlowpike.example", "Sent 07:16", "Claim CLM-20931 is open and with adjuster J. Park. Please send the repair estimate and the list of closed rooms with dates, so business income can be worked out.") + "</div>"
        + acts("Open claim", "Change adjuster"))
    return app("app.vitalops.ai/westmark/new-claims", "Westmark Specialty", "New claims",
               [("New today", "27"), ("Assigned", "24"), ("Coverage questions", "3"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Claims opened today", "27", ""), ("Opened without a person", "24", "ok"), ("Coverage questions", "3", "warn"), ("Average time to assign", "4 min", "ok")],
               [], rows, detail, "Read claims inbox 1 min ago")


def in_policy():
    rows = [
        ("POL-77120", "Kestrel Foods", "Property", pill("bad", "3 differences"), True),
        ("POL-77118", "Lyle Hotels", "Property", pill("ok", "Matches binder"), False),
        ("POL-77115", "Tessel Logistics", "Package", pill("warn", "1 difference"), False),
        ("POL-77111", "Penrose Schools", "Property", pill("ok", "Matches binder"), False),
        ("POL-77109", "Brook Dental", "Package", pill("ok", "Matches binder"), False),
    ]
    rowsd = [["Building limit, loc 1", "$11,400,000", "$11,400,000", ("Same", "okc")],
             ["Wind and hail deductible", "1%", ("2%", "dif"), ("Differs", "dif")],
             ["Business income", "12 months", "12 months", ("Same", "okc")],
             ["CP 04 05 Ordinance or law", "Included", ("Missing", "dif"), ("Differs", "dif")],
             ["CP 10 30 Special causes of loss", "Included", "Included", ("Same", "okc")],
             ["Additional insured, Ardent Bank", "Lender loss payable", ("Mortgagee", "dif"), ("Differs", "dif")],
             ["Premium", "$184,200", "$184,200", ("Same", "okc")]]
    detail = (dh("POL-77120 · Kestrel Foods · commercial property", "Issued policy 92 pages, read against binder BND-5512 · effective 1 Jan", "bad", "3 differences")
        + table(["Item", "Binder", "Issued policy", ""], rowsd)
        + draft("policy-services@westmark.example", "Drafted by the agent", "Please correct POL-77120 before it goes to the broker. The wind and hail deductible should be 1%, endorsement CP 04 05 is missing, and Ardent Bank should be shown as lender loss payable, as bound on BND-5512.")
        + acts("Send correction request", "Mark as checked", "Open both documents"))
    return app("app.vitalops.ai/westmark/policy-checking", "Westmark Specialty", "Policy checking",
               [("To check", "14"), ("Matches", "96"), ("Differences", "6"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Policies checked this week", "116", ""), ("Matched the binder", "96", "ok"), ("With differences", "6", "bad"), ("Pages read", "8,940", "")],
               [], rows, detail, "Read issued policies 15 min ago")


# ── finance ──
def fi_ap():
    rows = [
        ("INV-30981", "Mertz Castings", "$14,200.00", pill("warn", "Quantity differs"), True),
        ("INV-30979", "Sato Seals", "$2,310.00", pill("ok", "Posted"), False),
        ("INV-30977", "Vela Steel", "$48,900.00", pill("ok", "Posted"), False),
        ("INV-30975", "Hollis Fasteners", "$880.00", pill("bad", "No PO"), False),
        ("INV-30972", "Arlo Bearings", "$6,375.00", pill("warn", "Price above PO"), False),
        ("INV-30970", "Pell Components", "$3,120.00", pill("ok", "Posted"), False),
    ]
    detail = (dh("INV-30981 · Mertz Castings · $14,200.00", "PDF from ar@mertz.example, 08:02 · due 24 Dec · PO-48190 · receipt GR-6120", "warn", "On hold")
        + table(["Line", "Item", "Invoiced", "Ordered", "Received", "Price", ""], [["1", "Pump housing PH-40", ("500", "dif"), "500", ("480", "dif"), "$28.40", ("20 not received", "dif")], ["2", "Freight", "1", "1", "1", "$0.00", ("OK", "okc")]])
        + '<div class="d-g2">' + box("Why it's on hold", "<p>Goods receipt GR-6120 shows 480 housings. The packing slip also says 480, with 20 on backorder. The invoice bills all 500.</p>")
        + box("What the agent did", "<p>Posted $13,632.00 for the 480 received. Held $568.00 and asked Mertz for a credit note or a later invoice for the 20.</p>") + "</div>"
        + draft("ar@mertz.example", "Sent 08:05", "Invoice INV-30981 bills 500 housings on PO-48190, and we received 480. We have approved $13,632.00 and will pay the remaining 20 when they arrive. Please send a credit note for $568.00 or reissue the invoice.")
        + acts("Approve as posted", "Pay in full", "Open PO"))
    return app("app.vitalops.ai/tremont/payables", "Tremont Supply", "Supplier invoices",
               [("To check", "18"), ("Posted", "342"), ("No PO", "4"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Invoices today", "364", ""), ("Matched and posted", "342", "ok"), ("Exceptions", "22", "warn"), ("Average days to post", "0.3", "ok")],
               [], rows, detail, "Read AP inbox 2 min ago")


def fi_close():
    rows = [
        ("1010", "Operating account", "1,912 lines", pill("ok", "Reconciled"), False),
        ("1012", "Payroll account", "214 lines", pill("ok", "Reconciled"), False),
        ("1020", "Collections account", "3,480 lines", pill("warn", "3 breaks"), True),
        ("1310", "Intercompany, Tremont MX", "96 lines", pill("bad", "Out by $4,210"), False),
        ("2010", "AP sub-ledger", "2,240 lines", pill("ok", "Reconciled"), False),
        ("1210", "AR sub-ledger", "2,980 lines", pill("ok", "Reconciled"), False),
    ]
    breaks = [["Deposit 30 Nov $8,120.00", "In ledger only", "Deposit in transit, clears 1 Dec", ("Timing", "okc")],
              ["Bank fee $45.00", "On statement only", "Monthly account fee, missing from ledger", ("Entry", "dif")],
              ["ACH 77142 $6,115.75 twice", "In ledger twice", "Posted twice on 26 Nov", ("Reverse", "dif")]]
    detail = (dh("1020 · Collections account · November", "Bank statement to 30 Nov · ledger balance $1,284,906.12 · statement $1,270,836.37", "warn", "3 breaks, cause found")
        + '<div class="recon"><div><span>Lines matched</span><b>3,477 of 3,480</b></div><div><span>Difference</span><b>$14,069.75</b></div><div><span>Explained</span><b class="ok">$14,069.75</b></div></div>'
        + table(["Break", "Where", "Likely cause", ""], breaks)
        + '<div class="d-g2">' + box("Proposed entries", '<table class="je"><tr><td>Dr Bank fees</td><td>45.00</td><td></td></tr><tr><td>Cr Cash, collections</td><td></td><td>45.00</td></tr><tr><td>Dr Receivables, Pell</td><td>6,115.75</td><td></td></tr><tr><td>Cr Cash, collections</td><td></td><td>6,115.75</td></tr></table>')
        + box("Close progress", '<div class="prog"><i style="width:83%"></i></div><p>10 of 12 accounts reconciled. Intercompany with Tremont MX is out by $4,210 and is with the controller.</p>') + "</div>"
        + acts("Post entries and sign off", "Edit", "Export workpaper"))
    return app("app.vitalops.ai/tremont/month-end", "Tremont Supply", "Month-end close",
               [("Breaks", "4"), ("Reconciled", "10"), ("Signed off", "8"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Accounts", "12", ""), ("Reconciled", "10", "ok"), ("Open breaks", "4", "warn"), ("Day of close", "2", "")],
               [], rows, detail, "Matched bank file 08:00")


SCREENS = {"manufacturing": [mfg_certs, mfg_orders, mfg_maint], "supply-chain": [sc_acks, sc_late, sc_onboard],
           "logistics": [lg_audit, lg_pod, lg_quote], "healthcare": [hc_auth, hc_denials, hc_referral],
           "insurance": [in_subs, in_fnol, in_policy], "finance": [fi_ap, fi_cash, fi_close]}
