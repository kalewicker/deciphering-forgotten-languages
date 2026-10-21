# E78: read-only decomposition of E77's saved errors

Freeze this protocol, code and input hashes before computing the decomposition.
E77's aggregate outcomes are already known. This is a retrospective diagnosis,
not a new predictive test, success gate or independent replication.

Use all 13 original folds, all 1,918 targets and all 99 saved controls. Do not fit
new models, generate predictions, rerun E77, change vocabulary or masks, select
favorable groups, acquire text or score alternative parameters.

For each saved target, reconstruct the original training token and adjacent-pair
counts from E76's retained eligible units, using E77's original fold vocabulary
and unknown mapping. Bind UID, token indices, group and raw source offsets.
Partition targets by target category (known/unknown), context category
(known/unknown), and natural-training support:
- unseen_context: zero outgoing training pairs for this context;
- unseen_pair: positive context count but zero count of this context-target pair;
- seen_pair: positive pair count.
This makes 12 fixed cells per group, including empty cells. These support labels
always refer to original training counts, including when summarizing saved
shuffled-control losses. Also tabulate original target form status as known,
training_singleton or training_absent. These categories describe exposure to
training, not semantic knowledge.

Use only saved unigram, observed-context and control probabilities for loss
calculations. Preserve each target's gain log2(P_context/P_unigram) and all 99
control gains. For every cell, report count, summed gain, mean gain (null if empty),
and its contribution to the original group gain: summed gain / ALL targets in
that group. Average these contributions over all 13 groups, including zero
contributions from empty cells. Their sum must reproduce E77's primary macro
statistic. Report each draw's contribution in the same cells; do not replace
E77's ranks or gate. A cell mean is descriptive, not a subgroup success claim.

Check the algebraic implications of E77's fixed formula: zero outgoing context
count implies zero gain; a seen context with an unseen pair implies gain
log2(10/(context_count+10)), strictly negative. Reconstruct counts to attribute
losses, not to calculate counterfactual predictions or optimize smoothing.
Known-target conditional macro gain and its denominators must also reproduce
E77. Preserve raw-form absence/singleton totals, all controls and negative cells.

A separate verifier must independently rebuild count/status assignments, every
stored gain, complete partitions, fold totals and macro/control contributions.
Fixture tests cover zero cells, backoff, unseen-pair algebra, unknown status,
partition accounting and unequal group weighting. Verify E76/E77 seals and
hash-bound inputs. Preserve all historical files and E77's failed gate.

Stop after one report. This diagnosis cannot establish causal effects of changing
unknown handling or smoothing, validate meanings, or justify a favorable rescore.
It may motivate a separately justified proposal, but no model change is launched.
No new source identity, semantic label, independent review or untouched unit;
the natural semantic benchmark remains 0/4 qualifying works.
