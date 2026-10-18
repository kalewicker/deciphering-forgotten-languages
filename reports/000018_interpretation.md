# Experiment 18: frozen-candidate passage extension

Eight fixed extension units, two previously exposed components, 175 target tokens. Three primary and 34 secondary candidates were frozen from v17 before FL-only target predictions and source-only reference preparation. Shared lexicons and proposed target English were not used.

3/8 units pass the development positional-scoring gates. Four lack independent complete FL coverage; one has 21 FL versus 22 source tokens. They remain in the denominator. All FL evidence is historical/indexed; semantic and untouched-test eligibility remain zero.

| Predictor | All tokens | Predictions | Abstentions | Scoreable predictions | Verified positional matches | Conflicts | Unscoreable predictions |
|---|---:|---:|---:|---:|---:|---:|---:|
| primary | 175 | 34 | 141 | 16 | 16 | 0 | 18 |
| secondary | 175 | 88 | 87 | 37 | 37 | 0 | 51 |

Primary supported agreement over all frozen primary predictions: 16/34. Conditional agreement on scoreable predictions: 16/16. The unsupported remainder is unresolved, not proven wrong.

Registered one-sided ordering diagnostic p: 0.001; criterion p <= 0.01: met. 0/999 null match counts meet or exceed the observed count, with 0 exact ties; null mean 2.551552, maximum 8. All orders, gates and prediction denominators are preserved. This is conditional development evidence on three supported units, not lexical accuracy or fresh validation.

| Fixed control | Primary verified matches | Secondary verified matches |
|---|---:|---:|
| rotate_+1 | 0 | 0 |
| rotate_+2 | 1 | 1 |
| rotate_-1 | 0 | 0 |
| rotate_-2 | 1 | 1 |
| reverse | 2 | 2 |

The full unit, token and per-form ledgers preserve every abstention, positional conflict and unmet evidence gate. The original training conflicts remain unresolved; no majority label, alias, alternate tokenization or offset repair was introduced. The next experiment must address the observed mismatch and missing evidence with a separately registered rule, retaining this archive.

Interpretation and evidence coverage

The frozen lookup transfers consistently at the supported token positions in this extension. The primary result is 16 verified positional matches out of all 34 primary predictions (47.06% supported); 18 predictions are unresolved. The separate conditional result is 16/16 among scoreable positions. This does not mean 100% translation accuracy. The secondary diagnostic likewise has 37 supported matches out of 88 predictions, with 51 unresolved. Its zero observed positional conflicts do not justify selecting it as the primary model after seeing the outcome.

The 175 target-token denominator is retained throughout. The primary lookup abstains on 141 tokens and the secondary lookup on 87; prediction coverage is 19.43% and 50.29% respectively. The two previously conflicting forms, ċu and ńi, account for thirteen extension tokens; both predictors abstain on them rather than replacing the conflicts with majority labels. All unknown forms and abstentions remain visible in the token ledger.

Coverage of the exact fixed extension units:

| Unit | FL tokens | Source tokens | Development positional scoring | Primary matches / predictions | Secondary matches / predictions |
|---|---:|---:|---|---|---|
| 03:005 | 22 | 22 | eligible | 5 / 5 | 14 / 14 |
| 03:006 | 16 | 16 | eligible | 1 / 1 | 7 / 7 |
| 03:007 | 21 | 22 | equal_token_counts | 0 / 2 | 0 / 16 |
| 03:008 | 38 | 38 | historical_fl_unique_complete | 0 / 8 | 0 / 20 |
| 13:005 | 34 | 34 | eligible | 10 / 10 | 16 / 16 |
| 13:006 | 13 | 13 | historical_fl_unique_complete | 0 / 5 | 0 / 7 |
| 13:007 | 17 | 17 | historical_fl_unique_complete | 0 / 1 | 0 / 3 |
| 13:008 | 14 | 14 | historical_fl_unique_complete | 0 / 2 | 0 / 5 |

The three scoreable units contain 72 FL tokens. Four independently preserved complete FL statements are available in the extension, but unit 03:007 has unequal lengths (21 versus 22) and therefore does not receive invented one-to-one reference positions. Four more units lack a full independent FL snapshot. Their proposed FL strings are preserved as author transcriptions; they are not promoted into verified source captures. Predictions on all five unresolved units remain in the full predictor denominators and are not counted as proven errors.

The reference English comes only from consecutive complete statements in the saved publisher HTML, beginning immediately after each fixed v16 source anchor. It is not the target reading-edition English. Candidate dictionaries were frozen first, FL-only targets and predictions second, and references/gates third. The seals and UTC timestamps demonstrate that staging. This makes the lookup deterministic and prevents target-reference-dependent revision; it does not make the previously exposed inventory a blinded test.

All 999 registered permutations and five fixed controls keep the predictor outputs, evidence gates and complete eight-unit denominator unchanged. The permutation mean is 2.55 verified primary matches, maximum 8, compared with the observed 16. No null count met or exceeded the observation, and no exact ties occurred; the finite-resolution corrected diagnostic p is 1/1000, not zero. This supports ordering-specific development transfer on the three scoreable units. The source-coverage limitation is not removed by that result.

135 tests passed. The independent verifier rebuilds the candidate dictionaries solely from v17, replays all FL-only predictions, verifies pre-reference seals, recovers the same source continuations and token spans, independently counts every prediction/abstention/unsupported outcome, and replays all controls/permutations and integer tail counts. Experiments 1–17 are hash-verified and preserved. The positional lookup executed; no translation model, new lexical induction or shared lexicon was used. Semantic training labels and untouched-test units remain zero.

The next falsifiable step is a separately preregistered bounded alignment diagnostic on 03:007: retain all 21 FL and 22 source tokens, enumerate every possible single-English-token omission using the already frozen candidates, preserve every tie and failure, and compare the maximum alignment score against controls that perform the same complete search. That can test whether one local gap explains the positional mismatch without choosing a favorable repair after the fact. It must not overwrite this failed length gate or certify a translation. The four missing FL captures require independent source evidence before they can be scored.

Artifacts: [registration](../experiments/kamri_transfer_v18.md), [frozen candidates](../data/v18/frozen_candidates.json), [FL-only targets](../data/v18/targets.json), [prediction seal](../data/v18/prediction_seal.json), [source-only references](../data/v18/frozen_references.json), [reference seal](../data/v18/reference_seal.json), [immutable manifest](../runs/000018_kamri_passage_transfer/manifest.json), [all 175 token outcomes](../runs/000018_kamri_passage_transfer/token_ledger.json), [all unit gates](../runs/000018_kamri_passage_transfer/unit_ledger.json), and [independent verification](000018_verification.json).

Reproduce verification with `.venv/bin/python scripts/verify_transfer_v18.py` and the suite with `.venv/bin/python -m unittest discover -s tests -q`. The run script refuses to overwrite its directory. Preparation is one-shot: do not rerun the prediction script into sealed data/v18, because it writes the target export before checking for existing predictions. Use the verifier to reproduce the completed checks; any continuation needs a fresh registered directory.
