# Experiment 33: frozen optimal-alignment ambiguity audit

Registered before computing v33 outcomes. This is a diagnostic follow-up on
exposed synthetic v32 data, not an independent holdout or natural-language test.

## Fixed scope

Audit every one of the 2,520 distinct frozen v32 query/candidate alignments.
Retain all 420 queries, 2,100 panels and 420 true-parent pairs, including the
300 unqualified parent pairs. Primary positional assessment uses the same 120
qualified true-parent pairs and their 6,772 representative matches. These
denominators are inherited, not selected using this audit's results.

Hash-bind public tokens, decoded queries, model, original predictions, origin
oracle, assessment, v32 manifest and seals. Do not train, change scores or
coverage, rerank panels, replace representative traces, or rescore FL targets.
Structural auditing has no oracle argument and is saved before origin assessment.

## Rule

Use the frozen full global insertion/deletion model: gap cost one, equal known
symbol diagonal cost zero, no other diagonals. Blocked and unknown query forms
remain gaps. Compute minimum prefix/suffix costs and exact operation-path
counts. A diagonal is possible iff prefix cost plus suffix cost equals the
global optimum. Its through-path count is prefix ways times suffix ways.
A possible match is forced iff that count equals all optimal operation paths.
These integer counts are combinatorial accounting, not probabilities.

Preserve all possible diagonal alternatives with token indices into the frozen,
hash-bound views. Per token on both sides, retain all possible partners and
whether a gap occurs on any optimum. Distinguish forced match, always matched
with ambiguous partner, optional match/gap, and always gap. Retain original
representative matches separately; keep only forced matches in the diagnostic
retained-position policy. This policy does not change retrieval qualification.

## Falsifiable hypothesis and accounting

The synthetic hypothesis is: every retained forced match in the fixed primary
120 pairs agrees with its generator origin, and each primary pair retains at
least one match. It fails on any forced origin disagreement or empty pair.
Report failure without revising the monotonic model or filtering mechanisms.
A forced optimum may still be wrong under local reordering or repeated symbols.

Report exact precision fractions and retained fractions over all 6,772 original
primary matches, all query tokens in those pairs, and all query tokens across
the 420 parent pairs. Break out group and mechanism with zero denominators
explicitly retained. Show original wrong matches removed versus retained,
correct matches discarded, gap-order-only versus matched-pair ambiguity, and
whether each original origin disagreement has its true edge on any optimum.
Secondary summaries cover all parent pairs and all 2,520 candidate pairs.
Dependent keys/passages/panels are not independent statistical trials.

## Engineering verification

All frozen optimum costs, operation-path counts and representative matches must
agree. Every forced match must occur in the representative path and be possible;
forced matches must be monotonic and injective. Token ledgers must cover both
complete token sequences, including no-match pairs. Unknown/blocked positions
must never gain a match. The original mapping, decisions and traces are immutable.

Independently reconstruct decoded forms from the frozen model; compute maximum
LCS tables, possible diagonals via prefix/suffix scores, and forced diagonals
by intersecting match-edge sets over all optimal prefixes (DAG dominators).
Verify exact operation counts, ledgers, origin accounting and aggregates without
importing the primary audit module. Tiny exhaustive enumerations and edge-deletion
fixtures validate both implementations, including gap-only multiplicity, repeated
symbols, ambiguity, blocked tokens, empty inputs and forced-but-wrong origins.
Verify all 32 prior run inventories and earlier deliverable seals unchanged.

Natural scientific acceptance and semantic metrics stay null. No source identity,
meaning, independent review, untouched admission or external/neural model run.
