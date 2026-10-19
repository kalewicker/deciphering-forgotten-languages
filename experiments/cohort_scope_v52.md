# Experiment 52: uniform structural scope across five saved publisher pages

Question: how does a uniform paragraph-text channel compare with the old direct-p
scope across the complete saved publisher cohort? Freeze all FIVE pages: v42's
reference publisher plus all four v50 slots, including the two out-of-window
pages and the h1 failure. No selection by outcome, new acquisition, browser/CSS/
JavaScript execution, quote comparison, number inventory or scaffold scoring.
This is a representation audit, not a prose classifier or candidate admission.

Before computing new cohort scopes, freeze config, code/tests, original raw
bytes/receipts/observations, old direct-p scope, old v51 audit, and all 51 prior
manifests/seals. Prior exposure includes v51's one-page scope weakness. Apply
identical rules to every page, without post-inspection rule changes or exceptions.
Reproduce each old body/direct-paragraph string, span and mapping count exactly.
Retain v50's dates, h1 failure, one-ready/four-slot outcome and v51's URL conflict.

Use BeautifulSoup html.parser and the same script/style/noscript/template/svg/
canvas removal. Require one body and one
article[id^="post-"] > div.entry-content. Map EVERY nonempty NavigableString/
CData body leaf in DOM order to the unchanged get_text(' ',strip=True) body:
join stripped leaf strings by one space, tracking original resulting Unicode
start/end. That joined string must equal the frozen body. Keep each leaf's
individual DOM identity even if its text occurs repeatedly; no text-find shortcut
for prospective spans. These are parsed-body coordinates, not HTML byte offsets
or proof of browser visibility. Comments are not text leaves.

For every entry-content leaf retain raw/stripped text, body span, global body-
leaf index, container-leaf index, parent DOM ordinal and ancestor tags. Mark old
inclusion by whether its immediate container-child owner is a p. New channels
use fixed ancestor priority before reaching the container: form (form/button/
input/label), table (table/thead/tbody/tr/td/th), figure (figure/figcaption),
blockquote, list (ul/ol/li), heading (h1-h6), paragraph (p), then other.
Ancestor means any node on the leaf-to-container path; higher priority wins
even inside a direct p. Thus new paragraph scope need not be an old-scope superset.

For each channel the owner is the outermost matching ancestor below the container;
for other it is the immediate container-child element, or the container for loose
text. DOM ordinals are assigned before stripping. Record every channel, not only
paragraphs. Calling the new channel paragraph is a structural label, not a claim
of article prose, language, semantic relevance or absence of widgets outside forms.

Prospective paragraph runs join only adjacent paragraph-channel leaves having
the SAME owner, consecutive in the full container leaf ledger, with exactly one
body separator between spans. Every run retains original body span/text and all
source leaf indices. Never merge across an excluded leaf, another owner or an
original-body gap; never manufacture an identifier by deleting excluded text.
No new text is fed to an anchor extractor. Retain all p elements (direct/nested,
empty/nonempty and within non-paragraph channels) in an owner inventory, including
exact original DOM-derived spans and whether their own full text matches that
span. Flag nested-p structures; do not silently collapse overlapping p inventories.
Prospective paragraph runs themselves must be ordered and disjoint.

Report per-page channel counts/stripped characters, old versus prospective leaf
counts, added/removed leaf inventories, empty/nested-p owners, paragraph run
counts and original span coverage. Full-container leaves must reproduce exactly
the original container text. Old included leaves reproduce the old direct-p
join. New paragraph runs must cover every paragraph-channel leaf exactly once.
Do not interpret character counts as semantic coverage or translation accuracy.

Run the SEALED v51 title/identity diagnostic uniformly on each page and retain
its full outputs beside the new scope ledger. All title families, no-h1 and URL
disagreements remain under the same rules. Do not infer aliases or make requests.
Reproducing those diagnostics does not change old admission or add a new title
fallback. Dates and v50 readiness remain copied observations, not rescored gates.

The engineering accounting criterion passes only if all five old bodies/scopes
are reproduced, every leaf/run span is exact, all channel partitions account for
all leaves, runs cover paragraph leaves exactly once without overlap, form leaves
are excluded from the new paragraph channel and all old outcomes remain fixed.
Record the outcome without any semantic/source/readiness admission, irrespective
of how many paragraphs the new scope adds.

Before audit, fixture-test identical-text leaves with distinct DOM locations,
inline versus nested/empty paragraphs, category priority, old-included leaves
removed by higher-priority channels, nested p owners, no joining across excluded
gaps or owners, Unicode spans, comment/script removal and identity/ambiguity
failures. After audit, separately reconstruct body-leaf positions, categories,
owner inventories and all runs; verify old v51 diagnostics and all 51 historical
manifests/seals. Shared HTML parser and same-agent verification remain explicit.

Zero network requests, browser renders, numeric/uppercase/lexical/semantic scores,
new candidate readiness, meanings, source identities, independent reviews or
untouched units. Scientific acceptance/semantic metrics null. Seal evidence and
report, run full/public checks, checkpoint evidence only locally, commit/push
appropriate public artifacts on main. Do not edit sealed historical files.
