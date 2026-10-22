# E83: offline digest-layer diagnosis

E82 rejected its listing because the content-decoded saved body SHA1 differs
from the CDX digest. Initial design inspection already saw gzip response encoding
and curl size_download490079 versus863760 saved bytes. Freeze this scope, code
and input hashes before the systematic diagnostic. No new acquisition or scoring.
The outcome is explanatory accounting, not a new admission criterion.

Use exactly two retained captures: E82's label replay and E63's post replay,
with their CDX responses/selection, receipts, headers and telemetry. E63 is a
previously exposed engineering comparison, not independent source corroboration.
Verify E82 seal and the receipt-bound SHA256 of both bodies before interpreting.
Read no opaque prose into outputs; all body inspection is byte-structure metadata.

For each capture:
- Independently parse the exact five-field CDX row and compare its digest with
  the saved selection. Recompute SHA1/base32 and SHA256 over unchanged body bytes.
- Preserve final response headers for content-type/encoding/length, transfer-
  encoding, their x-archive-orig counterparts, Memento-Datetime and x-archive-src.
  Separate CONNECT/1xx from application responses. Do not infer missing headers.
- Record --compressed in the original command, telemetry size_download, body
  length and whether its first bytes have gzip magic or UTF8/UTF16 BOMs. Those
  are representation observations, not a test of original WARC payload identity.
- Count exact byte occurrences (positions only) of the fixed literals:
  'BEGIN WAYBACK TOOLBAR INSERT', 'END WAYBACK TOOLBAR INSERT', 'wombat.js',
  'bundle-playback.js', 'web-static.archive.org', '__wm.init', 'WB_wombat_Init'.
  These indicate marker presence only, not proof that a marker was newly injected.

No decompression/recompression, text decoding/reencoding, newline/BOM changes,
tag stripping, whitespace normalization, digest-prefix reinterpretation, trial
hash matching, CDX replacement or WARC request. Do not enumerate article links,
nominate posts or export prose. Never claim compressed wire bytes or original
WARC bytes were retained when they are absent from these registered inputs.

Report complete two-capture evidence and all seven marker counts, including
zeros. A compression-header/size difference establishes different transport and
saved representations, not which representation the CDX digest names. Marker
presence does not establish origin or a causal explanation. If saved receipt
hashes hold, CDX extraction reproduces, and the raw-body mismatch persists, label
the mismatch reproduced with cause unresolved. Do not fabricate a repair from
circumstantial observations. If receipt integrity fails, preserve that failure
and stop interpretation rather than changing old artifacts.

Independently verify hashes, extraction, byte signatures, all marker positions,
headers and evidence conclusions without importing production diagnostic functions.
Fixtures cover malformed CDX, marker overlaps/zeros, signatures, repeated headers
and compression-size observations. Preserve all E82 results and stop after one
report. No network, admission, model change or confirmation is authorized. Natural
semantic benchmark remains0/4; raw listing stays rejected/unscored. A future
purpose-limited use would need a separately justified provenance decision, not
an E82 rescore. All raw artifacts stay on the local-only evidence branch.
