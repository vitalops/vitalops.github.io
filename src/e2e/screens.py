"""App screens for the industry tabs on /e2e. Each one is a mock of the VitalOps review app for one job,
showing a real case the agent has worked through. Names, numbers and companies are made up.

Rendered at a fixed 1072px layout and scaled as a whole on the page (like a screen recording).
"""

NAV_ICONS = ["inbox", "circle-check", "triangle-alert", "list-checks", "users", "history", "bar-chart-3", "settings"]


def pill(kind, text):
    return f'<span class="pl {kind}">{text}</span>'


def app(url, org, section, nav, kpis, cols, rows, detail, agent_note):
    """nav: [(label, count)], kpis: [(label, value, kind)], rows: [(cells..., status_html, selected)]"""
    navh = "".join(
        f'<li class="{"on" if i == 0 else ""}"><i data-i="{NAV_ICONS[i % len(NAV_ICONS)]}"></i><span>{l}</span>{f"<em>{c}</em>" if c else ""}</li>'
        for i, (l, c) in enumerate(nav))
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
 <nav class="a-nav">
  <div class="a-org"><img src="../assets/vo-mark.svg" alt=""><div><b>{org}</b><span>VitalOps</span></div></div>
  <ul>{navh}</ul>
  <div class="a-agent"><i></i><div><b>Agent running</b><span>{agent_note}</span></div></div>
 </nav>
 <div class="a-main">
  <div class="a-head"><div><span class="a-crumb">{org} / {section}</span><b class="a-title">{section}</b></div><div class="a-tools"><span class="a-search"><i data-i="search"></i>Search</span><span class="a-btn"><i data-i="filter"></i>Filter</span><span class="a-btn"><i data-i="download"></i>Export</span></div></div>
  <div class="a-kpis">{kp}</div>
  <div class="a-split">
   <div class="a-list"><div class="ql-h"><span class="on">Needs a person</span><span>All</span><span>Done</span></div>{"".join(trs)}</div>
   <div class="a-det">{detail}</div>
  </div>
 </div>
</div></div>'''


def meter(label, value, lo, hi, pos, ok, unit_note):
    """pos: marker position 0..100 on the bar; lo/hi: spec band as 0..100."""
    return (f'<div class="mtr {"ok" if ok else "bad"}"><div class="mtr-l"><b>{label}</b><span>{unit_note}</span></div>'
            f'<div class="mtr-v">{value}</div><div class="mtr-b"><i class="band" style="left:{lo}%;width:{hi - lo}%"></i><i class="mk" style="left:{pos}%"></i></div></div>')


def manufacturing():
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


def supply_chain():
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


def logistics():
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


def healthcare():
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


def insurance():
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
    detail = f'''<div class="d-h"><div><b>Kestrel Foods · commercial property</b><span>From Harlow &amp; Pike, 08:31 · 6 attachments · effective 1 Jan · 14 locations</span></div>{pill("warn", "Waiting on broker")}</div>
<div class="d-g2 w">
 <div><span class="d-k">Locations from SOV_Kestrel_2026.xlsx, 6 of 14</span><table class="d-t"><thead><tr><th>Loc</th><th>City</th><th>Construction</th><th>Built</th><th>Sprinklers</th><th>Value</th></tr></thead><tbody>{st}</tbody></table></div>
 <div class="d-col"><span class="d-k">Against your appetite guide</span>
  <div class="ck ok"><i data-i="check"></i><span>Food processing is in appetite</span></div>
  <div class="ck ok"><i data-i="check"></i><span>Largest site $11.4M, limit $15M</span></div>
  <div class="ck ok"><i data-i="check"></i><span>2 claims in 5 years, $310k total</span></div>
  <div class="ck warn"><i data-i="triangle-alert"></i><span>Sprinklers not given for 3 sites</span></div>
  <div class="ck ok"><i data-i="check"></i><span>No coastal or wildfire tier 1 sites</span></div>
 </div>
</div>
<div class="d-g2 mt">
 <div class="d-box"><span class="d-k">Also read</span><p>ACORD 125 and 140, loss runs from 2 carriers covering 2021 to 2025, and a 2024 survey report for Fresno. All values are in the rating tool as draft quote Q-77812.</p></div>
 <div class="d-draft s"><div class="dr-h"><span>To: a.pike@harlowpike.example</span><span>Sent 08:36</span></div><p>Thanks for the Kestrel Foods submission. Please send sprinkler details for locations 4, 9 and 12 so we can quote all 14 sites.</p></div>
</div>
<div class="d-acts"><span class="b1">Send to underwriter</span><span>Decline</span><span>Open draft quote</span></div>'''
    return app("app.vitalops.ai/westmark/submissions", "Westmark Specialty", "Submission intake",
               [("New submissions", "34"), ("Quote ready", "18"), ("Out of appetite", "9"), ("Appetite guide", ""), ("Brokers", ""), ("Audit log", ""), ("Reports", ""), ("Settings", "")],
               [("Submissions today", "34", ""), ("Ready for underwriter", "18", "ok"), ("Waiting on broker", "7", "warn"), ("Out of appetite", "9", "bad")],
               ["Insured", "Broker", "Value"], rows, detail, "Read submissions inbox 2 min ago")


def finance():
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
 <div class="d-box"><span class="d-k">Entry posted</span><table class="je"><tr><td>Dr Cash, operating</td><td>12,480.00</td><td></td></tr><tr><td>Dr Customer deductions</td><td>150.00</td><td></td></tr><tr><td>Cr Receivables, Arden Steel</td><td></td><td>12,630.00</td></tr></table></div>
</div>
<div class="d-acts"><span class="b1">Open case 4471</span><span>Reverse posting</span><span>View remittance</span></div>'''
    return app("app.vitalops.ai/tremont/cash-application", "Tremont Supply", "Cash application",
               [("Bank lines", "412"), ("Posted", "371"), ("Deductions", "26"), ("Unapplied", "15"), ("Customers", ""), ("Audit log", ""), ("Reports", ""), ("Settings", "")],
               [("Payments today", "412", ""), ("Matched and posted", "371", "ok"), ("Deductions", "26", "warn"), ("Unapplied cash", "$41,880", "bad")],
               ["Bank line", "Customer", "Amount"], rows, detail, "Read bank file 6 min ago")


SCREENS = {"manufacturing": manufacturing, "supply-chain": supply_chain, "logistics": logistics,
           "healthcare": healthcare, "insurance": insurance, "finance": finance}
