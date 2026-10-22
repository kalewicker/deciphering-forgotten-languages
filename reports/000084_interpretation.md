# E84: original-record route requires an authorized resource

The two fixed metadata requests both completed HTTP200, but they did not provide
a usable public original-record retrieval route. **The exact CDX record exposes
neither filename nor byte offset; the item and named WARC file are explicitly
marked restricted/private.** No WARC download or authentication attempt was made.

This closes the registered locator-feasibility step with its gate false.
E82's mismatch remains unresolved and its listing remains rejected/unscored.
E79's positive development result still lacks confirmation on new reserved
material. No model scores, source identity, meaning, independent review or
untouched unit was admitted; semantic benchmark capacity remains 0/4.

## Fixed resource and requests

The [protocol](../experiments/warc_locator_v84.md) and
[configuration](../experiments/warc_locator_v84.json) froze the exact E82 capture,
the sole x-archive-src item/file reference, code, fixtures and the two-request
budget before acquisition. There was no item search, alternate record, timestamp,
server or query repair. Documentation lookup preceded registration and was
separate from these two target-resource observations.

The first request asked CDX for E82's exact original URL and timestamp, including
filename, offset and length fields. The second requested metadata for the exact
item named in the saved replay header. Both used the fixed system-curl limits,
HTTPS, no retries/redirects and no credentials. No full-file or range request ran.

The method used the archive's documented [CDX API](https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server)
and [item metadata API](https://archive.org/developers/md-read.html). The former
notes that fields such as filename can be access-restricted; it does not by itself
prove why a particular field is null. The [WARC specification](https://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.1/)
distinguishes record-block and payload digests. No original WARC record was
retrieved here, so that distinction does not resolve E82's specific CDX mismatch.

## Complete observed result

| Check | Observation |
|---|---|
| Target-resource attempts | 2/2, both curl exit0 and HTTP200 |
| Exact URLs / redirects | Both exact; zero redirects |
| Capture identity fields | Timestamp, original URL, status, MIME and digest match E82 |
| CDX filename | null |
| CDX offset | null |
| CDX length | `493318` |
| Named item identifier | Matches the saved x-archive-src item |
| Matching WARC file entries | Exactly one |
| Item `metadata.access-restricted-item` | `true` string |
| Matching file `private` | `true` string |
| Listed complete WARC size | 1,077,728,985 bytes |
| Usable bounded-record locator | **No** |
| WARC download / range / authentication attempts | **0 / 0 / 0** |
| Original payload identity | Unestablished |

The CDX row refers to the same timestamp `20260222130841` and digest
`5MTUCDM5W7ELKVSXEIWA2HEBBYZMHDC7` as E82. The length alone cannot locate a
record within the large WARC file. A filename present in an old replay header
also does not supply the missing byte offset or establish public access.

The primary locator assessment's generic reason is `filename_mismatch`: it is
the first failing check, triggered by a null field, not an observed different
filename. The later offset check cannot rescue the row; the independently
inspected raw response also has null offset. The item assessment's generic reason
is `restricted_or_unknown_access_flags`; here the retained raw metadata resolves
that ambiguity to explicit `true` restriction flags, rather than unknown values.

The primary rejected item assessment leaves `file_size` null. The listed size
above is a descriptive observation from the saved metadata, not an admitted file
or a relaxed access gate. No download URL/range was admitted or requested. The
whole WARC size is far beyond the planned 2MiB single-record budget.

Null locator fields and explicit item/file restrictions are separate observations.
Together they explain why this particular public-metadata retrieval design is not
ready. They do not identify the cause of E82's replay digest mismatch, prove
corruption, or imply that every archive copy or FL corpus resource is unavailable.

## Stop and next resource boundary

Close this exact locator/item route under its consumed budget. Do not try other
archive storage servers, credentials, API keys, whole-file downloads or field
variants to work around the recorded restrictions. No further normalization,
model changes or rescores of the exposed panel are justified by this result.

The next meaningful input is an **authorized original-record copy or usable
locator supplied by the archive/data provider**, or a different documented corpus
resource with defensible capture provenance. A new file still needs grouping,
duplication, masking and reservation checks before confirmation. There is no
additional local experiment proposed to disguise that missing resource.

E80/E81/E82 failures, E83's unresolved diagnosis, E77's failed model gate and
E79's adaptive development pass all remain preserved. This is a resource-bound
stopping point, not a claim that decipherment or confirmation is impossible.
No contact with the archive/provider or external reviewer was made.

## Verification and preservation

The independent verifier imports no E84 production functions. It reconstructs the
saved-header source, exact queries and command limits, two-request order, all
artifact hashes and transport outcomes, null locator fields, item/file checks
and the false feasibility decision. All E83 sealed files remain unchanged.
Independent accounting code is not independent scientific review or provider
attestation. Metadata describes access conditions; no download-permission test
was performed because no file request was authorized by this step.

Six new fixture tests cover safe source paths, missing/redacted locators, identity,
size caps and range bounds, restriction flags, duplicate file entries and bad
sizes. **609 workspace tests and 570 isolated-public tests pass**, with the same
39 archive-dependent exclusions. Raw metadata/telemetry stay on the local-only
evidence branch; public main contains code, protocol and small reports.

Read-only verification requires the local archive:

```sh
.venv/bin/python scripts/verify_warc_locator_v84.py
```

Preparation and acquisition are single-use; do not overwrite sealed paths.
