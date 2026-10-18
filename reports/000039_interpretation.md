# Experiment 39: instrument-name match only; longer quotation support absent

The one-source diagnostic returns **1/8 literal query matches**, consisting only
of the expanded instrument name in `quote01`. **None of the seven longer quoted
blocks occurs in full** under the unchanged v38 literal rule. The registered
longer-block question is therefore negative. All eight queries, all fifteen
source pages and every zero-page outcome remain in the ledger.

The source PDF also contains a provenance discrepancy: its margin identifies
arXiv 1809.09615v1, 25 Sep 2018, while the internal Dated line reads March 7,
2025. Both observations are preserved. The cause is unresolved; these results
describe the exact bytes served now, not authenticated 2018 PDF bytes. Source
relationship, opaque-text meanings and whole-post coverage remain unresolved.

## Frozen source, target and readout

The sole request to <https://arxiv.org/pdf/1809.09615v1> returns HTTP200 with a
complete PDF. Its requested version marker is visible, its title/first author
agree with the nominated bibliography entry, and all fifteen pages parse and
render. There is no new target request, search, other source, alternate version,
mirror or retry. The v38 archive capture and its earlier 0/8 result remain fixed.

The implementation imports the unchanged v38 literal matcher. All eight
quote IDs, target spans and text strings are byte-bound to the earlier ledger;
no query was shortened, split, replaced or excluded. Normalization remains NFC,
casefold and whitespace collapse only, page by page. Line-end hyphenation,
column reading order, ligatures, equations and spacing are not repaired.

| Fixed partition | Queries | Complete literal presence |
|---|---:|---:|
| Expanded instrument name, quote01 | 1 | 1 |
| Longer quoted blocks, all other IDs | 7 | 0 |
| Complete inventory | 8 | 1 |

The successful witness is source page1, Unicode span **[2377,2414)**:
`Antarctic Impulsive Transient Antenna`. Its normalized-source span is distinct
from the raw extracted-page coordinates. This named entity does not count as
longer-passage support under the predeclared primary question. Shared instrument
names are compatible with many accounts of the same topic.

The exact selected identifier also occurs once in the target bibliography. Its
enclosing-token witness is target span [8162,8181), including the `arXiv:` prefix
and final punctuation. That is citation identity, not an admitted immediate
source relationship.

All **15/15 engineered source-copy controls** hit their own page; the fixed
absent-marker control hits none. There are no empty-extraction pages or
unavailable query outcomes. These controls verify substring sensitivity and
coordinate accounting, not independent natural positives/negatives or semantic
accuracy. The full inventory contains 120 quote/page decisions. The
[assessment](../data/v39/assessment.json) retains every one, with source witnesses,
target coordinates, controls and the descriptive anchor counts.

For context, the unchanged whole-token anchor rule counts ANITA 66 times,
IceCube 113 times and the event number 15717147 once in the source extraction,
versus 17, 4 and 2 respectively in the frozen target. These exposed observations
show topical overlap; they are not calibrated source-attribution evidence.

The result does not show that the seven longer blocks are fabricated or wholly
unrelated to the paper. A block can contain edited or partial reuse without
occurring in full. Partial-fragment, sentence-level, paraphrase and opaque-
language comparisons were not performed and cannot replace this negative result.
The paper's scientific claims were not validated in this experiment.

## Source-date discrepancy and material scope

All fifteen complete page images were displayed. The title, author list,
requested version marker, two-column text, tables, plots and reference pages
are legible and ordered. The [visual inspection record](../data/v39/visual_review.json)
explicitly retains the first-page 2018 marker and 2025 internal date.

The registered representation gate requires the requested version marker and
parseable PDF material; it passes. A historical-byte gate was not registered,
so the new discrepancy is recorded separately rather than silently changing
the criterion. Marker agreement alone does not establish which exact bytes or
text were available when the FL post was published. No recompilation, revision,
mislabeling or other causal explanation is inferred without further evidence.

The saved source SHA-256 is
`b86c606efa1947fa4e2fc7b084b1d9329b306fb9eb7fbf1d230f7ef590a1d267`.
The complete [source export](../data/v39/source_export.json) binds each unmodified
page text, Unicode scope and image to the downloaded bytes. Existing source and
target coordinates from v38 remain separate.

## Neutral review handoff

The [neutral packet with provenance notice](../data/v39/neutral_review_packet_with_provenance.zip)
contains the unchanged source PDF, dated target export, page-local source text,
acquisition/archive receipts, blank reviewer declaration and a factual date
notice. It excludes our match outcomes, anchor counts, proposed meanings and
preferred alignment. Candidate source identity is disclosed; it cannot test
blinded source retrieval. No reviewer is assigned, contacted or declared complete.

The original packet and completed run are unchanged. The supplied packet is a
post-run derivative adding only the observed provenance facts and exact
first-page date witnesses. Its [receipt](000039_packet_receipt.json) binds it to
the frozen run and checks all eleven members plus exact source/target bytes.
The notice does not supply an answer to the quotation diagnostic. A reviewer
must disclose exposure to this report, our ledgers or earlier predictions.

Independent-review, semantic-label, source-identity and untouched-test admissions
remain zero; the four-work natural benchmark capacity is still unmet. Matching
an English instrument name does not establish a meaning for an opaque FL word,
and these exposed sources cannot be relabeled as an untouched test fold.

## Verification and next boundary

All **333 tests pass**. New checks ensure that unavailable material is not counted
as eight negative results, empty pages remain in the denominator, changed frozen
queries fail closed, and a name-only match cannot pass the longer-block question.
Registration, implementation and inputs were hash-sealed before the one request
and before source comparison.

The independent literal-count/witness verifier reproduces all query/page
decisions, controls and anchor counts, checks source/target preservation and
reextracts the PDF using the same explicitly shared extraction library. All
**38 prior run inventories and deliverable seals** verify unchanged. The
[verification receipt](000039_verification.json) passes. Same-assistant independent
implementation and visual QA are engineering checks, not external scientific
review. Scientific acceptance and semantic metrics remain null; opaque-passage
scores, lexical changes and external messages remain zero.

The next useful bounded step is **source-version provenance**: register official
version metadata and, if available within a fixed budget, a dated representation
or source-package check to distinguish the version marker from PDF generation
date. Preserve the observed date difference and do not promise that metadata
alone can establish 2018 byte identity. This investigation needs a new
registration; no extra request belongs to v39. A later partial-quotation audit
would separately need frozen units, all denominators and preserved whole-block
negatives. It would still be development evidence, not an opaque-language
decipherment claim.

Artifacts: [registration](../experiments/quoted_citation_v39.md),
[preflight](../data/v39/preflight.json),
[frozen queries](../data/v39/frozen_queries.json),
[acquisition receipt](../data/v39/acquisition/source/receipt.json),
[immutable report](../runs/000039_quoted_citation/report.json),
[source/date inspection](../data/v39/visual_review.json).

Verify offline with the existing runtimes and no new acquisition:

```sh
PYTHONPATH=src:.venv/lib/python3.14/site-packages /Users/kalewicker/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/verify_quoted_citation_v39.py
```

Generation and acquisition refuse existing evidence paths; successful
verification preserves its receipt.
