# Experiment 6: Misinfons correspondence audit

Experiment 6 is complete and verified. The unchanged alias bundle improves the two-statement continuation from one recovered link to two, but the five-statement mechanism passage remains at two of five links. Both additional blocks rank the correct source first in both variants; neither is admitted. The audit supplies four new equal-length positional agreements for the proposed forms of **of** and **that**, while retaining three conflicting opening occurrences. Every observation still comes from one article and one English source work. No lexical meaning is promoted to supported status.

## Frozen design and source boundaries

The [registration](../experiments/kamri_correspondence_v6.md) precedes the new passage scores. The [benchmark](../benchmarks/kamri_correspondence_v6.json) seals all source/input hashes and reference spans. Baseline and gated aliases call the unchanged v5 prediction functions, v4 token-mass local alignment, and ordered token decoder. The ten source candidates, three aliases, query-only gate, v1 lexicon, floor 0.72, penalties, and v5 thresholds are unchanged. No labels or reference-guided token paths train or select the scorer. The universal variant is omitted from this audit, so no universal-versus-gated benefit is claimed.

| Packet | FL scope | Corresponding source scope | Status |
|---|---|---|---|
| Opening | Existing seven statements, 162 tokens | Models of Magic atoms 55–63; nine unchanged edges | Development regression |
| Continuation | Two statements, 54 tokens | Atoms 64–65; two provisional edges | New within-article check |
| Mechanism | Five statements, 97 tokens | Atoms 66–70; five provisional edges | New within-article check |

Atom IDs in this report are zero-based. The two new FL blocks end at colons before English quotations. They remain separate queries; excluding the inserted quotation does not create a fictitious continuous passage. The continuation follows the morphic-fields paragraph. The mechanism follows the meme/misinfon quotation and ends before the cultural-information quotation. Both fit the registered 180-word cap without truncation.

FL text was imported from the [indexed Misinfons article](https://forgottenlanguages-full.forgottenlanguages.org/2019/09/misinfons-and-hypermemetic-logic.html), explicitly labeled as an indexed excerpt. A direct web open failed with a non-retryable captcha redirect; it was not bypassed. Search indexing may reflect an older page version. The English source remains the previously acquired [Models of Magic edition](https://www.spiralnature.com/magick/models/); its document and offsets are unchanged. The [acquisition ledger](../benchmarks/inputs/correspondence_v6_acquisition.json) preserves selected bytes, receipts, and quotation-boundary locators.

The selected additional-block denominator is **two, both available**. These are two blocks from the same previously studied article, not two independent works. There are zero fresh independent source works. All labels are inspected, single-analyst structural correspondences, not independently established token semantics. The unavailable Altruist source from experiment 5 remains unavailable and outside this audit.

## Retrieval and alignment

| Packet | Variant | Correct-source rank / 10 | Correct-source strength | Prediction coverage | Conditional edges: correct / proposed / reference | Admitted |
|---|---|---:|---:|---:|---:|---|
| Opening | Baseline | 3 | 0.020165 | 29/162 | 2/2/9 | No |
| Opening | Gated aliases | 1 | 0.020165 | 43/162 | 2/2/9 | No |
| Continuation | Baseline | 1 | 0.104148 | 10/54 | 1/1/2 | No |
| Continuation | Gated aliases | 1 | 0.108605 | 14/54 | 2/2/2 | No |
| Mechanism | Baseline | 1 | 0.056302 | 21/97 | 2/2/5 | No |
| Mechanism | Gated aliases | 1 | 0.060220 | 25/97 | 2/2/5 | No |

The opening exactly reproduces experiment 5's rankings, paths, counts, threshold, margin, admission, and source-absent outcome. Its shuffle controls use the separately registered v6 seed and therefore need not reproduce v5's shuffle counts.

On the two new blocks, conditional and retrieved edge counts coincide because the correct source ranks first. Aggregate baseline recovery is 3 correct / 3 proposed / 7 reference edges; gated recovery is 4/4/7. These are correlated within-article counts. All emitted edges in these two blocks agree with the structural reference; substantial correspondence remains unrecovered.

Both variants import the v5 threshold of 0.0447210756684702 without recalibration. The new blocks exceed it and have positive candidate margins, but link only one or two distinct FL atoms. The continuation has only two atoms and cannot satisfy the unchanged three-atom admission rule even with perfect recovery. The mechanism has five available atoms but only two linked. This distinction prevents treating the continuation's refusal as failure to identify its source.

No source-absent false admission occurs in either new-block control, in either variant. Source-absent controls remove the entire Models of Magic work. Two correlated controls do not estimate a general error rate.

## Alias evidence and token capacity

The [frozen annotations](../benchmarks/inputs/correspondence_v6_annotations.json) preserve every occurrence and compatible English word span. The saved diagnostic audit adds a one-to-one capacity check: if a reviewed FL atom has more occurrences of a proposed form than its corresponding English span has the proposed word, all occurrences cannot realize that identity simultaneously within the label. This conclusion is conditional on the structural span and editorial fidelity; it is not an independent semantic verdict.

| Proposed identity | Total occurrences in the three packets | Unequal-length presence only | Equal-length positional agreement | Proposed word absent from reviewed span |
|---|---:|---:|---:|---:|
| ńańi → of | 11 | 9 | 2 | 0 |
| daċċęįš → and | 6 | 5 | 0 | 1 |
| tawwdan → that | 5 | 1 | 2 | 2 |

The two continuation statements each have exactly the same token count as their source statements: 30/30 and 24/24. The four proposed **of/that** occurrences agree with English at the same token positions. This is stronger positional compatibility than word presence, but remains four observations from one work, under analyst structural references. It does not validate a semantic dictionary or establish an independent register.

All mechanism occurrences remain unequal-length presence evidence. Multiple English **of** positions remain unresolved; the audit saves all candidates rather than selecting convenient links.

The original premises atom retains one **and** and two **that** proposals with zero corresponding English occurrences. The count audit therefore retains a minimum of three unrealized aliases under that label. No new capacity contradiction appears in the selected blocks. Possible editorial changes and reference uncertainty remain alternatives to a semantic conclusion. The existing opening labels were retained exactly rather than repaired after viewing scores.

Reference-guided ordered token paths are saved separately from retrieved paths and explicitly marked as hypotheses unused by retrieval. Their one-to-one ordering and experimental alias origins are verified. They are not token truth or a semantic-accuracy benchmark. New supported lexical entries: **zero**.

## What blocks correspondence recovery

The diagnostics decompose each canonical reference block and each adjacent two-FL-atom union into length, punctuation, repetition, literal anchors, lexical overlap, blended score, and reward. They also record whether the span is actually available to the up-to-2:2 protected-unit proposal mechanism. This is a diagnostic probe using reference spans after retrieval is saved, not a reference-assisted scoring method.

| Reference proposal | FL/source tokens | Blended similarity, baseline → gated | Token-mass reward, baseline → gated | Observation |
|---|---:|---:|---:|---|
| Opening premises atom 1 | 41/38 | 0.6409 → 0.5431 | −0.1953 → −0.3884 | Aliases add three unmatched predictions; punctuation differs as well |
| Continuation atom 0 | 30/30 | 0.6650 → 0.7317 | −0.1025 → −0.0025 | Gated score exceeds floor but mass regularization still rejects the singleton |
| Both continuation atoms | 54/54 | 0.8309 → 0.8538 | +0.2315 → +0.2932 | Gated merge becomes stronger than the best singleton and yields both edges |
| Mechanism atom 0 | 16/26 | 0.6845 → 0.6845 | −0.0393 → −0.0393 | All emitted words occur in source, but length/structural agreement remains weak |
| Mechanism atom 2 | 20/35 | 0.6721 → 0.6721 | −0.0808 → −0.0808 | Large count difference and punctuation/repetition differences persist despite full lexical overlap |

The mechanism's source has parenthetical definitions and explanatory material whose literal/punctuation form differs from FL. Unknown FL replacements or semantic omissions are not resolved by this audit. Its final statement has equal token counts but different punctuation and still scores strongly; a punctuation mismatch alone is not sufficient to explain every failure.

Canonical and adjacent-union diagnostics have 11 feasible proposals for the opening, three for the continuation, and nine for the mechanism. Positive proposals number 4 → 5, 2 → 2, and 5 → 5 respectively. Some positive reference proposals are not selected by local alignment: the best surviving fragment can be stronger, and intervening gaps can wipe out an earlier positive fragment. Two opening unions require three source units and are outside the registered proposal scope.

In the mechanism, the first positive singleton has reward about 0.0866; the returned final two statements total about 0.2731 baseline or 0.2921 gated. Bridging the intervening third FL statement and corresponding English statement costs 0.35 + 0.6125 = 0.9625 under the fixed gap rule. The intact reference path therefore cannot simply join those fragments without loss. This explains the arithmetic for that path, not an independently identified causal effect of relaxing the gaps.

Inherited eligible predictions also conflict with specific reviewed spans: for example, **a/in** in continuation atom 0 and **a/of** in opening atom 3 lack sufficient English capacity. Their v1 eligibility is preserved; cross-work support does not guarantee applicability to every alternate-register span. The audit does not delete those predictions or add replacements.

## Order controls

Twenty shared nonidentity permutations were saved per packet, seed 6831, with repetitions allowed and windows recomputed.

| Packet | Unique orders / 20 draws | Shuffled maxima ≥ observed: baseline | Gated aliases |
|---|---:|---:|---:|
| Opening | 20 | 7/20 | 20/20 |
| Continuation | 1 | 20/20 | 0/20 |
| Mechanism | 16 | 5/20 | 5/20 |

The continuation has just one possible nonidentity order; twenty draws repeat it. The gated merged passage beats that reversed order, but this is one distinct comparison, not twenty independent negative cases or a calibrated p-value. The mechanism is only partially order-discriminative: five sampled permutations preserve a comparably strong surviving fragment.

## Verification and next experiment

One final execution completed in 7.45 seconds after **44 tests passed**. The [verification receipt](000006_verification.json) checks input/raw/code/output hashes, frozen v5 configuration and thresholds, exact opening regression, gates and origins, token offsets/order/uniqueness, edge support/counts, admissions, source-absent controls, permutation denominators, diagnostic cache-score agreement, capacity constraints, and unchanged experiments 1–5. No scoring change, lexical induction, or outcome-dependent rerun was performed.

The [immutable run report](../runs/000006_kamri_correspondence_audit/report.json) contains full rankings, token paths, and diagnostic decomposition. Replay requires the retained local data and a new run directory:

```sh
uv run python scripts/run_correspondence_v6.py --run-id replay_000006
uv run python scripts/verify_correspondence_v6.py
```

The next useful experiment is a controlled editorial-robustness test with fresh preregistered synthetic perturbations and matched scoring ablations. It should isolate structural count/punctuation changes and lexical conflicts, rather than expand the alias dictionary from this one article. Keep these real Misinfons blocks as development diagnostics, calibrate on a separate fixed panel, and retain full failures and denominators. Independent natural alternate-register transfer still requires an additional source work with auditable correspondence; none has been established here.
