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
        "systems": ["ERP", "Planning system", "Supplier portals", "Supplier email", "Sanctions lists"],
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
             "New suppliers send tax forms, bank details, insurance and quality certificates in any order, and someone chases the missing pieces for weeks.",
             "Checks each document for completeness and expiry dates, screens the company against sanctions lists, chases what's missing and sets up the vendor record.",
             "Two people approve any new or changed bank details."),
        ],
    },
    {
        "id": "logistics", "icon": "truck", "name": "Logistics",
        "who": "Freight forwarders, 3PLs, carriers and the transport teams of shippers.",
        "systems": ["TMS", "WMS", "Carrier portals", "Rate tables", "Driver apps and email"],
        "jobs": [
            ("Auditing freight invoices",
             "Carrier invoices come with fuel surcharges and extra charges for detention, liftgates and redelivery. Checking each one against the contract takes time, so many are paid as billed.",
             "Matches each invoice to the load and the contracted rate, checks every extra charge against gate times and delivery notes, and disputes unsupported ones.",
             "Your team approves disputes above an amount you set."),
            ("Closing out deliveries",
             "Signed delivery notes come back as phone photos. Billing waits until someone matches each one to a load and writes up any shortage or damage noted on it.",
             "Reads the delivery note, matches it to the load, records shortages and damage written on it, and releases the load for invoicing.",
             "Claims for shortage and damage stay with your claims team."),
            ("Answering quote requests",
             "Shippers email rate requests with lanes, weights and dates written in free text. Sales reps retype them into the TMS before they can price.",
             "Pulls out lane, weight, size and dates, prices standard lanes from your rate tables and drafts the reply.",
             "Reps handle unusual freight and anything below your margin floor."),
        ],
    },
    {
        "id": "healthcare", "icon": "stethoscope", "name": "Healthcare",
        "who": "Hospitals, clinic groups and specialty practices: patient access and revenue cycle teams.",
        "systems": ["EHR", "Practice management", "Insurer portals", "Fax and e-fax", "Remittance files"],
        "jobs": [
            ("Prior authorisations",
             "Staff check whether a procedure needs the insurer's approval, gather clinical notes, fill in each insurer's form or portal, then call back to check on it.",
             "Checks the insurer's rules for the procedure, pulls the relevant notes from the record, submits the request and tracks it until the insurer decides.",
             "Clinical questions go to the clinician. Denials go to your appeals team."),
            ("Working denied claims",
             "Denials come back as codes in remittance files. Staff look up each one, work out whether it can be fixed, and rework or appeal it before the insurer's deadline.",
             "Groups denials by reason, corrects clerical errors such as a wrong member ID, resubmits, and drafts appeal letters with the supporting records.",
             "A coder or the appeals team approves every correction and appeal."),
            ("Taking in referrals",
             "Referrals still arrive by fax. Someone reads each one, finds or creates the patient, checks insurance eligibility and calls to schedule.",
             "Reads the referral, matches the patient, checks eligibility with the insurer, asks the referring office for anything missing and adds the patient to the scheduling list.",
             "Schedulers book the visit. Clinical triage stays with clinicians."),
        ],
    },
    {
        "id": "insurance", "icon": "shield", "name": "Insurance",
        "who": "Carriers, MGAs and brokers: underwriting, claims and account management teams.",
        "systems": ["Policy admin", "Rating tools", "Claims system", "Broker email", "Document stores"],
        "jobs": [
            ("Clearing new submissions",
             "Brokers send ACORD forms, schedules of values and loss runs in every format. Assistants key them into the rating tool before an underwriter can look at the risk.",
             "Reads every attachment, builds the risk record, checks it against your appetite and lists what's missing.",
             "The underwriter decides whether to quote and at what price."),
            ("Opening new claims",
             "First notice of loss arrives by email with photos, police reports and repair estimates. Handlers open the claim, find the policy and request missing documents by hand.",
             "Opens the claim, finds the policy, checks the cover dates, sorts the claim by type and size, and routes it to the right adjuster.",
             "Adjusters decide on cover and payment."),
            ("Checking issued policies",
             "Account managers compare each issued policy with the quote and binder, form by form, to catch wrong limits and missing endorsements.",
             "Compares every limit, deductible, form and endorsement and lists the differences.",
             "The account manager sends the correction request."),
        ],
    },
    {
        "id": "finance", "icon": "landmark", "name": "Finance",
        "who": "Payables, receivables and accounting teams, in any industry.",
        "systems": ["ERP and ledger", "Bank feeds", "AP inbox", "Customer remittances", "Spreadsheets"],
        "jobs": [
            ("Processing supplier invoices",
             "AP staff key invoices from PDFs and match them to the order and the goods receipt. Mismatches sit in someone's inbox.",
             "Reads the invoice, matches it to the PO and receipt, posts it when they agree and explains the difference when they don't.",
             "AP approves exceptions. Two people approve any bank detail change."),
            ("Applying customer payments",
             "Payments arrive with the remittance in an email, a PDF or a line of bank text. Short payments and deductions are matched by hand.",
             "Matches each payment to invoices, including partial payments and deductions, and posts it.",
             "Collections decides on disputed deductions."),
            ("Month-end reconciliations",
             "Bank, intercompany and sub-ledger reconciliations are done in spreadsheets in the last days of the month.",
             "Matches lines every day, and for each break proposes a likely cause with the entries behind it.",
             "The controller reviews the breaks and signs off."),
        ],
    },
]


SHOW_PHOTOS = False  # photos are off until we have good, modern ones

PHOTOS = {  # id: (file in e2e/img, credit, licence, source page)
    "manufacturing": ("manufacturing.webp", "Jorge Royan", "CC BY-SA 3.0", "https://commons.wikimedia.org/wiki/File:India_-_Varanasi_electric_fan_factory_-_1464.jpg"),
    "supply-chain": ("supply-chain.webp", "Prabhat1729", "CC BY-SA 4.0", "https://commons.wikimedia.org/wiki/File:CWC_Godown,_Bamanheri_operated_by_Food_Corporation_of_India_for_stocking_foodgrains.jpg"),
    "logistics": ("logistics.webp", "Andrew Thomas", "CC BY-SA 2.0", "https://commons.wikimedia.org/wiki/File:Truck,_Mumbai_-_India,_April_12_2014._(14101792825).jpg"),
    "healthcare": ("healthcare.webp", "Barry Pousman", "CC BY 2.0", "https://commons.wikimedia.org/wiki/File:My_nurses_at_the_hospital_in_Pondi_(6290972608).jpg"),
    "insurance": ("insurance.webp", "Dil Shad Roshan", "CC BY-SA 4.0", "https://commons.wikimedia.org/wiki/File:Flooded-home-companypady-2018-kerala-floods.jpg"),
    "finance": ("finance.webp", "VitalOps", "", ""),
}


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
        img, who, lic, src = PHOTOS[ind["id"]]
        credit = f'<a class="ph-c" href="{src}" target="_blank" rel="noopener" aria-label="Photo credit: {e(who)}, {lic}"><i data-i="info"></i><span>Photo: {e(who)}, {lic}</span></a>' if src else ""
        hidden = "" if i == 0 else " hidden"
        photo = f'<div class="ind-ph"><img src="img/{img}" alt="" loading="lazy">{credit}</div>' if SHOW_PHOTOS else ""
        nocls = "" if SHOW_PHOTOS else " nophoto"
        panels.append(
            f'<div class="ind" role="tabpanel" id="{ind["id"]}" aria-labelledby="tab-{ind["id"]}"{hidden}>'
            f'<div class="ind-h{nocls}">{photo}'
            f'<div class="ind-t"><span class="ind-ic"><i data-i="{ind["icon"]}"></i></span><h3>{e(ind["name"])}</h3><p>{e(ind["who"])}</p>'
            f'<div class="ind-sys"><span>Systems we connect to</span><div>{chips}</div></div></div></div>'
            f'<div class="jobs">{jobs}</div></div>'
        )
    return f'<div class="tabs-ind" role="tablist" aria-label="Industries">{"".join(tabs)}</div>' + "".join(panels)
