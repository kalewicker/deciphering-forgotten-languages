# E84: exact-capture WARC locator feasibility

E83 leaves E82's replay/CDX mismatch unresolved because original WARC bytes are
absent. Test whether the named original resource has a usable bounded byte locator.
This is metadata feasibility, not an original-record download or provenance
admission. Initial documentation lookup found that CDX filename fields can be
restricted and that item metadata lists files; availability is not assumed.

Primary references consulted before registration:
- https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server
- https://archive.org/developers/md-read.html
- https://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.1/
The WARC specification distinguishes payload and record-block digests. It does not
by itself identify the byte layer of this particular CDX record. Documentation
lookups are preparatory references, not additional target-resource observations.

## Fixed inputs and two-request budget

Freeze E83's seal, E82's exact record and replay headers, protocol/code and fixtures.
Derive the sole item/file pair from the single saved x-archive-src value. Require
exactly two nonempty safe path components, no traversal or query, with filename
ending .warc.gz. Do not browse/search items or select an alternate source file.

Make exactly two GET attempts, in order, regardless of the first result:
1. One CDX exact-original query with from=to=E82's timestamp, matchType=exact,
   JSON, limit=1, and fields timestamp,original,statuscode,mimetype,digest,filename,
   offset,length. Require an exact match to all five old identity fields; never
   choose another record, timestamp or digest.
2. One https://archive.org/metadata/{exact_item} request for the item named in
   the saved header. No download, server fallback or other metadata endpoint.

Each uses system curl, config disabled, HTTPS only, zero retries/redirects,
8s connect/20s total limits, max4MiB and fixed E84 user-agent, under the approved
outer execution setting. No credentials, cookies, authentication attempts,
certificate/TLS changes, browser or API-key search. Save intent, raw response,
headers, telemetry/stderr and hashes. Transport requires exit0, HTTP200, exact
final URL, zero redirects, one application response block excluding CONNECT/1xx,
no Location, nonempty body <=4MiB; then parse JSON. Metadata errors/restrictions
remain failures. No replacement request after any outcome.

## Locator and file gates

The CDX response must have exactly the eight requested field names and one data
row. Identity fields must exactly equal E82. Filename must be the saved full
item/file pair or its exact basename. Offset and length must be decimal strings,
offset>=0 and 1<=length<=2MiB. Missing/redacted fields are unavailable, not zero.

Item JSON must be an object without error, with metadata.identifier equal to the
header item, and exactly one files entry named by the saved filename. Size must
be a positive integer/decimal string (not boolean). Item-level is_dark,
is_restricted, metadata.access-restricted-item and file-level private flags must
be absent or explicitly false/0/'false'/'0'. Unknown flag values reject rather
than implying public access. Absence of restriction flags is only metadata
compatibility, not proven download permission.

Bounded-record feasibility passes only if both transports/parsers and all gates
pass and offset+length<=listed file size. A derived bytes=start-end range and
standard archive.org/download/item/file URL may then be recorded but never
requested here. No whole-file request, even if metadata supplies a URL or server.
No CDX-field or item-schema repair. Four old post slots remain empty regardless.

## Stop and interpretation

Stop after these two metadata observations and verification. A pass supports only
a future separately registered single-range original-record retrieval, requiring
response206/range checks, record parsing and digest binding. It does not prove
access, payload identity or resolve E82. A failure leaves this resource unavailable
under this exact public-metadata route; do not sweep endpoints/fields/authentication.
If essential locators are restricted, progress needs an authorized resource from
the archive/data provider or another documented corpus source.

Independently reconstruct saved-header derivation, exact queries, budgets,
transport/hashes, record/file checks and range arithmetic. Fixture tests cover
safe paths, missing/redacted locators, changed identity, oversized/out-of-bounds
ranges, duplicate files and restriction flags. No prose display, model scores,
source/meaning/review/untouched admissions. Preserve E82/E83 and E79's unconfirmed
development result. Semantic benchmark remains0/4. Public code/protocol/reports;
raw metadata stays on the local-only evidence branch.
