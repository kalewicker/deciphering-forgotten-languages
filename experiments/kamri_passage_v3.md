# Experiment 3 registration: boundaries, passage blocks, and lexical anchors

Registered 2026-09-30 before scoring any newly selected inputs.

Purpose: exploratory engineering comparison of sentence-boundary handling, many-to-many passage alignment, and frozen lexical anchors. No semantic translation accuracy or blind source discovery is claimed.

## Inputs and fixed selection

- Development: all seven works from experiments 1–2. Use Johnson Chapter 13 for Gad; the original edition remains archived.
- Fresh selected denominator: two new source works, risk_math (the opening Kamri block of War Algorithmics, 2019-05-15; Gonçalves, arXiv:1211.6683) and models_magic (the opening Kamri block of Misinfons and the Hypermemetic Logic, 2019-09; Frater U.D., Models of Magic).
- These inputs were nominated by the existing public Kamri source report. Register selection before checking alignment performance. Do not replace missing or unusable inputs; report acquisition/audit failures against the fixed denominator of two.
- FL selection: complete opening Kamri sentences up to 180 whitespace words, ending at the first embedded English paragraph or at the available indexed-excerpt limit. No normalization of the alternate Misinfons register into standard Kamri.
- English scope: raw Models of Magic HTML article body, and Gonçalves PDF pages 1–3 including introduction and opening theory discussion. Previously saved English inputs retain their scopes. Scope differences are disclosed.
- Retain raw receipts, declared normalized transformations, Unicode offsets, frozen hashes, and analyst correspondence spans before evaluation. Single-analyst source audit remains structural and provisional.

## Fixed factorial comparison

Eight variants cross these three factors; no tuning or variant selection after fresh outcomes:

1. Sentence boundaries: original parser, or protected abbreviations (i.e., e.g., Mr., Mrs., Ms., Dr., Prof., vs., etc.). The protected parser merges adjacent original atomic sentences when the intervening period belongs to a registered abbreviation. Offsets and original atomic sentence identities are preserved. No source-specific substitutions.
2. Blocks: 1:1 effective units, or up to 2:2 adjacent effective units, with explicit gaps. Block text covers the exact contiguous saved-text span. Every inferred atomic edge in the block Cartesian product is counted; extra edges are errors rather than automatically credited.
3. Score: structural only, or the frozen 0.60 structural + 0.40 lexical multiset agreement from experiment 2. Use the exact v1 lexicon and original eligibility rules. Missing lexical predictions contribute neutral 0.50. Do not train a new lexicon or patch unknown register forms.

For all eight variants: match floor 0.72; gap cost 0.35 per skipped effective unit; merge penalty 0.04 per additional effective unit beyond 1:1; block reward = (similarity - 0.72) × mean number of FL/source effective units minus merge penalty. Permit a block only when reward is positive. Normalize best local path strength by the number of FL effective units. Deterministic first-maximum tie handling. Require at least three distinct original FL atomic sentences linked to admit a source.

Each factor comparison holds the other two fixed. Comparisons across boundary settings still change unit denominators; calibrate each variant separately and report this limitation.

## Evaluation and controls

- Rank a fixed nine-work candidate collection. All available selected source documents may be candidates even if that FL query is missing. Withhold answer/source identity and reference annotations from scoring.
- Variant-specific admission threshold = maximum wrong-work strength on the seven development queries + 1e-6. Fresh queries never set thresholds. Source-absent controls remove every edition of the correct work.
- Primary: fresh top-1 / 2 selected; fresh correct admissions / 2; retrieved atomic-edge precision/recall against audited span correspondences; fresh source-absent false admissions / 2. Report available and missing counts. Do not treat an unavailable reference as zero reference edges or claim aggregate selected-sample recall when reference coverage is incomplete.
- Secondary: development recovery of the boundary/merge cases observed in experiment 2, and all pairwise factorial differences. Report end-to-end retrieved alignment separately from alignment conditional on the correct source.
- Controls: 20 shared FL atomic-sentence permutations per query, RNG seed 2731. Reorder atomic units; retain each variant's precomputed protected FL groups as indivisible groups only if their members remain consecutive in original order in the permutation. Recompute adjacent block scores after permutation, never shuffle cached merged-score rows. Descriptive exceedance counts only; these are not calibrated p-values.
- Evidence includes blocks, spans, inferred edges, frozen predictions, rankings, source-absent decisions, exact permutations, thresholds, and input/code/output hashes. No automatic claim acceptance.
- Stop: one final execution after synthetic tests and input audit. Preserve failures. Any post-result changes require a new run and convert fresh groups into development material.

## Expected limitations

Tiny known-source sample; indexed FL text rather than current/raw full pages; uneven English source scopes; single-analyst structural references; common function-word anchors; local alignment may find partial passages; up to 2:2 spans cannot represent arbitrary rewriting; protected abbreviation heuristic may suppress genuine sentence ends; alternative Misinfons register may be largely unknown to the frozen lexicon.
