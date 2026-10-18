# Experiment 22: broader text coverage does not broaden copied-form support

The unchanged primary calibration gate still fails. The retest finds the same two proposals—Shakra ↔ Shakra and Brahma ↔ Brahmā—in the same two Nichiren units, with two distinct keys. The minimum remains three proposals across three units and keys. **No target gap qualifies as a conditional development lead; both original hypotheses remain unresolved.**

This completes the planned retest on all nineteen packets selected by experiment 21, retaining five previously exposed connected groups and all 476 FL/source token pairs. The execution reuses the byte-unchanged v20 scoring module, rule settings, thresholds, target packet and target-comparison procedure. Every unit stays in the denominator, including zero-candidate and zero-proposal units. No name, packet, parsing rule or threshold was changed after scoring.

| Full-panel observation | Folded primary | Exact NFC baseline, descriptive |
|---|---:|---:|
| Units / token pairs | 19 / 476 | 19 / 476 |
| Eligible FL/source candidate tokens | 5 / 9 | 5 / 9 |
| Proposals / supporting units / distinct keys | 2 / 2 / 2 | 1 / 1 / 1 |
| Diacritic-dependent proposals | 1 | 0 |
| Positional conflicts | 0 | 0 |
| FL tokens without a proposal | 474 | 475 |
| Conditional calibration gate | fails | fails |

The primary unmet conditions are minimum proposals, supporting units and distinct keys. All other registered conditions pass. Baseline gate fields use the same primary requirements descriptively; exact equality cannot provide the diacritic-dependent support required of the primary rule, and the baseline never replaces it.

| Connected group | Units | Token pairs | Eligible FL/source candidates | Primary proposals |
|---|---:|---:|---:|---:|
| Nichiren images | 6 | 143 | 5 / 8 | 2 |
| Dark side of light | 5 | 141 | 0 / 0 | 0 |
| Capra foreword / Weber holomovement | 4 | 105 | 0 / 1 | 0 |
| Risk mathematics / war accountability | 3 | 80 | 0 / 0 | 0 |
| Western esoterism | 1 | 7 | 0 / 0 | 0 |

The eight additions contribute 192 token pairs across three additional groups, but **zero eligible FL candidate tokens under the frozen capitalization, position, length and spelling restrictions**. Fourteen of nineteen units have no eligible FL candidate. Experiment 21 established broader complete-statement evidence; this experiment shows that it supplies no additional calibration support for this particular rule. That does not prove copied forms are absent generally or that the new passages lack recoverable correspondence. It limits the present rule's evidence coverage.

All five group-removal summaries retain the original positive requirements. Removing Nichiren leaves zero proposals; removing any other group leaves the same two proposals. No removal satisfies the positive breadth conditions. These are descriptive dependence summaries, with no control re-pooling, recalibration, fresh holdout or alternative acceptance decision. All positive support depends on one already exposed passage.

| Fixed control family, denominator per rule | Folded primary proposals | Exact baseline proposals |
|---|---:|---:|
| Cyclic wrong-name views, 19 | 0 | 0 |
| Cross-connected-group comparisons, 274 | 0 | 0 |
| Copied-name-preserving frame lures, 19 | 2 | 1 |

The cyclic control uses the pool from the entire frozen panel; every replacement's original token and source origin are retained. Cross-group comparisons preserve composite group assignments. Their zero proposals are bounded observations: only 65 comparisons have any eligible FL candidate, and only five have eligible candidates on both sides. The enlarged nominal negative denominator should not be read as extensive name-matching rejection evidence. Name-preserving frame lures still retain both primary proposals, demonstrating that copied names alone do not establish the source sentence or source identity.

Full calibration, controls, group accounting and dependence summaries were sealed before the deterministic target comparison. On 03:007 the folded rule mechanically prefers gap 1: Agama ↔ Āgama aligns when English “an” is left unpaired. It scores one anchor at gap 1 and zero at gap 2. Exact NFC equality proposes no anchor and ties both. The failed primary calibration makes the conditional comparison unavailable; `primary_gap_lead` remains null. The v20 failed gate, v19 fourteen primary maximizers and two secondary alternatives, and v18 length-gate failure remain unchanged.

170 tests pass. The independent verifier reconstructs the exact nineteen-unit panel, original source/FL token spans and group assignments; replays Unicode matching, all-token multiplicity, every positive and all 312 control views/comparisons per rule; and checks all group totals and removal summaries. It verifies the calibration-before-target seal, independently replays both target hypotheses, confirms that the scorer still matches its v20 code hash, and preserves experiments 1–21 plus the v20/v21 deliverable seals. The deterministic orthographic rule executed. No fitted model, p-value, translation accuracy, shared lexicon, new lexical induction, semantic labels, current raw FL or untouched-test admission is claimed.

The registered failure branch now applies: prioritize new independently captured evidence and independent review. The next bounded task should be an acquisition-and-review pilot with whole passages nominated before matching, fixed request limits, immutable capture receipts, and every unavailable passage retained. Reserve genuinely unexposed connected source groups for future frozen predictions and realistic wrong-source/source-absent validation. Raw-capture availability and independent semantic review are separate requirements; neither copied names nor another successful replay can supply them. Further refinements of the Agama gap are paused in the research sequence pending suitable evidence, with no threshold relaxation or favorable subset selection.

Artifacts: [registration](../experiments/kamri_orthographic_retest_v22.md), [frozen nineteen-unit panel](../data/v22/frozen_panel.json), [unchanged target packet](../data/v22/frozen_target.json), [immutable manifest](../runs/000022_kamri_orthographic_retest/manifest.json), [full calibration/control ledgers](../runs/000022_kamri_orthographic_retest/calibration.json), [all group accounting](../runs/000022_kamri_orthographic_retest/group_accounting.json), [all five dependence summaries](../runs/000022_kamri_orthographic_retest/group_removal_support.json), [calibration seal](../runs/000022_kamri_orthographic_retest/calibration_seal.json), [target comparison](../runs/000022_kamri_orthographic_retest/target_comparison.json), and [independent verification](000022_verification.json).

Reproduce verification with `.venv/bin/python scripts/verify_orthographic_retest_v22.py` and the suite with `.venv/bin/python -m unittest discover -s tests -q`. Verification preserves an existing successful receipt; preparation and execution refuse existing output paths. Changed rules, thresholds, panels or acquisition require a new registration and directory.
