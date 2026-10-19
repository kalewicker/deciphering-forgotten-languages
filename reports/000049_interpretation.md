# Experiment 49: publisher comparison survives the registered citation mask

The publisher's sealed numeric LCS of **6** still exceeds both paper maxima
after the document-wide citation mask. The strongest 11-numeric-anchor window
scores **1** in each paper, versus **1 and 2** in the original whole-text v47
comparison. The registered descriptive sensitivity criterion passes for these
two exposed candidate papers.

This supports robustness to this particular mask. It does not establish an
immediate source, meanings, calibrated confidence or specificity over a broad
same-topic collection. The masked ANITA paper's own order criterion remains
**false**: four filtered controls exceed its observed best-window score.

## Frozen masks and unchanged comparison rules

The [registration](../experiments/citation_sensitivity_v49.md), config, scoring
code/tests and **107 input hashes** were fixed before masking or scoring.
Reference boundaries were selected by structural inspection of saved text and
page images beforehand, without new scores: *Neutrino Radar* page 7 offset
**1013** begins the References heading; the ANITA paper page 13 offset **1382**
begins reference [1] after acknowledgments. Exact boundary needles, offsets and
image identities were frozen. Each mask extends through the complete document
tail, including later reference pages and footers.

The second rule scans every original page for syntactic numeric bracket
singletons/lists/ranges, including comma/semicolon separators and ASCII hyphen,
en dash or minus. Each match before the reference boundary is masked; matches
inside the reference tail remain in the candidate ledger as already covered.
Spaces/newlines within a page are allowed. No broken cross-page bracket is
repaired, range expanded or digit normalized. This may mask numerical intervals
and miss other citation forms; it is a reproducible syntactic sensitivity rule,
not independently certified citation segmentation.

Every full v47 inventory was reconstructed identically before filtering. Masks
operate on original coordinates and remove all overlapping numeric/uppercase
anchors, regardless of target overlap. Original spans, page-local coordinates
and old indices remain recorded; dense retained indices support bookkeeping.
No mask-edited text was rescanned, so removed characters cannot manufacture
identifier fragments. All **8 and 15 page units** remain, including pages with
zero retained anchors. No PDF extraction, rendering, OCR or acquisition occurred.

| Paper | Reference-tail characters masked | Inline numeric-bracket masks | Mixed anchors before / after | Numeric anchors before / after |
|---|---:|---:|---:|---:|
| *Neutrino Radar* | 2351 | 12 | 164 / 51 | 156 / 47 |
| ANITA anomalous events | 14257 | 126 | 1604 / 1091 | 1182 / 717 |

The original masked target, its **10 numeric occurrences**, literal extractor,
publisher score **6**, numeric window budget **11** and original control seed
are unchanged. Paper quotation/table/header scope remains broader than the
publisher's scoped, quotation-masked HTML; this experiment does not equalize
document genre, text length, information content or historical-version evidence.

## Complete result and prior comparison

| Paper | Shared distinct types before / after | Whole-document LCS before / after | Windows before / after | Best 11-anchor window before / after | Masked tied-best starts |
|---|---:|---:|---:|---:|---:|
| *Neutrino Radar* | 1 / 1 | 1 / 1 | 146 / 37 | 1 / 1 | 11 |
| ANITA anomalous events | 5 / 3 | 4 / 2 | 1172 / 707 | 2 / 1 | 44 |

Masked bag capacities are **1 and 3**. Retained shared keys are **40** in the
first paper and **96, 180 and 2006** in the second. Every contiguous window,
index list, score and tied maximum is retained in the local
[scope/inventory/assessment ledgers](../data/v49/). Windows may cross pages or
join anchors separated by masked material. Equal anchor budget is not equal
textual distance. Removing nonmatching anchors can increase window scores by
compressing that distance; a fixture explicitly tests this possibility.

Both comparisons retain at least 11 numeric anchors and pass functional checks.
The registered criterion therefore remains eligible and passes: **6 > 1** for
both papers. Historical v47 metrics are copied into the comparison ledger;
their artifacts and scores were not replaced or rewritten.

The v48 containment ledger accounts for every one of the **13 visually audited
occurrences**: **5 retained, 8 removed**. The seven reference-list occurrences
are removed by the complete tails and the prose citation [40] by the syntax
rule. The table date year and four other prose occurrences remain. This is a
post-mask accounting readout, not a target-key-dependent mask-selection rule.

## All original control draws retained

Every original v47 permutation was filtered through the same mask, preserving
family/draw ID and complete page order. The reduced inventories were **not
reshuffled**. There are **zero new random control draws**. Original indices were
filtered and remapped to dense retained indices; every retained mixed-anchor
bag and index inventory is preserved. All 34 cases per paper remain, including
any ties, duplicates or identities. No identity case occurred after filtering.

| Masked paper | Observed best window | Global reversal | Within-page reversal | 16 filtered anchor shuffles max | 16 filtered page shuffles max | Ties | Controls greater | Secondary order criterion |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| *Neutrino Radar* | 1 | 1 | 1 | 1 | 1 | 34 | 0 | Null: one shared type |
| ANITA anomalous events | 1 | 1 | 1 | 2 | 2 | 30 | 4 | False: eligible, controls exceed observation |

All controls receive the same exhaustive window search. Sparse/null and
eligible/false outcomes remain visible. No p-values, confidence levels, source
probabilities or estimated false-positive rates are inferred from these finite
controls or the repeated exposed-pair sensitivity tests.

## Verification, limits and next step

**373/373 full-workspace tests** and **334/334 isolated-public-export tests**
pass; the same 39 archive-dependent tests are excluded publicly. Seven new
fixtures cover reference tails, supported/unsupported bracket syntax and page
breaks, identity failures, original boundaries, dense/original index mapping,
filtering the actual parent draws rather than regenerating them, empty pages/
identity retention and the possible increase in a compressed-window score.

The [separate verifier](../scripts/verify_citation_sensitivity_v49.py) rebuilds
masks with a character grammar rather than the production bracket regex. It
reconstructs every retained/removed anchor, all **68 original parent control
draws and their filtered orders**, and all **26,040 window scores** with full-
table LCS DP. It verifies all 13 audited-occurrence retention rows and all
**48 previous runs and deliverable seals**. See the
[verification receipt](000049_verification.json) and local
[immutable report](../runs/000049_citation_sensitivity/report.json).

This is same-agent engineering verification, using the same saved exports and
literal-number definition. It is not independent scientific review, a new glyph
audit or proof that the masks perfectly separate citations. Two new structural
sensitivity comparisons perform zero opaque lexical/semantic scores. No meanings,
immediate source identities, independent reviews or untouched natural units are
admitted. The failed synthetic source-absence gate is unchanged. Natural-
benchmark capacity stays unmet; scientific acceptance and semantic metrics null.

The main remaining specificity limitation is the candidate collection: two
cited scholarly papers are a narrow, differently formatted comparison to a
publisher article already selected through English quotation evidence. Further
numeric rule variants on this same exposed pair would not fix that limitation.

Next bounded step: register an intake of additional same-topic **publisher
articles**, with queries, dates, eligibility, exposure/exclusion records, candidate
cap and request budget fixed before browsing. Preserve first-eligible selections,
failed requests and empty slots without substitutions. Resolve capture and scope
feasibility before any scoring. These would be alternative candidates, not
certified false parents or independent natural test works; no acquisition or
new source selection is part of the present experiment.
