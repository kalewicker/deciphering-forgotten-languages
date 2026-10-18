# Experiment 10: frozen content-candidate capacity

Completed and independently verified on 2026-10-01. **Correct content candidates enable narrow useful admissions, but do not remove unknown-content ambiguity.** The content scorers admit 128/192 changed-content cases under the preregistered primary policy, including partial sources. A policy calibrated across all negative families still refuses every fresh case. These are engineering capacity results under predictions that are correct by construction, not validation of the proposed meanings. No model or meaning is promoted.

Evidence: [registration](../experiments/kamri_content_v10.md), [frozen benchmark](../benchmarks/kamri_content_v10.json), [manifest](../runs/000010_kamri_content_capacity/manifest.json), [machine report](../runs/000010_kamri_content_capacity/report.json), [threshold tables](../runs/000010_kamri_content_capacity/thresholds.json), [matched contrasts](../runs/000010_kamri_content_capacity/comparisons.json), and [verification receipt](000010_verification.json).

## What was frozen

The roster uses unchanged v1 positional candidates:

| Form | Provisional candidate | Observations for candidate | Supporting source groups |
|---|---|---:|---|
| warċa | world | 2 | Christisis, Nichiren Images |
| mirnaķ | lord | 2 | Golden Age, Nichiren Images |
| misndin | made | 2 | Christisis, Golden Age |

All three satisfy the existing emission criteria, with candidate fraction 1.0. That fraction is not a calibrated probability. Their support is positional, and this experiment adds no natural evidence for their meanings. Synthetic text deliberately assigns these forms their frozen candidate words so that the experiment can test scoring capacity if those predictions are correct.

Calibration uses seeds 10401–10432 and fresh evaluation 10501–10532: **32 independently seeded worlds in each panel**. Each has eighteen paired conditions, crossing content density 0/1/3 per statement, full/half source availability, and three negative families. Each panel therefore has 576 conditions, not 576 independent texts. Candidate position is randomized once per world and shared across conditions. Intentional query duplicates stay within worlds and never cross calibration/fresh splits.

Each six-statement query retains the/and forms. Three fixed nonfunction probe positions per statement contain distinct unknown words, with the first zero, one or three replaced by cyclic roster words at the corresponding density. Full sources retain six statements; half sources retain only the first three while the query remains six. References include only available source occurrences, and unavailable query identities are separately saved.

The four-candidate pools contain a correct source plus three negatives:

- **Content renamed:** rename all nonfunction words, including any roster words, preserving token counts and repetition patterns.
- **Unknown renamed:** rename only unknown material, preserving all roster evidence and its positions.
- **Probe order:** rotate or reverse the three probe values, preserving word bags and function positions.

Answers, reference identities, keys, condition labels and negative roles do not enter scoring. Twelve previously inspected real queries remain development material; ten calibrate real thresholds, and two additional Misinfons blocks do not. There are zero fresh real works and zero new supported lexical entries. The unavailable Altruist archive and historical denominator remain unchanged.

One final execution produced 9,312 result rows in approximately 104 seconds. Both calibration tables and calibration scores were sealed before fresh/audit evaluation. No seeds, cases, thresholds or scoring choices were changed after outcomes.

## Scoring and admission policies

Eight variants cross the original and tolerant backgrounds with four modes. Each background selects the same blocks and uses the unchanged decoder in all modes:

| Mode | Multiplier before ranking |
|---|---|
| Base | 1, preserving background strength |
| Positional | V9 covered-span token-DP agreement, including unknown positional credit |
| Content bag | Blockwise multiset roster matches / covered roster predictions |
| Content order | Blockwise roster longest-common-subsequence matches / covered roster predictions |

Content modes give unknown tokens and function-word predictions no content credit. No covered roster prediction means quality zero. Matches cannot cross selected block boundaries. Extra source roster words are uncharged; the multiplier is an agreement-recall fraction, not a semantic accuracy or confidence estimate. None of these modes charges uncovered query material or repairs the base path.

Two policies were registered before execution. **Primary** calibrates synthetic thresholds only on the 192 content-renamed calibration conditions; its fresh capacity claim is restricted to the matching 192 conditions. Behavior on other families is an out-of-scope stress diagnostic. **Pooled** calibrates on all 576 conditions and evaluates all 576 fresh conditions. Both use maximum wrong-candidate strength plus 1e-6, require margin >1e-9 and at least three linked FL atoms, and are retained without choosing a winner. Their real thresholds use the same ten development queries.

## Primary changed-content result

The following counts apply identically to both backgrounds. All counts have denominator 192.

| Mode | Unique correct retrieval | Correct primary admissions | Wrong admissions | Source-absent false admissions | Pooled correct admissions on these cases |
|---|---:|---:|---:|---:|---:|
| Base | 128 | 0 | 0 | 0 | 0 |
| Positional | 128 | 0 | 0 | 0 | 0 |
| Content bag | 128 | **128** | 0 | 0 | 0 |
| Content order | 128 | **128** | 0 | 0 | 0 |

Every density-one and density-three primary case uniquely retrieves correctly in every mode: 32/32 at each density and source extent, totaling **128/128 cases with content evidence**. Both content scorers admit all of them under the primary policy, including all 64 half-source cases. The 64 density-zero conditions remain ambiguous and refused. This is 128/192 on the full selected primary denominator, not an unqualified 100% success claim.

**The new multiplier does not improve primary unique retrieval over the base.** Supplying correct content predictions already makes base lexical scoring rank those sources uniquely. The content modes instead change the score distribution and calibration: renamed negatives get zero content quality, so their primary threshold is 0.000001. Density-zero controls also get zero quality and cannot pass the margin rule. Base and positional calibration retain strong ambiguous negatives at density zero, producing thresholds 0.265001 for the original background and 0.205001 for the tolerant background; they refuse the uniquely ranked positive cases too.

Source-absent errors are zero for every mode, but the content-renamed negatives contain no roster words and therefore all get zero content scores. This is a deliberately narrow rejection control, not a demonstrated error rate against arbitrary sources. All 32 worlds have zero observed absent errors.

## Stress controls and all fresh conditions

On all 576 fresh conditions, the counts below again apply to both backgrounds. Primary-policy admissions outside content-renamed are explicitly stress behavior; they are not covered by the primary calibration claim.

| Mode | Unique correct | Top-score ties | All-zero ties | Correct admissions using primary policy | Correct admissions using pooled policy |
|---|---:|---:|---:|---:|---:|
| Base | 128 | 448 | 0 | 0 | 0 |
| Positional | 256 | 320 | 0 | 0 | 0 |
| Content bag | 128 | 448 | 192 | 128 | 0 |
| Content order | 192 | 384 | 192 | 192 | 0 |

The correct source belongs to the maximum-score set in 576/576 for every variant. Wrong admissions and source-absent false admissions are zero under both policies throughout. These counts do not turn tied rankings into successes.

Unknown-renamed produces **zero unique successes in all 192 cases under every mode**, even at density three. It preserves every word and structural feature the method uses to identify content. Adding known words cannot distinguish differences confined to unknown material.

Probe-order isolates a different limit. Content bag cannot distinguish any of its 192 cases. Content order uniquely retrieves and, under the primary policy, admits the 64 density-three cases: it sees changes in the relative order of three known words. At density one it still ties, because filtering to one known word discards that word's location among unknowns. Positional scoring retrieves the 128 density-one/three probe cases uniquely, but admits none under its primary threshold. Content-only scoring therefore does not dominate positional retrieval.

Each row below contains 32 worlds. Entries are **unique correct / correct admissions using the primary policy**. Outcomes are identical across backgrounds. All source-absent errors are zero, and all pooled-policy admissions are zero in every stratum.

| Density | Source | Family | Base | Positional | Content bag | Content order |
|---:|---|---|---|---|---|---|
| 0 | Full | Content renamed | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 0 | Full | Unknown renamed | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 0 | Full | Probe order | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 0 | Half | Content renamed | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 0 | Half | Unknown renamed | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 0 | Half | Probe order | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 1 | Full | Content renamed | 32 / 0 | 32 / 0 | 32 / 32 | 32 / 32 |
| 1 | Full | Unknown renamed | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 1 | Full | Probe order | 0 / 0 | 32 / 0 | 0 / 0 | 0 / 0 |
| 1 | Half | Content renamed | 32 / 0 | 32 / 0 | 32 / 32 | 32 / 32 |
| 1 | Half | Unknown renamed | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 1 | Half | Probe order | 0 / 0 | 32 / 0 | 0 / 0 | 0 / 0 |
| 3 | Full | Content renamed | 32 / 0 | 32 / 0 | 32 / 32 | 32 / 32 |
| 3 | Full | Unknown renamed | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 3 | Full | Probe order | 0 / 0 | 32 / 0 | 0 / 0 | 32 / 32 |
| 3 | Half | Content renamed | 32 / 0 | 32 / 0 | 32 / 32 | 32 / 32 |
| 3 | Half | Unknown renamed | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 3 | Half | Probe order | 0 / 0 | 32 / 0 | 0 / 0 | 32 / 32 |

Pooled thresholds are 0.265001 for every original mode and 0.205001 for every tolerant mode. Unknown-renamed calibration controls attain the same ceiling as true sources, including for content modes. The max-wrong-plus-1e-6 rule therefore refuses **all 576 fresh cases**. This policy's zero false admissions again accompanies zero useful admissions. Both policy results were preregistered and retained; the narrow policy cannot substitute for general rejection calibration.

## Correspondence recovery and real development

Conditional on the correct source, every variant recovers **2,592/2,592 available synthetic edges and 26,154/26,154 available token identities**, with no extra links. Candidate paths are unchanged across modes. Ranking metrics include refusals and nominal top candidates in ties; such tie-broken correspondence counts depend partly on randomized candidate position and are not unique retrieval evidence. Full precision/recall counts for both backgrounds remain in the machine report.

The real base and positional strengths and admission decisions exactly reproduce v9. They uniquely retrieve all ten calibration/development queries and admit nine. Content bag/order uniquely retrieve and admit five of ten under either background; the other five become zero-score ties because they contain no emitted roster candidates. The five with content candidates are Golden Age, Nichiren Images, Gad the Seer, Christisis, and the Manichaean hymn. Both extra Misinfons blocks likewise lack roster predictions and become zero ties; the opening also lacks them and is refused. Sparse roster coverage therefore imposes a substantial development recall cost.

The content modes retrieve 37/64 reviewed real development edges; proposed edges are 45 for the original background and 48 for the tolerant one. This decline reflects discarded queries and nominal zero ties, not altered conditional paths. No real source-absent control is admitted. These queries share data with threshold selection and remain single-analyst structural development evidence, not fresh natural-language validation.

## Verification and next experiment

All **77 tests passed** before execution. The separate auditor checked all input/raw/code/output hashes; regenerated all registered panels; verified frozen eligibility, predictions, roster density and available/unavailable identities; independently computed full-matrix positional and content-sequence objectives and checked token evidence spans; and audited all 9,312 rankings, ties, paths, metrics and both admission policies. It checked actual shuffled evidence and maxima, all 480 summaries and 4,608 matched contrasts, and exact real base/positional compatibility with v9. Ten shared nonidentity query-atom permutations per fresh/real query recompute base search and candidate evidence; exceedances remain descriptive, not p-values. Experiments 1–9 remain unchanged.

No new supported meanings, general rejection reliability, natural register transfer or promoted model follows from these results. The primary improvement is conditional capacity when the roster is correct and the candidates differ on those known words. The constructed schema and 32 paired worlds limit generalization; universal refusal under the pooled policy remains an explicit failure of useful admission.

The next experiment should test **incorrect or conflicting content anchors and misleading distractors**. Preregister fixed anchor-conflict and omission levels on new calibration/fresh worlds, retaining occurrence references through corruptions, plus competing sources that preserve some roster evidence while changing other content. Compare useful admissions and wrong/source-absent admissions, keep partial-source and zero-content controls, and report both calibration scopes. This would test the assumption this experiment grants—that emitted content candidates are correct—before any natural semantic claim. V10 is now development data; natural validation still requires independent evidence from a fresh auditable source work.
