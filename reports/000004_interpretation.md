# Experiment 4: reward mass and internal correspondence precision

Experiment 4 is complete and verified. Ordered decoding reduced unsupported sentence edges, and token mass made the reward of an identical token-span block invariant to the tested boundary regroupings. Neither change resolved Misinfons. Token mass also favored larger blocks, making Cartesian edge expansion substantially less precise. There is no semantic decipherment claim.

## Evidence and scope

The [registration](../experiments/kamri_precision_v4.md) preceded synthetic generation and scoring. The [frozen benchmark](../benchmarks/kamri_precision_v4.json) contains all nine existing real works as development material, eight synthetic calibration cases (seeds 4301–4308), and 40 fresh synthetic cases (seeds 4401–4440). Each of eight families contributes five fresh cases. Nothing was replaced after outcomes were observed.

Synthetic content forms are generated substitutions absent from the original lexicon. Function forms for “the” and “and” agree with frozen hypotheses by construction. Four candidate packets contain identical word inventories and sentence lengths, with three candidates permuted within sentences. The scorer receives text features and frozen predictions; substitution keys and shared occurrence identities remain in the evaluation harness. Synthetic labels therefore support engineering measurements, not natural-language translation accuracy or generalization to additional FL works.

All four variants use protected abbreviations, up to 2:2 effective-unit blocks, lexical scoring, floor 0.72, and the unchanged v1 lexicon. The factorial crosses effective-unit/token reward with Cartesian/ordered edges. Calibration uses the maximum wrong-source strength plus 0.000001, separately for real development and synthetic calibration. Fresh synthetic scores never set thresholds. Admission additionally requires a unique top candidate and at least three linked FL atomic sentences.

## Fresh synthetic results

These edge counts include the top retrieval even when it is refused. Recall retains every reference edge in all 40 selected cases. Both reward modes uniquely ranked the correct packet first in 40/40 and correctly admitted 28/40. Each variant had 0/40 source-absent false admissions. The 12 refused cases remain in the admission denominator. These controls describe this small constructed domain, not a general false-match rate.

| Reward / decoder | Edge precision | Edge recall | Extra edges | Correct admissions |
|---|---:|---:|---:|---:|
| Effective / Cartesian | 133/150 (88.7%) | 133/135 (98.5%) | 17 | 28/40 |
| Effective / ordered | 127/137 (92.7%) | 127/135 (94.1%) | 10 | 28/40 |
| Tokens / Cartesian | 133/193 (68.9%) | 133/135 (98.5%) | 60 | 28/40 |
| Tokens / ordered | 127/137 (92.7%) | 127/135 (94.1%) | 10 | 28/40 |

Ordered decoding removes extra cross-product links but loses six correct edges compared with Cartesian expansion. Token reward alone is not an alignment-precision improvement: its larger selected blocks create many more Cartesian extras. Ordered decoding gives the same aggregate fresh results under both reward modes, so the fresh panel supplies no evidence that token mass improves retrieval or decoded correspondence accuracy.

Both ordered variants proposed 1,156 token pairs; 1,067 agree with generated occurrence identities (92.3% precision). They recover 1,067/1,195 reference pairs (89.3% recall). Identity accuracy is stricter than word equality: aligning the wrong occurrence of a repeated word counts as an error. Cartesian variants make no token-pair claim.

The following family results apply to both ordered variants. Correct source top-1 is 5/5 in every family.

| Family | Correct admissions | Edge precision | Edge recall | Token precision | Token recall |
|---|---:|---:|---:|---:|---:|
| Diagonal boundaries | 5/5 | 15/15 | 15/15 | 150/150 | 150/150 |
| Source split | 5/5 | 20/20 | 20/20 | 150/150 | 150/150 |
| FL split | 5/5 | 20/20 | 20/20 | 150/150 | 150/150 |
| English insertion | 4/5 | 14/14 | 14/15 | 140/142 | 140/150 |
| English deletion | 4/5 | 14/14 | 14/15 | 137/138 | 137/145 |
| Abbreviation split | 5/5 | 20/20 | 20/20 | 150/150 | 150/150 |
| Sentence reordering | 0/5 | 9/19 | 9/15 | 40/126 | 40/150 |
| Sparse anchors | 0/5 | 15/15 | 15/15 | 150/150 | 150/150 |

Reordering accounts for all ten ordered extra edges and 86 of 89 wrong token pairs. A monotonic path can look plausible while linking unrelated portions inside a merged block. No reordered case was admitted, but those provisional paths remain visible in retrieval metrics. Sparse-anchor cases recover exact positional links yet fail the calibrated score threshold, demonstrating a coverage limit rather than a source-ranking failure.

## Real development diagnostics

All four variants uniquely rank 8/9 works correctly and correctly admit those eight. Misinfons ranks the Christisis source first, its correct source second, and remains refused. The source-absent rate of 0/9 is a development diagnostic: these same nine queries set the real wrong-source threshold.

| Reward / decoder | Retrieved edge precision | Retrieved edge recall | Conditional correct-source precision | Conditional recall |
|---|---:|---:|---:|---:|
| Effective / Cartesian | 47/52 | 47/58 | 49/51 | 49/58 |
| Effective / ordered | 47/50 | 47/58 | 49/49 | 49/58 |
| Tokens / Cartesian | 49/63 | 49/58 | 51/61 | 51/58 |
| Tokens / ordered | 49/52 | 49/58 | 51/51 | 51/58 |

“Conditional” supplies the corresponding source to isolate alignment from retrieval. Its perfect ordered edge precision is agreement with single-analyst structural reference edges on development data; it is not independent validation of token meanings. Retrieved results retain three wrong-source Misinfons edges for both ordered variants.

Christisis has six reference edges. Effective/Cartesian proposes eight, token/Cartesian ten, and both ordered variants recover exactly six. The two original cross-product errors are removed. On the supplied Misinfons source, every variant recovers only 2/9 reference edges, linking one FL atom to the “e.g.” English split. The change in reward mass does not solve its vocabulary or retrieval failure.

The frozen predictions cover 29/162 Misinfons tokens (17.9%), versus 52/141 Dark Side of Light tokens (36.9%). Misinfons’s predicted English forms are “the,” “it,” “two,” “to,” “as,” “in,” “of,” and “a.” This descriptive coverage comparison suggests a limited lexical signal for the technical passage; it does not establish a register effect, new content-word meanings, or causation. No register normalization or lexical retraining was performed.

## Boundary rewards and order controls

There are 151 unique selected blocks across the real queries' candidate-specific alignments, including wrong-source candidates, with identical spans feasible under both legacy and protected proposals. Four actually change effective-unit counts; effective rewards change in all four, while token rewards differ by exactly zero. The other 147 comparisons do not change representation and are consistency checks. For the Misinfons “e.g.” block, effective reward changes from 0.240000 to 0.186667, while token reward remains 0.163333 in both representations.

This establishes reward invariance for identical spans. It does not establish globally invariant retrieval: the bounded block proposal space, gap paths, and merge regularization can favor different partitions.

Twenty shared FL atom permutations per real query and ten per fresh synthetic case were scored after rebuilding adjacency. In the 40 fresh cases, 11 had no shuffled maximum reach the observed strength under either reward mode. In 29, at least one did. One effective-mode case had 10/10 exceedances. Identity and repeated permutations were allowed by the registered sampling procedure: 55 of the 400 synthetic draws were the original order. The headline exceedances therefore cannot establish that a changed order works equally well.

A descriptive post-run audit of the same saved controls finds nonidentity exceedances in seven cases under each reward mode: 37/345 nonidentity draws for effective reward and 32/345 for token reward. All original draws remain in the registered summaries. These controls are not p-values, and lexical inventories remain unchanged under shuffling.

## Verification and reproducibility

One final model execution completed in 18.1 seconds after 31 unit/synthetic tests passed. The [verification receipt](000004_verification.json) checks input/raw/code/output hashes, all 228 result rows, reference and token spans, decoder evidence, calibration separation, fixed denominators, source-absent decisions, shared permutations, summaries, and prior experiments. Experiments 1–3 and the execution-frozen model code are unchanged. Full scores, predictions, token paths, rankings, and controls are in the [immutable run directory](../runs/000004_kamri_precision_mass/report.json).

The execution-frozen auditor passed the v4 checks but failed its final historical check because v1 `input_hashes` uses document IDs hashing text, while later runs use file paths hashing files. The separately saved [v4a auditor](../scripts/verify_precision_v4a.py) handles both formats. Its hash and correction are in the verification receipt. No input, model, threshold, result, or frozen auditor was changed; no model rerun followed the outcomes.

```sh
uv run python scripts/run_precision_v4.py --run-id replay_000004
uv run python scripts/verify_precision_v4a.py
```

The verification command audits the original registered run. Replays require a new directory and retained local raw/normalized/synthetic documents; they reproduce existing evidence rather than supplying new fresh cases. The generated benchmark, saved code, and dependency files must accompany the project.

## Next experiment

Audit register-aware lexical hypotheses for the unresolved technical passage, using these nine real works and all 48 synthetic cases as development data. Before measuring a new method, select and freeze additional independently sourced real passages and negative candidates. Preserve Misinfons’s failure and unsupported lexical abstentions. Treat non-monotonic block correspondence as a separate known weakness: this experiment shows its failure under controlled reordering, but the supplied Misinfons reference edges are ordered and do not establish that reordering explains its failure.
