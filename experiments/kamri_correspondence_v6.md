# Experiment 6 registration: Misinfons correspondence audit

Registered 2026-09-30 before new passage scoring. This is a diagnostic experiment with the unchanged v5 scorer, not a new lexical model. Previously inspected source identities and prose inform the single-analyst span labels; these are not blind annotations or semantic gold.

## Fixed scope

Retain the seven-statement opening Misinfons development query and its nine existing reference edges unchanged. Select two further blocks from the same indexed FL article, `Misinfons and the hypermemetic logic` (2019-09-27):

1. `continuation`: the two Kamri statements immediately following the opening morphic-fields statement and ending before the embedded English quotation about memes and misinfons. The second statement ends with a colon; retain it as a complete selected prose block and explicitly mark the quotation boundary. These correspond provisionally to Models of Magic source atoms 64–65.
2. `mechanism`: the next Kamri block, beginning with the application of the information model and containing five statements, ending at the colon before the embedded English quotation about cultural information. These correspond provisionally to source atoms 66–70. Preserve cybermagic, kundalini, etc. as literal strings when present; do not infer translations from them.

No adjacent English quotations enter the scoring queries. Keep the two blocks separate: removing an embedded quotation must not manufacture a continuous FL passage. Each selected block is capped at 180 whitespace words, with no dropping, replacement, or extension based on model outcomes. Missing acquisition or reference coverage stays in the selected denominator of two. This selection deliberately includes one two-atom query that cannot meet the inherited three-linked-atom admission requirement; report this structural constraint separately from retrieval and link recovery.

Use the previously saved Models of Magic source document and exactly the ten v5 candidate packets. The English source edition and old opening offsets do not change. Import the inspected search-index excerpt with an explicit receipt, preserving selected text and quotation-boundary locators; a failed raw page/captcha redirect is retained as an acquisition limitation, not bypassed. Indexed content is not a raw/current page snapshot. Additional sources mentioned in the article are outside this experiment's scope.

All three packets belong to one FL article and one English source work. The two added blocks are prospective within-article checks, not independently held-out works or register-transfer evidence. Capra and all earlier available data are development material. The unavailable Altruist source remains unavailable; this audit does not repair or replace that selection.

## Frozen comparison

Compare `baseline` and `gated_aliases`, calling the unchanged v5 prediction functions and v4 token-mass aligner/ordered decoder. Omit the universal variant because this experiment concerns the query-only gate; do not infer a gating benefit from that omission. The three proposed aliases, gate, frozen v1 lexicon, feature weights, floor, penalties, protected abbreviations, and decoder are unchanged. Import each variant's already frozen v5 threshold; do not recalibrate on these blocks. Never induce words from new labels or token paths.

Freeze all normalized inputs, source-group identities, atom/span references, block scopes, source edition, acquisition receipts, configuration, and diagnostic annotations before the final scoring execution. Retain the prior seven-statement reference exactly; any possible semantic/editorial ambiguity is recorded separately rather than silently relabeled.

## Audits and measures

- For each reference FL atom, save its complete corresponding English span, token counts, punctuation sequences, literal ASCII/numeric differences, and the existing alias presence/equal-length positional audit. Distinguish visible orthographic differences from inferred semantic additions or omissions. No unknown token is glossed.
- For each alias within each reference atom, record occurrence counts and all compatible English word spans. If the FL count exceeds English capacity, a complete one-to-one realization of that alias in that reviewed span is impossible under the proposed identity. This is conditional on the structural label and editorial fidelity, not independent disproof or validation of a meaning. Do not resolve repeated words by choosing convenient positions.
- After the scoring output is obtained, separately diagnose each canonical reference block and its adjacent two-FL-unit unions. Show length, punctuation, repetition and literal-anchor components; lexical multiset overlap and unmatched predictions with their origins; blended score; mass-normalized reward; and whether the block is actually enumerated by the inherited up-to-2:2 protected-unit proposal mechanism. Reference-guided diagnostics cannot affect retrieval or decoding.
- Save ranked candidates, conditional and retrieved edge precision/recall, admissions, margins, gate/coverage, and one-to-one provisional token paths. Token matches labeled frozen anchors or experimental aliases remain model-derived evidence, never semantic truth.
- Source-absent controls remove the entire corresponding source work. Use 20 shared nonidentity atom permutations per available packet, seed 6831. Repetitions are allowed; report unique orders as well as the full denominator, especially for the two-atom block. Recompute shuffled windows. Exceedances are descriptive, not p-values.
- One final execution after implementation checks and input freeze. No post-result tuning or rerunning to improve an outcome. Preserve experiments 1–5, record input/raw/code/output hashes, and verify their historical manifests.

## Decision limits

Zero new supported lexical entries. No fluent translation, recovered grammar, or independently validated token meanings. State whether failures are consistent with boundary changes, token-count differences, lexical coverage/conflicts, or the fixed scoring floor, without asserting a causal diagnosis from this observational audit alone. A future scoring change needs its own registration and independent evaluation material; this audit only supplies development evidence.
