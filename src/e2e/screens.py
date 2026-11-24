"""App screens for the industry tabs on /e2e. Each one is a mock of the VitalOps review app for one job,
showing a real case the agent has worked through. Names, numbers and companies are made up.

Rendered at a fixed layout and scaled as a whole on the page (like a screen recording).
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
        ("2291", "XR-40 resin", "Kalpa Polymers", "08:52", pill("bad", "Held · viscosity"), True),
        ("2290", "PP copolymer", "Suryodaya Chem", "08:40", pill("ok", "Released"), False),
        ("2288", "Glass fibre GF-13", "Ostwal Fibre", "08:31", pill("warn", "Certificate chased"), False),
        ("2287", "Black masterbatch", "Rangoli Colours", "08:12", pill("ok", "Released"), False),
        ("2285", "XR-40 resin", "Kalpa Polymers", "07:58", pill("ok", "Released"), False),
        ("2284", "UV stabiliser", "Suryodaya Chem", "07:40", pill("warn", "Old spec revision"), False),
        ("2281", "PA66 natural", "Ferro Deccan", "07:22", pill("ok", "Released"), False),
        ("2279", "Talc filler T5", "Narmada Minerals", "07:05", pill("ok", "Released"), False),
    ]
    spark = '''<svg class="spark" viewBox="0 0 220 64" aria-hidden="true"><rect x="0" y="14" width="220" height="30" class="sb"/><polyline points="4,38 26,36 48,39 70,34 92,33 114,30 136,26 158,22 180,17 202,8" class="sl"/><circle cx="202" cy="8" r="3.5" class="sd"/><text x="0" y="11">400</text><text x="0" y="58">350</text></svg>'''
    detail = f'''<div class="d-h"><div><b>Lot 2291 · XR-40 resin · 20 t</b><span>Kalpa Polymers · PO-48213 · receipt GR-5521 · spec RS-40 rev C</span></div>{pill("bad", "Held for QA")}</div>
<div class="d-g2">
 <div class="d-doc"><div class="dd-h"><b>CERTIFICATE OF ANALYSIS</b><span>Kalpa Polymers Pvt Ltd · Lot 2291</span></div>
  <div class="dd-r"><span>Viscosity (cP)</span><b class="hl">412</b></div><div class="dd-r"><span>Moisture (%)</span><b>0.08</b></div><div class="dd-r"><span>Density (g/cm³)</span><b>1.21</b></div><div class="dd-r"><span>Melt flow (g/10 min)</span><b>12.4</b></div><div class="dd-r"><span>Ash (%)</span><b>0.4</b></div>
  <div class="dd-sig">Approved: K. Shah, QC</div><div class="dd-stamp">QC</div></div>
 <div class="d-col"><span class="d-k">Against spec RS-40 rev C</span>
  {meter("Viscosity", "412 cP", 20, 70, 82, False, "350–400")}
  {meter("Moisture", "0.08%", 0, 70, 56, True, "max 0.10")}
  {meter("Density", "1.21", 20, 80, 52, True, "1.18–1.24")}
  {meter("Melt flow", "12.4", 20, 80, 56, True, "10–14")}
 </div>
</div>
<div class="d-g2 mt">
 <div class="d-box"><span class="d-k">Viscosity, last 10 lots from Kalpa</span>{spark}<p>Rising on each of the last 5 lots. Lot 2291 is the first one over the limit.</p></div>
 <div class="d-box"><span class="d-k">Effect on production</span><p><b>WO-7731</b> needs 12 t of XR-40 on Thursday. Lot 2285 (18 t, released) covers it, so nothing is late.</p><p class="d-m">Lot 2291 is on quality hold Q2 in the ERP.</p></div>
</div>
<div class="d-acts"><span class="b1">Hold and raise NCR</span><span>Release under deviation</span><span>Ask supplier to retest</span></div>'''
    return app("app.vitalops.ai/sahyog/incoming-inspection", "Sahyog Plastics", "Incoming inspection",
               [("Inspection queue", "12"), ("Released today", "48"), ("Held lots", "3"), ("Specs", "214"), ("Suppliers", ""), ("Audit log", ""), ("Reports", ""), ("Settings", "")],
               [("Certificates read today", "61", ""), ("Released without review", "48", "ok"), ("Held for QA", "3", "bad"), ("Waiting on supplier", "2", "warn")],
               ["Lot", "Material", "Supplier", "Received"], rows, detail, "Last certificate 2 min ago")


def mfg_maint():
    rows = [
        ("WO-90412", "Extruder 3, drive motor", "Closed 14:20", pill("bad", "4th in 60 days"), True),
        ("WO-90409", "Chiller 1", "Closed 13:05", pill("ok", "Coded"), False),
        ("WO-90407", "Press 12, hydraulics", "Closed 11:40", pill("ok", "Coded"), False),
        ("WO-90401", "Conveyor C4", "Closed 10:15", pill("warn", "Asset unclear"), False),
        ("WO-90398", "Extruder 1, heater band", "Closed 09:30", pill("ok", "Coded"), False),
        ("WO-90392", "Dryer D2", "Closed 08:10", pill("ok", "Coded"), False),
    ]
    detail = (dh("WO-90412 · Extruder 3, drive motor", "Closed by R. Pawar, 14:20 · 2.5 h · line down 1 h 10 min", "bad", "Repeat failure")
        + '<div class="note"><span class="d-k">Technician note</span><p><mark>replaced brg</mark> on <mark>drive end</mark>, motor <mark>running hot again</mark> and smelled burning, checked <mark>alignment</mark> ok and greased, <mark>same as last month</mark></p></div>'
        + '<div class="d-g2">'
        + box("Codes assigned", '<div class="codes"><div><span>Asset</span><b>EXT-03-M1</b></div><div><span>Failure</span><b>Bearing, drive end</b></div><div><span>Symptom</span><b>Overheating</b></div><div><span>Cause</span><b>Lubrication, suspected</b></div><div><span>Action</span><b>Replaced bearing</b></div></div>')
        + box("EXT-03-M1, last 90 days", '<div class="dots90"><i style="left:12%"></i><i style="left:44%"></i><i style="left:71%"></i><i class="now" style="left:96%"></i><span>Sep</span><span>Oct</span><span>Nov</span></div><p>4 bearing replacements in 60 days. Other extruder motors average one a year. Grease interval on the PM plan is 2,000 h.</p>')
        + "</div>"
        + acts("Send to reliability engineer", "Edit codes", "Open in CMMS"))
    return app("app.vitalops.ai/sahyog/maintenance", "Sahyog Plastics", "Maintenance records",
               [("Closed today", "23"), ("Repeat failures", "3"), ("Asset unclear", "1"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Work orders coded this month", "612", ""), ("Coded without a person", "588", "ok"), ("Repeat failures found", "7", "bad"), ("Downtime from repeats", "19 h", "warn")],
               [], rows, detail, "Read CMMS 5 min ago")


def mfg_orders():
    rows = [
        ("CPO-55102", "Brahma Motors", "8 lines", pill("warn", "2 to check"), True),
        ("CPO-55101", "Pratham Auto", "3 lines", pill("ok", "Entered"), False),
        ("CPO-55098", "Lakshmi Pumps", "12 lines", pill("ok", "Entered"), False),
        ("CPO-55097", "Brahma Motors", "1 line", pill("bad", "Unknown part"), False),
        ("CPO-55095", "Kesar Tools", "5 lines", pill("ok", "Entered"), False),
        ("CPO-55094", "Pratham Auto", "2 lines", pill("ok", "Entered"), False),
        ("CPO-55090", "Arcot Fluid", "4 lines", pill("warn", "Date we can't meet"), False),
    ]
    lines = [["10", "BR-7781", "HSG-220-B", "400", "₹1,520", "₹1,520", "12 Jan", "OK"],
             ["20", "BR-7790", "CVR-118", "1,200", ("₹174", "dif"), "₹195", "12 Jan", ("Price", "dif")],
             ["30", "BR-7712", "SHF-40-S", "250", "₹815", "₹815", ("5 Jan", "dif"), ("Date", "dif")],
             ["40", "BR-7795", "GSK-61", "3,000", "₹35", "₹35", "12 Jan", "OK"]]
    detail = (dh("CPO-55102 · Brahma Motors", "PDF from orders@brahmamotors.example, 07:48 · 8 lines · 4 shown · contract BR-2026", "warn", "2 lines to check")
        + table(["Line", "Their part", "Our part", "Qty", "PO price", "Contract", "Wanted", ""], lines)
        + '<div class="d-g2">'
        + box("Line 20 price", "<p>Brahma's PO has ₹174. Contract BR-2026 has ₹195 since 1 Oct. The order total is ₹25,200 lower than it should be.</p>")
        + box("Line 30 date", "<p>250 of SHF-40-S by 5 Jan. Stock is 60 and the next run finishes 11 Jan. Earliest full delivery is 12 Jan.</p>")
        + "</div>"
        + draft("orders@brahmamotors.example", "Drafted by the agent", "Thanks for order CPO-55102. Lines 10, 40 and the four not shown are confirmed for 12 Jan. Line 20 is priced at ₹195 under contract BR-2026. For line 30 we can ship 60 now and 190 on 12 Jan.")
        + acts("Send confirmation", "Accept as sent", "Edit draft"))
    return app("app.vitalops.ai/sahyog/order-entry", "Sahyog Plastics", "Order entry",
               [("To check", "4"), ("Entered", "112"), ("Unknown parts", "1"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Orders today", "117", ""), ("Entered without a person", "112", "ok"), ("To check", "4", "warn"), ("Average time to confirm", "6 min", "")],
               [], rows, detail, "Read orders inbox 1 min ago")


def sc_acks():
    rows = [
        ("PO-48213", "Arya Bearings", "Price +7%, date +7 d", pill("bad", "WO-7731 late"), True),
        ("PO-48190", "Mehta Castings", "Qty 400 → 380", pill("warn", "To buyer"), False),
        ("PO-48177", "Sai Seals", "No change", pill("ok", "Confirmed"), False),
        ("PO-48166", "Kiran Electronics", "Date +21 d", pill("bad", "SO-2290 at risk"), False),
        ("PO-48152", "Arya Bearings", "No reply, 4 days", pill("warn", "Chased twice"), False),
        ("PO-48140", "Vela Steel", "2 of 5 lines", pill("warn", "Partial"), False),
        ("PO-48133", "Sai Seals", "No change", pill("ok", "Confirmed"), False),
        ("PO-48129", "Hosur Fasteners", "No change", pill("ok", "Confirmed"), False),
    ]
    lines = [("10", "Bearing 6205-2RS", "500", "500", "₹198", "₹211", "5 Dec", "5 Dec", (0, 1, 0)),
             ("20", "Bearing 6206-2RS", "300", "300", "₹246", "₹246", "5 Dec", "5 Dec", (0, 0, 0)),
             ("30", "Bearing 6305-ZZ", "200", "200", "₹342", "₹342", "3 Dec", "10 Dec", (0, 0, 1)),
             ("40", "Seal kit SK-14", "120", "120", "₹93", "₹93", "3 Dec", "3 Dec", (0, 0, 0))]
    lt = "".join(
        f'<tr><td>{n}</td><td>{it}</td><td>{q1}</td><td class="{"dif" if d[0] else ""}">{q2}</td><td>{p1}</td><td class="{"dif" if d[1] else ""}">{p2}</td><td>{s1}</td><td class="{"dif" if d[2] else ""}">{s2}</td></tr>'
        for n, it, q1, q2, p1, p2, s1, s2, d in lines)
    detail = f'''<div class="d-h"><div><b>PO-48213 · Arya Bearings</b><span>Reply received 08:14 by email · 4 of 6 lines shown · buyer: M. Rao</span></div>{pill("bad", "2 changes")}</div>
<table class="d-t"><thead><tr><th>Line</th><th>Item</th><th>Qty ours</th><th>Theirs</th><th>Price ours</th><th>Theirs</th><th>Ship ours</th><th>Theirs</th></tr></thead><tbody>{lt}</tbody></table>
<div class="d-g2 mt">
 <div class="d-box"><span class="d-k">Line 30, ship to arrival</span>
  <div class="gt2"><div class="gt2-r"><span>Our order</span><div class="tr"><i style="left:14%;width:29%"></i><b style="left:50%"></b></div></div><div class="gt2-r bad"><span>Supplier</span><div class="tr"><i style="left:64%;width:29%"></i><b style="left:50%"></b></div></div><div class="gt2-x"><span>1 Dec</span><span class="nd">8 Dec · WO-7731</span><span>15 Dec</span></div></div>
  <p>Arrives 13 Dec with transit. Work order WO-7731 starts 8 Dec and feeds customer order SO-2281, due 19 Dec.</p></div>
 <div class="d-box"><span class="d-k">Line 10 price</span><p>Agreement <b>PA-112</b> fixes ₹198 until 31 Mar. The new price adds ₹6,500 to this order and ₹1,56,000 a year at current volume.</p></div>
</div>
<div class="d-draft"><div class="dr-h"><span>To: t.naik@aryabearings.example</span><span>Drafted by the agent</span></div><p>Hi Tushar, thanks for confirming PO-48213. Two lines differ from our order. Line 10 is at ₹211, but agreement PA-112 fixes ₹198 until 31 March. Line 30 now ships 10 Dec, and we need it on site by 8 Dec. Please confirm the agreed price and an earlier date for line 30.</p></div>
<div class="d-acts"><span class="b1">Send reply</span><span>Accept changes</span><span>Edit draft</span></div>'''
    return app("app.vitalops.ai/vardhan/order-confirmations", "Vardhan Pumps", "Order confirmations",
               [("Changes to review", "17"), ("Confirmed", "121"), ("No reply", "9"), ("Agreements", "38"), ("Suppliers", ""), ("Audit log", ""), ("Reports", ""), ("Settings", "")],
               [("Replies today", "143", ""), ("Matched the PO", "121", "ok"), ("Changes to review", "17", "bad"), ("No reply after 3 days", "9", "warn")],
               ["PO", "Supplier", "Change"], rows, detail, "Checked purchasing inbox 1 min ago")


def sc_late():
    rows = [
        ("PO-48166 / 10", "Kiran Electronics", "Due 2 Dec", pill("bad", "21 days late"), True),
        ("PO-48201 / 30", "Mehta Castings", "Due 4 Dec", pill("warn", "Split offered"), False),
        ("PO-48155 / 20", "Vela Steel", "Due 5 Dec", pill("ok", "Date confirmed"), False),
        ("PO-48190 / 10", "Sai Seals", "Due 6 Dec", pill("warn", "No reply yet"), False),
        ("PO-48177 / 40", "Hosur Fasteners", "Due 9 Dec", pill("ok", "On time"), False),
        ("PO-48162 / 20", "Arya Bearings", "Due 9 Dec", pill("ok", "On time"), False),
    ]
    thread = ('<div class="thread"><div class="msg out"><span>Agent · 08:00</span><p>PO-48166 line 10, 80 control boards due 2 Dec. Please confirm the dispatch date.</p></div>'
              '<div class="msg in"><span>Kiran Electronics · 10:12</span><p>Chip shortage on our side. We can dispatch 30 on 4 Dec and the other 50 on 23 Dec.</p></div></div>')
    detail = (dh("PO-48166 line 10 · Kiran Electronics", "Control board CB-220 · 80 pcs · planner: S. Iyer", "bad", "Affects 2 customer orders")
        + '<div class="d-g2">' + box("Supplier reply", thread)
        + box("What it affects", table(["Order", "Needs", "With split"], [["WO-7802", "30 on 5 Dec", ("On time", "okc")], ["WO-7815", "50 on 9 Dec", ("14 days late", "dif")], ["SO-2290 Kesar", "ships 16 Dec", ("30 Dec", "dif")]]))
        + "</div>"
        + box("Options the agent found", '<div class="opts"><div><b>Take the split</b><span>SO-2290 ships 30 Dec. Kesar has a late penalty of 2% per week.</span></div><div><b>Buy 50 from Prism Components</b><span>Approved supplier, ₹340 more per board, ships 6 Dec.</span></div><div><b>Send the 50 by air</b><span>Kiran quotes 16 Dec by air cargo, ₹18,500.</span></div></div>')
        + acts("Buy 50 from Prism", "Accept the split", "Reschedule WO-7815"))
    return app("app.vitalops.ai/vardhan/expediting", "Vardhan Pumps", "Late deliveries",
               [("At risk", "23"), ("Confirmed", "64"), ("No reply", "6"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Open lines due in 14 days", "412", ""), ("Dates confirmed", "383", "ok"), ("At risk", "23", "bad"), ("Chased today", "48", "")],
               [], rows, detail, "Chased 48 suppliers today")


def sc_onboard():
    rows = [
        ("SUP-1182", "Prism Components", "7 of 9 documents", pill("warn", "Bank check"), True),
        ("SUP-1181", "Ravel Plastics", "9 of 9", pill("ok", "Ready"), False),
        ("SUP-1179", "Nora Metalworks", "4 of 9", pill("warn", "Chased twice"), False),
        ("SUP-1176", "Ganga Logistics", "9 of 9", pill("bad", "GSTIN cancelled"), False),
        ("SUP-1175", "Ilango Coatings", "8 of 9", pill("warn", "Certificate expired"), False),
    ]
    docs = [("GST registration", "ok", "GSTIN active, legal name Prism Components Pvt Ltd"), ("PAN", "ok", "Matches the GST registration"),
            ("Bank letter", "bad", "Account name is Prism Holdings Pvt Ltd"), ("MSME certificate", "ok", "Udyam registered, small. Pay within 45 days"),
            ("ISO 9001 certificate", "ok", "Valid to Mar 2028, checked on the registry"), ("GST returns", "warn", "GSTR-1 not filed for October, asked why"),
            ("Quality questionnaire", "gray", "Waiting, sent 21 Nov")]
    dl = "".join(f'<div class="ck2 {k}"><i data-i="{"check" if k == "ok" else "triangle-alert" if k in ("bad", "warn") else "clock"}"></i><b>{n}</b><span>{t}</span></div>' for n, k, t in docs)
    detail = (dh("Prism Components Pvt Ltd", "Requested by S. Iyer for control boards · started 18 Nov", "warn", "Waiting on 2 items")
        + f'<div class="cklist">{dl}</div>'
        + '<div class="d-g2">'
        + box("Bank details", "<p>The account name on the bank letter is Prism Holdings Pvt Ltd, a different company from the one you are paying. The agent has asked Prism to explain, and the bank details stay locked until two people approve them.</p>", "warnb")
        + draft("vendors@prismcomponents.example", "Sent 09:40", "Thanks for the documents. The bank letter is in the name of Prism Holdings Pvt Ltd. Please send a letter for an account in the name of Prism Components Pvt Ltd, or a note on company letterhead explaining the link.")
        + "</div>" + acts("Approve bank details", "Reject", "Call supplier"))
    return app("app.vitalops.ai/vardhan/supplier-onboarding", "Vardhan Pumps", "Supplier onboarding",
               [("In progress", "11"), ("Ready", "3"), ("Blocked", "2"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("New suppliers this quarter", "38", ""), ("Average days to set up", "6", "ok"), ("Waiting on supplier", "9", "warn"), ("Blocked", "2", "bad")],
               [], rows, detail, "Checked GST portal 12 min ago")


def lg_audit():
    rows = [
        ("TI-88120", "Konkan Roadlines", "LR 30417", "₹53,590", pill("bad", "Disputed ₹4,300"), True),
        ("TI-88117", "Om Sai Transport", "LR 30402", "₹28,400", pill("ok", "Approved"), False),
        ("TI-88114", "Konkan Roadlines", "LR 30399", "₹61,250", pill("warn", "Diesel above clause"), False),
        ("TI-88109", "Pawan Carriers", "LR 30391", "₹18,900", pill("warn", "Extra drop not on LR"), False),
        ("TI-88101", "Om Sai Transport", "LR 30388", "₹33,100", pill("ok", "Approved"), False),
        ("TI-88097", "Harsh Logistics", "LR 30380", "₹44,200", pill("bad", "Duplicate of 88021"), False),
        ("TI-88093", "Pawan Carriers", "LR 30376", "₹21,750", pill("ok", "Approved"), False),
        ("TI-88090", "Konkan Roadlines", "LR 30371", "₹47,800", pill("ok", "Approved"), False),
    ]
    detail = f'''<div class="d-h"><div><b>Invoice TI-88120 · Konkan Roadlines</b><span>LR 30417 · Bhiwandi to Nagpur, 32 ft truck · delivered 21 Nov · rate contract RC-9921</span></div>{pill("bad", "₹4,300 disputed")}</div>
<table class="d-t"><thead><tr><th>Charge</th><th>Billed</th><th>Contract</th><th>Evidence</th><th></th></tr></thead><tbody>
<tr><td>Freight</td><td>₹46,500</td><td>₹46,500</td><td>Rate contract RC-9921</td><td>{pill("ok", "OK")}</td></tr>
<tr><td>Diesel escalation 6%</td><td>₹2,790</td><td>₹2,790</td><td>Diesel clause, Mumbai price on 1 Nov</td><td>{pill("ok", "OK")}</td></tr>
<tr class="bad"><td>Halting, 1 day</td><td>₹2,500</td><td>₹0</td><td>Gate log: on site 6 h 40 min, 24 h free</td><td>{pill("bad", "Dispute")}</td></tr>
<tr class="bad"><td>Unloading</td><td>₹1,800</td><td>₹0</td><td>Contract: unloading by consignee</td><td>{pill("bad", "Dispute")}</td></tr>
</tbody></table>
<div class="d-g2 mt">
 <div class="d-box"><span class="d-k">Time at the Nagpur DC, from the gate log</span>
  <div class="gl"><div class="gl-free" style="left:4%;width:84%"><span>Free time 24 h</span></div><div class="gl-on" style="left:4%;width:23%"></div><b style="left:4%">In 10:05</b><b class="r" style="left:27%">Out 16:45</b></div>
  <p>The truck left the same day, well inside the free time, so no halting charge is owed.</p></div>
 <div class="d-box"><span class="d-k">Payment</span><div class="pay"><div><span>Billed</span><b>₹53,590</b></div><div><span>Approved to pay</span><b class="ok">₹49,290</b></div><div><span>Held</span><b class="bad">₹4,300</b></div></div><p class="d-m">The transporter has 14 days to respond under the contract.</p></div>
</div>
<div class="d-draft"><div class="dr-h"><span>To: billing@konkanroadlines.example</span><span class="att"><i data-i="file-text"></i>gate-log-LR30417.pdf <i data-i="file-text"></i>RC-9921.pdf</span></div><p>Invoice TI-88120 for LR 30417: we are paying ₹49,290 and disputing ₹4,300. The gate log shows the truck at our Nagpur DC from 10:05 to 16:45 the same day, inside the 24 hours of free time, and our contract puts unloading on the consignee. Both documents are attached.</p></div>
<div class="d-acts"><span class="b1">Send dispute</span><span>Pay in full</span><span>Edit draft</span></div>'''
    return app("app.vitalops.ai/tarang/freight-audit", "Tarang Logistics", "Freight audit",
               [("To check", "46"), ("Approved", "1,704"), ("Disputed", "131"), ("Rate contracts", "22"), ("Transporters", ""), ("Audit log", ""), ("Reports", ""), ("Settings", "")],
               [("Invoices this week", "1,912", ""), ("Paid as billed", "1,704", "ok"), ("Disputed", "131", "bad"), ("Recovered this month", "₹6,84,200", "ok")],
               ["Invoice", "Transporter", "LR", "Billed"], rows, detail, "Read transporter emails 4 min ago")


def lg_pod():
    rows = [
        ("LR 30417", "Nagpur DC", "Driver photo 15:02", pill("warn", "Short 2 cartons"), True),
        ("LR 30415", "Bharat Retail, store 12", "Driver photo 14:40", pill("ok", "Released"), False),
        ("LR 30411", "Kailash Marine", "Scan 14:05", pill("ok", "Released"), False),
        ("LR 30409", "Pillai Builders", "Driver photo 13:30", pill("bad", "No stamp"), False),
        ("LR 30406", "Pune DC", "Driver photo 12:55", pill("ok", "Released"), False),
        ("LR 30402", "Noor Fabrication", "Driver photo 12:10", pill("warn", "Damage noted"), False),
    ]
    pod = ('<div class="podp"><div class="pp-h"><b>LORRY RECEIPT · POD COPY</b><span>Konkan Roadlines · LR 30417</span></div>'
           '<div class="dd-r"><span>Consignee</span><b>Tarang, Nagpur DC</b></div><div class="dd-r"><span>Packages</span><b>24 plt / 960 ctn</b></div>'
           '<div class="dd-r"><span>E-way bill</span><b>2718 4410 9921</b></div><div class="pp-hand">short 2 ctn SKU 44120<br>rcvd 958 · door 12</div><div class="pp-sig">J. More 21/11</div></div>')
    detail = (dh("LR 30417 · Nagpur DC", "POD photo from the driver app, 15:02 · invoice waiting on proof of delivery", "warn", "Exception")
        + '<div class="d-g2">' + f'<div>{pod}</div>'
        + '<div class="d-col"><span class="d-k">Read from the POD</span>'
        + table(["Field", "Value", ""], [["Signed by", "J. More", ("OK", "okc")], ["Stamp", "Tarang Nagpur DC", ("OK", "okc")], ["E-way bill", "Matches the invoice", ("OK", "okc")], ["Received", ("958 of 960 ctn", "dif"), ("Check", "dif")], ["Note", ("short 2 ctn SKU 44120", "dif"), ""]])
        + "</div></div>"
        + '<div class="d-g2">' + box("Billing", "<p>Load released for invoicing at 958 cartons. Customer invoice INV-77120 drafted for ₹1,76,540, 2 cartons less than ordered.</p>")
        + box("Shortage claim", "<p>Claim OSD-3391 opened against Konkan Roadlines for 2 cartons of SKU 44120, ₹7,180, with the photo and the LR attached.</p>") + "</div>"
        + acts("Send claim to transporter", "Release in full", "Open load"))
    return app("app.vitalops.ai/tarang/delivery-closeout", "Tarang Logistics", "Delivery close-out",
               [("Exceptions", "9"), ("Released", "214"), ("Missing POD", "12"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Loads delivered today", "236", ""), ("Released for billing", "214", "ok"), ("Exceptions", "9", "warn"), ("Average days to invoice", "0.4", "ok")],
               [], rows, detail, "Read driver app 1 min ago")


def lg_quote():
    rows = [
        ("RFQ-6120", "Bharat Retail", "Bhiwandi to Bengaluru", pill("ok", "Quoted"), True),
        ("RFQ-6119", "Pillai Builders", "Chennai to Hyderabad", pill("ok", "Quoted"), False),
        ("RFQ-6118", "Kailash Marine", "Mundra to Ludhiana", pill("warn", "Hazardous goods"), False),
        ("RFQ-6117", "Lakshmi Pumps", "Coimbatore to Pune", pill("ok", "Quoted"), False),
        ("RFQ-6115", "Noor Fabrication", "Indore to Jaipur", pill("warn", "Below margin floor"), False),
        ("RFQ-6114", "Bharat Retail", "Bhiwandi to Ahmedabad", pill("ok", "Won"), False),
    ]
    mail = ('<div class="d-mail"><div class="dm-h"><b>Rate request</b><span>logistics@bharatretail.example · 09:41</span></div>'
            '<p>hi, need rate for <mark>14 pallets</mark>, approx <mark>7.6 tonnes</mark>, <mark>Bhiwandi warehouse to our Bengaluru DC</mark>, loading <mark>Thursday</mark>, <mark>closed body</mark> only. pls share asap</p></div>')
    calc = table(["Item", "Amount"], [["Freight, 32 ft closed, 985 km", "₹54,000"], ["Diesel escalation 6%", "₹3,240"], ["Loading at Bhiwandi", "₹1,500"], ["Total before GST", "₹58,740", "@tot"]])
    detail = (dh("RFQ-6120 · Bharat Retail", "Email, 09:41 · quoted 09:42 · rep: A. Lele", "ok", "Quoted in 1 min")
        + '<div class="d-g2">' + mail
        + '<div class="d-col"><span class="d-k">Read</span><div class="codes"><div><span>Route</span><b>Bhiwandi to Bengaluru</b></div><div><span>Load</span><b>14 plt, 7.6 t</b></div><div><span>Loading</span><b>Thu 27 Nov</b></div><div><span>Truck</span><b>32 ft closed</b></div></div></div>'
        + "</div>"
        + '<div class="d-g2">' + box("Price from your rate table", calc) + box("Margin", '<div class="pay"><div><span>Truck cost</span><b>₹49,500</b></div><div><span>Margin</span><b class="ok">15.7%</b></div><div><span>Floor</span><b>12%</b></div></div><p class="d-m">Above the floor, so the agent sent the quote.</p>') + "</div>"
        + draft("logistics@bharatretail.example", "Sent 09:42", "Thanks for the request. 14 pallets, Bhiwandi to your Bengaluru DC, loading Thursday 27 Nov in a 32 ft closed truck: ₹58,740 plus GST. Reply to book and we will send the truck number the day before.")
        + acts("Open in TMS", "Revise quote"))
    return app("app.vitalops.ai/tarang/quotes", "Tarang Logistics", "Quote requests",
               [("New", "6"), ("Quoted", "88"), ("For a rep", "5"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Requests today", "99", ""), ("Quoted by the agent", "88", "ok"), ("Sent to a rep", "11", "warn"), ("Median time to quote", "2 min", "ok")],
               [], rows, detail, "Read quotes inbox 30 s ago")


def fi_ap():
    rows = [
        ("INV-30981", "Mehta Castings", "₹13,92,400", pill("warn", "Quantity differs"), True),
        ("INV-30979", "Sai Seals", "₹2,72,580", pill("ok", "Posted"), False),
        ("INV-30977", "Vela Steel", "₹57,70,200", pill("ok", "Posted"), False),
        ("INV-30975", "Hosur Fasteners", "₹1,03,840", pill("bad", "No PO"), False),
        ("INV-30972", "Arya Bearings", "₹7,52,250", pill("warn", "Price above PO"), False),
        ("INV-30970", "Prism Components", "₹3,68,160", pill("warn", "Not in GSTR-2B"), False),
    ]
    detail = (dh("INV-30981 · Mehta Castings · ₹13,92,400", "PDF from ar@mehtacastings.example, 08:02 · due 24 Dec · PO-48190 · receipt GR-6120", "warn", "On hold")
        + table(["Line", "Item", "Invoiced", "Ordered", "Received", "Price", ""], [["1", "Pump housing PH-40", ("500", "dif"), "500", ("480", "dif"), "₹2,360", ("20 not received", "dif")], ["2", "Freight", "1", "1", "1", "₹0", ("OK", "okc")], ["", "GST 18%", "", "", "", "₹2,12,400", ("In GSTR-2B", "okc")]])
        + '<div class="d-g2">' + box("Why it's on hold", "<p>Goods receipt GR-6120 shows 480 housings. The delivery challan also says 480, with 20 to follow. The invoice bills all 500.</p>")
        + box("What the agent did", "<p>Posted ₹11,32,800 plus GST for the 480 received. Held ₹47,200 plus GST and asked Mehta for a credit note for the 20.</p>") + "</div>"
        + draft("ar@mehtacastings.example", "Sent 08:05", "Invoice INV-30981 bills 500 housings on PO-48190, and we received 480. We have approved ₹11,32,800 plus GST and will pay for the other 20 when they arrive. Please send a credit note for ₹47,200 plus GST or reissue the invoice.")
        + acts("Approve as posted", "Pay in full", "Open PO"))
    return app("app.vitalops.ai/aravali/payables", "Aravali Metals", "Supplier invoices",
               [("To check", "18"), ("Posted", "342"), ("No PO", "4"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Invoices today", "364", ""), ("Matched and posted", "342", "ok"), ("Exceptions", "22", "warn"), ("Average days to post", "0.3", "ok")],
               [], rows, detail, "Read AP inbox 2 min ago")


def fi_cash():
    rows = [
        ("NEFT 77120", "Arjun Steel", "₹12,46,737", pill("warn", "Posted · ₹15,000 deduction"), True),
        ("RTGS 5512", "Pillai Builders", "₹48,00,000", pill("ok", "Posted"), False),
        ("NEFT 77131", "Noor Fabrication", "₹9,31,240", pill("warn", "Remittance asked"), False),
        ("Cheque 2290", "Kailash Marine", "₹3,88,000", pill("ok", "Posted"), False),
        ("NEFT 77140", "Kohli Metals", "₹15,20,000", pill("bad", "Overpaid ₹20,000"), False),
        ("NEFT 77142", "Pillai Builders", "₹6,11,575", pill("ok", "Posted"), False),
        ("RTGS 5519", "Sangam Rail", "₹71,94,000", pill("ok", "Posted"), False),
        ("NEFT 77150", "Kailash Marine", "₹2,25,000", pill("ok", "Posted"), False),
    ]
    detail = f'''<div class="d-h"><div><b>NEFT 77120 · Arjun Steel · ₹12,46,737</b><span>Bank line 24 Nov · remittance by email from ap@arjunsteel.example, 23 Nov 17:02</span></div>{pill("warn", "Deduction routed")}</div>
<div class="d-g2">
 <div class="d-mail"><div class="dm-h"><b>Payment advice</b><span>Arjun Steel accounts payable</span></div><p>Paid 24 Nov by NEFT, total 12,46,737.00</p><p class="mono">INV-3310 &nbsp; 5,20,000.00<br>INV-3318 &nbsp; 4,88,000.00<br>INV-3325 &nbsp; <mark>2,40,000.00 PRICE ADJ</mark><br>TDS 194Q &nbsp; -1,263.00</p></div>
 <div><span class="d-k">Match</span><table class="d-t"><thead><tr><th>Invoice</th><th>Open ₹</th><th>Paid ₹</th><th>Short ₹</th></tr></thead><tbody>
 <tr><td>INV-3310</td><td>5,20,000</td><td>5,20,000</td><td>0</td></tr><tr><td>INV-3318</td><td>4,88,000</td><td>4,88,000</td><td>0</td></tr><tr><td>INV-3325</td><td>2,55,000</td><td>2,40,000</td><td class="dif">15,000</td></tr>
 <tr><td>TDS 0.1%</td><td></td><td>1,263</td><td class="okc">OK</td></tr>
 <tr class="tot"><td>Total</td><td>12,63,000</td><td>12,48,000</td><td>15,000</td></tr></tbody></table></div>
</div>
<div class="d-g2 mt">
 <div class="d-box"><span class="d-k">Deduction</span><p>Reason PRICE ADJ. Sales opened price dispute <b>case 4471</b> on 2 Nov for INV-3325, for ₹15,000. Routed to collections with the case attached. The TDS is booked for checking against Form 26AS.</p></div>
 <div class="d-box"><span class="d-k">Entry posted</span><table class="je"><tr><td>Dr Bank</td><td>12,46,737</td><td></td></tr><tr><td>Dr TDS receivable</td><td>1,263</td><td></td></tr><tr><td>Dr Deductions</td><td>15,000</td><td></td></tr><tr><td>Cr Receivables, Arjun</td><td></td><td>12,63,000</td></tr></table></div>
</div>
<div class="d-acts"><span class="b1">Open case 4471</span><span>Reverse posting</span><span>View remittance</span></div>'''
    return app("app.vitalops.ai/aravali/cash-application", "Aravali Metals", "Cash application",
               [("Bank lines", "412"), ("Posted", "371"), ("Deductions", "26"), ("Unapplied", "15"), ("Customers", ""), ("Audit log", ""), ("Reports", ""), ("Settings", "")],
               [("Payments today", "412", ""), ("Matched and posted", "371", "ok"), ("Deductions", "26", "warn"), ("Unapplied cash", "₹4,18,800", "bad")],
               ["Bank line", "Customer", "Amount"], rows, detail, "Read bank statement 6 min ago")


def fi_close():
    rows = [
        ("1010", "Current account", "1,912 lines", pill("ok", "Reconciled"), False),
        ("1012", "Salary account", "214 lines", pill("ok", "Reconciled"), False),
        ("1020", "Collections account", "3,480 lines", pill("warn", "3 breaks"), True),
        ("1310", "Intercompany, Aravali FZE", "96 lines", pill("bad", "Out by ₹3,42,000"), False),
        ("2010", "AP sub-ledger", "2,240 lines", pill("ok", "Reconciled"), False),
        ("1210", "AR sub-ledger", "2,980 lines", pill("ok", "Reconciled"), False),
    ]
    breaks = [["Cheque 30 Nov ₹8,12,000", "Ledger only", "In clearing, credited 1 Dec", ("Timing", "okc")],
              ["Bank charges ₹531", "Bank only", "₹450 plus GST, missing in ledger", ("Entry", "dif")],
              ["NEFT 77142 ₹6,11,575", "Ledger twice", "Posted twice on 26 Nov", ("Reverse", "dif")]]
    detail = (dh("1020 · Collections account · November", "Bank statement to 30 Nov · ledger balance ₹12,84,90,612 · statement ₹12,70,66,506", "warn", "3 breaks, cause found")
        + '<div class="recon"><div><span>Lines matched</span><b>3,477 of 3,480</b></div><div><span>Difference</span><b>₹14,24,106</b></div><div><span>Explained</span><b class="ok">₹14,24,106</b></div></div>'
        + table(["Break", "Where", "Likely cause", ""], breaks)
        + '<div class="d-g2">' + box("Proposed entries", '<table class="je"><tr><td>Dr Bank charges</td><td>450.00</td><td></td></tr><tr><td>Dr GST input credit</td><td>81.00</td><td></td></tr><tr><td>Cr Bank, collections</td><td></td><td>531.00</td></tr><tr><td>Dr Receivables, Pillai</td><td>6,11,575</td><td></td></tr><tr><td>Cr Bank, collections</td><td></td><td>6,11,575</td></tr></table>')
        + box("Close progress", '<div class="prog"><i style="width:83%"></i></div><p>10 of 12 accounts reconciled. Intercompany with Aravali FZE is out by ₹3,42,000 and is with the controller.</p>') + "</div>"
        + acts("Post entries and sign off", "Edit", "Export workpaper"))
    return app("app.vitalops.ai/aravali/month-end", "Aravali Metals", "Month-end close",
               [("Breaks", "4"), ("Reconciled", "10"), ("Signed off", "8"), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
               [("Accounts", "12", ""), ("Reconciled", "10", "ok"), ("Open breaks", "4", "warn"), ("Day of close", "2", "")],
               [], rows, detail, "Matched bank statement 08:00")


# ── healthcare (India: cashless claims through TPAs) ──
HOSP = ("Meridian Multispeciality Hospital", "app.vitalops.ai/meridian")


def hc_preauth():
    rows = [
        ("IP-8812", "S. Deshpande", "Lap. cholecystectomy", "Sunrise TPA", pill("ok", "Query answered"), True),
        ("IP-8810", "A. Iyer", "Cataract, right eye", "Indus General", pill("ok", "Approved"), False),
        ("IP-8809", "M. Shaikh", "Knee arthroscopy", "Harbour TPA", pill("warn", "Note needed"), False),
        ("IP-8807", "R. Nair", "Angioplasty", "Sagar Health", pill("ok", "Submitted"), False),
        ("IP-8806", "P. Gupta", "Hernia repair", "Sunrise TPA", pill("bad", "Waiting period"), False),
        ("IP-8804", "K. Reddy", "Dengue, medical", "Harbour TPA", pill("ok", "Approved"), False),
        ("IP-8801", "V. Joshi", "Hysterectomy", "Indus General", pill("ok", "Submitted"), False),
    ]
    est = table(["Estimate", "Days", "Amount"], [
        ["Room, twin sharing", "3", "₹13,500"], ["Surgeon and OT", "", "₹52,000"], ["Anaesthesia", "", "₹12,000"],
        ["Investigations", "", "₹9,600"], ["Medicines and consumables", "", "₹21,300"], ["Total", "", "₹1,08,400", "@tot"]])
    detail = (dh("IP-8812 · S. Deshpande · laparoscopic cholecystectomy", "Dr. N. Kulkarni · admission 26 Nov · Indus General Health Optima via Sunrise TPA", "ok", "Query answered")
        + '<div class="steps"><div class="on"><i></i><b>Admission note</b><span>24 Nov 17:05</span></div><div class="on"><i></i><b>Policy checked</b><span>Covered</span></div>'
        '<div class="on"><i></i><b>Form sent</b><span>24 Nov 17:21</span></div><div class="on"><i></i><b>TPA query</b><span>25 Nov 10:02</span></div><div class="nx"><i></i><b>Approval</b><span>expected today</span></div></div>'
        + '<div class="d-g2">' + f'<div><span class="d-k">Cost estimate sent</span>{est}</div>'
        + '<div class="d-col"><span class="d-k">Policy</span>'
        '<div class="ck2 ok"><i data-i="check"></i><b>Sum insured</b><span>₹5,00,000, ₹4,62,000 left this year</span></div>'
        '<div class="ck2 ok"><i data-i="check"></i><b>Room rent limit</b><span>₹5,000 a day, twin sharing is ₹4,500</span></div>'
        '<div class="ck2 ok"><i data-i="check"></i><b>2 year wait for gallbladder</b><span>Policy since March 2023, met</span></div>'
        '<div class="ck2 ok"><i data-i="check"></i><b>Co-pay</b><span>None on this policy</span></div></div></div>'
        + '<div class="crit"><div class="cr"><span class="cr-n">' + pill("ok", "Answered 10:09") + '<b>TPA query: send ultrasound report and how long the symptoms have lasted</b></span>'
        '<q>Ultrasound abdomen, 22 Nov: multiple gallstones, largest 11 mm. OPD note, 18 Nov: pain after meals for 3 months.</q><em>Both from the hospital record, uploaded to the Sunrise portal</em></div></div>'
        + acts("Open in HIS", "View TPA portal", "Message desk"))
    return app(f"{HOSP[1]}/pre-auth", HOSP[0], "Cashless pre-authorisation",
               [("Worklist", "27"), ("Approved", "164"), ("TPA queries", "9"), ("Policies", ""), ("TPAs", ""), ("Audit log", ""), ("Reports", ""), ("Settings", "")],
               [("Planned admissions", "27", ""), ("Sent within 30 min", "25", "ok"), ("Open TPA queries", "9", "warn"), ("Not covered", "2", "bad")],
               ["Admission", "Patient", "Procedure", "TPA"], rows, detail, "Read admission notes 2 min ago")


def hc_discharge():
    rows = [
        ("IP-8779", "L. Fernandes", "Bed 412", pill("warn", "₹31,150 to pay"), True),
        ("IP-8781", "H. Singh", "Bed 207", pill("ok", "Approved"), False),
        ("IP-8783", "T. Menon", "Bed 318", pill("ok", "Sent to TPA"), False),
        ("IP-8776", "D. Bose", "Bed 109", pill("gray", "Summary not signed"), False),
        ("IP-8785", "N. Pillai", "Bed 221", pill("ok", "Approved"), False),
        ("IP-8772", "F. Ansari", "Bed 330", pill("warn", "More cover asked"), False),
    ]
    bill = table(["Bill item", "Billed", "Payable", ""], [
        ["Room, single, 4 days", "₹18,000", ("₹12,000", "dif"), "limit"],
        ["Nursing", "₹6,000", ("₹4,000", "dif"), "pro rata"],
        ["Doctor visits", "₹8,400", ("₹5,600", "dif"), "pro rata"],
        ["Surgeon and OT", "₹54,000", ("₹36,000", "dif"), "pro rata"],
        ["Medicines and consumables", "₹14,200", "₹14,200", ""],
        ["Investigations", "₹9,800", "₹9,800", ""],
        ["Gloves, masks, admission kit", "₹2,350", ("₹0", "dif"), "not payable"],
        ["Total", "₹1,12,750", "₹81,600", "", "@tot"]])
    detail = (dh("IP-8779 · L. Fernandes · appendicectomy", "Discharge summary signed 10:12 · Sagar Health via Harbour TPA · pre-auth ₹90,000", "warn", "Family told")
        + '<div class="steps"><div class="on"><i></i><b>Summary signed</b><span>10:12</span></div><div class="on"><i></i><b>Bill checked</b><span>10:18</span></div>'
        '<div class="on"><i></i><b>Sent to TPA</b><span>10:21 · 9 files</span></div><div class="on"><i></i><b>Family told</b><span>10:40</span></div><div class="nx"><i></i><b>Final approval</b><span>usually 2 h</span></div></div>'
        + bill
        + box("Why the family pays ₹31,150", "<p>The policy pays room rent up to <b>₹3,000 a day</b>. The patient chose a ₹4,500 room, so the insurer pays two thirds of room-linked charges. Billing told the family at 10:40.</p>", "mt")
        + acts("Open bill", "Ask TPA for more cover", "View files sent"))
    return app(f"{HOSP[1]}/discharge", HOSP[0], "Cashless discharge",
               [("Discharges today", "23"), ("Approved", "15"), ("With TPA", "6"), ("Room limits", ""), ("TPAs", ""), ("Audit log", ""), ("Reports", ""), ("Settings", "")],
               [("Discharges today", "23", ""), ("Sent within 15 min", "21", "ok"), ("Waiting on TPA", "6", "warn"), ("Average wait", "1 h 50 m", "")],
               ["Admission", "Patient", "Bed"], rows, detail, "Read signed summaries 1 min ago")


def hc_settle():
    rows = [
        ("NEFT 8841", "Indus General", "12 claims", "₹9,77,600", pill("warn", "1 dispute drafted"), True),
        ("NEFT 8838", "Sagar Health", "7 claims", "₹4,12,650", pill("ok", "Matched"), False),
        ("NEFT 8836", "Harbour TPA", "3 claims", "₹1,96,000", pill("warn", "Letter missing"), False),
        ("NEFT 8831", "Indus General", "9 claims", "₹6,70,120", pill("ok", "Matched"), False),
        ("NEFT 8829", "Sunrise TPA", "1 claim", "₹38,400", pill("bad", "No claim found"), False),
        ("NEFT 8826", "Sagar Health", "5 claims", "₹2,88,900", pill("ok", "Matched"), False),
    ]
    lines = table(["Claim", "Claimed", "Paid", "Deduction", "Reason given", "Check"], [
        ["CL-50412", "₹1,45,000", "₹1,38,200", ("₹6,800", "dif"), "Package rate", ("Wrong", "dif")],
        ["CL-50398", "₹74,900", "₹72,550", "₹2,350", "Non-payable items", ("Correct", "okc")],
        ["CL-50377", "₹62,400", "₹56,160", "₹6,240", "10% co-pay", ("Correct", "okc")],
        ["9 more", "₹7,10,690", "₹7,10,690", "₹0", "", ("Correct", "okc")],
        ["Total", "₹9,92,990", "₹9,77,600", "₹15,390", "", "", "@tot"]])
    detail = (dh("NEFT 8841 · Indus General · ₹9,77,600", "Bank credit 24 Nov · 12 settlement letters from the insurer's email, 23 Nov", "warn", "Dispute to approve")
        + lines
        + '<div class="d-g2 mt">' + box("Package rate, CL-50412", "<p>Knee arthroscopy is <b>₹1,45,000</b> in the tariff agreed with Indus General from 1 Apr 2026. They paid the old 2025 rate.</p>")
        + draft("claims@indusgeneral.example", "Draft", "Claim CL-50412 was settled at the 2025 package rate. Our 2026 tariff, annexure B page 4, sets knee arthroscopy at ₹1,45,000. Please pay the balance of ₹6,800.")
        + "</div>" + acts("Approve and send", "Edit draft", "Accept deduction"))
    return app(f"{HOSP[1]}/settlements", HOSP[0], "Claim settlements",
               [("Payments", "38"), ("Matched", "31"), ("Disputes", "5"), ("Tariffs", ""), ("Insurers", ""), ("Audit log", ""), ("Reports", ""), ("Settings", "")],
               [("Settled this month", "₹1.42 Cr", ""), ("Matched to claims", "31 of 38", "ok"), ("Wrong deductions", "₹1,18,400", "warn"), ("Recovered", "₹86,200", "ok")],
               ["Payment", "Insurer", "Claims", "Amount"], rows, detail, "Read bank statement 08:00")


SCREENS = {"manufacturing": [mfg_certs, mfg_orders, mfg_maint], "supply-chain": [sc_acks, sc_late, sc_onboard],
           "logistics": [lg_audit, lg_pod, lg_quote], "healthcare": [hc_preauth, hc_discharge, hc_settle],
           "finance": [fi_ap, fi_cash, fi_close]}
