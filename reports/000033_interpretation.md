# Experiment 33: optimal-alignment ambiguity audit

The engineering audit passes. The registered hypothesis that every forced
primary match agrees with its generator origin **fails**: eight disagreements
remain. Keeping forced matches removes twelve of the original twenty
disagreements and discards 252 correct positions. The original v32 result,
retrieval decisions, mapping, coverage rule and traces remain unchanged.

## Fixed result

The registration predates v33 outcome computation, but uses already exposed v32
synthetic data. It is a diagnostic follow-up, not an independent holdout.
All 2,520 distinct candidate pairs, 420 queries and 2,100 panels remain in scope.
The primary denominator is the original 120 qualified true-parent pairs.

| Primary positional accounting | Original representative | Forced-only diagnostic |
|---|---:|---:|
| Retained matches | 6,772 | 6,508 |
| Exact generated-origin matches | 6,752 | 6,500 |
| Origin disagreements | 20 | 8 |
| Exact-origin precision | 99.705% | 99.877% |
| Fraction of original matches retained | 100% | 96.102% |
| Fraction of all 7,680 primary query tokens retained | 88.177% | 84.740% |

All 120 primary pairs retain at least one forced match. The 264 removed
representative matches comprise twelve disagreements and 252 correct positions.
The retained fraction over all 26,880 query tokens in the full 420-query
source-present denominator is 6,508/26,880, or 24.211%. The 300 unqualified
parent pairs remain unqualified; this audit does not relax coverage to recover
their positions.

| Qualified group / mechanism | Pairs | Original matches | Forced matches | Forced exact | Wrong removed | Wrong retained | Correct discarded |
|---|---:|---:|---:|---:|---:|---:|---:|
| Seen / bijective | 24 | 1,464 | 1,464 | 1,464 | 0 | 0 | 0 |
| Seen / insertion | 24 | 1,464 | 1,464 | 1,464 | 0 | 0 | 0 |
| Seen / deletion | 24 | 1,248 | 1,240 | 1,240 | 4 | 0 | 4 |
| Seen / reordering | 24 | 1,252 | 996 | 988 | 8 | 8 | 248 |
| Sparse unknown / bijective | 24 | 1,344 | 1,344 | 1,344 | 0 | 0 | 0 |

All other group/mechanism cells have zero qualified pairs. Their explicit zero
denominators and all-parent diagnostics remain in
[assessment.json](../runs/000033_alignment_ambiguity/assessment.json).

## What ambiguity means here

Every primary pair has multiple optimal operation paths, but only 32 have
different matched-pair sets across those paths: eight deletion pairs and all
24 reordering pairs. The other 88 have identical matches with different gap
orders. Path multiplicity alone would incorrectly mark all their positions
ambiguous.

Across all 2,520 candidate pairs, 1,419 have matched-pair ambiguity and 1,101
have gap-order-only multiplicity. The latter includes all 720 pairs with no
matches. There are 68,013 possible diagonal edges, 48,060 matches in the original
representative traces and 36,992 forced edges. These candidate-pair counts reuse
query tokens and are not independent observations or unique-corpus coverage.

The full ledger preserves every possible match edge, its exact through-path
count, forced status and original representative match list. Both token
sequences have complete per-token ledgers distinguishing forced match,
ambiguous partner with no gap, optional match/gap and always gap. Indices point
into hash-bound v32 views with their original text and character offsets.
Operation-path counts are combinatorial accounting, not confidence estimates.

## Why eight disagreements survive

All twelve removed primary disagreements have their actual origin edge on some
optimal path. None of the eight retained disagreements has its origin edge on
an optimum under the frozen monotonic model.

The eight retained disagreements are the same two-position event replicated
under keys 11, 29, 47 and 83 in source passage 5. At zero-based positions 13
and 14, both source tokens are `symbol9`; their query aliases are also identical.
The generator swaps the two lineage labels. Every monotonic optimum instead
keeps the two occurrences in their visible order.

[The post-run evidence note](000033_origin_note.json) preserves all eight exact
token/offset witnesses and verifies equal source and query surfaces. Skipping
this equal-symbol swap would leave the visible forms unchanged while changing
lineage. That is observational equivalence under these two transformation
alternatives. The known generator recipe still defines strict origins; this
note does not revise that gold, exclude these errors or turn the failed
hypothesis into a pass. The four key variants are dependent repetitions.

A forced optimum establishes agreement within the alignment model. It does
not by itself establish historical token ancestry. Strict lineage and visible
symbol correspondence need separate evaluation targets when repeated symbols
can exchange places. This finding supplies no natural word meaning.

For completeness, the secondary diagnostic across all 420 true-parent pairs
finds 15,400 forced matches, 15,376 origin-exact, with 24 disagreements retained.
Those include below-coverage pairs and are not extra admitted positions. They
are separate from the fixed primary policy and its 6,508 retained positions.

## Verification and evidence limits

All 283 tests pass, including exhaustive enumeration over 1,600 tiny sequence
pairs, direct edge-deletion checks, gap-only multiplicity, repeated symbols,
empty inputs, blocked tokens, corrupted frozen traces/counts and forced matches
with wrong origins.

The independent implementation reconstructs decoded forms from the frozen map,
recomputes maximum-LCS prefix/suffix tables, and finds mandatory match edges by
intersecting edge sets over all optimal prefixes. It agrees with the primary
minimum-cost/path-product implementation on every pair, exact path count,
alternative edge, token ledger, origin disagreement and aggregate. This is an
independent algorithm implementation, not an external reviewer.

All 32 earlier run inventories and deliverable seals verify unchanged. The
structural ledger was saved before loading the origin oracle for assessment.
Scientific acceptance and natural semantic metrics remain null. No source
identity, semantic label, independent review or untouched test admission occurs;
no natural target is rescored and no external/neural model is executed.

Reproduce the verification without overwriting the run:

```sh
uv run python scripts/verify_alignment_ambiguity_v33.py
```

Key artifacts: [registration](../experiments/alignment_ambiguity_v33.md),
[preflight](../data/v33/preflight.json),
[all alternatives](../runs/000033_alignment_ambiguity/ambiguity.json),
[origin assessment](../runs/000033_alignment_ambiguity/assessment.json),
[immutable report](../runs/000033_alignment_ambiguity/report.json),
[verification receipt](000033_verification.json).

## Next evidence boundary

Stop v33 with its failed strict-origin hypothesis. Register a bounded paired-world
positional-identifiability test: identical-symbol swaps with equal public inputs
but different lineage, plus unequal-symbol swaps whose visible order changes.
Keep strict-origin results and observable correspondence results separate from
the start. This will establish what the evidence can distinguish before deciding
whether a richer reordering model addresses a recoverable error. Do not retune
v32, erase v33 disagreements or transfer these synthetic labels to FL text.
