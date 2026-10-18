# Experiment 35: adjacent-transposition alignment

The registered synthetic recovery gate passes. Adding a fixed-cost adjacent
crossing block recovers all **658/658 affected positions** in the same 329
unequal-symbol swap worlds where v34's forced-only policy returned none.
Every returned primary position agrees with its generated origin and occurs
in every optimum under the registered new model.

The 26 strict-origin disagreements in the thirteen equal-symbol swap worlds
remain. The new operation addresses visible local order changes; the v34
identical-input ancestry limit remains intact. Neither the earlier failed
hypothesis nor any original prediction is changed.

## What changed and what stayed frozen

The decoder and 96-entry v32 mapping remain unchanged. The new path model permits
a block consuming two adjacent query and source tokens, crossing their matches
when all symbols are known, distinct within the block, and unblocked. Its cost
is one, compared with two for a deletion and insertion. Ordinary matches cost
zero and gaps cost one. Blocks cannot overlap, although several disjoint blocks
can occur in one path. This is a specific local operation, not arbitrary
reordering or a learned translation mechanism.

The fixed objective minimizes total cost and then maximizes matched-token count
among cost ties. Trace priority and every optimal-path definition were registered
before scoring. Coverage still requires at least 24 matches and 4/5 of each
full token sequence, including unknown forms and barriers. Synthetic panel
decisions retain the v32 unique-qualifying-top rule and tie abstention.

All 335 original v34 public observations, 684 worlds, 378 site rows and 36
exclusions are preserved. Six identities are reused as controls, and 36 new
observations provide the other controls: 371 distinct observations, 42 control
rows and eighteen panels. All world and control denominators remain explicit;
content reuse and repeated contexts are not independent trials.

## Primary recovery and ancestry limits

| World stratum | Worlds | Affected positions | v35 forced exact / returned |
|---|---:|---:|---:|
| Equal symbols, identity | 13 | 26 | 26 / 26 |
| Equal symbols, swapped | 13 | 26 | 0 / 26 |
| Unequal symbols, identity | 329 | 658 | 658 / 658 |
| Unequal symbols, swapped | 329 | 658 | 658 / 658 |

The unequal-swap affected denominator is unchanged from v34. Forced coverage rises
from 0/658 to 658/658, with 658 exact origins. The old representative policy had
returned 330 positions, one at the wrong origin. All 20,862 mapped identity-world
positions are retained as forced origin-exact matches.

Across all worlds, both representative and forced policies return 41,724 known
matches from 43,776 query tokens. Of these, 41,698 are strict-origin exact;
26 are the preserved equal-symbol ancestry disagreements. Affected-position
precision across all four strata is 1,342/1,368. The synthetic recovery gate
targets visible unequal swaps and controls; it is not a universal exact-ancestry
gate, and the full denominator still contains the equal-swap errors.

All thirteen identical-input collision certificates still verify. Across their
balanced identity/swap worlds the affected calls are 26/52 origin-exact, the
same point-answer bound as before. No new observation identifies which identical
occurrence supplied a token. Symbol compatibility accepts these occurrences by
construction and remains a consistency check, not independent accuracy or meaning.

A concrete recovered case is passage 0, swap site 13. The old representative
matches query 13 to source 14 and query 14 to source 15; the latter origin should
be 13. The new operation maps `[13,14]` and `[14,13]`, both forced, and reduces
whole-sequence edit cost from eight to seven. The source symbols at positions
13 and 14 are `symbol8` and `symbol13`. The
[witness ledger](000035_witnesses.json) preserves exact query/source token spans,
all 329 recovered sites and all 26 retained ancestry disagreements.

## Controls and panels

| Control family | Pairs | Representative matches per pair | Qualified pairs | Behavior |
|---|---:|---|---:|---|
| Identity | 6 | 61 | 6 | All known positions retained exactly |
| Unknown-all query | 6 | 0 | 0 | No guessed labels or matches |
| Unknown swap endpoint | 6 | 60 | 6 | Unknown endpoint unmatched; other affected token recovered |
| Barrier swap | 6 | 61 | 6 | Known token recovered through gaps; no crossing block consumes a barrier |
| Fully blocked source | 6 | 0 | 0 | No matches |
| Rotated-symbol impostor | 6 | 14–19 | 0 | Below fixed coverage; no parent nomination |
| Unique frame source | 6 | 0 | 0 | No matches |

Unknown-endpoint and barrier-swap controls each recover one of their two affected
tokens in every passage, leaving the unknown or blocked token unmatched. Their
remaining known context allows qualification. These controls test local guards,
not whole-query rejection whenever one token is unknown. Gaps can align known
tokens around barriers; barriers are unmatched tokens, not segmentation walls.

All eighteen zero-match controls and all six impostors fail coverage. Impostors
can still have local matches and crossing operations; the rejection result
depends on the fixed full-sequence coverage rule. Their source origins and
origin precision are deliberately null rather than fabricated.

All six present panels recover slot0. All six source-absent panels abstain for
insufficient coverage. All six duplicate-parent panels abstain on a top tie.
The control classes are registered, exposed fixtures; this is not a calibrated
natural-source false-positive rate.

## All-optimal-path accounting and verification

Every original v34 observation now has the same matched-pair set across all
optima. Seven new control observations retain matched-pair ambiguity: six
impostors and one unknown-endpoint case. Full alternative operations, possible
token pairs, supporting-operation indexes, exact path counts and both complete
token ledgers remain available.

The audit aggregates support at the token-pair level. A pair can be present in
every optimum even if a diagonal produces it on one path and a crossing block
produces it on another. The exhaustive tests include such a case. Pair-invariant
operation multiplicity is recorded separately from matched-pair ambiguity;
operation counts are not confidence probabilities.

All 309 tests pass, including exhaustive enumeration over 1,600 tiny sequence
pairs, collective pair support, multiple disjoint crossings, the secondary
objective, equal/unknown/blocked forms, empty inputs, coverage boundaries and
qualified duplicate ties.

The independent verifier reconstructs all controls and panels. It replaces the
primary tuple-cost/path-support calculation with an integer-weighted DAG and
mandatory token-pair bitsets, and agrees on all 371 predictions, path counts,
operation alternatives, pair supports, token ledgers, 684 world scores and
registered gate conditions. All 34 prior run inventories and deliverable seals
verify unchanged. Independent implementation does not count as external review.

Code freezes before controls, controls before prediction, and predictions before
loading the new oracle for assessment. Model payload hashes agree before and
after prediction. Natural scientific acceptance and semantic metrics remain
null. No source identity, meaning, independent review, untouched admission,
external/neural model run or natural-target rescore occurs.

Artifacts: [registration](../experiments/adjacent_transposition_v35.md),
[preflight](../data/v35/preflight.json),
[public inputs and panels](../data/v35/public_observations.json),
[complete oracle](../data/v35/oracle.json),
[predictions](../runs/000035_adjacent_transposition/predictions.json),
[prediction receipt](../runs/000035_adjacent_transposition/prediction_receipt.json),
[assessment and control decisions](../runs/000035_adjacent_transposition/assessment.json),
[immutable report](../runs/000035_adjacent_transposition/report.json),
[verification](000035_verification.json).

```sh
uv run python scripts/verify_adjacent_transposition_v35.py
```

## Next evidence boundary

Freeze v35 at this exposed single-swap mechanism result. Register a fresh
synthetic mixed-edit test before generating its passages: combine insertions,
deletions, disjoint swaps and withheld forms with fixed full-token denominators,
source-absent/impostor/duplicate controls and separate identifiable-position
metrics. Reuse this mapping and aligner without further tuning. Preserve
equal-symbol ancestry uncertainty and model-mismatch failures. Passing this
small exposed family does not authorize natural target scoring or word meanings.
