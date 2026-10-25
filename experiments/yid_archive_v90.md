# E90: one bounded Yid ZIP acquisition and metadata inventory

## Fixed resource and purpose

E89 identified one explicit archive offer in the documented Yid primary report.
Acquire that offer once to answer whether it supplies an intact, bounded archive
whose complete member inventory can support a later provenance/schema decision.
This is intake, not corpus admission, source adjudication, confirmation or scoring.

Read the exact shared URL from frozen data/v89/observations.json. Change only the
single terminal dl=0 query value to dl=1, preserving all other URL bytes. Dropbox's
published download documentation supports that parameter; its provider-returned
snapshot is retained locally. Freeze the full retrieval URL locally and its hash
publicly before acquisition. Do not expose the complete share URL in public docs.

## Acquisition budget and representation

One logical anonymous GET chain, maximum four followed redirects (five HTTP
requests), no retries, authentication, cookies, browser, mirrors or endpoint/query
fallbacks. Redirects must be HTTP 301/302/303/307/308, HTTPS, without userinfo,
nondefault ports or fragments, on dropbox.com or dropboxusercontent.com or their
actual subdomains (dot-delimited suffix checks). Resolve each Location before
validating it; reject multiple/missing Location fields. No HEAD probe. urllib's
redirect handler is disabled and each allowed hop is explicitly recorded before
request. Use the system TLS trust store and environment proxy settings, without
printing proxy configuration or credentials. No proxy/client/TLS sweeps.

Each hop has a ten-second socket timeout; the entire chain has a sixty-second
wall deadline. Maximum aggregate retained response entity bodies: 64 MiB; read
at most one byte beyond that bound to detect oversize and retain those bytes as
rejected evidence. Request Accept-Encoding: identity; require absent/identity
Content-Encoding and exact Content-Length when supplied on the final response.
Preserve request intents, response headers (including each redirect), final or
error body, status, URL and timestamps. Stored bodies are HTTP response entities
after transfer framing, not TLS/wire bytes. An HTTP error is an observed failed
intake; no retry. Approval/sandbox setup before an actual network call is not a
scientific retry. The run itself is single-use; never rerun a consumed chain.

Transport passes only with completed HTTP 200, permitted final URL, bounded
nonempty body and consistent final entity encoding/length. Do not require a
particular MIME spelling; record it and require a readable nonempty ZIP for the
separate archive gate. A text preview, login page, block or corrupt body stays
rejected, without guessing a corrected download URL.

## Complete archive inventory and checks

No filesystem extraction, document rendering, translation parsing or execution.
List ALL central-directory entries in order before deciding the metadata gate.
Keep original filename, size, compressed size, CRC32, compression method, flag
bits, Unix type bits, directory flag, local-header offset and metadata reasons.
The name is metadata, not a verified article title or post identity.

Limits: 1,000 entries, 256 MiB total advertised regular-member size, 32 MiB each,
and advertised member expansion ratio <=1,000 (nonempty/zero-compressed fails).
Permit stored/deflate methods only; reject encryption, symlinks/special types,
invalid directory type, NUL/control characters, absolute/drive/backslash paths,
empty/interior-dot/dot-dot path components, exact or NFC/casefold name collisions,
and a file used as an ancestor path. Directories may have zero bytes only.
Directory trailing slashes are metadata; strip one for collision checking only.
Retain every reason and original entry, with no deletion or replacement.

If metadata passes, stream EVERY regular member through the ZIP decoder to EOF
in chunks, enforcing both actual bounds and a separate thirty-second wall
budget. Retain SHA-256, actual size and CRC validation for each. zipfile's EOF CRC
check is required; failures stop hash reading and retain completed/failed/unread
statuses for all members. Do not call a partially checked ZIP integrity-passed.
Report exact-byte duplicate classes among regular members, counting extra copies
rather than silently deleting them. Group counts by filename suffix as metadata;
nested containers remain opaque. No post/unit count is inferred from file count,
filename numbering, English text or the author's claim of 86 posts.

## Registration, verification and stop

Before acquisition freeze this protocol, new code/tests/verifier, documentation,
retrieval intent, E89 seal and all its bound evidence. Fixture-check URL binding,
redirect restrictions, complete inventory, unsafe names/types/encryption, metadata
limits, CRC failure and exact-byte duplicates. Preserve all old sealed files.

A separate verifier imports no E90 production code. It reconstructs the exact
URL transformation, hop accounting, frozen hashes, transport gate, all member
metadata/reasons, decompressed sizes/hashes/CRC and duplicate classes when possible.
The ZIP decoder/standard libraries are shared; this is computational verification,
not independent archive authentication or scientific review. No network on replay.

Stop after this single intake, pass or fail. An intact archive becomes quarantined
third-party material only. A later schema/provenance census requires a new protocol
before reading document contents or selecting a corpus. Claimed translations and
lexicons are hypotheses, not answer keys. Native FL identity, language, semantic
correctness, prior exposure and connected-group capacity remain unresolved.
No model/prediction/mask/group/threshold change, source download or Kamri listing.
E79 remains unconfirmed and natural semantic qualifying works remain 0/4.
All acquired bytes, full shared/redirect URLs and member ledgers stay local-only.
Public main contains code, protocol and small aggregate reports under PUBLICATION.md.
