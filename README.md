# FL-Decipher

An offline, evidence-tracked Forgotten Languages research pilot. The larger architecture is proposed in [PLAN_REVIEW.md](PLAN_REVIEW.md).

**Latest completed step: experiment 44.** This public repository contains code,
protocols, tests and reports. Downloaded documents, review packets and generated
research archives remain local. See [publication scope and verification](PUBLICATION.md)
for what a public clone can reproduce. Run `uv run python scripts/test_public_snapshot.py`
for the tests that do not require the archive.

Current boundary: [experiment 44](reports/000044_interpretation.md) found one
22-token exact English fragment in quote02; the other five unmatched longer
blocks stay below the fixed eight-token cutoff. Experiment 43's whole-block
results remain unchanged. Copying direction, historical provenance and opaque
FL meanings remain unresolved. Experiment 40's date-mechanism finding and
experiment 39's name-only result stay fixed.
Immediate passage relationship and natural-benchmark capacity remain unresolved/
unmet, and synthetic feature expansion is stopped. No natural decipherment claim
has been validated.

The first experiment has run on **five short Kamri excerpts**, covering 30 reviewed sentence correspondences across five nominated source works. Four source groups train a positional lexical baseline; *The Dark Side of Light* is held out. This is an exploratory engineering result, not a validated decipherment.

## First result

See [the immutable run report](runs/000001_kamri_excerpt_baseline/report.md) and [the interpretation](reports/000001_interpretation.md).

- Correct source ranked first for 4/5 excerpts in a fixed five-work collection.
- Held-out passage alignment recovered 5/5 reviewed sentence links.
- The lexical model emitted candidates for 52/141 held-out tokens and abstained on 89/141.
- 49/52 emitted candidates agreed with projected English positions. **This is not independently measured semantic translation accuracy.**
- Tamar ranked second and the aligner recovered 0/7 reviewed links. That failure remains in the denominator.

Most supported predictions are grammatical words. No fluent translation or recovered grammar is claimed.

## Run locally

Requires Python 3.12+ and `uv`.

```sh
uv sync --frozen
uv run python -m unittest discover -s tests -v
uv run fl-decipher run --run-id replay_000001
```

The run is entirely offline once dependencies and data are present. Choose a new run ID each time; existing run directories are never overwritten. Replaying the same frozen inputs is allowed; using these results to tune a model makes the held-out excerpt development data for subsequent experiments.

The benchmark checks normalized-document and acquisition-artifact hashes, configuration identity, source-group separation, and exact duplicate FL sentences across splits. Its protection is limited to declared source groups and exact duplicate sentences; archive-wide near-duplicate detection is not implemented.

## Data and acquisition limits

Direct FL downloads were blocked by the local network filter. The five FL inputs are explicitly labeled indexed web excerpts, selected from the available opening Kamri-only span under a fixed 180-word cap. They are **not raw HTML snapshots or complete articles**. They may reflect older indexed page versions. The raw FL acquisition gap is recorded in `data/acquisition_fl.json`.

The five English works were downloaded as raw HTML or Internet Archive OCR. Raw artifacts, retrieval metadata, normalized views, character spans, and hashes are retained locally in `data/`. OCR for *Christisis* has not been checked against scan images.

The supplied source identities came from a public Kamri report. An analyst reviewed the ordered source passages and marked which training links were compatible with positional projection. This audit supports passage correspondence; it does not independently establish every lexical meaning. Tamar's wording and order differed enough that all its links were excluded from lexical induction.

Acquisition helpers are separate from experiment execution:

```sh
uv run python scripts/acquire_sources.py
uv run python scripts/import_indexed_excerpts.py
```

They reuse existing normalized inputs. For a new experiment, create a new configuration, audit, and benchmark ID rather than replacing frozen inputs. `scripts/freeze_benchmark.py` materializes the initial reviewed correspondence manifest and refuses to overwrite it. A fresh download can change hashes; it cannot silently replace an input to the frozen benchmark.

## Artifacts

Each run contains:

- `manifest.json`: completion state, configuration, code/input hashes, runtime, output hashes, and metrics.
- `report.md` / `report.json`: retrieval rankings, alignment links/gaps, counts, controls, and limitations.
- `lexicon.json`: proposed lexical candidates, counts, independent source-group support, and evidence spans.
- `predictions.json`: held-out candidates, unresolved words, and explicitly provisional positional-reference comparisons.
- `evidence.sqlite`: documents, sentences, reviewed pairs, proposed claims, and supporting token spans.

The aligner receives neither bibliography nor lexical answers. The lexical model learns only from the declared training groups. Emission requires two observations, support from two source groups, and at least 0.8 frequency among nominated candidates. That frequency is not a calibrated probability.

## Second experiment

The [source-edition and alignment experiment](reports/000002_interpretation.md) is complete; see its [immutable run report](runs/000002_kamri_alignment_editions/report.md).

- The unchanged baseline recovered Tamar 7/7 with the Johnson edition, versus 0/7 with the original edition.
- On two fresh source groups, the frozen lexical/structural method ranked 2/2 works first and recovered 6/15 reviewed edges; the baseline ranked 1/2 first and recovered 1/15 through its retrieved sources.
- No fresh source-absent controls were admitted. This is two negative cases, not an estimated error rate.
- Fourteen tests passed; saved inputs, code, outputs, spans, and first-run artifacts were verified.

The new method changes both lexical scoring and the match floor, so this comparison does not isolate the contribution of lexical anchors. All v1 inputs are development data in experiment 2. Future tuning makes the two additional groups development data too. No semantic translation accuracy is claimed.

Run the frozen second experiment offline with a new run ID:

```sh
uv run python scripts/run_alignment_v2.py --run-id replay_000002
```

Its [registration](experiments/kamri_alignment_v2.md) and [benchmark](benchmarks/kamri_alignment_v2.json) preserve source-group identities and many-to-many reference edges. English candidate scopes differ: five original documents remain unchanged, while three newly acquired PDF inputs use declared source packets. Local raw artifacts and normalized data must accompany the project; acquisition is separate from execution.

## Third experiment

The [passage alignment factorial](reports/000003_interpretation.md) is complete and verified. Eight variants separate abbreviation protection, up-to-2:2 effective-unit blocks, and lexical anchors at a common match floor of 0.72.

- The full protected/multi/lexical variant recovered 43/45 development edges but proposed two extra edges.
- All eight variants admitted Risk Mathematics and recovered its 4/4 fresh edges.
- Misinfons remained unadmitted in every variant. The full variant ranked its correct source second; its failure remains in the two-query denominator.
- No fresh source-absent false admissions; 24 tests passed. This remains structural engineering evidence, not validated semantic translation accuracy.

See the [immutable report](runs/000003_kamri_passage_factorial/report.md), [registration](experiments/kamri_passage_v3.md), and [pre-execution input amendment](experiments/kamri_passage_v3a_amendment.md). The initial preparation is preserved; the final run uses the v3a configuration and benchmark.

```sh
uv run python scripts/run_passage_v3.py --run-id replay_000003
uv run python scripts/verify_passage_v3.py --run-id 000003_kamri_passage_factorial
```

## Fourth experiment

The [reward-mass and internal precision experiment](reports/000004_interpretation.md) is complete and verified. It crosses effective-unit/token reward with Cartesian/ordered edges, using 40 fresh controlled synthetic cases, eight synthetic calibration cases, and all nine real works as development diagnostics.

- All four variants uniquely ranked the correct synthetic packet first in 40/40 and correctly admitted 28/40; source-absent false admissions were 0/40.
- Ordered edge precision improved from 88.7% to 92.7% under effective reward, while recall fell from 98.5% to 94.1%.
- Token reward was invariant across four actual boundary changes. With Cartesian expansion, however, it produced 60 synthetic extra edges versus 17 under effective reward.
- Ordered decoding removed Christisis's extra edges. Misinfons still ranked second and was refused. Reordering remains a measured weakness of the provisional token path.
- 31 tests passed; saved artifacts and experiments 1–3 were verified unchanged. Synthetic truth is constructed and does not measure natural-language semantic accuracy.

See the [registration](experiments/kamri_precision_v4.md), [frozen benchmark](benchmarks/kamri_precision_v4.json), and [immutable report](runs/000004_kamri_precision_mass/report.md).

```sh
uv run python scripts/run_precision_v4.py --run-id replay_000004
uv run python scripts/verify_precision_v4a.py
```

The v4a auditor corrects compatibility with experiment 1's document-ID/text hashes; execution-frozen code and outputs remain unchanged. The verification receipt records the correction.

## Fifth experiment

The [scoped lexical alias comparison](reports/000005_interpretation.md) is complete and verified, with one of two selected fresh sources unavailable. Three variants compare original predictions, universal overrides of three externally proposed function forms, and overrides gated by query-only markers.

- Misinfons's correct source moves from third to first in the expanded ten-candidate pool, but its strength and 2/9 conditional links are unchanged. It remains refused.
- Capra's foreword was independently acquired and checked. Every variant admits the new passage and recovers 6/6 reference edges.
- The Altruist chapter remains unavailable; the selected denominator is two, and only one source-absent control is evaluated. Selected-sample alignment recall is unavailable.
- Universal and gated aliases behave identically because only Misinfons contains the alias forms. No independent register transfer or new supported lexical meaning is established.
- 39 tests passed; saved artifacts and experiments 1–4 are unchanged. All 48 synthetic cases are development regressions.

See the [registration](experiments/kamri_register_v5.md), [benchmark](benchmarks/kamri_register_v5.json), and [immutable report](runs/000005_kamri_scoped_register/report.md).

```sh
uv run python scripts/run_register_v5.py --run-id replay_000005
uv run python scripts/verify_register_v5.py
```

## Sixth experiment

The [Misinfons correspondence audit](reports/000006_interpretation.md) is complete and verified. It preserves the v5 scorer and thresholds, audits the opening passage, and tests two fixed additional blocks from the same article.

- Gated aliases improve the continuation from 1/2 to 2/2 reference links; the mechanism passage stays at 2/5. Both blocks rank the correct source first and remain unadmitted.
- Four new equal-length positional agreements support compatibility of the proposed **of/that** forms, while three conflicting opening occurrences remain. All evidence still comes from one source work; zero lexical meanings are promoted.
- Separate reference-guided diagnostics expose token-count, punctuation, lexical-capacity, regularization, and gap constraints. They never enter retrieval or become semantic gold.
- 44 tests passed; saved inputs, outputs, token paths, and experiments 1–5 were verified. The two-statement continuation cannot satisfy the inherited three-statement admission rule.

See the [registration](experiments/kamri_correspondence_v6.md), [benchmark](benchmarks/kamri_correspondence_v6.json), and [immutable report](runs/000006_kamri_correspondence_audit/report.md).

```sh
uv run python scripts/run_correspondence_v6.py --run-id replay_000006
uv run python scripts/verify_correspondence_v6.py
```

## Seventh experiment

The [controlled editorial-robustness factorial](reports/000007_interpretation.md) is complete and verified. Eight scoring variants are tested on 128 fresh conditions from eight independently seeded texts, with 32 calibration conditions from two other texts and twelve real development queries.

- The full combination improves unique synthetic retrieval from 36/128 to 64/128, but still fails every fully edited case and lowers token precision.
- It recovers all nine reviewed opening Misinfons edges with one extra edge; the opening remains below admission threshold. This is development correspondence recovery, not validated decipherment.
- Source-absent errors persist: baseline 5/128 concentrates entirely in five of eight pristine worlds. Neutral punctuation adds errors on punctuation-only cases.
- 52 tests passed; all 1,376 rows, paired contrasts, token identities, calibration sealing, and experiments 1–6 were verified. No scoring variant is promoted and no new meaning is supported.

See the [registration](experiments/kamri_editorial_v7.md), [frozen benchmark](benchmarks/kamri_editorial_v7.json), and [immutable report](runs/000007_kamri_editorial_robustness/report.md).

```sh
uv run python scripts/run_editorial_v7.py --run-id replay_000007
uv run python scripts/verify_editorial_v7.py
```

## Eighth experiment

The [candidate token-order and admission experiment](reports/000008_interpretation.md) is complete and verified. Four variants cross the original and tolerant backgrounds with order scoring off/on, using 192 fresh conditions from 32 independently seeded texts and a separate calibration panel of the same size.

- Enlarged calibration reduces fresh source-absent errors from 8 to 1 (original) and 38 to 0 (tolerant), applying old versus new thresholds to identical order-off paths. Correct admissions stay at 32/192 and 64/192 respectively.
- Order scoring has mixed effects: original errors fall from 1/192 to 0/192, while tolerant errors rise from 0/192 to 2/192, both in one world. Every fully edited condition still fails.
- Tolerant/order-on admits the development Misinfons opening with all nine reviewed links plus one extra. Its path is unchanged; the score and separately calibrated threshold both fall. This establishes no new lexical meaning.
- 59 tests passed; all 1,616 result rows, order objectives, shuffle controls, paired contrasts, and experiments 1–7 were verified. No model is promoted.

See the [registration](experiments/kamri_order_v8.md), [frozen benchmark](benchmarks/kamri_order_v8.json), [immutable report](runs/000008_kamri_order_admission/report.md), and [verification receipt](reports/000008_verification.json).

```sh
uv run python scripts/run_order_v8.py --run-id replay_000008
uv run python scripts/verify_order_v8.py
```

## Ninth experiment

The [order, coverage and matched-negative experiment](reports/000009_interpretation.md) is complete and verified. Eight variants separate token-order agreement from uncovered-query penalties, with 384 fresh conditions from 32 worlds and an equally sized separate calibration panel. Conditions cross anchor density, source availability, and three negative families.

- Renaming unknown content while preserving structure and function words leaves the correct source tied in all 128 cases. Neither order nor coverage resolves this ambiguity.
- Pooled calibration refuses all 384 fresh cases in every variant. Zero false admissions therefore accompanies zero correct admissions.
- Coverage penalties reduce unique retrieval from 256/384 to 177–178/384 and create 117 zero-score ties, all on partial sources. Conditional on the correct source, all available synthetic links remain perfectly recovered.
- The tolerant Misinfons opening is admitted only with both factors. Its strength equals order-only strength; coverage changes the wrong-work calibration threshold, not the opening's alignment.
- 67 tests passed; all 6,240 rows, factor objectives, controls, contrasts, and experiments 1–8 were verified. No meaning or model is promoted.

See the [registration](experiments/kamri_coverage_v9.md), [frozen benchmark](benchmarks/kamri_coverage_v9.json), [immutable report](runs/000009_kamri_coverage_negatives/report.md), and [verification receipt](reports/000009_verification.json).

```sh
uv run python scripts/run_coverage_v9.py --run-id replay_000009
uv run python scripts/verify_coverage_v9.py
```

## Tenth experiment

The [frozen content-candidate capacity experiment](reports/000010_interpretation.md) is complete and verified. Eight variants compare base, positional, content-bag and ordered-content scoring on 576 fresh conditions from 32 worlds, with a separate calibration panel of the same size. The fixed provisional roster is world/lord/made; predictions are correct by construction in the synthetic panel.

- Under the preregistered changed-content calibration policy, content modes correctly admit 128/192 primary cases, including all 64 partial-source cases with content evidence. Base scoring already uniquely retrieves those 128 cases but admits none under its threshold.
- Ordered content also resolves 64 three-word reorder controls. Unknown-renamed material stays tied in all 192 cases, and single-word content order cannot recover position among unknowns.
- Calibration pooled across all negative families still refuses every fresh case. Narrow capacity does not establish generally useful rejection.
- The small content roster discards five of ten real development queries and all Misinfons blocks. No new meaning or model is promoted.
- 77 tests passed; all 9,312 rows, two calibration policies, candidate evidence, controls, contrasts, and experiments 1–9 were verified.

See the [registration](experiments/kamri_content_v10.md), [frozen benchmark](benchmarks/kamri_content_v10.json), [immutable report](runs/000010_kamri_content_capacity/report.md), and [verification receipt](reports/000010_verification.json).

```sh
uv run python scripts/run_content_v10.py --run-id replay_000010
uv run python scripts/verify_content_v10.py
```

## Eleventh experiment

The [incorrect-anchor and prediction-lure experiment](reports/000011_interpretation.md) is complete and verified. Eight unchanged v10 variants are tested on 768 fresh conditions from 32 worlds and a separate equally sized calibration panel. Six query settings include clean, conflicting and omitted anchors, with full/half sources and two fixed negative families.

- Content modes correctly admit 256/384 primary cases against fully renamed negatives. Under those narrow thresholds, bag scoring admits 104/384 misleading wrong sources and ordered scoring 168/384; both fail in every fresh world.
- Ordered scoring also falsely admits a lure in all 64 clean source-absent controls. Identical known content cannot establish a source work's identity or presence.
- Wrong anchors damage conditional token recovery even when given the true source. All-conflict token recall falls to about 70%, with extra cross-occurrence pairs; statement edges stay perfectly recovered.
- Broader calibration refuses every fresh case. Real diagnostics exactly reproduce v10. No meaning or model is promoted.
- 86 tests passed; all 12,384 rows, two calibration policies, retained truth identities, shuffled candidate evidence, mode/corruption contrasts, and experiments 1–10 were verified.

See the [registration](experiments/kamri_conflict_v11.md), [frozen benchmark](benchmarks/kamri_conflict_v11.json), [immutable report](runs/000011_kamri_anchor_conflicts/report.md), and [verification receipt](reports/000011_verification.json).

```sh
uv run python scripts/run_conflict_v11.py --run-id replay_000011
uv run python scripts/verify_conflict_v11.py
```

## Twelfth experiment

The [natural source acquisition/eligibility pilot](reports/000012_interpretation.md) is complete and verified as an acquisition result. It selected exactly two unused source components before fetching the new passages: Liber Azazel and Book of Vile Darkness, with the related D&D books grouped together.

- Both indexed FL openings were saved under the fixed 180-word cap. Neither English source produced an eligible reference packet.
- Azazel remains an unverified indexed preview; its PDF route returned 404. Vile Darkness has a catalogue record, while the linked archive item is dark and exposes no files.
- Both selections remain in the denominator. No model was run; accuracy and false-admission metrics are unavailable, not zero. No meaning or model is promoted.
- 92 tests passed; raw attempts, discovery limits, quarantine, token spans, missing-evidence gates and experiments 1–11 were verified.

See the [registration](experiments/kamri_natural_v12.md), [frozen ledger](benchmarks/inputs/natural_v12_acquisition.json), [immutable acquisition report](runs/000012_kamri_natural_acquisition/report.md), and [verification receipt](reports/000012_verification.json).

```sh
uv run python scripts/verify_natural_v12.py
```

## Thirteenth experiment

The [source-provenance continuation](reports/000013_interpretation.md) is complete and verified as an acquisition outcome. It retained the same two selected works and exact v12 FL openings.

- An archived contemporary publisher excerpt establishes inspectable Book of Vile Darkness work evidence, but covers Juiblex rather than the frozen chapter-one passage. Liber Azazel's authorship and source prose remain unresolved.
- Zero of two pairs is reference eligible. No model executed; accuracy and rejection metrics are unavailable. No meaning or model is promoted.
- Eight discovery queries, eight source/provenance routes and nine raw requests include one disclosed external DNS diagnostic. Failed routes and the wrong-section excerpt remain preserved.
- 98 tests passed; raw receipts, scope/provenance gates, unchanged FL token denominators and experiments 1–12 were verified. The report discloses incomplete serialization of one discovery response.

See the [registration](experiments/kamri_provenance_v13.md), [frozen ledger](benchmarks/inputs/provenance_v13_acquisition.json), [immutable report](runs/000013_kamri_source_provenance/report.md), and [verification receipt](reports/000013_verification.json).

```sh
uv run python scripts/verify_provenance_v13.py
```

## Fourteenth experiment

The [source-first feasibility experiment](reports/000014_interpretation.md) retained the one remaining unexposed Kamri inventory component, Religious Architecture. Its 2013 publisher-hosted opening preview was frozen before acquiring the indexed FL opening.

- 380 English words and 174 FL words were preserved. Concrete correspondence could not be established within the fixed openings; zero of one selected pairs is reference eligible.
- No model executed, scoring metrics remain unavailable, and no meaning or model is promoted. The outcome does not disprove a relationship elsewhere in the post.
- The full inventory audit joins 22 source-work nodes across 24 posts into 14 components. Thirteen were already exposed; this stage covers the remaining provisional component. No further untouched component remains in this inventory.
- 103 tests passed; raw evidence, source-first order, all selected tokens, component boundaries and experiments 1–13 were verified. A failed XML link with an unavailable destination is disclosed.

See the [registration](experiments/kamri_feasibility_v14.md), [component audit](data/v14/component_audit.json), [frozen ledger](benchmarks/inputs/feasibility_v14_acquisition.json), [immutable report](runs/000014_kamri_source_feasibility/report.md), and [verification receipt](reports/000014_verification.json).

```sh
uv run python scripts/verify_feasibility_v14.py
```

## Fifteenth experiment

The [public alignment-package audit](reports/000015_interpretation.md) accounts for all 978 Kamri units across 24 posts and 48 Western units. Its combined edition duplicates the article files; the 459/296-entry lexicons remain quarantined.

- Saved independent evidence corroborates 273 English units, 108 FL units and both texts for 55 units; 33 paired matches have an authoritative English source with reviewed extraction. Zero whole articles are fully corroborated on both sides. These are review leads, not semantic gold.
- Published word counts are not reproduced under reading-edition whitespace counting. Article 7 has two stale uncertainty locators and only aggregate confidence totals. All 48 Western English renderings differ from their Kamri counterparts.
- Five source routes and three raw requests yielded one new publisher-hosted roundup; unavailable and excluded routes are preserved. Fourteen relevant PDF pages were visually reviewed. All fourteen components remain exposed; no new untouched fold or training label is admitted.
- 111 tests passed. Independent byte, row, occurrence, scope and hash checks passed, including preservation of experiments 1–14. A supplemental source-order check finds no inversions in the matched subsets; it does not verify skipped passages.

See the [registration](experiments/kamri_dataset_audit_v15.md), [immutable run](runs/000015_kamri_dataset_audit/report.md), [unit ledger](runs/000015_kamri_dataset_audit/unit_ledger.json), [split readiness](runs/000015_kamri_dataset_audit/split_readiness.json), and [verification receipt](reports/000015_verification.json).

```sh
uv run python scripts/verify_dataset_audit_v15.py
```

## Sixteenth experiment

The [bounded correspondence review](reports/000016_interpretation.md) retains the first four units from each of two exposed publisher-backed passages. It also prepares [separate annotation errata](reports/000016_proposed_errata.md).

- All eight proposed English units match unique complete source statements, in order, alongside exact historical indexed FL statements. Two passages meet the development-reference gate.
- Both current publisher sources downloaded; both FL endpoints failed with TLS protocol alerts. The FL evidence remains historical/indexed, and zero current raw-FL passages are admitted.
- All eight pairs have equal project token counts, compared with five equal whitespace-count reading-edition pairs. The 212 token-position pairings remain explicitly unvalidated hypotheses; no word meanings, training labels or untouched test units are accepted.
- 118 tests and independent statement/token/span/provenance checks passed. Experiments 1–15 are preserved. Source extraction drift is explained by whitespace, a byline and section headings.

See the [registration](experiments/kamri_correspondence_pilot_v16.md), [immutable report](runs/000016_kamri_correspondence_review/report.md), [unit ledger](runs/000016_kamri_correspondence_review/unit_ledger.json), [passage gates](runs/000016_kamri_correspondence_review/passage_gates.json), and [verification receipt](reports/000016_verification.json).

```sh
uv run python scripts/verify_correspondence_review_v16.py
```

## Seventeenth experiment

The [frozen positional-consistency experiment](reports/000017_interpretation.md) retains all 212 hypotheses, eight sentences and two exposed components, with 999 preregistered permutations and six fixed controls.

- Primary form-macro cross-unit agreement is 0.974537, versus a permutation mean of 0.025998 and maximum of 0.108515. The one-sided conditional diagnostic p is 0.001; the registered p <= 0.01 development criterion is met. This is not lexical accuracy or held-out semantic success.
- Of 107 FL types, 36 recur across sentences: 34 have one English positional outcome and two conflict. Both conflicts and all singleton forms remain in the ledger. Repetition inside one sentence is not independent support.
- Three forms meet the strict cross-component review-lead rule. They remain unvalidated function-word pairing hypotheses. No meanings, semantic training labels or untouched test units are admitted, and shared lexicons were not used.
- 127 tests passed. Independent brute-force pair statistics, all permutations/controls, exact tail counts, source offsets and preservation of experiments 1–16 passed verification.

See the [registration](experiments/kamri_consistency_v17.md), [immutable report](runs/000017_kamri_positional_consistency/report.md), [form/conflict ledger](runs/000017_kamri_positional_consistency/form_ledger.json), [review leads](runs/000017_kamri_positional_consistency/review_leads.json), and [verification receipt](reports/000017_verification.json).

```sh
uv run python scripts/verify_consistency_v17.py
```

## Eighteenth experiment

The [frozen-candidate passage extension](reports/000018_interpretation.md) retains units 5–8 from each of the two exposed passages: eight units and 175 FL tokens. Primary/secondary positional candidate dictionaries and target predictions were frozen before source-only reference preparation.

- Three units pass positional scoring. Four lack full independent FL coverage; one has 21 FL versus 22 source tokens. All eight units and predictions remain in the denominator.
- The primary predictor has 16 verified positional matches, zero scoreable conflicts and 18 unresolved predictions: 16/34 supported overall, with 141 abstentions. The separate conditional figure is 16/16. This is not translation accuracy.
- The secondary diagnostic has 37 verified matches and 51 unresolved predictions out of 88. No candidate changes, majority repairs, semantic-label promotion or untouched-test admissions occurred.
- All 999 permutations and five fixed controls are preserved. The registered conditional ordering diagnostic p is 0.001 and the development criterion is met on the supported subset.
- 135 tests and independent source/prediction/seal/accounting/permutation checks passed; experiments 1–17 are preserved. Current raw FL provenance remains unavailable.

See the [registration](experiments/kamri_transfer_v18.md), [immutable report](runs/000018_kamri_passage_transfer/report.md), [token outcomes](runs/000018_kamri_passage_transfer/token_ledger.json), [unit gates](runs/000018_kamri_passage_transfer/unit_ledger.json), and [verification receipt](reports/000018_verification.json).

```sh
uv run python scripts/verify_transfer_v18.py
```

## Nineteenth experiment

The [exhaustive single-gap diagnostic](reports/000019_interpretation.md) retains all 21 FL and 22 original English tokens in exposed unit 03:007. All 22 possible gap positions are searched in every observation and control.

- The primary maximum is 2/2 frozen predictions, with 19 abstentions. Fourteen gaps (indices 0–13) tie; no unique gap is identified.
- The secondary descriptive maximum is 16/16, with five abstentions. Gaps 1 and 2 tie: they leave “an” or “Āgama” unpaired. FL “Agama” has no frozen prediction, so these hypotheses remain unresolved.
- The full-search permutation diagnostic p is 0.005: four of 999 null maxima tie the observation. The registered p <= 0.01 development criterion is met. Rotation −1 also reaches the primary maximum; two anchors do not uniquely locate the gap.
- 145 tests and independent replay of all alignments, permutations, controls, spans and hashes pass. Experiments 1–18 and the original v18 length-gate failure are preserved. No semantic training labels, untouched test units or current raw FL are admitted.

See the [registration](experiments/kamri_gap_v19.md), [immutable report](runs/000019_kamri_single_gap/report.md), [all 22 full alignments](runs/000019_kamri_single_gap/observed_alignments.json), [null searches](runs/000019_kamri_single_gap/permutations.json), and [verification receipt](reports/000019_verification.json).

```sh
uv run python scripts/verify_gap_v19.py
```

## Twentieth experiment

The [orthographic-anchor diagnostic](reports/000020_interpretation.md) retains eleven complete development pairs and all 284 FL/source token pairs, excluding target 03:007 from calibration.

- The frozen folded-spelling rule proposes Shakra/Shakra and Brahma/Brahmā at their prior positional-hypothesis indices. Two proposals, units and keys fail the registered minimum of three. The exact baseline finds Shakra alone.
- All eleven cyclic wrong-name views and sixty opposite-component source-absent comparisons yield zero proposals. Two primary proposals survive name-preserving frame lures; copied names do not establish source identity.
- The folded rule mechanically favors gap 1, leaving “an” unpaired. Calibration failure blocks that preference from qualifying as a gap lead; both v19 hypotheses remain, and all earlier gates/ties are unchanged.
- 156 tests and independent Unicode/token/span/control/gate/seal checks pass; experiments 1–19 and the v19 deliverable seal are preserved. No semantic labels, untouched test units, current raw FL or source-identity claims are admitted.

See the [registration](experiments/kamri_orthographic_v20.md), [immutable report](runs/000020_kamri_orthographic_anchors/report.md), [calibration and control ledgers](runs/000020_kamri_orthographic_anchors/calibration.json), [target comparison](runs/000020_kamri_orthographic_anchors/target_comparison.json), and [verification receipt](reports/000020_verification.json).

```sh
uv run python scripts/verify_orthographic_v20.py
```

## Twenty-first experiment

The [calibration-evidence audit](reports/000021_interpretation.md) freezes all 33 publisher-backed Kamri review leads before checking statement eligibility. The eleven prior calibration pairs are a separate comparator.

- Eighteen nominees and all eleven comparator units pass the conservative development-packet gate. Deduplication yields a future panel of 19 units, five connected groups and 476 token pairs.
- Eight eligible additions span three groups outside the prior panel. The registered minimum of six new units, two additional groups and three total groups is met. All groups remain previously exposed.
- All fifteen ineligible nominees remain archived. Twelve have count mismatches, one fails source boundaries and three fail FL boundaries, with overlap. Eleven complete unequal-length pairs remain structural review leads.
- Duplicate indexed support views count once per unit. All original document offsets and observable order checks are retained. No orthographic rule, lexical predictor or target comparison ran.
- 165 tests and independent occurrence/boundary/provenance/QA/order/gate/deduplication checks pass; experiments 1–20 and the v20 deliverable seal are preserved. The v20 failure and both v19 gap hypotheses remain unchanged. No semantic labels, untouched-test units or current raw FL are admitted.

See the [registration](experiments/kamri_calibration_evidence_v21.md), [immutable report](runs/000021_kamri_calibration_evidence/report.md), [all nominee outcomes](runs/000021_kamri_calibration_evidence/nominee_ledger.json), [frozen future panel](runs/000021_kamri_calibration_evidence/future_panel.json), and [verification receipt](reports/000021_verification.json).

```sh
uv run python scripts/verify_calibration_evidence_v21.py
```

## Twenty-second experiment

The [unchanged orthographic retest](reports/000022_interpretation.md) retains all nineteen development units, five connected groups and 476 token pairs, with byte-unchanged v20 scoring and thresholds.

- Primary calibration still has only two proposals, units and keys: Shakra and Brahma/Brahmā, entirely within Nichiren. The three-proposal/unit/key minimum fails. The exact baseline retains Shakra alone.
- The eight added units have no eligible FL candidates under the frozen rule. Dropping Nichiren removes all support; dropping another group leaves the same two proposals. These summaries do not alter the full-panel gate.
- All nineteen wrong-name views and 274 cross-group comparisons yield zero proposals. Only five cross-group comparisons have eligible candidates on both sides. Name-preserving frame lures retain two primary and one baseline proposal; source specificity remains limited.
- The target's mechanical gap-1 preference remains ineligible. Both original alternatives, the v20 failure, v19 ties and v18 length gate are preserved.
- 170 tests and independent full-panel/Unicode/control/group/dependence/seal checks pass. Experiments 1–21 and v20/v21 deliverable seals remain unchanged. No meanings, semantic labels, untouched-test units or current raw FL are admitted.

See the [registration](experiments/kamri_orthographic_retest_v22.md), [immutable report](runs/000022_kamri_orthographic_retest/report.md), [calibration ledgers](runs/000022_kamri_orthographic_retest/calibration.json), [group support](runs/000022_kamri_orthographic_retest/group_accounting.json), and [verification receipt](reports/000022_verification.json).

```sh
uv run python scripts/verify_orthographic_retest_v22.py
```

## Twenty-third experiment

The [bounded capture/review pilot](reports/000023_interpretation.md) fixes two whole posts, two publisher PDF windows and at most eight primary requests before acquisition.

- Both native FL requests fail with TLS errors. Exact-URL archive queries recover dated raw post replays from April 10 and March 12, 2026. Their extracted bodies contain 1,091 and 1,736 whitespace words including mixed-language prefaces and references; no language or meaning labels are accepted.
- Both publisher PDFs download and all eight fixed pages render and pass same-assistant visual QA. Western's PDF bytes differ from the earlier snapshot, so its normalized prose remains withheld. Risk's PDF matches its earlier snapshot.
- Western's decoded archive payload agrees with the index digest; Risk's does not. The discrepancy remains an open provenance/representation issue in its review dossier, without changing criteria or retrying.
- One packet meets the registered paired-material gate; both dossiers have blank independent-review forms and explicit limitations. No independent semantic review, model evaluation, semantic label or untouched-group admission occurs.
- 178 tests and independent request/archive/date/PDF/provenance/export/hash checks pass. Experiments 1–22 and the v22 deliverable seal are preserved. Existing groups remain exposed; prospective holdout reservation requires new source works.

See the [registration](experiments/kamri_capture_review_v23.md), [immutable report](runs/000023_kamri_capture_review/report.md), [Western dossier](data/v23/review_packets/western_esoterism/review.md), [Risk dossier](data/v23/review_packets/risk_math/review.md), and [verification receipt](reports/000023_verification.json).

```sh
uv run python scripts/verify_capture_review_v23.py
```

## Twenty-fourth experiment

The [provenance continuation](reports/000024_interpretation.md) freezes the two Western PDF snapshots, pages 90–94, two native permalinks and one existing Risk archive timestamp before execution.

- Western's fixed window passes exact text, page-dimension and RGB-pixel comparison on all five pages; decoded page streams also match. Raw PDF hashes and whole-book extracted text differ, so equivalence is limited to the fixed window. A new current-PDF page export supplements independent review; the original v23 byte-binding failure stays unchanged.
- Risk's preserved gzip entity matches the frozen CDX digest exactly. Decompression reproduces v23's HTML bytes and whole-post text exactly. The earlier mismatch is explained by comparison across encoding layers; original WARC identity and semantic/source correspondence are not established.
- Both native requests fail TLS with the second certificate-verifying Python/OpenSSL client. All three fixed attempts remain visible, without retries or alternate archive timestamps; current raw-FL materials remain 0/2.
- 185 tests and offline independent verification pass, preserving experiments 1–23. The first verifier failed on the run-1 document-ID hash schema; the failed audit and original code remain sealed. A separately registered audit revision uses the existing schema-aware checker, with all v24 gates unchanged.
- Both new review supplements keep independent reviewer fields blank. No semantic labels, model evaluation or untouched-test admission occurs.

See the [registration](experiments/kamri_provenance_v24.md), [immutable report](runs/000024_kamri_provenance/report.md), [Western supplement](data/v24/review_supplements/western_esoterism/review.md), [Risk supplement](data/v24/review_supplements/risk_math/review.md), [audit revision](experiments/kamri_provenance_v24_audit_revision1.md), and [verification receipt](reports/000024_verification.json).

```sh
uv run python scripts/verify_provenance_v24_revision1.py
```

## Twenty-fifth step: external review handoff

The [external review handoff](reports/000025_external_review_guide.md) packages the existing Western and Risk materials into two self-contained ZIP archives with unchanged publisher PDFs, fixed page images/text, dated FL posts, hash manifests, instructions and blank return forms.

- Candidate source identities are disclosed; prior reading translations, dictionaries and predictions are excluded. The fixed windows and previously exposed groups stay unchanged.
- Returned evidence uses exact quoted spans and Unicode code-point offsets, with explicit reviewer identity/independence/exposure, language scope, boundaries, coverage and uncertainty. Support, rejection and entirely uncertain reviews are permitted.
- A read-only validator checks bindings, structure and offsets without admitting source identity or semantic labels. Blank forms correctly fail. All 192 tests and independent packet/member/hash/history checks pass; experiments 1–24 remain unchanged.
- Engineering handoff is complete; both packets await external independent returns. No reviewer result, semantic label, untouched admission, model evaluation, external contact or new acquisition occurs.

See the [handoff guide and ZIP links](reports/000025_external_review_guide.md), [report](reports/000025_interpretation.md), [registration](experiments/kamri_review_handoff_v25.md), and [verification receipt](reports/000025_verification.json).

```sh
uv run python scripts/verify_review_handoff_v25.py
```

## Twenty-sixth experiment: ordered-anchor source specificity

The [restricted-corpus diagnostic](reports/000026_interpretation.md) incorporates the automated review's supplied evidence appendix while preserving its exposed, non-independent status. All nine paired observations, four unmatched-English blocks and four packet-text hashes verify. Literal absence of the English blocks is not a semantic coverage result.

- Three primary clusters (Western names, Western Saturn labels, Risk spellings) and three descriptive single-anchor queries are frozen against eleven existing publisher exports. Length-matched rules produce 61 Western and 98 Risk windows, for 477 natural scores. Two Western clusters remain dependent observations from one work.
- All three primary clusters uniquely retrieve the nominated source in the natural panel and abstain when it is removed. The convenience panel also lets every descriptive single anchor retrieve uniquely; it does not measure broad source specificity.
- All three ordered copied-anchor frames fool the source-absent procedure; adding them beside the actual source creates ties. The registered combined gate fails. This is an explicit representational limitation, not an estimated real-world error rate or a rejection of all textual dependence.
- Reversed, anchor-masked and Risk spelling-corrected controls are retained. All 201 tests and independent full replay pass; experiments 1–25 and the earlier automated intake remain unchanged.
- No source identity, meaning, independent semantic review or untouched-test admission occurs. No target rescore, PDF re-extraction or network request runs.

See the [registration](experiments/kamri_source_specificity_v26.md), [immutable report](runs/000026_kamri_source_specificity/report.md), [query ledgers](runs/000026_kamri_source_specificity/query_ledgers.json), [control scores](runs/000026_kamri_source_specificity/control_scores.json), and [verification](reports/000026_verification.json).

```sh
uv run python scripts/verify_source_specificity_v26.py
```

## Twenty-seventh experiment: residual literal context

The [residual-context diagnostic](reports/000027_interpretation.md) fixes three FL contexts at forty lexical tokens around each reported cluster and masks all nineteen component tokens of the v26 anchor vocabulary as hard barriers.

- Eight raw, page-separated publisher views provide same-work alternatives; nine historical exports remain in the panel. Seventeen views generate 775 fixed windows and 2,325 natural comparisons. No source search or PDF-page expansion occurs.
- No natural window shares an eligible residual four-token seed with any query. Expected-page retrieval is 0/3 at the frozen eight-token threshold. All source-work-absent panels abstain; the primary gate fails.
- All three exact-context copies qualify with longest residual runs of forty tokens. Anchor-only frames, reversed contexts and legacy publisher-window controls all score zero. The search is sensitive to literal copies, while the tested natural contexts supply no qualifying residual literal signal.
- All 210 tests and independent diagonal-run/PDF/text/pixel/hash replay pass. Experiments 1–26 and original packets remain unchanged.
- This does not reject translation or paraphrase. No source identity, meaning, independent semantic review or untouched admission occurs. Extraction/footnote/boundary limits and prior failures remain explicit.

See the [registration](experiments/kamri_residual_context_v27.md), [immutable report](runs/000027_kamri_residual_context/report.md), [query ledgers](runs/000027_kamri_residual_context/query_ledgers.json), [controls](runs/000027_kamri_residual_context/control_scores.json), and [verification](reports/000027_verification.json).

```sh
uv run python scripts/verify_residual_context_v27.py
```

## Twenty-eighth step: block-boundary and export-coverage audit

The [structural audit](reports/000028_interpretation.md) reconstructs both archived FL exports exactly, preserving every atom, join separator, final newline and original evidence offset. It maps 2,950 words on the eight unchanged publisher pages into 318 geometry lines, with all ambiguous and unmapped concordances retained.

- Western and Risk contain 27 and 28 nonempty paragraph block runs. Neither has explicit quotation/navigation markup under the registered rule. Bibliographic-looking entries and related-post references remain visible without forced semantic labels.
- All three v27 contexts cross paragraph runs; the Western Saturn context extends into a bibliographic entry. The original contexts and v27's failed literal gate remain unchanged.
- The saved Risk raw page texts contain 24 bracketed numeric citation markers with no matching bracketed form in the legacy export. Unmapped full lines are not automatically missing content, and short-token reference intersections can be incidental.
- Visual QA confirms Western note-region candidates and records missed Risk footnote separators on pages 2 and 3, rotated-margin fragmentation and unresolved roles. All 219 tests and independent DOM/geometry/concordance/reference reconstruction pass; the prior 27 runs and packets remain unchanged.
- Engineering accounting is complete. No source identity, meaning, independent-review admission, untouched admission, new network acquisition or semantic evaluation occurs.

See the [registration](experiments/kamri_block_audit_v28.md), [Western block sheet](data/v28/maps/western_esoterism_html.md), [Risk block sheet](data/v28/maps/risk_math_html.md), [PDF layout sheet](data/v28/maps/pdf_layout.md), [visual receipt](data/v28/visual_review.json), [immutable report](runs/000028_kamri_block_audit/report.json), and [verification](reports/000028_verification.json).

```sh
uv run python scripts/verify_block_audit_v28.py
```

## Twenty-ninth step: Risk character-layout derivative

The [source-layout derivative](reports/000029_interpretation.md) passes its four registered engineering checks on the three already exposed Risk pages. It retains all 7,246 extracted character records with native-string offsets and geometry, explicitly records 1,152 inferred spaces and 123 synthetic newlines, and preserves all original representations.

- The rotated margin becomes one lane rather than 26 fragments. Raster scanning finds the two visible footnote separators missing from v28's vector inventory, with three and five candidate note lines on pages 2 and 3.
- The main-text `as-` / `tronomy` page-edge continuation is recorded around the footnote interruption without creating a joined word. All 24 bracketed citation occurrences retain their raw-page key multiplicities.
- Full-line concordance remains incomplete: 47 unique, 2 ambiguous and 74 unmapped raw-page matches across 123 derivative lines. The denominator differs from v28, so these counts are not calibrated extraction recall. Ligatures, split words, spellings, short incidental matches and unresolved roles remain visible.
- All 231 tests, three-page visual QA and independent character/raster/grouping/piece/concordance/continuity replay pass. The prior 28 run inventories and original packet hashes verify unchanged.
- This is exposed-fixture engineering validation. Scientific acceptance and semantic metrics remain null; no source identity, word meaning, independent review or untouched admission occurs.

See the [registration](experiments/risk_layout_derivative_v29.md), [full source-linked layout sheet](runs/000029_risk_layout_derivative/layout_review.md), [page/piece maps](runs/000029_risk_layout_derivative/pages.json), [continuity ledger](runs/000029_risk_layout_derivative/continuities.json), [visual receipt](data/v29/visual_review.json), [immutable report](runs/000029_risk_layout_derivative/report.json), and [verification](reports/000029_verification.json).

```sh
uv run python scripts/verify_risk_layout_v29.py
```

## Thirtieth experiment: anchor-masked paragraph repetition patterns

The [paragraph-level diagnostic](reports/000030_interpretation.md) freezes all 55 FL paragraphs, 65 source regions and 36 primary source candidates. Three selected queries test a token-renaming invariant: ten-token equality patterns after all nineteen anchor components become hard barriers. It uses 108 natural comparisons and 199 complete shuffled panels, with 21,492 null scores and search-wide maxima.

- The registered structural criterion fails: 0/3 nominated paragraphs retrieved. Western names selects the preceding source paragraph; Risk selects a Western fragment; Saturn has no eligible query fingerprints.
- Opaque positives qualify for 2/3, making Saturn's natural abstention uninformative under this feature rule. Search-max corrected tails are 0.015, 1 and 0.13; none passes the fixed 0.01 criterion.
- One source-work-absent panel nominates a different-work unit. All anchor frames score zero; adding the frame does not remove Risk's existing nomination. Opaque repetition-equivalent controls also fool localization in two panels.
- The top natural matches each comprise three overlapping windows within one twelve-token span. They are dependent structural observations, not multiple independent alignments or admitted meanings. The neighboring Western paragraph remains a lead, without changing the failed target definition.
- All 243 tests and independent registry/equality-partition/witness/control/null/gate replay pass. All 29 earlier run inventories and deliverable hashes verify unchanged. Semantic metrics and scientific acceptance remain null; no meaning, source identity, independent review or untouched admission occurs.

See the [registration](experiments/paragraph_patterns_v30.md), [unit registry](data/v30/units.md), [natural ledgers](runs/000030_paragraph_patterns/query_ledgers.json), [controls](runs/000030_paragraph_patterns/controls.json), [null scores](runs/000030_paragraph_patterns/nulls.json), [gate](runs/000030_paragraph_patterns/gate.json), and [verification](reports/000030_verification.json).

```sh
uv run python scripts/verify_paragraph_patterns_v30.py
```

## Thirty-first experiment: synthetic mechanism and identifiability calibration

The [known-lineage synthetic assay](reports/000031_interpretation.md) freezes 40 symbolic parents, 200 transformed queries and 1,000 panels before running the unchanged v30 scorer. It separates public predictor inputs from the generator oracle and records feature availability before scoring. No natural target is rescored.

- Bijective recovery is 24/40 overall and 24/24 among feature-available queries. Present-parent recovery falls to 4/40 with insertions, 0/40 with deletions or contextual forms, and 20/40 with the fixed local swaps. All 92 unavailable queries remain; all 460 unavailable panels abstain.
- The 600 rejection panels produce 51 non-parent nominations. Explicit collision panels abstain in 199/200 cases; one frequency-shuffle distractor still wins. No anchor frame is selected.
- All 40 equivalent-impostor certificates and all 200 paired-world feature/score/decision equalities verify. In 48 paired worlds the same slot nomination recovers the true generated parent in one and names a constructed non-parent in the other. Within-paragraph equality features cannot separate those worlds.
- Engineering calibration passes; the synthetic candidate-localization admission criterion fails. All 255 tests and independent generator/origin/equality/witness/metric replay pass; the prior 30 runs and deliverable hashes verify unchanged.
- Profiles, relabeling keys, mechanisms and panel variants are dependent fixtures, not independent natural-language trials. Scientific acceptance and natural semantic metrics stay null, with no source identity or meaning admitted.

See the [registration](experiments/synthetic_mechanisms_v31.md), [public cases](data/v31/public_cases.json), [generator oracle](data/v31/oracle.json), [pre-score availability](data/v31/availability.json), [predictions](runs/000031_synthetic_mechanisms/predictions.json), [assessment](runs/000031_synthetic_mechanisms/assessment.json), and [verification](reports/000031_verification.json).

```sh
uv run python scripts/verify_synthetic_mechanisms_v31.py
```

## Thirty-second experiment: frozen mapping and gap-aware synthetic transfer

The [synthetic transfer assay](reports/000032_interpretation.md) learns 96 alias-to-symbol entries from eight aligned training passages, freezes the mapping before test generation, and scores 420 queries in 2,100 panels with global insertion/deletion alignment. All unknown forms and barriers remain penalized gaps in the coverage denominator.

- The registered synthetic criterion passes: 96/96 supported seen-vocabulary parents retrieved, both with and without structural impostors;840/840 absent/impostor-only panels abstain; 420/420 exact-duplicate panels abstain; 900/900 dense-unknown/unseen-key panels abstain.
- The complete source-present denominator is 120/420 recoveries and 300 abstentions. Seen-contextual forms are untrained; sparse unknown types combined with edits can exceed coverage. All 276 unavailable queries and 1,380 corresponding panels remain visible.
- Cross-passage lexical constraints distinguish repetition-equivalent impostors. Exact duplicate candidates still tie when qualified. These are supervised synthetic capabilities, not natural source identity or unknown-word inference.
- Qualified parent paths return 6,772 known matches, with 6,752 exact generated-origin matches and 20 positional disagreements. All 120 qualified pairs have multiple optimal operation paths; gap-order multiplicity is not automatically matched-pair ambiguity.
- All 270 tests and independent training/generation/learning/LCS/path/metric replay pass. All 31 prior runs and seals remain unchanged. The symbolic learner/aligner ran; a post-run note clarifies the frozen report's ambiguous legacy model-execution flag. Natural semantic acceptance remains null.

See the [registration](experiments/synthetic_transfer_v32.md), [frozen mapping](data/v32/frozen_mapping.json), [test cases](data/v32/public_cases.json), [predictions](runs/000032_synthetic_transfer/predictions.json), [origin assessment](runs/000032_synthetic_transfer/assessment.json), [execution note](reports/000032_execution_note.json), and [verification](reports/000032_verification.json).

```sh
uv run python scripts/verify_synthetic_transfer_v32.py
```

## Thirty-third experiment: all-optimal-alignment ambiguity audit

The [frozen positional audit](reports/000033_interpretation.md) covers all 2,520 v32 candidate pairs, 420 queries and 2,100 panels. It preserves every possible diagonal match and distinguishes forced edges from optional matches and gap-order-only path multiplicity.

- The strict synthetic origin hypothesis fails: the forced-only diagnostic retains 6,508/6,772 primary matches, removes twelve of twenty origin disagreements, retains eight, and discards 252 correct positions. All 120 qualified parent pairs retain a match; the 300 unqualified pairs remain in the denominator.
- Only 32/120 primary pairs have matched-pair ambiguity. The other 88 have multiple operation paths with identical matches. Exact path multiplicity is not a probability or automatically positional uncertainty.
- All eight retained disagreements are an adjacent equal-symbol swap in one source passage replicated under four keys. Visible tokens stay identical while the generator swaps ancestry. The post-run witnesses explain the limit without revising the failed strict-origin criterion.
- All 283 tests and independent maximum-LCS/DAG-mandatory-edge verification pass. All 32 earlier run inventories and seals verify unchanged. The mapping, coverage, scores, retrieval decisions and original traces remain fixed. Scientific acceptance and semantic metrics remain null.

See the [registration](experiments/alignment_ambiguity_v33.md), [all alternatives](runs/000033_alignment_ambiguity/ambiguity.json), [assessment](runs/000033_alignment_ambiguity/assessment.json), [origin witnesses](reports/000033_origin_note.json), and [verification](reports/000033_verification.json).

```sh
uv run python scripts/verify_alignment_ambiguity_v33.py
```

## Thirty-fourth experiment: paired-world positional identifiability

The [paired-world diagnostic](reports/000034_interpretation.md) enumerates all 378 adjacent sites across six exposed v32 passages under one frozen alias key. It retains 36 excluded sites and assesses 684 worlds from 342 eligible sites through 335 distinct content-only observations.

- Thirteen equal-symbol swaps preserve every public input byte while changing ancestry. All collision certificates verify the balanced point-answer bound of two exact affected calls out of four; the frozen policies reach that bound. This is a conditional identifiability demonstration, not natural semantic validation.
- All 329 unequal-symbol controls change query bytes. The frozen forced-only policy returns zero of their 658 swapped positions. Its registered nonvacuous safety hypothesis fails on coverage; zero returned errors is not a successful recovery guarantee.
- The representative policy returns 330 affected unequal-swap positions with 329 exact origins. Strong full-context scores hide abstention or error at the manipulated positions. Symbol compatibility accepts identical occurrences by construction and remains a consistency check, not independent accuracy.
- All 295 tests and independent fixture/LCS/mandatory-edge/world-score replay pass. All 33 prior runs and deliverable seals remain unchanged. The mapping, old retrieval decisions and scientific limits remain fixed; natural acceptance and semantic metrics stay null.

See the [registration](experiments/positional_worlds_v34.md), [public observations](data/v34/public_observations.json), [site/world oracle](data/v34/oracle.json), [predictions](runs/000034_positional_worlds/predictions.json), [assessment](runs/000034_positional_worlds/assessment.json), [exact witnesses](reports/000034_witnesses.json), and [verification](reports/000034_verification.json).

```sh
uv run python scripts/verify_positional_worlds_v34.py
```

## Thirty-fifth experiment: adjacent-transposition alignment

The [local crossing assay](reports/000035_interpretation.md) preserves all 335 v34 observations, 684 worlds and 378 site rows, then adds deterministic controls for 371 distinct observations, 42 control rows and eighteen synthetic panels. The mapping and prior scores remain frozen.

- The registered synthetic recovery gate passes. The new crossing block recovers all 658/658 unequal-swap affected positions as forced origin-exact matches; v34 returned zero there. All mapped identity-world positions remain forced and exact.
- The 26 equal-symbol swap ancestry disagreements remain in the full denominator. Identical public inputs still support different histories; the new operation supplies no ancestry information for those cases or natural word meanings.
- Unknown/blocked tokens enter no possible optimal match or crossing block. Eighteen zero-match controls and six impostors fail coverage. Six present panels recover; six absent and six duplicate panels abstain. Sparse unknown/barrier controls can qualify through their known context while leaving the protected token unmatched.
- All 309 tests and independent integer-DAG/mandatory-pair verification pass. All 34 earlier run inventories and seals verify unchanged. Natural scientific acceptance and semantic metrics stay null; no source identity, meaning, external review or untouched admission occurs.

See the [registration](experiments/adjacent_transposition_v35.md), [inputs and panels](data/v35/public_observations.json), [predictions](runs/000035_adjacent_transposition/predictions.json), [assessment](runs/000035_adjacent_transposition/assessment.json), [exact witnesses](reports/000035_witnesses.json), and [verification](reports/000035_verification.json).

```sh
uv run python scripts/verify_adjacent_transposition_v35.py
```

## Next evidence boundary

Freeze v35 at its exposed single-swap mechanism result. Register a fresh synthetic mixed-edit test before generating passages: combine insertions, deletions, disjoint swaps and withheld forms with fixed full-token denominators, source-absent/impostor/duplicate controls and separate identifiable-position metrics. Reuse this mapping and aligner without tuning. Preserve equal-symbol ancestry uncertainty and model-mismatch failures. No natural target rescore or semantic admission follows from v35.

## Experiment 36: mixed-edit transfer and natural-evidence decision

The [fresh frozen-model test](reports/000036_interpretation.md) is complete. The
combined registered gate fails. All 32 primary mixed-edit queries select the
parent when present; all 32 nominate the near-copy when the parent is absent;
all 32 duplicate panels abstain. Clean forced matches retain 2,000/2,016
recoverable tokens, with 1,992/2,000 exact origins. Affected positions separately
retain 189/192, of which 181 are origin-exact. Mapping-error interventions show
that every optimal path can agree on the wrong symbol: the sparse branch has
19 wrong-symbol forced matches in qualified parent pairs across all profiles.

The full inventory retains 16 new parents, 80 queries, three dictionary branches,
1,200 alignments, 720 panel decisions and 5,760 query tokens per branch. Unknowns,
block mismatches, absent parents, copied competitors, duplicate ties and all
failures remain visible. The initial preparation label-format failure and its
registered repair are preserved; seed, edits, model and criteria were unchanged.

315 tests pass. Independent integer-DAG replay agrees on all alignments and
decisions, independently checks fixture/metric accounting and reconstructs the
natural inventory. All 35 prior runs and deliverable hashes verify unchanged.

The [feasibility audit](reports/000036_natural_evidence_feasibility.md) finds 25
tracked reading-edition articles in 14 conservative connected groups, all exposed;
19 eligible development units in five groups; two dated-post review dossiers;
and zero qualifying unexposed independently reviewed works against the registered
four-work pilot capacity rule. This is an inventory limit, not a claim about all
FL material. Natural meanings, source identities, semantic accuracy, independent
review admissions and untouched-test admissions remain unestablished.

Stop synthetic feature expansion. The next bounded step is a separately
registered source-first acquisition/review-feasibility pilot with fresh connected
works, exposure tracking, exact artifact provenance and a fixed request budget.
Keep existing groups as development evidence; do not create a test fold by
relabeling them or repair the failed gate by changing thresholds.

Verify offline with `.venv/bin/python scripts/verify_mixed_edit_transfer_v36.py`.
Generation/scoring refuse existing outputs; the verifier preserves its receipt.

## Experiment 37: bounded source intake

The [source-first acquisition and review-feasibility pilot](reports/000037_interpretation.md)
is complete. Four fixed queries nominated four posts from eight slots; two
queries returned no results. All four direct FL requests failed before HTTP
during TLS setup. Exact-URL browser fallbacks supplied three indexed responses
and one fetch error. Those responses do not establish raw/current or complete
posts, and discovery exposure remains explicit.

The fixed explicit-link rule nominated one previously unrecorded arXiv identifier
and left three source slots empty. Its single source request recovered a complete
PDF; a same-assistant title-page/page-count inspection confirms the requested
identifier and version. Source-work independence, remaining extraction, source
coverage and passage correspondence are unresolved. The paper is one citation,
not an admitted immediate source. No natural target, lexicon or translator ran.

The [provisional intake bundle](data/v37/source00_intake_bundle.zip) contains the
unchanged PDF, first-page image, indexed target response, separate acquisition
receipts, hash manifest and a blank review declaration. It is not review-ready
semantic gold, independent review, or an untouched test unit. No reviewer has
been assigned or contacted. The four-work natural-capacity gate stays unmet.

323 tests pass. Offline checks independently reconstruct post nomination,
verify route/limit/hash/capacity accounting and preserve all 36 prior runs and
deliverables. Citation parsing is shared with execution and is not independently
validated source identity. An unattributed initial search batch and its registered
same-query interface repair remain in the eight-execution discovery ledger.

Next: seek an adequate dated target capture for post00, then perform a scoped
material/citation review of the fixed recovered lead. Preserve uncertainty and
the missing independent-review requirement; do not assume a cited source supplies
meanings for opaque prose or extend the finished search budget.

Verify offline with `.venv/bin/python scripts/verify_source_intake_v37.py`.
Acquisition refuses existing output directories; verification preserves its receipt.

## Experiment 38: dated capture and citation scope

The [fixed dated-capture and source-scope audit](reports/000038_interpretation.md)
is complete. Both registered routes succeed: exact-URL CDX metadata and the
selected replay at 2026-01-10 22:21:00 UTC. Post-body/title/permalink identity,
Memento timestamp and saved decoded-body digest all agree. The material gate
passes. This is a dated archive observation; v37's current-native failures and
indexed limitations remain preserved.

All eight source PDF pages were exported without text repairs and visually
inspected. The unchanged literal rule finds 0/8 target quoted spans in that
paper; engineered source-copy controls pass 8/8 and the absent marker hits no
page. The exact source citation occurs once in the target. Shared topic terms
and a bibliography entry do not establish opaque-text meanings or an immediate
source relationship; exact-text absence does not reject translated/edited reuse.

The [neutral source-disclosed review packet](data/v38/neutral_review_packet.zip)
contains the dated target, unchanged source PDF, page-local source text, capture
and material receipts, hashes and a blank review declaration. It excludes our
quote/anchor results and proposed answers. The [annotated project bundle](data/v38/scoped_materials.zip)
separately retains observations. No reviewer is assigned or contacted, and no
independent review, source identity, meaning or untouched test unit is admitted.

329 tests pass. Independent literal-count/witness checks, PDF reextraction,
route accounting and ZIP checks pass; all 37 prior runs and deliverable seals
remain unchanged. An initial PDF-runtime import-path failure is preserved,
with no code, source or criteria changes.

Next bounded diagnostic: register one acquisition of the saved bibliography's
first other explicit versioned arXiv identifier, 1809.09615v1, and test the same
eight literal quotation queries with the unchanged rule. Retain absence and
acquisition failures; no English match would establish an opaque FL translation.
Independent review and the four-work natural capacity requirement remain open.

## Experiment 39: next cited paper, unchanged quote queries

The [one-paper quotation diagnostic](reports/000039_interpretation.md) is complete.
One request acquired arXiv1809.09615v1, fifteen pages. All eight target queries
and the v38 literal matcher stay fixed. Result: 1/8 literal matches, entirely
the expanded instrument name; 0/7 longer quoted blocks occur in full. All
120 query/page decisions remain available. Page-copy controls pass 15/15;
the absent marker matches no page. This does not reject edited/partial reuse,
and the name-only hit is not passage, translation or opaque-word evidence.

All complete source page images were inspected. The margin says v1, 25 Sep
2018, but the internal Dated line says March7,2025. Both facts remain visible;
their cause and historical PDF-byte identity are unresolved. The registered
version-marker/representation gate passes without becoming a historical gate.

The [neutral packet with factual provenance notice](data/v39/neutral_review_packet_with_provenance.zip)
excludes match outcomes and proposed answers. No reviewer is assigned or
contacted; no independent review, meaning, source identity or untouched unit
is admitted. Natural-benchmark capacity remains unmet.

333 tests pass. Independent literal counts/witnesses, PDF reextraction, route
and packet checks pass; all 38 prior runs and deliverable seals remain intact.
Next: a separately registered source-version provenance check to investigate
the observed date difference. No additional source request or partial-query
search belongs to this completed experiment.

## Experiment 40: source-version and date provenance

The [provenance diagnostic](reports/000040_interpretation.md) is complete.
Both registered official requests succeeded: the version page and source
package for arXiv1809.09615v1. The current submission history lists v1 on
25 September 2018. The source contains `\date{\today}` in its title section;
the saved PDF's creation/modification fields both give 7 March 2025, matching
its internal date. This supports a later rendering with a dynamic date. The
exact build chain and historical 2018 bytes remain unauthenticated.

337 tests pass. Receipt hashes, source inventory, exact date witnesses and
PDF metadata are verified; all 39 prior runs and seals remain unchanged.
No quotation was rescored or semantic/source-identity claim admitted.

Next: a separately registered, one-request quotation-origin discovery test
using complete quote00, the lowest-ID long quotation from v38. The date branch
stops here; natural-benchmark capacity and independent review remain open.

## Experiment 41: one full-quotation discovery search

The [one-request discovery diagnostic](reports/000041_interpretation.md) is
complete. The unchanged full quote00 query returned seven attributable results.
Four display the complete quotation: Physics World, the existing FL target and
two credited reposts. Only the first, the Physics World article, qualifies for
external lead nomination. Its indexed text displays 17 July 2018. This remains
a discovery lead, with no raw capture, authenticated original quotation source,
opaque FL meaning or untouched test unit admitted.

337 full-workspace tests and 298 isolated-public-export tests pass. All 40 prior
runs and seals remain intact. At the user's request, each work turn now ends
with a public `main` commit/push and a separate local evidence checkpoint.
Next: one registered native capture of the nominated URL, with no search retry
or opaque-passage alignment in this completed experiment.

## Experiment 42: native publisher quotation and attribution

The [single-request native check](reports/000042_interpretation.md) is complete.
The current Physics World page was captured with HTTP 200 and passes all eight
registered representation checks. Complete quote00 appears once in its visible
body, in a paragraph that names Gorham and follows the quotation with he-says
wording. Publisher date metadata is preserved without becoming historical
authentication. No other quotation or opaque passage was scored.

340 full-workspace and 301 isolated-public-export tests pass. All 41 prior runs
and seals remain intact. Evidence stays local; public changes are committed and
pushed at turn end. Next: register all eight unchanged quotation queries against
the already saved publisher body, using quote00 as a known positive control.

## Experiment 43: fixed whole-quotation inventory on the publisher body

The [offline eight-query check](reports/000043_interpretation.md) is complete.
There are 2/8 complete matches: known quote00 and the expanded instrument name.
The seven-long-block count is 1/7, entirely the known control; the new open
question returns 0/6 for the remaining longer blocks. No query, matcher, source
body or historical result changed, and no network request was made.

Known-positive, engineered body-copy and absent-marker controls pass. 340 local
and 301 isolated-public-export tests pass; all 42 prior runs and seals remain
intact. No opaque meanings, source identity, independent review or untouched
test unit is admitted. Next: separately register an exact-fragment audit across
all six unmatched longer blocks, preserving this whole-query result.

## Experiment 44: exact partial English overlap

The [six-block exact-fragment audit](reports/000044_interpretation.md) is complete.
At the preregistered eight-token cutoff, quote02 has one 22-token run; the other
five blocks have longest runs of two tokens and no qualifying run. Covered
tokens total 22/375 under this rule, with overlaps counted once. All four controls
pass. No gap, punctuation repair, fuzzy match or new acquisition was used.

A separate suffix-DP verifier reproduces all runs, offsets and coverage. 345
full-workspace and 306 isolated-public-export tests pass; all 43 old runs and
seals remain intact. This is English fragment correspondence, not opaque FL
translation, copying direction or untouched benchmark evidence. Next: a frozen
quote02 context dossier separating the shared span from nonmatching context
and reported attribution before considering opaque-passage alignment.
