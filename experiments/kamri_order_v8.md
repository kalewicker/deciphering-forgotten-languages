# Experiment 8 registration: source discrimination and admission

Registered 2026-09-30 before generating/scoring new panels. Engineering stress test with constructed occurrence identity truth; no natural semantic validation.

## Fixed panels

Reuse the v7 generator unchanged with calibration seeds 8401–8432 and fresh seeds 8501–8532. Each independently seeded world receives masks **0, 1, 2, 4, 8, 15**: pristine, punctuation only, parenthetical insertion only, repeated-word insertion only, lexical conflict only, and all four edits. Each panel contains 192 paired conditions from 32 independent worlds. This is a six-condition stress panel, not a repetition of the sixteen-condition factorial. Seeds 98001 are implementation fixtures only. No case replacement, culling, tuning, or outcome-dependent retry.

Candidate pools and occurrence references are generated exactly as in v7: six statements, corresponding source plus three within-statement rotations, randomized candidate position constant within world, inserted source tokens without FL identities, and deliberately conflicting eligible function forms retaining their generated identities. Save all generated text, identity/span references, seeds/masks, normalized documents and synthetic receipts before scoring. Models never receive identities, answer IDs, references, or edit labels.

All twelve real queries from v7 remain development diagnostics. Ten available v5 queries set real thresholds; the two additional Misinfons blocks do not. Carry forward the eight v7 fresh pristine synthetic packets as **old development diagnostics**, never calibration or fresh evaluation. The Altruist source remains unavailable in its existing archive. No independent fresh real work is selected.

## Four fixed variants

Cross two v7 backgrounds (`p0_r0_l0`, original; `p1_r1_l1`, full tolerant combination) with candidate token-order multiplier off/on. Backgrounds were selected as the two endpoints of the previous factorial, not as winning models. Preserve all four outcomes. All predictions use the unchanged frozen v1 eligibility and existing query-only v5 aliases. No new dictionary entries or gate changes.

First compute the unchanged background local alignment and its selected blocks. Compute a separate order-quality term for every candidate **before sorting candidate scores**, using only query/source tokens, frozen predictions, selected blocks and fixed parameters. It does not reopen the block search or change token decoding.

For each selected block, calculate the full global token-DP objective using the inherited decoder diagonal and gap scores: exact eligible prediction +2, known mismatch −2, unknown diagonal 0.5 minus absolute normalized token-center displacement, token gap −0.75. Retain the full objective including negative diagonals/gaps rather than summing only the decoder's retained nonnegative pairs. Sum these block objectives, then charge −0.75 for each query token outside selected blocks. Unselected source prose outside local blocks is not charged.

Let U be the sum over every query token of 2 if it has an emitted prediction and 0.5 otherwise. Define quality = clip((summed objectives − uncovered query tokens × 0.75)/U, 0, 1). If U=0, quality=0. Candidate strength with order on is **background strength × quality**; order off preserves background strength exactly. Save U, block objectives, covered/uncovered token counts, raw/clipped quality, base strength and multiplied strength. No blending coefficient or parameter search. The term can only reduce strength and cannot recover an alignment the base search missed. Unknown-token agreement remains positional and does not establish word meaning; anchor-poor same-length text may be indistinguishable.

Length/feature weights, floor 0.72, reward reference mass 20, merge/gap penalties, protected up-to-2:2 blocks, ordered decoder, aliases and three-linked-atom admission rule remain fixed. This tests candidate ranking/rejection, not repair of severe editorial changes or lexical conflicts.

## Calibration and evaluation

Calibrate separate synthetic thresholds for each of four variants: maximum wrong-candidate strength across all 192 calibration conditions plus 1e-6. Real thresholds use maximum wrong-work strength across the ten real calibration/development queries plus 1e-6. Persist/seal both tables before scoring fresh conditions, old pristine diagnostics, or the two extra real blocks. No fresh result sets thresholds or chooses a winner.

Admission additionally requires margin >1e-9 and at least three distinct FL atoms with decoded links. Source-absent controls remove the corresponding synthetic candidate or all editions of the real source work. Evaluate every selected condition, including zero-strength ties and refusals.

Primary fresh measures: unique correct top-1/192, correct and wrong admissions/192, source-absent false admissions/192, and retrieved/conditional edge and generated token-identity precision/recall with unadmitted retrievals included. Report all six 32-world condition strata, especially pristine false admissions **out of 32**, and per-world counts. Conditions sharing a world are paired, not independent samples.

For order-off variants only, compute a saved counterfactual applying that background's previously sealed v7 synthetic threshold to the **same fresh v8 paths/rankings**. Compare admissions/absent errors under old versus enlarged-panel thresholds; no additional scoring run. This isolates threshold choice on those paths, not the sole causal effect of sample size: v8 changes calibration world count and condition scope. Old score-scale thresholds do not apply to multiplied scores, so order-on counterfactuals are unavailable, never zero.

Save paired order-on versus order-off differences per world/condition/background: unique retrieval, correct admission, absent false admission, retrieved correct edges/tokens, and correct-source quality/strength. Retain threshold changes in interpreting admission effects. Old pristine controls can show development behavior under enlarged thresholds; never label them fresh confirmations.

Use ten shared nonidentity FL atom permutations per fresh condition and real/old-development query, seed 8831; calibration has no permutations. Recompute base windows and order multiplier for every shuffled candidate. Both order levels and backgrounds use identical orders for a query. Repetitions allowed, identity forbidden, actual unique-order counts saved. Exceedances are descriptive, not p-values.

Save full rankings, base paths, decoded token origins, quality decomposition, predictions/gates, thresholds, counterfactuals, controls, comparisons, counts, inputs/raw/code/output hashes, and durable run state. After implementation tests and freeze, one final model execution. Keep failed/diagnostic results and experiments 1–7 unchanged. No winner promotion or semantic claims based on outcomes.

## Limits and decision

Thirty-two seeded worlds still cover one engineered generator and three rotation distractors. Paired conditions and shared templates limit effective independence. This does not validate rejection against arbitrary English sources or natural alternate registers. More conservative rejection may discard true partial passages, especially under lexical conflicts; report recall/admission costs alongside false admissions. A zero observed error count is not proof of a generally safe threshold. No new supported lexical entries; independent natural validation still requires another auditable work.
