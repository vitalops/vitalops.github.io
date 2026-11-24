# LLM tells in B2B landing-page copy: a checklist

For rewriting a landing page so it doesn't read as machine-written. Section A covers the tells that need a
person to judge them, which `src/tools/copy_tells.py` can't catch. Section B lists the regex-able tells briefly
and marks the ones the script already flags. No single tell proves anything. Readers react to clusters, and to
copy that could sit on any competitor's site unchanged.

Format: **Tell.** Why readers notice. *Bad:* ... *Fixed:* ... (Numbers and customers in the fixed examples are made up to show the shape. Use real ones.)

---

## A. Tells that need judgement

### A1. Framing: the page talks about itself

1. **Self-describing the page or section.** ("Each tab shows...", "Below you'll find...", "This section covers...")
   The reader can already see the tab. Narrating the layout is filler that a chatbot adds to orient a user.
   *Bad:* Each tab below shows how VitalOps handles a different part of the order cycle.
   *Fixed:* (Delete it. Let the tab labels do the work.)

2. **Announce-then-answer (preamble).** Explaining what the reader is about to see instead of showing it.
   It delays the point and sounds like an essay plan.
   *Bad:* Here is how a purchase order moves through the system, step by step.
   *Fixed:* A PO arrives by email at 9:02. By 9:04 it's in your ERP with the supplier's prices checked.

3. **Compulsive counting.** Stating the number of items before listing them.
   Readers can count. It's a structural crutch from listicle training data.
   *Bad:* Three reasons teams switch to VitalOps.
   *Fixed:* Why teams switch

4. **Lede restates the heading.** The paragraph under a heading says the heading again, longer.
   It reads like padding and tells the reader the writer had nothing new.
   *Bad:* H2 "Faster order entry" / "VitalOps makes order entry faster for your team."
   *Fixed:* H2 "Faster order entry" / "Orders that took a clerk 12 minutes now take 40 seconds of review."

5. **Tie-back and fractal summary.** A closing line that restates what the section just said.
   ("In short...", "The result: a team that...", "All of this means...")
   *Bad:* In short, your team spends less time on admin and more time on suppliers.
   *Fixed:* (Stop one sentence earlier.)

6. **Explaining the benefit of the feature you just named.** The "so you can..." tail on every sentence.
   One is fine. On every line it sounds like the writer assumes the reader is slow.
   *Bad:* Invoices are matched automatically, so you can focus on what matters.
   *Fixed:* Invoices are matched to the PO and the receipt. Mismatches go to a queue for your AP team.

7. **"Think of it as..." analogy.** Reaching for a metaphor instead of describing the product.
   It's patronising to a buyer who knows their own process.
   *Bad:* Think of it as an extra team member who never sleeps.
   *Fixed:* It runs overnight and leaves a list of exceptions for the morning.

### A2. Structure and shape

8. **Neat lists of three.** Triads everywhere: three adjectives, three benefits, three cards.
   Pangram measured triads at about 4x the human rate. Real lists have two items, or five.
   *Bad:* Faster, more accurate and fully auditable.
   *Fixed:* Fewer keying errors. Every change has a name and a time on it.

9. **"With X, Y and Z" summary sentences.** One sentence that bundles three features into a list.
   It summarises instead of showing any one of them.
   *Bad:* With automated matching, real-time alerts and full audit trails, your team stays in control.
   *Fixed:* When a supplier changes a price, the buyer gets the old and new price side by side before it posts.

10. **Parallel paragraphs or cards of identical shape.** Every card: bold label, one sentence, same length.
    The sameness is visible from across the room before anyone reads a word.
    *Bad:* Four cards, each "Label. One 12-word sentence about a benefit."
    *Fixed:* Vary them. One card can be a number, one a screenshot caption, one a two-sentence story.

11. **Evenly sized sentences.** Every sentence 12 to 18 words, same subject-verb-object shape.
    Human writing is bursty. Uniform length is the most cited rhythm tell.
    *Bad:* VitalOps reads every order email. It checks each line against your catalogue. It flags prices that changed.
    *Fixed:* VitalOps reads the order email, checks each line against your catalogue and price list, and posts what matches. Changed prices wait for a buyer.

12. **Anaphora.** Consecutive sentences that open with the same word ("It reads... It checks... It flags...").
    Feels like a template filling in slots.
    *Fixed:* Merge them, or start one with the object: "Price changes go to a buyer."

13. **Labelled mini-headings and bold-first bullets.** "**Speed:** ...", "**Accuracy:** ..." on every item.
    Bold inline headers are 43x more common in AI text (Pangram) and Wikipedia flags them by name.
    *Bad:* **Visibility:** See every order in one place.
    *Fixed:* Every open order is on one screen, sorted by ship date.

14. **Title Case and "What/Why/How" headings.** "How It Works", "Why VitalOps", "What We Do Differently".
    Default headings say nothing about this product.
    *Fixed:* Use the claim as the heading: "Orders post to SAP in under two minutes".

15. **Never-ending close and quotable one-liners.** A final line built to be screenshotted that says little.
    *Bad:* Because your suppliers won't wait, and neither should you.
    *Fixed:* (Delete. End on the last fact.)

### A3. Rhetorical moves

16. **Colon reveal and "The X? A Y."** Setting up suspense for an ordinary point.
    The script catches colons in headings and all question marks, not colon reveals in body copy.
    *Bad:* The result? Fewer errors. / Here's the catch: most ERPs can't read PDFs.
    *Fixed:* Most ERPs can't read a PDF order, so someone retypes it.

17. **Negation chains.** "Not a chatbot. Not another dashboard. An operations team." Or "No X, no Y."
    The tripled negative-parallelism form; the script only catches "not just" and ", not Y".
    *Fixed:* Say what it is: "It works your order inbox and keys orders into your ERP."

18. **Invented problems and strawmen.** Correcting a misconception nobody held.
    *Bad:* Automation isn't about replacing people.
    *Fixed:* Your buyers still approve every price change.

19. **Grandiose stakes.** Small features presented as a turning point ("the future of procurement").
    B2B buyers discount it to zero and trust the rest of the page less.
    *Fixed:* Name the actual change: "Your team stops retyping orders."

20. **Trailing -ing clause that adds vague significance.** ", helping teams stay ahead."
    Wikipedia lists this as "superficial analysis". It attaches a meaning the sentence didn't earn.
    *Bad:* Orders sync every five minutes, giving your team full visibility.
    *Fixed:* Orders sync every five minutes.

21. **Copula avoidance.** "serves as", "acts as", "stands as", "functions as" instead of "is".
    *Bad:* The exception queue serves as your single source of truth.
    *Fixed:* The exception queue is where anything VitalOps couldn't post ends up.

### A4. Word choice that needs a reader

22. **Abstract nouns standing in for concrete things.** "visibility", "efficiency", "control", "workflows",
    "operations", "complexity". Readers can't picture them, so they skim.
    *Bad:* Gain visibility and control across your procurement operations.
    *Fixed:* See which supplier confirmations are late, by supplier, this morning.

23. **No numbers, names or nouns a competitor couldn't use.** The biggest failure in a scan of 239
    landing pages (82% had no numbers). The swap test: if a rival's logo fits, rewrite it.
    *Bad:* Trusted by leading distributors.
    *Fixed:* 14 distributors in Ohio and Indiana run their order desk on it.

24. **Hedges.** "can help", "may", "aims to", "helps you", "potentially". Copy that won't commit sounds generated.
    *Bad:* VitalOps can help reduce order errors.
    *Fixed:* Order keying errors dropped from 3.1% to 0.4% at one customer over six months.

25. **Magic adverbs.** "quietly", "seamlessly", "effortlessly", "fundamentally". The script catches some
    intensifiers but not these.
    *Bad:* It quietly handles the work in the background.
    *Fixed:* It runs every five minutes. You only see it when something needs a decision.

26. **Synonym cycling (elegant variation).** The platform... the system... the tool... the solution.
    Readers wonder if these are four products. Pick one name and repeat it.

27. **Vague attribution and social proof.** "Experts agree", "teams everywhere", "industry leaders".
    *Fixed:* Name a customer and quote them, or drop it.

28. **Tone that's too polished for the setting.** HN's most-developed complaint: every line has a flourish,
    with no plain sentences in between. A good page has boring connective sentences.
    *Fix:* Let half your sentences be plain statements of fact with no rhetoric at all.

---

## B. Regex-able tells

Already flagged by `copy_tells.py` (keep running it): em and en dashes; "not just / not only / X, not Y /
rather than"; hype words (seamless, leverage, robust, unlock, insights, solution...); formula openers
(Imagine, Introducing, Here's, That's where...); rhetorical questions; exclamation marks; colon reveals in
headings; "from X to Y"; one-to-three-word fragments; intensifiers (truly, really, just, simply...); self-praise;
problem melodrama; stock phrases (end-to-end, at scale, out of the box, built for, in a few clicks...);
corporate verbs (ensure, enhance, enable...); Title Case headings; emoji; slogan triads in headings.

Not yet flagged (patterns in the reply and listed here for reference):

- Page self-reference: "below you'll find", "this section", "each tab shows", "the following", "scroll down".
- Compulsive counting: "three ways", "5 reasons", "four steps".
- "serves as / acts as / stands as / functions as".
- Signposted conclusions and filler transitions: "in short", "in summary", "bottom line", "put simply",
  "at the end of the day", "ultimately", "it's worth noting", "notably", "importantly", "moreover",
  "furthermore", "additionally", "that said".
- "That's why", "This means", "Which means", "Think of it as/like".
- Sentence-initial "Not" chains and "No X, no Y".
- "with X, Y and Z" in body text (the script only checks triads in headings).
- Trailing -ing clauses: ", helping...", ", giving...", ", allowing...", ", so you can...".
- Hedges: "can help", "helps you", "aims to", "may", "potentially".
- Magic adverbs: quietly, effortlessly, fundamentally, significantly, completely, every single.
- Grand nouns: tapestry, testament, cornerstone, underscore, showcase, vibrant, unparalleled, reimagine,
  redefine, "the future of", "a new era", "next level", "all-in-one", "single source of truth".
- Landing-page cliches: "for every team", "teams of all sizes", "trusted by", "get started in minutes",
  "lightning-fast", "blazing", "-first" (privacy-first), "by design", "we're on a mission".
- Question-word headings without a "?": "How it works", "Why X", "What we do".
- Colon reveals in body copy ("Here's the catch: ...").
- Bold-first list items (`<li><strong>Label</strong>:`), which needs the raw HTML.
- Unicode the script misses: arrows (→), approx (≈), ellipsis (…), curly quotes if your style is straight.
- ALL-CAPS words outside the NAMES list.
- Measurable rhythm: sentence-length spread per paragraph, and consecutive sentences with the same first word.

---

## C. How to rewrite (procedure)

1. **Run the script** and fix every hit. That clears the cheap tells so you can see the structural ones.
2. **Delete the meta.** Strike every sentence that describes the page, a section, or what's coming next.
   Strike every closing line that restates the section. Read what's left; it usually stands up.
3. **Swap test each claim.** Put a competitor's name in. If it still works, replace it with a number, a
   named system (SAP, NetSuite, EDI 850), a customer, a time, or a specific step.
4. **Replace each abstract noun** (visibility, efficiency, control) with the thing the buyer would see on screen.
5. **Break the triads.** For every list of three, drop one or add the fourth real one. Check cards too.
6. **Fix the rhythm.** Read each paragraph aloud. If every sentence is the same length, merge two and cut one
   down to a short plain clause. Vary the first word of consecutive sentences.
7. **Strip the labels.** Turn "**Speed:** X" bullets into plain sentences, and headings into claims in
   sentence case.
8. **Remove hedges and intensifiers together.** "can really help" becomes the measured result, or nothing.
9. **Allow plain sentences.** Not every line needs a turn. Most should just state a fact.
10. **Re-run the script**, then read the page cold the next day, or have someone who didn't write it do so.

---

## Sources

- https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
- https://tropes.fyi
- https://www.pangram.com/signs-of-ai-writing
- https://seangoedecke.com/chatgpt-house-style/
- https://carly.substack.com/p/spotting-machine-made-prose
- https://www.deadlanguagesociety.com/p/rhetorical-analysis-ai
- https://news.ycombinator.com/item?id=50077652
- https://dev.to/parweb/we-scored-239-real-landing-pages-for-ai-slop-here-is-the-data-2nl0
- https://evilmartians.com/chronicles/hey-developer-tool-teams-dont-copy-these-copywriting-cliches
- https://www.prsa.org/article/which-signs-of-ai-writing-disengage-people-most-APRIL26 (summary of a Search Engine Land study; original page returned 403)
- https://www.fastcompany.com/91469729/structure-sentence-dead-giveaway-that-ai-wrote-it (headline and search snippet only; page returned 403)
