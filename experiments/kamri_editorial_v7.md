# Experiment 7 registration: controlled editorial robustness

Registered 2026-09-30 before generating or scoring the evaluation corpus. Engineering evaluation with generated identity truth; no independent natural-language semantic validation.

## Panels and fixed perturbations

Calibration worlds: seeds 7401–7402. Fresh worlds: seeds 7501–7508. Implementation fixtures use seed 97001, never calibration/evaluation seeds. Every world receives all sixteen combinations of four binary edits. Calibration denominator is 32 conditions from two worlds; fresh denominator is 128 conditions from eight worlds. Conditions sharing a world are paired observations, not independent samples. No replacement, culling, outcome-dependent retry, parameter search, or winning-variant selection.

Each world contains six generated statements with lengths drawn from 8, 10, 12 tokens. Two function words per statement (`the`, `and`) use the corresponding eligible v1 forms (`şu`, `aš`); other words use unknown artificial forms absent from the lexicon. Repeated content vocabulary is seeded. Token identities distinguish repeated occurrences. Correct-source candidate position is randomized once per world and reused across its conditions.

Each query has four candidates: the corresponding packet and three within-statement rotations of base source tokens by one, two, or three positions. Inserted editorial material and punctuation positions remain identical across the four candidates. Rotations preserve per-statement word counts and bags of words, providing close order distractors; this deliberately adversarial candidate collection is not a corpus sample. Fail preparation on accidental exact candidate duplicates rather than replacing a case.

Perturbation bits, applied in this fixed order:

1. Punctuation: add a comma after the second FL token and a semicolon after the sixth in every statement. Source punctuation is unchanged. Identities and boundaries are unchanged.
2. Parenthetical insertion: insert four source-only artificial words in parentheses after the fourth base token of every statement. They have no FL identities.
3. Repeated-word insertion: insert two extra occurrences of an existing source content word after the sixth base token in every statement. They have no FL identities; repetition and lengths change.
4. Lexical conflict: replace the first FL form (whose generated identity means `the`) by eligible form `aš` in every statement. The frozen predictor therefore proposes `and` for those identities. This constructs local prediction conflicts without changing gold identities or English text. It is injected polysemy/noise, not evidence about actual FL semantics.

Preserve all sixteen conditions, including pristine and combined edits. Freeze original texts, opaque document/candidate IDs, acquisition-kind synthetic receipts, per-token identities and Unicode spans, reference edges, split/seed/condition labels, and code/configuration hashes. The scorer receives text, frozen eligible predictions, and global parameters only; never identities, answer IDs, references, or perturbation labels. No induced dictionary or register expansion.

Real development: all ten available v5 queries plus the two additional Misinfons blocks from v6, unchanged documents and labels. All eight variants use the existing v5 query-only gated alias predictions. The unavailable Altruist source remains outside scoring and preserved in historical manifests; it is not replaced. No fresh real work is selected in this experiment.

## Eight matched variants

Cross these three binary scoring factors, naming variants `p0_r0_l0` through `p1_r1_l1`:

- **P:** original punctuation SequenceMatcher ratio / fixed neutral punctuation component 0.5. Weights stay unchanged. Neutralization removes both punctuation agreement bonuses and mismatch penalties; it does not simply boost edited cases.
- **R:** original absolute-index repetition-pair Jaccard / relative-position repetition-pair multiset Jaccard. For a block of n tokens, map each repeated-word pair (i,j) to `(floor(8*i/n), floor(8*j/n))`. Preserve multiplicity. Similarity is sum of pair-bin minima divided by sum of maxima; empty/empty remains 0.5. Eight bins are fixed before generation. This preserves coarse order information while testing tolerance to length shifts; it is not an order-free frequency histogram.
- **L:** original lexical overlap fraction / neutral unmatched lexical predictions. With m eligible emitted predictions and k multiset matches, original k/m changes to `0.5 + 0.5*k/m` when m>0. With no predictions, both remain 0.5. Perfect agreement remains 1. Absence gets neutral credit, which may admit distractors. Predictions and the ordered decoder are unchanged, so this cannot directly fix token paths that reject known mismatches.

`p0_r0_l0` must exactly reproduce the inherited scorer and alignments. Structural feature weights 0.55/0.20/0.20/0.05, length ratio, literal anchors, 0.60/0.40 blend, floor 0.72, token-mass reward/reference mass 20, merge penalty 0.04, token-scaled gaps 0.35, up-to-2:2 protected blocks, decoder, and three-linked-atom admission requirement stay unchanged. Severe additions and gaps are intentionally not repaired in this experiment.

## Calibration, measures, and controls

Calibrate a separate synthetic threshold per variant as the maximum wrong-candidate strength over all 32 calibration conditions plus 1e-6. Real thresholds use maximum wrong-work strength over the ten available v5 development queries plus 1e-6; the two extra Misinfons blocks never set thresholds. All editions of a real work are removed in source-absent controls. Synthetic source-absent controls remove the corresponding candidate. Admission also requires margin >1e-9 and at least three distinct linked FL atoms. Fresh outcomes do not set any threshold or select a variant.

Primary fresh measures for all eight variants: unique correct top-1/128, correct and wrong admissions/128, source-absent false admissions/128, retrieved and conditional edge precision/recall, and generated token-identity precision/recall. Include unadmitted retrievals in edge/token measures. Report proposed/correct/reference counts and all sixteen eight-world condition slices. Do not describe nominal top-1 under a tie as successful retrieval.

Within each world, compare each edited condition to its pristine condition. Save differences in unique retrieval, admission, conditional correct edges, and conditional correct tokens. Save paired scoring-factor effects over the complete eight-variant cube, with each contrast changing exactly one factor. Counts/contrasts are descriptive; no p-values, confidence intervals, or claims of 128 independent samples.

Save ten shared nonidentity FL atom permutations per fresh synthetic condition and per real query, seed 7831. Calibration has zero shuffles. Repetitions are allowed; identities forbidden; recompute adjacent windows and report unique-order counts. Exceedances use the observed maximum across candidates and are descriptive. Each variant uses the same orders for a query.

Save full rankings, scores, blocks, token paths/origins, predictions/gates, thresholds, margins, source-absent decisions, identity metrics, comparisons, run status, and input/raw/code/output hashes. After implementation tests and input validation, perform one final model execution. Preserve every result and experiments 1–6. Any later scoring change requires another experiment.

## Interpretation limits

Constructed substitution/perturbation truth is not natural-language translation accuracy. Synthetic candidate rotations, eight independent worlds, a narrow edit family, correlated conditions, and real development calibration limit inference. Changing scoring can help recall while weakening order discrimination or increasing false admissions; report both. All newly inspected material becomes development for subsequent choices. No new supported lexical entries or independent alternate-register transfer claim.
