# E76: saved excerpts support a small word-order development test

The registered corpus-capacity check **passes**. Thirteen of fourteen conservative
connected groups meet the fixed resource minima, providing **98 retained units,
2,189 unmasked tokens and 1,918 adjacent-word pairs** for a prospective grouped
prediction diagnostic. No predictor was trained or scored. This establishes
available observations under a fixed representation, not predictable word order,
grammar or meaning.

The user authorized this pivot while pursuing an independent reviewer separately.
It changes the observable question: a future predictor would be assessed against
actual stored next tokens, without using a disputed English correspondence as
its answer key. It does not reopen E30's source-localization hypothesis, the
stopped synthetic feature programme, or E62/E70 discovery routes.

## Complete selection accounting

The [registration](../experiments/order_corpus_v76.md) and
[hash-bound configuration](../experiments/order_corpus_v76.json) preceded the
capacity run. Earlier schemas and examples informed the design, so selection
is explicitly exposed development work.

| Disposition | Units |
|---|---:|
| Full annotation inventory, 25 articles | 1,026 |
| Excluded: article or unit not declared exactly Kamri | 48 |
| Excluded: no old scoped exact match to a saved FL excerpt | 871 |
| Exact-bound candidates | 107 |
| Excluded: duplicate complete normalized token sequence | 3 |
| Excluded: overlapping saved spans after duplicate removal | 0 |
| Retained across all 14 connected groups | 104 |
| Retained in the 13 groups meeting the fixed pair minimum | 98 |

All qualifying old exact-match coordinates were checked against unchanged saved
FL text, document hashes and article URLs. Alternative views are retained as
bindings of the same unit; they are not independent samples. Whitespace-only and
ordered-word-only matches were not repaired or admitted. There were no shared
normalized eight-token windows across the original connected groups, so the
registered conservative duplicate screen added no group merges. This does not
exclude shorter overlaps, approximate duplicates or undeclared connections.

A union of **4,147 word forms** from all supplied annotation English fields was
used only as a literal exclusion dictionary. Equal forms and numeric-adjacent
fragments are blocked. Punctuation, numeric material, masked tokens and unit
boundaries break adjacency; removing words never creates a new neighbor pair.
Raw Unicode offsets remain bound to the saved text via the canonical unit span.

## Fixed capacity result

| Connected group | Retained units | Unmasked adjacent pairs | Eligible |
|---|---:|---:|---|
| Accidental Altruist / interstellar intersubjectivity | 8 | 158 | Yes |
| Capra foreword / Weber holomovement | 6 | 138 | Yes |
| Christisis | 6 | 85 | No |
| Dark Side of Light | 5 | 123 | Yes |
| Deep physics / fake news / models of magic | 14 | 271 | Yes |
| Exalted deeds / vile darkness | 11 | 144 | Yes |
| Gad the Seer | 7 | 149 | Yes |
| Golden Age / secret symbols | 5 | 151 | Yes |
| Liber Azazel | 6 | 122 | Yes |
| Manichaean hymn / Roman texts | 6 | 139 | Yes |
| Nichiren images | 7 | 146 | Yes |
| Religious architecture | 12 | 150 | Yes |
| Risk mathematics / war accountability | 4 | 110 | Yes |
| Western esoterism | 7 | 117 | Yes |

Each eligible group has at least two retained units and 100 usable pairs. Every
prospective leave-one-group-out fold has **1,647–1,808 training pairs**, above the
fixed 500-pair floor. All thirteen qualifying groups are retained; Christisis's
85 pairs remain in the ledger, excluded from the prospective model panel by the
unchanged rule. Across all fourteen groups there are 2,290 unmasked tokens and
2,003 pairs. Capacity minima are pragmatic pilot limits, not a power calculation.

## What this corpus can and cannot answer

This is a small collection of historical/indexed excerpts selected by prior work,
not a representative full-post corpus. Language labels and source connections
come from supplied annotations and historical bookkeeping. An exact saved-text
match supports the representation used here, not the authenticity of a language
or its claimed source. The mask may remove genuine shared forms and leave copied
words, names or quotations missing from the English fields. It is not a certified
opaque-only segmentation, and its vocabulary was defined using the full exposed
annotation collection before any future fold training.

A future effect would therefore concern **masked declared-Kamri excerpts** under
these exclusions. Templates, register, editorial selection and generator rules
could create sequential predictability. Even a positive word-order result would
not distinguish those explanations from grammar or establish opaque meanings.
The 13 capacity-eligible groups are not 13 independently validated source works.
The separate natural semantic benchmark remains **0/4 qualifying works**.

## Next bounded experiment, not launched here

The capacity result supports a separate prospective protocol comparing a fixed
unigram model, a fixed preceding-word context model and the same context model
trained on order-destroyed text. Freeze vocabulary and unknown-token handling
from training groups only, smoothing, control draws, segment boundaries and the
primary group-level comparison before scoring. Preserve each group's loss,
unknown-token burden and control outcomes, rather than pooling all pairs as
independent evidence or selecting the best group/model. Evaluate actual text in
each reserved group; keep test answers out of fitting and tuning.

That model experiment needs its own registration and fixed stopping rule. E76
stops at this feasibility result. No vocabulary-overlap statistics, likelihoods,
model rankings, model API calls, new acquisitions or reviewer contacts were made.
The earlier reviewer gate remains relevant to independent semantic acceptance;
it does not prevent this separately scoped observable-text diagnostic.

## Verification and preservation

An independent implementation reconstructs all 1,026 unit dispositions, exact
bindings, Unicode tokens, masks, adjacency flags, duplicate decisions, connected
groups and prospective folds. It uses character-run partitioning and graph
traversal rather than the primary scanner and union-find. The entire computed
report agrees. All 21 historical input files match the preceding local evidence
checkpoint, and all 25 E75 sealed artifacts remain unchanged.

Six new fixture tests cover Unicode offsets/numeric fragments, hard barriers,
transitive duplication connections, short duplicate sequences, overlapping views
and the training-capacity floor. **559 full-workspace tests and 520 isolated-public
tests pass**, with the same 39 archive-dependent exclusions. No sealed historical
file was edited. Generated ledgers and the mask stay in the local evidence branch;
public main contains code, protocol and small reports.

Read-only reconstruction (requires the local evidence archive):

```sh
.venv/bin/python scripts/verify_order_corpus_v76.py
```

Preparation and execution are single-use; do not rerun them into sealed paths.
