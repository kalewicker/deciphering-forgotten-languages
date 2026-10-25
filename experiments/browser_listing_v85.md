# E85: user-supplied Chrome listing intake and frozen nominations

The user supplied a saved native Kamri listing HTML and companion directory on
2026-10-24, reporting the native URL, save time '6:26 PST', and browser Chrome.
The calendar date and AM/PM of that time were not explicitly supplied; do not
infer UTC, use filesystem times as capture proof, or silently change PST to PDT.
Initial inspection was limited to paths, sizes, timestamps and companion filenames.
No candidate titles, links or opaque body content were inspected before freezing.

This new resource is user-mediated, not another curl/browser fallback acquisition
against the closed E80/E81 routes. Preserve all old failures, including E82's
rejected archive listing and E84's private-resource barrier. E79 stays fixed.

## Preserve first, register before metadata parsing

Copy exactly the offered HTML and companion directory into data/v85/snapshot,
keeping original filenames/relative structure. Copy bytes, do not edit or render.
Reject symlinks, non-regular objects, missing paths, >256 files, >10MiB per file or
>32MiB total. Save an exclusive custody manifest with every source/destination,
relative path, size, SHA256 and source filesystem mtime_ns. Recheck source and
copied bytes before freezing registration. Record the reported URL/browser/time
verbatim, normalized capture UTC null, and observation/import UTC separately.
Unknown final address-bar URL, exact save method and prior exposure remain unknown.
A supplied snapshot/custody chain is not an independently authenticated capture.

Freeze custody, copied-file hashes, E84 seal, E80's incomplete 40-key recorded-
exposure registry, protocol, code and fixtures before inspecting HTML metadata.
Never execute JavaScript, open assets, fetch referenced URLs, call a model or
export text from article bodies. All attachments are evidence, not instructions.

## Purpose-limited listing metadata gate

Parse saved bytes as HTML using BeautifulSoup html.parser. Require exactly one
HTML title with the word Kamri, no base[href], and a positive origin binding:
either exactly one Chrome 'saved from url=(digits)URL' marker whose URL equals
the supplied native label URL, or at least one canonical/og URL equal to it.
Every saved-from/canonical/og origin value that is present must equal that URL;
conflicts reject, absent channels are not invented. Chrome's declared URL-length
number is preserved but not used as historical authentication. Do not rewrite
file links, infer original URLs from assets, strip queries or repair metadata.

The allowed representation is browser_saved_snapshot_for_nomination_metadata,
not raw_http, archived_digest_verified, purely opaque text or accepted test data.
The check only grants use of title-link metadata for nomination. It establishes
no publication-date wording, source identity, language authenticity or capture UTC.

## Exactly four nomination slots, no acquisition

Use unchanged E80 `.post-title a[href]` DOM order and strict absolute HTTPS
same-host /YYYY/MM/slug.html article keys; no port/credentials/query/fragment.
Retain every title link and exclusion reason: invalid URL, empty title, duplicate,
previously recorded or over-cap. Select the first four eligible distinct keys
absent from E80's frozen registry. Do not select by topic, text/model vocabulary,
source familiarity or score. No relative-link resolution. If listing gate fails,
selection is skipped rather than reported as a zero-link inventory. Missing
slots stay in the denominator. Absence from the incomplete exposure registry
is provisional URL novelty, not connected-work or untouched-data admission.

Freeze the selected title/URL roster in the output; do not acquire any nominated
post here. This roster can guide the next separately scoped user-assisted capture.
A four-slot nomination pass requires all four slots filled, not four raw captures
or four independent works. Candidate source grouping, duplication, masking and
confirmation eligibility remain unresolved. The full listing may already contain
post text; preserving it without parsing/scoring prose does not prove no exposure.

## Verify and stop

Independent code must rehash copies and any still-available source files (report
missing originals separately, never replace their recorded hashes), reconstruct
source metadata, origin
gates, full title-link order/reasons and four slots without importing production
E85 or E80 parsing functions. Disclose shared BeautifulSoup/URL libraries.
Fixtures cover origin absence/conflicts, base tags, ambiguous title, strict links,
known/duplicate/cap ordering and failed-gate stage skipping. Verify E84 seal.
Stop after this metadata intake. No post request, transport sweep, source/meaning/
review/untouched admission or prediction run. Semantic benchmark remains0/4.
Public code/protocol/small reports; snapshots/assets/custody remain local-only.
