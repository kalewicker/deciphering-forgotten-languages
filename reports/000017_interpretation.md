# Experiment 17: positional cross-unit consistency

All 212 frozen position hypotheses across eight units and two previously exposed components are retained. No new retrieval, lexicon input, morphology aliases, lexical induction or model execution.

There are 107 FL form types; 36 appear in at least two distinct units. Of those, 34 have one English token outcome and 2 have conflicting outcomes. 1 types repeat only within one unit and receive no cross-unit-support credit.

Primary form-macro cross-unit agreement: 0.974537. Null mean: 0.025998; null maximum: 0.108515. The one-sided Monte Carlo diagnostic p is 0.001000 (0 of 999 controls meet or exceed the observed statistic; 0 exact ties). Registered criterion p <= 0.01: met. This is conditional ordering-specific development evidence, not semantic or held-out success.

| Scope | Eligible FL forms | Distinct unit-pairs across forms | Macro agreement | Matching occurrence pairs / all pairs |
|---|---:|---:|---:|---|
| global | 36 | 118 | 0.9745370370370371 | 406 / 420 |
| within_component | 35 | 74 | 0.9904761904761905 | 206 / 214 |
| between_components | 11 | 44 | 0.8939393939393939 | 200 / 206 |

| Fixed control | Primary agreement | Strict global repeated types | Cross-component review leads |
|---|---:|---:|---:|
| rotate_+1 | 0.278223 | 8 | 0 |
| rotate_+2 | 0.227227 | 7 | 0 |
| rotate_-1 | 0.315768 | 9 | 0 |
| rotate_-2 | 0.155334 | 4 | 0 |
| reverse | 0.044489 | 1 | 0 |
| length_matched_swap | 0.456878 | 10 | 0 |

3 FL forms satisfy the strict cross-component review-lead rule: one English outcome, both components, at least two distinct units in each. Their full occurrence evidence and every conflicting form are preserved. No per-form significance or independently validated meanings are assigned.

The primary metric averages English outcome-frequency agreement across distinct unit pairs, then equally across eligible FL forms. Repeated positions within one sentence never create a second independent unit. Exact rational comparisons preserve ties. All 999 shuffled orders, complete statistics and six fixed controls are saved. Identity draws are retained, and the length-matched swap exchanges only the preregistered 26-token pair.

Semantic training eligibility remains zero and no untouched test fold is created, regardless of the diagnostic criterion. The raw-FL provenance limitation from v16 persists. Next work must test these hypotheses on a separately registered extension or independently reviewed word-order/meaning evidence; reuse of this panel remains development.

Interpretation and preserved conflicts

This experiment meets its registered ordering-specific development criterion. It provides evidence that the fixed token positions preserve repeated-form correspondences much better than independently shuffling the English positions within the same eight statements. It does not measure translation accuracy, establish individual word meanings or supply an independent population test. The 0.974537 value is form-macro agreement under the stated frequency-weighted unit-pair rule, not 97.45% lexical accuracy.

All 107 FL form types remain in the form registry. Thirty-six have cross-unit support; the other 71 occur within only one selected sentence, including one type that repeats inside that sentence. Those types contribute no invented independent support. Across the 36 eligible types there are 118 distinct unit comparisons, corresponding to 420 occurrence pairs. The unweighted form-macro and occurrence-weighted summaries are deliberately separate, so frequent function words do not dominate the primary result.

The two conflicting repeated forms are retained exactly:

| FL form | Positional English outcomes | Distinct units | Interpretation |
|---|---|---:|---|
| ċu | are: 2, on: 1 | 3 | One context-free English label does not fit all observed positions. |
| ńi | into: 2, of: 8 | 4 | One context-free English label does not fit all observed positions. |

These conflicts are compatible with several explanations, including context-dependent grammatical functions, polysemy or local ordering differences. The diagnostic does not choose among them, rewrite labels or remove the forms. No lemmatization, English synonym merging, morphology alias or post-result repair was introduced.

Only three forms meet the stricter cross-component review-lead rule:

| FL form | Consistently paired English token | Occurrences | Nichiren units | Dark Side units |
|---|---|---:|---:|---:|
| şed | one | 4 | 2 | 2 |
| şo | to | 10 | 3 | 3 |
| şu | the | 24 | 4 | 3 |

The English column describes a pairing in this frozen panel, not a promoted translation. All three are function-word candidates and all arise from two already exposed source components. Their recurrence supports review priority, not an independent semantic claim. There are no per-form p-values or separate scientific admissions.

All six fixed controls have lower primary agreement. The 26-token source swap changes two of eight units, leaving six units intact; its residual 0.456878 agreement is therefore not a source-absent rejection rate. The shifted controls likewise preserve repeated English collocations and can retain some consistency. The full control form ledgers preserve those patterns and conflicts. No secondary control was selected as the reference distribution after seeing the outcome.

The primary randomization uses all 999 registered permutations, including any identity draws, and one unchanged RNG stream. None met or exceeded the observed score, and there were no exact ties. The corrected one-sided diagnostic p is 1/1000, the finite-resolution minimum for this registered horizon; it is not zero and does not imply an arbitrarily small population probability. The exposed, audit-informed selection is an explicit limitation of inference.

127 tests passed. The independent verifier computes agreement by enumerating actual English-outcome comparisons between occurrences in different sentences, rather than reusing the runner's count-product implementation. It replays every shuffle order and six fixed controls, verifies all occurrence identities and source offsets, checks strict/conflicting/support ledgers, recomputes exact rational tail counts and confirms all sixteen historical archives. Semantic-training eligibility and untouched-test eligibility remain zero.

The next useful experiment is a separately preregistered passage extension: freeze the current candidates before reviewing additional sentences, retain every selected extension unit and mismatch, and test transfer as development evidence. Preserve the two conflicted forms as unresolved. Independent word-order/meaning evidence and legitimate raw FL provenance remain necessary for stronger claims; a fresh held-out result requires separately nominated unexposed source components.

Artifacts: [registration](../experiments/kamri_consistency_v17.md), [immutable manifest](../runs/000017_kamri_positional_consistency/manifest.json), [all 212 occurrences](../runs/000017_kamri_positional_consistency/occurrence_ledger.json), [all forms and conflicts](../runs/000017_kamri_positional_consistency/form_ledger.json), [fixed controls](../runs/000017_kamri_positional_consistency/fixed_controls.json), [all 999 permutations](../runs/000017_kamri_positional_consistency/permutations.json), [review leads](../runs/000017_kamri_positional_consistency/review_leads.json), and [independent verification](000017_verification.json).

Reproduce verification with `.venv/bin/python scripts/verify_consistency_v17.py` and run the test suite with `.venv/bin/python -m unittest discover -s tests -q`. The runner deliberately refuses to overwrite the completed run.
