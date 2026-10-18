# Experiment 35: adjacent-transposition alignment

Registered before v35 fixtures/outcomes. Exposed synthetic mechanism test, not
independent holdout evidence or a natural-language evaluation. Preserve v1–v34.

## Frozen inputs and new model

Reuse the unchanged v32 mapping, every one of v34's 335 public observations,
378 site rows, 36 exclusions and 684 worlds. Primary target: the same 658 affected
query positions in all 329 unequal-symbol swap worlds. Keep identity worlds,
equal-symbol worlds, full-token denominators and repeated-content accounting.

Extend the full global indel path by a two-query/two-source transposition block.
It maps the first query token to the second source token and vice versa. Both
decoded query symbols must be known and distinct; both source tokens must be
unblocked, distinct, and equal to the crossed decoded symbols. Diagonal matches
cost zero, query/source gaps cost one, and a transposition block costs one.
No mismatch substitution. Blocks consume their two positions, so operation
blocks cannot overlap; a path may contain multiple disjoint blocks. This is
not a general arbitrary-reordering model.

Minimize (total cost, negative matched-token count) lexicographically. The
secondary objective is fixed now; it equals v32's match maximization without
transpositions. Define all optima using both components. Representative traceback
priority: diagonal match, transposition, query gap, source gap. Count every
optimal operation path exactly. Retain full paths, possible matching operations,
all possible token pairs and complete token ledgers on both sides.

A token pair can occur through different operations on different paths. Sum its
through-path counts across all supporting operations before declaring the pair
forced; a forced pair need not have a forced supporting operation. Each token
is consumed exactly once on a path, so these support events are disjoint.
Counts are combinatorial accounting, not probabilities. Report representative
and forced-pair policies separately.

Coverage remains at least 24 matches and at least 4/5 of each full token sequence.
Score candidate pairs by matched count under the fixed objective. Synthetic
panels use unchanged v32 unique-qualifying-top decision/tie abstention. This
creates new synthetic predictions only; no old score, trace or panel changes.

## Controls frozen before scoring

For each of the six v34 base passages use its identity observation, plus:

1. Unknown-all query: replace every nonblocked alias with a unique unseen
   `v35unknownallp{passage}at{index}` form; preserve barriers and length.
2. Unknown endpoint: take its first unequal swap site (lowest left index), swap
   the two query aliases, then replace the left query token with unseen
   `v35unknownendpointp{passage}`. Preserve the generator origins and unknown flag.
3. Barrier swap: take its first adjacent site touching a blocked source token,
   and exchange the query tokens and origin indices. Matching a known token by
   gaps is allowed; no transposition may consume any blocked token.
4. Blocked source: replace every source token with `copiedanchor0`.
5. Impostor: rotate each nonblocked source `symbolC` to `symbol((C+1)%24)`;
   retain source barriers and the identity query.
6. Frame source: replace each nonblocked source form with unique
   `v35framep{passage}at{index}`; retain barriers and the identity query.

These are 42 control rows including six reused identities. Content-address and
deduplicate all public observations while preserving every world/control row.
Unseen forms must be absent from frozen model entries and ledger. No oracle
origin is asserted for blocked-source, impostor or frame-source pairs.

Create three panels/base: present (identity, impostor, frame); absent (impostor,
frame); duplicate (two identity slots sharing the same observation, impostor,
frame). Retain all eighteen panels. Expected slots/roles stay in the oracle.
Predictor inputs contain only source/query views; public panels contain only
anonymous slots and observation references. No site, origin, mechanism, role,
relation or world label enters the aligner.

## Registered synthetic recovery gate and accounting

Pass only if all 658 unequal-swap affected positions are returned as forced
origin-exact pairs; all mapped identity-world positions are forced and exact;
no unknown/blocked token participates in any possible optimal match or block;
all eighteen unknown-all/blocked-source/frame pairs score zero and fail coverage;
all six impostors fail coverage; six present panels select slot0; six absent
and six duplicate panels abstain. Preserve failure without tuning any rule.

Keep all thirteen equal-symbol collisions and both histories. Report their
strict-origin disagreements and balanced point bound without excluding them
from overall totals. An unchanged visible order need not imply unchanged ancestry.
Symbol compatibility retains v34's definition and is a consistency check implied
by fixture labels and allowed edges, not independent accuracy or semantics.

Report full and affected origin/compatibility/coverage fractions for all 684
worlds and all four relation/world strata, plus the fixed v34 baseline delta.
Show new control outcomes, every panel decision, costs, matched counts,
transposition counts, optimal-path ambiguity and possible alternatives. Counts
reuse source passages and identity observations, not independent statistical
trials. Distinguish pair precision with zero returns from actual recovery.

## Freeze and independent verification

Code freezes before controls, controls before predictions, predictions before
loading the new oracle for assessment. Mapping payload is immutable. Independently
reconstruct controls and panels; replay alignment with an integer-weighted DAG
objective and mandatory token-pair bitsets, instead of the primary tuple-cost
and through-path aggregation implementation. Verify all traces, operation/pair
supports, token ledgers, metrics, baseline comparisons and preserved v34 worlds.
Use exhaustive tiny-path enumeration, including repeated symbols, collective
pair support across operations, empty/unknown/barrier inputs and multiple disjoint
blocks. Verify all 34 earlier run inventories and deliverable seals unchanged.

Natural scientific acceptance and semantic metrics stay null. No new source,
meaning, identity, untouched admission, independent reviewer or external/neural
model; no natural FL rescoring.
