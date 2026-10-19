# Experiment 48: all 13 selected numeric glyphs agree; contexts differ

All **13 frozen numeric occurrences** agree with the digit sequences visible in
their original saved PDF page images. All seven complete pages were inspected;
each occurrence maps to nearby words, a column/section and its original saved
page-text span. No mismatch, unreadable glyph or unresolved occurrence mapping
was recorded. The descriptive glyph-agreement criterion passes.

Context is a separate finding: **7 occurrences are in reference lists**, **1
is in a table**, and **5 are in prose**, including one inline citation marker.
Thus literal digit agreement does not imply corresponding quantities or meanings
in the FL post. This is a same-agent visual representation audit, not an
independent scientific review, source identification or a translation result.

## Fixed selection and visual method

The [registration](../experiments/numeric_glyph_context_v48.md), code/tests,
config and 97 input hashes were frozen before source-context inspection and
opening the seven images in this audit. Selection exhaustively includes every
v47 paper inventory occurrence of kind number whose exact key belongs to the
unchanged masked-target numeric inventory. Repeated keys and occurrences remain
distinct; no best-window selection was used. The denominator was fixed at **1
occurrence on 1 page** for *Neutrino Radar* and **12 on 6 pages** for the ANITA
anomalous-events paper. Saved global/page spans, anchor indices and image hashes
were preserved, with unchanged +/-120-character page-text context slices.

The original PNG bytes were checked against the original page exports and
inspected using `view_image`. Complete-page views were sufficient; no crops,
new rendering, OCR, extraction or downloads were used. Image identity is a byte
check, not authentication of the historical PDF version. Earlier exposure to the
papers and their images is not erased by this frozen selection.

Each observation records a visible literal, glyph status, context category,
image hash, occurrence locator, context detail and note in the local
[review ledger](../data/v48/review_ledger.json). Matching digits elsewhere on a
page were not used as substitutes. Repeated years were located by reference
item and neighboring journal/page information. Font size, superscript notation
and adjacent units/brackets do not change a literal digit sequence; they are
recorded as context rather than interpreted as FL semantics.

## All occurrence outcomes

Every row below has glyph status `literal_match`; none was dropped or replaced.
Source IDs and anchor indices are frozen v47 mixed-anchor indices, not newly
assigned numeric positions.

| Source / anchor index | Saved page | Literal | Context | Visible role / locator |
|---|---:|---:|---|---|
| Neutrino Radar / 30 | 4 | 40 | Prose | Opening paragraph, distance followed by km |
| ANITA anomalous / 121 | 2 | 2006 | Table | Table I, year at start of event date |
| ANITA anomalous / 382 | 4 | 96 | Prose | Lower left column, horizon expression with degree sign |
| ANITA anomalous / 675 | 7 | 180 | Prose | Lower right column, angular-range endpoint with degree sign |
| ANITA anomalous / 890 | 9 | 40 | Prose | Left column near bottom, inline citation [40] |
| ANITA anomalous / 985 | 9 | 96 | Prose | Right column near bottom, confidence percentage |
| ANITA anomalous / 1434 | 14 | 2007 | Reference | Publication year in reference [35] |
| ANITA anomalous / 1458 | 14 | 40 | Reference | Reference-list item label [40] |
| ANITA anomalous / 1497 | 15 | 2007 | Reference | Publication year in reference [46] |
| ANITA anomalous / 1508 | 15 | 2006 | Reference | Publication year in reference [48] |
| ANITA anomalous / 1542 | 15 | 2007 | Reference | Publication year in reference [54] |
| ANITA anomalous / 1548 | 15 | 2006 | Reference | Publication year in reference [55] |
| ANITA anomalous / 1554 | 15 | 2007 | Reference | Publication year in reference [56] |

The seven reference-list occurrences comprise six publication years and one item
label. The prose citation marker is counted as prose under the registered rule,
with its citation role explicit. The date year is counted as table context.
No selected occurrence has figure, header or ambiguous context. These are visible
source roles; no judgment of equality with an opaque-target quantity is made.

The gate requires all 13 literal matches; a mismatch would force false, while
unreadable/ambiguous glyphs without a mismatch would yield null. Here it is true,
and context completeness independently passes. This does not certify all other
PDF anchors, all reading order, all character extraction or the text's semantic
interpretation. No quantity normalization or source text repair was performed.

## Checks and limits

**366/366 full-workspace tests** and **327/327 isolated-public-export tests**
pass; the same 39 archive-dependent tests are excluded publicly. Six new fixture
tests cover exhaustive repeated selection, clipped contexts, text/image/span
identity failures, missing/duplicate/new IDs, deliberate glyph contradictions,
mismatches overriding uncertainty, and separate glyph/context null accounting.

The [separate verifier](../scripts/verify_numeric_glyph_context_v48.py) rebuilds
all 13 selections/context slices and checks every original image hash, complete
ledger coverage, allowed categories, literal consistency and summary arithmetic.
It checks all **47 previous manifests and deliverable seals**, preserving all
old scores. It **does not independently verify the visual judgments**. The
reviewer is the same agent that prepared this research; no independent review
is admitted. See the [verification receipt](000048_verification.json) and local
[immutable report](../runs/000048_numeric_glyph_context/report.json).

This is one 13-occurrence representation audit with **zero new structural,
lexical or semantic scores**. The v46 publisher result and v47 comparison are
unchanged, including sparse/null and tied/false paper control outcomes. There
are no new meanings, immediate source identities, untouched natural test units
or calibrated probabilities. Natural-benchmark capacity stays unmet; scientific
acceptance and semantic metrics remain null.

Next bounded step: register a citation-masking sensitivity comparison of these
same papers, with document-wide reference-list and inline-citation masks fixed
before rescoring. Preserve the target, literal extractor, 11-anchor budget,
seed, all exhaustive windows and control draws. Freeze full source boundaries
without choosing only the matched occurrences above, and retain the whole-text
v47 results beside the new results. This would test how citation content affects
the comparison without treating digit matches as semantic correspondences.
