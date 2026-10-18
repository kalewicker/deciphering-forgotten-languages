# Experiment 8: candidate token order and admission calibration

Completed and independently verified on 2026-09-30. **Enlarged calibration substantially improves rejection on this panel; adding token-order quality has mixed effects.** It admits the development Misinfons opening under the tolerant background, but does not repair severe edits or support new meanings. No variant is promoted.

Evidence: [registration](../experiments/kamri_order_v8.md), [frozen benchmark](../benchmarks/kamri_order_v8.json), [run manifest](../runs/000008_kamri_order_admission/manifest.json), [machine report](../runs/000008_kamri_order_admission/report.json), [paired contrasts](../runs/000008_kamri_order_admission/comparisons.json), and [verification receipt](000008_verification.json).

## Design and denominators

The four variants cross the original v7 background (`p0_r0_l0`) and the fully tolerant background (`p1_r1_l1`) with a fixed token-order multiplier off/on. Both backgrounds were preregistered endpoints of the previous factorial. Predictions, eligibility, query-only aliases, base alignment, match floor, token decoder, and the minimum of three linked FL atoms are unchanged.

Calibration uses 32 independently seeded texts, seeds 8401–8432; fresh evaluation uses 32 others, seeds 8501–8532. Each text receives six paired conditions: pristine, punctuation only, English parenthetical insertion, repeated-word insertion, lexical conflict, and all four edits. Each panel therefore has **192 conditions, not 192 independent texts**. This uses the unchanged v7 generator: six statements and three within-statement rotation distractors. Candidate position is randomized within each world and held constant across its conditions. Constructed token identities provide engineering references, not semantic gold.

Ten previously inspected real queries calibrate separate real thresholds. The two additional Misinfons blocks are real development audits excluded from calibration. Eight previously fresh v7 pristine packets are now old development diagnostics. There are **zero fresh real source works and zero new supported lexical entries**. The unavailable Altruist source remains in its historical archive and denominator.

There was one final execution after tests and input freezing: 1,616 result rows across all panels and variants, completed in approximately 76 seconds. Calibration scores and thresholds were sealed before fresh and audit evaluation. No failed condition was removed, no fresh result adjusted a threshold, and no outcome-dependent rerun occurred.

## What the order score measures

For every candidate, the unchanged background first selects alignment blocks. A separate global token dynamic program scores each selected block: exact frozen-prediction agreement +2, known mismatch −2, unknown positional agreement up to +0.5, and gaps −0.75. Its full objective retains costs omitted from displayed token pairs. Each query token outside the selected blocks costs another −0.75. Unselected source prose outside the local blocks is uncharged.

The adjusted objective is divided by an upper bound over **all query tokens**, then clipped to [0, 1]. Order-on strength equals base strength times this quality, before candidate ranking. This cannot increase a candidate's strength, reopen the block search, or change its decoded links. It combines order agreement with coverage and gap penalties; this experiment does not isolate those components.

Thresholds are separately recalibrated on each variant's score scale. Consequently, a smaller multiplied score can still become admitted when its calibrated threshold falls further. Differences in admission measure the complete scoring/calibration pipeline, not an order effect with a constant threshold.

## Fresh results

All admissions and errors below have denominator 192. Unique retrieval requires an untied correct top score; metrics include refusals. A source-absent control removes the correct candidate and tests admission among the three remaining distractors.

| Background | Order | Unique correct | Correct admissions | Wrong admissions, source present | Source-absent false admissions | Worlds with an absent error / 32 |
|---|---|---:|---:|---:|---:|---:|
| Original | Off | 131 | 32 | 0 | 1 | 1 |
| Original | On | 128 | 64 | 0 | 0 | 0 |
| Tolerant | Off | 147 | 64 | 0 | 0 | 0 |
| Tolerant | On | 151 | 64 | 0 | 2 | 1 |

The original background gains 32 admissions with order on, all punctuation-only conditions, while losing three unique correct retrievals overall. The tolerant background gains four unique retrievals but no additional admissions, and gains two source-absent errors. **Order scoring does not uniformly improve discrimination.** Observed zero errors are limited to this generator and panel.

There are 1,152 reference edges and 11,772 reference token identities per variant. Retrieved-source precision and recall are:

| Background / order | Correct / proposed edges | Edge recall | Correct / proposed token identities | Token recall |
|---|---:|---:|---:|---:|
| Original / off | 750/800 | 65.1% | 7,168/7,963 | 60.9% |
| Original / on | 768/798 | 66.7% | 7,322/7,973 | 62.2% |
| Tolerant / off | 857/923 | 74.4% | 7,843/9,153 | 66.6% |
| Tolerant / on | 891/936 | 77.3% | 8,070/9,317 | 68.6% |

Conditional on the correct source, paths and metrics are exactly identical across order levels within each background, as independently verified. Thus the retrieved-source gains reflect ranking changes rather than improved decoding. Conditional correct edges are 769 for the original background and 891 for the tolerant one.

Each condition stratum contains 32 paired worlds. Entries below are **unique correct retrievals / correct admissions / source-absent false admissions**, each out of 32.

| Condition | Original off | Original on | Tolerant off | Tolerant on |
|---|---|---|---|---|
| Pristine | 32 / 32 / 1 | 32 / 32 / 0 | 32 / 32 / 0 | 32 / 32 / 1 |
| Punctuation only | 32 / 0 / 0 | 32 / 32 / 0 | 32 / 32 / 0 | 32 / 32 / 1 |
| Parenthetical insertion | 6 / 0 / 0 | 0 / 0 / 0 | 20 / 0 / 0 | 23 / 0 / 0 |
| Repeated-word insertion | 29 / 0 / 0 | 32 / 0 / 0 | 31 / 0 / 0 | 32 / 0 / 0 |
| Lexical conflict | 32 / 0 / 0 | 32 / 0 / 0 | 32 / 0 / 0 | 32 / 0 / 0 |
| All four edits | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

Every admitted fresh case is pristine or punctuation-only. All fully edited conditions fail retrieval and produce no links. Parenthetical insertion remains difficult: original/on loses all six original/off unique successes; tolerant/on improves retrieved correct edges from 95 to 123 out of 192, while still admitting none. Lexical-conflict cases retrieve correctly but discard 192 conflicted token identities, leaving 1,770/1,962 correct identities in every variant and no admissions.

The original/off absent error occurs in pristine seed 8516. Tolerant/on errors occur in seed 8504's pristine and punctuation-only conditions: **two paired errors from one world**, not two independent failures. Pristine error counts are explicitly 1/32, 0/32, 0/32, and 1/32 respectively.

## Enlarged calibration versus old thresholds

The saved counterfactual applies the old v7 thresholds to the **same fresh order-off paths and controls**, without rescoring. It isolates threshold choice on these paths. Calibration also changed condition scope as well as world count, so it cannot isolate the sole causal effect of adding worlds.

| Background, order off | Old synthetic threshold | Enlarged-panel threshold | Absent errors using old → new threshold / 192 | Correct admissions using old → new threshold / 192 |
|---|---:|---:|---:|---:|
| Original | 0.15644160 | 0.16675395 | **8 → 1** | 32 → 32 |
| Tolerant | 0.13002322 | 0.14092673 | **38 → 0** | 64 → 64 |

This is the clearest rejection improvement. The old tolerant threshold falsely admits 19 pristine and 19 punctuation-only controls from the same 19 worlds. The enlarged threshold removes those errors without losing correct admissions on this panel. Applying enlarged thresholds to the eight old pristine packets yields eight correct admissions and zero absent errors in every variant; those packets remain development data.

Order-on synthetic thresholds are 0.13292416 (original) and 0.11767232 (tolerant). Old-threshold counterfactuals are unavailable on this multiplied score scale and are saved as null, never as zero errors.

## Misinfons and real development behavior

The tolerant/order-on variant **admits the opening Misinfons passage**. Its unchanged path recovers 9/9 reviewed edges and proposes one extra edge. Quality is 0.65388717, reducing strength from 0.03336124 to 0.02181448. The corresponding real threshold falls from 0.06438033 without order to 0.01619728 with order; the multiplied score clears that threshold and has a positive margin. This is development admission supported by frozen function-form and positional agreement, not independently validated translation.

Across the ten real calibration/development queries, correct admissions are 9, 9, 9, and 10; source-absent errors are zero. Unique correct retrievals are 10, 9, 10, and 10. These observations share data with threshold selection and are not fresh rejection estimates.

The original/order-on real threshold is only 0.000001 because every wrong-work calibration score is zero after multiplication. This degenerate calibration boundary warrants further testing. Original order quality also zeroes the correct opening passage: only 17/162 query tokens lie within selected blocks, and the uncovered-token penalty outweighs their objective. All candidates tie at zero, so the unique-retrieval and admission tests fail.

In the two additional blocks, both tolerant variants admit the mechanism passage with 3/5 correct edges and one extra edge. The original/order-on mechanism likewise becomes a zero-score tie: its correct source covers 46/97 tokens, and the 51 uncovered tokens erase its positive objective. The continuation retains 2/2 links in every variant but cannot satisfy the inherited three-atom admission minimum. No block is omitted from the audit denominator.

## Verification, limits, and next experiment

All **59 tests passed** before execution. The separate auditor verified hashes, generated seeds and identity spans, frozen predictions and aliases, calibration sealing, all 1,616 decisions and paths, 172 summaries, and 384 paired contrasts. It independently calculated order objectives using a full token-DP matrix, including all 18,400 shuffled candidate qualities. Shared nonidentity shuffle controls recompute both base windows and order quality; their exceedances are descriptive, not p-values. Inputs, code, and outputs of experiments 1–7 remain unchanged.

Unknown tokens still earn positional credit: same-length, entirely unknown unrelated text can receive quality 1. The panel's fixed schema and rotation distractors do not test arbitrary sources, paraphrases, anchor-poor passages, or natural register transfer. All real references remain single-analyst structural judgments. Existing aliases remain experimental single-work evidence; no meanings, grammar, or production model are promoted.

The next experiment should **separate covered-span order agreement from the uncovered-query penalty and add anchor-poor, length-matched distractors**. Preregister a fixed coverage off/on ablation alongside order off/on, fresh calibration/evaluation seeds, and fixed negative families that preserve function-word positions while varying unknown content. Keep partial-passage recall, zero-score ties, pristine absent errors, and paired world denominators explicit. This would test whether apparent order discrimination comes from anchors, token mass, or coverage before expanding semantic claims. Independent natural validation still requires another auditable source work.
