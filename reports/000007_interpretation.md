# Experiment 7: controlled editorial robustness

Experiment 7 is complete and verified. The full scoring combination recovers all nine reviewed opening Misinfons edges, proposes one extra edge, and remains unadmitted. On fresh synthetic conditions it increases unique correct retrieval from 36/128 to 64/128, but does not solve editorial robustness: every variant fails unique retrieval on the fully edited condition, source-absent errors persist, and some recall gains reduce token precision. No variant is promoted to the default and no lexical meaning is newly supported.

## Registration, panels, and comparison

The [registration](../experiments/kamri_editorial_v7.md) fixes the experiment before synthetic generation or scoring. The [benchmark](../benchmarks/kamri_editorial_v7.json) freezes 32 calibration conditions from two generated worlds, 128 fresh conditions from eight different worlds, and twelve unchanged real development/audit queries. Each world has six statements and receives all sixteen combinations of four edits. The 128 conditions are paired observations from **eight independently seeded texts**, not 128 independent samples.

The edits are FL punctuation changes, four-word English parenthetical insertions per statement, two extra repetitions of an English content word per statement, and six deliberately conflicting FL function forms per packet. Gold correspondence uses occurrence identities: inserted words have no FL identity, and the deliberately conflicting forms retain their original generated identity. This is constructed noise/polysemy, not evidence about natural FL word meanings.

Each four-candidate collection contains the corresponding packet and three within-statement rotations of source words. Candidate positions are randomized once per world and reused across conditions. All candidates preserve per-statement word bags, lengths, editorial insertion positions, and punctuation. These close order distractors deliberately test discrimination; they are not sampled English works.

Eight variants cross three binary factors. In the tables, a three-digit code is **P/R/L**, corresponding to the full run ID `pP_rR_lL`:

- **P:** neutralize the punctuation feature to 0.5, removing both agreement bonuses and disagreement penalties.
- **R:** replace absolute repetition-pair indices with eight-bin relative-position repetition pairs, preserving multiplicity and coarse order.
- **L:** give unmatched lexical predictions neutral credit: lexical overlap k/m becomes 0.5 + 0.5k/m when predictions exist.

`000` exactly reproduces the inherited scorer and the v5/v6 gated-alias paths. Every variant uses the same unchanged predictions, eligibility rules, aliases, gate, decoder, length ratio, feature weights, floor, token-mass normalization, penalties, search scope, and three-linked-atom admission requirement. L changes block scoring; it does not repair known token mismatches inside the decoder.

Thresholds are calibrated separately per variant. Synthetic thresholds use maximum wrong-candidate strength over the 32 calibration conditions plus 1e-6; real thresholds use maximum wrong-work strength over ten available v5 development queries plus 1e-6. Both threshold tables were persisted and sealed **before** scoring the 128 fresh conditions and two extra Misinfons blocks. No fresh outcome sets a threshold or chooses a variant.

## Fresh synthetic results

All rows retain the fixed 128-condition denominator. Edge/token metrics include unadmitted retrievals. Token comparisons refer to generated occurrence identities, not natural semantic translation accuracy.

| P/R/L | Unique correct / 128 | Correct admissions / 128 | Absent false / 128 | Retrieved edge correct/proposed | Edge recall count / 768 | Token precision | Token recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| 000 | 36 | 8 | 5 | 186/233 | 186 | 1699/2185 | 1699/7488 |
| 001 | 45 | 8 | 5 | 234/294 | 234 | 2119/2728 | 2119/7488 |
| 010 | 47 | 8 | 3 | 209/261 | 209 | 1891/2463 | 1891/7488 |
| 011 | 60 | 8 | 3 | 299/340 | 299 | 2610/3193 | 2610/7488 |
| 100 | 34 | 16 | 10 | 160/234 | 160 | 1446/2240 | 1446/7488 |
| 101 | 54 | 16 | 10 | 256/346 | 256 | 2286/3232 | 2286/7488 |
| 110 | 46 | 16 | 6 | 264/328 | 264 | 2154/3090 | 2154/7488 |
| 111 | 64 | 16 | 6 | 348/452 | 348 | 2924/4194 | 2924/7488 |

Wrong-source admissions with the correct source present are zero in all eight variants. That does not imply successful source rejection: removing the correct candidate causes false admissions in every variant.

The full combination recovers more edges and tokens but lowers retrieved token precision from 77.8% to 69.7%. Variant 011 has 60 unique recoveries, 3 source-absent errors, and token precision 81.7%; adding P increases unique retrieval to 64 but source-absent errors to 6 and reduces token precision. Those observed tradeoffs are retained; this experiment does not select a winning model.

Only pristine cases are admitted by variants with P off. P-on variants additionally admit punctuation-only cases. No other edited condition is admitted by any variant. Consequently, the admission count of 16 for P-on models is eight pristine plus eight punctuation-only cases, not broad tolerance to combined editorial changes.

## Every condition and its failures

Edit letters: **C** = FL comma/semicolon changes; **H** = English parenthetical insertion; **R** = repeated-word insertion; **X** = conflicting FL function forms. Each cell below is unique correct retrieval **out of eight paired worlds**. Codes in the columns refer to scoring factors, not edit masks.

| Mask | Edits | 000 | 001 | 010 | 011 | 100 | 101 | 110 | 111 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | Pristine | 8 | 8 | 8 | 8 | 8 | 8 | 8 | 8 |
| 1 | C | 8 | 8 | 8 | 8 | 8 | 8 | 8 | 8 |
| 2 | H | 0 | 0 | 3 | 3 | 2 | 2 | 6 | 6 |
| 3 | C H | 0 | 0 | 3 | 3 | 2 | 2 | 6 | 6 |
| 4 | R | 7 | 7 | 8 | 8 | 6 | 6 | 8 | 8 |
| 5 | C R | 4 | 4 | 5 | 5 | 6 | 6 | 8 | 8 |
| 6 | H R | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 0 |
| 7 | C H R | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 0 |
| 8 | X | 8 | 8 | 8 | 8 | 1 | 8 | 1 | 8 |
| 9 | C X | 0 | 8 | 0 | 8 | 1 | 8 | 1 | 8 |
| 10 | H X | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 11 | C H X | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 12 | R X | 1 | 2 | 2 | 7 | 0 | 2 | 0 | 2 |
| 13 | C R X | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 2 |
| 14 | H R X | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 15 | C H R X | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

All variants recover all 48 conditional reference edges and all 468 generated token pairs in the pristine and punctuation-only conditions. Punctuation-only changes therefore affect legacy admission, not its conditional correspondence recovery in this panel.

Parenthetical insertions expose a larger weakness. Even some uniquely correct retrievals have no correct reference edges: coarse structural agreement can select the corresponding packet while matching the wrong internal span. In H-only cases, conditional correct edges are 0/48 for 000, 010, and 011, despite 010/011 each uniquely ranking the correct source in three worlds. Variant 110 recovers 36/48 conditional edges there, while 111 recovers 30/48. Better ranking is not equivalent to internal correspondence recovery.

In X-only cases, models 100 and 110 recover zero conditional reference edges; adding L restores 48/48. The inherited decoder still drops the six deliberately conflicted identities per packet: 420/468 conditional generated token matches remain, rather than 468/468. Neutral scoring can retain a passage without validating or fixing every token prediction.

The fully edited condition has zero unique retrieval and zero correct conditional reference edges/tokens in every variant. Length scoring, gap costs, and the floor were deliberately unchanged, so this experiment does not resolve severe combined edits by construction or outcome.

## Paired effects and negative-control concentration

The saved [comparisons](../runs/000007_kamri_editorial_robustness/comparisons.json) contain 960 condition-versus-pristine contrasts and 1,536 matched scoring-factor contrasts. Each scoring factor has 512 contrasts across the same worlds/conditions and four settings of the other factors. Mean differences below are descriptive and correlated; they are not confidence intervals or independent-sample estimates.

| Scoring factor switched on | Mean change in unique-correct indicator | Mean change in correct admission | Mean change in absent false admission | Mean conditional correct-edge change |
|---|---:|---:|---:|---:|
| P | +0.0195 | +0.0625 | +0.0313 | +0.2070 |
| R | +0.0938 | 0 | −0.0234 | +0.4961 |
| L | +0.1172 | 0 | 0 | +0.6328 |

Admission effects include each variant's separately calibrated threshold. These averages do not establish uniform improvement across edit families; the matrix shows reversals and severe failures.

Source-absent errors concentrate in the easiest conditions. Baseline has **5/8 false admissions on pristine source-absent controls**, producing its aggregate 5/128 count. Relative-repetition variants with P off have 3/8 pristine false admissions. Turning P on repeats those errors on punctuation-only conditions: ten conditions from five worlds under absolute repetition, or six conditions from three worlds under relative repetition. An aggregate fraction over 128 heterogeneous, paired conditions would conceal this concentration and should not be treated as a general error-rate estimate.

The calibration panel's maximum wrong strength is not a sufficient guard against fresh-world order distractors. Further calibration and rejection testing remain necessary before adopting these scoring changes.

## Real development results

All twelve real queries are development evidence. The unchanged ten available v5 queries set real thresholds; the two additional Misinfons blocks do not. Baseline exactly reproduces their earlier gated scores and paths. No independent alternate-register work or new semantic reference has been acquired.

| P/R/L | Opening Misinfons conditional correct/proposed/reference | Opening admitted | Mechanism conditional correct/proposed/reference | Mechanism admitted |
|---|---:|---|---:|---|
| 000 | 2/2/9 | No | 2/2/5 | No |
| 001 | 2/2/9 | No | 3/4/5 | Yes |
| 010 | 2/2/9 | No | 2/2/5 | No |
| 011 | 0/3/9 | No | 3/4/5 | No |
| 100 | 3/3/9 | No | 1/1/5 | No |
| 101 | 4/4/9 | No | 3/4/5 | Yes |
| 110 | 4/4/9 | No | 1/1/5 | No |
| 111 | 9/10/9 | No | 3/4/5 | Yes |

With 111, the opening source uniquely ranks first and nine distinct FL/source reference edges are recovered, with one extra edge. Its strength is 0.0333612356, below the separately calibrated real threshold 0.0643803267. Minimum linked-atom support is now satisfied; threshold remains the rejection reason. This is improved structural recall on a repeatedly inspected development passage, not a decipherment or admission success.

The full combination retrieves all 64 reference edges across the ten calibration/development queries with one extra edge, versus baseline 57 correct out of 57 proposed. Some other variants lose source ranking or correspondence accuracy on the opening. All remain reported.

The continuation remains unadmitted in every variant because its two atoms cannot meet the inherited three-atom requirement. Seven variants recover both of its reference links; 100 recovers one. Mechanism admissions under 001, 101, and 111 each retain an extra edge and only three of five correct references. Admission therefore must not be read as complete passage recovery or semantic correctness.

Real development source-absent errors are zero, but those ten queries also set the thresholds; this is a calibration diagnostic. The two same-article audit controls are also zero and remain correlated with known development material. The Altruist source remains unavailable as recorded in experiment 5; no missing source is replaced.

## Order controls, verification, and next experiment

Ten shared nonidentity FL atom permutations per fresh condition and real query were saved with seed 7831; calibration has zero permutations. Each variant recomputes windows for the same orders. Across the 1,280 fresh draws, shuffled maxima reach/exceed the observed top strength 948 times for 000 and 589 times for 111. These totals include cases with weak or zero observed strength, repeat orders, and paired worlds; they are descriptive diagnostics, not p-values or 1,280 independent negative examples. Per-query counts and actual unique-order denominators are saved.

One final model execution completed in **250.9 seconds** after **52 tests passed**. The [verification receipt](000007_verification.json) checks all 1,376 rows, all 224 summaries, input/raw/code/output hashes, regeneration of every synthetic condition, occurrence identities and spans, frozen predictions/origins, calibration-before-fresh sealing, thresholds, token paths, edge/token counts, admissions, source-absent controls, permutations, paired contrasts, exact legacy v5/v6 regression, and unchanged experiments 1–6. No outcome-dependent model rerun or tuning was performed.

The [immutable report](../runs/000007_kamri_editorial_robustness/report.json) retains all rankings and paths. Replays require retained local data and a new directory:

```sh
uv run python scripts/run_editorial_v7.py --run-id replay_000007
uv run python scripts/verify_editorial_v7.py
```

The next useful experiment is a source-discrimination and admission stress test using more independently seeded calibration/fresh worlds and a fixed token-order scoring ablation before candidate ranking. Preserve these v7 conditions as development material, include pristine source-absent controls explicitly, and keep length/edit severity strata visible. This addresses the observed close-distractor false admissions before adopting tolerant scoring or expanding the dictionary. Independent natural alternate-register validation still requires another auditable source work; none is established here.
