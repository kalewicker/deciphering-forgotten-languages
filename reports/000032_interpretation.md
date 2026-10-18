# Experiment 32: frozen symbolic transfer passes; positional alignment remains imperfect

The registered **synthetic-transfer criterion passes**. A mapping learned from eight separate synthetic training passages recovers all **96 supported seen-vocabulary parent cases**, both with and without a repetition-equivalent impostor. All **840 absent-parent/impostor-only panels abstain**, all **420 exact-duplicate panels abstain**, and all **900 dense-unknown/unseen-key panels abstain**. Every unmapped or blocked query token remains unmatched.

This is supervised symbolic transfer on fixed generated fixtures, not natural FL decipherment. It uses aligned training supervision that has not been established for the natural examples. Of all 420 source-present test cases, **120 retrieve their parent and 300 abstain**. Among qualified parent alignments, **6,752 of 6,772 returned token positions match the exact generated origins; 20 do not**. Passing retrieval therefore does not establish fully correct positional alignment.

All **270 tests pass**. Independent regeneration, mapping learning and maximum-match/LCS replay agree with the execution code's minimum-cost gap alignment on every one of **2,520 distinct pair alignments** and **2,100 panels**. All 31 earlier runs and their deliverable hashes verify unchanged; no natural target is rescored or natural meaning/source identity admitted.

## What the frozen training adds

Four trained keys each supply two aligned passages. Each passage includes three permutations of all 24 trained symbols, plus four explicit barriers. The learner uses only these supplied aligned observations, requiring one source outcome and support in both training units. It freezes **96 key-specific query aliases mapping to 24 source symbols**, with zero conflicting or insufficient-support entries in this training corpus. Withheld source types 24–31 and alternate contextual aliases never enter the mapping.

The 196-file code/input seal precedes full training generation. The training receipt is recorded at 09:34:11.328704 UTC; the mapping freezes at 09:34:11.412430; full test preparation follows at 09:34:20.974167. Test-origin labels do not update the mapping. All prediction outputs and their hash receipt precede oracle-origin assessment. The generator and keys are public; this is controlled development with new sequence contexts, not a secret-key or natural-language held-out trial.

The 84 test parents include 24 seen-vocabulary, 24 sparse-withheld-type, 24 dense-withheld-type and 12 unseen-key cases. Five transformations give 420 queries; five candidate-panel conditions give 2,100 panels. Keys, vocabulary groups, transformations and panels reuse underlying passage patterns, so these counts do not represent independent population samples.

The aligner gives match credit only to a frozen, nonnull query-to-source entry equal to an unblocked candidate token. All other tokens remain gaps with cost1 each. Qualification requires at least 24 known matches and 80% matched coverage of both complete sequences. Unknowns and barriers remain in those denominators; none is silently deleted or source-filled. The fixed threshold was chosen to cover the declared synthetic edit schedule, not calibrated on natural data.

## Transfer results and retained abstentions

For seen-vocabulary queries, each row contains all24 parents:

| Mechanism | Potentially available | Present parent retrieved | Abstentions | Exact origin / returned matches in qualified parent pairs |
|---|---:|---:|---:|---:|
| Bijective renaming | 24/24 | 24/24 | 0 | 1,464 / 1,464 |
| Insertion after every seventh position | 24/24 | 24/24 | 0 | 1,464 / 1,464 |
| Deletion of every seventh position | 24/24 | 24/24 | 0 | 1,244 / 1,248 |
| Alternating contextual alias | 0/24 | 0/24 | 24 | No qualified pairs |
| Periodic local swaps | 24/24 | 24/24 | 0 | 1,236 / 1,252 |

The first, second, third and fifth rows form the frozen96-case positive requirement. The contextual aliases were not trained: their unavailable features and abstentions are retained, not counted as a rejection of contextual mappings in general.

Across the complete test inventory:

| Vocabulary/key group | All queries | Potentially available | Present parent retrieved | Present abstentions |
|---|---:|---:|---:|---:|
| Seen vocabulary and trained key | 120 | 96 | 96 | 24 |
| Sparse withheld types | 120 | 48 | 24 | 96 |
| Dense withheld types | 120 | 0 | 0 | 120 |
| Unseen key | 60 | 0 | 0 | 60 |
| Total | 420 | 144 | 120 | 300 |

Potential availability is a pre-score upper bound on match coverage, not a guarantee of order-compatible matches. Sparse-withheld bijective queries recover all24 parents while leaving their unknown tokens unlabeled. Sparse reordering has24 potentially available queries but no qualified parent alignments; the combined missing forms and swaps exceed the readout's supported coverage. Sparse insertions/deletions/context variants also abstain. All 276 unavailable queries remain in the denominator, producing **1,380 unavailable panels**, all of which abstain.

The saved decoder records **10,052 null query-token labels**, including blocked anchors, insertions, unseen aliases/types and unseen keys. None receives a matched trace diagonal. The result does not show prediction of new lexical types: it shows transfer of already learned symbolic entries into new contexts, with conservative abstention elsewhere.

## Impostors, exact duplicates and specificity scope

| Candidate panel | All panels | Correct-parent nominations | Non-parent nominations | Abstentions |
|---|---:|---:|---:|---:|
| Parent plus shuffle/different-pattern/frame | 420 | 120 | 0 | 300 |
| Parent absent | 420 | 0 | 0 | 420 |
| Equivalent impostor replaces parent | 420 | 0 | 0 | 420 |
| Parent plus equivalent impostor | 420 | 120 | 0 | 300 |
| Parent plus exact duplicate | 420 | 0 | 0 | 420 |

All 84 impostors preserve the full anonymous repetition pattern, but shift source symbol identities. The separately frozen mapping can distinguish this alternative from the true generated key; within-paragraph repetition fingerprints alone lacked that information. This demonstrates the capability of the combined supervised-mapping/gap method on this assay. The corpus and readout differ from v31, so the two experiments are not a controlled component ablation or a natural error-rate comparison.

Exact duplicate candidates still have identical visible constraints. In 120 duplicate panels, the qualified parent and duplicate tie and the method abstains. The other 300 duplicate panels abstain for insufficient coverage. The method does not claim to recover hidden provenance from byte-identical alternatives.

## Retrieval success is not unique positional truth

There are 120 distinct qualified true-parent pairs. Their representative paths return 6,772 known matches;6,752 agree with the exact generator origins. The 20 positional disagreements occur in 16 qualified pairs: four deletion pairs and twelve reordering pairs, with repeated key/profile structure. They do not imply20 independent observed linguistic errors.

For example, seen-key 11, passage 0, reordering query position 14 is returned against source position 15 although its recorded origin is 13; both source positions contain `symbol8`. Token-value consistency therefore does not establish the correct occurrence. The chosen global order assumption and repeated values can leave a plausible representative path with wrong origin positions.

All 120 qualified pairs have multiple optimal **operation paths**. Some alternatives merely commute gaps around unmatchable barriers and need not change matched token pairs. The exact operation-path count is thus not a count of distinct semantic alignments, nor proof that every match is ambiguous. The report retains the chosen path, count and origin disagreements rather than interpreting deterministic tie-breaking as certainty.

## Verification, execution metadata and stopping boundary

All six synthetic-transfer requirements pass:96/96 supported present recoveries,96/96 supported parent-plus-impostor recoveries,840/840 rejection abstentions,420/420 duplicate abstentions,900/900 dense-unknown/unseen-key abstentions, and no matches on unadmitted/blocked tokens. These denominators overlap by design; they are not summed as independent trials.

The independent verifier imports no primary v32 code. It regenerates training and test surfaces/origins, independently learns the mapping and decoder, and uses a maximum-LCS recurrence to verify the minimum-indel-cost implementation. Every path's full token accounting, cost, optimal operation-path count, representative trace, candidate decision, origin metric and criterion agrees. It also checks hashes, model immutability, training/model-before-test chronology and all 31 prior run/seal inventories. The [verification receipt](000032_verification.json) passes.

The frozen run JSON retains an ambiguous legacy `model_executed:false` field. The **symbolic mapping learner and aligner did execute**; no external/neural translation model was used. The [post-run execution note](000032_execution_note.json) clarifies this bookkeeping issue without rewriting the sealed run, code or outcomes. Use the saved training, mapping and prediction receipts as execution evidence.

Natural scientific acceptance and semantic metrics remain null. Natural source identities, semantic labels, independent-review admissions and untouched linguistic admissions remain zero. Synthetic supervision, controlled symbol transfer and candidate retrieval do not establish natural word meanings, general edit robustness or unique source provenance.

Experiment 32 stops here. The next bounded step is an **ambiguity audit of these frozen synthetic alignments**: determine which matched pairs are forced across all optimal paths, preserve optional alternatives and compare forced/optional origin precision and retained coverage separately. Do not equate forced optimal pairs with truth automatically: the monotonic alignment model itself can be wrong for reordered material. Keep the mapping, retrieval decisions, coverage rule and original representative traces unchanged, and register the audit before measuring its outcomes. This is a positional-evidence boundary before any natural lexicon admission, not permission to rescore the FL pairs.

Artifacts: [registration](../experiments/synthetic_transfer_v32.md), [machine plan](../experiments/synthetic_transfer_v32.json), [preflight](../data/v32/preflight.json), [training pairs](../data/v32/training.json), [training receipt](../data/v32/training_receipt.json), [frozen mapping and learning ledger](../data/v32/frozen_mapping.json), [public test cases](../data/v32/public_cases.json), [separate origin oracle](../data/v32/oracle.json), [pre-score decode/availability/certificates](../data/v32/availability.json), [test preparation receipt](../data/v32/test_preparation_receipt.json), [benchmark](../benchmarks/synthetic_transfer_v32.json), [predictions and complete paths](../runs/000032_synthetic_transfer/predictions.json), [prediction receipt](../runs/000032_synthetic_transfer/prediction_receipt.json), [assessment and origin metrics](../runs/000032_synthetic_transfer/assessment.json), [immutable report](../runs/000032_synthetic_transfer/report.json), [verification](000032_verification.json), and [deliverable seal](000032_deliverable_seal.json).

Verify offline with `.venv/bin/python scripts/verify_synthetic_transfer_v32.py`; run tests with `.venv/bin/python -m unittest discover -s tests -q`. Preparation stages and execution refuse existing outputs; verification preserves its successful receipt.
