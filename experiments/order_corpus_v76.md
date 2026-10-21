# E76: corpus feasibility for a monolingual word-order pivot

This is one offline feasibility step, not a predictor run. The user authorized
the pivot on 2026-10-21. Freeze this protocol, input hashes and implementation
before computing the capacity ledger. Earlier examples and schemas were inspected
for design; no claim of blind corpus selection is made.

Question: do the saved v15 excerpts support at least four conservatively separated
groups for a later, separately registered, word-context development diagnostic?
The observable target in that future diagnostic would be the next stored token,
not an English correspondence. E30's source-localization route and synthetic
feature expansion remain closed. No new acquisition or model review occurs.

## Fixed inventory and representation

Use every unit in `data/v15/parsed_annotations.json`, preserving the full unit
denominator, the v15 unit ledger and benchmark document registry. Bind the v36
connected-group ledger; its declared connections are conservative grouping
constraints, not independently established source identities. Include only units
whose unit AND article language are exactly `Kamri` and that have at least one
old scope-accepted **exact** FL match. Recheck all qualifying match coordinates
against the saved document text and its internal text hash, expected article URL,
kind and registered document path. Whitespace/ordered-word-only matches are
excluded without repair. Retain every eligible exact binding, choosing the
lexicographically first (document ID, start, end) as its canonical coordinate.

Tokenize maximal Unicode letter/mark runs beginning with a letter; normalize
each token with NFC then casefold. Retain raw Unicode code-point offsets. Digits,
punctuation and all other non-whitespace material are hard barriers between
tokens. No cross-unit adjacency, concatenation across a mask, spelling repair,
stemming or learned segmentation. Tokens adjoining digits are conservatively
blocked, so an alphanumeric identifier cannot become a word fragment.

Freeze a conservative literal mask from the union of normalized word forms in
**all** annotation English fields, irrespective of claimed language or inclusion.
Mask any equal FL token as a hard barrier. These supplied English fields are used
only as an exclusion dictionary, never as translations/labels. This intentionally
overmasks shared forms and cannot guarantee removal of all copied English, Latin,
names or quotations. The resulting view is called masked declared-Kamri excerpts,
not verified purely opaque text. Later results would be conditional on this mask.

## Dependence and capacity

Start with all v36 connected groups. Merge groups if any corroborated candidate
units share an eight-token normalized sequence before masking, even across
punctuation; this conservative leakage screen does not certify absence of shorter
or approximate duplication. Preserve the witnesses and transitive connections.
Deduplicate identical complete normalized token sequences, keeping the lowest UID.
In UID order, exclude a unit if any exact binding overlaps any binding of an
already retained unit in the same saved document. Keep exclusions in the ledger;
do not substitute a weaker match or different capture to rescue them.

For each final connected group, count retained units, unmasked tokens and adjacent
unmasked token pairs separated only by whitespace. Pairs never cross unit,
punctuation, numeric or mask barriers. A group is capacity-eligible at >=100 pairs
from >=2 retained units. Use ALL eligible groups for a prospective leave-one-group-
out diagnostic; each fold must have >=500 training pairs from the other eligible
groups. Capacity passes only with >=4 eligible groups and all folds meeting that
training floor. These are pragmatic small-pilot resource minima, not power
calculations, significance thresholds or the four-work semantic benchmark.

Save the full unit ledger, source bindings, token/barrier records, mask, duplicate
witnesses, group counts and every prospective fold. Zero/undersized groups remain
visible. Do not compute vocabulary overlap, likelihood, predictor rankings or
context effects in E76. No group selection or threshold adjustment after counts.

## Stop and interpretation

Stop after one capacity ledger and verification, whether it passes or fails.
A pass permits proposing a separate fixed unigram/context/shuffled-training
comparison; it does not launch it. A failure closes this exact saved-corpus
design without relaxing thresholds, broadening to uncorroborated annotations or
automatically acquiring more texts. Review a materially different resource or
question before another run. Do not create a sequence of repairs solely to make
this gate pass.

All material is exposed development evidence. Indexed excerpts, supplied language
labels, source group claims and incomplete literal masks are explicit limitations.
No grammar, meaning, language authenticity, independent review, immediate source
identity or untouched test unit is admitted. The natural semantic benchmark
remains 0/4 qualifying works. Verify raw bindings, masking/barriers, duplicate
accounting, complete denominators, group/fold arithmetic and frozen hashes. Use
new versioned code and fixture tests; preserve all historical files and evidence.
