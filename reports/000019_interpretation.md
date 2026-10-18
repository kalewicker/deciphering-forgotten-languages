# Experiment 19: a single gap fits the frozen predictions, but its location remains unresolved

The registered conditional development criterion is met: the maximum primary match count is 2/2, with a search-corrected one-sided permutation p of 0.005. This does **not** identify a unique gap. Fourteen primary maximizers remain, and the secondary diagnostic retains two tied hypotheses. No token alignment or word meaning is accepted as semantic gold.

Exactly one previously exposed unit, 03:007, was nominated before scoring because experiment 18 found 21 FL tokens versus 22 publisher-source tokens. Experiment 19 reuses the unchanged v18 predictions from three primary and 34 secondary candidates. It searches all 22 monotone alignments that leave one English token unpaired. Every source token stays in the evidence and retains its original identity and document offsets. Every FL token retains both target-string and historical-document offsets. No new prediction, lexical induction, shared lexicon, alias, accent stripping or tokenization change was introduced.

| Quantity | Primary | Secondary, descriptive |
|---|---:|---:|
| All FL tokens | 21 | 21 |
| Frozen predictions | 2 | 16 |
| Abstentions | 19 | 5 |
| Maximum matches | 2 | 16 |
| Conflicts at a maximizer | 0 | 0 |
| Maximizing gaps, zero-based | 0–13 | 1, 2 |
| Unique gap | no | no |

The primary predictions concern two later function-word positions. Any gap in positions 0–13 shifts both into their matching source positions, so all fourteen gaps tie. The primary match count tests compatibility with the bounded gap family; it cannot locate an omission in the earlier sentence.

The secondary maximum is 16/16 at gaps 1 and 2. These hypotheses leave **“an”** and **“Āgama”** unpaired, respectively. They differ in the English token aligned to FL “Agama”; the frozen lookup abstains on that FL form. The other twenty paired positions are identical. The primary/secondary maximizer intersection is therefore also [1, 2], and cannot select one hypothesis. No proper-name intuition or secondary score was used to break the tie. The previously conflicted form ńi remains an abstention.

All 999 seeded shuffles independently repeat the complete 22-gap search. Four null maxima equal the observed primary count of two; none exceeds it. The corrected tail probability is (1 + 4)/(1 + 999) = 0.005, with a null mean maximum of 139/999 = 0.139139 and maximum of two. The unchanged registered threshold is p <= 0.01. Secondary null curves are archived descriptively and do not substitute for the primary test.

| Fixed control, also searching all 22 gaps | Primary maximum | Secondary maximum |
|---|---:|---:|
| rotate +1 | 0 | 1 |
| rotate +2 | 0 | 1 |
| rotate −1 | 2 | 15 |
| rotate −2 | 0 | 1 |
| reverse | 0 | 1 |

Rotation −1 also reaches the primary maximum. This reinforces the limited resolution of two frozen anchors. The direct-index comparator, which pairs FL index i with English index i and leaves final English token 21 unpaired, has zero primary and one secondary match. The maximum-search correction accounts for searching gaps within each shuffled order; it does not make a previously exposed, mismatch-selected unit an untouched validation set or test unrelated-source rejection.

The original experiment 18 `equal_token_counts` failure remains unchanged. A separate gate permits only this registered gap diagnostic after independently checking source authority, complete statements, orderly source continuation, exact historical FL coverage and the fixed 21/22 lengths. Current raw FL remains unavailable. Semantic training eligibility and untouched-test eligibility remain zero. The four other v18 units missing complete independent FL coverage remain unresolved.

145 tests pass. The independent verifier reconstructs frozen predictions and original source/FL spans, retains the v18 gate, and replays all observed gaps, controls and 999 null searches using deletion-and-zip alignment rather than the execution scorer. It verifies integer ties, the unchanged criterion, all input/code/output hashes and preservation of experiments 1–18.

The next falsifiable step is a separately registered orthographic-anchor diagnostic. Calibrate a fixed matching rule on separate development units, keep 03:007 out of calibration, include wrong-name and source-absent controls, and then compare both retained gap hypotheses. The target remains previously exposed; this cannot be described as fresh held-out validation. Failure to distinguish the hypotheses must preserve both. Independent FL acquisition remains necessary for the four missing v18 statements.

Artifacts: [registration](../experiments/kamri_gap_v19.md), [frozen evidence](../data/v19/frozen_evidence.json), [immutable manifest](../runs/000019_kamri_single_gap/manifest.json), [all 22 full alignments](../runs/000019_kamri_single_gap/observed_alignments.json), [all 999 orders and score curves](../runs/000019_kamri_single_gap/permutations.json), [five fixed controls](../runs/000019_kamri_single_gap/fixed_controls.json), [machine report](../runs/000019_kamri_single_gap/report.json), and [independent verification](000019_verification.json).

Reproduce verification with `.venv/bin/python scripts/verify_gap_v19.py` and the suite with `.venv/bin/python -m unittest discover -s tests -q`. Preparation and execution are one-shot and refuse existing output paths; use the verifier for replay. Any changed hypothesis requires a new registration and output directory.
