# E83: mismatch reproduced; saved layers do not identify its cause

The offline diagnosis reproduces E82's digest mismatch and verifies the saved
bytes against their original receipt. **The cause remains unresolved.** Gzip
response decoding occurs in both the mismatching E82 replay and the matching
E63 comparison, so gzip decoding alone is not a sufficient explanation.
All seven registered archive-marker searches return zero in both bodies.

No new request, candidate selection, body transformation or model prediction
was made. E82's failed gate and four empty post slots remain unchanged. Its
listing stays rejected and unscored. E79 remains positive exposed-development
evidence awaiting confirmation on new material; no new semantic/source identity,
independent review or untouched unit is admitted. Semantic benchmark capacity
remains 0/4 qualifying works.

## Exactly two retained byte representations

The [protocol](../experiments/digest_layers_v83.md) fixed two captures and seven
literal marker searches before the systematic diagnosis. Initial design
inspection already exposed E82's gzip header and transfer/saved sizes. The E63
replay is a previously exposed engineering comparison, not independent scientific
corroboration or an additional natural test work.

| Observation | E63 post replay | E82 Kamri listing replay |
|---|---:|---:|
| Receipt-bound SHA256 agrees with current body | Yes | Yes |
| CDX digest extracted identically from saved index/selection | Yes | Yes |
| Original curl used `--compressed` | Yes | Yes |
| Replay Content-Encoding | gzip | gzip |
| Curl telemetry download size | 33,461 | 490,079 |
| Saved content-decoded body bytes | 209,306 | 863,760 |
| Saved body has gzip magic | No | No |
| Saved body has UTF8/UTF16 BOM | No | No |
| Saved body SHA1/base32 matches CDX | **Yes** | **No** |
| Original transfer-encoding header | chunked | chunked |
| Original content-encoding header retained | Absent | Absent |

Headers missing from the saved response are reported as absent, not inferred.
The download-size differences and decoded body prefixes are consistent with
curl saving a different representation from the compressed transfer. They do
not establish which byte representation the CDX digest names. E63 demonstrates
that matching a saved decoded body to a CDX digest is possible under this capture
procedure, while leaving capture-specific differences unresolved.

The unchanged E82 values remain:

```text
CDX SHA-1/base32:        5MTUCDM5W7ELKVSXEIWA2HEBBYZMHDC7
Saved-body SHA-1/base32: WG3T2TCXKYCE4P3FKVMABA44LR74F4NT
Saved-body SHA-256:     8bb952394a00261c1648d10cd3d1a4679880b76bb2904380869d904674c0524e
```

These checks show no discrepancy between the current saved body and its original
receipt, or between the recorded digest and its extraction from CDX. They do not
validate the body against the original capture payload or independently attest
the acquisition history. SHA256 continuity is local integrity evidence, not
proof of historical source identity.

## All fixed marker results

| Exact byte marker | E63 occurrences | E82 occurrences |
|---|---:|---:|
| BEGIN WAYBACK TOOLBAR INSERT | 0 | 0 |
| END WAYBACK TOOLBAR INSERT | 0 | 0 |
| wombat.js | 0 | 0 |
| bundle-playback.js | 0 | 0 |
| web-static.archive.org | 0 | 0 |
| __wm.init | 0 | 0 |
| WB_wombat_Init | 0 | 0 |

No evidence of those particular literal markers was found. This finite list
does not rule out other replay changes, rewriting, capture differences or
unrecognized injections. Even a marker's presence would not by itself prove it
was introduced after capture. No HTML interpretation, article-link enumeration,
prose display, stripping, reencoding, newline change, recompression or trial-hash
search was performed.

The registered inputs contain neither the gzip-encoded transfer body nor the
original WARC payload bytes. A header names an archive source file, but the file
itself is not in this diagnostic. Without a defensible additional byte-layer
reference, the current evidence cannot assign the cause or support a digest
repair. Do not recompress the saved HTML and call that the original wire body.

## Disclosed pre-execution compatibility revision

The initial [registration](../experiments/digest_layers_v83.json), runner,
verifier and fixtures remain unchanged. Before the diagnostic executed, a receipt
schema check found that E63 stores artifact hashes inside metadata objects while
E82 stores hashes directly as strings. The original runner/verifier assumed only
the former. No systematic diagnosis or original execution had run.

The [compatibility revision](../experiments/digest_layers_v83_revision1.md) and
[revision1 registration](../experiments/digest_layers_v83_revision1.json) accept
both existing schemas, retaining the original registration and code hashes.
Only the revision1 runner executed, into a new revision1 run directory. No
receipt bytes, input selection, marker, digest rule, transformation budget or
outcome criterion changed. This is compatibility correction, not a favorable
revision after observing the diagnostic outcome.

## Decision and verification

This closes the offline diagnosis. It does not authorize admitting the rejected
listing, rerunning E82 or starting another normalization/parameter/endpoint sweep.
Progress toward confirmation requires original archival payload evidence that can
resolve the mismatch, or a different documented corpus resource. Such acquisition
or a purpose-limited provenance policy would require a separate fixed scope and
must preserve the unresolved mismatch. There is no further discriminating check
of these same saved layers proposed by E83.

An independent verifier imports none of the E83 production functions. It checks
all frozen hashes, both receipt formats, raw CDX records, header blocks and
all marker positions, and compares decoded expected SHA1 bytes with recomputed
SHA1 bytes. Its regex marker enumeration agrees with the primary substring walk.
All E82 sealed artifacts remain unchanged. This is accounting verification,
not an independent observation of the archive or a scientific source review.

Six structural fixtures and two compatibility/scope checks pass, alongside
**603 full-workspace tests and 564 isolated-public tests**; the same 39
archive-dependent exclusions remain. All original preparation files and the
explicit compatibility revision are preserved. Byte evidence and the full
comparison remain on the local-only evidence branch; code, protocol and small
reports are public.

Read-only reconstruction requires the local archive and the revision1 verifier:

```sh
.venv/bin/python scripts/verify_digest_layers_v83_revision1.py
```

Do not execute the incompatible original runner or overwrite revision1 outputs.
