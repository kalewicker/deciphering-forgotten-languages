# E68: fixed post/PDF literal passage-presence screen

Register before matching or full-PDF extraction. The target post and its full
bibliography were exposed in E63-E67; E67 also exposed the PDF's first page.
Pages 2-15 have not been text-extracted or visually reviewed in this sequence.
This is a development feasibility screen of one cited work, not a blind source
prediction, semantic alignment or untouched evaluation. No network requests,
new candidates, alternate editions, threshold changes or replacement queries.

## Inputs and complete target scope

Use only E63 raw HTML, E64's unchanged 12,344-character body, E65's complete
original-coordinate owner-run inventory and E67's frozen arxiv:0812.0349v1 PDF.
Keep all 67 prior runs/seals and E66/E63 failed gates unchanged. Require the E67
PDF-available decision and original hashes. Require E65's unique disclosed
Aissen reference-tail boundary; missing/ambiguous scope is an unavailable result,
not permission to choose another boundary.

Every nonempty E65 direct-child owner run before that boundary whose original
HTML owner is div[align=justify] is a target block. Include all such runs without
language labeling, English selection, quotation marks, apparent relevance or
length exclusion. Retain one scope-ledger row for every nonempty owner run,
including excluded title/copyright/layout and reference-tail runs. Validate every
run's original DOM locator, body text and half-open Unicode span against unchanged
raw bytes/export. Repeated text remains distinct by DOM-derived coordinates.

The primary query is the entire whitespace-token sequence of each block. The
fixed secondary query set is every consecutive **12 whitespace tokens** wholly
within each block, overlapping at every token position. Retain duplicate queries
and every short block: blocks shorter than 12 have a primary query and zero
secondary queries, explicitly counted. Do not select a fragment after seeing a
match. All target/query spans map back to original E64 body coordinates.

## Source representation and matching

Extract all 15 PDF pages with unmodified pypdf extract_text(); require pypdfium2
page-count agreement and the fixed 15-page denominator, plus exact agreement with
E67's page-1 text. Retain each full page, its text SHA256 and character length.
Join page strings with a single newline, including empty pages. Preserve headers,
footers, references, footnotes, line-break hyphens and punctuation. Record source
page/document offsets and every whitespace token. Empty/unextractable pages or
parser/count failure make representation/control readiness false; do not replace
text with OCR, another parser's text, screenshots, or another PDF edition.

Normalize each whitespace-delimited token by Unicode NFC then casefold only.
A match requires contiguous equality of the complete normalized token sequence;
whitespace variation is allowed, punctuation/hyphenation/word boundaries remain.
No dehyphenation, ligature repair, stemming, punctuation removal, translation,
fuzzy comparison, word bags, numeric projection or semantic inference. The source
sequence spans the whole joined document, so a query may cross a page boundary;
page headers/footers are still tokens and can interrupt it. Preserve every exact
occurrence, including overlapping/repeated and cross-page occurrences, with
original page-local and document spans/quotes. Match presence alone is the readout;
there is no source-identity or statistical significance admission threshold.

## Controls, visual checks, outcomes and stop

For each source page, take its first min(12, token count) whitespace tokens as a
positive query and search the complete source with the same matcher. A positive
control passes only if an occurrence covers that page's own prefix. Empty pages
retain a failing positive control, never an empty query matching everywhere.
For each positive-prefix query append the fixed one-token marker
`flv68absencecontrol20261020` as a negative query; search every negative over the
whole document. A negative passes only with zero occurrences and no marker
collision anywhere in target/source. These are engineered pipeline checks, not
natural absent-source controls or an estimated false-positive rate.

Controls and representation availability are required for interpreting presence
counts. Preserve every control, query, hit and unfavorable result. Render page 1,
page 15, and every source page containing any target hit at scale 1.2; deduplicate
page IDs only, not queries/hits. Inspect those complete images and record a
same-agent receipt for legibility and any target-hit text consistency. A cap is
unnecessary for this fixed 15-page source. Visual inspection cannot override a
failed exact match or control. Do not claim that unrendered pages were visually
reviewed; extraction fidelity for those pages remains unverified. Any positive
literal hit would need its own interpretation, without promoting it to opaque
meanings or proving a unique/immediate source.

Write target scope/queries before full-PDF extraction; preserve full source
representation, controls, complete primary/secondary match tables, per-block
counts, conditional visual receipts and a run report. Zero matches are a valid
outcome for these exact rules; they do not rule out paraphrase, shorter overlap,
PDF extraction artifacts, other editions or opaque transformations. Freeze new
code/tests/input registration before execution. A separate verifier uses an
alternative normalized-string search and independent DOM/source reconstruction,
checks all 67 earlier runs/seals and exact render bytes, and shares only declared
older helpers/parsers. Same-agent verification is not independent scientific
review. Keep research text/images private and publish small reports/code only.
Stop after this screen; do not lower 12, rephrase queries or acquire another work
in this turn. Natural-benchmark capacity and review admissions remain unchanged.
