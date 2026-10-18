# Step 29: Risk source-layout derivative passes its engineering checks

The separately registered derivative resolves the specific layout failures recorded in v28: **one rotated margin lane replaces 26 fragments, both visible footnote separators are detected, and the page-2/page-3 main-text continuation is recorded without joining it**. Every one of the **7,246 extracted PDF character records** belongs to exactly one line and one source-linked piece. All four registered engineering components pass, followed by visual inspection of the three original pages and independent reconstruction. All **231 tests pass**.

This is an engineering result on three already exposed development pages. It does not establish word meanings, translation quality, source identity, independent semantic review or general extraction accuracy. Semantic metrics and scientific acceptance remain null. All original packets, raw pypdf texts, v28 maps and 28 prior runs remain unchanged; v27's 0/3 literal result is not rescored.

## What the derivative preserves and changes

| Risk PDF page | Extracted character records | Derivative lines | Inferred spaces | Raster separators | Footnote-candidate lines |
|---|---:|---:|---:|---:|---:|
| 1 | 1,717 | 32 | 254 | 0 | 0 |
| 2 | 2,595 | 44 | 412 | 1 | 3 |
| 3 | 2,934 | 47 | 486 | 1 | 5 |
| Total | 7,246 | 123 | 1,152 | 2 | 8 |

The native glyph string concatenates extractor character text in PDF content order. Its offsets are a new explicitly named coordinate system, distinct from PDF bytes, v27 pypdf text and the legacy publisher window. Every glyph piece links derivative offsets to its native index/string offsets and saved font, matrix and bounding box. Sorting glyph pieces by native index reconstructs that native string exactly. The 1,152 inferred ASCII spaces and 123 line-ending newlines have separate synthetic records; these account for the derivative's 8,521 code points without inventing source-character offsets for inserted text.

Character grouping uses anchored baselines instead of words split by font size. Smaller superscript groups can attach to nearby larger baseline groups under the frozen geometry rule; their digits and original geometry remain. Gaps determine synthetic spaces, with explicit whitespace retained. Ligatures, spelling, punctuation, citation digits and line/page-edge hyphens remain unchanged. No dictionary, OCR, spelling repair, citation deletion or vocabulary-based grouping is used.

The first page's 48 rotated characters form a single bottom-to-top lane. Its arXiv identifier/date reads in the expected order, including the original double spaces. The margin is appended after upright lines in the derivative; this explicit lane ordering differs from the older pypdf export. It remains separately identified and is not treated as article body. Title, author, abstract and section headings remain visible but mostly have `body_or_unresolved` hints; the derivative does not supply a full semantic document hierarchy.

The unchanged raster pages expose separators that the v28 vector-edge inventory did not capture. The selected raster bounds map to PDF top coordinates **635.333333 on page 2** and **618.666667 on page 3**. Three and five smaller-font lines below those separators receive footnote-candidate hints. Visual comparison with the complete page images confirms the two note regions and the preserved note markers. These are validated layout expectations on known fixtures, not independently labeled linguistic data.

The continuity ledger links page 2's final body line ending in `as-` to page 3's first body line beginning `tronomy`, excluding the intervening note and header hints. Both line texts and offsets remain separate; no joined word is created. Page 1 to page 2 does not qualify under the fixed hyphen/lowercase rule. Footnotes are not automatically linked across pages.

## Concordance remains incomplete

| Representation | Lines | Raw-page matches: unique / ambiguous / unmapped | Legacy-window matches: unique / ambiguous / unmapped |
|---|---:|---|---|
| v28 Risk geometry | 148 | 45 / 3 / 100 | 54 / 6 / 88 |
| v29 Risk derivative | 123 | 47 / 2 / 74 | 60 / 2 / 61 |

These are full-line normalized-token concordances with exact raw target spans. The line denominators and line contents differ; the table is not a calibrated extraction-recall comparison. The frozen rule preserves every possible occurrence, including short incidental matches, and makes no first-match selection. An unmapped line does not prove deleted text or missing semantic content.

The saved pypdf text visibly contains intraword spacing differences such as `form alism` and `t o`, while the corresponding derivative lines read continuously in agreement with the displayed page. Literal ligatures and split words are also retained, and the legacy text has its own representation differences. This audit does not assign every unmatched line to a unique cause or try another normalization after seeing the counts. Original pypdf/legacy offsets remain available only through the recorded exact concordances, rather than an asserted universal one-to-one conversion.

All **24 bracketed numeric citation occurrences** have matching key multiplicities in the derivative and the corresponding raw page: 2, 7 and 15 on pages 1–3. This covers the registered comma-separated numeric pattern only. Superscript markers are preserved as native glyphs but are not counted as bracketed citations. The old legacy export's missing bracketed forms remain unchanged. The visible `pos-` / `sibile` line break and `possibilites` spelling are preserved, without revisiting the earlier anchor results.

## Verification and evidence limits

The machine registration and 181-file code/input seal precede primitive extraction. Frozen primitives and benchmark precede the one derivative run. A same-assistant visual receipt follows execution and records comparison of all 123 full derivative lines with the three complete original page images. No code, parameter, role hint or original text changes after execution.

The separate verifier imports no primary derivative code. It re-extracts all character primitives and independently scans raster rows; it rebuilds anchored groups, superscript attachments, reading order, spaces, glyph pieces, roles, all-occurrence concordances, citation inventories, summaries and page-edge records. It independently checks native and derivative accounting, replays all four gate components and validates the prior 28 run inventories and earlier deliverable seals. The [receipt](000029_verification.json) confirms the combined automatic-plus-visual engineering gate passes. Independent implementation replay is not independent semantic review.

The complete-accounting result is relative to pdfplumber's extracted character inventory. It is not proof that every visual PDF object or possible reading order was recovered. Spacing is inferred, role hints remain provisional, raster rules depend on these fixed legible page images, and the grouping algorithm has not been validated on unexposed works. All unresolved concordances remain in the output.

No network acquisition, new publisher page, FL alignment, model, target rescore or external message occurs. Source identities, semantic labels, independent-review admissions and untouched-test admissions remain zero.

## Stopping boundary

Step 29 stops with this versioned derivative and its known limitations. The specific layout prerequisite for these three Risk pages is satisfied; do not keep tuning it against old scores or replace earlier representations silently.

The next research step is to **freeze paragraph-bounded FL/source candidate units and preregister a correspondence diagnostic**. Use v28's explicit paragraph boundaries to avoid the earlier context spill into bibliographic entries; preserve unresolved roles and the derivative's footnote/margin distinctions. Before scoring, specify what observation beyond copied anchors would support the prediction, which same-work alternatives and source-absent/copied-anchor controls could defeat it, and when to abstain. A nonliteral metric needs an independently assessable prediction; an AI's plausible gloss is not semantic gold. These exposed pairs can support a diagnostic, while independent semantic acceptance and genuine held-out validation remain separate requirements.

Artifacts: [registration](../experiments/risk_layout_derivative_v29.md), [machine plan](../experiments/risk_layout_derivative_v29.json), [preflight seal](../data/v29/preflight.json), [PDF/raster primitives](../data/v29/primitives.json), [benchmark](../benchmarks/risk_layout_derivative_v29.json), [source-linked pages](../runs/000029_risk_layout_derivative/pages.json), [continuity ledger](../runs/000029_risk_layout_derivative/continuities.json), [full layout review sheet](../runs/000029_risk_layout_derivative/layout_review.md), [page 1 text](../runs/000029_risk_layout_derivative/risk_math_001.txt), [page 2 text](../runs/000029_risk_layout_derivative/risk_math_002.txt), [page 3 text](../runs/000029_risk_layout_derivative/risk_math_003.txt), [run report](../runs/000029_risk_layout_derivative/report.json), [visual receipt](../data/v29/visual_review.json), [verification](000029_verification.json), and [deliverable seal](000029_deliverable_seal.json).

Verify offline with `.venv/bin/python scripts/verify_risk_layout_v29.py`; run tests with `.venv/bin/python -m unittest discover -s tests -q`. Extraction and execution refuse existing outputs; verification preserves its successful receipt.
