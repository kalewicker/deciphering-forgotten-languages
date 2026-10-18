# Experiment 3 completed: better passage recovery, uneven generalization

The registered eight-way comparison is complete and verified. All variants used the same **0.72 match floor**. Protecting abbreviations and allowing adjacent sentence blocks improved the previously observed difficult passages, but their combination did **not** consistently improve the two fresh inputs. Preserve this failure; do not select a winner and retune on these results.

The full protected/multi/lexical variant recovered **43/45 development reference edges**, with **45 proposed edges**. On fresh inputs it ranked **1/2** sources first and recovered **4/13 reference edges**, with **7 proposed edges**. Every variant admitted the Risk Mathematics source and refused Misinfons. There were no fresh source-absent false admissions, but only two source-absent queries per variant.

## Complete fresh comparison

| Boundaries | Effective-unit blocks | Scoring | Correct source top-1 | Correct admissions | Correct / proposed / reference edges | Absent false admissions |
|---|---|---|---:|---:|---:|---:|
| Legacy | 1:1 | Structural | 1/2 | 1/2 | 4/6/13 | 0/2 |
| Legacy | 1:1 | Lexical | 1/2 | 1/2 | 4/5/13 | 0/2 |
| Legacy | Up to 2:2 | Structural | 1/2 | 1/2 | 4/10/13 | 0/2 |
| Legacy | Up to 2:2 | Lexical | 2/2 | 1/2 | 6/6/13 | 0/2 |
| Protected | 1:1 | Structural | 1/2 | 1/2 | 4/6/13 | 0/2 |
| Protected | 1:1 | Lexical | 2/2 | 1/2 | 6/6/13 | 0/2 |
| Protected | Up to 2:2 | Structural | 1/2 | 1/2 | 4/10/13 | 0/2 |
| Protected | Up to 2:2 | Lexical | 1/2 | 1/2 | 4/7/13 | 0/2 |

These are correlated comparisons on the same two inputs, not sixteen independent trials. Correct source ranking alone does not imply an admitted alignment. Edge counts include links from the top-ranked source even when the admission rule refuses it; they are not automatically accepted claims. Structural references are provisional, single-analyst span correspondences, not independently validated semantic labels.

## The development gains separate into identifiable factors

All comparisons below hold the match floor, input collection, and other factors fixed within this run. Seven prior source groups are development data; these are engineering diagnostics rather than fresh validation.

| Diagnostic | Legacy 1:1 lexical | Protected 1:1 lexical | Protected up-to-2:2 lexical |
|---|---:|---:|---:|
| Larsen passage, correct / proposed / reference | 3/3/9 | 7/7/9 | 7/7/9 |
| Manichaean hymn, correct / proposed / reference | 3/3/6 | 3/3/6 | 6/6/6 |
| All development groups, correct / proposed / reference | 36/36/45 | 40/40/45 | 43/45/45 |

Abbreviation protection recovered the missing Larsen links around “i.e.”. Adjacent blocks recovered both FL sentences corresponding to the hymn's single source sentence. The complete method still misses two Larsen edges; boundary handling does not solve all wording differences.

The full method also merges two Christisis sentence pairs into a 2:2 block, implying four Cartesian edges where the reference supports two. Those **two extra edges count against precision**. Development edge precision falls from 36/36 to 43/45 (95.6%), while recall rises from 36/45 (80.0%) to 43/45 (95.6%). This is a measured recall/precision tradeoff, not an unqualified improvement.

Lexical scoring has observable benefits at matched floors: for example, with protected 1:1 units, adding anchors raises development recovery from 36 to 40 edges and fresh top-1 from 1/2 to 2/2. The same anchor factor does not improve fresh top-1 with protected multi blocks. All 12 paired factorial contrasts are retained in the [machine-readable report](../runs/000003_kamri_passage_factorial/report.json); interactions matter.

## Fresh query 1: Risk Mathematics

The opening four Kamri sentences of [War Algorithmics](https://forgottenlanguages-full.forgottenlanguages.org/2019/05/war-algorithmics-quantum-game-theory.html) correspond structurally to the opening of Section 2 in [Gonçalves's arXiv paper](https://arxiv.org/abs/1211.6683). The source candidate is a declared PDF-pages-1–3 packet; its matched paragraph was visually checked on page 2.

All eight variants ranked the correct work first, admitted it, and recovered **4/4 edges** without extra edges. This input already works with matched-floor structural 1:1 alignment, so it gives no evidence that the more complex aligner is necessary. Frozen lexical candidates were emitted for 27/120 FL tokens (22.5%); the rest were abstentions.

One of the 20 atom permutations was the original order, and each variant's shuffle exceedance count was 1/20. These controls are descriptive; they do not provide a calibrated p-value.

## Fresh query 2: Misinfons remains unresolved

The seven opening Kamri sentences of [Misinfons and the Hypermemetic Logic](https://forgottenlanguages-full.forgottenlanguages.org/2019/09/misinfons-and-hypermemetic-logic.html) correspond provisionally to the Information Model subsection of [Frater U.D.'s Models of Magic](https://www.spiralnature.com/magick/models/). The opening changes topic/date wording, later prose adapts phrasing, and the alternate register is retained exactly as acquired.

Legacy multi lexical and protected 1:1 lexical ranked the correct work first but linked only FL sentence 5 to the English pair split by “e.g.”. They recovered **2/9 edges**, covered only **one FL atomic sentence**, and fell below the admission threshold. All 20 sentence shuffles matched or exceeded this isolated-match strength. Those variants do not establish an ordered passage recovery.

Combining protection with multi blocks changes that successful 1:2 block into a 1:1 effective-unit block, changing its reward weight. Meanwhile an unrelated Christisis alignment spans three FL atoms. Christisis therefore ranks first for the full variant, with strength 0.03020 versus 0.02667 for Models of Magic. The threshold is 0.03822, so the incorrect retrieval is **refused**, and the failure remains in the selected denominator.

The frozen lexicon emits candidates for only 29/162 tokens (17.9%). The register forms `ńańi`, `daċċęįš`, and `tawwdan` receive abstentions. Limited support, editorial adaptations, and block reward scaling may all contribute. This run does not isolate which causes the failure. No form was normalized, no meaning was added, and no fluent translation is claimed.

## Frozen protocol and evidence

The [registration](../experiments/kamri_passage_v3.md) fixed two additional source works before evaluation. A [pre-execution preparation amendment](../experiments/kamri_passage_v3a_amendment.md) corrected a sample-selection omission: a seventh Misinfons sentence fit the 180-word cap. The initial six-sentence input and initial freeze remain unchanged. The final [v3a benchmark](../benchmarks/kamri_passage_v3a.json) has 120-word and 162-word FL samples, 11 FL atoms, and 13 reviewed fresh edges. No model scores were examined before the correction.

The fixed candidate collection contains nine works, with Johnson Chapter 13 retained for Gad. English source scopes remain uneven. All earlier groups became development data. The exact v1 lexicon was reused, with no new induction or claim acceptance. Each variant's threshold is maximum wrong-work strength on development queries plus 1e-6; fresh query outcomes never set thresholds. Fresh English source documents remain allowable candidates/development distractors in the fixed collection.

Source-absent controls remove all editions of the correct work. All variants had 0/2 fresh false admissions, which is too small a sample to establish an error rate. Twenty shared atom permutations per query were generated with seed 2731. Adjacent block scores were rebuilt for each permutation, and protected FL groups survived only when their atoms stayed adjacent in original order.

The [immutable run report](../runs/000003_kamri_passage_factorial/report.md) records all eight variants, 72 query/variant outcomes, blocks, original Unicode spans, inferred edges, rankings, controls, thresholds, and predictions. The [verification receipt](000003_verification.json) confirms frozen input/raw/code/output hashes, Cartesian edge expansion, fixed denominators, development-only threshold computation, and unchanged prior-run code/artifacts. **24 unit/synthetic tests passed** before the single final run, which took approximately 31 seconds.

## Next experiment

Prioritize **precise links inside candidate passage blocks and register-aware evidence**, rather than increasing span size again. The same passage represented with different sentence boundaries should have comparable reward mass, and a 2:2 block should not automatically assert all four atomic correspondences. Develop those changes on these nine groups, audit uncertain word/phrase mappings, and register new source works before evaluating any proposed improvement. Do not reuse these two fresh outcomes as confirmation.

## Reproduce offline

```sh
uv sync --frozen
uv run python scripts/run_passage_v3.py --run-id replay_000003
uv run python scripts/verify_passage_v3.py --run-id 000003_kamri_passage_factorial
```

Existing run directories cannot be overwritten. Carry the retained normalized inputs and raw acquisition artifacts when moving the project; downloads must not replace frozen files. Preparation PDF extraction used the bundled pdfplumber/PDFium runtime and is separate from offline execution. The saved `freeze_passage_v3a.py` helper documents the preparation amendment and was added after execution; it is not part of the original run's code-hash set.
