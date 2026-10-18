# Experiment 36: frozen-model mixed edits, hard competitors and mapping errors

Registered before generating any new passages or computing predictions. This is
one bounded synthetic transfer test followed by a read-only natural-evidence
feasibility audit. No outcome authorizes another aligner change in this run.

## Fixed design

Use the exact v32 mapping and v35 aligner, decoder, objective, trace priority,
all-optimal-path policy and unique-qualifying-top decision. Minimum matches 24;
both complete token sequences require at least 80% matched coverage. All unknown,
inserted and blocked tokens stay in the denominators. No fitting or threshold
selection. The generator family is declared development machinery, not a blind
external evaluation or a new language. New contexts are generated only after
the registration, implementation, tests and evidence inputs are hash-sealed.

Sixteen new 72-token parents: keys 11,29,47,83 crossed with passages 0..3.
For each source position i, symbol = integer SHA256 of
`v36|fresh-context-20261018|parent|key|passage|i` modulo 24. Positions 17,35,53
are copiedanchor0,1,2 instead. This does not reuse v32-v35 passage sequences.

Five profiles per parent, retaining all 80 queries:

| Profile | Deleted source indices | Unknown origin indices | Adjacent swap left indices | Insert after origin indices |
|---|---|---|---|---|
| identity | none | none | none | none |
| light | 6,26 | 10,30 | 12,40 | 15,45 |
| moderate | 6,26,46,66 | 10,30,50,62 | 8,20,40,58 | 15,31,47,63 |
| dense_unknown | 6,14,26,34,46,54,66,70 | 2,10,22,30,42,50,60,64 | 8,20,40,58 | 3,11,19,27,39,43,55,67 |
| block_mismatch | same as moderate | same as moderate | same as moderate | same as moderate |

Apply swaps to source-origin order, then reverse origins 38..45 for block_mismatch,
then delete origins; encode surviving symbols with the original v32 aliases.
Unknown origins use withheld parity-1 aliases. Insert unique unmapped strings
after the indicated surviving origins. Keep equal-symbol swaps and every origin;
do not regenerate passages to avoid ambiguous or difficult cases.

Each query has five candidate pairs: parent; a near-copy swapping the first
unequal pair selected from `(1,61),(2,62),(3,63),(4,64)`; an eight-substitution
near-copy at 1,9,21,29,41,49,61,69 (+1 modulo24); a histogram-preserving
shuffle of all nonbarrier positions sorted by SHA256 of
`v36|fresh-context-20261018|shuffle|key|passage|i`; and a fresh unrelated
generated context using `unrelated` in place of `parent`. If all four near-copy
pairs have equal symbols, retain the byte-identical collision and mark it.
These are operational nonparent units with known generator provenance. Sharing
copied text makes them deliberately hard; they are not certified natural
unrelated documents and do not estimate a natural false-positive rate.

Three panels per query: all five candidates; parent absent (four); duplicate
parent (six). Slot order is SHA256 of `query_id|scenario|candidate_role`.
Query IDs are `k{key}p{passage}{profile}`. Duplicate slots have distinct names
and identical observations. Prediction sees only source/query token views and
slot IDs, never generator origins, profile, key, passage or candidate role.

## Mapping-error intervention

Clean branch uses the original 96 entries unchanged. Two diagnostic branches
copy it: sparse swaps symbols 0 and 1 for each key (8/96 entries); dense cycles
symbols 0..7 to (symbol+1) modulo8 (32/96 entries). Only `source_form` in entries
changes; the original support ledger remains visibly inconsistent by design.
These are injected errors, not learned alternative models. Branches are frozen
before prediction and never update the original mapping or each other.
All three branches score all 400 pairs and 240 panels: 1,200 alignments,
720 panel decisions. Reused parents, keys, profiles, branches and panels are
dependent observations, not independent trials.

## Outcomes and fixed decision

Primary clean branch comprises all 32 light/moderate queries, with all their
tokens and all parent/source-absent/duplicate panels. Require:

1. 32/32 parent-present panels uniquely select the parent.
2. 0/32 parent-absent panels nominate any nonparent.
3. 32/32 duplicate panels abstain.
4. Across their true-parent pairs, forced matches have >=99% strict-origin
   precision and >=90% coverage of surviving, mapped, unblocked origin tokens.

All four are required for the synthetic transfer gate. No case replacement,
seed change, threshold change, profile removal, alternate target or rerun after
results. Identity, dense_unknown and block_mismatch remain in complete summaries
and are diagnostic; dense_unknown is deliberately below potential coverage.
Mapping-error branches are diagnostic, with no claim that the model can detect
their corruption. Negative outcomes are retained.

Report by branch/profile: complete query/source tokens, known recoverable
tokens, affected-known tokens, uniquely occurring source-symbol positions,
repeated-symbol positions, representative/forced returned/exact-origin/true-
symbol-compatible counts, wrong calls and unmatched positions. A singleton
symbol identifies its occurrence conditional on the intended source and correct
mapping; it does not identify the source work. Repeated ancestry uncertainty
remains explicit. True-symbol compatibility is assessed from generator truth,
separately from compatibility under the possibly corrupted model.

Freeze prediction files and model hashes before loading oracle for assessment.
Replay every pair with the existing independent v35 integer-DAG/mandatory-pair
implementation, independently recompute panel decisions and metric sums, verify
generator edit/provenance invariants and all previous run/seal inventories.
Independent implementation by this assistant is not external review.

## Stop and natural-evidence decision

Stop synthetic development after this experiment, whichever way the gate goes.
Audit saved natural evidence without new scoring or reclassifying old exposures.
Inventory connected source groups, full-post versus excerpt provenance, review
independence, correspondence status and exposure. An immediate untouched natural
benchmark is feasible only if at least four unexposed independent connected works
with hash-bound FL/source material and independent passage review are available:
two development and two test groups, with at least two nonoverlapping reviewed
passage units per group. This is a minimum pilot capacity rule, not statistical
power or semantic validation. Absent capacity means evidence acquisition/review
is the next bottleneck, not permission for another synthetic feature expansion.

Semantic metrics and natural scientific acceptance remain null; natural semantic
labels/source identities/reviews/untouched admissions and natural rescores remain
zero. Existing frozen evidence is preserved. No network or external contact.
