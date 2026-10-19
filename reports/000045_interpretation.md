# Experiment 45: quote02 context and reported attribution

The local [quote02 context dossier](../data/v45/dossier.md) is complete. Its
fixed 22-token shared span lies in the publisher paragraph reporting **Alan
Watson's** comments. The preceding paragraph contains the separate Gorham
quotation studied in experiment 42. In the target, quote02 uses first-person
wording and includes a final beacon sentence. The complete target prefix and
suffix, and the specific beacon phrase, are absent as literal strings from the
captured publisher body.

These are observations about two frozen English passages. They do not establish
copying direction, original authorship, historical contents or opaque FL meanings.

## Fixed context and exact partitions

The [registration](../experiments/context_dossier_v45.md), original quote02,
v44 witness, v42 HTML/export, code/tests and prior ledgers were frozen before
preparation. There were **zero network requests**. One declared re-extraction
from the saved HTML exactly reproduces the 12,072-character source body.
Exactly one paragraph candidate contains the complete fixed witness: DOM p
index **16**, body span **[7109, 7437)**. No new maximal-run search or alignment
was performed; the report's `new_overlap_assessments` count refers to such assays.
Eleven new, predeclared literal context checks are reported below.

| Region outside/inside the fixed witness | Target quote characters | Publisher paragraph characters |
|---|---:|---:|
| Prefix | 112 | 201 |
| Shared span | 127 | 127 |
| Suffix | 166 | 0 |
| Total | 405 | 328 |

Each partition concatenates exactly to its original passage, including whitespace
and the empty publisher suffix. The shared source span remains **[7310, 7437)**
and its full-target span remains **[1353, 1480)**. No v44 boundary or token was
changed. “Outside the fixed witness” does not mean every other word is unrelated
or novel; shorter overlaps and paraphrases were not exhaustively assessed.

The source window contains paragraphs **15, 16 and 17**, with original body
occurrence spans. The target window is **[1081, 1806)**, comprising the complete
quote and 160 characters on either side. Its opaque surroundings are displayed
for provenance and remain unscored. The complete JSON evidence is in
[dossier.json](../data/v45/dossier.json); source prose stays local.

## Eleven registered wording checks

| Exact wording query | Target quote | Selected publisher paragraph | Entire saved publisher body |
|---|---|---|---|
| Complete target prefix | — | Absent | Absent |
| Complete target suffix | — | Absent | Absent |
| Giselian beacon | Present | Absent | Absent |
| Alan Watson | — | Present | — |
| Fixed shared fragment | Present | Present | Present |

All eleven checks have available outcomes and exact scope-relative Unicode
witnesses where present. The three shared-fragment checks and exact partition
reassembly pass. These are case-selected context checks, not an accuracy score
or independent tests of the six-block population. Full-prefix/suffix absence
does not reject edited or partial correspondence in their component wording.

The [same-agent context review](../data/v45/context_review.json) distinguishes
the publisher-reported speaker from authentication of a person or interview.
The target's beacon wording is absent only from the declared saved publisher
scopes; no claim about its existence elsewhere or physical validity is tested.
No independent reviewer was assigned or contacted.

## Verification, limits and next step

**349/349 full-workspace tests** and **310/310 isolated-public-export tests**
pass. Four new tests cover exact reassembly/windows, duplicate paragraph
ambiguity, changed-witness/export rejection, empty intervals and safe verbatim
fencing. The same 39 archive-dependent tests remain excluded publicly.

The [separate verifier](../scripts/verify_context_dossier_v45.py) reconstructs
the unique paragraph selection, source re-extraction, all partitions/windows,
eleven literal checks, fixed offsets and dossier contents. All **44 earlier
runs and deliverable seals** remain intact. It was written after dossier
preparation and shares BeautifulSoup html.parser and the prior independent
literal-occurrence checker. This is engineering verification by the same
agent, not independent scientific review. See
[verification receipt](000045_verification.json) and
[immutable report](../runs/000045_context_dossier/report.json).

The whole-query and exact-fragment results remain unchanged. No opaque meanings,
immediate source identity, independent review or untouched test unit is admitted.
Natural-benchmark capacity remains unmet; semantic metrics and scientific
acceptance remain null.

Next bounded step: register a **nonlexical scaffold audit** of opaque-only target
text against the saved publisher material. Mask English quotations and the
bibliography before extracting numerals/acronyms; freeze scopes, normalization
and order-disrupting controls before measuring anything. Such an exposed
development check could test structural consistency, while leaving meaning,
ancestry and source-identity claims unadmitted. No anchor extraction, opaque
scoring or source selection for that next assay occurred in experiment 45.
