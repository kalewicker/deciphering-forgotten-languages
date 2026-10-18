# Audit 28: exact export maps with unresolved PDF layout and coverage

The structural audit passes its registered engineering checks: **both archived FL bodies reconstruct their existing exports exactly**, every one of **2,950 PDF words on eight fixed pages** belongs to exactly one layout line, and all **16 FL references and nine legacy-source reference spans** retain valid original offsets. Independent reconstruction agrees with the saved maps and verifies preservation of all 27 earlier runs. All **219 tests pass**.

This audit exposes boundaries and representation differences; it supplies no linguistic acceptance criterion. Source identities, semantic labels, independent-review admissions and untouched-test admissions remain zero, and semantic evaluation metrics remain null. The automated findings and appendix remain project-exposed observations. No network request, new page, text repair, target rescore or translation occurs.

## Archived HTML: exact offsets, limited structural roles

| Work | Flat code points | Saved export including final newline | Text atoms | Paragraph block runs | Join spaces |
|---|---:|---:|---:|---:|---:|
| Western esoterism | 6,709 | 6,710 | 66 | 27 | 65 |
| Risk mathematics | 10,412 | 10,413 | 55 | 28 | 54 |

Atoms, join spaces and the final newline partition each saved export exactly. The maps preserve decoded DOM strings, trimming bounds, parsed DOM paths, ancestor tags, link/emphasis metadata and zero-text events: Western has five images and thirty line breaks; Risk has four images and twenty-eight line breaks. DOM paths describe the registered parsed/filtered HTML tree, not raw HTML byte positions or a browser rendering.

Every nonempty block run has paragraph markup. Neither body has an explicit blockquote, heading, list or navigation run under the registered owner rule; neither has a link-only run. These observations do not establish that all paragraphs serve the same purpose. In particular, bibliographic-looking entries and related-post references remain in the full export and are not discarded or automatically assigned semantic roles.

All four previously reported English blocks R5–R8 map within individual Risk paragraph runs, b007, b010, b015 and b019. Their quotation-like text does not become explicit quotation markup. Their presence or literal noncorrespondence to the fixed publisher window cannot establish translated coverage.

All three frozen v27 contexts cross paragraph runs:

| Context | Original FL export span | Intersecting runs | Boundary observation |
|---|---|---|---|
| Western names | [1269,1835) | b004–b005 | Includes parts of two paragraphs |
| Western Saturn | [4244,5065) | b009–b011 | Extends into the entry beginning with Agrippa's name and bibliographic details at offset 4893 |
| Risk spellings | [3006,3690) | b011–b012 | Includes parts of two paragraphs |

These are descriptive maps of the existing forty-token extensions, not revised queries. The v27 0/3 literal result and its original limits remain unchanged. The explicit boundary evidence will help avoid mixing article context and bibliographic entries in a separately registered follow-up.

## Publisher pages: complete word accounting, incomplete concordance

| Fixed page set | Geometry lines | Raw-page concordance: unique / ambiguous / unmapped | Legacy-window concordance: unique / ambiguous / unmapped |
|---|---:|---|---|
| Western PDF 90–94, printed 65–69 | 170 | 149 / 3 / 18 | 140 / 12 / 18 |
| Risk PDF 1–3 | 148 | 45 / 3 / 100 | 54 / 6 / 88 |
| Total | 318 | 194 / 6 / 118 | 194 / 18 / 106 |

Each line is searched using the registered normalized Unicode token sequence, preserving all returned exact target spans. Punctuation is ignored; digits, split words, spacing-dependent token boundaries and order are not repaired. Consequently, an unmapped line can reflect segmentation, extraction or ordering differences, rather than deleted text. These counts measure this mapping procedure, not semantic coverage or extraction recall. Even unique normalized matches do not establish a meaningful paragraph correspondence.

Twenty lines on Western pages 91–94 receive footnote-candidate hints below four selected separators. Inspection of all eight unchanged page images finds those candidates consistent with the visible note regions. Western note 72 continues from page 93 to 94, and page-edge main-text continuations remain separate; the audit does not automatically join either.

**Risk's layout mapping has material retained limitations.** Pages 2 and 3 visibly contain bottom footnotes and separators, but their extracted horizontal-edge inventories are empty. The frozen procedure therefore returns no footnote candidates on those pages and leaves the notes in `body_or_unresolved`. Page 3's header/page number is also unresolved. The first page's rotated arXiv margin is retained but fragmented into 26 line groups by the horizontal grouping rule. Font-size hints do not fully identify title/abstract/heading semantics. No hints or rules were corrected after visual inspection. The [post-run visual receipt](../data/v28/visual_review.json) records these misses page by page; it is same-assistant QA, not independent semantic review.

The restricted citation inventory finds **24 bracketed numeric marker occurrences in Risk's saved raw page texts: 2, 7 and 15 on pages 1, 2 and 3**. None has a matching whitespace-normalized bracket key in the legacy publisher-window export. Thus those bracketed forms are unrepresented there. This does not show that every referenced claim, number, or citation style was lost. Western has zero occurrences matching this specific bracketed-numeric pattern; its superscript footnotes are outside the pattern's scope.

## Reference maps preserve uncertainty

All sixteen FL spans map to their original atoms and block runs. Eight of nine legacy-source reference spans intersect at least one line's legacy concordance occurrence, while R3 (`possibile`) has none. These intersections are candidates only; they do not validate the reported page or source hypothesis.

R2 illustrates why the eight-of-nine count is not a success rate: its only candidate is a one-character overlap, `a`, from a fragmented rotated line on Risk page 1, although the reported reference page is 2. This is an incidental short-token collision, not evidence that the reference belongs on page 1. The frozen map retains it without using the reported page to filter it. Likewise, R3's unmapped status does not establish absence of the word from the source. Full intersection records, including every quote and offset, remain available for inspection.

## Verification and stopping boundary

The registration and 176-file code/input preflight precede PDF geometry extraction; the geometry and benchmark are frozen before the audit run. Visual QA follows mapping and does not alter it. A separate verifier independently rebuilds DOM traversal/offset/group maps, line grouping/roles, Unicode concordance, numeric citation inventories, reference intersections and summaries. It re-extracts all PDF word/edge primitives using the pinned runtime and checks the prior 27 run inventories and earlier deliverable hashes. The [verification receipt](000028_verification.json) passes. Independent implementation replay verifies bookkeeping; it does not provide an independent linguistic reviewer.

Audit 28 stops here. The next bounded step should be a **separately registered source-layout derivative**, focused on Risk's unresolved footnote regions, rotated margin and fragmented line concordance. Preserve the current maps, raw page text, images, legacy exports and offsets; any improved representation needs explicit links back to original characters/geometry and visible unresolved cases. A replacement must be checked for complete accounting and page/footnote continuity before use in downstream correspondence scoring. Do not silently relabel the present hints or rescore v27.

After that representation check, a nonliteral test still needs a separately specified, independently assessable prediction. Paragraph boundaries, bibliographic entries and copied names do not supply word meanings. Independent external review remains pending; genuine held-out evaluation requires unexposed source works and frozen predictions.

Artifacts: [registration](../experiments/kamri_block_audit_v28.md), [machine plan](../experiments/kamri_block_audit_v28.json), [preflight](../data/v28/preflight.json), [geometry](../data/v28/pdf_geometry.json), [benchmark](../benchmarks/kamri_block_audit_v28.json), [HTML maps](../runs/000028_kamri_block_audit/html_maps.json), [PDF maps](../runs/000028_kamri_block_audit/pdf_maps.json), [FL references](../runs/000028_kamri_block_audit/fl_references.json), [source references](../runs/000028_kamri_block_audit/source_references.json), [summary](../runs/000028_kamri_block_audit/summary.json), [Western sheet](../data/v28/maps/western_esoterism_html.md), [Risk sheet](../data/v28/maps/risk_math_html.md), [PDF layout sheet with unchanged page images](../data/v28/maps/pdf_layout.md), [immutable run report](../runs/000028_kamri_block_audit/report.json), [verification](000028_verification.json), and [deliverable seal](000028_deliverable_seal.json).

Verify offline with `.venv/bin/python scripts/verify_block_audit_v28.py`; run tests with `.venv/bin/python -m unittest discover -s tests -q`. Extraction and execution refuse existing outputs; verification preserves its successful receipt.
