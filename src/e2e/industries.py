"""Industry tabs for the /e2e page. build.py renders this into __INDUSTRIES__.

Each industry has a photo, an app screen (screens.py) and three jobs. Keep the copy plain: run the build, which runs the copy checker.
"""
from html import escape as e

INDUSTRIES = [
    {
        "id": "manufacturing", "icon": "factory", "name": "Manufacturing",
        "who": "Plants and contract manufacturers: quality, customer service, planning and maintenance teams.",
        "systems": ["ERP", "MES", "Quality system", "Maintenance system", "Customer and supplier email"],
        "jobs": [
            ("Checking incoming material certificates",
             "Quality staff open each supplier's certificate of analysis or mill test report and compare every value with the spec before a lot can be released.",
             "Reads the certificate, finds the receipt and the spec, checks each value against its limits and releases conforming lots in the ERP.",
             "QA decides on anything out of spec, missing or unreadable."),
            ("Entering customer orders",
             "Customer service retypes purchase orders from PDFs and emails into the ERP, then checks part numbers, prices and requested dates by hand.",
             "Enters the order, maps the customer's part numbers to yours, checks prices against the contract and dates against lead times, and sends the confirmation.",
             "Customer service handles price differences, unknown parts and dates you can't meet."),
            ("Coding maintenance work orders",
             "Technicians close work orders with notes like “replaced brg, motor running hot again”. Nobody codes them, so repeat failures go unnoticed.",
             "Reads closed work orders, assigns asset, failure and cause codes, and lists assets that keep failing.",
             "The reliability engineer decides what to do about each repeat failure."),
        ],
    },
    {
        "id": "supply-chain", "icon": "boxes", "name": "Supply chain",
        "who": "Buyers, planners and supplier managers in companies that buy from hundreds of suppliers.",
        "systems": ["ERP", "Planning system", "Supplier portals", "Supplier email", "GST portal"],
        "jobs": [
            ("Checking order acknowledgements",
             "Suppliers confirm orders by email or portal, often with a changed date, quantity or price. Buyers are meant to compare each one with the PO, and many replies are never read.",
             "Reads every acknowledgement, compares it line by line with the PO, updates confirmed dates in the ERP and chases suppliers who haven't replied.",
             "The buyer sees only changed lines, with the orders they affect."),
            ("Following up late deliveries",
             "Planners work through a long list of late and at-risk lines each morning and email suppliers one at a time for a new date.",
             "Asks each supplier for a date, records the answer, and shows which production and customer orders are affected.",
             "The planner decides whether to expedite, buy elsewhere or reschedule."),
            ("Onboarding new suppliers",
             "New suppliers send GST and PAN details, bank letters, MSME and quality certificates in any order, and someone chases the missing pieces for weeks.",
             "Checks each document for completeness and expiry dates, checks the GSTIN is active and returns are filed, chases what's missing and sets up the vendor record.",
             "Two people approve any new or changed bank details."),
        ],
    },
    {
        "id": "logistics", "icon": "truck", "name": "Logistics",
        "who": "Transport companies, 3PLs, freight forwarders and the logistics teams of manufacturers.",
        "systems": ["TMS", "WMS", "E-way bill portal", "Rate tables", "Driver apps and email"],
        "jobs": [
            ("Auditing transporter invoices",
             "Transporter invoices come with diesel escalation and extra charges for halting, loading and unloading. Checking each one against the contract takes time, so many are paid as billed.",
             "Matches each invoice to the load and the contracted rate, checks every extra charge against gate times and delivery notes, and disputes unsupported ones.",
             "Your team approves disputes above an amount you set."),
            ("Closing out deliveries",
             "Signed LR copies come back as phone photos. Billing waits until someone matches each one to a load and writes up any shortage or damage noted on it.",
             "Reads the signed LR, matches it to the load and e-way bill, records shortages and damage written on it, and releases the load for invoicing.",
             "Claims for shortage and damage stay with your claims team."),
            ("Answering quote requests",
             "Customers email and WhatsApp rate requests with routes, weights and dates in free text. Sales reps retype them into the TMS before they can price.",
             "Pulls out route, weight, truck size and dates, prices standard routes from your rate tables and drafts the reply.",
             "Reps handle unusual freight and anything below your margin floor."),
        ],
    },
    {
        "id": "healthcare", "icon": "stethoscope", "name": "Healthcare",
        "who": "Hospitals and hospital chains: insurance desk, billing and revenue teams.",
        "systems": ["Hospital information system", "TPA and insurer portals", "NHCX", "Insurance desk email", "Bank statements"],
        "jobs": [
            ("Cashless pre-authorisation",
             "The insurance desk fills a different pre-auth form for each TPA, attaches notes and a cost estimate, uploads it, then answers queries while the patient waits to be admitted.",
             "Checks the policy, fills the TPA's form from the hospital record, submits it and answers routine queries with reports already in the system.",
             "Doctors answer clinical queries. The desk tells the patient about anything the policy won't cover."),
            ("Cashless discharge",
             "Once the discharge summary is signed, staff send the final bill to the TPA and wait hours for approval. The patient waits too, and the bed stays full.",
             "Sends the final bill and reports as soon as the summary is signed, and works out deductions for room rent limits and non-payable items so the family hears early.",
             "Billing explains deductions to the family and asks the TPA for more cover when needed."),
            ("Reconciling claim settlements",
             "Insurers pay many claims in one bank transfer. Accounts match each payment to claims by hand, and wrong deductions are rarely challenged.",
             "Matches each payment to its claims, reads the settlement letters, checks every deduction against your tariff agreement and the policy, and drafts disputes.",
             "The revenue team approves each dispute before it goes out."),
        ],
    },
    {
        "id": "finance", "icon": "landmark", "name": "Finance",
        "who": "Payables, receivables and accounting teams, in any industry.",
        "systems": ["ERP and ledger", "Bank statements", "AP inbox", "GST portal", "Spreadsheets"],
        "jobs": [
            ("Processing supplier invoices",
             "AP staff key invoices from PDFs, match them to the order and the goods receipt, and check GSTR-2B before claiming input credit. Mismatches sit in someone's inbox.",
             "Reads the invoice, matches it to the PO, the receipt and GSTR-2B, posts it when they agree and explains the difference when they don't.",
             "AP approves exceptions. Two people approve any bank detail change."),
            ("Applying customer payments",
             "Payments arrive by NEFT, RTGS or cheque, with the remittance in an email or a line of bank text. TDS, short payments and deductions are matched by hand.",
             "Matches each payment to invoices, including TDS, partial payments and deductions, and posts it.",
             "Collections decides on disputed deductions."),
            ("Month-end reconciliations",
             "Bank, intercompany and sub-ledger reconciliations are done in spreadsheets in the last days of the month.",
             "Matches lines every day, and for each break proposes a likely cause with the entries behind it.",
             "The controller reviews the breaks and signs off."),
        ],
    },
]


SHOW_PHOTOS = True

PHOTOS = {  # id: file in e2e/img. All from Unsplash, whose licence needs no credit; we show one anyway.
    "manufacturing": "manufacturing.webp", "supply-chain": "supply-chain.webp", "logistics": "logistics.webp",
    "healthcare": "healthcare.webp", "finance": "finance.webp",
}
PHOTO_POS = {"finance": "65% 0"}  # where to anchor the crop, when the middle is wrong


def render():
    from screens import SCREENS
    tabs, panels = [], []
    for i, ind in enumerate(INDUSTRIES):
        sel = "true" if i == 0 else "false"
        tabs.append(f'<button role="tab" id="tab-{ind["id"]}" aria-controls="{ind["id"]}" aria-selected="{sel}"><i data-i="{ind["icon"]}"></i>{e(ind["name"])}</button>')
        jobs = "".join(
            f'<div class="jrow{" flip" if k % 2 else ""}"><div class="jtext"><span class="jn">{k + 1:02d}</span><h4>{e(t)}</h4>'
            f'<div class="jr today"><span class="jl"><i data-i="clock"></i>Today</span><p>{e(a)}</p></div>'
            f'<div class="jr agent"><span class="jl"><i data-i="bot"></i>The agent</span><p>{e(b)}</p></div>'
            f'<div class="jr person"><span class="jl"><i data-i="user-check"></i>Your team</span><p>{e(c)}</p></div></div>'
            f'<div class="jshot"><div class="screen" data-w="860" role="img" aria-label="Mock of the VitalOps app: {e(t.lower())}"><div class="screen-in">{SCREENS[ind["id"]][k]()}</div></div></div></div>'
            for k, (t, a, b, c) in enumerate(ind["jobs"])
        )
        chips = "".join(f"<em>{e(x)}</em>" for x in ind["systems"])
        img = PHOTOS[ind["id"]]
        credit = '<span class="ph-c" tabindex="0" aria-label="Photo from Unsplash"><i data-i="info"></i><span>Photo: Unsplash</span></span>'
        hidden = "" if i == 0 else " hidden"
        photo = f'<div class="ind-ph"><img src="img/{img}" alt="" loading="lazy"{f' style="object-position:{PHOTO_POS[ind["id"]]}"' if ind["id"] in PHOTO_POS else ""}>{credit}</div>' if SHOW_PHOTOS else ""
        nocls = "" if SHOW_PHOTOS else " nophoto"
        panels.append(
            f'<div class="ind" role="tabpanel" id="{ind["id"]}" aria-labelledby="tab-{ind["id"]}"{hidden}>'
            f'<div class="ind-h{nocls}">{photo}'
            f'<div class="ind-t"><span class="ind-ic"><i data-i="{ind["icon"]}"></i></span><h3>{e(ind["name"])}</h3><p>{e(ind["who"])}</p>'
            f'<div class="ind-sys"><span>Systems we connect to</span><div>{chips}</div></div></div></div>'
            f'<div class="jobs">{jobs}</div></div>'
        )
    return f'<div class="tabs-ind" role="tablist" aria-label="Industries">{"".join(tabs)}</div>' + "".join(panels)
