# Experiment 57: shared numerals have thirteen occurrences and distinct local contexts

The complete audit contains **13 retained occurrences: seven in the target,
six in the reference**, over six shared numeric key types. The target has two
separate `180` occurrences: one followed by `°`, the other beginning the literal
`180- 1200 MHz` range. The reference's single `180` occurs in an English phase
description. A shared numeral alone therefore does not specify a unique local
context or equivalent quantity.

All thirteen original spans, fixed windows and review rows are accounted for.
The complete-text supplementary scan found **zero additional masked, boundary-
rejected or out-of-scope copies** of these six full numeric candidates. No new
score or alignment pair was chosen. E56 remains unchanged at reference **6**
versus comparator maxima **0, 1, 1, 0**. Quantity-correspondence and visual-glyph
gates remain **null**, and all opaque target contexts remain unresolved.

## Frozen selection and original-text provenance

The [registration](../experiments/numeric_context_v57.md), config and code/tests
were frozen with **114 input hashes**, all **56 prior manifests** and available
seals before new selection and annotations. The shared keys are derived from
the saved E56 inventory intersection in reference occurrence order: **96, 40,
1.3, 180, 2006, 7000**. The frozen inventories require seven target and six source
occurrences, retaining the repeated target `180` rather than assuming six pairs.
All material is exposed development data; some contexts appeared in prior
outputs and preparation. This is not blind annotation or independent review.

Every matching full numeric candidate in each complete original text was scanned
with the unchanged literal regex. Larger numbers, decimal variants and embedded
identifiers cannot be shortened to rescue a shared key. Original containing
units, mask reasons, boundary tests and mixed-anchor indices were retained.
Core membership exactly reproduces E56. The supplementary denominator is zero,
not an omitted set of masked observations.

Each occurrence has an exact **+/-120 Unicode-character window**, clipped at
document edges, and a separate original-unit-clipped view. The full window may
include nearby known English quotation text; that does not put the quotation
back into retained scope. All mask flags and clipped views remain available.
The narrow direct/range cue probe has a fixed **64-character horizon** and is
clipped to an original unit when one contains the numeral.

The target export exactly reproduces the saved **January 10, 2026 archival HTML
post-body capture**. Its saved bytes match the export's parent SHA-256 and the
recorded CDX digest; the prior dated-material gate remains intact. This is
archival raw HTML provenance rather than merely an indexed excerpt. It does
not authenticate the post's 2018 wording, current bytes or historical source
relationship. The reference reproduces the original v42 native HTML/receipt and
E52 parsed body/scope. These are text coordinates, not raw-byte or pixel offsets.

No network request, rendering, screenshot inspection, OCR or new export was
performed. **No visual glyph judgment is imported from the earlier PDF audit**:
these are different materials. Every glyph status remains not_visually_checked.
Matching an original parsed-text slice verifies text traceability, not what a
rendered glyph looked like or what the opaque words mean.

## Complete per-key context accounting

| Literal key | Target retained occurrences and observed notation | Reference retained occurrences and English context | What remains unresolved |
|---|---|---|---|
| 96 | 1; no direct registered marker | 1; radio-antenna count | Opaque noun/count correspondence |
| 40 | 1; `40 km` | 1; altitude with `km` | Referent and quantity correspondence despite the same marker |
| 1.3 | 1; no direct registered marker | 1; area described in million square kilometres | Opaque words are not assigned an area meaning |
| 180 | 2; `180°` and `180- 1200 MHz` | 1; phase description, literal `180˚` | Occurrence/context correspondence and symbol equivalence |
| 2006 | 1; `2006-2007` | 1; first-flight campaign/date context, `2006-7` | No endpoint expansion or opaque calendar interpretation |
| 7000 | 1; `7000 km` | 1; path through solid matter, with `km` | Referent and quantity correspondence |
| **Total** | **7** | **6** | **All cross-text quantity judgments unresolved** |

The table groups occurrences by literal key; it does not select six source-
target pairs. In particular, this audit does not choose which target `180`
corresponds to the source occurrence. E56 reported LCS lengths, not an ancestry
path. The two target contexts remain separate original observations.

All seven target review classes are **opaque_context_unresolved**. Literal `km`,
degree notation and range strings are recorded without assigning meanings to
adjacent opaque tokens. Same-marker presence is not proof that the objects,
quantities or passages correspond. The source-side classes describe explicit
English context, not independent verification of the publisher's factual claims.

## Fixed-rule limits retained after inspection

Two limitations surfaced and were preserved without revising the registration:

- The source's phase numeral is followed by **`˚` U+02DA RING ABOVE**; the earlier
  target occurrence uses **`°` U+00B0 DEGREE SIGN**. The registered automatic
  marker set contains only the latter. The source marker probe therefore remains
  null. Manual English-context review records angle_or_phase with exact text
  evidence, preserving the distinct source character. No normalization or visual
  equivalence is inferred.
- The source's **1.3 describes area**, not volume. The fixed source-context rubric
  omitted an area category. Its review stays **other_or_unresolved**, with a note
  identifying the explicit area wording and the rubric omission. It is not
  silently relabeled volume or given a new post-result category.

The six source classes are: **two distance_or_length, one discrete_count, one
angle_or_phase, one calendar_or_campaign_date, one other_or_unresolved**. The
marker probe is deliberately limited; absence from its output does not mean
that the surrounding text lacks a unit or quantity role. The original windows
preserve all evidence beyond that probe's vocabulary.

The literal range spellings `2006-2007` and `2006-7` are kept distinct. No omitted
digits are expanded, and no opaque year or campaign meaning is projected from
the English source. Likewise, the target's `180- 1200 MHz` is recorded as an
explicit numeric-range surface, without translating the surrounding sentence.

## Verification, limits and next boundary

**433/433 workspace tests** and **394/394 isolated-public-export tests** pass;
the same 39 archive-dependent tests remain excluded publicly. Six new fixtures
cover repeated candidates across all four status classes, full-number/decimal
boundaries, exact direct/range cues and unit clipping, stale core inventories,
complete exact review evidence, forbidden semantic/glyph promotion and one
literal key with multiple marker contexts.

The [separate verifier](../scripts/verify_numeric_context_v57.py) reconstructs
the archival/native parent texts, all thirteen candidates, mask/unit/boundary
accounting, every context window and every literal cue. Its marker probe uses
an explicit token-list traversal rather than the production regex. It checks
complete review coverage, exact evidence slices, summaries and all **56 previous
runs and deliverable seals**. It makes zero requests. See the
[verification receipt](000057_verification.json).

The verifier validates annotation traceability and allowed classes; it does not
independently ratify the same-agent context judgments. BeautifulSoup parsing is
shared. No rendered glyph, English-to-opaque word meaning, quantity equivalence,
immediate source identity, independent review or untouched unit is validated.
All earlier score, intake and synthetic failure results remain fixed. Natural-
benchmark capacity stays unmet; scientific acceptance and semantic metrics stay
null.

Next bounded step: register a **harder-comparator feasibility intake** with fixed
request budgets, retaining the native date/title/scope requirements and requiring
at least three shared literal numeric key types in a prospective quote-masked
scope. E56's four comparators had at most one, so further weak-overlap pages
cannot resolve its order-specificity limitation. Preserve every failed or empty
slot and stop at the declared budget if no closer candidate is found. A closer
candidate would remain development data with uncertified source/false-parent
status. No such acquisition, marker-list change, rubric change or rescoring was
performed in E57.
