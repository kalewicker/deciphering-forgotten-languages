# Experiment 20: orthographic calibration is too narrow to resolve the gap

The registered primary calibration gate fails. The folded-spelling rule finds two copied-form proposals in two units, with two distinct keys. The preregistered minimum was three proposals across three units and three keys. Its mechanical preference on target 03:007 therefore remains descriptive: **no gap lead is eligible, and both original hypotheses remain**.

The fixed calibration panel contains eleven previously exposed, complete equal-length pairs: eight v16 units plus 03:005, 03:006 and 13:005 from v18. All 284 FL and 284 source tokens remain in the panel, including nine units with zero proposals. The target is excluded. The primary rule requires a capitalized, noninitial token, at least four folded ASCII letters, equal NFD-casefold keys after removing Unicode mark categories, and reciprocal uniqueness across every token in both statements. Original forms and offsets are preserved. The exact NFC-casefold baseline uses the same candidate eligibility and uniqueness restrictions.

| Calibration observation | Folded primary | Exact baseline, descriptive |
|---|---:|---:|
| Complete paired units | 11 | 11 |
| FL/source tokens | 284 / 284 | 284 / 284 |
| Eligible FL/source candidate tokens | 5 / 8 | 5 / 8 |
| Proposals | 2 | 1 |
| FL tokens without a proposal | 282 | 283 |
| Supporting units / distinct keys | 2 / 2 | 1 / 1 |
| Diacritic-dependent proposals | 1 | 0 |
| Positional conflicts | 0 | 0 |

The primary proposals are Shakra ↔ Shakra in 03:004 and Brahma ↔ Brahmā in 03:005. Both lie at their existing development positional-hypothesis indices. Only the Brahma proposal depends on removing diacritics. The exact baseline retains Shakra alone. Baseline gate fields are calculated under the same primary requirements for transparency; an exact-equality baseline cannot supply diacritic-dependent support. It is never substituted for the primary rule.

All positive support comes from the Nichiren component. The other component contributes five zero-proposal units. This is scarce, exposed development evidence; the absence of positional conflicts in two proposals is not an estimate of lexical or name-recognition accuracy. The breadth minimum is an engineering eligibility requirement, not a statistical guarantee. The target relationship and these calibration texts were previously inspected; registration did not create a blinded design.

| Control family, full denominator per rule | Folded primary proposals | Exact baseline proposals |
|---|---:|---:|
| Cyclic wrong-name substitution, 11 views | 0 | 0 |
| Other-component English statements, 60 comparisons | 0 | 0 |
| Copied-name-preserving frame lures, 11 views | 2 | 1 |

Wrong-name views replace every eligible English name candidate with the next distinct folded key from the fixed calibration pool. Replacement surfaces and their origins are saved separately from original source identities and spans. Real source-absent comparisons enumerate every opposite-component statement for each FL unit; no favorable comparison is selected. Their zero proposals are bounded rejection observations on this small panel, which contains few eligible candidate tokens.

The harder synthetic lures retain eligible capitalized English tokens at their original positions while replacing every other comparison surface with `xqframe`. Both primary copied-form proposals survive. This demonstrates that copied names can remain when the correct full sentence is absent. These lures are not positive calibration examples, and their survival is explicitly a limit on source specificity. The rule is an anchor-proposal mechanism, not a source-identity classifier; zero source-identity claims are admitted. This limitation is separate from the conditional token-anchor calibration gate, which already fails for insufficient breadth.

The rules, calibration outcomes, all controls and failed gate were sealed before the target comparison. The comparison retains exactly the two fixed v19 secondary/intersection hypotheses:

| Hypothesis | Unpaired English token | Primary orthographic matches | Exact baseline matches |
|---|---|---:|---:|
| gap 1 | an | 1 | 0 |
| gap 2 | Āgama | 0 | 0 |

The folded rule mechanically proposes Agama ↔ Āgama; this pair appears in gap 1. The exact baseline proposes no target anchor and ties both hypotheses. Because primary calibration fails, the target's conditional comparison is unavailable and `primary_gap_lead` is null. The mechanical preference cannot repair the failed calibration, overwrite the original fourteen primary v19 maximizers, or resolve its two secondary hypotheses. No candidate dictionary or old positional label was changed. The original v18 equal-token-count failure also remains intact.

156 tests pass. The independent verifier reconstructs the full eleven-unit selection, original complete statements, all 568 calibration token spans, Unicode keys, eligibility, reciprocal multiplicities, every proposal and abstention, all control views and the failed gate. It verifies the calibration-before-target seal, replays both hypotheses, and confirms input/code/output hashes plus preservation of experiments 1–19 and the experiment 19 deliverable seal. The new deterministic orthographic rule executed; no fitted model, randomization, p-value, translation model or shared lexicon was used. Current raw FL, semantic training labels and untouched-test admissions remain zero.

The next step is a separately preregistered calibration-evidence audit of the v15 publisher-backed paired leads. Freeze nominees by provenance and completeness before running any orthographic matching, keep 03:007 out of calibration, and retain every missing or ineligible pair. Establish whether a broader independently corroborated statement panel is actually available before retesting the unchanged rule, controls and breadth minima. Do not nominate a convenient third name after this failure or relax the threshold. Previously exposed components remain development evidence; fresh held-out validation requires unexposed components.

Artifacts: [registration](../experiments/kamri_orthographic_v20.md), [frozen eleven-unit panel](../data/v20/frozen_panel.json), [unchanged target hypotheses](../data/v20/frozen_target.json), [immutable manifest](../runs/000020_kamri_orthographic_anchors/manifest.json), [full calibration and control ledgers](../runs/000020_kamri_orthographic_anchors/calibration.json), [calibration seal](../runs/000020_kamri_orthographic_anchors/calibration_seal.json), [two-hypothesis comparison](../runs/000020_kamri_orthographic_anchors/target_comparison.json), [machine report](../runs/000020_kamri_orthographic_anchors/report.json), and [independent verification](000020_verification.json).

Reproduce verification with `.venv/bin/python scripts/verify_orthographic_v20.py` and the suite with `.venv/bin/python -m unittest discover -s tests -q`. Preparation guards all output paths before writing; execution refuses its existing run directory. Use the verifier for replay. Changed rules, panels, thresholds or evidence require a new registration and directory.
