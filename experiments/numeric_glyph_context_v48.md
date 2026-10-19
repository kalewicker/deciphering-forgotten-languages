# Experiment 48: fixed numeric glyph and context audit

Question: do all 13 saved PDF numeric occurrences sharing a masked-target literal
key in v47 agree with the original page images, and what visible context contains
each occurrence? This is an exposed, same-agent representation audit. It does not
rescore v47, alter source/target masks, interpret opaque FL words or establish
source identity. Prior outcomes and every previous artifact remain fixed.

Before opening page images or reading source context in this audit, freeze the
config, code/tests, v47 reference and both inventories, both original PDF bytes/
page exports, all seven original page-image hashes, and all 47 prior manifests
and seals. Selection is exhaustive over saved source inventory rows of kind
number whose exact key belongs to the saved v47 masked-target numeric inventory.
Keep every occurrence, repeated key, exact global/page span and mixed-anchor
index. Stable ID is source ID plus original mixed-anchor index. Require the
predeclared denominator of 13 occurrences on seven document/page pairs (1 on
one page for Neutrino Radar, 12 on six pages for ANITA anomalous events). If scope
or identity fails, stop unavailable; do not choose substitutes.

No new PDF extraction, OCR, rendering, downloads, external review or scoring.
Reuse the saved PNGs, checking bytes against the original export hashes. Inspect
each complete selected page, not only a search highlight. Crops or magnification
of the same pixels may clarify a glyph; retain their provenance locally if used.
For each selected occurrence preserve the unchanged +/-120-character page-text
window (clipped at page edges), then locate its corresponding image occurrence
using nearby words, column and section. Do not infer visual identity merely from
matching digits elsewhere on the page. If duplicate or layout ambiguity prevents
mapping the exact occurrence, mark ambiguous even when the digits are legible.

Record one review row per frozen ID: original image hash, visible_literal,
glyph_status, context, locator, context_detail and note. Glyph status is one of
literal_match (same digit/punctuation sequence, independent of font/superscript),
serialization_mismatch (mapped occurrence differs), unreadable or ambiguous.
Literal matches require exact visible_literal equality to the frozen value;
mismatches require a different nonempty literal. Do not normalize any punctuation.
Unreadable literals are null. Context categories are prose, figure, table,
header, reference or ambiguous. Inline citation markers remain prose with that
role stated in context_detail; a reference-list item remains reference. Record
visible role, not whether the quantity means the same thing as an FL number.
Keep glyph and context judgments separate. Surrounding equation notation,
typesetting, column order and bibliographic years may matter to the note.

All 13 rows are mandatory; no omitted or duplicated IDs, replaced image hashes,
invalid category, empty locator/detail/note or unresolved status may disappear
from the denominator. The descriptive glyph-agreement gate is true only if all
13 are literal matches, false if any serialization mismatch, otherwise null for
unreadable/ambiguous rows. Context completeness is reported separately and cannot
rescue a glyph gate. Report all status/context counts and source breakdowns.
Any mismatch is retained and requires a new registered correction before future
rescoring; v46/v47 results are not rewritten.

Fixture checks before review: exhaustive repeated selection, page/global span and
text/image hash identity, complete ID coverage, deliberate mismatched glyphs,
ambiguous/unreadable propagation and independent context classification. After
review, a separate verifier reconstructs the selected rows/context slices from
old inputs, validates the ledger and arithmetic, checks all prior manifests/seals
and preservation of old scores. It cannot independently verify a visual judgment;
report that limitation rather than calling this independent review.

This is one 13-occurrence visual representation audit, zero new structural,
lexical or semantic scores. No meanings, immediate source identity, independent
review or untouched natural units are admitted. Scientific acceptance and semantic
metrics stay null. Seal report/evidence, run full/public checks, checkpoint local
evidence and commit/push only appropriate public files on main.
