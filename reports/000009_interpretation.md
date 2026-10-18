# Experiment 9: order, coverage, and matched negatives

Completed and independently verified on 2026-10-01. **The scorer cannot distinguish sources whose unknown content is renamed while observable structure and function words remain fixed. Coverage penalties also erase useful partial matches.** All eight variants refuse all 384 fresh conditions after pooled calibration. Zero false admissions therefore comes with zero true admissions, not useful general rejection performance. No model or meaning is promoted.

Evidence: [registration](../experiments/kamri_coverage_v9.md), [frozen inputs](../benchmarks/kamri_coverage_v9.json), [manifest](../runs/000009_kamri_coverage_negatives/manifest.json), [machine report](../runs/000009_kamri_coverage_negatives/report.json), [paired contrasts](../runs/000009_kamri_coverage_negatives/comparisons.json), and [verification receipt](000009_verification.json).

## Design and fixed scope

Eight variants cross the original and tolerant v7 backgrounds with token-order agreement off/on and uncovered-query costs off/on. The base search, dictionary eligibility, query-only aliases, decoder, match floor, and three-linked-atom admission minimum are unchanged. Both factors off preserves base scores; both on exactly reproduces experiment 8's multiplier.

Calibration uses seeds 9401–9432; fresh evaluation uses seeds 9501–9532. Each panel contains **384 paired conditions from 32 independently seeded worlds**. Each world has twelve conditions: normal or zero lexical anchors, full or half source availability, and three separate negative families. Query duplicates within a world are intentional; none cross calibration and fresh panels. Candidate position is randomized once per world and shared across conditions.

Normal queries emit twelve frozen the/and predictions over six statements. Zero-anchor queries replace those forms with unseen forms while preserving lengths, English sources, repetition patterns and occurrence identities. Half availability retains only the first three source statements while the query retains six. References include only available source occurrences; missing query identities are saved separately. Thus partial-reference recall does not count unavailable material as an alignment failure.

Each four-candidate pool has the correct source plus three negatives:

- **Rotation:** rotate every statement's tokens by one, two or three positions.
- **Renamed:** bijectively rename unknown content with three disjoint vocabularies, preserving function words, positions, repetition, token counts and punctuation.
- **Content order:** rotate only the content subsequence, leaving function words in their original positions and retaining each statement's word bag.

All pools passed the duplicate-text check without replacing seeds. Generated identities, answers and negative labels never enter scoring. Twelve inspected real queries remain development diagnostics: ten calibrate real thresholds and two additional Misinfons blocks are excluded. There are zero fresh real works and zero new supported lexical entries. The unavailable Altruist archive and historical denominator remain unchanged.

One final execution produced 6,240 rows in approximately 85 seconds. Calibration scores and thresholds were sealed before fresh/audit execution. No tuning, condition removal or outcome-dependent rerun occurred.

## Separating order and coverage

For selected blocks, let D be the inherited full token-DP objective, Uc the covered-query upper bound, Ut the full-query upper bound, and N the number of uncovered query tokens. Predicted tokens contribute 2 to bounds; unknowns contribute 0.5. The objective retains exact agreement +2, mismatch −2, unknown positional agreement up to +0.5 and gap −0.75.

| Factors | Quality before clipping |
|---|---|
| Neither | 1 |
| Order only | D / Uc |
| Coverage only | (Uc − 0.75N) / Ut |
| Both | (D − 0.75N) / Ut |

Quality is clipped to [0,1]; zero denominators give zero for active factors. Neither remains 1 even for empty paths, preserving the baseline exactly. Strength equals base strength times quality, before ranking. No factor changes the selected blocks or decoded links. Clipping and denominators allow interactions; these effects are not an additive decomposition. Unselected source prose remains uncharged.

## Fresh discrimination and refusal

All counts below have denominator 384. A maximum-score set includes candidates within 1e-9 of the highest score. Unique retrieval requires a positive margin; merely picking a candidate first by ID during a tie is not success.

| Background | Factors | Unique correct | Correct in maximum set | Top ties | All-zero ties | Correct admissions | Absent false admissions |
|---|---|---:|---:|---:|---:|---:|---:|
| Original | Neither | 256 | 384 | 128 | 0 | 0 | 0 |
| Original | Coverage only | 177 | 383 | 206 | 117 | 0 | 0 |
| Original | Order only | 256 | 384 | 128 | 0 | 0 | 0 |
| Original | Both | 178 | 384 | 206 | 117 | 0 | 0 |
| Tolerant | Neither | 256 | 384 | 128 | 0 | 0 | 0 |
| Tolerant | Coverage only | 177 | 383 | 206 | 117 | 0 | 0 |
| Tolerant | Order only | 256 | 384 | 128 | 0 | 0 | 0 |
| Tolerant | Both | 178 | 384 | 206 | 117 | 0 | 0 |

Wrong-source admissions with the source present are also zero in every variant. Every world has zero absent false admissions, but no true case is admitted either. The pooled synthetic threshold is **0.265001** for every original variant and **0.205001** for every tolerant variant. Renamed negatives attain the perfect-match ceiling during calibration; the maximum-wrong-score-plus-1e-6 rule puts thresholds above that ceiling. These unchanged criteria refuse every fresh true source, including uniquely retrieved cases.

The 128 renamed conditions produce no unique correct retrieval under any variant. The correct source remains in the maximum set in all 128. Without coverage penalties, rotation and content-order each achieve 128/128 unique retrieval; with coverage, those totals fall to 88 and 89 respectively, or 89 and 89 when order is also enabled. Strong structural repetition patterns can discriminate these rotations even with zero anchors; that is not evidence of recognizing their content.

The following twelve strata each contain 32 worlds. Unique-retrieval counts are identical across backgrounds; all stratum admissions and absent false admissions are zero.

| Anchors | Availability | Family | Neither | Coverage only | Order only | Both |
|---|---|---|---:|---:|---:|---:|
| Normal | Full | Rotation | 32 | 32 | 32 | 32 |
| Normal | Full | Renamed | 0 | 0 | 0 | 0 |
| Normal | Full | Content order | 32 | 32 | 32 | 32 |
| Normal | Half | Rotation | 32 | 24 | 32 | 25 |
| Normal | Half | Renamed | 0 | 0 | 0 | 0 |
| Normal | Half | Content order | 32 | 25 | 32 | 25 |
| Zero | Full | Rotation | 32 | 32 | 32 | 32 |
| Zero | Full | Renamed | 0 | 0 | 0 | 0 |
| Zero | Full | Content order | 32 | 32 | 32 | 32 |
| Zero | Half | Rotation | 32 | 0 | 32 | 0 |
| Zero | Half | Renamed | 0 | 0 | 0 | 0 |
| Zero | Half | Content order | 32 | 0 | 32 | 0 |

Coverage creates 117 all-zero ties: all 96 zero-anchor half-source conditions plus 21 normal-anchor half-source conditions in seven worlds (9501, 9502, 9503, 9512, 9514, 9529, 9532). The lost uniqueness is therefore concentrated in true partial sources. Coverage alone also moves the correct source out of the maximum set in one nonzero rotation case per background, at seeds 9513 and 9520 respectively. Order restores that one case in each background, but cannot recover the zeroed cases.

Across matched contrasts, adding order without coverage changes no unique-retrieval count. Adding coverage loses 79 unique successes without order and 78 with order, per background. All admission contrasts remain zero under the pooled thresholds. These are paired descriptive differences from 32 worlds, not independent-case statistical estimates.

## Alignment recovery and ambiguity

Conditional on the correct source, **every variant recovers 1,728/1,728 available edges and 17,280/17,280 available token identities**, with no extra links. All conditional paths are unchanged across factor settings. This engineered correspondence success does not establish lexical meaning or natural translation accuracy.

Retrieved-source metrics include refused cases and use the saved nominal top candidate, even in ties. Neither and order-only recover 1,206/1,728 edges and 12,088/17,280 identities in both backgrounds. Coverage-only recovers 987 edges and 9,912 identities; both recovers 990 edges and 9,940 identities. Proposed counts differ slightly between backgrounds under coverage; full precision denominators are preserved in the machine report. These nominal-top counts depend partly on randomized candidate position in ambiguous pools and must be read alongside the tie counts, not as successful unique retrieval.

Renaming unknown content preserves the features this method observes, including known function-word positions and the unknown-token objective. Unknown positional credit can be perfect for unrelated equal-length material. The experiment exposes this equivalence directly; additional order or coverage penalties cannot supply missing content evidence.

## Real development: what caused the Misinfons admission

Both-off and both-on real scores and admission decisions exactly reproduce experiment 8. Across ten real development queries, correct admissions are 9/10 for each variant except tolerant/both, which admits 10/10. All real source-absent controls are refused. These queries also select thresholds, so these are development observations, not fresh error estimates.

The tolerant Misinfons opening has full selected coverage, so turning coverage on does **not** change its own order-based strength:

| Tolerant factors | Opening strength | Real threshold | Admitted |
|---|---:|---:|---|
| Neither | 0.03336124 | 0.06438033 | No |
| Coverage only | 0.03336124 | 0.04736442 | No |
| Order only | 0.02181448 | 0.02603730 | No |
| Both | 0.02181448 | 0.01619728 | Yes |

Thus coverage enables this admission **through its effect on wrong-work calibration scores**, not through better opening alignment or increased opening strength. Its path remains 9/9 reviewed edges plus one extra. Under the original background, coverage alone zeroes the opening's partial path; order alone preserves its unique ranking but leaves it refused. The earlier zero tie cannot be attributed to token order alone.

For the two additional blocks, the tolerant mechanism passage is admitted with neither, order only, and both, but refused with coverage only; all retain 3/5 correct edges and one extra. Original/order-only preserves the mechanism's unique correct ranking, while both factors produce the v8 zero tie. It remains refused under every original variant, including because only two FL atoms have decoded links. The continuation retains 2/2 edges but cannot meet the three-atom minimum under any variant. These remain single-work structural diagnostics, not independent register transfer.

## Verification and next step

All **67 tests passed** before execution. The separate auditor checked input/raw/code/output hashes; regenerated all registered packets; verified available and unavailable identity spans, anchor density and frozen predictions; independently computed full-matrix objectives and factor formulas; and audited all 6,240 rows, ties, paths, metrics, decisions and calibration sealing. It also checked all 33,120 actual shuffled candidate qualities, 408 summaries and 3,072 matched contrasts. Ten shared nonidentity atom permutations per fresh/real query recompute base search and factors; their exceedances remain descriptive. Experiments 1–8 are unchanged.

No new dictionary entries or scoring model are promoted. This panel is one artificial schema with three deliberately chosen negative families; it does not estimate archive-wide reliability. Real references remain single-analyst structural judgments. Universal refusal and perfect conditional synthetic paths do not validate decipherment.

The next experiment should test **whether frozen content-word candidates can break the renamed-content equivalence**, with an explicit distinction between lexical agreement and positional unknown credit. The frozen eligible dictionary already includes provisional candidates for world, lord and made; a fresh constructed capacity test can use these unchanged candidates at preregistered densities without inducing or promoting new meanings. It should include a zero-content-anchor condition, matched renamed negatives, useful-admission counts, and partial-source controls, and avoid treating positional agreement as content support. Any natural semantic claim still needs independent source-group evidence and a fresh auditable work. This v9 panel is now development data and must not be reused for fresh tuning claims.
