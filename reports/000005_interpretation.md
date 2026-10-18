# Experiment 5: scoped lexical aliases

Experiment 5 is complete and verified, with one of two selected fresh sources unavailable. The fixed alias bundle moves Misinfons's corresponding source from third to first in the expanded candidate collection, but does not improve its corresponding-source score, recover additional reference links, or cause admission. The independently sourced Capra passage is recovered by every variant. No new lexical meaning is promoted to supported status.

## Registered comparison and source coverage

The [registration](../experiments/kamri_register_v5.md) precedes model execution and fresh correspondence scoring. All nine existing real works are development material; all 48 v4 synthetic cases are development regressions. Three variants share the v4 token-mass aligner, protected boundaries, up-to-2:2 blocks, ordered decoder, floor 0.72, and frozen v1 lexicon:

1. Baseline: original eligible predictions.
2. Universal aliases: override ńańi -> of, daċċęįš -> and, tawwdan -> that everywhere.
3. Gated aliases: override only when the query contains at least two distinct alias forms and at least three total occurrences.

The three meanings are external proposals from the [public Kamri report](https://www.reddit.com/r/ForgottenLanguages/comments/1v1q1fw/i_translated_all_24_kamri_posts_on_forgotten/), evaluated as a fixed bundle. The gate uses query tokens only. The original requirement for independently supported v1 entries is unchanged; alias predictions and token matches are separately labeled experimental. The scorer receives neither source answers nor reference annotations.

Two new source works were selected before scoring:

| Selected work | Input status | Frozen scope and reference |
|---|---|---|
| Capra, foreword to Metaphors of Consciousness | Available | Publisher front matter PDF pages 6–9, printed ix–xii; entire 1,252-word foreword. FL opening excerpt: 163 words, six statements, six audited edges. |
| Langston, The Accidental Altruist | Source unavailable | FL indexed opening excerpt retained: 178 words, eight statements. Publisher chapter and PDF routes returned subscription HTML and abstract, not chapter prose. Reference edges remain unavailable. |

Capra's [publisher preview](https://link.springer.com/book/10.1007/978-1-4613-3802-4) was downloaded and the matched prose visually checked on PDF page 7. Extraction joins line-wrap hyphens, removes headers/page labels, and repairs the visually checked extraction error “playa” to “play a.” The initial percent-encoded preview URL failed; the exact unencoded publisher href returned the PDF. An institutional quotation source found during discovery is retained as an unused acquisition artifact. Langston's [publisher chapter](https://link.springer.com/chapter/10.1007/978-3-642-37750-1_9) supplies bibliographic metadata and an abstract but no usable full prose in the finite acquisition. Neither case was replaced.

FL texts are explicitly indexed excerpts, not raw/current page snapshots. The [acquisition ledger](../benchmarks/inputs/register_v5_acquisition.json), saved receipts, failures, bytes, PDF extraction, and [frozen benchmark](../benchmarks/kamri_register_v5.json) preserve these distinctions. Available candidates comprise nine unchanged source packets plus Capra's foreword. The unavailable Altruist source is not represented by its abstract as if it were the corresponding chapter.

## Development audit of the proposals

The [alias audit](../benchmarks/inputs/register_v5_alias_audit.json) examines 14 occurrences against existing reviewed Misinfons/source spans. It distinguishes word presence from positional and semantic evidence.

| Proposal | Occurrences | Meaning present somewhere in corresponding span | Meaning absent in corresponding span | Exact equal-length positional projections |
|---|---:|---:|---:|---:|
| ńańi -> of | 7 | 7 | 0 | 0 |
| daċċęįš -> and | 4 | 3 | 1 | 0 |
| tawwdan -> that | 3 | 1 | 2 | 0 |

All 14 observations have unequal token counts between the FL atom and its reviewed English span. Eleven therefore establish only span-level compatibility, and three lack the proposed English word in that span. Multiple repeated English occurrences remain unresolved; the audit does not select one as token truth. Source absence is a conflict with the exact proposed correspondence, but may reflect editorial changes or imperfect structural references rather than uniquely falsifying a lexical hypothesis.

Every observation comes from one source work. Common function-word presence is weak evidence, and there is no independently established token-level semantic reference. All three proposals were retained in the registered comparison, including conflicting evidence. New supported lexical entries: zero.

## Misinfons result

| Variant | Corresponding-source rank | Prediction coverage | Corresponding-source strength | Conditional edges | Admitted |
|---|---:|---:|---:|---:|---|
| Baseline | 3/10 | 29/162 (17.9%) | 0.020165 | 2/9 | No |
| Universal aliases | 1/10 | 43/162 (26.5%) | 0.020165 | 2/9 | No |
| Gated aliases | 1/10 | 43/162 (26.5%) | 0.020165 | 2/9 | No |

The expanded pool adds a plausible Capra distractor, so the baseline rank of three differs from its rank of two in v4. This is a pool change, not a baseline algorithm change.

The alias variants leave the exact corresponding-source block unchanged: FL atom 5 links to English atoms 61–62 around “e.g.” Its strength remains 0.020164609, and only one FL atom is linked. Admission still fails both the 0.044721076 threshold and the three-linked-atom requirement.

Ranking improves because wrong-source strengths fall: Christisis decreases from 0.028670821 to 0.019197531, and Capra from 0.026941067 to 0.018381396. This is reduced competitor agreement, not additional recovery of the corresponding passage. With the correct source ranked first, retrieved metrics credit two existing correct edges instead of the baseline's three wrong-source edges. Conditional alignment remains 2/9 throughout.

All 20 nonidentity Misinfons shuffles reach or exceed the alias variants' observed top strength, versus 12/20 for baseline. The partial match supplies no convincing sentence-order discrimination in this control. These counts are descriptive and not calibrated p-values.

## Remaining development works

The eight other works have no alias occurrences, so all three variants give identical predictions and outcomes there. All eight corresponding sources rank first and are admitted. Across the nine development queries:

| Variant | Unique correct top-1 | Correct admissions | Retrieved edge precision | Retrieved edge recall | Conditional edge precision / recall |
|---|---:|---:|---:|---:|---:|
| Baseline | 8/9 | 8/9 | 49/52 | 49/58 | 51/51; 51/58 |
| Universal aliases | 9/9 | 8/9 | 51/51 | 51/58 | 51/51; 51/58 |
| Gated aliases | 9/9 | 8/9 | 51/51 | 51/58 | 51/51; 51/58 |

Each variant calibrates against the strongest wrong-work score over these nine queries in the ten-candidate pool, plus 0.000001. Thresholds coincide; fresh query outcomes do not influence them. Source-absent false admissions are 0/9, but these same development cases set the thresholds, so that is a calibration diagnostic.

## Fresh result and missing denominator

Capra's correct source uniquely ranks first and is admitted in every variant, with six correct edges, six proposed edges, and six reference edges. Its strength is 0.192769895. Prediction coverage is 52/163; there are no alias forms, so it tests baseline transfer to a new ordinary-Kamri technical passage, not alternate-register transfer.

The selected success count is **one case out of two selected**, with **one scored and one source unavailable**. On the single scored case, edge precision and recall are both 6/6. Alignment recall across the two selected works is unavailable because the Altruist reference is missing; it is not treated as zero reference edges. There are no source-absent false admissions in one evaluated control, with the second control unavailable. A 0/2 error-rate claim would conceal missing evaluation and is not reported.

None of Capra's 20 nonidentity shuffled maxima reaches the observed strength; the highest is 0.124171779. This is a small positive order-control diagnostic, not independent lexical or semantic validation.

## What the gate does and does not establish

The gate activates only on Misinfons, with three distinct markers and 14 occurrences. All ten other selected FL excerpts, including the unavailable Altruist query, contain no alias forms. Universal and gated aliases consequently produce the same predictions and results on this corpus. This experiment cannot establish that gating improves empirical precision or avoids harmful overrides elsewhere. Unit tests verify its specified behavior on controlled marker cases only.

All 48 existing synthetic cases remain explicitly development regressions. No gate activates, and none of the three variants changes any synthetic prediction. They are neither newly fresh evidence nor calibration cases.

## Verification and continuation

One final model execution completed in 53.5 seconds after 39 tests passed. The [verification receipt](000005_verification.json) audits input/raw/code/output hashes, query-only gate decisions, experimental anchor labels, prediction eligibility/offsets, one-to-one token paths, edge support, thresholds, controls, all 33 result rows, missing reference treatment, synthetic regressions, and unchanged experiments 1–4. The [immutable report](../runs/000005_kamri_scoped_register/report.json) retains the scores and full paths. No post-result tuning or model rerun was performed.

```sh
uv run python scripts/run_register_v5.py --run-id replay_000005
uv run python scripts/verify_register_v5.py
```

The verification command audits the original run. Replays require retained local normalized/raw/synthetic documents and a new run directory. The benchmark also seals the dependency lock and project configuration.

The next useful experiment is a correspondence audit of Misinfons before expanding the alias list: inspect editorial substitutions, reference boundaries, and token correspondences in additional source blocks from the same article. Treat that as within-article development/validation, not an independent alternate-register test. Freeze new span labels and a separate evaluation scope before changing scoring. Obtain additional independent register examples when available; otherwise retain that transfer limitation. Capra's new passage and every input inspected here become development material for subsequent model choices. The unavailable Altruist chapter remains an acquisition gap, not an invitation to replace the selected failure after seeing outcomes.
