# E67: disclosed author-format correction and one conditional v1 PDF capture

This registration follows the exposed E66 failure on native author metadata
`Weinstein, Steven`. E66's parser assumed given-name-first words and retained a
false metadata gate with 6/7 checks. Preserve its code, tests, inputs, receipt,
report and skipped PDF stage. This is a development correction after an observed
failure, not a blind validation or a changed E66 result.

## Fixed inputs and narrow correction

Reuse exactly E66's saved arXiv HTML bytes, receipt, intent, metadata assessment,
selected arxiv:0812.0349 reference and exposure inventory. Make no new metadata
request. Replay the complete E66 assessment with its frozen implementation and
require exact equality to the saved false result. Keep all six non-author checks
unchanged, including title, ID, history, year and native route checks. Replace
only author representation handling under a new named criterion.

Accept a single citation_author in either `given family` or `family, given`
form. Normalize NFC, case and whitespace, retain original literal and form, and
parse one family token plus one or more given-name tokens. Tokens contain Latin
letters with optional internal apostrophe or hyphen, or a one-letter initial
with optional period; periods on initials are removed for canonical components.
Require nonempty components; reject more than one comma, empty comma sides,
semicolons, ampersands, slash/digits, conjunction and, suffixes jr/sr/ii/iii/iv,
and malformed tokens. Explicit multi-token family fields and unsupported scripts
abstain. The unmarked form treats its final token as family under this narrow
grammar; it does not resolve surname particles. Name parsing is a bounded grammar, not a global
personal-name standard. For this abbreviated citation require family Weinstein
and first given component initial S. This is name compatibility, not independent
proof of personal identity. Do not replace names or add aliases by topic.

## Single conditional acquisition and first-page audit

Only if all corrected metadata checks pass, request exactly
https://arxiv.org/pdf/0812.0349v1 once. One source slot, one route and at most one
application response, zero redirects/retries/searches/alternate hosts or versions.
HTTPS only, 8-second connect, 30-second total, 20 MiB maximum decoded PDF body.
Record intent before request, preserve curl command/telemetry/stderr/headers/body,
UTC times, SHA256 hashes and unsuccessful outcomes. No PDF result has been seen
before this registration. Do not use E66's unused allowance as authority; this
request has its own fresh one-route registration.

Retain E66's PDF transport/content-type/final-versioned-URL, magic, two-parser
page-count agreement and 1-40 page bound, normalized title and visible exact
0812.0349v1 marker requirements. Extract only first-page text and render the
whole first page at scale 1.5. Correct the PDF author comparison as well: use the
parsed complete metadata given components and family, matching either contiguous
`given family` or `family, given` in normalized page text with word boundaries.
Allow optional whitespace next to the comma. Require all full given components;
no initial/full-name expansion, token bag, arbitrary permutation, fuzzy spelling,
substring-of-longer-name match or new alias. Record normalized-coordinate name
match witnesses. Other first-page identity criteria stay unchanged. No body
passage matching, full-paper text extraction or full-paper visual review occurs.

Inspect the entire first-page rendering and separately record visible title,
author and exact version marker, each as pass/fail/unresolved. Link the image and
source hashes. Availability requires machine and visual identity checks to pass;
visual judgments cannot override a failed machine criterion. Preserve a PDF or
identity failure without repair, another request or replacement. A render/text
failure is recorded, not treated as semantic evidence. Freeze the full PDF bytes
locally even if a downstream identity check fails.

## Outcomes, verification and stop

Record corrected metadata result alongside E66's unchanged false value, the
complete conditional acquisition/skip result, first-page audit, full source hash,
exposure history and one-slot denominator. The citation itself has no version;
v1 is a prospective development edition, never established as the FL author's
actual edition. Native history is a provider claim. E65/E66/E67 material is
exposed development material. An incomplete known-URL inventory cannot establish
new connected work, independent source identity or untouched test status.
E63's false original gate and E62's ANITA closure remain unchanged. No semantic,
source-relationship, independent-review or natural-benchmark admission occurs.

Freeze new code/fixtures/inputs before corrected assessment and request. The
separate same-agent verifier reconstructs the corrected name and first-page
checks without production E67 functions, checks unchanged E66 criteria, receipts,
request limits, all output hashes and all 66 historical runs/seals. It may share
BeautifulSoup and sealed older helpers and PDF parsers; it cannot independently
prove the visual judgment. Keep evidence local and publish only small reports,
registration/code/tests. Stop after this acquisition/identity milestone. Any
later comparison needs a new fixed-scope, controlled registration.
