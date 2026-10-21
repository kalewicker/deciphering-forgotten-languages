# E77: fixed grouped word-order prediction diagnostic

Freeze code, this protocol, E76 inputs and all shuffle orders before scoring.
Use every one of E76's 13 eligible connected groups and 98 retained units, with
all 1,918 recorded adjacent pairs as evaluation targets. No corpus edits or new
texts. Christisis stays excluded by E76. All material is exposed development
text; this is not an untouched semantic benchmark.

Question: does a fixed preceding-word model improve prediction of stored next
word categories over word frequencies, and over the same model fitted to
within-segment shuffled training text?

## Representation, models and folds

Use E76 tokens, masks and pair flags unchanged. Partition each retained unit into
maximal unmasked segments connected by pair flags. Singleton segments contribute
to frequency counts but have no prediction target. No prediction crosses a
barrier or unit boundary. Preserve UID, token indices and original offsets.

Run exactly 13 leave-one-connected-group-out folds. Training vocabulary comprises
forms appearing at least twice among all unmasked training tokens. Map training
singletons and evaluation forms outside this vocabulary to one reserved `<UNK>`
category; no evaluation counts enter vocabulary or fitting. The output alphabet
is training vocabulary plus `<UNK>`. Unknown-category prediction does not predict
the spelling or meaning of an unseen word.

Unigram probability: (training token count + 0.5)/(training tokens + 0.5*K).
Context probability for previous category h and target category w:
(c(h,w) + 10*P_unigram(w))/(c(h) + 10), where c(h) counts outgoing within-segment
pairs, not all occurrences. An unseen context backs off exactly to the unigram.
Both models score the identical recorded target pairs in actual evaluation text.
Use base-2 negative log probability and average within each group. No tuning,
alternative smoothing, feature expansion or fitted hyperparameters.

For each draw 0..98, each segment independently permutes its original token
indices by SHA-256 of `v77|draw|uid|segment_start_token_index|token_index`, breaking
ties by token index. Save all orders before scoring; keep identities and duplicate
orders. Reuse the same draw across folds, but include only training groups in
fitting. Preserve segment lengths, masks and per-segment token histograms. Each
shuffle shares its fold's original training vocabulary and unigram probabilities.
The evaluation sequence is never shuffled. This control changes endpoint/context
counts as well as pair associations; it tests this fixed sequence procedure.

## Fixed metrics and gate

Primary gain is unigram loss minus observed context loss, averaged equally across
all 13 groups. Retain each group's losses, gains, pair count, unknown context and
target counts, and target-known-only losses. Report a token-weighted summary only
as secondary. Unknowns stay in the full denominator; also report the macro gain
on known targets separately, retaining all 13 groups.

Each control draw has its own macro gain computed against the same unigram.
Report conditional rank (1 + count(control_macro_gain >= observed_macro_gain))/100,
including ties. This is a descriptive control rank for dependent folds and the
fixed exposed corpus, not a calibrated population p-value or confidence interval.
Report the full control distribution and group range; do not treat 1,918 pairs
as independent samples or bootstrap overlapping folds as independent replicates.

The development gate requires: observed macro gain >=0.05 bits/target; strictly
positive gain in >=10/13 groups; >=20 known targets in every group; strictly
positive macro known-target gain; conditional rank <=0.05. All components must
pass. A zero known-target denominator fails rather than dropping a group. These
are prospective practical criteria, not a claim of statistical power. Preserve
all failures, negative gains, unknowns and all 99 controls.

## Verification and stopping

Test barriers, vocabulary leakage, unknown handling, normalized probabilities,
backoff, shuffle reproducibility/histograms and equal group weighting. Freeze
inputs/code/control orders in a preparation receipt before a single scoring run.
Retain per-target probabilities for all models and all controls. An independent
implementation must reconstruct segments, vocabulary, category counts, every
probability/loss, control order, group statistic and gate without importing the
runner/model code. Check E76's seal and complete pair/group denominators.

Stop after this result regardless of outcome. No alternate vocabulary, model,
mask, seed, corpus expansion or favorable subgroup rerun. A pass supports only
transferable next-category regularity under these excerpts and preprocessing.
Templates, genre, copied residues and generator rules remain alternatives to
grammar. A failure does not establish meaningless text. No source identity,
meaning, independent review or untouched unit is admitted; semantic benchmark
capacity remains 0/4. Further work requires a separately justified question.
