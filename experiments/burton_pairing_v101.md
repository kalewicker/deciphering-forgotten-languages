# E101 tests pairing specificity in the exposed Burton post

The panel is the same 22 prose pairs from E93 and E96–E100. Use the
package-assigned English row as the test label. The first 18 pairs come
from one excerpt and the last four from the other. The heading is outside
the panel. This is an internal development test of text-specific associations.
Semantic benchmark capacity remains 0/4.

## Fold design and frozen candidates

Tokenize each string as Unicode letter runs after case folding. Keep accented
letters. Digits, combining marks, punctuation and all other nonletters delimit
tokens. Apply no additional Unicode normalization. Preserve token
multiplicity only for lengths. For each query choose the other English row in
its excerpt with the closest token count to the assigned English. Break equal
distances by SHA-256 of the original English UTF-8, then by ordinal only for
equal hashes. Use the same choices for all methods. Record any absent alternative
as unscored. Candidate selection knows the assigned length. The scorer receives
candidate texts and never receives package ordinals, page positions, or the
answer label. Order the candidates by text hash and count exact score ties as ties.

Exclude the query and distractor rows on both sides from training. Also exclude
every training row whose token sequence on either side equals a withheld row's
sequence on that side. Within each fold mask identical token forms present on
both sides of the combined training and displayed test texts. This removes
literal shared forms, including names when identically spelled. Names rendered
differently and correlated topic words can remain. Masking uses test vocabularies
without their labels. Training can otherwise draw on either excerpt.

## Rule and controls

Represent each training row by token presence on each side. A query form must
occur in at least two training Yid rows to contribute. A candidate form must
occur in at least one training English row to contribute. For each eligible
Yid and English token pair, compute the fraction of training rows containing
the English form among rows with the Yid form, minus the overall fraction.
Average these differences over the Cartesian product of eligible query and
candidate forms. Use exact rational arithmetic. If the query or either candidate
has no eligible forms, abstain for all three methods in the comparison. Report
the support sizes per fold.

The length baseline estimates the median ratio of English to Yid token counts
from the fold's training pairs using pre-mask token counts. A candidate's score
is the negative absolute difference between its length and this ratio times
the query length. Report the baseline on the learned rule's scored rows.
The shuffle control repeats the same token rule with English training rows
permuted within each excerpt. Keep fold membership, input masking, support,
and candidates fixed. Use 999 deterministic SHA-256 keyed permutations per fold
with distinct replicate keys. Retain identity and repeated permutations.
The shared replicate index aggregates folds descriptively. Dependent folds and
overlapping training sets preclude interpreting this reference as a calibrated
significance test.

## Decision

Report wins, ties, losses and abstentions on all 22 queries and separately
for both excerpts. Use win = 1, tie = 1/2, loss = 0 and abstention = 1/2
for the all-query comparison score. Display unscored rows explicitly.
Before recommending a separate reserved-source replication, require coverage
of at least 16/22 overall and 2/4 in the short excerpt, an all-query score of at
least 0.65, improvement of at least 0.15 over both the length baseline and the
median shuffled score, and a score strictly above the empirical 95th percentile
of the 999 shuffled scores (nearest rank). These are practical development
criteria. A miss closes this rule on the panel with a recorded outcome.
A pass concerns within-work pairing discrimination and supports a later
replication decision. It leaves opaque meanings and generalization unresolved.

Seal the protocol, code, relevant prior evidence and fold plan before scoring.
Run one fixed rule and its controls. Check held-out exclusions and candidate
invariance with synthetic fixtures, then independently reconstruct the observed,
length and shuffled scores. Store the texts' token data and fold-level scores
locally. Publish methods and aggregate counts. End at this study's decision.
