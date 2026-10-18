# Experiment 21: broader development evidence is available

The preregistered evidence-breadth decision passes. The audit identifies **eight eligible units outside the prior calibration panel across three additional connected source groups**. The frozen future development panel contains **19 units, five connected groups and 476 token pairs**, compared with the prior eleven units, two groups and 284 pairs. No orthographic matching or target scoring executed in this experiment.

All 33 Kamri v15 rows marked `both_with_authoritative_english` were nominated using provenance alone. Target 03:007 was explicitly excluded. Names, matching success, token lengths and boundary outcomes did not influence selection. Every nominee remains in the ledger; 18 qualify for the conservative equal-length development packet and 15 remain ineligible. The separate eleven-unit comparator requalifies all eleven previous packets. Ten eligible nominees overlap that panel by UID; 03:005 is present only in the comparator. Deduplication therefore yields 19 future units, rather than counting the two routes as separate examples.

| Conservative connected source group | Nominees | Eligible nominees | Future-panel units | Future-panel token pairs |
|---|---:|---:|---:|---:|
| Nichiren images | 5 | 5 | 6 | 143 |
| Dark side of light | 5 | 5 | 5 | 141 |
| Western esoterism | 7 | 1 | 1 | 7 |
| Risk mathematics / war accountability | 4 | 3 | 3 | 80 |
| Capra foreword / Weber holomovement | 6 | 4 | 4 | 105 |
| Models of magic / related declared works | 6 | 0 | 0 | 0 |
| Total | 33 | 18 | 19 | 476 |

Composite group assignments remain joined. These are three additional groups relative to the earlier calibration panel; all were already exposed elsewhere in the project. They do not create untouched source-group holdouts or newly acquired FL captures.

The eight eligible additions are 04:005, 08:001–003 and 10:001–004. All were admitted by the frozen statement/provenance/count/order rules, without checking whether they contain copied names. The unchanged orthographic rule may still fail its own breadth or control requirements when retested. Packet availability does not predict that outcome.

Every token-sequence occurrence was reconstructed in the original normalized document, with Unicode offsets, full sentence atoms and actual source text. Ordered-word-view offsets from v15 were not treated as document coordinates. Eligibility requires a unique source occurrence, complete statement groups in all FL supports, verified artifact provenance, original article/component scope, compatible duplicate support, equal project counts and no observed order conflict. Publisher extraction review and selected PDF QA are inherited from their saved receipts; no new visual or independent semantic review was performed.

Twenty-nine nominees pass all requirements except the equal-length restriction. Twelve nominees have unequal project counts, one has a source boundary failure and three have an FL boundary failure; these counts overlap, producing fifteen ineligible units. Specifically:

- Eleven complete, otherwise qualifying pairs fail only the equal-length requirement: 04:001–004, 04:007, 08:004, 10:005, 12:003, 12:004, 12:011 and 12:013. They remain possible structural-alignment review leads. Their length mismatch does not prove incorrect correspondence or mistranslation.
- 04:006 fails both the source complete-statement-group requirement and equal token counts. The frozen sentence parser splits at `i.e.` and creates a lowercase continuation atom beginning “life”. This is a conservative parser limitation, not evidence that the actual publisher sentence is truncated. The exclusion remains under the registered rule; parsing was not repaired after seeing the outcome.
- 10:006, 12:009 and 12:014 fail the FL complete-group rule. Saved colon-ended/truncated material is preserved rather than repaired or accepted through alternate punctuation rules.

There are 35 FL support views for the 33 nominees. Two Models of Magic units have identical support in two indexed document selections. Both views and their provenance are archived, but they represent one unit each and add no independent examples. All inputs remain historical/indexed on the FL side. Current raw FL admissions are zero.

The audit retains 130 observable order checks among nominee routes and 50 in the separate comparator; none shows inversion or overlap. Different documents/clips can be incomparable, and these observations do not establish continuity across skipped or missing statements. Future packet selection fails closed if any frozen route for a UID is ineligible, preventing a successful route from silently replacing a failed route. Each outcome remains separately visible.

The registered decision required at least six new eligible UIDs, two additional connected groups and three total groups. The observed values are eight, three and five, respectively. This is an evidence-availability decision, not a statistical success, semantic accuracy estimate or source-identity claim. The v20 calibration failure, v19 fourteen primary ties and two secondary hypotheses, and original v18 unequal-length gate remain unchanged.

165 tests pass. The independent verifier reconstructs the provenance-only nomination and comparator inputs, snapshot artifact hashes and prior QA binding, sentence boundaries, exhaustive token windows, complete groups and every token offset. It independently rebuilds duplicate-support handling, route gates, observable ordering, panel deduplication and the registered breadth decision. It verifies all input/code/output hashes, experiments 1–20 and the v20 deliverable seal. Reverification preserves an existing successful receipt rather than rewriting its timestamp and invalidating later seals. No lexical model, shared lexicon, translation model, orthographic rule or target comparison ran. Semantic-training, untouched-test and current-raw-FL admissions remain zero.

The next bounded step is a separately registered retest of the unchanged v20 orthographic rules, controls and breadth minima on exactly this frozen 19-unit development panel, keeping 03:007 out of calibration and preserving every outcome. Report support by connected group alongside units/keys so a passing aggregate cannot conceal dependence on one source. The larger project milestone remains frozen predictions on an untouched source group with realistic wrong-source and source-absent controls; that needs new evidence and independent review. The present audit supports development-panel expansion only.

Artifacts: [registration](../experiments/kamri_calibration_evidence_v21.md), [frozen nominees/comparator/documents](../data/v21/frozen_inputs.json), [immutable manifest](../runs/000021_kamri_calibration_evidence/manifest.json), [all 33 nominee outcomes](../runs/000021_kamri_calibration_evidence/nominee_ledger.json), [eleven comparator outcomes](../runs/000021_kamri_calibration_evidence/comparator_ledger.json), [frozen future panel and decision](../runs/000021_kamri_calibration_evidence/future_panel.json), [machine report](../runs/000021_kamri_calibration_evidence/report.json), and [independent verification](000021_verification.json).

Reproduce verification with `.venv/bin/python scripts/verify_calibration_evidence_v21.py` and the suite with `.venv/bin/python -m unittest discover -s tests -q`. Preparation guards every output path before writing; execution refuses its existing run directory. Changed parsing, rules, thresholds, panel selection or acquisition require a new registration and directory.
