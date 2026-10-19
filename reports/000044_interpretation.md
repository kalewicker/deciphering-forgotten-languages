# Experiment 44: one exact English fragment in six unmatched blocks

**1/6 longer blocks has a qualifying exact fragment:** quote02 shares one
**22-token** contiguous run with the frozen Physics World publisher body.
Each of the other five blocks has a longest run of two tokens, below the
registered eight-token cutoff. All four controls pass. The result adds a
partial English correspondence; experiment 43's **0/6 complete-block result
remains unchanged**.

## Registered method and complete readout

The [registration](../experiments/exact_fragments_v44.md), six original query
IDs/offsets, unchanged 12,072-character source, algorithm, runner and five fixture
tests were frozen before scoring. There were **zero network requests and zero
new document extractions**. The full saved publisher body remains the scope,
including navigation and existing whitespace/DOM joins.

Tokens are original Unicode non-whitespace spans, normalized with NFC then
casefold. Punctuation, apostrophes and order remain significant. There are no
gaps, stemming, synonyms, punctuation repairs or paraphrase matches. Every
maximal diagonal exact run of at least eight tokens is retained, including
ties, overlaps and repeated occurrences. Coverage unions query-token indices
rather than double-counting repeated witnesses. All below-threshold longest
runs remain visible.

| Query | Tokens in query | Longest exact run | Runs at least 8 tokens | Query tokens covered by qualifying runs |
|---|---:|---:|---:|---:|
| quote02 | 67 | 22 | 1 | 22 |
| quote03 | 80 | 2 | 0 | 0 |
| quote04 | 31 | 2 | 0 | 0 |
| quote05 | 39 | 2 | 0 | 0 |
| quote06 | 76 | 2 | 0 | 0 |
| quote07 | 82 | 2 | 0 | 0 |
| Total | 375 | — | 1 | 22 |

The **22/375** covered-token count is descriptive coverage under this exact-run
rule, not semantic translation accuracy, source uniqueness or general reuse
coverage. The eight-token threshold is a reporting cutoff, not a significance
test. No probability or independent corroboration is inferred.

The retained quote02 run has these half-open coordinates:

| Coordinate system | Span |
|---|---|
| quote02 tokens | [20, 42) |
| Publisher-body tokens | [1156, 1178) |
| quote02 Unicode characters | [112, 239) |
| Full frozen FL-target Unicode characters | [1353, 1480) |
| Publisher-body Unicode characters | [7310, 7437) |

Exact raw fragments, normalized token sequences, all counts and union coverage
are retained locally in [assessment.json](../data/v44/assessment.json).
The [frozen query ledger](../data/v44/frozen_queries.json) keeps all six targets
and the two original control queries. Source prose is not published.

## Controls, verification and limits

Known quote00 has a 23-token run, meeting the predeclared minimum of 23 after
allowing its two enclosing boundary tokens. The short instrument name has a
four-token run and remains below eight. The eight-token nonce control has
longest run zero. Reversed quote00 has longest run one and no qualifying run.
All four controls pass, so the six-query readout is valid. These are engineered
or already exposed controls, not independent natural validation.

The [independent verifier](../scripts/verify_exact_fragments_v44.py) uses a
suffix-length dynamic program and maximal right ends rather than the scorer's
left-start extension algorithm. It reproduces every retained run, longest
length, original Unicode/token coordinate, global target offset and coverage
union, as well as all control decisions. All **43 previous runs and deliverable
seals** remain intact. The verifier was written after scoring; both programs
implement the same declared normalization. This is same-agent engineering
verification, not independent scientific review. See
[verification receipt](000044_verification.json) and
[immutable report](../runs/000044_exact_fragments/report.json).

**345/345 full-workspace tests** and **306/306 isolated-public-export tests**
pass. The five new tests cover repeated/tied and overlapping runs, thresholds,
union coverage, punctuation/apostrophes, gaps/order, Unicode coordinates and
unavailable separation. The same 39 archive-dependent tests remain excluded
from the public suite.

This finding establishes an exact partial English overlap in these saved files.
It does not establish copying direction, original historical contents, opaque
FL ancestry/meanings, whole-post source identity or a new untouched source work.
No semantic labels or independent reviews are admitted. Natural-benchmark
capacity remains unmet; semantic metrics and scientific acceptance remain null.

Next bounded step: make a **quote02 context dossier** using the frozen target
and source paragraphs. Keep the 22-token witness fixed, show its surrounding
English context and nonmatching text with separate coordinates, and distinguish
publisher-reported attribution from original-source authentication. This would
produce a reviewable correspondence record before any opaque-passage alignment;
no further search or semantic mapping was performed in experiment 44.
