# E82: archive listing recovered but rejected by the digest gate

The archive provider was reachable and supplied an exact-URL CDX record and an
HTTP200 listing replay. The replay passes **12/13 checks**, including the matching
Memento timestamp, but its saved body digest differs from the CDX digest.
The registered combined gate therefore fails. **No candidate selection or post
request ran; all four post slots remain empty.**

This is a provenance mismatch, not a finding that the listing lacks eligible
posts. E79's positive development result remains unconfirmed on new reserved
material. No model scoring, text export, source identity, independent review,
semantic label or untouched-unit admission occurred. The separate semantic
benchmark remains 0/4 qualifying works.

## Different provider, fixed budget

The user authorized continuation after E81 found neither installed client could
reach HTTP on the live FL endpoint. E82 used the Internet Archive, which had
previously supplied CDX/replay material in E38/E63. It did not retry the live
host, change TLS settings, or reopen E62/E70's closed routes.

The [protocol](../experiments/archive_intake_v82.md) and
[configuration](../experiments/archive_intake_v82.json) froze the exact observed
Kamri label URL, capture cutoff, E80's incomplete recorded-exposure registry and
all code before acquisition. At most ten requests were allowed: index/replay for
the label page, followed conditionally by index/replay for each of four posts
selected in DOM order. There were no retries, redirects followed, alternate
originals, timestamps, query variants, pagination or replacement candidates.

## Exact preserved result

| Stage | Outcome |
|---|---|
| Label CDX request | curl exit0, HTTP200, exact final URL, no redirects |
| Archive selection | One exact original record, eligible under the frozen schema |
| Selected capture timestamp | 2026-02-22 13:08:41 UTC |
| Label replay | curl exit0, HTTP200, exact id_ replay URL, no redirects |
| Memento time | Matches the selected CDX timestamp |
| HTML title | One title containing Kamri |
| Static challenge / identity conflicts | No registered challenge literal or conflicting canonical/og value |
| Saved content-decoded body size | 863,760 bytes |
| Body digest matches CDX | **False** |
| Candidate parser invoked | No |
| Post index/replay attempts | 0 / 0 |
| Total acquisition attempts | 2 / maximum 10 |
| Raw post captures | **0/4** |
| Confirmation eligibility | Unresolved |

The exact digest values are:

```text
CDX SHA-1/base32:        5MTUCDM5W7ELKVSXEIWA2HEBBYZMHDC7
Saved-body SHA-1/base32: WG3T2TCXKYCE4P3FKVMABA44LR74F4NT
Saved-body SHA-256:     8bb952394a00261c1648d10cd3d1a4679880b76bb2904380869d904674c0524e
```

The latter two identify the unchanged bytes saved after curl's transfer/content
decoding. No alternate decoding, whitespace transformation, tag removal or digest
repair was tried. The mismatch alone does not identify corruption, manipulation
or its cause; it could involve differing digest/response byte layers or replay
behavior. This experiment did not determine which explanation applies.

The CDX record, replay headers and timestamp all come from the archive provider;
their agreement is not independent corroboration or authentication of wording at
the publication date. A successful network transfer is distinct from passing
provenance checks. The raw listing is retained locally as rejected, unscored
material, not as admitted confirmation text.

The empty candidate ledger is a skipped-stage result. It is not an inventory of
zero links. Neither the first four candidates nor any later candidates were
examined by the nomination parser. Unused request opportunities are not a retry
budget and are not carried forward under E82.

## Stop and next decision

E82 closes this archive-listing batch with its gate failed. E80/E81 and every
historical result remain unchanged. Do not normalize the saved body until its
digest matches, loosen the digest rule, select a different timestamp or request
posts from this rejected listing under the consumed registration.

The next justified task is a separately scoped diagnosis of the saved index,
transport headers and digest byte layers, with no new acquisition or scoring.
Its purpose would be to explain the mismatch or leave it unresolved, not to
manufacture a pass. A future purpose-limited provenance decision would need its
own explicit justification and would preserve E82's failure. If the mismatch
cannot be resolved defensibly, obtain a different documented material resource.
No diagnostic, admission or additional network request is launched by this report.

## Verification and preservation

A separate verifier imports no E82 acquisition, CDX-selection or digest-check
functions. It reconstructs requests, commands, chronology, hashes, exact archive
selection, transport gates, Memento/digest checks, skipped nomination stage and
all four empty slots. It shares the unchanged E80 nomination/post parsers and
BeautifulSoup; neither post parser was reached on this failed listing. This is
accounting verification, not independent scientific review.

Six new fixture tests cover exact versus missing/ambiguous records, original URL,
time and digest constraints, matching/mismatched replay evidence, label identity
and fixed query parameters. **595 workspace tests and 556 isolated-public tests
pass**, with the same 39 archive-dependent exclusions. All E81 sealed artifacts
remain unchanged. The local-only archive preserves raw responses and receipts;
public main contains code, protocol and small reports.

Read-only reconstruction requires the local evidence archive:

```sh
.venv/bin/python scripts/verify_archive_intake_v82.py
```

Preparation and acquisition are single-use; do not overwrite sealed paths.
