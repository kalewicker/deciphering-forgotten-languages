# E90: Yid ZIP acquired and verified as quarantined material

The bounded download and complete archive inventory **pass**. The final ZIP is
**847,713 bytes**, with **180 entries: 179 regular files and one directory**.
Every regular member was streamed to EOF and passed decompressed-size, CRC32
and SHA-256 accounting. No document was extracted, rendered, parsed as a
translation or used by a model. This is an intact third-party archive in local
quarantine, not an admitted corpus or validated decipherment.

The package can now support a separately registered schema/provenance census.
The author's claim of **86 posts remains unverified**: file counts and names do
not establish post identities, language, independent groups or reference answers.
E79 remains unconfirmed, and the natural semantic benchmark remains **0/4**.

## Frozen acquisition and observed transport

The [protocol](../experiments/yid_archive_v90.md), implementation, eleven fixtures,
verifier, E89 evidence and exact local retrieval URL were
[frozen](../experiments/yid_archive_v90.json) before acquisition. Only the terminal
`dl=0` value was changed to `dl=1`, following
[Dropbox's download documentation](https://help.dropbox.com/share/force-download).
No alternate link, client, retry, HEAD request or endpoint search was used.

| Transport observation | Result |
|---|---:|
| Logical GET chains | 1 |
| HTTP requests / allowed maximum | 2 / 5 |
| Followed redirects / allowed maximum | 1 / 4 |
| First response | HTTP 302; 258-byte body |
| Final response | HTTP 200; 847,713-byte body |
| Aggregate retained response bodies | 847,971 bytes |
| Final entity-length/encoding checks | Pass |
| Registered response-body limit | 64 MiB |
| Final ZIP SHA-256 | `719f5aaa47a12fa543d1b8a10e1536477dcd3ba5e7c7934ee927e4f992d1c75f` |

The redirect was validated before following it, within the frozen HTTPS Dropbox
host rules. Intent, headers, status, timestamps, body and hash are retained for
each hop. Stored bytes are HTTP response entities after transfer framing, not
TLS/wire captures or authenticated historical FL responses. No cookies, account
login or origin authentication were supplied. Successful ZIP delivery does not
independently authenticate the report author's corpus or translations.

## All-member inventory and duplicate accounting

| Archive observation | Result |
|---|---:|
| Central-directory entries | 180 |
| Regular files / directories | 179 / 1 |
| Advertised expanded regular-file bytes | 1,956,836 |
| Regular files verified to EOF | 179 / 179 |
| Metadata violations | 0 |
| CRC/size/decompression failures | 0 |
| Exact-byte duplicate classes | 1 |
| Members in that duplicate class | 90 |
| Extra duplicate copies | 89 |
| Unique regular-member content hashes | 90 |
| Files under `__MACOSX/` | 90 |
| Regular files outside `__MACOSX/` | 89 |
| Filesystem extraction or document parsing | 0 |

All ninety members of the duplicate class have identical **163-byte** contents
and names under `__MACOSX/`. Those names are consistent with packaging sidecars;
their format was not interpreted. All 89 regular files outside that directory
have distinct complete-file SHA-256 hashes. No copy was deleted, and different
complete hashes do not establish absence of overlapping passages or a combined
edition duplicating individual documents.

Filename-suffix accounting is 178 `txt` entries and one `_yid-complete-86-share-ready`
suffix from a sidecar name. This is filename metadata only. Every central entry,
including directories and packaging members, remains in the ordered local ledger.
The gate checked paths/types, case/NFC collisions, encryption, compression,
advertised and actual sizes, expansion ratios and file-ancestor conflicts. It
then streamed all regular members; no safety check selected a favorable subset.
No file contents were displayed or classified as genuine Yid/English units.

## Stop and next evidence boundary

E90 is complete and stopped. The next useful step is a separately registered
**schema and provenance census across the preserved package**, accounting for
all members and identifying document roles, claimed original URLs, languages,
unit boundaries, combined editions and declared source links without modeling.
It should bind observations to exact saved-member bytes/offsets, preserve missing
or conflicting locators, and distinguish supplied annotation from corroborated
native FL text. Corpus capacity comes after that representation assessment.

No text is admitted as untouched confirmation. Prior payload exposure remains
unknown; the report's examples/claims were already exposed in E89. English
renderings and any lexical claims stay quarantined as hypotheses. A future Yid
development programme is a different declared-label question; it cannot be
presented as a fresh Kamri confirmation of E79. No source links were fetched,
semantic claims reviewed, predictions made or groups admitted here.

The stopped Kamri pagewalk, restricted WARC route, failed E77 gate, E79's adaptive
development pass and E88's exact-overlap audit remain preserved.

## Verification and publication

The separate [offline verifier](../scripts/verify_yid_archive_v90.py) imports no
E90 production code. It reconstructs the exact retrieval transformation, hop
records/headers and transport gate, all 180 entries and metadata reasons, every
member hash/size/CRC and duplicate class, and the entire report. It shares the
standard ZIP decoder; computational agreement is not independent scientific
review or original-source authentication. No network request occurs on replay.
All ten E89 sealed deliverables still match both their seals and local archive.

**644 workspace tests and 605 isolated-public tests pass**, with the same 39
archive-dependent exclusions. Eleven new fixtures cover URL transformation and
redirect domains, entity checks, complete inventories, unsafe paths/types,
encryption, limits, duplicate classes, CRC failure and non-ZIP/empty responses.

The ZIP, complete shared/redirect URLs, HTTP records and member ledger stay on
the local-only evidence branch. Public main contains protocol, code, synthetic
fixtures and aggregate reports, as specified by PUBLICATION.md. Read-only replay
requires the local archive:

```sh
.venv/bin/python scripts/verify_yid_archive_v90.py
```

Preparation and acquisition are single-use and refuse to overwrite their paths.
