# E96: one offered Burton representation and bounded page-specific wording test

Fixed claim: candidate 01, second source-catalog bullet, all 22 prose renderings.
Freeze package pair ordinals 2..23 as the proposed prose subset, excluding ordinal
1 as the separately claimed heading. This assignment is our explicit test
hypothesis, not an author-supplied ordinal map. Preserve all 22 and their English
spans; no favorable unit selection. Source order claimed: printed pages 254–256,
then 252–253. No independent translation validation is implied.

Acquire only the exact catalog-offered Gutenberg plain-text URL ending
/cache/epub/57208/pg57208.txt. One anonymous GET, no redirects, no cookies or
credentials, 30-second socket timeout and 60-second overall deadline; maximum
8 MiB body plus one byte for oversize detection. Preserve intent, response headers,
body and errors before decoding. Non-200, oversized, encoded or undecodable bodies
fail intake. Use strict UTF-8, retaining a possible BOM in the original string.
No second edition, HTML version, mirror, retry or endpoint search. A sandbox access
failure may be escalated for that same command, never hidden as a successful GET.

Before any wording search, inspect at most the first 10,000 characters for edition
metadata, and inventory candidate explicit page markers throughout the text.
Recognized locator candidates are bracketed/brace-delimited integer labels with
optional Pg/Page/p prefix, or standalone integer lines. Retain every marker span
and count. Do not treat arbitrary bracketed footnote numbers as pages. Manual
page-binding judgment must be documented using coherent page sequencing and
explicit pagination context, with ambiguous candidates left unresolved.

Require a unique, credible run of page boundaries 252,253,254,255,256,257 to bind
both complete ranges; inspect marker context only (up to 150 characters each)
to assess pagination. Require header identity compatible with the named Burton
work and edition metadata retained. Do not infer page boundaries from target
wording. If this representation cannot establish the printed-page windows,
stop as page-binding unresolved: comparison not executed, match counts null.
Do not search the whole book or substitute a passage found by matching targets.

If page binding is established, save exact source spans for pages 254–256 and
252–253. Freeze a fixture-tested comparison runner and binding ledger before
searching those spans for target wording. Compare every English target literally,
and separately under whitespace collapse only. Report every occurrence and greedy
ordered nonoverlapping coverage in the prescribed two-window order; do not permit
matches spanning the artificial jump between ranges. No punctuation, case, accent,
spelling, hyphenation or fuzzy repair. Missing units remain misses. Preserve offsets
in original and diagnostic coordinate systems. All 22 units stay in the denominator.

Stop after this one acquisition/intake/page-binding decision and, only if admitted,
one bounded comparison. No source expansion, controls selected after results,
lexicon/model work or semantic benchmark admission. This tests a catalog wording
claim, not unique source identity, opaque meanings or translation accuracy. Raw
source text, package English, URLs and ledgers remain local-only; publish aggregate
status and reproducibility code. Prior sealed artifacts remain unchanged.
