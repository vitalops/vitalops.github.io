"""Flag copy that reads as machine-written.

Usage: python3 src/tools/copy_tells.py desk/index.html [more.html ...]

Checks the visible text of a page (scripts, styles and <blockquote> client quotes are skipped, since
quotes are the client's own words). Exit code 1 if anything is found.

The tells, by kind:

 1. Dashes as punctuation: em dash, en dash, or a spaced hyphen joining two clauses.
 2. Antithesis: "not just", "not only", "X, not Y", "isn't X, it's Y", "rather than".
 3. Hype and filler words: seamless, leverage, robust, unlock, empower, elevate, transform,
    revolutionise, cutting-edge, state-of-the-art, best-in-class, world-class, game-changing,
    innovative, holistic, streamline, harness, supercharge, effortless, frictionless, delve,
    landscape, ecosystem, journey, synergy, paradigm, comprehensive, pivotal, crucial, foster,
    navigate, realm, bespoke, tailored, mission-critical, actionable, insights, powerful,
    intelligent, smart, magic, AI-powered, agentic, next-gen, cutting edge, solution(s).
 4. Formula openers: "In today's", "In an era", "Whether you're", "Imagine", "What if",
    "Ready to", "Let's", "Say goodbye", "No more", "Meet", "Introducing", "Here's",
    "The result", "The best part", "That's where", "Enter", "The truth is", "The good news".
 5. Questions outside an FAQ: rhetorical questions in headings or body copy.
 6. Exclamation marks.
 7. Colon reveals in headings ("Speed: redefined").
 8. "From X to Y" span claims ("from the GPU to the finished work").
 9. Punchline fragments: sentences of one to three words ("Simple." "No surprises.").
10. Intensifiers and hedges: truly, really, incredibly, deeply, genuinely, simply, just,
    actually, literally, very, extremely, absolutely.
11. Self-congratulation: "we're good at", "we pride", "we believe", "our mission",
    "passionate", "obsessed", "we love".
12. Problem melodrama: drowning, buried, headache, pain point, nightmare, struggle.
13. Stock phrases: the hard part, the easy part, in a few clicks, before you notice, what you're paying for,
    turnkey, hands-free, zero-touch, it just works, the last mile, the last 30 percent, end to end / end-to-end,
    at scale, peace of mind, under the hood, out of the box, single pane of glass,
    heavy lifting, and more, and beyond, game changer, built for, designed to,
    purpose-built, up to N%.
14. Corporate verbs: ensure, enhance, utilise, facilitate, empower, enable.
15. Title Case Headings (three or more capitalised words in a row that aren't names).
16. Emoji.
17. Triads as slogans: a heading or lede made of exactly three short comma-separated items.

Some tells (parallel paragraphs of identical shape, a lede that restates the heading) need a person
to read for them; the script can't catch those.
"""
import html, re, sys

WORDS = r"seamless\w*|leverag\w*|robust\w*|unlock\w*|empower\w*|elevat\w*|transform\w*|revolutioni[sz]\w*|cutting[- ]edge|state[- ]of[- ]the[- ]art|best[- ]in[- ]class|world[- ]class|game[- ]chang\w*|innovati\w*|holistic\w*|streamlin\w*|harness\w*|supercharg\w*|effortless\w*|frictionless|delv\w*|landscape|ecosystem\w*|journey\w*|synerg\w*|paradigm\w*|comprehensive\w*|pivotal|crucial\w*|foster\w*|navigat\w*|realm\w*|bespoke|tailored|mission[- ]critical|actionable|insights?|powerful\w*|intelligent\w*|smart|magic\w*|ai[- ]powered|agentic|next[- ]gen\w*|solutions?"
OPENERS = r"in today's|in an era|whether you're|imagine\b|what if\b|ready to\b|let's\b|say goodbye|no more\b|meet\b|introducing\b|here's\b|the result\b|the best part|that's where|enter\b|the truth is|the good news"
INTENS = r"truly|really|incredibly|deeply|genuinely|simply|just|actually|literally|very|extremely|absolutely"
SELF = r"we're good at|we are good at|we pride|we believe|our mission|passionate|obsess\w*|we love"
DRAMA = r"drown\w*|buried|headache\w*|pain[- ]points?|nightmare\w*|struggl\w*"
STOCK = r"the hard parts?|the last mile|the last \d+ ?(?:percent|%)|end[- ]to[- ]end|at scale|peace of mind|under the hood|out of the box|single pane of glass|heavy lifting|and more\b|and beyond|built for|designed to|purpose[- ]built|up to \d+ ?(?:%|percent)|the easy (?:part|bit|step)|in a few clicks|with a few clicks|before (?:you|your \w+) (?:even )?notice|what you(?:'re| are) paying for|that's the part|hassle|no[- ]brainer|it just works|zero[- ]touch|turnkey|hands[- ]free"
CORP = r"ensur\w*|enhanc\w*|utili[sz]\w*|facilitat\w*|enabl\w*"
NAMES = {"VitalOps", "ERP", "EDI", "SFTP", "SSO", "API", "PDF", "Straightops", "Chatfin"}

def visible(src):
    src = re.sub(r"(?is)<(script|style|blockquote|svg|code)\b.*?</\1>", " ", src)
    src = re.sub(r"(?is)<!--.*?-->", " ", src)
    faq = re.findall(r"(?is)<summary[^>]*>(.*?)</summary>", src)
    heads = [re.sub(r"<[^>]+>", "", h) for h in re.findall(r"(?is)<h[1-4][^>]*>(.*?)</h[1-4]>", src)]
    blocks = re.findall(r"(?is)>([^<>]+)<", src)
    text = [html.unescape(b).strip() for b in blocks]
    return [t for t in text if t], [html.unescape(h).strip() for h in heads], [html.unescape(re.sub(r"<[^>]+>", "", q)).strip() for q in faq]

def check(path):
    texts, heads, faqs = visible(open(path, encoding="utf-8").read())
    hits = []
    def find(kind, pat, items, flags=re.I):
        for t in items:
            for m in re.finditer(pat, t, flags):
                hits.append((kind, m.group(0), t[:110]))
    find("dash", r"—|(?<!\d)–|–(?!\d)|\s-\s", texts, 0)  # an en dash between numbers is a range
    find("antithesis", r"\bnot just\b|\bnot only\b|,\s*not\s+\w+|\bisn't\b[^.]*\bit's\b|\brather than\b", texts)
    find("hype word", rf"\b(?:{WORDS})\b", texts)
    find("opener", rf"(?:^|[.!?]\s+)(?:{OPENERS})", texts)
    find("question", r"\?", [t for t in texts if t not in faqs])
    find("exclamation", r"!", texts, 0)
    find("colon reveal", r":\s*\S", heads, 0)
    find("from X to Y", r"\bfrom\s+(?:the\s+)?[\w-]+(?:\s+[\w-]+)?\s+(?:down\s+|up\s+|all the way\s+)?to\s+(?:the\s+)?[\w-]+", texts)
    find("fragment", r"(?:^|[.!?]\s+)(?:\S+\s+){0,2}\S+[.!]$", texts, 0)
    find("intensifier", rf"\b(?:{INTENS})\b", texts)
    find("self-praise", rf"\b(?:{SELF})\b", texts)
    find("melodrama", rf"\b(?:{DRAMA})\b", texts)
    find("stock phrase", rf"\b(?:{STOCK})", texts)
    find("corporate verb", rf"\b(?:{CORP})\b", texts)
    for h in heads:
        caps = [w for w in re.findall(r"[A-Za-z][\w'-]*", h)[1:] if w[0].isupper() and w not in NAMES]
        if len(caps) >= 2:
            hits.append(("title case", " ".join(caps), h))
        parts = [p.strip() for p in re.split(r",|\band\b", h) if p.strip()]
        if len(parts) == 3 and all(len(p.split()) <= 2 for p in parts):
            hits.append(("slogan triad", h, h))
    find("emoji", r"[\U0001F300-\U0001FAFF☀-➿]", texts, 0)
    # from the LLM tells checklist (2026-11-24): framing, filler and structure
    find("page self-reference", r"\b(?:below|above),? you(?:'ll| will)\b|\bthis (?:page|section|tab)\b|\beach (?:tab|card|section|panel|step|row) (?:shows|lists|covers|walks|opens)\b|\bthe following\b|\bscroll (?:down|to)\b|\bhere is (?:what|how)\b|\ban example of\b", texts)
    find("counting", r"\b(?:two|three|four|five|six|seven) (?:ways|things|steps|reasons|pillars|principles|benefits)\b|\bper industry\b", texts)
    find("serves as", r"\b(?:serves?|stands?|functions?) as\b", texts)
    find("signpost", r"\b(?:in short|in summary|in conclusion|bottom line|put simply|at the end of the day|ultimately|it's worth noting|notably|importantly|moreover|furthermore|additionally|that said)\b", texts)
    find("explainer opener", r"(?:^|[.!?]\s+)(?:that's why|this means|which means|think of it (?:as|like))\b", texts)
    find("denial string", r"(?:^|[.!?]\s+)Not (?:a|an|another|just)\b|\bno \w+(?: \w+)?, no\b", texts)
    find("with X, Y and Z", r"\bwith (?:what [^,.]+|[\w-]+), [\w-]+(?: [\w-]+)?,? and [\w-]+", texts)
    find("benefit tail", r",\s+(?:helping|giving|allowing|letting|making|freeing|saving|keeping)\b|\bso (?:you|your \w+) can\b", texts)
    find("hedge", r"\b(?:can help|helps? (?:you|teams?)|aims? to|potentially|may help)\b", texts)
    find("adverb", r"\b(?:quietly|effortlessly|fundamentally|significantly|completely|entirely|every single)\b", texts)
    find("grand word", r"\b(?:tapestry|testament|cornerstone|underscor\w*|showcas\w*|vibrant|unparalleled|unprecedented|reimagin\w*|redefin\w*|the future of|a new era|next level|all[- ]in[- ]one|single source of truth|trusted by|in minutes|by design|on a mission)\b", texts)
    find("symbol", r"[↔≈…]", texts, 0)  # → is allowed inside the app screens
    # fragments: ignore short labels (buttons, list headings, numbers) that are not sentences
    hits = [h for h in hits if not (h[0] == "fragment" and len(h[2].split()) <= 4 and not h[2].endswith((".", "!")))]
    return hits

if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:]:
        for kind, m, ctx in check(p):
            bad += 1
            print(f"{p}: {kind}: {m!r}  ::  {ctx}")
    print(f"{bad} tell(s)")
    sys.exit(1 if bad else 0)
