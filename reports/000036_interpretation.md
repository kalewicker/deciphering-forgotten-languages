# Experiment 36: mixed-edit transfer works conditionally; source-absence gate fails

The combined registered synthetic-transfer gate **fails**. With the unchanged
correct mapping and v35 aligner, all **32/32 primary mixed-edit queries** select
their generated parent when present. Remove that parent and all **32/32** instead
nominate the near-copy competitor. Alignment similarity does not establish the
immediate source unit or detect its absence in these deliberately difficult panels.

The mapping-error intervention also demonstrates that matches shared by every
optimal path can be wrong even about symbol identity. Engineering replay passes;
natural decipherment remains unvalidated. Synthetic feature expansion stops at
this registered decision boundary.

## Frozen design and complete denominators

Sixteen new 72-token parent contexts span four trained keys and four passages per
key. Each produces identity, light mixed edits, moderate mixed edits, dense
unknowns, and a block-reversal model mismatch: **80 queries**. Light/moderate
edits combine insertions, deletions, disjoint adjacent swaps and withheld forms.
Every query retains 72 tokens, including unknowns, copied barriers and insertions.

Five candidate pairs per query include the parent, a two-position near-copy,
an eight-substitution near-copy, a histogram-preserving shuffle and an unrelated
generated context. Present, absent and duplicate panels retain every candidate
and top tie. Clean, sparse-error and dense-error dictionaries each score all
400 distinct pairs and 240 panels: **1,200 alignments and 720 decisions**.

The original 96-entry mapping, aligner, edit costs, 24-match minimum, 80% coverage
on both full sequences and decision rule are unchanged. The diagnostic sparse
dictionary corrupts 8/96 entries; dense corrupts 32/96. Neither intervention
changes the original mapping or the other branch. Support ledgers deliberately
remain inconsistent with the injected entries; these are not learned models.

Contexts are fresh, but the generator family, trained keys, operation model and
test design are exposed development machinery. The sixteen parent contexts,
their profiles, keys, candidate copies and interventions are dependent evidence,
not 1,200 independent trials or a natural-language held-out benchmark.

## Registered primary gate

The complete primary panel is all 32 light/moderate queries under the clean
mapping, with no exclusions or substitutions after scoring.

| Requirement | Observed | Outcome |
|---|---:|---|
| Correct unique parent when present | 32/32 | Pass |
| Zero nonparent nominations when parent absent | 32/32 nominate near-copy | **Fail** |
| Duplicate-parent abstention | 32/32 | Pass |
| Forced strict-origin precision >=99% | 1,992/2,000 = 99.60% | Pass |
| Forced coverage of recoverable tokens >=90% | 2,000/2,016 = 99.21% | Pass |

All four registered requirements are necessary; precision and coverage are
checked separately. The combined gate remains failed despite good true-parent
alignment. Near-copy alternatives intentionally share most text with the parent.
Their generator provenance identifies them as distinct nonparent units, but
they are not natural unrelated documents. The 32/32 result is a conditional
failure demonstration, not an estimated real-world false-attribution rate.

The full primary query denominator is **2,304 tokens**. Forced matches cover
2,000/2,304 (86.81%), including 1,992 exact origins and eight wrong occurrences.
The 2,016 recoverable-token denominator excludes only known generation-time
insertions, withheld forms and barriers; the excluded 288 tokens remain in the
full-token denominator and the original qualification rule.

Affected known positions expose more difficulty than the aggregate: **181/189
returned** are origin-exact, with 189/192 affected-known positions returned.
All eight wrong origins are on affected tokens. All 2,000 primary returned
symbols agree with generator symbol truth, so these eight errors concern repeated
occurrences rather than different symbols. The singleton-symbol stratum returns
103/103, all origin-exact. This does not prove every repeated-position error is
unidentifiable; the complete paths and origins remain available for inspection.

## Mapping errors and limits of forced matches

| Mapping branch | Primary present parent recovered | Primary absent nonparent nominations | Primary duplicate abstentions | Primary forced origin exact / returned | Primary wrong-symbol matches |
|---|---:|---:|---:|---:|---:|
| Clean | 32/32 | 32/32 | 32/32 | 1,992/2,000 | 0 |
| Sparse: 8/96 entries wrong | 23/32 | 14/32 | 32/32 | 1,852/1,872 | 14 |
| Dense: 32/96 entries wrong | 0/32 | 0/32 | 32/32 | 1,309/1,394 | 82 |

The match counts in this table describe the forced token ledger on every
true-parent pair, including pairs that fail whole-sequence qualification. They
are not all accepted panel outputs. Reduced absent-parent nominations under
corruption do not establish improvement: coverage and parent recovery collapse.

Restricting to **qualified** true-parent pairs across all five profiles, the
sparse branch still has **19 wrong-symbol forced matches among 2,414 returned**
in 39 pairs. Thus the failure is not confined to rejected low-coverage pairs.
One witness, k11p3identity query token69, truly comes from source69 `symbol1`;
the corrupted dictionary decodes it to `symbol0`, and every optimal path matches
it to source70 `symbol0`. Both symbols occur only once in that source. This is
an upstream mapping error even in the singleton-symbol stratum.

For comparison, the clean k11p3moderate query58 truly comes from source59
`symbol5`, while the forced call returns source58, also `symbol5`. The
[witness ledger](000036_witnesses.json) contains all eight clean primary origin
errors and all nineteen sparse qualified-pair symbol errors with exact token
spans, the original query aliases, decoded forms and generator origins.

## Diagnostic profiles remain visible

| Clean profile | Queries | Parent nominations when present | Nominations when parent absent | Duplicate abstentions |
|---|---:|---:|---:|---:|
| Identity | 16 | 16 | 16 | 16 |
| Light mixed edits | 16 | 16 | 16 | 16 |
| Moderate mixed edits | 16 | 16 | 16 | 16 |
| Dense unknowns | 16 | 0 | 0 | 16 |
| Block reversal mismatch | 16 | 2 | 0 | 16 |
| Total | 80 | 50 | 48 | 80 |

Every dense-unknown query has only 53/72 potentially recoverable tokens, below
the frozen 80% rule. Its abstention is an expected availability restriction,
not evidence against contextual forms generally. Block-reversal results retain
the model mismatch and its repeated-origin errors. Neither profile is removed
from the complete 80-query, 5,760-token denominator per branch. The raw token
ledgers remain diagnostic even when a whole pair does not qualify.

## Natural-evidence feasibility and next decision

The separately reconstructed [natural-evidence audit](000036_natural_evidence_feasibility.md)
finds 25 reading-edition articles in 14 conservatively connected tracked groups;
all are exposed. The existing usable development panel has 19 units in five
groups. Two full dated-post dossiers support further source/passage review, but
their fixed publisher windows do not establish whole-post source coverage. The
supplied automated, source-disclosed review and evidence spans remain useful
development leads, with no admitted independent review or semantic gold.

There are **zero qualifying unexposed, independently reviewed connected works**
in this audited inventory, against the registered minimum pilot capacity of four
(two development and two test, each with two reviewed nonoverlapping passages).
The immediate untouched natural benchmark is therefore not feasible. This is a
statement about saved project evidence, not the whole FL archive or what might
be obtainable later. The minimum is a planning rule, not statistical power.

Stop synthetic feature expansion. The next bounded task is a source-first
evidence-acquisition and review-feasibility pilot with fresh connected works,
explicit exposure records and a fixed request budget. Preserve old groups as
development evidence. Do not turn the absent-source failure into success by
changing the coverage threshold or importing another edit operation. Fresh
natural evidence and a defensible review route are now the bottleneck.

## Preparation repair and verification

The first preparation attempt stopped before writing fixtures or making
predictions: inserted token labels included an underscore from the profile name,
which the frozen token view rejects. The failure, original preflight and original
code are preserved. A [registered presentation-only revision](../experiments/mixed_edit_transfer_v36_preparation_revision1.md)
removes that underscore from inserted-token surfaces; source contexts, edit
schedules, identities, unknown status, model and criteria stay fixed. A snapshot
helper's basename collision was separately recorded and the original module
recovered by reversing that one edit, with its pre-repair SHA-256 verified.
No favorable seed, case replacement or scientific rerun occurred.

All **315 tests pass**, including the profile-format and lineage regression
checks. The revised implementation is sealed before fixture generation; all
three prediction files and model hash receipts precede runtime oracle loading.
The independent integer-DAG/mandatory-pair implementation reproduces all 1,200
alignments and 720 decisions. Independent reconstruction also checks generator
edits/candidates, metric sums, the failed gate and the natural inventory. All
35 prior run inventories and deliverable hashes verify unchanged. The
[verification receipt](000036_verification.json) passes. Independent implementation
by the same assistant is not external scientific review.

Scientific acceptance and semantic metrics remain null. Natural source
identities, semantic labels, independent-review admissions, untouched-test
admissions, natural rescores, external/neural model calls, network requests and
external messages remain zero.

Artifacts: [registration](../experiments/mixed_edit_transfer_v36.md),
[original preflight](../data/v36/preflight.json),
[revised preflight](../data/v36/preflight_revision1.json),
[failure record](../data/v36/preparation_failure/receipt.json),
[public observations](../data/v36/public_observations.json),
[oracle](../data/v36/oracle.json),
[model interventions](../data/v36/model_variants.json),
[prediction receipt](../runs/000036_mixed_edit_transfer/prediction_receipt.json),
[complete assessment](../runs/000036_mixed_edit_transfer/assessment.json),
[natural inventory](../runs/000036_mixed_edit_transfer/natural_evidence_audit.json),
[immutable report](../runs/000036_mixed_edit_transfer/report.json).

Verify offline with `.venv/bin/python scripts/verify_mixed_edit_transfer_v36.py`.
Preparation and execution refuse existing evidence. Verification preserves its
successful receipt; do not rerun generation or scoring into this run.
